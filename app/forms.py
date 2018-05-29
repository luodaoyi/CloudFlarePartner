#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'luo_dao_yi'
__date__ = '2018/5/29 15:29'

from flask_wtf import Form
from wtforms.fields import (StringField, BooleanField,
                            SelectField, IntegerField)
from wtforms.validators import Length, NumberRange


class RecordForm(Form):
    type = SelectField('记录类型', choices=[
        ('A', 'A'),
        ('AAAA', 'AAAA'),
        ('CNAME', 'CNAME'),
        ('TXT', 'TXT'),
        ('SRV', 'SRV'),
        ('LOC', 'LOC'),
        ('MX', 'MX'),
        ('NS', 'NS'),
        ('SPF', 'SPF')
    ])
    name = StringField('记录名', validators=[Length(max=255)])
    content = StringField('记录内容')
    ttl = IntegerField('TTL', validators=[NumberRange(min=1, max=2147483647)])
    priority = IntegerField('权重', validators=[NumberRange(min=0, max=65535)])
    proxied = BooleanField('CDN')
