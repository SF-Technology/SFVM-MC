# -*- coding:utf-8 -*-

import os
import paramiko
import logging
import time
import json
import threading

import env
env.init_env()

from helper.log_helper import add_timed_rotating_file_handler
from helper.encrypt_helper import decrypt
from service.s_host import host_service as host_s
# from controller.other_api.e_host_metric.host_metric_manage import flush_host_perform_data_to_db
from helper.time_helper import get_datetime_str, datetime_to_timestamp, get_timestamp
from helper.encrypt_helper import decrypt
from collect_data.base import check_collect_time_out_interval
from config.default import HOST_PERFORMANCE_COLLECT_INTERVAL, HOST_PERFORMANCE_COLLECT_WORK_INTERVAL, \
    HOST_PERFORMANCE_COLLECT_NUMS, GET_HOST_PERFORMANCE_USER, GET_HOST_PERFORMANCE_PWD


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
    log_basic_path = os.path.dirname(os.path.abspath(__file__))[0:-17]
    log_name = log_basic_path + 'log/' + str(service_name) + '.log'
    add_timed_rotating_file_handler(log_name, logLevel='ERROR')


# 将每台虚拟机起一个线程获取性能文件并将数据写入数据库
def host_perform_multithreading(host_ip, host_ostype):
    user = GET_HOST_PERFORMANCE_USER
    passwd = decrypt(GET_HOST_PERFORMANCE_PWD)
    port = 22
    try:
        # 从远端拷贝文件到本地
        t = paramiko.Transport((host_ip, port))
        t.connect(username=user, password=passwd)
        sftp = paramiko.SFTPClient.from_transport(t)
        remotepath = '/tmp/' + host_ip
        localpath = '/app/hostinfo/' + host_ip
        sftp.get(remotepath, localpath)
        t.close()
        logging.info("host " + host_ip + " performance file get success")
    except Exception:
        logging.error("host " + host_ip + " connection error")
        update_host_table_time(host_ip)
        return

    try:
        # 将取回来性能数据入库
        ftime = os.path.getmtime("/app/hostinfo/%s" % host_ip)
        current_time = time.time()
        if (current_time - ftime) > 300:
            # 主机状态文件更新时间大于5分钟认为过期，不更新数据库信息
            pass
        else:
            with open("/app/hostinfo/%s" % host_ip, 'r') as f:
                data = json.load(f)
                if data['collect_time']:
                    collect_timestamp = time.mktime(time.strptime(data['collect_time'],'%Y-%m-%d %H:%M:%S'))
                    if get_timestamp() - collect_timestamp > 300:
                        return
                else:
                    return

                # ret_msg = _msg_format(host_ip=host_ip, host_name=data['hostname'], cpu_core=data['cpu_core'],
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
                update_host_table(host_ip, data['ostype'])
                # flush_host_perform_data_to_db(datadict=ret_msg)

    except:
        # 文件物理机信息不存在，不更新数据库信息
        update_host_table_time(host_ip)
        pass
    return


# 操作数据库host表更新host_performance_collect_time、ostype字段
def update_host_table(host_ip, ostype):
    _update_data_h = {
        'host_performance_collect_time': get_datetime_str(),
        'ostype': ostype
    }
    _where_data_h = {
        'ipaddress': host_ip,
        'isdeleted': '0'
    }
    ret_h = host_s.HostService().update_host_info(_update_data_h, _where_data_h)
    if ret_h != 1:
        logging.error('update collect time first error when collect host data, update_data:%s, where_data:%s',
                      _update_data_h, _where_data_h)
    return 'done'


# 操作数据库host表更新host_performance_collect_time字段
def update_host_table_time(host_ip):
    _update_data_h = {
        'host_performance_collect_time': get_datetime_str(),
    }
    _where_data_h = {
        'ipaddress': host_ip,
        'isdeleted': '0'
    }
    ret_h = host_s.HostService().update_host_info(_update_data_h, _where_data_h)
    if ret_h != 1:
        logging.error('update collect time error when collect host data, update_data:%s, where_data:%s',
                      _update_data_h, _where_data_h)
    return 'done'


# 获取满足条件host列表
def get_collect_hosts(interval=180, nums=20):
    '''
        获取前20个上次收集时间最久远并且超过了时间间隔的host
    :param interval:
    :param nums:
    :return:
    '''
    params = {
        'WHERE_AND': {
            '!=': {
                'isdeleted': '1',
                'status': '1'
            },
        },
        'ORDER': [
            ['host_performance_collect_time', 'asc']
        ],
    }
    hosts_list = []
    hosts_nums, hosts_data = host_s.HostService().query_data(**params)
    for _host in hosts_data:
        if check_collect_time_out_interval(_host['host_performance_collect_time'], interval) and len(hosts_list) <= nums:
            hosts_list.append(_host)

    return hosts_list


# 依次对db表中host取性能数据文件
def get_host_perform():
    threads = []
    hosts_data = get_collect_hosts(interval=HOST_PERFORMANCE_COLLECT_INTERVAL, nums=HOST_PERFORMANCE_COLLECT_WORK_INTERVAL)
    if not hosts_data:
        print 'no collect host now, please wait'
        # 任务休息
        time.sleep(HOST_PERFORMANCE_COLLECT_NUMS)
    for _host in hosts_data:
        host_ip = _host['ipaddress']
        host_ostype = _host['ostype']
        host_thread = threading.Thread(target=host_perform_multithreading,
                                       args=(host_ip, host_ostype,))
        threads.append(host_thread)
        host_thread.start()

        # 判断多线程是否结束
    for t in threads:
        t.join()
    return 0


if __name__ == '__main__':
    _init_log('get_host_performance')
    while True:
        get_host_perform()


