# coding=utf8
'''
    Balent监控
'''


from flask import request
import json_helper
from model.const_define import ErrorCode
import logging
from lib.monitor.monitor import get_target_id, get_metric_id, get_metric_data
from helper.time_helper import datetime_to_timestamp, get_range_timestamp_str, change_datetime_to_timestamp
from config.default import BALANT_ATTR
import json
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user


@login_required
def monitor():
    '''
        Balent监控
    :return:
    '''
    # ip_list: [{ip1:[m1,m2,m3,m4]},{ip2:[m1,m2,m3,m4]},{ip3:[]}]
    print "-"*25
    print request.get_data()
    print "-" * 25
    ip_list = json.loads(request.get_data()).get('ip_list')

    start_time = json.loads(request.get_data()).get('start_time')
    end_time = json.loads(request.get_data()).get('end_time')

    if not ip_list or not start_time or not end_time:
        logging.info('params is invalid when get monitor data')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="参数错误")

    try:
        start_timestamp, end_timestamp = get_range_timestamp_str(start_time)
    except Exception:
        start_timestamp = change_datetime_to_timestamp(start_time)
        end_timestamp = change_datetime_to_timestamp(end_time)

    if not all((start_timestamp, end_timestamp)):
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="时间区间无效")

    if not ip_list:
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=[])

    req_metrics = []
    req_ips = []
    for ip_dict in ip_list:
        metrics = ip_dict.values()[0]
        temp_metric = []
        if metrics:
            for i in range(0, len(BALANT_ATTR)):
                temp_metric.append(metrics[i])
        req_metrics.append(temp_metric)

        ip = ip_dict.keys()[0]
        req_ips.append(ip)

    if any(req_metrics):
        pass
    else:
        for index, ip in enumerate(req_ips):
            target_id = get_target_id(ip)
            print target_id
            metric_list = get_metric_id(target_id)
            req_metrics[index] = metric_list

    metric_data = get_metric_data(req_ips, req_metrics, start_timestamp, end_timestamp)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=metric_data)
