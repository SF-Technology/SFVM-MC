# !/usr/bin/env python2.7
# -*- coding:utf-8 -*-
#


#   Date    :   2017/12/13
#   Desc    :   克隆虚拟机的实际函数

import logging
from helper import json_helper
from lib.shell import ansibleCmdV2
from service.s_host import  host_schedule_service as host_s_s
from service.s_host import host_service as ho_s
from model.const_define import  VMStatus,  InstaceActions, ActionStatus,VsJobStatus
from helper.time_helper import get_datetime_str
from service.s_request_record import request_record as request_r_s
import random
import requests
from lockfile import LockFile
import time
from config import default
from lib.other import fileLock
from service.s_instance_action import instance_action as ins_a_s
from lib.vrtManager import instanceManager as vmManager
import traceback
import threading
import json
from model.const_define import ErrorCode
from service.s_instance import  instance_service as ins_s

succeed_http_code = ['200', '500']


def init_env():
    import sys
    import os
    reload(sys)
    sys.setdefaultencoding('utf-8')
    file_basic_path = os.path.dirname(os.path.abspath(__file__))
    print file_basic_path
    basic_path = file_basic_path[0:-17]
    os.environ["BASIC_PATH"] = basic_path  # basic path 放到全局的一个变量当中去
    sys.path.append(basic_path)
    sys.path.append(basic_path + '/config')
    sys.path.append(basic_path + '/helper')
    sys.path.append(basic_path + '/lib')
    sys.path.append(basic_path + '/model')
    sys.path.append(basic_path + '/controller')
    sys.path.append(basic_path + '/service')
    print sys.path

init_env()


