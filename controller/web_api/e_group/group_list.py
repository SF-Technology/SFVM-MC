# coding=utf8
'''
    GROUP管理
'''


from flask import request
import logging
from model.const_define import ErrorCode, ErrorMsg
import json_helper
from service.s_group import group_service
from service.s_user.user_service import get_user
from service.s_user_group import user_group_service as user_g_s
import traceback
from common_data_struct import base_define, group_info
import json
from model import group
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user


class GroupListResp(base_define.Base):

    def __init__(self):
        self.total = None
        self.rows = []


@login_required
def group_list():
    '''
        查询组列表，不传参直接返回所有group列表，传参owner或者group_name筛选group列表
        '''
    search = request.values.get('search')
    params = {
        'WHERE_AND': {
            '=': {
                'isdeleted': '0'
            },
            'like': {
                'name': None,
                'owner': None,
                'user_id': None
            }
        },
        'page_size': request.values.get('page_size', 20),
        'page_no': request.values.get('page_no', 1),
    }
    if search:
        json_search = json.loads(search)
        owner = json_search.get('owner')
        if owner:
            params['WHERE_AND']['like']['owner'] = '%' + owner + '%'
        group_name = json_search.get('group_name')
        if group_name:
            params['WHERE_AND']['like']['name'] = '%' + group_name + '%'
        user_id = json_search.get('user_id')
        if user_id:
            params['WHERE_AND']['like']['user_id'] = '%' + user_id + '%'

    # 超级管理员组内的成员可以看到所有组
    user_groups_num, user_groups_data = user_g_s.UserGroupService().get_allgroup_user(get_user()['user_id'])
    super_group_flag = False
    for _user_group in user_groups_data:
        if _user_group['group_name'] == "supergroup":
            super_group_flag = True
            break

    total_nums, data = group.user_group_list(get_user()['user_id'], is_super_group=super_group_flag, **params)
    resp = GroupListResp()
    resp.total = total_nums
    for i in data:
        _user_info = group_info.GroupInitInfo().init_from_db(i)
        resp.rows.append(_user_info)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp.to_json())
