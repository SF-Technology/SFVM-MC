#coding=utf8
'''
频率限制
'''
import logging

__author__ =  ""

import const_define
from flask import request
from rratelimit import Limiter
from cache import redis_lib
import json_helper

def rate_limit():
    #TODO   通用化  配置化
    module_name = request.values.get('module_name')

    ip = request.values.get('ip')

    redis_cache = redis_lib.RedisForCommon.get_instance_for_common_1()
    if module_name == '/account/check_sign_in':
        #ip地址的限制
        if ip:
            key='ip'
            ip_limiter = Limiter(redis_cache, action=module_name+key, limit= 20, period = 60 * 10 )
            ip_limiter_2 = Limiter(redis_cache, action=module_name+key+'2', limit= 50, period = 60 * 60 * 2)
            ret = ip_limiter.checked_insert(ip)
            if not ret:
                return json_helper.format_api_resp(const_define.ErrorCode.RATE_LIMIT_ERR)
            ret = ip_limiter_2.checked_insert(ip)
            if not ret:
                return json_helper.format_api_resp(const_define.ErrorCode.RATE_LIMIT_ERR)

    return json_helper.format_api_resp()
