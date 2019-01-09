# coding=utf8
'''
    物理机监控服务
'''
# __author__ =  ""

from __future__ import division
from helper.time_helper import datetime_to_timestamp
from model import host_perform
from decimal import Decimal


def get_metric_data(req_ips, metric_list, start_time, end_time):
    '''
        根据host性能数据来统计监控数据
    :param req_ips:
    :param metric_list:
    :param start_time:
    :param end_time:
    :return:
    '''
    all_metric_req = []
    cpu_used_req = []
    mem_used_req = []

    if not req_ips:
        all_metric_req.append(cpu_used_req)
        all_metric_req.append(mem_used_req)
        return all_metric_req

    metric_data = host_perform.get_metric_data(set(req_ips), start_time, end_time)
    collect_time_list = []
    for _data in metric_data:
        collect_time_list.append(_data['collect_time'])
    # 去除重复并升序
    collect_time_list = set(list(collect_time_list))
    collect_time_list = list(collect_time_list)
    collect_time_list.sort()

    # 遍历不同时间
    for _collect_time in collect_time_list:
        _cumulate_cpu_used = 0
        _cumulate_cpu_all = 0
        _cumulate_mem_used = 0
        _cumulate_mem_all = 0

        for _data in metric_data:
            if _data['collect_time'] == _collect_time:
                for _ip in req_ips:
                    if str(_data['ip']) == _ip:
                        _cumulate_cpu_used += int(_data['current_cpu_used']) / 100 * int(_data['cpu_core'])
                        _cumulate_cpu_all += int(_data['cpu_core'])
                        _cumulate_mem_used += int(_data['current_mem_used']) / 100 * int(_data['mem_size'])
                        _cumulate_mem_all += int(_data['mem_size'])

        # 生成13位的时间戳
        _timestamp = datetime_to_timestamp(_collect_time) * 1000
        # 单个时间的cpu计算结果
        _cpu_used_single = []
        # 使用率为小数点两位的str   eg:  "0.00"
        # _cpu_used = _cumulate_cpu_used * 100 / _cumulate_cpu_all
        _cpu_used = _cumulate_cpu_used * 100 / _cumulate_cpu_all
        # 取小数点后两位
        _cpu_used = Decimal(_cpu_used).quantize(Decimal('0.00'))
        _cpu_used_single.append(_timestamp)
        _cpu_used_single.append(str(_cpu_used))
        if _cpu_used_single:
            cpu_used_req.append(_cpu_used_single)

        # 单个时间的mem计算结果
        _mem_used_single = []
        _mem_used = _cumulate_mem_used * 100 / _cumulate_mem_all
        # 取小数点后两位
        _mem_used = Decimal(_mem_used).quantize(Decimal('0.00'))
        _mem_used_single.append(_timestamp)
        _mem_used_single.append(str(_mem_used))
        if _mem_used_single:
            mem_used_req.append(_mem_used_single)

    all_metric_req.append(cpu_used_req)
    all_metric_req.append(mem_used_req)

    return all_metric_req


