# -*- coding:utf-8 -*-


import logging
from helper import json_helper
from default import IMAGE_EDIT_SERVER
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
def image_console():
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
    instance_name = peeledapple[1]
    if not console_server_host:
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    kvm_host_ip = IMAGE_EDIT_SERVER
    # 连接libvirtd查询虚拟机console端口号
    connect_instance = vmManager.libvirt_get_connect(kvm_host_ip, conn_type='instance', vmname=instance_name)
    status, vnc_port = vmManager.libvirt_get_vnc_console(connect_instance, instance_name)
    if not status:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    token = str(kvm_host_ip) + '-' + str(vnc_port)
    resp = make_response(render_template('console-vnc.html', vm_name=instance_name, ws_host=console_server_host,
                                         ws_port=6080))
    resp.set_cookie('token', token)
    return resp
