# -*- coding:utf-8 -*-
# __author__ =  ""

import os
# from flask.ext.httpauth import HTTPBasicAuth
from flask_httpauth import HTTPBasicAuth
from helper.log_helper import add_timed_rotating_file_handler
from flask import request
import logging
from helper import json_helper
from helper.time_helper import get_datetime_str
# from controller.other_api.e_host_metric.host_metric_manage import flush_host_perform_data_to_db
from service.s_host import host_service as host_s
from service.s_user import user_service as user_s
from model.const_define import ErrorCode

auth_api_user = HTTPBasicAuth()


# 传参格式化
# def _msg_format(host_ip='', host_name='', cpu_core='', mem_size='', disk_size='', net_size='', \
#                 current_cpu_used='', current_mem_used='', current_disk_used='', week_cpu_p95_used='', \
#                 week_mem_p95_used='', current_net_rx_used='', current_net_tx_used='', start_time='',
#                 libvirt_port='', libvirt_status='', images=''):
#     collect_time = get_datetime_str()
#     msg = {'params': {
#         'cpu_core': {
#             "host_ip": host_ip,
#             "host_name": host_name,
#             "collect_time": collect_time,
#             "data_value": cpu_core
#         },
#         'mem_size': {
#             "host_ip": host_ip,
#             "host_name": host_name,
#             "collect_time": collect_time,
#             "data_value": mem_size
#         },
#         'disk_size': {
#             "host_ip": host_ip,
#             "host_name": host_name,
#             "collect_time": collect_time,
#             "data_value": disk_size
#         },
#         'net_size': {
#             "host_ip": host_ip,
#             "host_name": host_name,
#             "collect_time": collect_time,
#             "data_value": net_size
#         },
#         'current_cpu_used': {
#             "host_ip": host_ip,
#             "host_name": host_name,
#             "collect_time": collect_time,
#             "data_value": current_cpu_used
#         },
#         'current_mem_used': {
#             "host_ip": host_ip,
#             "host_name": host_name,
#             "collect_time": collect_time,
#             "data_value": current_mem_used
#         },
#         'current_disk_used': {
#             "host_ip": host_ip,
#             "host_name": host_name,
#             "collect_time": collect_time,
#             "data_value": current_disk_used
#         },
#         'week_cpu_p95_used': {
#             "host_ip": host_ip,
#             "host_name": host_name,
#             "collect_time": collect_time,
#             "data_value": week_cpu_p95_used
#         },
#         'week_mem_p95_used': {
#             "host_ip": host_ip,
#             "host_name": host_name,
#             "collect_time": collect_time,
#             "data_value": week_mem_p95_used
#         },
#         'current_net_rx_used': {
#             "host_ip": host_ip,
#             "host_name": host_name,
#             "collect_time": collect_time,
#             "data_value": current_net_rx_used
#         },
#         'current_net_tx_used': {
#             "host_ip": host_ip,
#             "host_name": host_name,
#             "collect_time": collect_time,
#             "data_value": current_net_tx_used
#         },
#         'start_time': {
#             "host_ip": host_ip,
#             "host_name": host_name,
#             "collect_time": collect_time,
#             "data_value": start_time
#         },
#         'libvirt_port': {
#             "host_ip": host_ip,
#             "host_name": host_name,
#             "collect_time": collect_time,
#             "data_value": libvirt_port
#         },
#         'libvirt_status': {
#             "host_ip": host_ip,
#             "host_name": host_name,
#             "collect_time": collect_time,
#             "data_value": libvirt_status
#         },
#         'images': {
#             "host_ip": host_ip,
#             "host_name": host_name,
#             "collect_time": collect_time,
#             "data_value": images
#         },
#     }
#     }
#     return msg


# 日志格式化
def _init_log(service_name):
    log_basic_path = os.path.dirname(os.path.abspath(__file__))[0:-25]
    log_name = log_basic_path + 'log/' + str(service_name) + '.log'
    add_timed_rotating_file_handler(log_name, logLevel='ERROR')


@auth_api_user.login_required
def host_perform_data_to_db():
    '''
      此函数用于将物理机上报上来的性能数据写入数据库
    :return:
    '''
    data_from_host = request.data
    data = json_helper.loads(data_from_host)

    if not data or not data['ip']:
        # 物理机性能数据中ip为空，不做任何操作
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='无法获取上传性能数据中的物理机ip信息，录入性能数据失败')

    # ret_msg = _msg_format(host_ip=data['ip'], host_name=data['hostname'], cpu_core=data['cpu_core'],
    #                       mem_size=data['mem_size'], disk_size=data['disk_size'], net_size=data['net_size'],
    #                       current_cpu_used=data['current_cpu_used'],
    #                       current_mem_used=data['current_mem_used'],
    #                       current_disk_used=data['current_disk_used'],
    #                       week_cpu_p95_used=data['week_cpu_p95_used'],
    #                       week_mem_p95_used=data['week_mem_p95_used'],
    #                       current_net_rx_used=data['current_net_rx_used'],
    #                       current_net_tx_used=data['current_net_tx_used'],
    #                       start_time=data['start_time'],
    #                       libvirt_port=data['libvirt_port'],
    #                       libvirt_status=data['libvirt_status'],
    #                       images=data['images'])
    # 更新host表
    __update_host_table(data['ip'], data['ostype'], data['cpu_core'], data['mem_size'], data['disk_size'],
                        data['net_size'], data['current_cpu_used'], data['current_mem_used'], data['current_disk_used'],
                        data['week_cpu_p95_used'], data['week_mem_p95_used'], data['current_net_rx_used'],
                        data['current_net_tx_used'], data['start_time'], data['libvirt_port'], data['images'],
                        data['libvirt_status'])
    # flush_host_perform_data_to_db(datadict=ret_msg)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, msg='%s：录入性能数据成功' % data['ip'])


# 操作数据库host表更新host_performance_collect_time、ostype字段
def __update_host_table(host_ip, ostype, cpu_core, mem_size, disk_size, net_size, current_cpu_used, current_mem_used,
                        current_disk_used, week_cpu_p95_used, week_mem_p95_used, current_net_rx_used, current_net_tx_used,
                        start_time, libvirt_port, images, libvirt_status):
    _update_data_h = {
        'host_performance_collect_time': get_datetime_str(),
        'ostype': ostype,
        'cpu_core': cpu_core,
        'mem_size': mem_size,
        'disk_size': disk_size,
        'net_size': net_size,
        'current_cpu_used': current_cpu_used,
        'current_mem_used': current_mem_used,
        'current_disk_used': current_disk_used,
        'week_cpu_p95_used': week_cpu_p95_used,
        'week_mem_p95_used': week_mem_p95_used,
        'current_net_rx_used': current_net_rx_used,
        'current_net_tx_used': current_net_tx_used,
        'start_time': start_time,
        'libvirt_port': libvirt_port,
        'images': images,
        'libvirt_status': libvirt_status
    }
    _where_data_h = {
        'ipaddress': host_ip,
        'isdeleted': '0'
    }
    host_s.HostService().update_host_info(_update_data_h, _where_data_h)
    return 'done'


@auth_api_user.verify_password
def verify_api_user_pwd(username_or_token, password):
    if not username_or_token:
        return False
    api_user = user_s.verify_api_auth_token(username_or_token)
    if not api_user:
        api_user = user_s.UserService().get_user_info_by_user_id(username_or_token)
        if not api_user or not user_s.verify_password(password, api_user['password']):
            return False
        if api_user['auth_type'] != 2:
            return False
    elif api_user['auth_type'] != 2:
        return False
    return True
