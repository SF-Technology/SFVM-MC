# coding=utf8
'''
    收集host数据、状态
'''


from service.s_host import host_service as host_s
from collect_data.base import check_collect_time_out_interval
from lib.vrtManager.connection import CONN_TCP, CONN_SSH, connection_manager
from model.const_define import HostStatus, HostLibvirtdStatus
from helper.time_helper import get_datetime_str
import logging


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
            ['host_collect_time', 'asc']
        ],
    }
    hosts_list = []
    hosts_nums, hosts_data = host_s.HostService().query_data(**params)
    for _host in hosts_data:
        if check_collect_time_out_interval(_host['host_collect_time'], interval) and len(hosts_list) <= nums:
            hosts_list.append(_host)

    return hosts_list


def collect_host_data(host_ip):
    result = connection_manager.host_is_up(CONN_TCP, host_ip)
    # host_status = connection_manager.host_is_up(CONN_SSH, host_ip)
    if result is True:
        status = HostStatus.RUNNING
        libvirtd_status = HostLibvirtdStatus.NORMAL
    elif result is "error(111, 'Connection refused')" or result is "timeout('timed out',)":
        status = HostStatus.ERROR
        libvirtd_status = HostLibvirtdStatus.UNUSUAL
    else:
        status = HostStatus.ERROR
        libvirtd_status = HostLibvirtdStatus.UNUSUAL

    # 更新收集时间
    _update_data_h = {
        'host_collect_time': get_datetime_str(),
        'status': status,
        'libvirtd_status': libvirtd_status
    }
    _where_data_h = {
        'ipaddress': host_ip,
        'isdeleted': '0'
    }
    ret_h = host_s.HostService().update_host_info(_update_data_h, _where_data_h)
    if ret_h != 1:
        logging.error('update collect time error when collect host data, update_data:%s, where_data:%s',
                      _update_data_h, _where_data_h)

    print 'end colletc host ' + host_ip + ' data at ' + get_datetime_str()
    print '*' * 40
    return 0
