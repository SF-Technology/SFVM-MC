# coding=utf8
'''
    机房管理
'''


from flask import request
from model.const_define import ErrorCode
import json_helper
from common_data_struct import base_define, datacenter_info
from model import datacenter
from service.s_user.user_service import get_user, current_user_all_area_ids
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user


class DatacenterListResp(base_define.Base):

    def __init__(self):
        self.total = None
        self.rows = []


@login_required
def datacenter_list():
    params = {
        'page_size': request.values.get('page_size', 20),
        'page_no': request.values.get('page_no', 1),
    }

    # 通过user_id，传回该user所拥有权限的所有datacenter list
    total_nums, data = datacenter.user_datacenter_list(get_user()['user_id'], current_user_all_area_ids(), **params)
    resp = DatacenterListResp()
    resp.total = total_nums
    for i in data:
        _datacenter_info = datacenter_info.DataCenterInfo().init_from_db(i)
        resp.rows.append(_datacenter_info)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp.to_json())