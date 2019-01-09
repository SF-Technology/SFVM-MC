# coding=utf8
'''
    USER管理
'''
# __author__ =  ""

from flask import request
import traceback
from model.const_define import ErrorCode
from service.s_user import user_service
import logging
import json_helper
from common_data_struct import base_define, user_info
import json


class UserListResp(base_define.Base):

    def __init__(self):
        self.total = None
        self.rows = []


def user_list():
    '''
        查询用户列表，不传参时返回所有tb_user表中没有标记删除的用户信息列表
    :parameter 如果传参search中包含user_id，那就筛选出这个user_id的信息
    '''
    search = request.values.get('search')
    params = {
        'ORDER': [
            ['id', 'desc'],
        ],
        'PAGINATION': {
            'page_size': request.values.get('page_size', 20),
            'page_no': request.values.get('page_no', 1),
        },
        'WHERE_AND':{
            '=':{
                'isdeleted': '0',
            }
        }
    }
    if search:
        json_search = json.loads(search)
        user_id = json_search.get('user_id')
        if user_id:
            params['WHERE_AND']['=']['userid'] = user_id
    total_nums, data = user_service.UserService().query_data(**params)
    resp = UserListResp()
    resp.total = total_nums
    for i in data:
        _user_info = user_info.UserInfo().init_from_db(i)
        resp.rows.append(_user_info)

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp.to_json())