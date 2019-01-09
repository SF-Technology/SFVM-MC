# coding=utf8
'''
    GROUP管理
'''


from flask import request
import logging
from model.const_define import ErrorCode, OperationObject, OperationAction, AuditType
import json_helper
from service.s_group import group_service as group_s
from service.s_user_group import user_group_service as user_g_s
from service.s_instance import instance_group_service as ins_g_s, instance_service as ins_s
from model import group
from service.s_access import access_service
from model import access
from model import area
from time_helper import get_datetime_str
from service.s_role import role_service
from service.s_user import user_service as user_s
from service.s_user.user_service import get_user, current_user_group_ids
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
from helper.log_helper import CloudLogger
from service.s_operation.operation_service import add_operation_group


@login_required
@add_operation_group(OperationObject.USER_GROUP, OperationAction.ADD)
def add_group():
    name = request.values.get('name')
    owner = request.values.get('owner')
    cpu = request.values.get('cpu')
    mem = request.values.get('mem')
    disk = request.values.get('disk')
    vm = request.values.get('vm')
    env = request.values.get('dc_type')
    role_id = request.values.get('role_id')
    area_str = request.values.get('area_str')
    p_cluster_id = request.values.get('p_cluster_id')

    if not name or not owner or not area_str or not str(env):
        logging.info('no name or owner or area_str or env when add group')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    role_exist = role_service.RoleService().query_role('id', role_id)
    if not role_exist:
        logging.info('no such role %s when add group', role_id)
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    # 应用组名不能重复
    if _check_duplicated_group_name(name, str(env)):
        logging.error('duplicated group name %s when add group', name)
        return json_helper.format_api_resp(code=ErrorCode.DUPLICATED_ERR, msg="应用组名不能重复，请更改应用组名!")

    params_u = {
        'WHERE_AND': {
            '=': {
                'userid': owner,
                'isdeleted': '0',
            },
        },
    }
    user_num, user_data = user_s.UserService().query_data(**params_u)
    if user_num <= 0:
        username = ''
        # 用户不存在，新增
        user_data = {
            'userid': owner,
            'username': username,
            'status': '0',
            'created_at': get_datetime_str()
        }
        user_ret = user_s.UserService().add_user(user_data)

        # 记录安全日志
        field_data = {
            'User_name': owner or None,
            'Oper_type': 'add'
        }
        if user_ret.get('row_num') > 0:
            field_data.update({'Oper_result': '1 Success'})
            CloudLogger.audit(AuditType.USERMGR, field_data)
        else:
            field_data.update({'Oper_result': '0 Fail', 'fail_reason': 'insert new user info to db fail'})
            CloudLogger.audit(AuditType.USERMGR, field_data)
            return False, 'add new user info to db fail'
        # logging.error('no user %s info when add group', owner)
        # return json_helper.format_api_resp(code=ErrorCode.NOT_EXIST_USER, msg='不存在该用户，请检查用户ID')
    else:
        username = user_data[0]['username']

    insert_data = {
        'name': name,
        'displayname': name,
        'isdeleted': '0',
        'owner': owner,
        'cpu': cpu,
        'mem': mem,
        'disk': disk,
        'vm': vm,
        'dc_type': str(env),
        'p_cluster_id': p_cluster_id,
        'created_at': get_datetime_str()
    }
    ret = group_s.GroupService().add_group_info(insert_data)
    if ret.get('row_num') <= 0:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    group_id = ret.get('last_id')
    ret_result = access_service.add_access_list(int(group_id), int(role_id), str(area_str))
    if ret_result.get('row_num') <= 0:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    user_group_data = {
        'user_id': owner,
        'user_name': username,
        'group_id': group_id,
        'group_name': name,
        'role_id': role_id,
        'status': '0',
        'created_at': get_datetime_str(),
        'expire_at': get_datetime_str(),  # todo
    }
    ret_u_g = user_g_s.UserGroupService().add_user_group(user_group_data)
    if ret_u_g.get('row_num') <= 0:
        logging.error('add user group info error when add group, insert_data:%s', user_group_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


def group_area_info(group_id):
    '''通过group_id，查询数据库中access表中它映射的所有area'''
    info_tuple = group.group_area_info(group_id)
    info_list = list(info_tuple)
    parent_id_list = []
    result_list = []
    for i in info_list:
        if i.get('parent_id') != -1:
            parent_id_list.append(i.get('parent_id'))
    set_parent_id = list(set(parent_id_list))

    for y in set_parent_id:
        list_child = []
        for i in info_list:
            children_dict = {'id': None, 'name': None}
            group_dict = {'parent_id': None, 'parent_name': None, 'children': children_dict}
            if i['parent_id'] == y:
                group_dict['parent_id'] = y
                group_dict['parent_name'] = i['parent_name']
                children_dict['id'] = i['area_id']
                children_dict['name'] = i['name']
                list_child.append(children_dict)
                group_dict['children'] = list_child
                result_list.append(group_dict)
    for i in info_list:
        if i['parent_id'] == -1:
            group_dict = {
                'parent_id': i['area_id'],
                'parent_name': i['name'],
                'children': None
            }
            result_list.append(group_dict)
    list_unique = []
    [list_unique.append(x) for x in result_list if x not in list_unique]
    return (list_unique)


@login_required
def init_group_info(group_id):
    '''
    用户编辑组时的初始化信息
    :param group_id:
    :return:
    '''
    resp = {}
    group_tuple = group_s.GroupService().get_group_info(group_id)
    group_dict = group_tuple[1][0]
    area_list = group_area_info(group_id)
    # role_info = access_service.AccessService().get_one('group_id', group_id)
    # role_id = role_info['role_id']
    num, role_info = user_g_s.UserGroupService().get_user_role(group_dict['owner'], group_id)
    if num <= 0:
        role_id = None
    else:
        role_id = role_info[0]['role_id']

    used_area = []

    result_dict = {
        'vm': group_dict['vm'],
        'disk': group_dict['disk'],
        'cpu': group_dict['cpu'],
        'mem': group_dict['mem'],
        'owner': group_dict['owner'],
        'role_id': role_id,
        'name': group_dict['name'],
        'area_list': area_list,
        'p_cluster_id': group_dict['p_cluster_id']
    }
    used_area.append(result_dict)
    # used_area = group_init_info.GroupInitInfo().init_group_info(result_dict)
    resp['used_area'] = used_area

    ret_init = area.get_area_info()
    for i in ret_init:
        if i["parent_id"] == -1:
            i["parent_id"] = i["id"]
            i["parent_name"] = i["name"]
            i["name"] = None
            i["id"] = None
        all_area = []
    for i in ret_init:
        all_area = []
    resp['all_area'] = ret_init
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data = resp)


