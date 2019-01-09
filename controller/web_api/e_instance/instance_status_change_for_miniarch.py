# -*- coding:utf-8 -*-
# __author__ =  ""
from flask import request
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
from helper import json_helper
from model.const_define import ErrorCode, VMStatus
from service.s_instance import instance_service as instance_s


@login_required
def instance_status_change_for_miniarch():
    '''
        修改虚拟机状态为v2v中，或者关机中
    :return:
    '''
    instance_uuid = request.values.get('instance_uuid')
    instance_status = request.values.get('instance_status')
    if not instance_uuid or not instance_status:
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="请求入参缺失")

    if instance_status not in [VMStatus.MINIARCH_MIGRATE, VMStatus.SHUTDOWN]:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="待修改的虚拟机状态无法识别")

    ins_data = instance_s.InstanceService().get_instance_info_by_uuid(instance_uuid)
    if not ins_data:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="无法获取虚拟机信息")

    # 将克隆源vm状态改成关机
    where_data = {
        'uuid': instance_uuid
    }
    update_data = {
        'status': instance_status
    }
    ret_change_vm_status = instance_s.InstanceService().update_instance_info(update_data, where_data)
    if ret_change_vm_status < 1:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="虚拟机状态更新失败")

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, msg="虚拟机状态更新成功")
