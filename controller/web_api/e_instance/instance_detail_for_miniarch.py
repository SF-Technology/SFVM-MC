# -*- coding:utf-8 -*-

from flask import request
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
from helper import json_helper
from model.const_define import ErrorCode, VMLibvirtStatus
from service.s_instance import instance_service as instance_s
from lib.vrtManager import instanceManager


@login_required
def instance_detail_for_miniarch():
    '''
        返回miniarch虚拟机所在物理机ip、应用系统信息、cpu、mem、操作系统类型、操作系统版本、磁盘信息、网卡信息
    :return:
    '''
    instance_uuid = request.values.get('instance_uuid')
    if not instance_uuid:
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="请求入参缺失")

    ins_data = instance_s.InstanceService().get_instance_info_by_uuid(instance_uuid)
    if not ins_data:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="无法获取虚拟机信息")

    ins_host_data = instance_s.get_host_of_instance(ins_data['id'])
    if not ins_host_data:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="无法获取虚拟机所在物理机信息")

    # vm_status = instanceManager.libvirt_instance_status(ins_host_data['ipaddress'], ins_data['name'])
    # # 虚拟机开机状态才可以做迁移
    # if vm_status != VMLibvirtStatus.SHUTDOWN:
    #     return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="只有关机状态虚拟机才可执行迁移")

    ins_flavor_data = instance_s.get_flavor_of_instance(ins_data['id'])
    if not ins_flavor_data:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="无法获取虚拟机cpu、mem信息")

    ins_group_data = instance_s.get_group_of_instance(ins_data['id'])
    if not ins_group_data:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="无法获取虚拟机应用组信息")

    ins_image_data = instance_s.get_images_of_instance(ins_data['id'])
    if not ins_image_data:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="无法获取虚拟机镜像信息")

    get_device_status, vm_disks_info = instanceManager.libvirt_get_instance_device(ins_host_data['ipaddress'],
                                                                                   ins_data['name'])
    if get_device_status == -100:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="无法使用libvirtd获取虚拟机磁盘信息")

    for _vm_disk in vm_disks_info:
        if _vm_disk['dev'] == 'vda':
            _vm_disk['size_gb'] = 80
        else:
            disk_detail = instance_s.get_a_disk_of_instance(ins_data['id'], _vm_disk['dev'])
            if not disk_detail or not disk_detail['size_gb']:
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="获取虚拟机磁盘大小失败")
            _vm_disk['size_gb'] = disk_detail['size_gb']

    netcard_list = []
    ins_netcard_info = instance_s.get_net_info_of_instance(ins_data['id'])
    if not ins_netcard_info:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="无法获取网卡信息")
    for _netcard in ins_netcard_info:
        netcard_params = {
            'ip_address': _netcard['ip_address'],
            'vlan': _netcard['vlan'],
            'mac': _netcard['mac']

        }
        netcard_list.append(netcard_params)

    instance_data = {
        'instance_name': ins_data['name'],
        'instance_group': ins_group_data['name'],
        'instance_app_info': ins_data['app_info'],
        'instance_password': ins_data['password'],
        'cpu': ins_flavor_data['vcpu'],
        'mem': ins_flavor_data['memory_mb'],
        'os_system': ins_image_data[0]['system'],
        'os_version': ins_image_data[0]['version'],
        'image_name': ins_image_data[0]['name'],
        'src_host_ip': ins_host_data['ipaddress'],
        'disk': vm_disks_info,
        'netcard': netcard_list
    }
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=instance_data)




