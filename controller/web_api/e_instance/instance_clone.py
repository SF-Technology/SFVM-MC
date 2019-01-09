# -*- coding:utf-8 -*-

import logging
import requests
import json
import time
from config import default
from helper import json_helper
from flask import request

from lib.shell import ansibleCmdV2
from service.s_user.user_service import get_user
from service.s_group import group_service as group_s
from service.s_host import host_service as host_s, host_schedule_service as host_s_s
from model.const_define import ErrorCode, VMStatus, VMTypeStatus,\
    OperationObject, OperationAction,ApiOrigin,VsJobStatus,ActionStatus
from config import KAFKA_TOPIC_NAME
from lib.mq.kafka_client import send_async_msg
from helper.time_helper import get_datetime_str, get_datetime_str_link
from lib.vrtManager.util import randomUUID,randomMAC
from service.s_instance_action import instance_action as ins_a_s
from lib.vrtManager import instanceManager as vmManager
from service.s_ip import segment_service as seg_s
from service.s_instance import instance_host_service as ins_h_s, \
    instance_image_service as ins_img_s, instance_disk_service as ins_d_s, instance_service as ins_s, \
    instance_flavor_service as ins_f_s, instance_group_service as ins_g_s  ,instance_migrate_service as ins_m_s
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
from service.s_operation.operation_service import add_operation_vm
from service.s_request_record import request_record as request_r_s


succeed_http_code = ['200', '500']


