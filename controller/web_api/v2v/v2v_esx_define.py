# coding=utf8
'''
    v2v_esx_define
'''
# __author__ = 'anke'

import logging
from helper import json_helper
from model.const_define import ErrorCode
from flask import request
from pyVim.connect import SmartConnectNoSSL, Disconnect
import base64
from config.default import OPENSTACK_DEV_USER
from model.const_define import esx_env


def esx_vm_define():
    esx_env = request.values.get("esx_env")
    esx_ip = request.values.get("esx_ip")
    esx_passwd_en = request.values.get("esx_passwd")
    vm_name = request.values.get("vm_name")

    if not esx_env or not esx_ip or not esx_passwd_en or not vm_name:
        logging.info('params are invalid or missing')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg='入参缺失')
    else:
        esx_passwd = base64.b64decode(esx_passwd_en)
        try:
            c = SmartConnectNoSSL(host=esx_ip, user=OPENSTACK_DEV_USER, pwd=esx_passwd)
        except Exception as e:
            if "unreachable" in str(e):
                err_detail = "ESXi无法连接"
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=err_detail)
            elif "timed out" in str(e):
                err_detail = "ESXi连接超时"
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=err_detail)
            elif "No route to host" in str(e):
                err_detail = "ESXi无法连接"
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=err_detail)
            else:
                err_msg = e.msg
                if "incorrect user name or password" in err_msg:
                    err_detail = "esxi用户名密码错误"
                    return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=err_detail)
                else:
                    err_detail = "未知异常"
                    return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=err_detail)


        datacenter = c.content.rootFolder.childEntity[0]
        vms = datacenter.vmFolder.childEntity
        vmlist = []
        for i in vms:
            vmlist.append(i.name)
        if vm_name not in vmlist:
            err_detail = "ESXi中未找到目标vm"
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=err_detail)
        else:
            index = vmlist.index(vm_name)
            index_int = int(index)
            vm = vms[index_int]
            vm_state = vms[index_int].summary.runtime.powerState
            vm_osname = vms[index_int].summary.guest.hostName
            vm_ip = vms[index_int].summary.guest.ipAddress
            vm_disk = vms[index_int].summary.storage.committed + vms[index_int].summary.storage.uncommitted
            vm_disk_GB = vm_disk/1024/1024/1024 + 1
            vm_osver = vms[index_int].summary.guest.guestFullName
            if not vm_osname:
                err_detail = "获取vm OSname失败"
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=err_detail)
            elif not vm_ip:
                err_detail = "获取vm IP失败"
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=err_detail)
            elif not vm_disk:
                err_detail = "获取vm磁盘大小失败"
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=err_detail)
            elif not vm_osver:
                err_detail = "获取vmOS版本失败"
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=err_detail)
            else:
                data_ret = {
                    "vm_osname":vm_osname,
                    "vm_ip":vm_ip,
                    "vm_disk":vm_disk_GB,
                    "vm_osver":vm_osver,
                    "esx_env":esx_env,
                    "vmware_vm":vm_name
                }
            msg_succ = "vm信息获取成功"
            Disconnect(c)
            return json_helper.format_api_resp(code=ErrorCode.SUCCESS, msg=msg_succ,data = data_ret)

