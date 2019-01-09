# coding=utf8
'''
    网络区域监控
'''
# __author__ =  ""

from flask import request
import json_helper
from model.const_define import ErrorCode
import logging
from config.default import HOST_MONITOR_ATTR
from helper.time_helper import get_range_timestamp_str
from service.s_host.host_monitor_service import get_metric_data
from service.s_host.host_service import get_hosts_of_net_area
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user


@login_required
def net_area_monitor(net_area_id):
    # 这里的时间是距当前时间多少分钟，或者是月，天
    start_time = request.values.get('start_time')
    end_time = request.values.get('end_time')

    if not net_area_id or not start_time or not end_time:
        logging.info('params is invalid when get monitor data')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="参数错误")

    try:
        start_time_dt, end_time_dt = get_range_timestamp_str(start_time, style='dt')
    except Exception:
        start_time_dt = start_time
        end_time_dt = end_time

    if not all((start_time_dt, end_time_dt)):
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="时间区间无效")

    req_metrics = []
    req_ips = []
    all_hosts_data = get_hosts_of_net_area(net_area_id)
    for _host in all_hosts_data:
        req_ips.append(_host['ipaddress'])
        req_metrics.append([])

    # 设置监控项
    if any(req_metrics):
        pass
    else:
        # 设置所有的监控项
        for index, ip in enumerate(req_ips):
            temp_metric = []
            for i in range(0, len(HOST_MONITOR_ATTR)):
                temp_metric.append(HOST_MONITOR_ATTR[i])
            req_metrics[index] = temp_metric

    metric_data = get_metric_data(req_ips, req_metrics, start_time_dt, end_time_dt)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=metric_data)