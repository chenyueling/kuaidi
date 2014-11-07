#!/usr/bin/env python
#coding: utf8
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import time
import random
import base64
from datetime import datetime
try:
    import json
except ImportError:
    import simplejson as json

import requests
from rq import Queue
from redis import Redis

from push_task import PushService
from MySQL import DB
from const import REDIS_HOST, REDIS_PORT

redis_conn = Redis(host=REDIS_HOST, port=REDIS_PORT)
q = Queue("kuaidi_task", connection=redis_conn)

def set_kuaidi_auth(sid=None, api_secret=None):
    if api_secret and sid:
        auth = base64.encodestring(sid+":"+api_secret).replace("\n", '')
        # write into Redis like kuaidi:sid:auth
        r = Redis(host=REDIS_HOST, port=REDIS_PORT)
        result = r.set("kuaidi:%s:auth"% sid, auth)
        if not result:
            print "Error: Failed to set kuaidi:%s:auth=%s" % (sid, auth)
        else:
            print "Successfule to set kuaidi:%s:auth=%s" % (sid, auth)

def start_kuaidi_task():
    r = Redis(host=REDIS_HOST, port=REDIS_PORT)
    kuaidi_key = r.keys("kuaidi:*:auth")
    print kuaidi_key
    if kuaidi_key:
        sid = kuaidi_key[0].split(':')[1]
        loop_kuaidi_task(sid)

def add_kuaidi_tixing(cid, com, nu):
    db = DB()

    now = int(time.time())
    create_time = datetime.fromtimestamp(now)

    try:
        sql = "insert into t_dd_kuaidi(cid, com, nu, create_time, active)\
                values('{0}', '{1}', '{2}', '{3}', 1)".format(cid, com, nu, create_time)
        db.update(sql)
        print "Successful to add kuaidi tixing: cid=%s, com=%s,\
                nu=%s" % (cid, com, nu)
    except Exception,e:
        print "Error: Failed to add kuaidi tixing: cid=%s, com=%s,\
                nu=%s" % (cid, com, nu)
        print "Failed info:", e
        print "sql:", sql

def delete_kuaidi_tixing(cid):
    try:
        db = DB()
        sql = "update t_dd_kuaidi set active=0 where cid = '%s'" % cid
        db.update(sql)
        print "Successful to Delete cid:%s from t_dd_kuaidi!" % cid
    except Exception,e:
        print "Error:Faild delete cid:%s from t_dd_kuaidi!" % cid
        print "Failed info:", e
        print "sql:",sql

def active_kuaidi_tixing(cid):
    try:
        db = DB()
        sql = "update t_dd_kuaidi set active=1 where cid = '%s'" % cid
        db.update(sql)
        print "Successful to Active cid:%s from t_dd_kuaidi!" % cid
    except Exception,e:
        print "Error:Faild active cid:%s from t_dd_kuaidi!" % cid
        print "Failed info:", e
        print "sql:",sql

def loop_kuaidi_task(sid):
    db = DB()
    sql = """
    select cid, com, nu
    from t_dd_kuaidi
    where active=1
    """

    print "Start loop kaudi task..."
    data = db.query(sql)
    dtype = 'loop'
    for record in data:
        cid, com, nu = record[0], record[1], record[2]
        q.enqueue(query_kuaidi_info, sid, cid, com, nu, dtype)

def query_kuaidi_info(sid, cid, com, nu, dtype, push_token=None):
    com_to_code = {
        "顺丰": "shunfeng",
        "圆通": "yuantong",
        "韵达": "yunda",
        "申通": "shentong",
        "中通": "zhongtong",
        "宅急送": "zhaijisong",
        "EMS": "ems",
        "全峰": "quanfengkuaidi",
        "天天": "tiantian",
        "百世汇通": "huitongkuaidi",
        "德邦物流": "debangwuliu", 
    }

    com,old = com_to_code.get("{0}".format(com), None), com

    if com:
        #query_url = 'http://api.kuaidi100.com/api?id={0}&com={1}&nu={2}&\
        #        show=0&muti=0&order=desc'.format('10ed70c45cc9b32e', com, nu)
        query_url = 'http://www.kuaidi100.com/query?id=1&type=%s&postid=%s&\
                valicode=&temp=%s' % (com, nu, random.random())
        
        error_times = 0
        while True:
            try:
                json_data = requests.get(query_url).text
                break
            except Exception,e:
                print "Error when query kuaidi info:",e
                print "query_url:", query_url
                error_times += 1
                if dtype != 'ding':
                    time.sleep(error_times*1)
                if error_times >= 5:
                    print "The API provided by Kuaidi100.com is not available!!!!!"
                    return 

        dict_data = json.loads(json_data)
    
        now = int(time.time())
        check_time= datetime.fromtimestamp(now)
    
        status = dict_data['status']
        if status == '200':
            # 查询成功
            state = dict_data['state']
            
            kuaidi_data = dict_data['data']
            last_info = kuaidi_data[0]
            last_time = last_info['time']
            last_context = last_info['context']
    
            q.enqueue(push_handler, sid, cid, check_time, last_time, last_context, dtype, push_token)

            if state == '3':
                q.enqueue(delete_kuaidi_tixing, cid)
        elif status == '201':
            # 接口出现异常
            msg = '单号暂时不存在或者已经过期'
            print "Error:%s%s%s" % (com, nu, msg)
        else:
            # 物流单暂无结果
            msg = dict_data['message']
            print "%s, %s:%s" % (msg, com, nu)
    else:
        print "Sorry we haven't provide %s kuaidi service." % old

def push_handler(sid, cid, ck_time, last_time, context, dtype, push_token):
    db = DB()
    sql = "select state_time, check_time from t_dd_kuaidi where cid='%s'" % cid
    data = db.query(sql)

    state_time = data[0][0]
    check_time = data[0][1]

    # update check_time
    udb = DB()
    sql = "update t_dd_kuaidi set check_time='%s' where cid='%s'" % (ck_time, cid)
    print "Update check_time,sql:", sql
    udb.update(sql)

    #print "state_time:%s, last_time:%s" % (state_time, last_time)

    if state_time != last_time or dtype=='ding':
        # push new state and update push_time, state_time
        print "Start push message..."
        Push = PushService(sid, cid, push_token)
        status_code = Push.push_text('快递提醒', context)

        now = int(time.time())
        push_time = datetime.fromtimestamp(now)

        if status_code == 200:
            print "Push message Successful!"
            sdb = DB()
            sql = "update t_dd_kuaidi set state_time='%s',\
                    push_time='%s' where cid='%s'" % (last_time, push_time, cid)
            sdb.update(sql)
            print "Update state_time, push_time:%s" % sql
        else:
            print "Push message Error!"
            print "Status code: %s, Error accurs when push new state: cid=%s, ck_time=%s,\
                    last_time=%s, context=%s, push_token=%s, push_time=%s\
                    " % (status_code, cid, ck_time, last_time, context, push_token, push_time)


def response_ding_action(sid, cid, push_token):
    db = DB()
    sql = "select com,nu from t_dd_kuaidi where cid='%s'" % cid
    data = db.query(sql)

    com = data[0][0]
    nu = data[0][1]

    dtype = "ding"

    q.enqueue(query_kuaidi_info, sid, cid, com, nu, dtype, push_token)
