# coding=utf8
'''
    v2v_openstack_batch
'''
# __author__ = 'anke'
import logging
from helper import json_helper
from model.const_define import ErrorCode,v2vActions,VMStatus,VMTypeStatus,VMCreateSource, InstanceNicType
from flask import request
from service.v2v_task import v2v_task_service as v2v_op
from service.s_instance_action import instance_action as in_a_s
from service.s_instance import instance_host_service as ins_h_s, instance_ip_service as ins_ip_s, \
    instance_disk_service as ins_d_s, instance_service as ins_s, \
    instance_flavor_service as ins_f_s, instance_group_service as ins_g_s
from service.s_ip import ip_service as ip_s ,segment_service as seg_s
from service.s_flavor import flavor_service
from service.s_host import host_service as ho_s
from service.v2v_task import v2v_instance_info as v2v_in_i
from cal_dest_host_batch import calc_dest_host_batch as cal_host_batch
from lib.vrtManager.util import randomUUID, randomMAC
from helper.time_helper import get_datetime_str
import json


# 信息入库函数
def instance_db_info(uuid, vmname, vm_app_info, owner, flavor_id, group_id, host, mac, vmdisk, ip_id, vmostype, requestid, ver_data):
    vm_ostype_todb = ''
    vmhost = ho_s.HostService().get_host_info_by_hostip(host)
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
        'create_source': VMCreateSource.OPENSTACK
    }
    ret = ins_s.InstanceService().add_instance_info(instance_data)
    if ret.get('row_num') <= 0:
        logging.info('add instance info error when create instance, insert_data: %s', instance_data)
        message = 'add instance info error when create instance'
        return False, message

    instance_id = ret.get('last_id')
    if vmostype == 'Windows':
        vm_ostype_todb = 'windows'
    elif vmostype == 'Linux':
        vm_ostype_todb = 'linux'

    # 往v2v_instance_info表添加记录
    v2v_instance_data = {
        'instance_id': instance_id,
        'os_type': vm_ostype_todb,
        'isdeleted': '0',
        'created_at': get_datetime_str(),
        'request_id': requestid,
        'os_version': ver_data
    }
    ret_v2v_instance = v2v_in_i.v2vInstanceinfo().add_v2v_instance_info(v2v_instance_data)
    if ret_v2v_instance.get('row_num') <= 0:
        logging.info('add v2v_instance info error when create instance, v2v_instance_data: %s',
                     v2v_instance_data)
        message = 'add v2v_instance info error when create instance'
        return False, message

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
        return False, message

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
        return False, message

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
        return False, message

    # 往instance_ip表添加记录
    instance_ip_data = {
            'instance_id': instance_id,
            'ip_id': ip_id,
            'mac': mac,
            'type': InstanceNicType.MAIN_NETWORK_NIC,
            'isdeleted': '0',
            'created_at': get_datetime_str()
    }
    ret4 = ins_ip_s.InstanceIPService().add_instance_ip_info(instance_ip_data)
    if ret4.get('row_num') <= 0:
        logging.info('add instance_ip info error when create instance, insert_data: %s', instance_ip_data)
        message = 'add instance_ip info error when create instance'
        return False, message

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

    message = "信息入库成功"
    return True, message


def intodb_batch():
    # 定义整个函数执行情况的returnlist
    return_list = []
    # 将入参转化为list对象
    v2v_list_str = request.values.get('openstack_batch')
    v2v_list = json.loads(v2v_list_str)
    total_num = len(v2v_list)
    # 将入参的list按照group_id进行list分组
    group_list = task_into_list(v2v_list)
    # 针对group分组后的list套用host筛选算法
    for task_list in group_list:
        tag1, task_list = cal_group_host(task_list)
        # 如果同group下list套用host算法失败，则将这部分task存入returnlist
        for task in task_list:
            if task.get('error_message'):
                return_list.append(task)

    # 统计总return_list值
    error_num = len(return_list)
    if error_num == total_num:
        message = "全部失败"
        return_code = ErrorCode.ALL_FAIL
    elif error_num == 0:
        message = "全部成功"
        return_code = ErrorCode.SUCCESS
    else:
        message = "部分成功"
        return_code = ErrorCode.SUCCESS
    return json_helper.format_api_resp(code=return_code, msg=message, data=return_list)


# 针对同一group_id的task list计算host list
def cal_group_host(task_list):
    # 针对每个分组内的list，计算可用host list
    for task in task_list:
        flavor_id = task['flavor_id']
        vm_group_id = task['group_id']
        vm_disk = task["vm_disk"]
        hostpool_id = task['hostpool_id']
        vm_disk_total = int(vm_disk) + 50
        flavor_info = flavor_service.FlavorService().get_flavor_info(flavor_id)
        vm_mem = flavor_info['memory_mb']
        code, data, msg = cal_host_batch(hostpool_id, vm_mem, vm_disk_total, vm_group_id, 1)
        if code < 0:
            task["error_message"] = msg
        else:
            host_list = data
            vm_host = host_list[0]
            task['dest_host'] = vm_host["ip"]
            res_task_intodb,msg_task_intodb = task_intodb(task)
            if not res_task_intodb:
                task["error_message"] = msg_task_intodb
    return True, task_list


# 单个task的入库函数
def task_intodb(task):

    # 入参赋值
    vmname = task['vm_name']
    vmip = task['vm_ip']
    flavor_id = task['flavor_id']
    cloudarea = task['cloud_area']
    vm_ostype = task['vm_ostype']
    vm_app_info = task['vm_app_info']
    vm_owner = task['vm_owner']
    vm_group_id = task['group_id']
    user_id = task['user_id']
    vm_segment = task['segment']
    vm_disk = task['vm_disk']
    vm_osver = task['vm_osver']
    host = task['dest_host']

    # 入参完全性判断
    if not vmname or not vmip or not flavor_id or not cloudarea or not vm_ostype \
            or not vm_app_info or not vm_owner or not vm_group_id or not user_id or not vm_segment:
        logging.info('params are invalid or missing')
        message = '入参缺失'
        return False,message
    else:
        # 获取flavor信息
        flavor_info = flavor_service.FlavorService().get_flavor_info(flavor_id)
        if not flavor_info:
            logging.info('id: %s flavor info not in db when create instance', flavor_id)
            message = '实例规格数据有误，无法进行v2v'
            return False,message
        vmcpu = flavor_info['vcpu']
        vmmem = flavor_info['memory_mb']

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
        instance_tag,instance_info = instance_db_info(vmuuid, vmname, vm_app_info, vm_owner, flavor_id, vm_group_id, host, vmmac,
                                         vm_disk, ip_id, vm_ostype, request_Id, vm_osver)
        if not instance_tag:
            message = instance_info
            return False,message

        # 将步骤信息存入instance_action表
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
            'source': VMCreateSource.OPENSTACK
        }
        v2v_insert = v2v_op.v2vTaskService().add_v2v_task_info(v2v_data)

        if v2v_insert.get('row_num') <= 0:
            logging.info('insert info to v2v_task failed! %s', v2v_data)
            message = '信息入库失败'
            return False,message

        # 将目标kvmhost存入信息表
        v2v_op.update_v2v_desthost(request_Id, host)

        v2v_op.update_v2v_step(request_Id, v2vActions.BEGIN)
        return True,message

#将入参list按照group_id分组函数
def task_into_list(list_get):
    list_value = []
    for list in list_get:
        list_value.append(list['group_id'])
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
            if task_info['group_id'] == v_str:
                list[num].append(task_info)
        return_list.append(list[num])
        num = num + 1

    return return_list









