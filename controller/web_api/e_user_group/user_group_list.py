# coding=utf8
'''
    USER_GROUP管理
'''


from flask import request
import logging
from model.const_define import ErrorCode
import json_helper
from service.s_user_group import user_group_service
from service.s_group import group_service
from common_data_struct import base_define, user_group_info
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user


class UsersGroup(base_define.Base):

    def __init__(self):
        self.total = None
        self.rows = []


@login_required
def users_in_group(group_id):
    '''
    :return: 返回某个group下的所有用户信息
    '''
    checkexist = group_service.GroupService().get_group_info(group_id)
    if not checkexist:
        logging.info('no such group_id')
        return json_helper.format_api_resp(code=ErrorCode.NOT_EXIST_USER)
    params = {
        'ORDER': [
            ['id', 'desc'],
        ],
        'PAGINATION': {
            'page_size': request.values.get('page_size', 20),
            'page_no': request.values.get('page_no', 1),
        }
    }
    total_nums, data = user_group_service.UserGroupService().get_alluser_group(group_id)
    resp = UsersGroup()
    resp.total = total_nums
    for i in data:
        _user_group_info = user_group_info.UserGroupInfo().user_group_info(i)
        resp.rows.append(_user_group_info)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp.to_json())
