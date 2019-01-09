# coding=utf8
'''
    V2V功能 - 转化openstack虚拟机时所需参数
'''
# __author__ = 'anke'

import json_helper
from model.const_define import ErrorCode
from service.s_hostpool import hostpool_service
from service.s_host import host_service as host_s
from service.s_flavor import flavor_service
from service.s_group import group_service
from common_data_struct import base_define, flavor_init_info, group_info
import logging


class V2v_0p_InitInfoResp(base_define.Base):

    def __init__(self):
        self.area = []
        self.flavors = []
        self.groups = []
        self.segment = []


def v2v_op_init_info():
    resp = V2v_0p_InitInfoResp()

    # area层级信息 - 总部
    area_data = hostpool_service.get_level_info_hostpool_cs()
    for i in area_data:
        if not _filter_least_host_num(i['hostpool_id'], i['least_host_num']):
           continue
        resp.area.append(i)



    # flavor信息
    flavors_nums, flavors_data = flavor_service.FlavorService().get_all_flavors()
    for i in flavors_data:
        _flavor_info = flavor_init_info.FlavorInitInfo().init_from_db(i)
        resp.flavors.append(_flavor_info)


    # segment信息
    resp.segment= []
    #     {"env": "SIT", "seg": "10.202.26.0"},
    #     {"env": "SIT", "seg": "10.202.34.0"},
    #     {"env": "SIT", "seg": "10.202.50.0"},
    #     {"env": "SIT", "seg": "10.202.32.0"},
    #     {"env": "SIT", "seg": "10.202.84.0"},
    #     {"env": "SIT", "seg": "10.202.86.0"},
    #     {"env": "SIT", "seg": "10.202.42.0"},
    #     {"env": "SIT", "seg": "10.202.24.0"},
    #     {"env": "SIT", "seg": "10.202.44.0"},
    #     {"env": "SIT", "seg": "10.202.91.0"},
    #     {"env": "SIT", "seg": "10.202.16.0"},
    #     {"env": "SIT", "seg": "10.202.40.0"},
    #     {"env": "SIT", "seg": "10.202.98.0"},
    #     {"env": "SIT", "seg": "10.202.54.0"},
    #     {"env": "SIT", "seg": "10.202.38.0"},
    #     {"env": "SIT", "seg": "10.202.90.0"},
    #     {"env": "SIT", "seg": "10.202.52.0"},
    #     {"env": "SIT", "seg": "10.202.36.0"},
    #     {"env": "SIT", "seg": "10.202.94.0"},
    #     {"env": "SIT", "seg": "10.202.99.0"},
    #     {"env": "DEV", "seg": "10.202.10.0"},
    #     {"env": "DEV", "seg": "10.202.11.0"},
    #     {"env": "DEV", "seg": "10.202.12.0"},
    #     {"env": "DEV", "seg": "10.202.125.0"},
    #     {"env": "DEV", "seg": "10.202.23.0"},
    #     {"env": "DEV", "seg": "10.202.13.0"},
    #     {"env": "DEV", "seg": "10.202.14.0"},
    #     {"env": "DEV", "seg": "10.202.15.0"},
    #     {"env": "DEV", "seg": "10.202.4.0"},
    #     {"env": "DEV", "seg": "10.202.5.0"},
    #     {"env": "DEV", "seg": "10.202.6.0"},
    #     {"env": "DEV", "seg": "10.202.7.0"},
    #     {"env": "DEV", "seg": "10.202.8.0"},
    #     {"env": "DEV", "seg": "10.202.9.0"}
    # ]


    # group信息
    groups_params = {
        'WHERE_AND': {
            '=': {
                'isdeleted': '0'
            }
        },
    }
    groups_nums, groups_data = group_service.GroupService().query_data(**groups_params)
    for i in groups_data:
        _group_info = group_info.GroupInitInfo().init_from_db_1(i)
        resp.groups.append(_group_info)

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp.to_json())


def _filter_least_host_num(hostpool_id, least_host_num):
    '''
        过滤掉不满足最少host数的集群
    :param hostpool_id:
    :param least_host_num:
    :return:
    '''
    # 获取主机列表
    all_hosts_nums, all_hosts_data = host_s.HostService().get_hosts_of_hostpool(hostpool_id)
    if all_hosts_nums < least_host_num or all_hosts_nums < 1:
        logging.info('filter hostpool %s that not enough resource when get create init info', hostpool_id)
        return False
    return True