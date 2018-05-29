#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'luo_dao_yi'
__date__ = '2018/5/28 12:36'

import logging
import pprint

import CloudFlare
from flask import Flask, send_from_directory, \
    render_template, request, redirect, \
    make_response, session, flash, url_for

import config
from cloud_flare import CF

cf = CF(config.cf_key)

_log_ = logging.getLoggerClass()
app = Flask(__name__)
app.secret_key = config.super_secret


# 静态文件
@app.route('/assets/<path:path>')
def send_assets(path):
    return send_from_directory('assets', path)


# 退出登录
@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user_info', None)
    return render_template('logout.html')


# 首页 登录
@app.route('/', methods=['POST', 'GET'])
def home():
    if 'user_info' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form['cloudflare_email']
        password = request.form['cloudflare_pass']
        if email and password:
            result = cf.user_create(email, password)
            if result['result'] == 'success':
                resp_data = result['response']
                resp = make_response(redirect('/dashboard'))
                session['user_info'] = resp_data
                return resp
            else:
                flash(result['msg'])
        else:
            flash('请正确输入email和password!')
    return render_template('home.html')


# 切换代理状态 enable 0 关闭 1开启
@app.route('/proxy/<string:zone_id>/<string:record_id>/<int:on>', methods=['GET'])
def proxy(zone_id, record_id, on=0):
    if 'user_info' not in session:
        return redirect(url_for('home'))
    user_info = session['user_info']
    cf_client = CloudFlare.CloudFlare(user_info['cloudflare_email'], token=user_info['user_api_key'])
    dns_record = cf_client.zones.dns_records.get(zone_id, record_id)
    option = '开启' if on == 1 else '关闭'
    if on == 0:
        dns_record['proxied'] = False
    else:
        dns_record['proxied'] = True
    try:
        cf_client.zones.dns_records.put(zone_id, record_id, data=dns_record)
        flash(f'{option}成功!', 'green')
    except Exception as e:
        flash(f'{option}失败!', 'red')
        flash(f'{e}', 'red')
    return redirect(url_for('zones', domain=dns_record['zone_name']))


# 查看域名
@app.route('/zones/<string:domain>', methods=['GET'])
def zones(domain):
    if 'user_info' not in session:
        return redirect(url_for('home'))
    user_info = session['user_info']
    cf_client = CloudFlare.CloudFlare(user_info['cloudflare_email'], token=user_info['user_api_key'])
    zones = cf_client.zones.get(params={'name': domain})
    if len(zones) != 1:
        return redirect(url_for('dashboard'))
    zone = zones[0]
    dns_records = cf_client.zones.dns_records.get(zone['id'])
    return render_template('zones.html', domain=domain, zone=zone, dns_records=dns_records)


# 控制面板
@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'user_info' not in session:
        return redirect(url_for('home'))
    user_info = session['user_info']
    cf_client = CloudFlare.CloudFlare(user_info['cloudflare_email'], token=user_info['user_api_key'])
    zones = cf_client.zones.get()
    # pprint.pprint(zones)
    return render_template('dashboard.html', zones=zones, partners='bitrabbit')


# 添加domain
@app.route('/add_domain', methods=['GET', 'POST'])
def add():
    if 'user_info' not in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        domain = request.form['domain']
        type = request.form['type']
        if not domain or not type:
            flash('请正确输入域名和正确选择接入类型', 'red')
            return render_template('add.html')
        user_info = session['user_info']
        if type == 'cname':
            result = cf.zone_set(user_info['user_key'], domain, 'example.com', '_domain-wildcard')
            pprint.pprint(result)
            if result['result'] == 'error':
                flash(result['msg'], 'red')
                return render_template('add.html')
            cf_client = CloudFlare.CloudFlare(user_info['cloudflare_email'], token=user_info['user_api_key'])
            zone = cf_client.zones.get(params={'name': domain})[0]
            dns_records = cf_client.zones.dns_records.get(zone['id'])
            for record in dns_records:
                if record['content'] == 'example.com':
                    cf_client.zones.dns_records.delete(zone['id'], record['id'])
            flash(f'添加域名 {domain} 成功!', 'green')
            return redirect(url_for('zones', domain=domain))
        if type == 'ns':
            result = cf.full_zone_set(user_info['user_key'], domain)
            pprint.pprint(result)
            if result['result'] == 'error':
                flash(result['msg'], 'red')
                return render_template('add.html')
            flash(f'添加域名 {domain} 成功!', 'green')
            flash(result['response']['msg'], 'red')
            return redirect(url_for('zones', domain=domain))
    return render_template('add.html')


