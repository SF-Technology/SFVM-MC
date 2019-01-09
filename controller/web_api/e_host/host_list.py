# coding=utf8
'''
    物理机管理
'''
# __author__ =  ""

from flask import request
from model.const_define import ErrorCode
import json_helper
from service.s_instance import instance_service as ins_s
from service.s_host import host_service as host_s
from service.s_host import host_schedule_service as host_s_s
from common_data_struct import base_define, host_info
from model import host
from service.s_user.user_service import get_user
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
import json
import threading

HOST_DATA_THREADINGLOCK = threading.Lock()


class HostListResp(base_define.Base):

    def __init__(self):
        self.total = None
        self.rows = []


def __get_host_info_multithreading(host_data, resp, num):
    '''
        多线程收集物理机详细信息
    :param host_data:
    :return:
    '''
    global INSTANCE_CREATE_THREADINGLOCK

    _host_info = host_info.HostInfo().init_from_db(host_data)
    _host_info.instance_nums = ins_s.get_instances_nums_in_host(host_data['host_id'])
    _host_info.mem_assign_per = host_s_s.get_host_mem_assign_percent(host_data)
    _host_info.num = num

    HOST_DATA_THREADINGLOCK.acquire()
    try:
        resp.rows.append(_host_info)
    finally:
        HOST_DATA_THREADINGLOCK.release()

    return


@login_required
def host_list():
    params = {
        'WHERE_AND': {
            '=': {
                'status': None
            },
            'like': {
                'name': None,
                'sn': None,
                'ip_address': None,
                'manage_ip': None
            },
            'in': {
                'id': None
            }
        },
        'search_in_flag': 0,
        'page_size': request.values.get('page_size'),
        'page_no': request.values.get('page_no'),
    }

    search = request.values.get('search')
    if search:
        json_search = json.loads(search)
        name = json_search.get('name')
        if name:
            params['WHERE_AND']['like']['name'] = '%' + name + '%'

        sn = json_search.get('sn')
        if sn:
            params['WHERE_AND']['like']['sn'] = '%' + sn + '%'

        ip_address = json_search.get('ip_address')
        if ip_address:
            params['WHERE_AND']['like']['ip_address'] = '%' + ip_address + '%'

        manage_ip = json_search.get('manage_ip')
        if manage_ip:
            params['WHERE_AND']['like']['manage_ip'] = '%' + manage_ip + '%'

        status = json_search.get('status')
        if status:
            params['WHERE_AND']['=']['status'] = status

        hostpool_name = json_search.get('hostpool_name')
        if hostpool_name:
            params['search_in_flag'] = 1
            # 先模糊查询hostpool name对应的HOST ID
            search_hostpool_data = host_s.get_hosts_by_fuzzy_hostpool_name(hostpool_name)
            host_id_list = [i['host_id'] for i in search_hostpool_data]
            if host_id_list:
                params['WHERE_AND']['in']['id'] = tuple(host_id_list)

    total_nums, data = host.user_host_list(get_user()['user_id'], **params)
    resp = HostListResp()
    resp.total = total_nums

    threads = []
    num = 0
    for i in data:
        num += 1
        host_thread = threading.Thread(target=__get_host_info_multithreading,
                                       args=(i, resp, num))
        threads.append(host_thread)
        host_thread.start()

    # 判断多线程是否结束
    for t in threads:
        t.join()

    host_datas = resp.rows
    host_datas = sorted(host_datas, key=lambda h: h.num)
    resp.rows = host_datas

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp.to_json())
