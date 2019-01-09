# -*- coding:utf-8 -*-
# __author__ =  ""


from flask import request
import threading
import json_helper
import logging
from service.s_image import image_service
from service.s_instance import instance_service as ins_s
from service.s_instance import instance_host_service as ins_h_s
from service.s_instance import instance_clone_create as ins_c_c
from service.s_instance import instance_image_service as ins_i_s
from service.s_hostpool import hostpool_service
from service.s_host import host_service as ho_s
from lib.mq.kafka_client import send_async_msg
from model.const_define import ErrorCode, VMStatus
from helper.time_helper import get_datetime_str
from config import KAFKA_TOPIC_NAME



def instance_clone_retry_create(request_id_list):
    '''
        虚拟机重新克隆创建，通过request_id重新发送kafka消息
    :return:
    '''
    threads = []
    req_ids = request_id_list
    if not req_ids:
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    req_ids_list = req_ids.split(',')
    for req_id in req_ids_list:
        ins_info = ins_s.InstanceService().get_instance_info_by_requestid(req_id)
        if ins_info:
            if ins_info['status'] != '102':
                continue
            kafka_send_thread = threading.Thread(target=instance_msg_send_to_kafka, args=(ins_info['task_id'], req_id,))
            threads.append(kafka_send_thread)
            kafka_send_thread.start()

    # 判断多线程是否结束
    if len(threads) == 0:
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data='没有找到需要重试的虚拟机')

    for t in threads:
        t.join()

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


