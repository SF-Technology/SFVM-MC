# coding=utf8
'''
    USER_GROUP管理
'''


from flask import request
import logging
from model.const_define import ErrorCode, AuditType, OperationObject, OperationAction
import json_helper
from service.s_user_group import user_group_service as user_g_s
from service.s_group import group_service as group_s
from model import area
from common_data_struct import base_define
from service.s_user import user_service
from service.s_access import access_service
from helper import encrypt_helper
from helper.time_helper import get_datetime_str
from helper.encrypt_helper import decrypt_str_aes
from helper.log_helper import CloudLogger
from service.s_operation.operation_service import add_operation_group
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user


class AreaListResp(base_define.Base):
    def __init__(self):
        self.total = None
        self.rows = []


def check(group_id, user_id):
    if not user_id or not group_id:
        logging.info('no user_id or group_id or rold_id when add user to a group')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    group_info = group_s.GroupService().get_group_info(group_id)
    if not group_info[1]:
        logging.info('no such group_id %s when add user to a group', group_id)
        return json_helper.format_api_resp(code=ErrorCode.NOT_EXIST_USER)

    user_group = user_g_s.UserGroupService().query_user_role_group(user_id, group_id)
    if user_group[1]:
        logging.info('same user %s already in group %s when add user to a group', user_id, group_id)
        return json_helper.format_api_resp(code=ErrorCode.DUPLICATED_ERR, msg='用户已经存在于该组，请不要重复加入')

    params = {
        'WHERE_AND': {
            '=': {
                'group_id': group_id,
            }
        }
    }
    is_exist_role_group = access_service.AccessService().query_info(params)
    if not is_exist_role_group[1]:
        # 查询access表中是否存在这个role-group的对应关系，(不查area)没有就报错
        logging.info('not such role_group_area mapping exist')
        return json_helper.format_api_resp(code=ErrorCode.NOT_EXIST_USER,
                                           msg="该组没有角色权限对应关系，不能添加新用户")


@login_required
@add_operation_group(OperationObject.USER_GROUP, OperationAction.ADD_INSIDE_USER)
def add_insideuser_to_group(group_id):
    '''
    在user_group表中将顺丰用户添加到某个组
    '''
    user_id = request.values.get('user_id')
    group_name = request.values.get('group_name')
    check_info = check(group_id, user_id)
    if check_info:
        return check_info

    params = {
        'WHERE_AND': {
            '=': {
                'userid': user_id,
                'auth_type': '0',
            }
        }
    }
    user_info = user_service.UserService().query_data(**params)

    if not user_info or not user_info[1]:
        user_name = ''
        # logging.error("query user error, no such user_id:%s", str(user_id))
        # return json_helper.format_api_resp(code=ErrorCode.NOT_EXIST_USER, msg="该用户请先登录平台，再来添加")
    else:
        user_name = user_info[1][0]['username']

    user_group_data = user_g_s.get_data_by_group_name(group_name)
    if not user_group_data:
        logging.error("group %s role id no exist in db when add insideuser to group", group_name)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    insert_user_data = {
        'user_id': user_id,
        'user_name': user_name,
        'group_id': group_id,
        'group_name': group_name,
        'role_id': user_group_data['role_id'],
        'status': '0',
        'created_at': get_datetime_str()
    }
    ret = user_g_s.UserGroupService().add_user_group(insert_user_data)
    if ret == -1:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


@login_required
@add_operation_group(OperationObject.USER_GROUP, OperationAction.ADD_OUTER_USER)
def add_outuser_to_group(group_id):
    '''
    为某个组增加外部用户，需要插入tb_user表，user_group表
    '''
    user_id = request.values.get('user_id')
    user_name = request.values.get('user_name')
    password = request.values.get('password')
    email = request.values.get('email')
    group_name = request.values.get('group_name')
    auth_type = request.values.get('auth_type')

    if not user_name or not email or not password:
        logging.info('not enough params when add outuser to a group')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    check_info = check(group_id, user_id)
    if check_info:
        return check_info

    # 检查用户ID是否已存在，如果已经存在，直接将该用户添加至组中
    userid_exist = user_service.UserService().check_userid_exist(user_id, auth_type=1)
    if userid_exist:
        # todo:如果已经存在，直接将该用户添加至组中
        logging.error("user %s has exist in group %s when add outuser to a group", user_id, group_id)
        return json_helper.format_api_resp(code=ErrorCode.EXIST_USER, msg='该用户ID已被使用，请更换新用户ID')

    user_group_data = user_g_s.get_data_by_group_name(group_name)
    if not user_group_data:
        logging.error("group %s role id no exist in db when add outuser to group", group_name)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    user_data = {
        'userid': user_id,
        'username': user_name,
        'password': password,
        'created_at': get_datetime_str(),
        'email': email,
        'auth_type': auth_type,
    }
    ret = user_service.UserService().add_user(user_data)

    # 添加安全日志
    field_data = {
        'User_name': user_name,
        'Oper_type': 'add'
    }
    # 先记录再返回
    if ret == -1:
        field_data.update({'Oper_result': '0 Fail', 'fail_reason': 'insert new user info to db fail'})
    else:
        field_data.update({'Oper_result': '1 Success'})
    CloudLogger.audit(AuditType.USERMGR, field_data)

    if ret == -1:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    user_group_data = {
        'user_id': user_id,
        'user_name': user_name,
        'group_id': group_id,
        'group_name': group_name,
        'role_id': user_group_data['role_id'],
        'status': '0',
        'created_at': get_datetime_str(),
    }
    rest = user_g_s.UserGroupService().add_user_group(user_group_data)
    if rest == -1:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


@login_required
@add_operation_group(OperationObject.USER_GROUP, OperationAction.REMOVE_USER)
def delete_user_group():
    '''
    将组中的某个用户删除
    '''
    user_id = request.values.get('user_id')
    group_id = request.values.get('group_id')
    if not user_id or not group_id:
        logging.info('no user_id or group_id when delete user from a group')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    user_group_num, user_group_data = user_g_s.UserGroupService().query_user_role_group(user_id, group_id)
    if user_group_num < 0:
        logging.info('no such user %s in group %s when delete user from a group', user_id, group_id)
        return json_helper.format_api_resp(code=ErrorCode.NOT_EXIST_USER)

    groups_num, groups_data = group_s.GroupService().get_group_info(group_id)
    if groups_num < 0:
        logging.error('no group %s info in db when delete user from a group', group_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    # 不能删除组所有者
    if groups_data[0]['owner'] == user_id:
        logging.warn('not allow delete group %s owner %s when delete user from a group', group_id, user_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='不能删除组的所有者!')

    ret = user_g_s.delete_user(user_id, group_id)
    if ret <= 0:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


@login_required
def group_init_area_info():
    '''
    为前端组编辑功能提供一个区域--子区域初始列表
    '''
    ret_init = area.get_area_info()
    if not ret_init:
        return []
    for i in ret_init:
        if i["parent_id"] == -1:
            i["parent_id"] = i["id"]
            i["parent_name"] = i["name"]
            i["name"] = None
            i["id"] = None
    resp = AreaListResp()
    for i in ret_init:
        resp.rows.append(i)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp.to_json())

