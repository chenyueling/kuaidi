#!/usr/bin/env python
#coding: utf8
import requests

def count_words_at_url(url):
    resp = requests.get(url)
    length = len(resp.text.split())
    print "length =", length
    return length

if __name__ == "__main__":
    count_words_at_url('http://renren.com')
