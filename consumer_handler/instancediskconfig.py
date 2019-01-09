# -*- coding:utf-8 -*-


import logging
from helper import json_helper
from lib.shell import ansibleCmdV2
from model.const_define import InstaceActions, ActionStatus
from service.s_instance.instance_service import get_hostip_of_instance, InstanceService
from service.s_instance_action import instance_action as ins_a_s
from service.s_instance import instance_disk_service as ins_d_s
from lib.vrtManager import instanceManager as vmManager
from helper.time_helper import get_datetime_str


def instance_disk_config(msg_data):
    logging.info("--" * 25)
    logging.info(msg_data)
    msg = json_helper.read(msg_data)
    data = msg.get('data')
    user_id = data.get('user_id')
    request_id = data.get('request_id')
    instance_id = data.get('instance_id')
    vm_uuid = data.get('uuid')
    disks = data.get('disk_msg')
    if request_id is None or instance_id is None:
        return 1
    instance_info = InstanceService().get_instance_info(instance_id)
    for disk in disks:
        # 查看虚拟机mount所在磁盘位置、磁盘当前大小，vg、lv名称
        host_ip = get_hostip_of_instance(instance_id)
        mount_point = disk['mount_point']
        if mount_point and host_ip and instance_info['name']:
            vm_name = instance_info['name']
            status, disk_path, disk_size, vm_vg_lv, _message = _check_volume_is_existed_and_volume_size(host_ip,
                                                                                                        vm_uuid,
                                                                                                        vm_name,
                                                                                                        mount_point,
                                                                                                        request_id,
                                                                                                        user_id)
            if status:
                if disk['size_gb'] <= disk_size:
                    logging.info('disk size user input less than now, failed')
                else:
                    add_instance_actions(vm_uuid, request_id, user_id, InstaceActions.INSTANCE_DISK_RESIZE, 'start')
                    connect_disk_resize = vmManager.libvirt_get_connect(host_ip, conn_type='instance', vmname=vm_name)
                    disk_resize_status, disk_resize_msg = vmManager.libvirt_config_disk_resize(connect_disk_resize,
                                                                                               disk_path,
                                                                                               int(disk['size_gb']))
                    logging.info(disk_resize_msg)
                    if disk_resize_status:
                        instance_disk_resize_status = ActionStatus.SUCCSESS
                        _message = 'instance %s disk %s resize successful' % (vm_name, disk_path)
                        update_instance_actions(vm_uuid, request_id, user_id, InstaceActions.INSTANCE_DISK_RESIZE,
                                                instance_disk_resize_status, _message)
                        print 'start to get disk dev:'
                        add_instance_actions(vm_uuid, request_id, user_id, InstaceActions.INSTANCE_DISK_DEVICE, 'start')
                        connect_disk_device_get = vmManager.libvirt_get_connect(host_ip, conn_type='instance',
                                                                                vmname=vm_name)
                        disk_device_status, disk_dev = vmManager.libvirt_get_disk_device_by_path(connect_disk_device_get,
                                                                                                 disk_path)
                        logging.info('disk device is: ' + disk_dev)
                        if disk_device_status:
                            instance_disk_device_status = ActionStatus.SUCCSESS
                            _message = 'instance %s disk device get successful, device name is %s' % (vm_name,
                                                                                                      disk_dev)
                            update_instance_actions(vm_uuid, request_id, user_id, InstaceActions.INSTANCE_DISK_DEVICE,
                                                    instance_disk_device_status, _message)
                            # 查看虚拟机状态
                            add_instance_actions(vm_uuid, request_id, user_id, InstaceActions.INSTANCE_STATUS_CHECK,
                                                 'start')
                            print 'start to check instance %s status' % instance_id
                            instance_info = InstanceService().get_instance_info(instance_id)
                            if instance_info['status'] == '3':
                                instance_status = ActionStatus.SUCCSESS
                                _message = 'instance %s is running' % vm_name
                                update_instance_actions(vm_uuid, request_id, user_id,
                                                        InstaceActions.INSTANCE_STATUS_CHECK,
                                                        instance_status, _message)
                                add_instance_actions(vm_uuid, request_id, user_id, InstaceActions.INSTANCE_DISK_INJECT_TO_OS,
                                                     'start')
                                # 下发qemu agent命令
                                connect_disk_inject = vmManager.libvirt_get_connect(host_ip, conn_type='instance',
                                                                                    vmname=vm_name)
                                disk_add_size = str(int(disk['size_gb']) - int(disk_size) - 1)
                                inject_disk_stauts, result_msg = vmManager.libvirt_inject_resize_disk(connect_disk_inject,
                                                                                                      disk_dev,
                                                                                                      vm_vg_lv,
                                                                                                      disk_add_size)
                                logging.info(result_msg)
                                if inject_disk_stauts:
                                    instance_disk_inject_on_os_status = ActionStatus.SUCCSESS
                                    _message = 'instance %s disk resize on os successful' % vm_name
                                    update_instance_actions(vm_uuid, request_id, user_id,
                                                            InstaceActions.INSTANCE_DISK_INJECT_TO_OS,
                                                            instance_disk_inject_on_os_status, _message)
                                    # 修改数据库虚拟机磁盘大小
                                    update_data = {
                                        'size_gb': disk['size_gb'],
                                        'updated_at': get_datetime_str()
                                    }
                                    where_data = {
                                        'instance_id': instance_id,
                                        'mount_point': mount_point
                                    }
                                    ret = ins_d_s.InstanceDiskService().update_instance_disk_info(update_data,
                                                                                                  where_data)
                                else:
                                    instance_disk_inject_on_os_status = ActionStatus.FAILD
                                    _message = 'instance %s disk resize on os failed because %s' % (vm_name,
                                                                                                    result_msg)
                                    update_instance_actions(vm_uuid, request_id, user_id,
                                                            InstaceActions.INSTANCE_DISK_INJECT_TO_OS,
                                                            instance_disk_inject_on_os_status, _message)
                            else:
                                instance_status = ActionStatus.FAILD
                                _message = 'failed: instance %s not running' % vm_name
                                update_instance_actions(vm_uuid, request_id, user_id,
                                                        InstaceActions.INSTANCE_STATUS_CHECK,
                                                        instance_status, _message)
                        else:
                            instance_disk_device_status = ActionStatus.FAILD
                            _message = 'instance %s disk device get failed' % vm_name
                            update_instance_actions(vm_uuid, request_id, user_id, InstaceActions.INSTANCE_DISK_DEVICE,
                                                    instance_disk_device_status, _message)
                    else:
                        instance_disk_resize_status = ActionStatus.FAILD
                        _message = 'instance %s disk %s resize faile because %s' % (vm_name, disk_path, disk_resize_msg)
                        update_instance_actions(vm_uuid, request_id, user_id, InstaceActions.INSTANCE_DISK_RESIZE,
                                                instance_disk_resize_status, _message)
            else:
                logging.info(_message)
    return 'all job done, check whether has error in database instance'


