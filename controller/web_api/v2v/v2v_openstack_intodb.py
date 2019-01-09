# coding=utf8
'''
    v2v_openstack
'''
# __author__ = 'anke'


import logging
from helper import json_helper
from lib.shell.ansibleCmdV2 import ansible_run_shell
from model.const_define import ErrorCode,v2vActions,ActionStatus,VMStatus,VMTypeStatus,VMCreateSource, InstanceNicType
from flask import request
from config.default import OPENSTACK_DEV_PASS,OPENSTACK_SIT_PASS,\
    KVMHOST_LOGIN_PASS,KVMHOST_SU_PASS,OPENSTACK_DEV_USER
from service.v2v_task import v2v_task_service as v2v_op
from service.s_instance_action import instance_action as in_a_s
from service.s_instance import instance_host_service as ins_h_s, instance_ip_service as ins_ip_s, \
    instance_disk_service as ins_d_s, instance_service as ins_s, \
    instance_flavor_service as ins_f_s, instance_group_service as ins_g_s
from service.s_ip import ip_service as ip_s ,segment_service as seg_s
from service.s_flavor import flavor_service
from service.s_host import host_service as ho_s
from service.v2v_task import v2v_instance_info as v2v_in_i
from calc_dest_host import calc_dest_host as cal_host
from lib.vrtManager.util import randomUUID, randomMAC
from helper.time_helper import get_datetime_str
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


