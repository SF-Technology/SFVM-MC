# -*- coding:utf-8 -*-
# __author__ =  ""

# from flask.ext.httpauth import HTTPBasicAuth
from flask_httpauth import HTTPBasicAuth
from service.s_user import user_service as user_s
from helper import json_helper
from model.const_define import VsJobStatus, DataCenterTypeTransform, DataCenterTypeForVishnu
from model import hostpool
from config.default import INSTANCE_MAX_NUMS_IN_HOST
from service.s_datacenter.datacenter_service import DataCenterService as dc_s
from service.s_ip.segment_service import SegmentService as ip_segment_s
from service.s_ip import ip_service
from service.s_host import host_service as host_s
from service.s_dashboard.dashboard_service import get_hostpool_mem_cpu_disk_used
from service.s_net_area.net_area import NetAreaService as net_area_s
from service.s_net_area.net_area import get_netarea_info_by_name
from service.s_instance import instance_filter
import json
from flask import request
import logging
from controller.web_api.ip_filter_decorator import ip_filter_from_other_platform

auth_api_user = HTTPBasicAuth()


@ip_filter_from_other_platform
@auth_api_user.login_required
def hostpool_capacity_to_other_platform():
    '''
        外部平台获取kvm物理集群资源信息
    :return:
    '''
    data_from_vishnu = request.data
    logging.info(data_from_vishnu)
    data_requset = json_helper.loads(data_from_vishnu)
    # data_requset = request.values.get("data")
    # data_requset = json.loads(data_requset)
    datacenter = data_requset['datacenter']
    env = data_requset['env']
    vcpu = data_requset['vcpu']
    mem_mb = data_requset['mem_MB']
    disk_gb = data_requset['disk_GB']
    page_num = data_requset['currentPage']
    page_size = data_requset['pageSize']
    net_area = data_requset['net_area']

    all_available_vm_count = 0

    # 获取指定机房详细信息存入dc_list列表
    dc_list = []
    dc_ret, dc_datas = dc_s().get_all_datacenters_by_name(datacenter)
    if not dc_ret:
        return json_helper.format_api_resp_msg_to_vishnu_resource(job_status=VsJobStatus.FAILED, detail='无法找到指定机房信息')
    for one_dc_data in dc_datas:
        dc_type = DataCenterTypeTransform.MSG_DICT.get(int(one_dc_data['dc_type']))
        if env.lower() == dc_type:
            dc_detail = {
                "dc_id": one_dc_data['id'],
                "dc_name": one_dc_data['name'],
                "dc_area_id": one_dc_data['area_id'],
                "dc_type": DataCenterTypeTransform.MSG_DICT.get(int(one_dc_data['dc_type'])),
            }
            dc_list.append(dc_detail)

    if len(dc_list) != 1:
        return json_helper.format_api_resp_msg_to_vishnu_resource(job_status=VsJobStatus.FAILED,
                                                                  detail='无法找到机房中对应环境%s的信息' % env)

    # 查询指定环境、机房下的网络区域信息
    if net_area:
        net_area_info = get_netarea_info_by_name(str(DataCenterTypeForVishnu.TYPE_DICT[env]), datacenter, net_area)
        if net_area_info:
            available_ip_count = __all_ip_available_num(dc_list[0]['dc_id'], net_area_info['id'])
        else:
            available_ip_count = 0
    else:
        available_ip_count = __all_ip_available_num(dc_list[0]['dc_id'])

    # 如果net_area为空，获取指定机房下所有集群信息。否则查询指定机房指定网络区域下的集群信息
    hostpool_num, hostpool_infos = hostpool.get_datacenter_hostpool_list(dc_list[0]['dc_id'], net_area, page_num,
                                                                         page_size)

    if hostpool_num <= 0:
        params = {
            "currentPage": int(page_num),
            "pageSize": int(page_size),
            "total": 0,
            "available_vm_count": all_available_vm_count,
            "available_ip_count": available_ip_count,
            "cluster_datas": []
        }
        return json_helper.format_api_resp_msg_to_vishnu_resource(job_status=VsJobStatus.SUCCEED,
                                                                  detail=params)
    capacity_detail = []

    for per_hostpool_info in hostpool_infos:
        if not per_hostpool_info['cluster_id']:
            pass
        else:
            # 查找每一个集群使用情况，以及集群中每一台物理机使用情况
            _all_host_num, _all_host_data = host_s.HostService().get_hosts_of_hostpool(per_hostpool_info['cluster_id'])
            if _all_host_num > 0:
                # # 过滤超过50台虚拟机的物理机
                v_filter = instance_filter.instance_nums_filter(INSTANCE_MAX_NUMS_IN_HOST)
                hosts = filter(v_filter, _all_host_data)
                if not hosts:
                    pass
                else:
                    _host_pool_cpu_mem_used = get_hostpool_mem_cpu_disk_used(hosts, mem_mb, disk_gb
                                                                             , per_hostpool_info['cluster_id'])
                    host_pool_params = {
                        "cluster_id": per_hostpool_info['cluster_id'],
                        "cluster_app_code": per_hostpool_info['cluster_app_code'],
                        "cluster_type": per_hostpool_info["cluster_type"],
                        "cluster_name": per_hostpool_info['cluster_name'],
                        "env": env,
                        "datacenter": datacenter,
                        "net_area": per_hostpool_info['net_area_name'],
                        "available_host_num": _host_pool_cpu_mem_used['all_available_host_num'],
                        "total_capacity": {
                            "mem_mb": _host_pool_cpu_mem_used['mem_all'],
                            "vcpu": _host_pool_cpu_mem_used['cpu_all'],
                            "disk_gb": _host_pool_cpu_mem_used['disk_all']
                        },
                        "assign_capacity": {
                            "mem_mb": _host_pool_cpu_mem_used['mem_assign'],
                            "vcpu": _host_pool_cpu_mem_used['cpu_assign'],
                            "disk_gb": _host_pool_cpu_mem_used['disk_assign']
                        },
                        "available_capacity": {
                            "mem_mb": _host_pool_cpu_mem_used['mem_available'],
                            "vcpu": _host_pool_cpu_mem_used['cpu_unused'],
                            "disk_gb": _host_pool_cpu_mem_used['disk_available'],
                            "vm_count": _host_pool_cpu_mem_used['available_create_vm'],
                            "ip_count": __all_ip_available_num(dc_list[0]['dc_id'], per_hostpool_info['net_area_id'])
                        },
                        "performance": {
                            "mem_usage": _host_pool_cpu_mem_used['mem_used_per'],
                            "vcpu_usage": _host_pool_cpu_mem_used['cpu_used_per'],
                            "disk_usage": _host_pool_cpu_mem_used['disk_used_per']
                        },
                        "host_datas": _host_pool_cpu_mem_used['all_host_performance_datas']
                    }
                    capacity_detail.append(host_pool_params)
                    all_available_vm_count += _host_pool_cpu_mem_used['available_create_vm']
    # TODO 维石之后取消
    # net_set = []
    # delete_set = []
    #
    # for index, each in enumerate(capacity_detail):
    #     net_area = each["net_area"]
    #     if net_area in net_set:
    #         delete_set.append(each)
    #     else:
    #         net_set.append(net_area)
    # for delete_each in delete_set:
    #     capacity_detail.remove(delete_each)
    # TODO 结束

    params = {
        "currentPage": int(page_num),
        "pageSize": int(page_size),
        "total": len(capacity_detail),
        "available_vm_count": all_available_vm_count,
        "available_ip_count": available_ip_count,
        "cluster_datas": capacity_detail
    }

    return json_helper.format_api_resp_msg_to_vishnu_resource(job_status=VsJobStatus.SUCCEED,
                                                              detail=params)


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
