#coding:utf-8

from flask import request
import traceback
from model.const_define import ErrorCode
import logging
import json_helper
from common_data_struct import base_define



class HostMetricResp(base_define.Base):

    def __init__(self):
        self.operate_return = None
        self.record_num = 0
        self.record_success_insert_num = 0

class HostMetricGetResp(base_define.Base):
    """
        把从数据库读回的11条记录【目前为止是11个监控字段】组装成一个字典；【共16个键】
    """
    def __init__(self):
        self.collect_time = None
        self.cpu_core = None
        self.current_cpu_used = None
        self.current_disk_used = None
        self.current_mem_used = None
        self.current_net_rx_used = None
        self.current_net_tx_used = None
        self.disk_size = None
        self.hostname = None
        self.id = None
        self.ip = None
        self.mem_size = None
        self.net_size = None
        #self.uuid = None
        self.week_cpu_p95_used = None
        self.week_mem_p95_used = None

# 把返回响应格式为api方式 【post过来的数据插入到数据库】
def host_metric_apiresp(result):
    '''
    :param kwargs:
    :return: 返回插入数据库的操作状态、待插入数、有效插入数
    '''
    operate_status, total_nums, insert_num, data = result

    resp = HostMetricResp()
    resp.operate_return = operate_status
    resp.record_num = total_nums
    resp.record_success_insert_num = insert_num

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp.to_json())

# 把返回格式化为api方式【通过get请求的数据】
def host_metric_getapiresp(result):
    '''
    :param kwargs:
    :return:
    '''
    resp = HostMetricGetResp()
    newlist = list(result)
    newlist.sort()
    print newlist
    newres = tuple(newlist)
    print "newres1=",newres
    print 'return len of dict = ',len(newres)
    logging.info()
    sres = [''.join(line.split(':',1)[1:]) for line in newres]
    resp.collect_time, resp.cpu_core, resp.current_cpu_used, resp.current_disk_used,\
    resp.current_mem_used, resp.current_net_rx_used, resp.current_net_tx_used,\
    resp.disk_size, resp.hostname, resp.id, resp.ip, resp.mem_size, resp.net_size,\
    resp.week_cpu_p95_used, resp.week_mem_p95_used  = sres
    print 'newres2=',newres
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp.to_json())