def instance_clone(msg_data):
    logging.info("--" * 25)
    logging.info(msg_data)
    msg = json_helper.read(msg_data)
    data = msg.get('data')
    request_id = data.get('request_id')
    host_ip = data.get('host_ip')
    uuid = data.get('uuid')
    memory_mb = data.get('memory_mb')
    hostname = data.get('hostname')
    vcpu = data.get('vcpu')
    images = data.get('disks')
    networks = data.get('networks')[0]
    user_id = data.get('user_id')
    instance_id = data.get('instance_id')
    src_instance_id = data.get('src_instance_id')
    source_host = data.get('src_host')
    snapshot_disk_data = data.get('snapshot_disk_data')
    vishnu_id = data.get("vishnu_id")
    power_status = data.get("power_status")
    task_id = data.get("task_id")

    # 操作前先判断host上是否有instance_clone任务在运行，有则等待30s，循环检测2hour
    _add_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CHECK_HOST_STATUS, 'start')
    time_count = 0
    while time_count < 28800 and not ho_s.HostService().get_hosts_clone_status(source_host):
        msg = "source host %s is locked while create clone for %s,wait 30s" % (source_host, src_instance_id)
        logging.info(msg)
        time.sleep(30)
        time_count += 30

    if time_count < 28800:
        _update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CHECK_HOST_STATUS,
                                 ActionStatus.SUCCSESS, "host status ok")
        # 更新host状态
        update_host_clone_status(source_host)
        # 添加针对source_host的文件锁，来保证同一台host上的串行
        lock_name = "instance_clone_" + source_host
        with LockFile(lock_name):
            try:
                # 创建虚拟机目录
                logging.info("start create instance dir %s " % uuid)
                print "start create instance dir %s " % uuid
                ret_check_dir,res_msg = _check_image_dir_and_create(request_id, host_ip, uuid, user_id)

                if ret_check_dir == ActionStatus.FAILD:
                    # 將源host狀態解鎖
                    release_host_clone_status(source_host)
                    logging.error(res_msg)
                    vm_create_status = VMStatus.CLONE_ERROR
                    _update_instance_status(uuid, vm_create_status)
                    # 将源vm置为关机
                    where_data = {
                        'id': int(src_instance_id)
                    }
                    update_data = {
                        'status': power_status
                    }
                    ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
                    if vishnu_id != " ":
                        job_status = VsJobStatus.FAILED
                        msg_back(task_id, job_status, src_instance_id, instance_id)
                    return 0

                # 创建虚拟机存储池
                logging.info("start create pool %s " % uuid)
                print "start create pool %s " % uuid
                create_stg_pool_ret = _create_storage_pool(request_id, host_ip, uuid, user_id)
                if create_stg_pool_ret == ActionStatus.FAILD:
                    # 將源host狀態解鎖
                    release_host_clone_status(source_host)
                    logging.error(res_msg)
                    vm_create_status = VMStatus.CLONE_ERROR
                    _update_instance_status(uuid, vm_create_status)
                    where_data = {
                        'id': int(src_instance_id)
                    }
                    update_data = {
                        'status': power_status
                    }
                    ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
                    if vishnu_id != " ":
                        job_status = VsJobStatus.FAILED
                        msg_back(task_id, job_status, src_instance_id, instance_id)
                    return 0

                # 如果源vm为运行中则创建快照文件
                if power_status == "3":
                    logging.info("start to create disk snapshot for  vm %s" % src_instance_id)
                    ret_disk_snapshot, msg = _vm_create_disk_snapshot(images,uuid,user_id,
                                                                                        request_id,source_host,src_instance_id)
                    if ret_disk_snapshot == ActionStatus.FAILD:
                        # 將源host狀態解鎖
                        release_host_clone_status(source_host)
                        logging.error(msg)
                        vm_create_status = VMStatus.CLONE_ERROR
                        _update_instance_status(uuid, vm_create_status)
                        where_data = {
                            'id': int(src_instance_id)
                        }
                        update_data = {
                            'status': power_status
                        }
                        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
                        if vishnu_id != " ":
                            job_status = VsJobStatus.FAILED
                            msg_back(task_id, job_status, src_instance_id, instance_id)
                        return 0

                # 拷贝虚拟机磁盘文件
                logging.info("start to cp images files for clone vm %s" % instance_id)
                src_instance_data = ins_s.InstanceService().get_instance_info(src_instance_id)
                res_cp_disk,message = _copy_vm_disks(request_id, source_host, host_ip, src_instance_data['uuid'],
                                                     uuid, user_id,src_instance_id,images)

                # 如果源vm为运行中则在拷贝完成后删除源vm快照文件
                if power_status == "3":
                    disk_tag_list = []
                    for disk_data in snapshot_disk_data:
                        disk_tag_list.append(disk_data[0])
                    logging.info("start to commit disk snapshot for  vm %s" % src_instance_id)
                    ret_snapshot_commit, msg = _vm_disk_snapshot_commit(task_id, uuid, user_id, request_id, source_host,
                                                                        src_instance_id, disk_tag_list)
                    if ret_snapshot_commit == ActionStatus.FAILD:
                        # 將源host狀態解鎖
                        release_host_clone_status(source_host)
                        logging.error(msg)
                        vm_create_status = VMStatus.CLONE_ERROR
                        _update_instance_status(uuid, vm_create_status)
                        where_data = {
                            'id': int(src_instance_id)
                        }
                        update_data = {
                            'status': power_status
                        }
                        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
                        if vishnu_id != " ":
                            job_status = VsJobStatus.FAILED
                            msg_back(task_id, job_status, src_instance_id, instance_id)
                        return 0
                if res_cp_disk == ActionStatus.FAILD:
                    # 將源host狀態解鎖
                    release_host_clone_status(source_host)
                    logging.error(message)
                    vm_create_status = VMStatus.CLONE_ERROR
                    _update_instance_status(uuid, vm_create_status)
                    where_data = {
                        'id': int(src_instance_id)
                    }
                    update_data = {
                        'status': power_status
                    }
                    ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
                    if vishnu_id != " ":
                        job_status = VsJobStatus.FAILED
                        msg_back(task_id, job_status, src_instance_id, instance_id)
                    return 0



                # 虚拟机磁盘文件重命名
                logging.info("start to rename images name for clone vm %s" % instance_id)
                ret_rename_image,res_msg = rename_vm_disk(images,host_ip,request_id,uuid,user_id,instance_id)
                if ret_rename_image ==  ActionStatus.FAILD:
                    # 將源host狀態解鎖
                    release_host_clone_status(source_host)
                    logging.error(res_msg)
                    vm_create_status = VMStatus.CLONE_ERROR
                    _update_instance_status(uuid, vm_create_status)
                    where_data = {
                        'id': int(src_instance_id)
                    }
                    update_data = {
                        'status': power_status
                    }
                    ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
                    if vishnu_id != " ":
                        job_status = VsJobStatus.FAILED
                        msg_back(task_id, job_status, src_instance_id, instance_id)
                    return 0

                # 创建虚拟机
                volumes_d = {}
                disk_dir = default.INSTANCE_DISK_PATH % (uuid, hostname + ".img")
                volumes_d[disk_dir] = "qcow2"
                networks_name = networks.get('net_card_name')
                mac = networks.get('mac')
                image_count = 0
                for image in images:
                    if image_count >= 1:
                        dir = default.INSTANCE_DISK_PATH % (uuid, hostname + ".disk" + str(image_count))
                        volumes_d[dir] = "qcow2"
                    image_count = image_count + 1
                create_instance_xml_ret, create_instance_xml_msg = create_instance_first(request_id, host_ip, uuid, user_id,
                                                                                         hostname, memory_mb, vcpu, volumes_d,
                                                                                         networks_name, mac)
                if create_instance_xml_ret is ActionStatus.FAILD:
                    # 將源host狀態解鎖
                    release_host_clone_status(source_host)
                    logging.error("instance %s create xml failed because %s" % (uuid, create_instance_xml_msg))
                    vm_create_status = VMStatus.CLONE_ERROR
                    _update_instance_status(uuid, vm_create_status)
                    where_data = {
                        'id': int(src_instance_id)
                    }
                    update_data = {
                        'status': power_status
                    }
                    ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
                    if vishnu_id != " ":
                        job_status = VsJobStatus.FAILED
                        msg_back(task_id, job_status, src_instance_id, instance_id)
                    return 0

                # 将源vm状态改为源状态
                where_data = {
                    'id': int(src_instance_id)
                }
                update_data = {
                    'status': power_status
                }
                ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)

                # 将新建vm状态改为关机
                where_data = {
                    'id': int(instance_id)
                }
                update_data = {
                    'status': '1'
                }
                ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)

                # 删除clone下残余文件
                rm_temp_disk(host_ip, images)
                # 將源host狀態解鎖
                release_host_clone_status(source_host)

                if vishnu_id != " ":
                    job_status = VsJobStatus.SUCCEED
                    msg_back(task_id, job_status, src_instance_id, instance_id)

            except:
                err = traceback.format_exc()
                # 将源vm状态改为源状态
                where_data = {
                    'id': int(src_instance_id)
                }
                update_data = {
                    'status': power_status
                }
                ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
                logging.info(traceback.format_exc())
                vm_create_status = VMStatus.CLONE_ERROR
                _update_instance_status(uuid, vm_create_status)
                # 將源host狀態解鎖
                release_host_clone_status(source_host)
                # 维石任务则回调维石接口并更新trace_request
                if vishnu_id != " ":
                    job_status = ActionStatus.FAILD
                    msg_back(task_id, job_status, src_instance_id, instance_id)
                return 0
    else:
        _update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CHECK_HOST_STATUS,
                                 ActionStatus.FAILD, "host keep locked all time")
        # 將源host狀態解鎖
        release_host_clone_status(source_host)
        # 将源vm状态改为源状态
        where_data = {
            'id': int(src_instance_id)
        }
        update_data = {
            'status': power_status
        }
        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
        logging.info(traceback.format_exc())
        vm_create_status = VMStatus.CREATE_ERROR
        _update_instance_status(uuid, vm_create_status)
        # 维石任务则回调维石接口并更新trace_request
        if vishnu_id != " ":
            job_status = ActionStatus.FAILD
            msg_back(task_id, job_status, src_instance_id, instance_id)
        return 0


