#!/usr/bin/env python
#coding: utf8
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from datetime import datetime
try:
    import json
except ImportError:
    import simplejson as json

from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application, url, authenticated
import tornado.autoreload
from tornado.escape import json_encode

from rq import Queue
from redis import Redis
#from apscheduler.scheduler import Scheduler

from kuaidi.jobs import count_words_at_url
from kuaidi.kuaidi_task import set_kuaidi_auth, start_kuaidi_task, add_kuaidi_tixing,\
        delete_kuaidi_tixing, active_kuaidi_tixing, loop_kuaidi_task, response_ding_action
from kuaidi.const import REDIS_HOST, REDIS_PORT

redis_conn = Redis(host=REDIS_HOST, port=REDIS_PORT)
q = Queue('kuaidi_tornado', connection=redis_conn)
#scheduler = Scheduler()
#scheduler.start()

class HelloHandler(RequestHandler):
    def get(self):
        self.write('Hello, world!')

class KuaiDiHandler(RequestHandler):
    """Kuaidi Factory
    
    Provide API for:
        add kuaidi tixing service when service created;
        delete certain kuaidi tixing service when followed num become 0;
        response the Ding action from user;
    """

    def post(self):
        post_data = self.request.body
        try:
            json_data = json.loads(post_data)
            print "json_data:", json_data
    
            sid = json_data['sid']
            action = json_data['action']
            if action == 'ACTION_SERVICE_CREATE':
                # 创建快递提醒服务
                title = json_data['title']
                api_secret = json_data['api_secret']
                
                q.enqueue(set_kuaidi_auth, sid, api_secret) 

                try:
                    c_data = json_data['c_data']
                except Exception,e:
                    print "c_data:%s" % e
                    resp = {
                        "code": 3000,
                        "message": "success"
                    }
                    self.write(json_encode(resp))
                    return
                    

                for c_data_item in c_data:
                    cid = c_data_item['cid']
    
                    c_data_data = c_data_item['data']
                    exec("c_json_data="+c_data_data)
                    com = c_json_data['com']   # 快递公司标示
                    nu = c_json_data['nu']   # 快件单号
    
                    print "com:%s, nu:%s" % (com, nu)
                    print "cid:%s" % cid
                    q.enqueue(add_kuaidi_tixing, cid, com, nu)
                   
                    resp = {
                        "code": 3000,
                        "message": "success"
                    }
                    self.write(json_encode(resp))
    
            elif action == 'ACTION_CLIENT_SERVICE_CREATE':
                # 客户端创建快递提醒服务
                data = json_data['data']
                exec("c_json_data="+data)
                
                com = c_json_data['com']
                nu = c_json_data['nu']
    
                cid = json_data['cid']
    
                print "客户端创建快递提醒:%s,%s" % (com, nu)
                q.enqueue(add_kuaidi_tixing, cid, com, nu)
    
                resp = {
                    "code": 3000,
                    "message": "success"
                }
                self.write(json_encode(resp))

            elif action == 'ACTION_SERVICE_FOLLOWED_CHANGE':
                # 快递提醒服务关注数变更，当为0的时候删掉此服务
                followed = json_data['followed']
                cid = json_data['cid']
                if followed == 0:
                    print "No People Follow ClientService:%s, deactivi it now:%s" % (cid, datetime.now())
                    q.enqueue(delete_kuaidi_tixing, cid)
                elif followed == 1:
                    print "This Service Follower now, active it! "
                    q.enqueue(active_kuaidi_tixing, cid)
                else:
                    print "There are %s People Follow ClientService %s." % (followed, cid)

                resp = {
                    "code": 3000,
                    "message": "success"
                }
                self.write(json_encode(resp))
    
            elif action == 'ACTION_SERVICE_DING':
                # 用户ding操作
                push_token_str = json_data['push_token']
                push_token = list()
                push_token.append(push_token_str)
                cid = json_data['cid']
                q.enqueue(response_ding_action, sid, cid, push_token)


                resp = {
                    "code": 3000,
                    "message": "success"
                }
                self.write(json_encode(resp))
            elif action == "ACTION_SERVICE_UPDATE":
                print "ACTION_SERVICE_UPDATE"
                resp = {
                    "code": 3000,
                    "message": "success"
                }
                self.write(json_encode(resp))
        except Exception, e:
            print "Error:%s",e

"""
def schedule_job():
    scheduler.add_cron_job(kuaidi_task, minute="*/1")

def kuaidi_task():
    q.enqueue(start_kuaidi_task)
"""

def make_app():
    app = Application([
        url(r'/hello', HelloHandler),
        url(r'/kuaidi', KuaiDiHandler),
        ])

    return app

def main():
    #schedule_job()

    if len(sys.argv) == 2:
        port = int(sys.argv[1])
    else:
        raise SystemExit

    app = make_app()
    app.listen(port)
    IOLoop.current().start()

if __name__ == "__main__":
    main()