# 更换接入方式参数 ns 1 标准  2通用
@app.route('/cname/<string:domain>/<int:ns>', methods=['GET'])
def cname(domain, ns):
    if 'user_info' not in session:
        flash('需要登录', 'red')
        return redirect(url_for('home'))
    user_info = session['user_info']
    cf_client = CloudFlare.CloudFlare(user_info['cloudflare_email'], token=user_info['user_api_key'])
    zones = cf_client.zones.get(params={'name': domain})
    if len(zones) != 1:
        flash('找不到域名!', 'red')
        return redirect(url_for('dashboard'))
    zone = zones[0]
    # 获得dns记录
    # dns_records = cf_client.zones.dns_records.get(zone['id'])
    # 删除域名
    try:
        cf_client.zones.delete(zone['id'])
        if ns == 1:
            return redirect(url_for('add', domain=domain, type='ns'))
        else:
            return redirect(url_for('add', domain=domain, type='cname'))
    except Exception as e:
        flash(f'操作失败!{e}', 'red')
        return redirect(url_for('dashboard'))


# 编辑dns record_id 记录id
@app.route('/record/<string:action>/<string:zone_id>/<string:domain>', methods=['GET', 'POST'])
def record(domain, action, zone_id):
    if 'user_info' not in session:
        flash('需要登录', 'red')
        return redirect(url_for('home'))
    user_info = session['user_info']
    cf_client = CloudFlare.CloudFlare(user_info['cloudflare_email'], token=user_info['user_api_key'])
    if request.method == 'POST':

        name = request.form.get('name', '')
        type_name = request.form.get('type', 'A')
        content = request.form.get('content', '')
        if not name or not type_name or not content:
            flash('请检查输入!', 'red')
            return render_template('record.html', domain=domain, record=None)
        ttl = request.form.get('ttl', 1)
        proxied = request.form.get('proxied', 'true')
        priority = request.form.get('priority', 10)  # 权重 仅仅mx
        if not priority:
            priority = 10
        post_json = {
            'type': type_name,
            'name': name,
            'content': content,
            'ttl': int(ttl),
            'priority': int(priority),
            'proxied': True if proxied == 'true' else False
        }
        # pprint.pprint(user_info)
        # pprint.pprint(post_json)
        try:
            if action == 'add':
                cf_client.zones.dns_records.post(zone_id, data=post_json)
                flash(f'创建成功!', 'green')
            if action == 'edit':
                record_id = request.args.get('record_id')
                if not record_id:
                    flash('未找到record_id', 'red')
                    return redirect(url_for('zones', domain=domain))
                cf_client.zones.dns_records.put(zone_id, record_id, data=post_json)
                flash(f'修改成功!', 'green')
            return redirect(url_for('zones', domain=domain))
        except Exception as e:
            print('*' * 150)
            pprint.pprint(e)
            flash(f'操作失败: {e}', 'red')
        return render_template('record.html', domain=domain, record=post_json)
    else:
        if action == 'delete':
            record_id = request.args.get('record_id')
            if not record_id:
                flash('未找到record_id', 'red')
                return redirect(url_for('zones', domain=domain))
            try:
                cf_client.zones.dns_records.delete(zone_id, record_id)
                flash('删除成功', 'green')
            except Exception as e:
                flash(f'删除失败:{e}', 'red')
            return redirect(url_for('zones', domain=domain))
        if action == 'add':
            return render_template('record.html', domain=domain, record=None)
        if action == 'edit':
            record_id = request.args.get('record_id')
            if not record_id:
                flash('未找到record_id', 'red')
                return redirect(url_for('zones', domain=domain))
            record = cf_client.zones.dns_records.get(zone_id, record_id)
            return render_template('record.html', domain=domain, record=record)
    return redirect(url_for('zones', domain=domain))


# 页面访问统计
@app.route('/analytics/<string:domain>', methods=['GET'])
def analytics(domain):
    if 'user_info' not in session:
        flash('需要登录', 'red')
        return redirect('/')
    flash('开发中', 'red')
    return redirect('/')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True, host='0.0.0.0')
