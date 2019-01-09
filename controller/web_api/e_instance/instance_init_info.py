# coding=utf8
'''
    虚拟机管理 - 获取创建VM需要的所有数据
'''
# __author__ =  ""

import json_helper
from model.const_define import ErrorCode
from service.s_hostpool import hostpool_service
from service.s_host import host_service as host_s
from service.s_flavor import flavor_service
from service.s_image import image_service
from service.s_group import group_service
from service.s_area import area_service
from common_data_struct import base_define, flavor_init_info, image_init_info, group_info, area_dq_init_info
import logging
from service.s_user.user_service import current_user_all_area_ids, current_user_groups
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user


class InstanceInitInfoResp(base_define.Base):

    def __init__(self):
        self.area_ZB = []
        self.area_DQ = []
        self.flavors = []
        self.images_windows = []
        self.images_linux = []
        self.groups = []


@login_required
def instance_init_info():

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

    resp = InstanceInitInfoResp()
    user_all_area_ids = current_user_all_area_ids()

    # area层级信息 - 总部
    area_zb_data = hostpool_service.get_level_info_hostpool_zb()
    for i in area_zb_data:
        # 不显示不满足最少host数的集群
        if not _filter_least_host_num(i['hostpool_id'], i['least_host_num']):
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

    # flavor信息
    flavors_nums, flavors_data = flavor_service.FlavorService().get_all_flavors()
    for i in flavors_data:
        _flavor_info = flavor_init_info.FlavorInitInfo().init_from_db(i)
        resp.flavors.append(_flavor_info)

    # image信息 - windows
    images_windows_nums, images_windows_data = image_service.ImageService().get_all_images('windows')
    for i in images_windows_data:
        _image_windows_info = image_init_info.ImageInitInfo().init_from_db(i)
        resp.images_windows.append(_image_windows_info)

    # image信息 - linux
    images_linux_nums, images_linux_data = image_service.ImageService().get_all_images('linux')
    for i in images_linux_data:
        _image_linux_info = image_init_info.ImageInitInfo().init_from_db(i)
        resp.images_linux.append(_image_linux_info)

    # group信息
    user_groups = current_user_groups()
    user_group_ids_list = []
    is_super_group = False
    for _groups in user_groups:
        user_group_ids_list.append(_groups['id'])
        # 超级管理员组
        if _groups['name'] == "supergroup":
            is_super_group = True

    groups_params = {
        'WHERE_AND': {
            '=': {
                'isdeleted': '0'
            }
        },
    }
    groups_nums, groups_data = group_service.GroupService().query_data(**groups_params)
    for i in groups_data:
        # 管理员组的成员可以显示所有组，而非管理员组的只显示当前用户所在应用组
        if not is_super_group and i['id'] not in user_group_ids_list:
            continue

        _group_info = group_info.GroupInitInfo().init_from_db_1(i)
        resp.groups.append(_group_info)

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp.to_json())