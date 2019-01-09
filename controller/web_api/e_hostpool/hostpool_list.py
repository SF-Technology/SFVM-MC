# coding=utf8
'''
    HOSTPOOL管理 - 列表
'''
# __author__ =  ""

from flask import request
from model.const_define import ErrorCode
import json_helper
from common_data_struct import hostpool_info, base_define
from model import hostpool
from service.s_user.user_service import get_user
from service.s_host import host_service as host_s
from service.s_dashboard.dashboard_service import get_cpu_mem_used
from service.s_net_area.net_area import NetAreaService as net_area_s
from service.s_ip.segment_service import SegmentService as ip_segment_s
from service.s_ip import ip_service
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
from service.s_instance import instance_filter
from config.default import INSTANCE_MAX_NUMS_IN_HOST


class HostPoolListResp(base_define.Base):

    def __init__(self):
        self.total = None
        self.rows = []


@login_required
def hostpool_list():

    params = {
        'page_size': request.values.get('page_size', 20),
        'page_no': request.values.get('page_no', 1),
    }

    total_nums, data = hostpool.user_hostpool_list(get_user()['user_id'], **params)

    resp = HostPoolListResp()
    resp.total = total_nums
    for i in data:
        _hostpool_info = hostpool_info.HostPoolInfo().init_from_db(i)
        _hostpool_info.hosts_nums = host_s.HostService().get_hosts_nums_of_hostpool(i['hostpool_id'])

        # 获取该集群下所有host的cpu、mem使用情况
        _all_host_num, _all_host_data = host_s.HostService().get_hosts_of_hostpool(i['hostpool_id'])
        # if _all_host_num > 0:
        #     _cpu_mem_used = get_cpu_mem_used(_all_host_data, i['hostpool_id'])
        #     _hostpool_info.cpu_nums = _cpu_mem_used['cpu_all']
        #     _hostpool_info.mem_nums = _cpu_mem_used['mem_all']
        #     _hostpool_info.cpu_used_per = _cpu_mem_used['cpu_used_per']
        #     _hostpool_info.mem_used_per = _cpu_mem_used['mem_used_per']
        #     _hostpool_info.mem_assign = _cpu_mem_used['assign_mem']
        #     _hostpool_info.mem_assign_per = _cpu_mem_used['assign_mem_per']
        #     _hostpool_info.available_create_vm_nums = _cpu_mem_used['available_create_vm_num']
        if _all_host_num > 0:

            # # 过滤超过50台虚拟机的物理机
            v_filter = instance_filter.instance_nums_filter(INSTANCE_MAX_NUMS_IN_HOST)
            _all_host_data = filter(v_filter, _all_host_data)
            if not _all_host_data:
                pass
            else:
                _cpu_mem_used = get_cpu_mem_used(_all_host_data, i['hostpool_id'])
                _hostpool_info.cpu_nums = _cpu_mem_used['cpu_all']
                _hostpool_info.mem_nums = _cpu_mem_used['mem_all']
                _hostpool_info.cpu_used_per = _cpu_mem_used['cpu_used_per']
                _hostpool_info.mem_used_per = _cpu_mem_used['mem_used_per']
                _hostpool_info.mem_assign = _cpu_mem_used['assign_mem']
                _hostpool_info.mem_assign_per = _cpu_mem_used['assign_mem_per']
                _hostpool_info.available_create_vm_nums = _cpu_mem_used['available_create_vm_num']
        _hostpool_info.available_ip_nums = __all_ip_available_num(i['datacenter_id'], i['net_area_id'])

        resp.rows.append(_hostpool_info)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp.to_json())


def __all_ip_available_num(dc_id, net_area_id=None):
    '''
        对于一个网络区域最大可使用ip个数以所有网段中ip个数最多的那个为准
    :param dc_id:
    :param net_area_id:
    :return:
    '''
    dc_ip_num = 0
    if not net_area_id:
        net_area_num, net_area_datas = net_area_s().get_net_area_datas_in_dc(dc_id)
        if net_area_num <= 0:
            return 0
        for one_net_area_data in net_area_datas:
            ip_num_list = []
            ip_segment_num, ip_segment_datas = ip_segment_s().get_segment_datas_in_net_area(one_net_area_data['id'])
            if ip_segment_num <= 0:
                continue
            for one_ip_segment in ip_segment_datas:
                ip_ret, ip_num = ip_service.get_available_ip_by_segment_id(one_ip_segment['id'])
                if ip_ret:
                    ip_num_list.append(ip_num)
            if len(ip_num_list) > 0:
                net_area_ip_num = max(ip_num_list)
                dc_ip_num += net_area_ip_num
    else:
        ip_num_list = []
        ip_segment_num, ip_segment_datas = ip_segment_s().get_segment_datas_in_net_area(net_area_id)
        if ip_segment_num <= 0:
            return 0
        for one_ip_segment in ip_segment_datas:
            ip_ret, ip_num = ip_service.get_available_ip_by_segment_id(one_ip_segment['id'])
            if ip_ret:
                ip_num_list.append(ip_num)
        if len(ip_num_list) > 0:
            net_area_ip_num = max(ip_num_list)
            dc_ip_num += net_area_ip_num
    return dc_ip_num
