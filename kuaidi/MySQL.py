#!/usr/bin/env python
#coding: utf8
"""
Encapsulate for python operate mysql

__author__ = tangjh
create_date: 2014.7.23
"""
import MySQLdb

from const import MYSQL_HOST, MYSQL_PORT,\
        MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB

class DB:
    """
    Operate mysql with Python
    """

    def __init__(self):
        self.host = MYSQL_HOST
        self.port = MYSQL_PORT
        self.user = MYSQL_USER
        self.password = MYSQL_PASSWORD
        self.db = MYSQL_DB
        self.charset = 'utf8'

        self.conn = self.getConn()

    def getConn(self):
        return MySQLdb.Connect(
                host=self.host,
                port=self.port,
                user=self.user,
                passwd=self.password,
                db=self.db,
                charset=self.charset)

    def query(self, sql):
        cursor = self.conn.cursor()

        cursor.execute(sql)
        data = cursor.fetchall()

        cursor.close()
        self.conn.close()
        return data

    def update(self, sql):
        cursor = self.conn.cursor()

        cursor.execute(sql)
        self.conn.commit()

        cursor.close()
        self.conn.close()

if __name__ == "__main__":
    db = DB()
    data = db.query('show tables;')
    print data
