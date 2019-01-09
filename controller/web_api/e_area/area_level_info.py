# coding=utf8
'''
    区域管理
'''
# __author__ =  ""

from model.const_define import ErrorCode
from common_data_struct import base_define, area_level_info
from service.s_area import area_service as area_s
import json_helper
from service.s_user.user_service import current_user_all_area_ids
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user


class ArealevelInfoResp(base_define.Base):

    def __init__(self):
        self.level_info = []


@login_required
def get_area_level_info():
    resp = ArealevelInfoResp()
    user_all_area_ids = current_user_all_area_ids()
    all_areas_nums, all_areas_data = area_s.AreaService().get_all_areas()

    parent_ids_list = []
    for i in all_areas_data:
        if i['parent_id'] != -1:
            parent_ids_list.append(i['parent_id'])
    # 去除重复的
    parent_ids_list = list(set(parent_ids_list))

    for i in all_areas_data:
        # 不显示有子区域的区域
        if i['id'] in parent_ids_list:
            continue

        # 只显示当前用户所属的区域
        if user_all_area_ids and i['id'] not in user_all_area_ids:
            continue

        _area = area_level_info.ArealevelInfo().init_from_db(i)
        if i['parent_id']:
            _parent = area_s.AreaService().get_area_info(i['parent_id'])
            if _parent:
                _area.area = _parent['displayname']
                _area.child_area = i['displayname']
            else:
                _area.area = i['displayname']
        else:
            _area.area = i['displayname']

        resp.level_info.append(_area)

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp.to_json())

