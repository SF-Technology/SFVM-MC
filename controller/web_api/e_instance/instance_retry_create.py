# -*- coding:utf-8 -*-
# __author__ =  ""

# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
from flask import request
import threading
import json_helper
import logging
from service.s_image import image_service
from service.s_instance import instance_service as ins_s
from service.s_hostpool import hostpool_service
from lib.mq.kafka_client import send_async_msg
from model.const_define import ErrorCode, ImageType, VMStatus
from helper.time_helper import get_datetime_str
from config import KAFKA_TOPIC_NAME


@login_required
def instance_retry_create(request_id_list):
    '''
        虚拟机重新创建，通过request_id重新发送kafka消息
    :return:
    '''
    threads = []
    req_ids = request_id_list
    #req_ids = request.values.get('request_ids')
    if not req_ids:
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    req_ids_list = req_ids.split(',')
    for req_id in req_ids_list:
        ins_info = ins_s.InstanceService().get_instance_info_by_requestid(req_id)
        if ins_info:
            if ins_info['status'] != '100':
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
        return logging.error('task %s : can not find instance info '
                             'when retry create instance send kafka msg', task_id)
    if _ins_info['isdeleted'] == '1':
        return logging.error('task %s : instance has been deleted '
                             'when retry create instance send kafka msg', task_id)

    _ins_host_ip = ins_s.get_hostip_of_instance(_ins_info['id'])
    _ins_hostpool_db_info = ins_s.get_hostpool_of_instance(_ins_info['id'])
    _ins_flavor_db_info = ins_s.get_flavor_of_instance(_ins_info['id'])

    if not _ins_host_ip or not _ins_hostpool_db_info or not _ins_flavor_db_info:
        return logging.error('task %s : instance host, hostpool or  flavor information'
                             'when retry create instance send kafka msg', task_id)

    # 获取虚拟机数据盘大小
    ret_disk_status, vm_disk_gb = ins_s.get_data_disk_size_of_instance(_ins_info['id'])
    if not ret_disk_status:
        return logging.error('task %s : instance data disk size can not find'
                             'when retry create instance send kafka msg', task_id)

    # 获取虚拟机对应网段信息
    segment_data = ins_s.get_net_segment_info_of_instance(_ins_info['id'])
    if not segment_data:
        return logging.error('task %s : instance segment information can not find'
                             'when retry create instance send kafka msg', task_id)

    # 获取虚拟机所在机房类型
    vm_env = hostpool_service.get_env_of_hostpool(_ins_hostpool_db_info['id'])
    if not vm_env:
        return logging.error('task %s : instance env information can not find'
                             'when retry create instance send kafka msg', task_id)

    ins_images = ins_s.get_images_of_instance(_ins_info['id'])
    if not ins_images:
        return logging.error('task %s : instance image information can not find'
                             'when retry create instance send kafka msg', task_id)
    else:
        instance_system = ins_images[0]['system']
        image_name = ins_images[0]['name']

    # 获取镜像信息，一个image_name可能对应多个id
    image_nums, image_data = image_service.ImageService().get_images_by_name(image_name)
    if image_nums <= 0:
        return logging.error('task %s : instance image information can not find'
                             'when retry create instance send kafka msg', task_id)

    # 拼装消息需要的镜像信息
    image_list = []
    # 数据盘数量
    data_image_num = 0
    for _image in image_data:
        _image_type = _image['type']
        _info = {
            "disk_format": _image['format'],
            "url": _image['url'],
            "image_size_gb": _image['size_gb']  # 镜像预分配大小
        }
        # 系统盘
        if _image_type == ImageType.SYSTEMDISK:
            _disk_name = _ins_info['name'] + '.img'
            _info['image_dir_path'] = '/app/image/' + _ins_info['uuid'] + '/' + _disk_name
            _info['disk_name'] = _disk_name
            _info['disk_size_gb'] = None
            _info['dev_name'] = 'vda'
        else:
            # 数据盘
            _disk_name = _ins_info['name'] + '.disk' + str(data_image_num + 1)
            _disk_dev_name = _get_vd_map(data_image_num)
            _info['image_dir_path'] = '/app/image/' + _ins_info['uuid'] + '/' + _disk_name
            _info['disk_name'] = _disk_name
            _info['disk_size_gb'] = int(vm_disk_gb)
            _info['dev_name'] = _disk_dev_name
            data_image_num += 1
        image_list.append(_info)

    # 发送异步消息到队列
    data = {
        "routing_key": "INSTANCE.CREATE",
        "send_time": get_datetime_str(),
        "data": {
            "task_id": task_id,
            "request_id": request_id,
            "host_ip": _ins_host_ip,
            "uuid": _ins_info['uuid'],
            "hostname": _ins_info['name'],  # 实例名
            "memory_mb": _ins_flavor_db_info['memory_mb'],
            "vcpu": _ins_flavor_db_info['vcpu'],
            "ostype": instance_system,
            "user_id": _ins_info['owner'],
            "disks": image_list,
            "disk_size": int(vm_disk_gb),
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
    return 'all done'


def _get_vd_map(vd_index):
    '''
        处理vd设备映射
    :param vd_index:
    :return:
    '''
    vd_arr = ['b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't']
    return 'vd' + vd_arr[vd_index]