# 创建虚拟机目录
def _check_image_dir_and_create(request_id, host_ip, uuid, user_id):
    ret_check_status, job_status = _check_job_step_done(request_id, InstaceActions.INSTANCE_CLONE_CREATE_DIR)
    if ret_check_status and job_status is 1:
        message = "pass"
        # logging.info(message)
        return ActionStatus.SUCCSESS, message
    else:
        _add_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CREATE_DIR, 'start')
        instance_directory_create_status = ActionStatus.SUCCSESS
        _message = "instance dir %s create successful" % uuid
        is_dir_existed = ansibleCmdV2.ansible_remote_check_instance_dir(host_ip, uuid)
        if not is_dir_existed:
            print "instance dir %s is not existed" % uuid
            logging.info("instance %s is not existed" % uuid)
            instance_dir_create_success = False
            i = 0
            while i < 3 and not instance_dir_create_success:
                time.sleep(3)
                instance_directory_create_ret = ansibleCmdV2.ansible_remote_mkdir_instance_dir(host_ip, uuid)
                if not instance_directory_create_ret:
                    instance_directory_create_status = ActionStatus.FAILD
                    _message = "instance dir %s create failed because directory has been exist" % uuid
                    logging.info(_message)
                    i += 1
                elif instance_directory_create_ret is 1:
                    instance_directory_create_status = ActionStatus.FAILD
                    _message = "instance dir %s create failed because ansible not available" % uuid
                    logging.info(_message)
                    i += 1
                else:
                    instance_dir_create_success = True
        elif is_dir_existed is 1:
            _message = "instance dir %s check error because ansible not available" % uuid
            instance_directory_create_status = ActionStatus.FAILD
            logging.info(_message)

        _update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CREATE_DIR,
                                 instance_directory_create_status, _message)

        return instance_directory_create_status,_message

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

