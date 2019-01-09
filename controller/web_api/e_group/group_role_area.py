# coding=utf8
'''
    管理GROUP-ROLE-AREA关系
'''
# __author__ =  ""

from flask import request
import logging
from model.const_define import ErrorCode
from model import access
from service.s_access import access_service
import json_helper


def group_role_area():
    '''
    新增group_role_area关系，新增应该只能新增group和role，新增area属于修改
    前端新增的时候需要判断，用户选择已有的group-role，是不能点新增按钮的
    '''
    group_id = request.values.get('group_id')
    role_id_list = request.values.get('role_id_list')
    area_id_list = request.values.get('area_id_list')
    if not group_id or not role_id_list or not area_id_list:
        logging.info('no name or owner when add group')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)
    for role_id in role_id_list:
        kwargs = {
            'group_id': group_id,
            'role_id': role_id,
        }
        rest = access_service.AccessService().query_info(kwargs)
        if rest < 0:
            logging.info('not group_role_area info')
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    access_list = []
    ret = access.add_access_info(access_list)