@login_required
@add_operation_vm(OperationObject.VM, OperationAction.CLONE_BACKUP)
def instance_clone(instance_id):
    logging.info("####################now print inputdata###########################")
    logging.info(request.data)
    logging.info(request.values)
    logging.info(request.form)
    req_json = request.data
    req_data = json_helper.loads(req_json)
    vishu_task_id = req_data["apiOrigin"]
    if not vishu_task_id:
        vishnu_id = ' '
    elif vishu_task_id == 'vishnu':
        vishnu_id = vishu_task_id
    else:
        vishnu_id = ' '

    logging.info("####################now print vishunu_id###########################")
    logging.info(vishnu_id)

    # 获取组信息用于检查配额是否足够

    group_data = ins_s.get_group_of_instance(instance_id)
    if not group_data or  group_data['group_id'] == '':
        logging.info('can not get instance group id when clone instance')
        if vishnu_id != " ":
            job_status = VsJobStatus.FAILED
            task_id = ins_s.generate_task_id()
            msg_back(task_id, job_status, instance_id, instance_id)
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="参数错误")

    group_id = group_data['group_id']

    if not instance_id :
        logging.info('the params is invalid when clone instance')
        if vishnu_id != " ":
            job_status = VsJobStatus.FAILED
            task_id = ins_s.generate_task_id()
            msg_back(task_id, job_status, instance_id, instance_id)
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="参数错误")

    ins_flavor_data = ins_s.get_flavor_of_instance(instance_id)
    if ins_flavor_data:
        src_instance_vcpu = ins_flavor_data['vcpu']
        src_instance_mem = ins_flavor_data['memory_mb']
        # 需要统计系统盘和数据盘总大小
        src_instance_sys_disk_size = ins_flavor_data['root_disk_gb']
        data_disk_status, src_instance_data_disk_size = ins_s.get_data_disk_size_of_instance(instance_id)
        if data_disk_status:
            src_instance_disk_size = int(src_instance_data_disk_size) + int(src_instance_sys_disk_size)
            ins_flavor_data['src_instance_disk_size'] = src_instance_disk_size
        else:
            logging.info('get instance data disk size error when clone instance')
            if vishnu_id != " ":
                job_status = VsJobStatus.FAILED
                task_id = ins_s.generate_task_id()
                msg_back(task_id, job_status, instance_id, instance_id)
            return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="获取源vm磁盘信息失败")
    else:
        logging.info('no instance flavor information find in db when clone instance')
        if vishnu_id != " ":
            job_status = VsJobStatus.FAILED
            task_id = ins_s.generate_task_id()
            msg_back(task_id, job_status, instance_id, instance_id)
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="获取源vm的flavor信息失败")

    # 组配额控制
    is_quota_enough = _check_group_quota(group_id, ins_flavor_data, 1)
    if not is_quota_enough:
        logging.error('group %s is no enough quota when create instance', group_id)
        if vishnu_id != " ":
            job_status = VsJobStatus.FAILED
            task_id = ins_s.generate_task_id()
            msg_back(task_id, job_status, instance_id, instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='应用组配额已不够，无法创建实例')

    instance_db_info = ins_s.InstanceService().get_instance_info(instance_id)
    instance_host_db_info = ins_s.get_host_of_instance(instance_id)
    instance_image_db_info = ins_s.get_images_of_clone_instance(instance_id)
    instance_disks_db_info = ins_s.get_full_disks_info_of_instance(instance_id)

    if not instance_db_info or not instance_host_db_info or not instance_image_db_info or not instance_disks_db_info:
        logging.error('can not get instance %s info', instance_id)
        if vishnu_id != " ":
            job_status = VsJobStatus.FAILED
            task_id = ins_s.generate_task_id()
            msg_back(task_id, job_status, instance_id, instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='无法获取待克隆虚拟机信息')

    src_instance_data = ins_s.InstanceService().get_instance_info(instance_id)
    source_vm_uuid = src_instance_data['uuid']

    # 获取host_id
    host_id = instance_host_db_info['id']
    # 获取虚拟机的应用组
    ins_group = ins_g_s.InstanceGroupService().get_instance_group_info(instance_id)
    if not ins_group:
        if vishnu_id != " ":
            job_status = VsJobStatus.FAILED
            task_id = ins_s.generate_task_id()
            msg_back(task_id, job_status, instance_id, instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="无法获取虚拟机所在应用组信息")

    # 获取虚拟机的OS类型
    ostype = instance_image_db_info[0]['system']

    # 获取待克隆vm的镜像文件数量
    def get_source_vm_image_num(vm_uuid, host_ip):
        dest_dir = '/app/image/' + vm_uuid
        ret_image_num, image_num = ansibleCmdV2.get_dir_image_num(host_ip, dest_dir)
        return ret_image_num, image_num

    # 查看原虚拟机状态
    src_instance_name = instance_db_info['name']
    host_ip = instance_host_db_info['ipaddress']
    vm_status = vmManager.libvirt_instance_status(host_ip, src_instance_name)
    # 如果vm状态非运行中或关机，无法进行克隆备份；5关机，1运行中
    if vm_status not in (5, 1):
        logging.error('instance %s status can not clone', instance_id)
        if vishnu_id != " ":
            job_status = VsJobStatus.FAILED
            task_id = ins_s.generate_task_id()
            msg_back(task_id, job_status, instance_id, instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='虚拟机当前状态无法进行克隆备份')
    # 记录源vm状态到old_status
    if vm_status == 1:
        old_status = "3"
    else:
        old_status = "1"
    src_instance_id = instance_id

    # 将源vm置为被克隆中
    where_data = {
        'id': int(instance_id)
    }
    update_data = {
        'status': '103'
    }
    ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)

    # ------------------------------------------ host资源判断开始 -----------------------------------------------
    # 获取可用物理机
    all_hosts_nums, all_hosts_data = host_s.HostService().get_hosts_of_hostpool(instance_host_db_info['hostpool_id'])
    if all_hosts_nums <= 0:
        logging.error('no host in hostpool %s when get migrate host', instance_host_db_info['hostpool_id'])
        err_msg = '克隆失败,无可用物理机'
        # 将源vm置为源状态
        where_data = {
            'id': int(instance_id)
        }
        update_data = {
            'status': old_status
        }
        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
        if vishnu_id != " ":
            job_status = VsJobStatus.FAILED
            task_id = ins_s.generate_task_id()
            msg_back(task_id, job_status, instance_id, instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS, msg=err_msg)

    # 过滤host
    hosts_after_filter = host_s_s.clone_filter_hosts(all_hosts_data, int(all_hosts_nums))
    if len(hosts_after_filter) == 0:
        logging.info('no available host when get migrate host')
        err_msg = '克隆失败,过滤后无可用物理机'
        # 将源vm置为源状态
        where_data = {
            'id': int(instance_id)
        }
        update_data = {
            'status': old_status
        }
        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
        if vishnu_id != " ":
            job_status = VsJobStatus.FAILED
            task_id = ins_s.generate_task_id()
            msg_back(task_id, job_status, instance_id, instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg = err_msg)

    # VM分配给HOST看是否满足
    vm = {
        "vcpu": ins_flavor_data['vcpu'],
        "mem_MB": ins_flavor_data['memory_mb'],
        "disk_GB": src_instance_disk_size,
        "group_id": group_id,
        "count": 1
    }
    host_after_match = host_s_s.clone_match_hosts(hosts_after_filter, vm, ins_group['group_id'], least_host_num=1,
                                                    max_disk=2000)

    if len(host_after_match) == 0:
        logging.info('no available host when get migrate host')
        # 将源vm置为源状态
        where_data = {
            'id': int(instance_id)
        }
        update_data = {
            'status': old_status
        }
        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
        if vishnu_id != " ":
            job_status = VsJobStatus.FAILED
            task_id = ins_s.generate_task_id()
            msg_back(task_id, job_status, instance_id, instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="目标物理机当前资源不满足克隆备份，请选择其他物理机")

    # 排除原host以及有vm迁入的host
    for host_data in host_after_match:
        if host_data['host_id'] == host_id or not _check_has_migrate(host_data['host_id']):
            index_data = host_after_match.index(host_data)
            host_after_match.pop(index_data)
    if len(host_after_match) == 0:
        logging.info('no available host when get migrate host')
        # 将源vm置为源状态
        where_data = {
            'id': int(instance_id)
        }
        update_data = {
            'status': old_status
        }
        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
        if vishnu_id != " ":
            job_status = VsJobStatus.FAILED
            task_id = ins_s.generate_task_id()
            msg_back(task_id, job_status, instance_id, instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="目标物理机当前资源不满足克隆备份，请选择其他物理机")

    dest_host_id = host_after_match[0]['host_id']

    # ------------------------------------------ host资源判断结束 ----------------------------------------------

    # 虚拟机入库预先占用物理机资源
    uuid = randomUUID()
    clone_instance_name = str(instance_db_info['name'] + '-clone' + str(get_datetime_str_link()))
    request_id = ins_s.generate_req_id()
    user_id = get_user()['user_id']

    # 往instance表添加记录
    instance_data = {
        'uuid': uuid,
        'name': clone_instance_name,
        'displayname': clone_instance_name,
        'description': '',
        'status': VMStatus.CREATING,
        'typestatus': VMTypeStatus.NORMAL,
        'isdeleted': '0',
        'app_info': instance_db_info['app_info'],
        'owner': instance_db_info['owner'],
        'created_at': get_datetime_str(),
        'password': instance_db_info['password']
    }
    ret = ins_s.InstanceService().add_instance_info(instance_data)
    if ret.get('row_num') <= 0:
        logging.info('add instance info error when create instance, insert_data: %s', instance_data)
        # 将源vm置为源状态
        where_data = {
            'id': int(src_instance_id)
        }
        update_data = {
            'status': old_status
        }
        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
        if vishnu_id != " ":
            job_status = VsJobStatus.FAILED
            task_id = ins_s.generate_task_id()
            msg_back(task_id, job_status, src_instance_id, src_instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    instance_id = ret.get('last_id')

    # 往instance_flavor表添加记录
    instance_flavor_data = {
        'instance_id': instance_id,
        'flavor_id': ins_flavor_data['flavor_id'],
        'created_at': get_datetime_str()
    }
    ret1 = ins_f_s.InstanceFlavorService().add_instance_flavor_info(instance_flavor_data)
    if ret1.get('row_num') <= 0:
        logging.info('add instance_flavor info error when create instance, insert_data: %s',
                     instance_flavor_data)
        # 将源vm置为源状态
        where_data = {
            'id': int(src_instance_id)
        }
        update_data = {
            'status': old_status
        }
        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
        if vishnu_id != " ":
            job_status = VsJobStatus.FAILED
            task_id = ins_s.generate_task_id()
            msg_back(task_id, job_status, src_instance_id, src_instance_id)
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
        # 将源vm置为源状态
        where_data = {
            'id': int(src_instance_id)
        }
        update_data = {
            'status': old_status
        }
        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
        if vishnu_id != " ":
            job_status = VsJobStatus.FAILED
            task_id = ins_s.generate_task_id()
            msg_back(task_id, job_status, src_instance_id, src_instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    #获取目标host信息
    dest_host_data = host_s.HostService().get_host_info(dest_host_id)
    dest_host_name = dest_host_data['name']


    # 往instance_host表添加记录
    instance_host_data = {
        'instance_id': instance_id,
        'instance_name': clone_instance_name,
        'host_id': dest_host_id,
        'host_name': dest_host_name,
        'isdeleted': '0',
        'created_at': get_datetime_str()
    }
    ret3 = ins_h_s.InstanceHostService().add_instance_host_info(instance_host_data)
    if ret3.get('row_num') <= 0:
        logging.info('add instance_host info error when create instance, insert_data: %s', instance_host_data)
        # 将源vm置为源状态
        where_data = {
            'id': int(src_instance_id)
        }
        update_data = {
            'status': old_status
        }
        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
        if vishnu_id != " ":
            job_status = VsJobStatus.FAILED
            task_id = ins_s.generate_task_id()
            msg_back(task_id, job_status, src_instance_id, src_instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    # host预分配资源
    ret4 = host_s.pre_allocate_host_resource(
        dest_host_id, src_instance_vcpu, src_instance_mem, src_instance_sys_disk_size)
    if ret4 != 1:
        logging.error('pre allocate host resource to db error when create instance')
        # 将源vm置为源状态
        where_data = {
            'id': int(src_instance_id)
        }
        update_data = {
            'status': old_status
        }
        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
        if vishnu_id != " ":
            job_status = VsJobStatus.FAILED
            task_id = ins_s.generate_task_id()
            msg_back(task_id, job_status, src_instance_id, src_instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    # 往instance_image表添加记录
    for _image in instance_image_db_info:
        instance_image_data = {
            'instance_id': instance_id,
            'image_id': _image['id'],
            'created_at': get_datetime_str()
        }
        ret5 = ins_img_s.InstanceImageService().add_instance_image_info(instance_image_data)
        if ret5.get('row_num') <= 0:
            logging.info('add instance_image info error when create instance, insert_data: %s', instance_image_data)
            # 将源vm置为源状态
            where_data = {
                'id': int(src_instance_id)
            }
            update_data = {
                'status': old_status
            }
            ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
            if vishnu_id != " ":
                job_status = VsJobStatus.FAILED
                task_id = ins_s.generate_task_id()
                msg_back(task_id, job_status, src_instance_id, src_instance_id)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    # 往instance_disk表添加记录
    for src_instance_disk in instance_disks_db_info:
        instance_disk_data = {
            'instance_id': instance_id,
            'size_gb': src_instance_disk['size_gb'],
            'mount_point': src_instance_disk['mount_point'],
            'dev_name': src_instance_disk['dev_name'],
            'isdeleted': '0',
            'created_at': get_datetime_str()
        }
        ret6 = ins_d_s.InstanceDiskService().add_instance_disk_info(instance_disk_data)
        if ret6.get('row_num') <= 0:
            logging.info('add instance_disk info error when create instance, insert_data: %s',
                         instance_disk_data)
            # 将源vm置为源状态
            where_data = {
                'id': int(src_instance_id)
            }
            update_data = {
                'status': old_status
            }
            ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
            if vishnu_id != " ":
                job_status = VsJobStatus.FAILED
                task_id = ins_s.generate_task_id()
                msg_back(task_id, job_status, src_instance_id, src_instance_id)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)


    # 获取源vm的网段信息
    src_ip = ins_s.get_ip_of_instance(src_instance_id)
    src_segment_id = src_ip['segment_id']
    segment_data = seg_s.SegmentService().get_segment_info(src_segment_id)
    mac = randomMAC()

    # 源vm拼装disk信息用于后端克隆进程
    snapshot_disk_data = []
    src_instance_data = ins_s.InstanceService().get_instance_info(src_instance_id)
    src_instance_name = src_instance_data['name']
    src_instance_uuid = src_instance_data['uuid']
    get_device_status, vm_disks_info = vmManager.libvirt_get_instance_device(instance_host_db_info['ipaddress'], src_instance_name)
    if get_device_status == -100:
        msg = 'get source vm disk list fail'
        logging.error(msg)
        # 将源vm置为源状态
        where_data = {
            'id': int(src_instance_id)
        }
        update_data = {
            'status': old_status
        }
        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
        if vishnu_id != " ":
            job_status = VsJobStatus.FAILED
            task_id = ins_s.generate_task_id()
            msg_back(task_id, job_status, src_instance_id, src_instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR,msg = msg)

    for disk in vm_disks_info:
        disk_tag = disk['dev']
        snapshot_path = '/app/image/' + src_instance_uuid + '/' + 'snapshot_' + disk_tag
        snapshot_disk_data.append([disk_tag, snapshot_path])

    # 获取源vm的磁盘文件list
    clone_image_list = []
    for disk in vm_disks_info:
        disk_url = disk['image']
        disk_name = disk_url.split('/')[-1]
        clone_image_list.append(disk_name)
    logging.info("clone_image_list")
    logging.info(clone_image_list)

    # 发送异步消息到队列
    task_id = ins_s.generate_task_id()
    logging.info('创建VM 步骤10-10：发送异步消息给队列 '
                 'task %s : send kafka message start when clone instance', task_id)
    data = {
        "routing_key": "INSTANCE.CLONE",
        "send_time": get_datetime_str(),
        "data": {
            "src_instance_id": src_instance_id,
            "instance_id":instance_id,
            "task_id": task_id,
            "request_id": request_id,
            "src_host":instance_host_db_info['ipaddress'],
            "host_ip": dest_host_data['ipaddress'],
            "uuid": uuid,
            "hostname": clone_instance_name,  # 实例名
            "memory_mb": ins_flavor_data['memory_mb'],
            "vcpu": ins_flavor_data['vcpu'],
            "ostype": ostype,
            "user_id": user_id,
            "power_status":old_status,
            "disks": clone_image_list,
            "snapshot_disk_data" :snapshot_disk_data,
            "vishnu_id":vishnu_id,
            "networks": [
                {
                    "net_card_name": "br_bond0." + segment_data['vlan'],
                    "netmask": segment_data['netmask'],
                    "dns1": segment_data['dns1'],
                    "dns2": segment_data['dns2'],
                    "mac": mac,
                    "gateway": segment_data['gateway_ip']
                }
            ]
        }
    }
    ret_kafka = send_async_msg(KAFKA_TOPIC_NAME, data)

    # 如果是维石创建则录入request_recode表
    if vishnu_id != " ":
        logging.info('task %s : create thread successful when create instance', task_id)
        # 录入维石的taskid到工单表格中
        time_now_for_insert_request_to_db = get_datetime_str()
        request_info_data = {
            "api_origin": ApiOrigin.VISHNU,
            "taskid_api": vishnu_id,
            "taskid_kvm": task_id,
            "vm_count": 1,
            "user_id": user_id,
            "start_time": time_now_for_insert_request_to_db,
            "task_status": "0",  # 代表任务执行中
            "response_to_api": "0",
            "istraceing": "0",
            "request_status_collect_time": time_now_for_insert_request_to_db
        }
        request_record_db_ret = request_r_s.RequestRecordService().add_request_record_info(request_info_data)
        if request_record_db_ret.get('row_num') <= 0:
            logging.error('task %s : can not add request record information to db when clone instance', task_id)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR,
                                                             msg='录入工单信息到数据库失败')
        else:
            return json_helper.format_api_resp(code=ErrorCode.SUCCESS,
                                                             msg='start to clone vm')
    else:
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS,msg ="操作成功")



def _check_group_quota(group_id, flavor_info, vm_count):
    '''
        判断应用组配额是否足够
    :param group_id:
    :param flavor_info:
    :param vm_count:
    :return:
    '''
    quota_used = group_s.get_group_quota_used(group_id)
    if not quota_used:
        logging.error('group %s has no quota used info when check group quota', group_id)
        return False

    group_num, group_info = group_s.GroupService().get_group_info(group_id)
    if group_num < 1:
        logging.error('no group %s info when check group quota', group_id)
        return False

    all_cpu_g = group_info[0]['cpu']
    all_mem_gb_g = group_info[0]['mem']
    all_disk_gb_g = group_info[0]['disk']
    all_vm_g = group_info[0]['vm']

    used_cpu_g = quota_used['all_vcpu']
    used_mem_mb_g = quota_used['all_mem_mb']
    used_disk_gb_g = quota_used['all_disk_gb']
    used_vm_g = quota_used['instance_num']

    cpu = flavor_info['vcpu']
    mem_mb = flavor_info['memory_mb']
    disk_gb = flavor_info['src_instance_disk_size']

    if int(used_vm_g) + int(vm_count) > int(all_vm_g):
        logging.error('group %s: vm used %s, apply count %s > all num %s',
                      group_id, used_vm_g, vm_count, all_vm_g)
        return False

    if int(used_cpu_g) + int(cpu) > int(all_cpu_g):
        logging.error('group %s: cpu used %s, flavor cpu %s > all cpu %s',
                      group_id, used_cpu_g, cpu, all_cpu_g)
        return False

    all_mem_mb_g = int(all_mem_gb_g) * 1024
    if int(used_mem_mb_g) + int(mem_mb) > all_mem_mb_g:
        logging.error('group %s: mem used %s, flavor mem %s > all mem %s',
                      group_id, used_mem_mb_g, mem_mb, all_mem_mb_g)
        return False

    if int(used_disk_gb_g) + int(disk_gb) > int(all_disk_gb_g):
        logging.error('group %s: disk used %s, flavor disk %s > all disk %s',
                      group_id, used_disk_gb_g, disk_gb, all_disk_gb_g)
        return False

    return True


def _add_instance_actions(uuid, request_id, user_id, action, message):
    data = {'action': action,
            'instance_uuid': uuid,
            'request_id': request_id,
            'user_id': user_id,
            'message': message
            }
    return ins_a_s.add_instance_actions(data)


def _update_instance_actions(uuid, request_id, user_id, action, status, message):
    return ins_a_s.update_instance_actions(request_id, action, status, message)

def _check_has_migrate(host_id):
    '''
        检查目的物理机当前是否有正在迁入的VM
    :param host_id:
    :return:
    '''
    params = {
        'WHERE_AND': {
            '=': {
                'dst_host_id': host_id,
                'migrate_status': '0'
            }
        },
    }
    migrate_num, migrate_host = ins_m_s.InstanceMigrateService().query_data(**params)
    if migrate_num > 0:
        return False
    return True

# 回调维石接口
def msg_to_vishnu(job_status,src_instance_id,instance_id):
    msg = [
            {
                "status":job_status
            },
            {
                "instance_id":str(instance_id)
            },
            {
                "parent_id":str(src_instance_id)
            }
        ]
    data = json.dumps(msg)
    headers = {"Content-Type": "application/json;charset=UTF-8"}

    url = default.INSTANCE_CLONE_MSG_TO_VS_URL
    logging.info("start requests to /vishnu-web/restservices/MiniArch url:{}, data:{}".format(url, data))
    try:
        # requests模块本身有超时机制，无需自己去编写
        r = requests.post(url, data=data, headers=headers)
        # 设置超时规则，每1s去获取返回结果，结果为空或者查询未超过3s，继续等待1
        timeout = 5
        poll_seconds = 1
        deadline = time.time() + timeout
        while time.time() < deadline and not r.status_code:
            time.sleep(poll_seconds)
        logging.info("requests to /vishnu-web/restservices/MiniArch data:{},status_code:{}".format(data, r.status_code))
        if not r.status_code:
            return str(ErrorCode.SYS_ERR)
        return str(r.status_code)
    except Exception as err:
        logging.error('post to vs error because:%s' % err)
        return str(ErrorCode.SYS_ERR)


# 回调维石接口并更新trace_request
def msg_back(task_id,job_status,src_instance_id,instance_id):
    ret_to_vs = msg_to_vishnu(job_status, src_instance_id, instance_id)
    if ret_to_vs not in succeed_http_code:
        response_to_api_status = '2'
    else:
        response_to_api_status = '1'
    update_db_time = get_datetime_str()
    if job_status == VsJobStatus.SUCCEED:
        updata_task_status = ActionStatus.SUCCSESS
    else:
        updata_task_status = ActionStatus.FAILD
    _update_data = {
        'task_status': updata_task_status,
        'response_to_api': response_to_api_status,
        'finish_time': update_db_time,
        'request_status_collect_time': update_db_time,
    }
    _where_data = {
        'taskid_kvm': task_id,
    }
    ret = request_r_s.RequestRecordService().update_request_status(_update_data, _where_data)
    if ret <= 0:
        logging.error('update request %s status to db failed' % task_id)
        return False
    else:
        logging.error('update request %s status to db successd' % task_id)
        return True