def _update_instance_status(uuid, vm_status):
    update_data = {
        'status': vm_status,
        'updated_at': get_datetime_str()
    }
    where_data = {
        'uuid': uuid
    }
    return ins_s.InstanceService().update_instance_info(update_data, where_data)

# 检测虚拟机创建指定步骤是否已经完成
def _check_job_step_done(_request_id, _action_name):
    return ins_a_s.get_instance_action_service_status(_request_id, _action_name)

# 创建存储池
def _create_storage_pool(request_id, host_ip, uuid, user_id):
    ret_check_status, job_status = _check_job_step_done(request_id, InstaceActions.INSTANCE_CLONE_CREATE_STORAGE_POOL)
    if ret_check_status and job_status is 1:
        message = "pass"
        # logging.info(message)
        return ActionStatus.SUCCSESS, message
    else:
        _add_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CREATE_STORAGE_POOL, 'start')
        connect_storages = vmManager.libvirt_get_connect(host_ip, conn_type='storages')
        pool_status, pool_name = vmManager.libvirt_create_storage_pool(connect_storages, uuid)
        if pool_status:
            status = ActionStatus.SUCCSESS
            message = "create storage pool %s  success!" % uuid
        else:
            status = ActionStatus.FAILD
            message = "create storage pool %s  failed!" % uuid
        _update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CREATE_STORAGE_POOL, status, message)
        return status,message


# 拷贝虚拟机磁盘文件
def _copy_vm_disks(request_id,source_host,dest_host,src_uuid,uuid,user_id,src_instance_id,images):
    ret_check_status, job_status = _check_job_step_done(request_id, InstaceActions.INSTANCE_CLONE_TRANS_IMAGE)
    if ret_check_status and job_status is 1:
        message = "pass"
        # logging.info(message)
        return ActionStatus.SUCCSESS, message
    else:
        _add_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_TRANS_IMAGE, 'start')

        source_dir = '/app/image/' + src_uuid
        res_cp_disk,msg = _copy_disk(source_dir,images,request_id,source_host,dest_host)
        message = msg
        if not res_cp_disk:
            status = ActionStatus.FAILD
        else:
            status = ActionStatus.SUCCSESS
        _update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_TRANS_IMAGE,
                                     status, message)
        return status,message


# 获取源vm的磁盘文件list
def _get_source_vm_disks(src_instance_id,source_host):
    src_image_list = []
    src_instance_data = ins_s.InstanceService().get_instance_info(src_instance_id)
    src_instance_name = src_instance_data['name']
    get_device_status, vm_disks_info = vmManager.libvirt_get_instance_device(source_host, src_instance_name)
    if get_device_status == -100:
        _status = ActionStatus.FAILD
        msg = 'get source vm disk list fail'
        return _status,msg
    else:
        for disk in vm_disks_info:
            if disk['image'] is None:
                continue
            src_image_list.append(disk['image'])
        if src_image_list == []:
            msg = 'source vm disk list is empty'
            _status = ActionStatus.FAILD
            return _status,msg
        else:
            _status = ActionStatus.SUCCSESS
            return _status,src_image_list


