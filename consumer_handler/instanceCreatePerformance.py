# !/usr/bin/env python2.7
# -*- coding:utf-8 -*-
#

#   Date    :   2018/11/09
#   Desc    :   vishi调用web平台性能接口
from helper import json_helper
from service.s_ip import ip_lock_service

succeed_http_code = ['200', '500']


def init_env():
    import sys
    import os
    reload(sys)
    sys.setdefaultencoding('utf-8')
    file_basic_path = os.path.dirname(os.path.abspath(__file__))
    print file_basic_path
    basic_path = file_basic_path[0:-17]
    os.environ["BASIC_PATH"] = basic_path  # basic path 放到全局的一个变量当中去
    sys.path.append(basic_path)
    sys.path.append(basic_path + '/config')
    sys.path.append(basic_path + '/helper')
    sys.path.append(basic_path + '/lib')
    sys.path.append(basic_path + '/model')
    sys.path.append(basic_path + '/controller')
    sys.path.append(basic_path + '/service')
    print sys.path

init_env()






def instance_performance(msg):
    '''虚拟机创建的性能检测接口'''
    msg = json_helper.read(msg)
    data = msg.get('data')
    table_name = data.get("table_name")
    if table_name != "performance_data":
        return  0
    update_data = {
        "istraceing": "1"
    }
    where_data = {
        "table_name": "performance_data"
    }
    ip_lock_service.IpLockService().update_ip_lock_info(update_data, where_data)
    return  0


