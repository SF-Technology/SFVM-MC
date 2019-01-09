# coding=utf8
'''
    v2v_esx_batch
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
from cal_dest_host_batch import calc_dest_host_batch as cal_host_batch
import base64
import json





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
        'create_source':VMCreateSource.ESX
    }
    ret = ins_s.InstanceService().add_instance_info(instance_data)
    if ret.get('row_num') <= 0:
        message = 'add instance info error when create instance'
        logging.info('add instance info error when create instance, insert_data: %s', instance_data)
        return False,message

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
        message = 'add v2v_instance info error when create instance'
        return False,message

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
        message = 'add instance_flavor info error when create instance'
        return False,message

    # 往instance_group表添加记录
    instance_group_data = {
        'instance_id': instance_id,
        'group_id': group_id,
        'created_at': get_datetime_str()
    }
    ret2 = ins_g_s.InstanceGroupService().add_instance_group_info(instance_group_data)
    if ret2.get('row_num') <= 0:
        logging.info('add instance_group info error when create instance, insert_data: %s', instance_group_data)
        message = 'add instance_group info error when create instance'
        return False,message


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
        message = 'add instance_host info error when create instance'
        return False,message

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
        message = 'add instance_ip info error when create instance'
        return False,message

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
        message = 'add instance_disk info error when create instance'
        return False,message
    message = "信息入库完成"
    return True,message

#vm单台入库函数
def task_esx_intodb(task):

    #获取vm入参
    vmname = task['vm_name']
    vmip = task['vm_ip']
    flavor_id = task['flavor_id']
    vm_ostype = task['vm_ostype']
    vm_app_info = task['vm_app_info']
    vm_owner = task['vm_owner']
    user_id = task['user_id']
    vm_segment = task['vm_segment']
    esx_env = task['esx_env']
    esx_ip = task['esx_ip']
    esx_passwd1 = task['esx_passwd']
    vmware_vm = task['vmware_vm']
    vm_osver = task['vm_osver']
    vm_group_id = task['vm_group_id']
    dest_host = task['dest_host']
    vm_disk = task['vm_disk']


    # 入参完全性判断
    if not vmname or not vmip  or not flavor_id or not  vm_ostype or not vm_app_info \
        or not vm_osver  or not vm_owner or not user_id or not vm_segment or not esx_passwd1:
        logging.info('params are invalid or missing')
        message = '入参缺失'
        return False,message
    else:
        esx_passwd = base64.b64decode(esx_passwd1)
        # 获取flavor信息
        flavor_info = flavor_service.FlavorService().get_flavor_info(flavor_id)
        if not flavor_info:
            logging.info('id: %s flavor info not in db when create instance', flavor_id)
            message = '实例规格数据有误，无法进行v2v'
            return False,message
        vmcpu = flavor_info['vcpu']
        vmmem = flavor_info['memory_mb']

        host = dest_host


        vmhost = ho_s.HostService().get_host_info_by_hostip(host)
        ret_4 = ho_s.pre_allocate_host_resource(vmhost['id'], vmcpu, vmmem, 50)
        if ret_4 != 1:
            logging.error('资源预分配失败')
            message = '资源预分频失败'
            return False,message

        # 获取并录入IP信息

        vm_segment = seg_s.SegmentService().get_segment_info_bysegment(vm_segment)
        if vm_segment == None:
            message = '网段信息有误，无法进行v2v'
            return False,message
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
                    message = "录入IP信息失败"
                    return False,message
                else:
                    ip_id = ret.get('last_id')
            else:
                ip_data_status = ip_data['status']
                vmvlan = ip_data['vlan']
                if ip_data_status != '0':
                    message = "IP与现有环境冲突,无法进行v2v"
                    return False,message
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
                        message = "更新IP状态失败"
                        return False,message

        # 生成request_id
        request_Id = v2v_op.generate_req_id()

        # 生成vm的uuid和mac
        vmuuid = randomUUID()
        vmmac = randomMAC()

        # 信息入instance相关库表
        instance_tag,instance_info = instance_db_info(vmuuid, vmname, vm_app_info, vm_owner, flavor_id, vm_group_id, host, vmmac, vm_disk,ip_id,vm_ostype,request_Id,vm_osver)
        if not instance_tag :
            message = instance_info
            return False,message


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
            message = '信息入库失败'
            return False,message

        message = '信息已添加至任务队列'
        return True,message

#vm电源状态判断
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

#vm磁盘大小获取
def vm_disksize(esx_ip,esx_passwd,vm_name):
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
        vm_disk = vms[index_int].summary.storage.committed + vms[index_int].summary.storage.uncommitted
        if not vm_disk:
            msg_del = "获取vm磁盘大小失败"
            Disconnect(c)
            return False,msg_del
        else:
            vm_disk_GB = vm_disk / 1024 / 1024 / 1024 + 1
            Disconnect(c)
            return True,vm_disk_GB

#主函数
def esx_intodb_batch():
    #定义整个函数执行情况的returnlist
    check_list = []
    error_list = []
    #将入参转化为list对象
    v2v_list_str = request.values.get('esx_batch')
    v2v_list = json.loads(v2v_list_str)
    total_num = len(v2v_list)
    #对list中每个v2v任务进行vm的信息检测
    for task in v2v_list:
        check_tag,check_res = esx_vm_check(task)
        if not check_tag:
            error_list.append(task)
        else:
            check_list.append(task)

    #如果全部失败则直接返回
    if check_list == []:
        message = "全部失败"
        return_info = error_list
        return json_helper.format_api_resp(code=ErrorCode.ALL_FAIL, msg=message,data = return_info)

    #将检测完后的list按照group_id进行list分组
    group_list = task_into_list(check_list)
    #针对group分组后的list套用host筛选算法
    for task_list in group_list:
        tag1,res1 = cal_group_host(task_list)
        #如果同group下list套用host算法失败，则将这部分task存入errorlist
        if not tag1:
            for task in task_list:
                task["error_message"] = "host资源不足"
                error_list.append(task)

        else:
            #host筛选完成，进行入库操作
            for task in task_list:
                tag2,res2 = task_esx_intodb(task)
                #如果入库失败，则存入returnlist
                if not tag2:
                    task["error_message"] = res2
                    error_list.append(task)

    #统计总errorlist值
    error_num = len(error_list)
    if error_num == total_num:
        message = "全部失败"
        return_code = ErrorCode.ALL_FAIL
    elif error_num == 0:
        message = "全部成功"
        return_code = ErrorCode.SUCCESS
    else:
        message = "部分成功"
        return_code = ErrorCode.SUCCESS
    return json_helper.format_api_resp(code=return_code, msg=message,data=error_list)


#将入参list按照group_id分组函数
def task_into_list(list_get):
    list_value = []
    for list in list_get:
        list_value.append(list['vm_group_id'])
    for value in list_value:
        while list_value.count(value) > 1:
            del list_value[list_value.index(value)]

    n = len(list_value)

    list = [
        [], [], [], [], [], [], [], [], [], []
    ]
    return_list = []

    num = 0
    for v in list_value:
        v_str = str(v)
        for task_info in list_get:
            if task_info['vm_group_id'] == v_str:
                list[num].append(task_info)
        return_list.append(list[num])
        num = num + 1

    return return_list

#针对同一group_id的task list计算host list
def cal_group_host(task_list):
    vm_mem_count = 0
    vm_disk_count = 0
    count = len(task_list)
    # 针对每个分组内的list，计算可用host list
    for task in task_list:
        flavor_id = task['flavor_id']
        vm_group_id = task['vm_group_id']
        vm_disk = task["vm_disk"]
        hostpool_id = task['hostpool_id']
        vm_disk_total = int(vm_disk) + 50
        flavor_info = flavor_service.FlavorService().get_flavor_info(flavor_id)
        vmmem = flavor_info['memory_mb']
        vm_mem_count = vm_mem_count + int(vmmem)
        vm_disk_count = vm_disk_count + vm_disk_total
    code, data, msg = cal_host_batch(hostpool_id,vm_mem_count,vm_disk_count,vm_group_id,count)
    if code < 0:
        return False,msg
    else:
        host_list = data
        host_len = len(host_list)
        #获取host list后，针对每个vm分配host
        task_len = len(task_list)
        for i in range(task_len):
            task_info = task_list[i]
            host_index = i % host_len
            vm_host = host_list[host_index]
            vm_host_ip = vm_host["ip"]
            task_info['dest_host'] = vm_host_ip
        return True, host_list

#单台vm的信息检测和获取
def esx_vm_check(task):
    vmware_vm = task["vmware_vm"]
    esx_ip = task['esx_ip']
    esx_passwd_en = task['esx_passwd']
    vm_ostype = task['vm_ostype']
    esx_passwd = base64.b64decode(esx_passwd_en)
    # 开关机状态判断
    tag1,res1 = vm_powerState(esx_ip,esx_passwd,vmware_vm)
    if not tag1:
        message = res1
        task["error_message"] = res1
        return False,message
    #vm磁盘大小获取
    tag2, res2 = vm_disksize(esx_ip, esx_passwd, vmware_vm)
    if not tag2:
        message = res2
        task["error_message"] = res2
        return False, message
    else:
        if vm_ostype == "Windows":
            vm_disk = int(res2) -50
            if vm_disk < 0:
                vm_disk = 0
            task["vm_disk"] = vm_disk
        else:
            task["vm_disk"] = int(res2)
            vm_disk = int(res2) - 30
            if vm_disk < 0:
                vm_disk = 0
            task["vm_disk"] = vm_disk
        message = "vm磁盘获取成功"
        return True,message