# NC传输磁盘文件
def _copy_disk(source_dir,src_image_list,request_id,src_host,dest_host):
    g_flag, g_speed = _confirm_image_get_speed(dest_host)
    if not g_flag:
        msg = "获取迁移用网速失败"
        return ActionStatus.FAILD,msg
    else:
        ret_s = ansibleCmdV2.ansible_migrate_qos_speed(src_host, dest_host, g_speed)
        if not ret_s:
            msg = "配置迁移限速失败"
            return ActionStatus.FAILD,msg
        else:
            # 迁移端口
            nc_transfer_port = v2v_ncport(dest_host)
            threads = []
            host_ip_d = dest_host

            # 获取源物理机上虚拟机卷名称，用于下面一步的数据拷贝
            logging.info('开始拷贝vm磁盘文件到目标主机')
            for _ins_vol in src_image_list:
                ins_vol_server_get_d = 'cd /app/clone;rm -rf %s;nc -l -4 ' % _ins_vol + str(nc_transfer_port) + ' > ' + _ins_vol
                ins_vol_server_send_s = 'cd ' + source_dir + ';nc -4 ' + dest_host + ' ' + str(
                    nc_transfer_port) + ' < ' + _ins_vol
                # 多线程启动nc拷贝镜像文件
                t_vol_host_d = threading.Thread(target=ansible_clone_file_get, args=(host_ip_d, ins_vol_server_get_d))
                threads.append(t_vol_host_d)
                t_vol_host_d.start()

                time.sleep(5)

                t_vol_host_s = threading.Thread(target=ansible_clone_file_get, args=(src_host, ins_vol_server_send_s))
                threads.append(t_vol_host_s)
                t_vol_host_s.start()

                # 判断多线程是否结束
                for t in threads:
                    t.join()
            speed_cal = ansibleCmdV2.ansible_migrate_cancel_qos_speed(src_host)
            if not speed_cal:
                msg = "取消限速失败"
                return False,msg
            else:
                # 拷贝后比对文件MD5
                dest_dir = '/app/clone'
                dst_check_disk = dest_dir + '/' + src_image_list[-1]
                src_check_disk = source_dir + '/' + src_image_list[-1]
                src_flag = False
                src_count = 0
                while not src_flag and src_count < 3:
                    ret_src, src_check_data = ansibleCmdV2.get_file_md5(src_host, src_check_disk)
                    if not ret_src:
                        logging.error(src_check_data)
                        src_count += 1
                    else:
                        src_flag = True
                if not src_flag:
                    return False, '获取源vm磁盘文件 %s MD5值失败' % src_check_disk
                src_check_disk_md5 = src_check_data
                dst_flag = False
                dst_count = 0
                while not dst_flag and dst_count < 3:
                    ret_dst, dst_check_data = ansibleCmdV2.get_file_md5(dest_host, dst_check_disk)
                    if not ret_dst:
                        logging.error(dst_check_data)
                        dst_count += 1
                    else:
                        dst_flag = True
                if not dst_flag:
                    return False, '获取克隆后磁盘文件 %s MD5值失败' % dst_check_disk
                dst_check_disk_md5 = dst_check_data
                if src_check_disk_md5 != dst_check_disk_md5:
                    err_msg = '源vm磁盘文件%s和克隆后磁盘文件%s MD5值不一致' %(src_check_disk, dst_check_disk)
                    logging.error(err_msg)
                    return False, err_msg
                else:
                    msg = '源vm磁盘文件%s和克隆后磁盘文件%s MD5值一致' %(src_check_disk, dst_check_disk)
                    logging.info(msg)
                    return True, msg

                # # 获取源host下目标文件夹的disk清单
                # check_disk = src_image_list[-1]
                # flag_src = False
                # i_src = 0
                # while i_src < 3 and not flag_src:
                #     time.sleep(5)
                #     ret, src_image_md5_list = get_md5_list(src_host, src_image_list, source_dir)
                #     if not ret:
                #         i_src += 1
                #     else:
                #         flag_src = True
                # if not flag_src:
                #     msg = 'get source image md5 list failed'
                #     logging.info(msg)
                #     return False, msg
                # flag_dest = False
                # i_dest = 0
                # while i_dest < 3 and not flag_dest:
                #     time.sleep(5)
                #     ret1, dest_image_md5_list = get_md5_list(dest_host, src_image_list, dest_dir)
                #     if not ret1:
                #         i_dest += 1
                #     else:
                #         flag_dest = True
                # if not flag_dest:
                #     msg = 'get dest image md5 list failed'
                #     logging.info(msg)
                #     return False, msg
                # src_info = 'src image list for vm %s' % src_image_list[0]
                # logging.info(src_info)
                # logging.info(src_image_md5_list)
                # dest_info = 'dest image list for vm %s' % src_image_list[0]
                # logging.info(dest_info)
                # logging.info(dest_image_md5_list)
                # src_image_md5_list.sort()
                # dest_image_md5_list.sort()
                # if src_image_md5_list == dest_image_md5_list:
                #     logging.info('copy img disk from source host to destination host successful')
                #     msg = 'vm拷贝vm磁盘文件成功'
                #     return True,msg
                # else:
                #     msg = '拷贝镜像文件后比对源和目标MD5失败'
                #     return False, msg