@login_required
@add_operation_group(OperationObject.USER_GROUP, OperationAction.ALTER)
def update_group(group_id):
    '''
        修改应用组信息
    :param group_id:
    :return:
    '''
    name_n = request.values.get('name')
    owner_n = request.values.get('owner')
    cpu_n = request.values.get('cpu')
    mem_n = request.values.get('mem')
    disk_n = request.values.get('disk')
    vm_n = request.values.get('vm')
    area_str_n = request.values.get('area_str')
    role_id_c = request.values.get('role_id')
    p_cluster_id = request.values.get('p_cluster_id')

    if not cpu_n or not mem_n or not disk_n or not vm_n or not area_str_n or not role_id_c:
        logging.info('param is invalid when update group')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    group_num_c, group_data_c = group_s.GroupService().get_group_info(group_id)
    if group_num_c <= 0:
        logging.error('no group %s info when update group', group_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    update_data = {
        'cpu': cpu_n,
        'mem': mem_n,
        'disk': disk_n,
        'vm': vm_n,
        'updated_at': get_datetime_str()
    }

    # 只能超级管理员组成员和组所有者才能修改组名和所有者，超级管理员组ID为1
    user_group_ids = current_user_group_ids()
    if group_data_c[0]['owner'] != get_user()['user_id'] and 1 not in user_group_ids:
        if name_n or owner_n:
            logging.error('only allow super group member or group owner %s to update group %s name or owner',
                          group_data_c[0]['owner'], group_id)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='您没有权限修改该应用组的组名和所有者!')

    if name_n:
        if group_data_c[0]['name'] != name_n and _check_duplicated_group_name(name_n):
            logging.error('duplicated group name %s when update group', name_n)
            return json_helper.format_api_resp(code=ErrorCode.DUPLICATED_ERR, msg="应用组名不能重复，请更改应用组名!")

        update_data['name'] = name_n
    if owner_n:
        # 新所有者一定要在该应用组里
        group_user_num, group_user_data = user_g_s.UserGroupService().get_alluser_group(group_id)
        in_group_flag = False
        for _group in group_user_data:
            if _group['user_id'] == owner_n:
                in_group_flag = True
                break

        if not in_group_flag:
            logging.error('new owner %s must exist in group %s when update group', owner_n, group_id)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='应用组新所有者必须属于该组，请先添加入组!')

        update_data['owner'] = owner_n

    if p_cluster_id:
        update_data['p_cluster_id'] = p_cluster_id

    where_data = {
        'id': group_id,
    }
    ret = group_s.update_group_info(update_data, where_data)
    if ret < 0:
        logging.error("update group error, update_data:%s, where_data:%s", str(update_data), str(where_data))
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    # 删除access中所有group_id的数据，然后插入前端提交的数据
    delete_access = access.delete_access_info(group_id)
    if delete_access < 0:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    ret_result = access_service.add_access_list(int(group_id), int(role_id_c), str(area_str_n))
    if ret_result < 0:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


