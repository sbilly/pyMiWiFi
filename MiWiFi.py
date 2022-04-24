#!/usr/bin/env python3
# encoding: utf-8
# ===============================================================================
#
#         FILE:  
#
#        USAGE:    
#
#  DESCRIPTION:  
#
#      OPTIONS:  ---
# REQUIREMENTS:  ---
#         BUGS:  ---
#        NOTES:  ---
#       AUTHOR:  YOUR NAME (), 
#      COMPANY:  
#      VERSION:  1.0
#      CREATED:  
#     REVISION:  ---
# ===============================================================================

from random import random
from time import time
from hashlib import sha1
from requests import get, post
from math import floor
import json
import re

class MiWiFiClient(object):
    """
    docstring for MiWiFi
    """
    # 小米路由器首页
    URL_ROOT = "http://miwifi.com"

    device_mac: str
    device_type: str = '0'
    password: str
    key: str
    stok: str
    cookies: str = None
    # 小米路由器当前设备清单页面，登录后取得 stok 值才能完成拼接
    url_action: str = None

    def __init__(self, password: str) -> None:
        self.password = password
        self.get_key()
 
    def gen_nonce(self) -> str:
        """
        docstring for gen_nonce()
        模仿小米路由器的登录页面，计算 hash 所需的 nonce 值
        """
        miwifi_time = str(int(floor(time())))
        miwifi_random = str(int(floor(random() * 10000)))
        return '_'.join([self.device_type, self.device_mac, miwifi_time, miwifi_random])

    def encode_pass(self, nonce) -> str:
        """
        docstring for encode_pass()
        模仿小米路由器的登录页面，计算密码的 hash
        """
        return sha1(str(nonce+sha1(str(self.password + self.key).encode()).hexdigest()).encode()).hexdigest()

    def get_key(self):
        url = '%s/cgi-bin/luci/web/home' % self.URL_ROOT
        try:
            ret = get(url)
            if ret.status_code != 200:
                raise RuntimeError('%s status code %s' % (url, ret.status_code))
        except Exception as e:
            raise e
        key_matched = False
        mac_matched = False
        # key: 'a2ffa5c9be07488bbb04a3a47d3c5f6a',
        re_key = re.compile("^\s*key:\s'([^']+)',")
        # var deviceId = 'f8:ff:c2:2b:1e:45';
        re_mac = re.compile("^\s*var\sdeviceId\s=\s'([^']+)';")
        ret_text= ret.text.split('\n')
        for t in ret_text:
            if key_matched is True and mac_matched is True:
                break
            is_match =  re_key.search(t)
            if is_match:
                self.key = is_match.groups()[0]
                key_matched = True
                continue
            is_match = re_mac.search(t)
            if is_match:
                self.device_mac = is_match.groups()[0]
                mac_matched = True
                continue

    def login(self):
        """
        docstring for login()
        登录小米路由器，并取得对应的 cookie 和用于拼接 URL 所需的 stok
        """
        url = "%s/cgi-bin/luci/api/xqsystem/login" % self.URL_ROOT
        nonce = self.gen_nonce()
        password = self.encode_pass(nonce)
        payload = {'username': 'admin', 'logtype': '2', 'password': password, 'nonce': nonce}
        # print payload
 
        try:
            r = post(url, data=payload)
            # print r.text
            stok = json.loads(r.text).get('url').split('=')[1].split('/')[0]
        except Exception as e:
            raise e

        self.stok = stok
        self.cookies = r.cookies
        self.url_action =  "%s/cgi-bin/luci/;stok=%s/api" % (self.URL_ROOT, self.stok)

    def list_device(self) -> dict:
        """
        docstring for list_device()
        列出小米路由器上当前的设备清单
        """
        if self.url_action is None or self.cookies is None:
            self.login()
        url = "%s/xqsystem/device_list" % self.url_action
        try:
            r = get(url, cookies = self.cookies)
            # print json.dumps(json.loads(r.text), indent=4)
            return json.loads(r.text).get('list')
        except Exception as e:
            raise e

    def run_action(self, action: str) -> dict:
        """
        docstring for run_action()
        run a custom action like "pppoe_status", "pppoe_stop", "pppoe_start" ...
        """
        if self.url_action is None or self.cookies is None:
            self.login()
        url = '%s/xqnetwork/%s' % (self.url_action, action)
        
        try:
            r = get(url , cookies = self.cookies)
            return json.loads(r.text)
        except Exception as e:
            raise e