# 源vm创建磁盘快照
def _vm_create_disk_snapshot(images,uuid,user_id,request_id,source_host,src_instance_id):
    ret_check_status, job_status = _check_job_step_done(request_id, InstaceActions.INSTANCE_CLONE_DISK_SNAPSHOT)
    if ret_check_status and job_status is 1:
        message = "pass"
        # logging.info(message)
        return ActionStatus.SUCCSESS, message
    else:
        _add_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_DISK_SNAPSHOT, 'start')
        src_instance_data = ins_s.InstanceService().get_instance_info(src_instance_id)
        src_instance_name = src_instance_data['name']
        src_instance_uuid = src_instance_data['uuid']
        connect_instance = vmManager.libvirt_get_connect(source_host, conn_type='instance', vmname=src_instance_name)
        if not connect_instance:
            _status = ActionStatus.FAILD
            msg = "源vm%s创建磁盘快照失败,libvirt连接失败" % src_instance_name
        else:
            #ret_disk_snapshot = ansibleCmd.create_disk_exter_snapshot(source_host,src_instance_name,snapshot_disk_data)
            snapshot_disk_data = []
            for image in images:
                image_url = '/app/image/' + src_instance_uuid + '/' + image
                snapshot_disk_data.append(image_url)
            ret_disk_snapshot = vmManager.ex_disk_snapshot(source_host, src_instance_name, snapshot_disk_data)
            if not ret_disk_snapshot:
                _status = ActionStatus.FAILD
                msg = "源vm %s 创建磁盘快照失败" % src_instance_name
            else:
                _status = ActionStatus.SUCCSESS
                msg = "源vm %s 创建磁盘快照成功" % src_instance_name

        _update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_DISK_SNAPSHOT,
                                 _status, msg)
        return _status, msg


# 源vm整合磁盘快照
def _vm_disk_snapshot_commit(task_id, uuid,user_id,request_id,source_host,src_instance_id,disk_tag_list):
    ret_check_status, job_status = _check_job_step_done(request_id, InstaceActions.INSTANCE_CLONE_DISK_SNAPSHOT_COMMIT)
    if ret_check_status and job_status is 1:
        message = "pass"
        # logging.info(message)
        return ActionStatus.SUCCSESS, message
    else:
        _add_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_DISK_SNAPSHOT_COMMIT, 'start')
        src_instance_data = ins_s.InstanceService().get_instance_info(src_instance_id)
        src_instance_name = src_instance_data['name']
        src_instance_uuid = src_instance_data['uuid']
        _status = ActionStatus.SUCCSESS
        msg = "虚拟机 %s 整合磁盘快照成功" % src_instance_name
        # 整合快照文件
        # for disk_tag in disk_tag_list:
        #     flag = False
        #     i = 0
        #     while i < 3 and not flag:
        #         time.sleep(5)
        #         ret_snapshot_commit = ansibleCmd.disk_snapshot_commit(source_host,src_instance_name,disk_tag)
        #         if not ret_snapshot_commit:
        #             i += 1
        #             err_msg = 'vm %s commit snapshot file for %s fail' % (src_instance_name, disk_tag)
        #             logging.info(err_msg)
        #         else:
        #             flag = True
        #     if not flag:
        #         _status = ActionStatus.FAILD
        #         msg = '虚拟机 %s 磁盘快照 %s 文件整合失败' %(src_instance_name, disk_tag)
        #         break
        ret_commit, commmit_msg = vm_snapshot_commit(task_id, source_host, src_instance_name, disk_tag_list, src_instance_uuid)
        if not ret_commit:
            _status = ActionStatus.FAILD
            msg = commmit_msg
        # if _status == ActionStatus.SUCCSESS:
        #     # 删除快照残余文件
        #     src_instance_uuid = src_instance_data['uuid']
        #     dest_dir = '/app/image/' + src_instance_uuid
        #     ret = rm_snapfile(source_host, dest_dir)
        #     if not ret:
        #         _status = False
        #         msg = "清除虚拟机%s快照残余文件失败" % src_instance_name
        _update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_DISK_SNAPSHOT_COMMIT,
                                 _status, msg)
        return _status, msg


def _confirm_image_get_speed(host_ip):
    '''
        确定镜像拷贝速度
    :param speed_limit:
    :param host_s:
    :return:
    '''
    # 目标主机的性能数据
    host_used_d = host_s_s.get_host_used_by_hostip(host_ip)
    if not host_used_d:
        return True, "20M"
    # 获取镜像前限速，根据网络使用率调整迁移速率为（网络带宽-当前使用上传带宽）* 0.8
    # 总带宽 - 已使用带宽 = 剩余带宽，然后只使用80%，这相当最大理论值
    if 'net_size' not in host_used_d:
        return False, ""
    if 'current_net_rx_used' not in host_used_d:
        return False, ""

    if float(host_used_d["current_net_rx_used"]) < 1:
        current_net_rx_used = 0
    else:
        current_net_rx_used = int(host_used_d["current_net_rx_used"])
    net_speed = (int(host_used_d["net_size"]) - (current_net_rx_used / 100) * int(host_used_d["net_size"])) \
                * 0.8
    # 迁移速度最小确保20MByte = 160 Mbit
    image_get_speed = net_speed if net_speed > 160 else 160

    return True, str(image_get_speed)