def instance_msg_send_to_kafka(task_id, request_id):
    '''
        通过传入的task_id, request_id拼凑消息发送kafka，可供外部接口调用
    :param request_id:
    :return:
    '''
    _ins_info = ins_s.InstanceService().get_instance_info_by_requestid(request_id)
    if not _ins_info:
        logging.error('task %s : can not find instance info '
                             'when retry create instance send kafka msg', task_id)
        return False, "can not find instance info", _ins_info['name']

    if _ins_info['isdeleted'] == '1':
        logging.error('task %s : instance has been deleted '
                             'when retry create instance send kafka msg', task_id)
        return False, "instance has been deleted", _ins_info['name']

    _ins_host_ip = ins_s.get_hostip_of_instance(_ins_info['id'])
    _ins_hostpool_db_info = ins_s.get_hostpool_of_instance(_ins_info['id'])
    _ins_flavor_db_info = ins_s.get_flavor_of_instance(_ins_info['id'])

    if not _ins_host_ip or not _ins_hostpool_db_info or not _ins_flavor_db_info:
        logging.error('task %s : instance host, hostpool or  flavor information'
                             'when retry create instance send kafka msg', task_id)
        return False, "instance host, hostpool or  flavor information error", _ins_info['name']

    # 获取虚拟机数据盘大小
    src_instance_sys_disk_size = _ins_flavor_db_info['root_disk_gb']
    data_disk_status, src_instance_data_disk_size = ins_s.get_data_disk_size_of_instance(_ins_info['id'])
    if not data_disk_status:
        logging.error('task %s : instance data disk size can not find'
                             'when retry create instance send kafka msg', task_id)
        return False, "instance data disk size can not find", _ins_info['name']

    src_instance_disk_size = int(src_instance_data_disk_size) + int(src_instance_sys_disk_size)
    _ins_flavor_db_info['src_instance_disk_size'] = src_instance_disk_size
    vm_disk_gb = int(src_instance_disk_size) if int(src_instance_disk_size) > 50 else 50


    # 获取虚拟机对应网段信息
    segment_data = ins_s.get_net_segment_info_of_instance(_ins_info['id'])
    if not segment_data:
        logging.error('task %s : instance segment information can not find'
                             'when retry create instance send kafka msg', task_id)
        return False, "instance segment information can not find", _ins_info['name']

    # 获取虚拟机所在机房类型
    vm_env = hostpool_service.get_env_of_hostpool(_ins_hostpool_db_info['id'])
    if not vm_env:
        logging.error('task %s : instance env information can not find'
                             'when retry create instance send kafka msg', task_id)
        return False, "instance env information can not find", _ins_info['name']

    ins_images = ins_s.get_images_of_instance(_ins_info['id'])
    if not ins_images:
        logging.error('task %s : instance image information can not find'
                             'when retry create instance send kafka msg', task_id)
        return False, "instance image information can not find", _ins_info['name']

    else:
        instance_system = ins_images[0]['system']
        image_name = ins_images[0]['name']

    # 获取镜像信息，一个image_name可能对应多个id
    image_nums, image_data = image_service.ImageService().get_images_by_name(image_name)
    if image_nums <= 0:
        logging.error('task %s : instance image information can not find'
                             'when retry create instance send kafka msg', task_id)
        return False, "instance image information can not find", _ins_info['name']

    #BT源信息获取
    source_ip = _ins_info['clone_source_host']
    source_vm = _ins_info['clone_source_vm']

    #instance相关信息
    instance_id = _ins_info['id']
    uuid = _ins_info['uuid']
    host_id = ins_h_s.get_ins_host_info_by_ins_id(instance_id)['host_id']
    host_ip = ho_s.HostService().get_host_info(host_id)['ipaddress']
    instance_name = _ins_info['name']



    #获取source_disk_list
    source_instance_info = ins_s.InstanceService().get_instance_info_by_name(source_vm)
    if not source_instance_info:
        logging.info('克隆源vm %s 不存在' % source_vm)
        return False, "克隆源vm %s 不存在" % source_vm

    source_instance_id = source_instance_info['id']
    instance_clone_create_data = ins_c_c.get_ins_clone_create_info_by_task_id(task_id)
    if not instance_clone_create_data:
        logging.info('获取克隆创建源vm信息失败')
        return False, "获取克隆创建源vm信息失败"

    clone_image_num = instance_clone_create_data['torrent_num']
    source_disk_list = []
    for i in range(int(clone_image_num)):
        clone_image_name = source_vm + '_' + task_id + '_' + str(i)
        source_disk_list.append(clone_image_name)

    # 获取源vm的镜像名称
    sour_instance_image = ins_i_s.get_ins_image_info_by_ins_id(source_instance_id)
    total_size = instance_clone_create_data["total_size"]
    trans_type = instance_clone_create_data["trans_type"]
    http_port = instance_clone_create_data["http_port"]
    md5_check = instance_clone_create_data["md5_check"]
    sour_image_id = sour_instance_image['image_id']
    sour_image_data = image_service.ImageService().get_image_info(sour_image_id)
    image_name = sour_image_data['name']





    # 发送异步消息到队列
    data = {
        "routing_key": "INSTANCE.CLONECREATE",
        "send_time": get_datetime_str(),
        "data": {
            "task_id": task_id,
            "source_ip":source_ip,
            "request_id": request_id,
            "instance_id":instance_id,
            "host_ip": host_ip,
            "uuid": uuid,
            "trans_type": trans_type,
            "http_port": http_port,
            "md5_check": md5_check,
            'source_vm':source_vm,
            "hostname": instance_name,  # 实例名
            "memory_mb": _ins_flavor_db_info['memory_mb'],
            "vcpu": _ins_flavor_db_info['vcpu'],
            "ostype": instance_system,
            "user_id": _ins_info['owner'],
            "clone_image_num": clone_image_num,
            "disks":source_disk_list,
            "total_size": total_size,
            "image_name": image_name,
            "net_area_id": segment_data['net_area_id'],
            "networks": [
                {
                    "net_card_name": "br_bond0." + segment_data['vlan'],
                    "ip": segment_data['ip_address'],
                    "netmask": segment_data['netmask'],
                    "dns1": segment_data['dns1'],
                    "dns2": segment_data['dns2'],
                    "mac": segment_data['mac'],
                    "gateway": segment_data['gateway_ip'],
                    "env": vm_env  # SIT STG PRD DR
                }
            ]
        }
    }
    ret_kafka = send_async_msg(KAFKA_TOPIC_NAME, data)
    # 修改虚拟机状态为创建中
    update_data = {
        'status': VMStatus.CREATING,
        'created_at': get_datetime_str(),
        'updated_at': get_datetime_str()
    }
    where_data = {
        'uuid': _ins_info['uuid']
    }
    ins_s.InstanceService().update_instance_info(update_data, where_data)
    return 'done'


def _get_vd_map(vd_index):
    '''
        处理vd设备映射
    :param vd_index:
    :return:
    '''
    vd_arr = ['b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't']
    return 'vd' + vd_arr[vd_index]
