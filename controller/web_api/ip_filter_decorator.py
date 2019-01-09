# -*- coding:utf-8 -*-
# __author__ =  ""
from functools import wraps
from flask import request
from helper import json_helper
from model.const_define import ErrorCode
from service.s_request_ip_permit import request_ip_permit_service as request_i_p_s
import logging


def ip_filter_from_other_platform(func):
    """
    判断外部接口调用ip白名单
    :param func:
    :return:
    """

    @wraps(func)
    def inner(*args, **kwargs):
        client_ip = request.headers.get('X-Forwarded-For', '')
        logging.warn("api ip:" + client_ip)
        if not client_ip:
            return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="无法获取请求方IP")

        ip_params = {
            'WHERE_AND':
                {
                    '=': {
                        'ip_permit': client_ip
                    }
                }
        }
        permit_ip_nums, permit_ip_datas = request_i_p_s.RequestIpPermitService().query_data(**ip_params)
        if permit_ip_nums <= 0:
            return json_helper.format_api_resp(code=ErrorCode.AUTH_ERROR, msg="请求应用IP地址无权访问，请联系系统组同事")
        return func(*args, **kwargs)

    return inner
