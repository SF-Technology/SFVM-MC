# coding=utf8
'''
    区域管理
'''
# __author__ =  ""

from flask import request
from model.const_define import ErrorCode
from service.s_area import area_service
from service.s_datacenter import datacenter_service
from service.s_user.user_service import current_user_all_area_ids
import json_helper
from common_data_struct import base_define, area_info
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user


class AreaListResp(base_define.Base):

    def __init__(self):
        self.total = None
        self.rows = []


@login_required
def area_list():
    '''
        request
    :return:
    '''
    resp = AreaListResp()
    user_areas_list = current_user_all_area_ids()
    if not user_areas_list:
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp.to_json())

    params = {
        'WHERE_AND': {
            'in': {
                'id': user_areas_list
            },
            '=': {
                'parent_id': -1,
                'isdeleted': '0'
            }
        },
        'ORDER': [
            ['id', 'desc'],
        ],
        'PAGINATION': {
            'page_size': request.values.get('page_size', 20),
            'page_no': request.values.get('page_no', 1),
        }
    }
    total_nums, data = area_service.AreaService().query_data(**params)

    resp.total = total_nums
    for i in data:
        _area_info = area_info.AreaInfo().init_from_db(i)
        _area_info.child_areas_nums = area_service.AreaService().get_child_areas_nums(i['id'])
        _area_info.datacenter_nums = datacenter_service.DataCenterService().get_datacenter_nums_in_area(i['id'])
        resp.rows.append(_area_info)

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp.to_json())