@login_required
@add_operation_group(OperationObject.USER_GROUP, OperationAction.DELETE)
def delete_group(group_id):
    '''
    删除用户组的流程：查询instance_group表，如果group在表中，就在tb_group表中将group的isdeleted改为1，
    然后在user_group表中删除所有group_id的行，在access表中删除group信息
    如果group不在instance_group表中，则直接删除group
    '''

    def _check_ins_exist_in_group(group_id):
        '''
            检查组下是否有VM
        :param group_id:
        :return:
        '''
        instances = ins_s.get_instances_in_group(group_id)
        if len(instances) > 0:
            return True
        return False

    if not group_id:
        logging.info('no group_id when delete group')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    group_num, group_data = group_s.GroupService().get_group_info(group_id)
    if group_num <= 0:
        logging.error('no group %s info in db when delete group', group_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    # 只能超级管理员组成员和组所有者才能删除，超级管理员组ID为1
    user_group_ids = current_user_group_ids()
    if group_data[0]['owner'] != get_user()['user_id'] and 1 not in user_group_ids:
        logging.error('only allow super group member or group owner %s to delete group %s',
                      group_data[0]['owner'], group_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='您没有权限删除该应用组!')

    # 该应用组下没有VM才能删除
    if _check_ins_exist_in_group(group_id):
        logging.error('no allow delete group %s which has vms when delete group', group_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='该应用组分配有虚拟机，不能删除该组!')

    # 删除access中所有group_id的数据，然后插入前端提交的数据
    delete_access = access.delete_access_info(group_id)
    if delete_access < 0:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    rest = ins_g_s.InstanceGroupService().query_data(where_field="group_id", where_field_value=group_id)
    # 如果instance_group表中没有group_id，就直接在group表中删除它
    if not rest:
        group.delete_group(group_id)

    else:
        update_data = {
            'isdeleted': '1',
            'deleted_at': get_datetime_str()
        }
        where_data = {
            'id': group_id,
        }
        ret = group_s.update_group_info(update_data, where_data)
        if ret < 0:
            logging.error("update group error, update_data:%s, where_data:%s", str(update_data), str(where_data))
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    # 不管group在不在Instance_group表中，都删除它下面的所有用户
    delete_users = user_g_s.delete_users_in_group(group_id)
    if delete_users < 0:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


def _check_duplicated_group_name(group_name, env=None):
    '''
        检查应用组是否重名
    :param group_name:
    :return:
    '''
    if env:
        params = {
            'WHERE_AND': {
                '=': {
                    'name': group_name,
                    'dc_type': env,
                    'isdeleted': '0',
                },
            },
        }
    else:
        params = {
            'WHERE_AND': {
                '=': {
                    'name': group_name,
                    'isdeleted': '0',
                },
            },
        }

    group_num, group_data = group_s.GroupService().query_data(**params)
    if group_num > 0:
        return True
    return False