def ansible_clone_file_get(host,command):
    hostlist = []
    hostlist.append(host)
    ansible_code, ansible_msg = ansibleCmdV2.ansible_run_shell(host,command)
    if ansible_code == 3:
        message = '连接目标KVM HOST %s 失败' % (host)
        logging.error(message)
        return False, message
    elif ansible_code != 0:
        logging.info('在host %s 上下发NC传输失败' % (host))
        return False
    elif 'failed' in ansible_msg['np_fact_cache'][host]:
        logging.info('在host %s 上下发NC传输失败' % (host))
        return False
    else:
        logging.info('host %s 上下发NC传输成功' % (host))
        return True

@fileLock.file_lock('clone_port_lock')
def v2v_ncport(dest_host):
     i=1
     while i< 1000:
         randport = random.randint(10001,10999)
         randport = str(randport)
         rand_res,msg = ansibleCmdV2.check_port_is_up(dest_host,randport)
         if rand_res == False:
             return randport
         else:
             i += 1

# 虚拟机磁盘文件重命名
def rename_vm_disk(src_image_list,host_ip,request_id,uuid,user_id,instance_id):
    instance_data = ins_s.InstanceService().get_instance_info(instance_id)
    instance_name = instance_data['name']
    ret_check_status, job_status = _check_job_step_done(request_id, InstaceActions.INSTANCE_CLONE_RENAME_IMAGES)
    if ret_check_status and job_status is 1:
        message = "pass"
        # logging.info(message)
        return ActionStatus.SUCCSESS, message
    else:
        _add_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_RENAME_IMAGES, 'start')
        for image in src_image_list:
            image_tag = image.split('.',1)
            new_im_name = instance_name + '.' + image_tag[1]
            dest_dir = '/app/image/' + uuid
            res_rename,message = ansibleCmdV2.rename_clone_image(host_ip,image,new_im_name,dest_dir)
            if not res_rename:
                status =  ActionStatus.FAILD
                message = '重命名 %s 磁盘文件时失败' % image
                _update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_RENAME_IMAGES,
                                 status, message)
                return status, message
        status = ActionStatus.SUCCSESS
        message = '重命名磁盘文件成功'
        _update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_RENAME_IMAGES,
                                 status, message)
        return status,message


# 创建虚拟机
def create_instance_first(request_id, host_ip, uuid, user_id, hostname, memory_mb, vcpu,
                          volumes_d, net_card_name, mac):
    ret_check_status, job_status = _check_job_step_done(request_id, InstaceActions.INSTANCE_CREATE)
    if ret_check_status and job_status is 1:
        status = ActionStatus.SUCCSESS
        message = "create instance  %s %s success! cpu:%s mem:%s " % (hostname, uuid, vcpu, memory_mb)
        return status, message
    else:
        if not ret_check_status:
            _add_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CREATE, 'start')
        connect_create = vmManager.libvirt_get_connect(host_ip)
        if not connect_create:
            status = ActionStatus.FAILD
            message = 'can not connect to libvirt'
            _update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CREATE, status, message)
            return status, message
        # 需要刷新存储池，否则libvirt创建虚拟机会找不到新建的虚拟机磁盘报错
        connect_create.refresh_storage_pool_by_name(uuid)
        create_status, instance_hostname = vmManager.libvirt_create_instance_xml_no_nic(connect_create, hostname, memory_mb, vcpu,
                                                                                 uuid, volumes_d,
                                                                                 net_card_name, mac)
        if create_status:
            status = ActionStatus.SUCCSESS,
            message = "create instance  %s %s success! cpu:%s mem:%s " % (hostname, uuid, vcpu, memory_mb)

        else:
            status = ActionStatus.FAILD,
            message = "create instance %s %s Failed!cpu:%s mem:%s" % (hostname, uuid, vcpu, memory_mb)
        _update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CREATE, status, message)
        return status, message


# 删除clone下残留文件
def rm_temp_disk(host_ip,src_image_list):
    for image in src_image_list:
        image_dest = '/app/clone/'+ image
        ansibleCmdV2.ansible_rm_file(host_ip,image_dest)



