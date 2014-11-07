#!/usr/bin/env python
#coding: utf8
from rq import Queue
from redis import Redis
from apscheduler.scheduler import Scheduler

from kuaidi.kuaidi_task import start_kuaidi_task
from kuaidi.const import REDIS_HOST, REDIS_PORT

redis_conn = Redis(host=REDIS_HOST, port=REDIS_PORT)
q = Queue('factory_scheduler', connection=redis_conn)
scheduler = Scheduler(daemonic=False)
scheduler.start()

def schedule_job():
    scheduler.add_cron_job(kuaidi_task, minute="*/1")

def kuaidi_task():
    q.enqueue(start_kuaidi_task)

def main():
    schedule_job()

if __name__ == "__main__":
    main()
