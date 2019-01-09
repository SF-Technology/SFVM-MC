# coding=utf8
'''
    v2v_openstack_batch_t1
'''
# __author__ = 'anke'
import logging
from helper import json_helper
from lib.shell.ansibleCmdV2 import ansible_run_shell
from model.const_define import ErrorCode
from flask import request
from config.default import OPENSTACK_DEV_PASS,OPENSTACK_SIT_PASS,OPENSTACK_DEV_USER
from service.s_ip import ip_service as ip_s ,segment_service as seg_s
from service.s_flavor import flavor_service
from helper.encrypt_helper import decrypt




#获取待转化vm的数据盘大小
def vm_disk_size(vmip,cloudarea,host,host_pass):
   # if cloudarea == "SIT":
   #     command = "/usr/bin/vmop " + vmip + " data_volume"
   # else:
    command = "/usr/bin/vmop " + vmip + " data_volume"
    remote_user= OPENSTACK_DEV_USER
    become_user=OPENSTACK_DEV_USER
    remote_pass=host_pass
    become_pass=host_pass
    ctrhost = host
    vmdisksize = ansible_run_shell(ctrhost,command)
    if 'contacted' not in vmdisksize:
       return False
    elif vmdisksize['contacted'] == {}:
        return False
        #return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='无法连接目标vm所在控制节点，无法完成v2v操作')
    elif 'failed' in vmdisksize['contacted'][ctrhost]:
        return False
        #return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='获取待转化vm总磁盘大小失败，无法完成v2v操作')
    else :
        disk_size = int(vmdisksize['contacted'][ctrhost]['stdout']) + 80
        return disk_size
        #return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='获取待转化vm总磁盘大小失败，无法完成v2v操作',data=disk_size)



#判断虚拟机是否输入错误
def vm_exist(vmip,host,host_pass):
    command = "/usr/bin/vmop " + vmip + " |grep id"
    remote_user = OPENSTACK_DEV_USER
    become_user = OPENSTACK_DEV_USER
    remote_pass = host_pass
    become_pass = host_pass
    ctrhost = host
    vmexist = ansible_run_shell(ctrhost, command)
    if 'contacted' not in vmexist:
        return False
    elif vmexist['contacted'] == {}:
        return False
        #return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='无法连接目标vm所在控制节点，无法完成v2v操作')
    elif 'failed' in vmexist['contacted'][ctrhost]:
        return False
        #return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='判断虚拟机状态失败，无法完成v2v操作')
    elif vmexist['contacted'][ctrhost]['stdout'] == '':
        return False
        #return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='虚拟机IP输入错误，无法完成v2v操作')
    else :
        return True
        #return json_helper.format_api_resp(code=ErrorCode.SUCCESS, msg='虚拟机IP输入正确，进行后续v2v步骤')


#判断vm是否关机
def vm_stat(vmip,host,host_pass):
    command = "/usr/bin/vmop " + vmip + " |grep 'vm_state'|grep 'stopped'"
    remote_user=OPENSTACK_DEV_USER
    become_user=OPENSTACK_DEV_USER
    remote_pass=host_pass
    become_pass=host_pass
    ctrhost = host
    vmstat = ansible_run_shell(ctrhost,command)
    if 'contacted' not in vmstat:
        return False
    elif vmstat['contacted'] == {}:
        return False
        #return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='无法连接目标vm所在控制节点，无法完成v2v操作')
    elif 'failed' in vmstat['contacted'][ctrhost]:
        return False
        #return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='获取待转化vm当前状态失败，无法完成v2v操作')
    elif vmstat['contacted'][ctrhost]['stdout'] == '':
        return False
        #return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='待转化vm未关机，无法完成v2v操作')
    else :
        return True
        #return json_helper.format_api_resp(code=ErrorCode.SUCCESS, msg='待转化vm已关机，进行后续v2v步骤')



