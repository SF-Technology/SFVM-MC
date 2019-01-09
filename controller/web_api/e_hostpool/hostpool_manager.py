# coding=utf8
'''
    HOSTPOOL管理
'''
# __author__ =  ""

from flask import request
import logging
from model.const_define import ErrorCode, OperationObject, OperationAction
import json_helper
from service.s_hostpool import hostpool_service as hostpool_s
from service.s_host import host_service as host_s
from time_helper import get_datetime_str
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
from service.s_operation.operation_service import add_operation_hostpool


@login_required
@add_operation_hostpool(OperationObject.HOSTPOOL, OperationAction.ADD)
def hostpool_add(net_area_id):
    name = request.values.get('name')
    least_host_num = request.values.get('least_host_num')
    hostpool_type = request.values.get('hostpool_type')  # '0'一般类型，'1'特殊类型
    app_code = request.values.get('app_code')

    if not net_area_id or not name or not least_host_num:
        logging.error('the params is invalid when add hostpool')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    # 名字不重复
    ret = hostpool_s.HostPoolService().check_name_exist(net_area_id, name)
    if ret > 0:
        logging.error('hostpool name is duplicated when add hostpool')
        return json_helper.format_api_resp(code=ErrorCode.DUPLICATED_ERR, msg='集群名不能重复，请更换集群名')

    if int(hostpool_type) == 0:
        app_code = "公共资源池"

    insert_data = {
        'name': name,
        'displayname': name,
        'isdeleted': '0',
        'net_area_id': net_area_id,
        'least_host_num': least_host_num,
        'app_code': app_code,
        'hostpool_type': hostpool_type,
        'created_at': get_datetime_str()
    }
    ret = hostpool_s.HostPoolService().add_hostpool(insert_data)
    if ret.get('row_num') <= 0:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


@login_required
@add_operation_hostpool(OperationObject.HOSTPOOL, OperationAction.DELETE)
def hostpool_delete():
    hostpool_ids = request.values.get('hostpool_ids')
    if not hostpool_ids:
        logging.error('no hostpool_ids when delete hostpool')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    hostpool_ids_list = hostpool_ids.split(',')
    # 操作的hostpool数
    all_num = len(hostpool_ids_list)
    msg = None
    fail_num = 0
    for _id in hostpool_ids_list:
        _hosts_nums = host_s.HostService().get_hosts_nums_of_hostpool(_id)
        if _hosts_nums > 0:
            logging.error('no allow to delete hostpool %s that has host', _id)
            fail_num += 1
            # 单台操作且已失败则直接跳出循环
            if all_num == 1:
                msg = '该集群下已分配有HOST，不允许删除'
                break
            continue

        _ret = hostpool_s.HostPoolService().delete_hostpool(_id)
        if _ret <= 0:
            logging.error('db delete hostpool %s fail when delete hostpool')
            fail_num += 1
            continue

    # 全失败
    if fail_num == all_num:
        logging.error("delete hostpool all failed")
        if msg:
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=msg)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    # 部分成功
    if 0 < fail_num < all_num:
        logging.error("delete hostpool part failed")
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS_PART, msg="部分集群删除成功")
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


@login_required
@add_operation_hostpool(OperationObject.HOSTPOOL, OperationAction.ALTER)
def hostpool_update(hostpool_id):
    name = request.values.get('name')
    least_host_num = request.values.get('least_host_num')
    if not hostpool_id or not name or not least_host_num:
        logging.error('the params is invalid when update hostpool')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    old_hostpool = hostpool_s.HostPoolService().get_hostpool_info(hostpool_id)
    if not old_hostpool:
        logging.error('the hostpool %s is not exist in db when upudate hostpool', hostpool_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    # 名字不重复
    if old_hostpool['name'] != name:
        ret = hostpool_s.HostPoolService().check_name_exist(old_hostpool['net_area_id'], name)
        if ret > 0:
            logging.error('hostpool name is duplicated when add hostpool')
            return json_helper.format_api_resp(code=ErrorCode.DUPLICATED_ERR, msg='集群名不能重复，请更换集群名')

    update_data = {
        'name': name,
        'displayname': name,
        'least_host_num': least_host_num,
        'updated_at': get_datetime_str()
    }
    where_data = {
        'id': hostpool_id,
    }
    ret = hostpool_s.HostPoolService().update_hostpool_info(update_data, where_data)
    if ret < 0:
        logging.error("update hostpool error, update_data:%s, where_data:%s", str(update_data), str(where_data))
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)