# coding=utf8
'''
json helper
'''
# __author__ =  ""

from model import const_define
import json
from flask import jsonify
import cgi
from json import JSONEncoder
from datetime import datetime, date


def read(data):
    return json.loads(data)


def write(data):
    return json.dumps(data)

loads = read
dumps = write


def format_api_resp(code=0, data=None, http_status_code=200, msg=None):
    if not msg:
        msg = const_define.ErrorMsg.MSG_DICT.get(code, '')

    # 对html代码进行escape编码，对XSS攻击过滤
    tmp = cgi.escape(json.dumps(data, cls=DatetimeEncoder))
    data = json.loads(tmp)

    resp = {
        'code': code,
        'data': data,
        'msg': msg,
    }
    r = jsonify(resp)
    r.status_code = http_status_code
    return r


def format_api_resp_token_to_vishnu(token=None, token_timeout=str(1296000), http_status_code=200):

    # 对html代码进行escape编码，对XSS攻击过滤
    tmp = cgi.escape(json.dumps(token, cls=DatetimeEncoder))
    token = json.loads(tmp)

    resp = {
        'token': token,
        'timeout': token_timeout,
    }
    r = jsonify(resp)
    r.status_code = http_status_code
    return r


def format_api_resp_msg_to_vishnu(req_id=None, job_status='succeed', detail='kvm system error', http_status_code=200):

    # 对html代码进行escape编码，对XSS攻击过滤
    tmp = cgi.escape(json.dumps(detail, cls=DatetimeEncoder))
    detail = json.loads(tmp)

    resp = {
        'jobStepNodeId': req_id,
        'status': job_status,
        'detail': detail
    }
    r = jsonify(resp)
    r.status_code = http_status_code
    return r


def format_api_resp_msg(code=0, job_status='succeed', detail='kvm system error', http_status_code=200):

    # 对html代码进行escape编码，对XSS攻击过滤
    tmp = cgi.escape(json.dumps(detail, cls=DatetimeEncoder))
    detail = json.loads(tmp)

    resp = {
        'code': code,
        'status': job_status,
        'detail': detail
    }
    r = jsonify(resp)
    r.status_code = http_status_code
    return r


def format_api_resp_msg_for_group_add(job_status='succeed', detail='kvm system error', http_status_code=200):

    # 对html代码进行escape编码，对XSS攻击过滤
    tmp = cgi.escape(json.dumps(detail, cls=DatetimeEncoder))
    detail = json.loads(tmp)

    resp = {
        'status': job_status,
        'detail': detail
    }
    r = jsonify(resp)
    r.status_code = http_status_code
    return r


def format_api_resp_msg_to_vishnu_resource(job_status='succeed', detail='kvm system error', http_status_code=200):

    # 对html代码进行escape编码，对XSS攻击过滤
    tmp = cgi.escape(json.dumps(detail, cls=DatetimeEncoder))
    detail = json.loads(tmp)

    resp = {
        'status': job_status,
        'detail': detail
    }
    r = jsonify(resp)
    r.status_code = http_status_code
    return r


class DatetimeEncoder(JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        else:
            return JSONEncoder.default(self, obj)