# -*- coding:utf-8 -*-
# __author__ =  ""

import logging
from helper import json_helper
from model.const_define import ErrorCode, OperationObject, OperationAction
from service.s_instance import instance_service as ins_s
from lib.vrtManager import instanceManager as vmManager
from flask import render_template, make_response, request
from service.s_instance.instance_service import InstanceService, get_hostip_of_instance
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
from service.s_operation.operation_service import add_operation_other
from service.s_user import user_service


@login_required
def console():
    """
    虚拟机vnc控制台
    :param instance_id:
    :return :
    """
    """
    if not instance_id:
        logging.info('no instance id when get configure info')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="参数错误")

    ins_data = ins_s.InstanceService().get_instance_info(instance_id)
    host_ip = ins_s.get_hostip_of_instance(instance_id)
    if not ins_data or not host_ip:
        logging.info('instance %s data is no exist in db when get configure info', instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    instance_name = ins_data['name']

    connect_disk_device_get = vmManager.libvirt_get_connect(host_ip, conn_type='instance', vmname=instance_name)
    # result, data = vmManager.libvirt_get_vnc_port(connect_disk_device_get, instance_name)
    # if not result:
        # logging.info(data)
        # return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    """
    console_server_host = request.host.split(':')[0]
    apple = request.query_string.decode().strip()
    peeledapple = apple.split('=')
    instance_uuid = peeledapple[1]
    if not instance_uuid or not console_server_host:
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)
    ins_info = InstanceService().get_instance_info_by_uuid(instance_uuid)
    if not ins_info:
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)
    kvm_host_ip = get_hostip_of_instance(ins_info['id'])
    if not kvm_host_ip:
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    # 连接libvirtd查询虚拟机console端口号
    connect_instance = vmManager.libvirt_get_connect(kvm_host_ip, conn_type='instance', vmname=ins_info['name'])
    status, vnc_port = vmManager.libvirt_get_vnc_console(connect_instance, ins_info['name'])
    if not status:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    token = str(kvm_host_ip) + '-' + str(vnc_port)
    resp = make_response(render_template('console-vnc.html', vm_name=ins_info['name'], ws_host=console_server_host,
                                         ws_port=6080))
    resp.set_cookie('token', token)
    # 添加操作记录: try.. except .. 部分
    try:
        user = user_service.get_user()
        extra_data = "name:"+ins_info['name'] + "," + "uuid:" + peeledapple[1]
        add_operation_other(user["user_id"], OperationObject.VM, OperationAction.CONSOLE, "SUCCESS", extra_data)
    except:
        pass
    return resp
