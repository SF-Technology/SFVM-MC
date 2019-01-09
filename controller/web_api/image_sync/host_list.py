# coding=utf8
'''
    image_sync host清单
'''
# __author__ =  ""




from service.s_hostpool import hostpool_service
from service.s_host import host_service as host_s
from service.s_area import area_service
from service.s_image_sync import image_sync_service as im_sy_s
from service.s_image_sync import image_sync_schedule as im_sy_sch
from common_data_struct import base_define, area_dq_init_info
from model.const_define import ErrorCode
import json_helper
import logging
from service.s_user.user_service import current_user_all_area_ids



class image_sync_host_list(base_define.Base):

    def __init__(self):
        self.area_ZB = []
        self.area_DQ = []




def image_sync_host():
    resp = image_sync_host_list()

    # area层级信息 - 总部
    area_ZB,area_DQ = v2v_esx_get_hostpool_info()
    if area_ZB != []:
        for single_area in area_ZB:
            hostpool_id = single_area['hostpool_id']
            params = {
                'WHERE_AND': {
                    "=": {
                        'isdeleted': '0',
                        'hostpool_id': hostpool_id
                    }
                },
            }
            host_data_list = host_s.HostService().query_data(**params)[1]
            single_area['host_data'] = host_data_list


    if area_DQ != []:
        for single_area in area_DQ:
            hostpool_id = single_area['hostpool_id']
            params = {
                'WHERE_AND': {
                    "=": {
                        'isdeleted': '0',
                        'hostpool_id': hostpool_id
                    }
                },
            }
            host_data_list = host_s.HostService().query_data(**params)[1]
            single_area['host_data'] = host_data_list


    resp.area_ZB =area_ZB
    resp.area_DQ=area_DQ
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp.to_json())



def v2v_esx_get_hostpool_info():
    '''
        获取层级信息
        机房 - 网络区域 - 集群
    :return:
    '''
    user_all_area_ids = current_user_all_area_ids()
    area_ZB = []
    area_DQ = []

    # area层级信息 - 总部
    area_zb_data = hostpool_service.v2v_get_level_info_hostpool_zb()
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
        area_ZB.append(i)

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
        area_DQ.append(_area_dq_info)

    return area_ZB,area_DQ


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


