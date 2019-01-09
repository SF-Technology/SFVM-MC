# coding=utf8
'''
    v2v_esx
'''
# __author__ = 'anke'


import logging
from helper import json_helper
from model.const_define import ErrorCode,VMStatus,VMTypeStatus,VMCreateSource,esx_v2vActions, InstanceNicType
from flask import request
from config.default import OPENSTACK_DEV_USER
from service.v2v_task import v2v_task_service as v2v_op
from service.s_instance_action import instance_action as in_a_s
from service.s_instance import instance_host_service as ins_h_s, instance_ip_service as ins_ip_s, \
    instance_disk_service as ins_d_s, instance_service as ins_s, \
    instance_flavor_service as ins_f_s, instance_group_service as ins_g_s
from service.s_ip import ip_service as ip_s ,segment_service as seg_s
from service.s_flavor import flavor_service
from service.s_host import host_service as ho_s
from service.v2v_task import v2v_instance_info as v2v_in_i
from lib.vrtManager.util import randomUUID, randomMAC
from helper.time_helper import get_datetime_str
from pyVim.connect import SmartConnectNoSSL, Disconnect
import base64
from calc_dest_host import calc_dest_host as cal_host




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


def v2v_esx_intodb(hostpool_id):
    '''
                v2v_esx
            :param hostpool_id:
            :return:
    '''

    #获取vm入库信息
    vmname = request.values.get('vm_name')
    vmip = request.values.get('vm_ip')
    flavor_id = request.values.get('flavor_id')
    vm_ostype = request.values.get('vm_ostype')
    vm_app_info = request.values.get('vm_app_info')
    vm_owner = request.values.get('vm_owner')
    vm_group_id = request.values.get('vm_group_id')
    user_id = request.values.get('user_id')
    vm_segment = request.values.get('segment')
    vm_osver = request.values.get('vm_osver')
    vm_disk = request.values.get('vm_disk')
    esx_env = request.values.get('esx_env')
    esx_ip = request.values.get('esx_ip')
    esx_passwd1 = request.values.get('esx_passwd')
    vmware_vm = request.values.get('vmware_vm')


    # 入参完全性判断
    if not vmname or not vmip  or not flavor_id or not  vm_ostype or not vm_app_info \
        or not vm_osver or not vm_disk  or not vm_owner or not vm_group_id or not user_id or not vm_segment or not esx_passwd1:
        logging.info('params are invalid or missing')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg='入参缺失')
    else:
        esx_passwd = base64.b64decode(esx_passwd1)
        powertag,msg_power = vm_powerState(esx_ip,esx_passwd,vmware_vm)
        if not powertag:
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=msg_power)

        # 获取flavor信息
        flavor_info = flavor_service.FlavorService().get_flavor_info(flavor_id)
        if not flavor_info:
            logging.info('id: %s flavor info not in db when create instance', flavor_id)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='实例规格数据有误，无法进行v2v')
        vmcpu = flavor_info['vcpu']
        vmmem = flavor_info['memory_mb']


        data_disk = int(vm_disk)

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
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=message)

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

        if not vm_osver:
            vm_osver = "unknown"

        # 信息入instance相关库表
        instance_info = instance_db_info(vmuuid, vmname, vm_app_info, vm_owner, flavor_id, vm_group_id, host, vmmac, data_disk,ip_id,vm_ostype,request_Id,vm_osver)
        if instance_info < 0:
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR,msg='信息入库失败')


        #   将步骤信息存入instance_action表
        v2v_cd_d1 = {
            'action': esx_v2vActions.CREATE_DEST_DIR,
            'request_id': request_Id,
            'message': 'start',
            'start_time': get_datetime_str()
        }
        in_a_s.InstanceActionsServices().add_instance_action_info(v2v_cd_d1)

        v2v_cr_pl = {
            'action': esx_v2vActions.CREATE_STOR_POOL,
            'request_id': request_Id,
            'message': 'other',
            'start_time': get_datetime_str()
        }
        in_a_s.InstanceActionsServices().add_instance_action_info(v2v_cr_pl)


        v2v_cp_fl = {
            'action': esx_v2vActions.COPY_FILE_TO_LOCAL,
            'request_id': request_Id,
            'message': 'other',
            'start_time': get_datetime_str()
        }
        in_a_s.InstanceActionsServices().add_instance_action_info(v2v_cp_fl)

        v2v_file = {
            'action': esx_v2vActions.VIRT_V2V_FILES,
            'request_id': request_Id,
            'message': 'other',
            'start_time': get_datetime_str()
        }
        in_a_s.InstanceActionsServices().add_instance_action_info(v2v_file)

        v2v_del_tmp = {
            'action': esx_v2vActions.DELETE_TMP_FILE,
            'request_id': request_Id,
            'message': 'other',
            'start_time': get_datetime_str()
        }
        in_a_s.InstanceActionsServices().add_instance_action_info(v2v_del_tmp)

        v2v_sysdisk_std = {
            'action': esx_v2vActions.VM_SYS_DISK_STD,
            'request_id': request_Id,
            'message': 'other',
            'start_time': get_datetime_str()
        }
        in_a_s.InstanceActionsServices().add_instance_action_info(v2v_sysdisk_std)

        v2v_datadisk_std = {
            'action': esx_v2vActions.VM_DATA_DISK_STD,
            'request_id': request_Id,
            'message': 'other',
            'start_time': get_datetime_str()
        }
        in_a_s.InstanceActionsServices().add_instance_action_info(v2v_datadisk_std)

        v2v_def_1 = {
            'action': esx_v2vActions.VM_DEFINE1,
            'request_id': request_Id,
            'message': 'other',
            'start_time': get_datetime_str()
        }
        in_a_s.InstanceActionsServices().add_instance_action_info(v2v_def_1)

        v2v_star_1 = {
            'action': esx_v2vActions.VM_START1,
            'request_id': request_Id,
            'message': 'other',
            'start_time': get_datetime_str()
        }
        in_a_s.InstanceActionsServices().add_instance_action_info(v2v_star_1)

        if vm_ostype == "Windows":

            v2v_att_disk = {
                'action': esx_v2vActions.ATTACH_DISK,
                'request_id': request_Id,
                'message': 'other',
                'start_time': get_datetime_str()
            }
            in_a_s.InstanceActionsServices().add_instance_action_info(v2v_att_disk)

            v2v_win_std = {
                'action': esx_v2vActions.WINDOWS_STD,
                'request_id': request_Id,
                'message': 'other',
                'start_time': get_datetime_str()
            }
            in_a_s.InstanceActionsServices().add_instance_action_info(v2v_win_std)

            v2v_vm_def2 = {
                'action': esx_v2vActions.WINDOWS_DISK_CH,
                'request_id': request_Id,
                'message': 'other',
                'start_time': get_datetime_str()
            }
            in_a_s.InstanceActionsServices().add_instance_action_info(v2v_vm_def2)

            v2v_vm_star2 = {
                'action': esx_v2vActions.VM_START2,
                'request_id': request_Id,
                'message': 'other',
                'start_time': get_datetime_str()
            }
            in_a_s.InstanceActionsServices().add_instance_action_info(v2v_vm_star2)


        message = '信息已添加至任务队列,等待执行'

        # 将v2v信息存入v2v_task表
        v2v_data = {
            'source':VMCreateSource.ESX,
            'request_id': request_Id,
            'destory': '0',
            'start_time': get_datetime_str(),
            'status': 0,
            'vm_ip': vmip,
            'vm_name': vmname,
            'vmvlan': vmvlan,
            'flavor_id': flavor_id,
            'cloud_area': esx_env,
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
            'dest_host':host,
            'esx_ip':esx_ip,
            'esx_passwd':esx_passwd,
            'vmware_vm':vmware_vm,
            'step_done':esx_v2vActions.BEGIN
        }
        v2v_insert = v2v_op.v2vTaskService().add_v2v_task_info(v2v_data)

        if v2v_insert.get('row_num') <= 0:
            logging.info('insert info to v2v_task failed! %s', v2v_data)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='信息入库失败')

        return json_helper.format_api_resp(code=ErrorCode.SUCCESS,msg = message)

def vm_powerState(esx_ip,esx_passwd,vm_name):
    try:
        c = SmartConnectNoSSL(host=esx_ip, user=OPENSTACK_DEV_USER, pwd=esx_passwd)
    except Exception as e:
        msg_del = "连接目标esxi失败"
        return False,msg_del
    datacenter = c.content.rootFolder.childEntity[0]
    vms = datacenter.vmFolder.childEntity
    vmlist = []
    for i in vms:
        vmlist.append(i.name)
    if vm_name not in vmlist:
        err_detail = "ESXi中未找到目标vm"
        return False,err_detail
    else:
        index = vmlist.index(vm_name)
        index_int = int(index)
        vm = vms[index_int]
        vm_state = vms[index_int].summary.runtime.powerState
        if not vm_state:
            msg_del = "获取vm状态失败"
            Disconnect(c)
            return False,msg_del
        elif vm_state != "poweredOff":
            msg_del = "vm未关机"
            Disconnect(c)
            return False,msg_del
        else:
            msg = "VM已关机"
            Disconnect(c)
            return True,msg