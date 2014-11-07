#!/usr/bin/env python
#coding: utf8
import re

import requests

def main():
    com_to_re = {
        "顺丰": r"\d{12}",
        "圆通": r"[a-zA-Z0-9]\d{9}",
        "韵达": r"\d{13}",
        "申通": r"\d{12}",
        "中通": r"\d{12}",
        "宅急送": r"\d{10}",
        "EMS": r"\d{13}",
        "全峰": r"\d{12}",
        "天天": r"\d{12}",
        "百世汇通": r"\d{12}",
        "德邦物流": r"\d{9}",
    }

    with open("danhao.txt", 'a') as f:
        for k,v in com_to_re.items():
            danhao = get_danhao(k, v)
            f.write(str(danhao)+'\n')
            raw_input("first:")

def get_danhao(com, v):
    p = re.compile(v)

    base_url = 'http://zhidao.baidu.com/search?word={0}&lm=0&site=-1&sites=0&date=2&ie=utf8'.format(com)
    danhao = set()

    for i in range(0, 100, 10):
        url = "%s&pn=%s" % (base_url, i)
        print url
        data = requests.get(url).text

        result = p.findall(data)
        for x in result:
            danhao.add(x)
    danhao = list(danhao)
    return ','.join(danhao)

if __name__ == "__main__":
    main()
