#!/usr/bin/env python
#coding: utf8
try:
    import json
except ImportError:
    import simplejson as json
import urllib2

import requests
from rq import Queue
from redis import Redis

from const import REDIS_HOST, REDIS_PORT 
class PushService(object):
    """Push message

    Push ding/text/article to users who has followed the service.
    :param sid: a string that specify service id
    :param cid: a string that specify the clientServiceId.
    :param push_token: None if push to all audience, else a list instead.
    """

    def __init__(self, sid, cid, push_token=None):
        self.sid = sid
        self.auth = self.get_auth()

        PUSH_URL = 'http://demo.91dd.cc:10012/v1/service/{sid}/{clientServiceId}/push'
        PUSH_URL = PUSH_URL.replace('{sid}', sid)
        self.url = PUSH_URL.replace('{clientServiceId}', cid)
        
        if push_token:
            self.audience = {
                "push_token":push_token
            }
        else:
            self.audience = "all"

    def get_auth(self):
        r = Redis(host=REDIS_HOST, port=REDIS_PORT)
        auth = r.get("kuaidi:%s:auth" % self.sid)
        return auth

    def push_ding(self):
        post_data = {
            "audience": self.audience,
            "type": "DING"
        }

        result = self.real_push(post_data)
        return result

    def push_text(self, title, content):
        post_data = {
            "audience": self.audience,
            "type": "TEXT",
            "text":{
                "ticker": title,
                "content": content
            }
        }

        result = self.real_push(post_data)
        return result

    def push_article(self, title, summary, cover_pic, link):
        post_data = {
            "audience": self.audience,
            "type": "ARTICLE",
            "article": {
                "title": title,
                "ticker": title,
                "summary": summary,
                "cover_pic": cover_pic,
                "link": link
            }
        }

        result = self.real_push(post_data)
        return result
    
    def real_push(self, post_data):
        json_data = json.dumps(post_data)
        #print "In real_push, json_data:", json_data
        headers = {
            'Authorization': 'Basic %s' % self.auth,
            'Content-Type': 'application/json',
        }
        
        try:
            #print "url:%s\ndata:\n%s\nheaders=\n%s" % (self.url, json_data, headers)
            resp = requests.post(self.url, data=json_data, headers=headers)
        except Exception,e:
            print "Push error:", e
            return 0
        else:
            return resp.status_code


if __name__ == "__main__":
    pass