#获取vm os版本
def get_vm_version(ctrhost,ctrpass,vmostype,vmip):
    command = "vmop " + vmip +"|grep image|cut -d '|' -f 3|cut -d ' ' -f 2"
    remote_user = OPENSTACK_DEV_USER
    become_user = OPENSTACK_DEV_USER
    remote_pass = ctrpass
    become_pass = ctrpass
    host = ctrhost
    osversion = ansible_run_shell(host, command)
    print osversion['contacted']
    if 'contacted' not in osversion:
        msg = '获取vmOS版本失败'
        return False, msg
    elif osversion['contacted'] == {}:
        msg = '获取vmOS版本失败'
        return False,msg
    elif 'failed' in osversion['contacted'][host]:
        msg = '获取vmOS版本失败'
        return False, msg
    else:
        osversion_s = osversion['contacted'][host]['stdout']
        if vmostype == "Windows":
            if '2008' in osversion_s:
                version_res = '2008'
            elif '2012' in osversion_s:
                version_res = '2012'
            elif 'win7' in osversion_s:
                version_res = 'win7'
            else:
                version_res = 'windows'
            return True, version_res
        elif vmostype == "Linux":
            if ('centos' or 'RHEL') in osversion_s:
                if '6.6' in osversion_s:
                    version_res = '6.6'
                elif '7.2'in osversion_s:
                    version_res = '7.2'
                else:
                    version_res = 'centos'

            elif 'ubuntu' in osversion_s:
                version_res = 'ubuntu'
            elif 'debian' in osversion_s:
                version_res = 'debian'
            else:
                version_res = 'unknown'
            return True,version_res


def task_check():

    # 入参赋值
    vmip = request.values.get('vm_ip')
    flavor_id = request.values.get('flavor_id')
    cloudarea = request.values.get('cloud_area')
    vm_ostype = request.values.get('vm_ostype')
    vm_segment = request.values.get('segment')

    # 入参完全性判断
    if not  vmip or not flavor_id or not cloudarea or not vm_ostype or not vm_segment:
        logging.info('params are invalid or missing')
        message = '入参缺失'
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg=message)
    else:
        # 获取flavor信息
        flavor_info = flavor_service.FlavorService().get_flavor_info(flavor_id)
        if not flavor_info:
            logging.info('id: %s flavor info not in db when create instance', flavor_id)
            message = '实例规格数据有误，无法进行v2v'
            return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg=message)


        # 获取对应openstack环境的管理节点及ssh账户信息
        if cloudarea == "SIT":
            ctr_host = '10.202.83.12'
            ctr_pass = decrypt(OPENSTACK_SIT_PASS)
        elif cloudarea == "DEV":
            ctr_host = "10.202.123.4"
            ctr_pass = decrypt(OPENSTACK_DEV_PASS)
        else:
            message = 'openstack环境参数错误，无法进行v2v操作'
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=message)

        # 判断vm信息是否输入错误
        vmexist = vm_exist(vmip, ctr_host, ctr_pass)
        if vmexist == False:
            message = '获取vm信息失败'
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=message)

        # 获取OS版本失败
        osstat, verdata = get_vm_version(ctr_host, ctr_pass, vm_ostype, vmip)
        if osstat == False:
            message = '获取vmOS版本失败'
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=message)
        else:
            ver_data = verdata

        # 获取待迁移vm磁盘大小
        vdiskdata = vm_disk_size(vmip, cloudarea, ctr_host, ctr_pass)
        if vdiskdata == False:
            message = '获取vm磁盘信息失败'
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=message)
        vdisk = vdiskdata
        data_disk = vdisk - 80

        # 判断待转化vm是否关机
        vmshutdown = vm_stat(vmip, ctr_host, ctr_pass)
        if vmshutdown == False:
            message = '待转化vm未关机'
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=message)

        # 获取并录入IP信息

        vm_segment = seg_s.SegmentService().get_segment_info_bysegment(vm_segment)
        if vm_segment == None:
            message = '网段信息有误，无法进行v2v'
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=message)
        else:
            ip_data = ip_s.IPService().get_ip_info_by_ipaddress(vmip)
            if ip_data :
                ip_data_status = ip_data['status']
                if ip_data_status != '0':
                    message = "IP与现有环境冲突,无法进行v2v"
                    return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=message)

        return_info = {
            'vm_osver':ver_data,
            'vm_disk':str(data_disk)
        }
        message = "获取VM信息成功"
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS, msg=message,data=return_info)