#信息入库函数
def instance_db_info(uuid,vmname,vm_app_info,owner,flavor_id,group_id,host,mac,vmdisk,ip_id,vmostype,requestid,ver_data):
    vm_ostype_todb = ''
    vmhost =ho_s.HostService().get_host_info_by_hostip(host)
    # 往instance表添加记录
    instance_data = {
        'uuid': uuid,
        'name': vmname,
        'displayname': vmname,
        'description': '',
        'status': VMStatus.CONVERTING,
        'typestatus': VMTypeStatus.NORMAL,
        'isdeleted': '0',
        'app_info': vm_app_info,
        'owner': owner,
        'created_at': get_datetime_str(),
        'create_source':VMCreateSource.OPENSTACK
    }
    ret = ins_s.InstanceService().add_instance_info(instance_data)
    if ret.get('row_num') <= 0:
        logging.info('add instance info error when create instance, insert_data: %s', instance_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    instance_id = ret.get('last_id')

    if vmostype == 'Windows':
        vm_ostype_todb = 'windows'
    elif vmostype == 'Linux':
        vm_ostype_todb = 'linux'

    #往v2v_instance_info表添加记录
    v2v_instance_data = {
        'instance_id':instance_id,
        'os_type':vm_ostype_todb,
        'isdeleted':'0',
        'created_at':get_datetime_str(),
        'request_id':requestid,
        'os_version':ver_data
    }
    ret_v2v_instance = v2v_in_i.v2vInstanceinfo().add_v2v_instance_info(v2v_instance_data)
    if ret_v2v_instance.get('row_num') <= 0:
        logging.info('add v2v_instance info error when create instance, v2v_instance_data: %s',
                     v2v_instance_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    # 往instance_flavor表添加记录
    instance_flavor_data = {
        'instance_id': instance_id,
        'flavor_id': flavor_id,
        'created_at': get_datetime_str()
    }
    ret1 = ins_f_s.InstanceFlavorService().add_instance_flavor_info(instance_flavor_data)
    if ret1.get('row_num') <= 0:
        logging.info('add instance_flavor info error when create instance, insert_data: %s',
                     instance_flavor_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    # 往instance_group表添加记录
    instance_group_data = {
        'instance_id': instance_id,
        'group_id': group_id,
        'created_at': get_datetime_str()
    }
    ret2 = ins_g_s.InstanceGroupService().add_instance_group_info(instance_group_data)
    if ret2.get('row_num') <= 0:
        logging.info('add instance_group info error when create instance, insert_data: %s', instance_group_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)


    # 往instance_host表添加记录
    instance_host_data = {
            'instance_id': instance_id,
            'instance_name': vmname,
            'host_id': vmhost['id'],
            'host_name': vmhost['name'],
            'isdeleted': '0',
            'created_at': get_datetime_str()
    }
    ret3 = ins_h_s.InstanceHostService().add_instance_host_info(instance_host_data)
    if ret3.get('row_num') <= 0:
        logging.info('add instance_host info error when create instance, insert_data: %s', instance_host_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    # 往instance_ip表添加记录
    instance_ip_data = {
            'instance_id': instance_id,
            'ip_id': ip_id,
            'mac': mac,
            'type': InstanceNicType.MAIN_NETWORK_NIC,
            'isdeleted': '0',
            'created_at': get_datetime_str()
    }
    ret4= ins_ip_s.InstanceIPService().add_instance_ip_info(instance_ip_data)
    if ret4.get('row_num') <= 0:
        logging.info('add instance_ip info error when create instance, insert_data: %s', instance_ip_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    # 往instance_disk表添加记录
    instance_disk_data = {
            'instance_id': instance_id,
            'size_gb': vmdisk,
            'mount_point': '',
            'dev_name': '',
            'isdeleted': '0',
            'created_at': get_datetime_str()
    }
    ret5 = ins_d_s.InstanceDiskService().add_instance_disk_info(instance_disk_data)
    if ret5.get('row_num') <= 0:
        logging.info('add instance_disk info error when create instance, insert_data: %s',
                         instance_disk_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


def v2v_openstack_intodb(hostpool_id):
    '''
                v2v_openstack
            :param hostpool_id:
            :return:
    '''

    # 判断是否为重试操作
    retry = request.values.get('retry')
    # 如果非重试进行以下步骤
    if retry != '1':
        # 入参赋值
        vmname = request.values.get('vm_name').strip()
        vmip = request.values.get('vm_ip').strip()
        flavor_id = request.values.get('flavor_id').strip()
        cloudarea = request.values.get('cloud_area').strip()
        vm_ostype = request.values.get('vm_ostype').strip()
        vm_app_info = request.values.get('vm_app_info').strip()
        vm_owner = request.values.get('vm_owner').strip()
        vm_group_id = request.values.get('group_id').strip()
        user_id = request.values.get('user_id').strip()
        vm_segment = request.values.get('segment').strip()

        # 入参完全性判断
        if not vmname or not vmip  or not flavor_id or not cloudarea or not vm_ostype \
                or not vm_app_info or not vm_owner or not vm_group_id or not user_id or not vm_segment:
            logging.info('params are invalid or missing')
            return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg='入参缺失')
        else:
            # 获取flavor信息
            flavor_info = flavor_service.FlavorService().get_flavor_info(flavor_id)
            if not flavor_info:
                logging.info('id: %s flavor info not in db when create instance', flavor_id)
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='实例规格数据有误，无法进行v2v')
            vmcpu = flavor_info['vcpu']
            vmmem = flavor_info['memory_mb']

            # 获取对应openstack环境的管理节点及ssh账户信息
            if cloudarea == "SIT":
                ctr_host = '10.202.83.12'
                ctr_pass = decrypt(OPENSTACK_SIT_PASS)
            elif cloudarea == "DEV":
                ctr_host = "10.202.123.4"
                ctr_pass = decrypt(OPENSTACK_DEV_PASS)
            else:
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='openstack环境参数错误，无法进行v2v操作')



            #判断vm信息是否输入错误
            vmexist = vm_exist(vmip,ctr_host,ctr_pass)
            if vmexist == False:
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='获取vm信息失败')

            #获取OS版本失败
            osstat,verdata=get_vm_version(ctr_host,ctr_pass,vm_ostype,vmip)
            if osstat == False:
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='获取vmOS版本失败')
            else:
                ver_data = verdata


            # 获取待迁移vm磁盘大小
            vdiskdata = vm_disk_size(vmip, cloudarea, ctr_host, ctr_pass)
            if vdiskdata == False:
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='获取vm磁盘信息失败')
            vdisk=vdiskdata
            data_disk = vdisk - 80

            # 判断待转化vm是否关机
            vmshutdown = vm_stat(vmip, ctr_host, ctr_pass)
            if vmshutdown == False:
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='待转化vm未关机')


            # 获取可用目标host
            host_code,host_data,host_msg = cal_host(hostpool_id, vmcpu, vmmem, data_disk,vm_group_id)
            if host_code < 0:
                return json_helper.format_api_resp(code=host_code, msg=host_msg)
            else:
                host = host_data



            vmhost = ho_s.HostService().get_host_info_by_hostip(host)
            ret_4 = ho_s.pre_allocate_host_resource(vmhost['id'], vmcpu, vmmem, 50)
            if ret_4 != 1:
                logging.error('资源预分配失败')
                message = '资源预分频失败'
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR,msg = message)

            # 获取并录入IP信息

            vm_segment = seg_s.SegmentService().get_segment_info_bysegment(vm_segment)
            if vm_segment == None:
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='网段信息有误，无法进行v2v')
            else:
                segment_id = vm_segment['id']
                vm_netmask = vm_segment['netmask']
                vm_gateway = vm_segment['gateway_ip']
                vm_dns1 = vm_segment['dns1']
                vm_dns2 = vm_segment['dns2']
                vmvlan = vm_segment['vlan']
                ip_data = ip_s.IPService().get_ip_info_by_ipaddress(vmip)
                if ip_data == None:
                    ip_data = {
                        'ip_address': vmip,
                        'segment_id': segment_id,
                        'netmask': vm_netmask,
                        'vlan': vmvlan,
                        'gateway_ip': vm_gateway,
                        'dns1': vm_dns1,
                        'dns2': vm_dns2,
                        'created_at': get_datetime_str(),
                        'status': '1'
                    }
                    ret = ip_s.IPService().add_ip_info(ip_data)
                    if ret.get('row_num') <= 0:
                        logging.info('add ip info error when create v2v task, insert_data: %s', ip_data)
                        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="录入IP信息失败")
                    else:
                        ip_id = ret.get('last_id')
                else:
                    ip_data_status = ip_data['status']
                    vmvlan = ip_data['vlan']
                    if ip_data_status != '0':
                        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="IP与现有环境冲突,无法进行v2v")
                    else:
                        ip_id = ip_data['id']
                        where_data = {
                            'id': ip_id
                        }
                        updata_data = {
                            'status': '1',
                            'updated_at': get_datetime_str()
                        }
                        ret1 = ip_s.IPService().update_ip_info(updata_data, where_data)
                        if not ret1:
                            logging.info('update ip info error when create v2v task, update_data: %s', updata_data)
                            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="更新IP状态失败")

            # 生成request_id
            request_Id = v2v_op.generate_req_id()

            # 生成vm的uuid和mac
            vmuuid = randomUUID()
            vmmac = randomMAC()





            # 信息入instance相关库表
            instance_info = instance_db_info(vmuuid, vmname, vm_app_info, vm_owner, flavor_id, vm_group_id, host, vmmac, data_disk,ip_id,vm_ostype,request_Id,ver_data)
            if instance_info < 0:
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR,msg='信息入库失败')


            #   将步骤信息存入instance_action表
            # 将createdir信息存入instance_action表
            v2v_cd_d1 = {
                'action': v2vActions.CREATE_DEST_DIR,
                'request_id': request_Id,
                'message': 'start',
                'start_time': get_datetime_str()
            }
            in_a_s.InstanceActionsServices().add_instance_action_info(v2v_cd_d1)

            # 将getfile信息存入instance_action表
            v2v_gf_d1 = {
                'action': v2vActions.GET_VM_FILE,
                'request_id': request_Id,
                'message': 'other',
                'start_time': get_datetime_str()
            }
            in_a_s.InstanceActionsServices().add_instance_action_info(v2v_gf_d1)

            # 将copy disk信息存入instance_action表
            v2v_cpd_d1 = {
                'action': v2vActions.COPY_VM_DISK,
                'request_id': request_Id,
                'message': 'other',
                'start_time': get_datetime_str()
            }
            in_a_s.InstanceActionsServices().add_instance_action_info(v2v_cpd_d1)

            # 将copy xml信息存入instance_action表
            v2v_cpx_d1 = {
                'action': v2vActions.COPY_VM_XML,
                'request_id': request_Id,
                'message': 'other',
                'start_time': get_datetime_str()
            }
            in_a_s.InstanceActionsServices().add_instance_action_info(v2v_cpx_d1)

            # 将创建存储池信息存入instance_action表
            v2v_csp_d1 = {
                'action': v2vActions.CREATE_STOR_POOL,
                'request_id': request_Id,
                'message': 'other',
                'start_time': get_datetime_str()
            }
            in_a_s.InstanceActionsServices().add_instance_action_info(v2v_csp_d1)

            # 将vm标准化信息存入instance_action表
            v2v_vmd_d1 = {
                'action': v2vActions.VM_STANDARDLIZE,
                'request_id': request_Id,
                'message': 'other',
                'start_time': get_datetime_str()
            }
            in_a_s.InstanceActionsServices().add_instance_action_info(v2v_vmd_d1)

            # 将vm注册信息存入instance_action表
            v2v_vmdef_d1 = {
                'action': v2vActions.VM_DEFINE,
                'request_id': request_Id,
                'message': 'other',
                'start_time': get_datetime_str()
            }
            in_a_s.InstanceActionsServices().add_instance_action_info(v2v_vmdef_d1)

            # 将IP注入信息存入instance_action表
            v2v_vmipj_d1 = {
                'action': v2vActions.IP_INJECT,
                'request_id': request_Id,
                'message': 'other',
                'start_time': get_datetime_str()
            }
            in_a_s.InstanceActionsServices().add_instance_action_info(v2v_vmipj_d1)

            # 将vm开机信息存入instance_action表
            v2v_vmstar_d1 = {
                'action': v2vActions.VM_START,
                'request_id': request_Id,
                'message': 'other',
                'start_time': get_datetime_str()
            }
            in_a_s.InstanceActionsServices().add_instance_action_info(v2v_vmstar_d1)

            message = '信息已添加至任务队列,等待执行'

            # 将v2v信息存入v2v_task表
            v2v_data = {
                'request_id': request_Id,
                'destory': '0',
                'start_time': get_datetime_str(),
                'status': 0,
                'vm_ip': vmip,
                'vm_name': vmname,
                'vmvlan': vmvlan,
                'flavor_id': flavor_id,
                'cloud_area': cloudarea,
                'vm_ostype': vm_ostype,
                'vm_app_info': vm_app_info,
                'vm_owner': vm_owner,
                'vm_group_id': vm_group_id,
                'user_id': user_id,
                'vm_mac': vmmac,
                'vm_uuid': vmuuid,
                'cancel': '0',
                'dest_dir': '/app/image/' + vmuuid,
                'on_task': '0',
                'port': '10000',
                'source':VMCreateSource.OPENSTACK
            }
            v2v_insert = v2v_op.v2vTaskService().add_v2v_task_info(v2v_data)

            if v2v_insert.get('row_num') <= 0:
                logging.info('insert info to v2v_task failed! %s', v2v_data)
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='信息入库失败')

            # 将目标kvmhost存入信息表
            v2v_op.update_v2v_desthost(request_Id, host)

            v2v_op.update_v2v_step(request_Id,v2vActions.BEGIN)
            return json_helper.format_api_resp(code=ErrorCode.SUCCESS,msg = message)