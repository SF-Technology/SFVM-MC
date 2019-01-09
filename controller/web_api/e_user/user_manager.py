# coding=utf8
'''
    USER管理
'''
# __author__ =  ""

from flask import request
import logging
from model.const_define import ErrorCode
import json_helper
from service.s_user import user_service
from service.s_role import role_service
from common_data_struct import base_define, user_info
from service.s_user_group import user_group_service
from model import permission
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user


class UserListResp(base_define.Base):

    def __init__(self):
        self.rows = []


@login_required
def update_user():
    user_id = request.values.get('user_id')
    where_field = request.values.get('where_field')
    where_field_value = request.values.get('where_field_value')
    if not user_id or not where_field:
        logging.info('no user_id or update_attr or update_attr_value when update user')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    update_data = {
        where_field: where_field_value,
    }
    where_data = {
        'userid': user_id,
    }
    ret = user_service.UserService().update_user_info(update_data, where_data)
    if ret <= 0:
        logging.error("update user error, update_data:%s, where_data:%s", str(update_data), str(where_data))
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


@login_required
def query_user_info():
    '''
    :return: 返回的是user_info.UserInfo().user_info()函数中写的字段
    '''
    user_id = request.values.get('user_id')
    if not user_id:
        logging.info('no user_id when query user info')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)
    data = user_service.UserService().query_user_info('userid', user_id)
    if data <= 0:
        logging.error("query user error, no such user_id:%s", str(user_id))
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    tuple_data = (data,)
    resp = UserListResp()
    for i in tuple_data:
        _user_info = user_info.UserInfo().init_from_db(i)
        resp.rows.append(_user_info)

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp.to_json())


@login_required
def add_user():
    user_id = request.values.get('user_id')
    user_name = request.values.get('user_name')
    if not user_id or not user_name:
        logging.info('no user_id or user_name when query user info')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    ret = user_service.UserService().query_user_info('userid', user_id)
    if ret > 0:
        logging.error("query user error, no such user_id:%s", str(user_id))
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    insert_data = {
        'userid': user_id,
        'username': user_name
    }

    ret1 = user_service.UserService().add_user(insert_data)
    if ret1 == -1:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)

