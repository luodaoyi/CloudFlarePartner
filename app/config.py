#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'luo_dao_yi'
__date__ = '2018/5/28 12:52'

import os

from dotenv import load_dotenv

load_dotenv()

cf_key = os.getenv('CF_KEY')
super_secret = os.getenv('SECRET')
