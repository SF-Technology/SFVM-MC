# -*- coding:utf-8 -*-
# __author__ =  ""
'''
    KVM平台公共信息查询接口--用于外部接口获取kvm平台公开的应用数据
'''

import json_helper
from model.const_define import ErrorCode
from service.s_hostpool import hostpool_service
from service.s_host import host_service as host_s
from service.s_group import group_service
from service.s_area import area_service
from service.s_user import user_service as user_s
from common_data_struct import base_define, group_info, area_dq_init_info
import logging
from service.s_user.user_service import current_user_groups
# from flask.ext.httpauth import HTTPBasicAuth
from flask_httpauth import HTTPBasicAuth
from flask import request

auth_api_user = HTTPBasicAuth()


class KvmInfoResp(base_define.Base):

    def __init__(self):
        self.area_ZB = []
        self.area_DQ = []
        self.groups = []


@auth_api_user.login_required
def kvm_common_info():

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
            logging.info('filter hostpool %s that has no least host nums %s when get create init info',
                         hostpool_id, least_host_num)
            return False
        return True

    def _filter_no_segment_info(hostpool_id):
        '''
            过滤掉没有网段信息的集群
        :param hostpool_id:
        :return:
        '''
        segments_list = hostpool_service.get_segment_info(hostpool_id)
        if not segments_list:
            logging.error('filter hostpool %s that has no segment info when get create init info', hostpool_id)
            return False
        return True

    data_from_api = request.data
    data_requset = json_helper.loads(data_from_api)
    user_id = data_requset['userId']

    resp = KvmInfoResp()
    user_all_area_ids = user_s.user_all_area_ids_by_userid(user_id)

    # area层级信息 - 总部
    area_zb_data = hostpool_service.get_level_info_hostpool_zb()
    for i in area_zb_data:
        # 不显示不满足最少host数的集群
        if not _filter_least_host_num(i['hostpool_id'], i['least_host_num']):
            continue

        # 不显示没有负载均衡网络的区域
        if "LoadBalance" not in i['net_area_name']:
            continue

        # 不显示没有网段信息的集群
        if not _filter_no_segment_info(i['hostpool_id']):
            continue

        # 只显示当前用户所属的区域
        if user_all_area_ids and i['area_id'] not in user_all_area_ids:
            continue
        resp.area_ZB.append(i)

    # area层级信息 - 地区
    area_dq_data = hostpool_service.get_level_info_hostpool_dq()
    for i in area_dq_data:
        # 不显示不满足最少host数的集群
        if not _filter_least_host_num(i['hostpool_id'], i['least_host_num']):
            continue

        # 不显示没有负载均衡网络的区域
        if "LoadBalance" not in i['net_area_name']:
            continue

        # 不显示没有网段信息的集群
        if not _filter_no_segment_info(i['hostpool_id']):
            continue

        # 只显示当前用户所属的区域
        if user_all_area_ids and i['area_id'] not in user_all_area_ids:
            continue

        _area_dq_info = area_dq_init_info.AreaDQInitInfo().init_from_db(i)
        # 表示有父区域
        if i['parent_id']:
            _parent_info = area_service.AreaService().get_area_info(i['parent_id'])
            if _parent_info:
                _area_dq_info.area_name = _parent_info['displayname']
                _area_dq_info.child_area_name = i['area_name']
            else:
                # 有父区域ID但没有相应信息，则当做没有父区域
                _area_dq_info.area_name = i['area_name']
        else:
            _area_dq_info.area_name = i['area_name']
        resp.area_DQ.append(_area_dq_info)

    # group信息
    user_groups = user_s.current_user_groups_by_userid(user_id)
    user_group_ids_list = []
    is_middleware_admin_group = False
    for _groups in user_groups:
        user_group_ids_list.append(_groups['id'])
        # 中间件管理员组，这里后期要注意，如果中间件管理员组id不为2，则识别不出用户是否是中间件管理员组
        if _groups['id'] == 2:
            is_middleware_admin_group = True

    groups_params = {
        'WHERE_AND': {
            '=': {
                'isdeleted': '0'
            }
        },
    }
    groups_nums, groups_data = group_service.GroupService().query_data(**groups_params)
    for i in groups_data:
        # 中间件管理员组可以显示所有组，而非管理员组的只显示当前用户所在应用组
        if not is_middleware_admin_group and i['id'] not in user_group_ids_list:
            continue

        _group_info = group_info.GroupInitInfo().init_from_db_1(i)
        resp.groups.append(_group_info)

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp.to_json())


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