# 回调维石接口
def msg_to_vishnu(job_status,src_instance_id,instance_id):
    msg =  {
                "status":job_status,
                "instance_id":str(instance_id),
                "parent_id":str(src_instance_id)
            }
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
        logging.info( "requests to /vishnu-web/restservices/MiniArch data:{},status_code:{}".format(data, r.status_code))
        if not r.status_code:
            return str(ErrorCode.SYS_ERR)
        return str(r.status_code)
    except Exception as err:
        logging.error('post to vs error because:%s' % err)
        return str(ErrorCode.SYS_ERR)


# 回调维石接口并更新trace_request
def msg_back(task_id,job_status,src_instance_id,instance_id):
    ret_request_re = request_r_s.RequestRecordService().get_request_record_info_by_taskid_kvm(task_id)
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


# 更新host的克隆状态为使用中
def update_host_clone_status(host_ip):
    _where_data_h = {
        'ipaddress': host_ip,
        'isdeleted': '0'
    }
    _update_data_h = {
        'host_clone_status': '1'
    }
    ret_h = ho_s.HostService().update_host_info(_update_data_h, _where_data_h)
    if ret_h != 1:
        ho_s.HostService().update_host_info(_update_data_h, _where_data_h)


# 更新host的克隆狀態為已完成
def release_host_clone_status(host_ip):
    _where_data_h = {
        'ipaddress': host_ip,
        'isdeleted': '0'
    }
    _update_data_h = {
        'host_clone_status': '0'
    }
    ret_h = ho_s.HostService().update_host_info(_update_data_h, _where_data_h)
    if ret_h != 1:
        ho_s.HostService().update_host_info(_update_data_h, _where_data_h)


# # 判断目标文件夹下文件是否齐全
# def check_dest_file(image_list, host_ip, dest_dir):
#     check_tag = 0
#     for image in image_list:
#         file_dir = dest_dir + '/' + image
#         ret, msg = ansibleCmd.check_file_exists(host_ip, file_dir)
#         if not ret:
#             check_tag += 1
#     if check_tag > 0:
#         return False
#     else:
#         return True


# 获取文件夹下所有镜像的MD5 list
def get_md5_list(host_ip, image_list, dest_dir):
    tag = True
    md5_list = []
    for image_disk in image_list:
        dest_file = dest_dir + '/' + image_disk
        ret, data = ansibleCmdV2.get_file_md5(host_ip, dest_file)
        if ret:
            md5_list.append(data)
        else:
            logging.info(ret)
            tag = False
            break
        time.sleep(3)
    if not tag:
        return False, md5_list
    else:
        return True, md5_list


# 虚拟机磁盘快照整合功能
def vm_snapshot_commit(task_id, source_host, source_vm_name, disk_tag_list, src_instance_uuid):
    # 创建快照整合脚本文件
    generate_snapshot_commit_shell(task_id, source_vm_name, disk_tag_list, src_instance_uuid)
    # 下发脚本文件到host
    ret_copy_commit_shell, copy_commit_shell_msg = ansibleCmdV2.cp_snapshot_commit_shell(source_host, task_id)
    if not ret_copy_commit_shell:
        return False, copy_commit_shell_msg
    # 执行脚本整合磁盘快照
    ret_exec_commit_shell, exec_commit_shell_msg = ansibleCmdV2.exec_commit_shell(source_host, task_id)
    if not ret_exec_commit_shell:
        return False, copy_commit_shell_msg
    message = '%s快照文件整合成功' % source_vm_name
    return True, message


# 生成磁盘文件整合脚本
def generate_snapshot_commit_shell(task_id, source_vm_name, disk_tag_list, src_instance_uuid):
    snapshot_commit_file = 'snapshot_commit_' + str(task_id) + '.sh'
    snapshot_commit_dir = default.DIR_DEFAULT + '/deploy/wgetdir/' + snapshot_commit_file
    with open(snapshot_commit_dir, 'w') as f:
        command1 = '''
#/bin/bash
commit_func()
{

        '''
        f.write(command1)
        for disk_tag in disk_tag_list:
            commit_command = '   virsh blockcommit %s %s --active  --verbose --wait --keep-relative --pivot' % (source_vm_name, disk_tag)
            f.write(commit_command)
            f.write('\n')
        f.write('}\n')
        dst_dir = '/app/image/%s' % src_instance_uuid
        command2 = '''
commit_func
if [ $? -eq 0 ]; then
    echo "commit snapshot success now rm snapshot files"
    cd %s;rm -rf *.snapshot
    exit 0
else
    echo "commit snapshot failed!"
    exit 1
fi

        ''' % dst_dir
        f.write(command2)