def _check_volume_is_existed_and_volume_size(host_ip, vm_uuid, vm_name, mount_point, request_id, user_id):
    add_instance_actions(vm_uuid, request_id, user_id, InstaceActions.INSTANCE_DISK_MOUNTPOINT_CHECK, 'start')
    vm_mount_point_check_status = ActionStatus.SUCCSESS
    _message = ''
    check_status, vm_lv_name, vm_vg_lv = ansibleCmdV2.ansible_remote_check_disk_mount_point(host_ip, vm_uuid, vm_name, mount_point)
    if check_status is 1:
        vm_mount_point_check_status = ActionStatus.FAILD
        _message = 'check vm %s mount point failed because ansible not available' % vm_uuid
    elif not check_status:
        vm_mount_point_check_status = ActionStatus.FAILD
        _message = 'check vm %s mount point failed because because virt-cat error' % vm_uuid
    else:
        if vm_lv_name == '':
            vm_mount_point_check_status = ActionStatus.FAILD
            _message = 'check vm %s mount point not exist' % vm_uuid
        else:
            _message = 'check vm %s mount point exist' % vm_uuid
    update_instance_actions(vm_uuid, request_id, user_id, InstaceActions.INSTANCE_DISK_MOUNTPOINT_CHECK,
                            vm_mount_point_check_status, _message)

    # 如果mount点存在，获取host上磁盘信息
    if vm_mount_point_check_status == ActionStatus.SUCCSESS:
        vm_disk_check = ActionStatus.SUCCSESS
        add_instance_actions(vm_uuid, request_id, user_id, InstaceActions.INSTANCE_DISK_CHECK, 'start')
        disk_check_status, vm_disks = ansibleCmdV2.ansible_remote_check_disk(host_ip, vm_uuid, vm_name)
        if disk_check_status is 1:
            vm_disk_check = ActionStatus.FAILD
            _message = 'check vm %s disk failed because ansible not available' % vm_uuid
        elif not disk_check_status:
            vm_disk_check = ActionStatus.FAILD
            _message = 'check vm %s disk failed because can not find disk' % vm_uuid
        else:
            if len(vm_disks) <= 0:
                vm_disk_check = ActionStatus.FAILD
                _message = 'check vm %s disk failed because can not find disk' % vm_uuid
            else:
                _message = 'check vm %s disk successful' % vm_uuid
        update_instance_actions(vm_uuid, request_id, user_id, InstaceActions.INSTANCE_DISK_CHECK, vm_disk_check, _message)

    # 如果虚拟机有磁盘，获取mount点对应的磁盘名称
    if vm_mount_point_check_status == ActionStatus.SUCCSESS and vm_disk_check == ActionStatus.SUCCSESS:
        vm_lv_size_check = ActionStatus.SUCCSESS
        add_instance_actions(vm_uuid, request_id, user_id, InstaceActions.INSTANCE_DISK_LV_CHECK, 'start')
        disk_size_check_status, vm_disk_lv_on = ansibleCmdV2.ansible_remote_check_vm_lv_size(host_ip, vm_disks,
                                                                                           vm_lv_name)
        if not disk_size_check_status:
            vm_lv_size_check = ActionStatus.FAILD
            _message = 'can not find disk where lv %s on' % vm_lv_name
        else:
            _message = 'lv %s on disk %s' % (vm_lv_name, vm_disk_lv_on[0])
        update_instance_actions(vm_uuid, request_id, user_id, InstaceActions.INSTANCE_DISK_LV_CHECK, vm_lv_size_check, _message)

    # 获取lv已经使用的磁盘大小
    vm_image_size_check = ActionStatus.FAILD
    if vm_mount_point_check_status == ActionStatus.SUCCSESS and vm_disk_check == ActionStatus.SUCCSESS \
            and vm_lv_size_check == ActionStatus.SUCCSESS:
        vm_image_size_check = ActionStatus.SUCCSESS
        add_instance_actions(vm_uuid, request_id, user_id, InstaceActions.INSTANCE_DISK_SIZE_CHECK, 'start')
        # todo 获取磁盘大小
        disk_size_lv_in_check_status, vm_disk_size_lv_on = ansibleCmdV2.ansible_remote_check_vm_lv_in_disk_size(host_ip,
                                                                                                              vm_disk_lv_on[0])
        if not disk_size_lv_in_check_status:
            vm_image_size_check = ActionStatus.FAILD
            _message = 'can not get disk %s size where lv %s on' % (vm_disk_lv_on[0], vm_lv_name)
        else:
            _message = 'disk %s size where lv %s on is %s' % (vm_disk_lv_on[0], vm_lv_name, vm_disk_size_lv_on)
        update_instance_actions(vm_uuid, request_id, user_id, InstaceActions.INSTANCE_DISK_SIZE_CHECK,
                                vm_image_size_check, _message)

    if vm_mount_point_check_status == ActionStatus.SUCCSESS and vm_disk_check == ActionStatus.SUCCSESS \
            and vm_lv_size_check == ActionStatus.SUCCSESS and vm_image_size_check == ActionStatus.SUCCSESS:
        return True, vm_disk_lv_on[0], int(vm_disk_size_lv_on), vm_vg_lv, _message
    else:
        return False, '', '', '', _message


def _check_vm_status(instance_id):

    return ''


def add_instance_actions(uuid, request_id, user_id, action, message):
    data = {'action': action,
            'instance_uuid': uuid,
            'request_id': request_id,
            'user_id': user_id,
            'message': message
            }
    return ins_a_s.add_instance_actions(data)


def update_instance_actions(uuid, request_id, user_id, action, status, message):
    return ins_a_s.update_instance_actions(request_id, action, status, message)
