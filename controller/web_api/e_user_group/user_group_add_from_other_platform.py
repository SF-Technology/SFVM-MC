# coding=utf8
'''
    应用组创建、配额分配(外接平台)
'''


import logging
import os
from flask import request
from helper import json_helper
from helper.time_helper import get_datetime_str
from model.const_define import VsJobStatus, AuditType
from service.s_user import user_service as user_s
from service.s_group import group_service as group_s
from service.s_area import area_service as area_s
from service.s_user_group import user_group_service as user_g_s
# from flask.ext.httpauth import HTTPBasicAuth
from flask_httpauth import HTTPBasicAuth
from helper.log_helper import CloudLogger, add_timed_rotating_file_handler
from service.s_access import access_service
from controller.web_api.ip_filter_decorator import ip_filter_from_other_platform

auth_api_user = HTTPBasicAuth()


# 日志格式化
def _init_log(service_name):
    log_basic_path = os.path.dirname(os.path.abspath(__file__))[0:-31]
    log_name = log_basic_path + 'log/' + str(service_name) + '.log'
    add_timed_rotating_file_handler(log_name, logLevel='INFO')


@ip_filter_from_other_platform
@auth_api_user.login_required
def group_create_from_other_platform():
    '''
      外部平台创建应用组
      目前供治水项目调用
    :return:
    '''
    _init_log('group_create_from_other_platform')
    data_from_zhishui = request.data
    logging.info(data_from_zhishui)
    data_requset = json_helper.loads(data_from_zhishui)

    sys_code = data_requset['sys_code']
    sys_opr_name = data_requset['group_master_name']
    sys_opr_id = data_requset['group_master_id']
    sys_env = data_requset['dc_type']

    ins_cpu = data_requset['cpu']
    ins_mem = data_requset['mem']
    ins_disk = data_requset['disk']
    ins_count = data_requset['vm_num']

    # 根据维石平台输入的系统运维人员工号维护对应应用组信息
    if not sys_opr_name or not sys_opr_id or not sys_code or not sys_env:
        _msg = 'empty input of sys_code, group_master_name, dc_type or group_master_id when create group'
        return json_helper.format_api_resp_msg_for_group_add(job_status=VsJobStatus.FAILED, detail=_msg)

    if not ins_cpu or not ins_mem or not ins_disk or not ins_count:
        _msg = 'empty input of ins_cpu, ins_mem ,ins_disk or ins_count  when create group'
        return json_helper.format_api_resp_msg_for_group_add(job_status=VsJobStatus.FAILED, detail=_msg)

    ret_group, group_id = _user_group_check(sys_code, sys_opr_name, sys_opr_id, sys_env, sys_code, ins_cpu, ins_mem,
                                            ins_disk, ins_count)
    if not ret_group:
        return json_helper.format_api_resp_msg_for_group_add(job_status=VsJobStatus.FAILED, detail=group_id)

    return json_helper.format_api_resp_msg_for_group_add(job_status=VsJobStatus.SUCCEED,
                                                         detail='应用组%s添加成功' % sys_code)


def _user_group_check(sys_code, sys_opr_name, sys_opr_id, sys_env, cluster_id, quota_cpu, quota_mem, quota_disk, quota_vm_num):
    # 检查应用系统管理员用户是否存在，不存在则新增
    user = user_s.UserService().get_user_info_by_user_id(sys_opr_id)
    if not user:
        # 用户不存在，新增
        user_data = {
            'userid': sys_opr_id,
            'username': sys_opr_name,
            'status': '0',
            'created_at': get_datetime_str()
        }
        user_ret = user_s.UserService().add_user(user_data)

        # 记录安全日志
        field_data = {
            'User_name': sys_opr_name or None,
            'Oper_type': 'add'
        }
        if user_ret.get('row_num') > 0:
            field_data.update({'Oper_result': '1 Success'})
            CloudLogger.audit(AuditType.USERMGR, field_data)
        else:
            field_data.update({'Oper_result': '0 Fail', 'fail_reason': 'insert new user info to db fail'})
            CloudLogger.audit(AuditType.USERMGR, field_data)
            return False, 'add new user info to db fail'

    # 检查应用组是否存在，不存在新建
    group = group_s.get_group_info_by_name(sys_code)
    if not group:
        group_data = {
            'name': sys_code,
            'displayname': sys_code,
            'dc_type': str(sys_env),
            'isdeleted': '0',
            'owner': sys_opr_id,
            'cpu': int(quota_cpu),
            'mem': int(quota_mem),
            'disk': int(quota_disk),
            'vm': int(quota_vm_num),
            'p_cluster_id': cluster_id,
            'created_at': get_datetime_str()
        }
        group_ret = group_s.GroupService().add_group_info(group_data)
        if group_ret.get('row_num') <= 0:
            return False, 'add group info to db fail'

        group_id = group_ret.get('last_id')
        role_id = 2
        area_zb_ret = area_s.AreaService().get_area_zb_info()
        if not area_zb_ret:
            return False, 'get zongbu area id fail'
        area_zb_id = area_zb_ret['id']
        ret_result = access_service.add_access_list(int(group_id), int(role_id), str(area_zb_id))
        if ret_result.get('row_num') <= 0:
            return False, 'add access info to db fail'

        user_group_data = {
            'user_id': sys_opr_id,
            'user_name': sys_opr_name,
            'group_id': group_id,
            'group_name': sys_code,
            'role_id': role_id,
            'status': '0',
            'created_at': get_datetime_str(),
            'expire_at': get_datetime_str(),  # todo
        }
        ret_u_g = user_g_s.UserGroupService().add_user_group(user_group_data)
        if ret_u_g.get('row_num') <= 0:
            logging.error('add user group info error when add group, insert_data:%s', user_group_data)
            return False, 'add user group info to db fail'
    else:
        # 获取应用组对应用户信息
        role_id = 2
        opr_is_exist = False
        group_id = group['id']
        ret_num, ret_query_g_u = user_g_s.UserGroupService().get_alluser_group(group_id)
        for one_ret_query_g_u in ret_query_g_u:
            if one_ret_query_g_u['user_id'] == sys_opr_id:
                opr_is_exist = True
        if not opr_is_exist:
            # 将用户加入应用组中
            user_group_data = {
                'user_id': sys_opr_id,
                'user_name': sys_opr_name,
                'group_id': group_id,
                'group_name': sys_code,
                'role_id': role_id,
                'status': '0',
                'created_at': get_datetime_str(),
                'expire_at': get_datetime_str(),  # todo
            }
            ret_u_g = user_g_s.UserGroupService().add_user_group(user_group_data)
            if ret_u_g.get('row_num') <= 0:
                logging.error('add user group info error when add group, insert_data:%s', user_group_data)
                return False, 'add user group info to db fail'

            # 修改应用组owner
            update_data = {
                'owner': sys_opr_id
            }
            where_data = {
                'id': group_id,
            }
            ret_change_owner = group_s.update_group_info(update_data, where_data)
            if ret_change_owner < 0:
                logging.error("update group error, update_data:%s, where_data:%s", str(update_data), str(where_data))
                return False, 'update group owner to db fail'

    return True, group_id


@auth_api_user.verify_password
def verify_api_user_pwd(username_or_token, password):
    if not username_or_token:
        return False
    api_user = user_s.verify_api_auth_token(username_or_token)
    if not api_user:
        api_user = user_s.UserService().get_user_info_by_user_id(username_or_token)
        if not api_user or not user_s.verify_password(password, api_user['password']):
            return False
        if api_user['auth_type'] != 2:
            return False
    elif api_user['auth_type'] != 2:
        return False
    return True
