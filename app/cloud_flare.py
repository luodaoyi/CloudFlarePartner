#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'luo_dao_yi'
__date__ = '2018/5/28 12:37'

import pprint

import CloudFlare
import requests
import config

class CF:
    def __init__(self, host_key):
        self._host_key = host_key
        self._session = requests.Session()
        self.json_data = dict()

    def _post(self, ):
        json_data = self.json_data
        json_data['host_key'] = self._host_key
        with self._session.post('https://api.cloudflare.com/host-gw.html', json_data) as resp:
            self.json_data = dict()
            return resp.json()

    def user_create(self, email, password):
        # //create a new user
        self.json_data['act'] = "user_create"
        self.json_data['cloudflare_email'] = email
        self.json_data['cloudflare_pass'] = password
        self.json_data['unique_id'] = None
        return self._post()

    def zone_set(self, user_key, zone_name, resolve_to, subdomains, ):
        # set or edit a zone
        self.json_data['act'] = 'zone_set'
        self.json_data["user_key"] = user_key
        self.json_data["zone_name"] = zone_name
        self.json_data["resolve_to"] = resolve_to
        self.json_data["subdomains"] = subdomains
        return self._post()

    def full_zone_set(self, user_key, zone_name):
        self.json_data['act'] = 'full_zone_set'
        self.json_data['user_key'] = user_key
        self.json_data['zone_name'] = zone_name
        return self._post()

    def user_lookup(self, email):
        # lookup for a user to get host_key
        self.json_data['act'] = 'user_lookup'
        self.json_data['cloudflare_email'] = email
        return self._post()

    def user_auth(self, email, password):
        self.json_data['act'] = "user_auth"
        self.json_data['cloudflare_email'] = email
        self.json_data['cloudflare_pass'] = password
        self.json_data['unique_id'] = None
        return self._post()

    def zone_lookup(self, user_key, zone_name):
        # 查看域名
        self.json_data["act"] = "zone_lookup"
        self.json_data["user_key"] = user_key
        self.json_data["zone_name"] = zone_name
        return self._post()

    def zone_delete(self, user_key, zone_name):
        # 删除域名
        self.json_data["act"] = "zone_delete"
        self.json_data["user_key"] = user_key
        self.json_data["zone_name"] = zone_name
        return self._post()

    # 当前所有domain
    def zone_list(self, limit, offset):
        self.json_data["act"] = "zone_list"
        self.json_data["limit"] = limit
        self.json_data["offset"] = offset
        self.json_data['zone_status'] = 'ALL'
        self.json_data['sub_status'] = 'ALL'
        return self._post()

