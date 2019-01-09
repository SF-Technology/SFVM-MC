# !/usr/bin/env python2.7
# -*- coding:utf-8 -*-
#

#   Date    :   2017/8/9
#   Desc    :  克隆创建虚拟机的实际函数
from lib.shell import ansibleCmdV2


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

from lib.vrtManager import instanceManager as vmManager
from libvirt import libvirtError
from service.s_instance import instance_service as ins_s
from service.s_instance_action import instance_action as ins_a_s
from service.s_instance.instance_action_service import _instance_net_down,_instance_net_on,_instance_xml_dump
from model.const_define import InstaceActions, ActionStatus, DataCenterTypeTransform, VMStatus, \
    DataCenterType, InstanceCloneCreateTransType
from config import default
from config.default import DIR_INSTANCE_XML_BACKUP

from helper import json_helper
from service.s_instance import instance_ip_service as ins_ip_s
from service.s_host import host_service as host_s, host_schedule_service as host_s_s
from helper.encrypt_helper import decrypt
from helper.time_helper import get_datetime_str
import logging
import time
import traceback




def clone_create(msg_data):
    logging.info("--" * 25)
    logging.info(msg_data)
    msg = json_helper.read(msg_data)
    data = msg.get('data')
    request_id = data.get('request_id')
    task_id = data.get('task_id')
    host_ip = data.get('host_ip')
    uuid = data.get('uuid')
    memory_mb = data.get('memory_mb')
    hostname = data.get('hostname')
    vcpu = data.get('vcpu')
    images = data.get('disks')
    image_name = data.get('image_name')
    networks = data.get('networks')[0]
    user_id = data.get('user_id')
    instance_id = data.get('instance_id')
    net_area_id = data.get('net_area_id')
    clone_image_num = data.get('clone_image_num')
    total_size = data.get('total_size')
    trans_type = data.get('trans_type')
    http_port = data.get('http_port')
    md5_check = data.get('md5_check')
    pool_status = False
    source_vm = data.get('source_vm')
    source_ip = data.get('source_ip')
    ostype = data.get('ostype')
    if host_ip is None or request_id is None or not net_area_id or not instance_id or not task_id or not uuid or not memory_mb \
            or not hostname or not vcpu or not images or not image_name or not networks or not user_id or not source_vm or not source_ip:
        logging.error("empty input of host_ip or net_area_id or request_id")
        vm_create_status = VMStatus.CLONE_CREATE_ERROR
        _update_instance_status(uuid, vm_create_status)
        return 0
    try:
        # 获取前端用户输入root密码用于注入修改
        ins_info = ins_s.InstanceService().get_instance_info_by_uuid(uuid)
        if ins_info:
            if ins_info['password']:
                user_passwd = decrypt(ins_info['password'])
            else:
                user_passwd = None
        else:
            user_passwd = None

        if trans_type == InstanceCloneCreateTransType.BT:
            # BT传输获取镜像
            logging.info("start BT trans to get images %s by transmission" % hostname)
            ret_bt_trans, bt_trans_msg = bt_trans_check(host_ip,task_id,source_ip,uuid,request_id,user_id,source_vm,
                                                       clone_image_num, total_size)
            if ret_bt_trans != 1:
                logging.error(bt_trans_msg)
                vm_create_status = VMStatus.CLONE_CREATE_ERROR
                _update_instance_status(uuid, vm_create_status)
                return 0

        else:
            # WGET传输获取镜像
            logging.info("start WGET trans to get images %s by transmission" % hostname)
            ret_wget_trans, wget_trans_msg = wget_image_list(task_id, user_id, uuid, request_id, host_ip, images, http_port, total_size, source_ip, md5_check)
            if ret_wget_trans != 1:
                logging.error(wget_trans_msg)
                vm_create_status = VMStatus.CLONE_CREATE_ERROR
                _update_instance_status(uuid, vm_create_status)
                return 0

        # 修改bt文件权限为644
        logging.info("start to chmod image files  %s " % hostname)
        ret_bt_trans, bt_trans_msg = change_image_mod(task_id, user_id, uuid, request_id, host_ip, images)
        if ret_bt_trans != 1:
            logging.error(bt_trans_msg)
            vm_create_status = VMStatus.CLONE_CREATE_ERROR
            _update_instance_status(uuid, vm_create_status)
            return 0

        # 创建存储池
        logging.info("start create pool %s " % uuid)
        create_stg_pool_ret, create_stg_pool_msg = create_storage_pool(request_id, host_ip, uuid, user_id, task_id)
        if create_stg_pool_ret is ActionStatus.FAILD:
            logging.error("create storage pool %s failed because %s" % (uuid, create_stg_pool_msg))
            vm_create_status = VMStatus.CLONE_CREATE_ERROR
            _update_instance_status(uuid, vm_create_status)
            return 0

        volumes_d = {}
        # 开始克隆镜像
        logging.info("start clone image %s " % images)
        clone_image_ret, clone_image_msg = create_clone_image(request_id, host_ip, uuid, user_id, task_id,instance_id,source_vm,clone_image_num)
        if clone_image_ret is ActionStatus.FAILD:
            logging.error("instance %s clone image failed because %s" % (uuid, clone_image_msg))
            vm_create_status = VMStatus.CLONE_CREATE_ERROR
            _update_instance_status(uuid, vm_create_status)
            return 0

        disk_dir = default.INSTANCE_DISK_PATH % (uuid, hostname + ".img")
        volumes_d[disk_dir] = "qcow2"

        # 创建虚拟机xml文件
        networks_name = networks.get('net_card_name')
        mac = networks.get('mac')
        image_count = 0
        for image in images:
            if image_count >= 1:
                dir = default.INSTANCE_DISK_PATH % (uuid, hostname+".disk"+str(image_count))
                volumes_d[dir] = "qcow2"
            image_count = image_count + 1
        create_instance_xml_ret, create_instance_xml_msg = create_instance_first(request_id, host_ip, uuid, user_id,
                                                                                 hostname, memory_mb, vcpu, volumes_d,
                                                                                 networks_name, mac, task_id)

        if create_instance_xml_ret is ActionStatus.FAILD:
            logging.error("instance %s create xml failed because %s" % (uuid, create_instance_xml_msg))
            vm_create_status = VMStatus.CLONE_CREATE_ERROR
            _update_instance_status(uuid, vm_create_status)
            return 0

        # 完成以上操作后开启虚拟机
        if not vmManager.libvirt_instance_startup(host_ip, hostname):
            logging.error("instance %s power on failed" % uuid)
            vm_create_status = VMStatus.CLONE_CREATE_ERROR
            _update_instance_status(uuid, vm_create_status)
            return 0

        time.sleep(5)


        #vm克隆创建预配置
        ret_pre_conf,pre_conf_msg = vm_pre_conf(request_id, networks, host_ip, uuid, user_id, hostname, ostype, task_id)
        if ret_pre_conf is ActionStatus.FAILD:
            logging.error('instance %s clone create fail because pre configuraiton failed' %uuid)
            vm_create_status = VMStatus.CLONE_CREATE_ERROR
            _update_instance_status(uuid, vm_create_status)
            return 0


        # 虚拟机连通网络
        ret_vm_network_up, vm_network_up_msg = clonevm_net_up(task_id, user_id, uuid, request_id, host_ip,instance_id)
        if ret_vm_network_up is ActionStatus.FAILD:
            time.sleep(10)
            ret_vm_network_up, vm_network_up_msg = clonevm_net_up(task_id, user_id, uuid, request_id, host_ip,
                                                                  instance_id)
            if ret_vm_network_up is ActionStatus.FAILD:
                logging.error("instance %s clone create failed because %s" % (uuid, vm_network_up_msg))
                vm_create_status = VMStatus.CLONE_CREATE_ERROR
                _update_instance_status(uuid, vm_create_status)
                return 0
            else:
                pass

        time.sleep(10)

        # 虚拟机初始化注入
        inject_data(request_id, networks, host_ip, uuid, user_id, hostname, ostype, user_passwd, image_name, task_id)
        ret_check_inject_status, job_inject_status = _check_job_step_done(request_id, InstaceActions.INSTANCE_INJECT_DATA)
        if ret_check_inject_status and job_inject_status is 1:
            vm_create_status = VMStatus.STARTUP
            _update_instance_status(uuid, vm_create_status)
            return 0
        else:
            vm_create_status = VMStatus.CLONE_CREATE_ERROR
            _update_instance_status(uuid, vm_create_status)
            return 0

    except:
        # 源HOST关闭http
        ansibleCmdV2.clone_http_kill(source_ip, str(http_port))
        err = traceback.format_exc()
        logging.info(traceback.format_exc())
        vm_create_status = VMStatus.CLONE_CREATE_ERROR
        _update_instance_status(uuid, vm_create_status)
        return 0


#检查镜像和同步函数
def source_server_prep(host_ip,clone_dir,uuid,request_id,user_id,task_id):
    #判断该步骤是否完成
    ret_check_status, job_status = _check_job_step_done(request_id, InstaceActions.INSTANCE_CLONE_CREATE_GET_IMAGE)
    if ret_check_status and job_status is 1:
        message = "pass"
        # logging.info(message)
        return ActionStatus.SUCCSESS,message
    else:
        if not ret_check_status:
            add_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CREATE_GET_IMAGE, 'start')
        retry_Flag = False
        retry_counts = 0
        while not retry_Flag and retry_counts < 8:
            ret_copy_torr_file,copy_torr_msg = copy_torrent_file(host_ip,clone_dir,uuid)
            if not ret_copy_torr_file:
                retry_counts = retry_counts +1
                time.sleep(2)
            else:
                retry_Flag = True
        if not retry_Flag:
            status = ActionStatus.FAILD
            message = "创建虚拟机 %s 出错,拷贝克隆镜像文件到/app/imge下失败" % uuid
            update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CREATE_GET_IMAGE, status, message,
                                    task_id)
            return status, message
        #刷新存储池
        connect_create = vmManager.libvirt_get_connect(host_ip, conn_type='create')
        if connect_create:
            vmManager.libvirt_refresh_image_pool(connect_create)
            _message = '刷新存储池成功'
            status = ActionStatus.SUCCSESS
            update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CREATE_GET_IMAGE, status, _message,
                                    task_id)
            return status, _message
        else:
            status = ActionStatus.FAILD
            message = "创建虚拟机 %s 出错,刷新存储池成功失败"
            update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CREATE_GET_IMAGE, status,
                                    message,
                                    task_id)
            return status, message


def _update_instance_status(uuid, vm_status):
    update_data = {
        'status': vm_status,
        'updated_at': get_datetime_str()
    }
    where_data = {
        'uuid': uuid
    }
    return ins_s.InstanceService().update_instance_info(update_data, where_data)


# 创建存储池
def create_storage_pool(request_id, host_ip, uuid, user_id, task_id):
    ret_check_status, job_status = _check_job_step_done(request_id, InstaceActions.STORAGE_POOL_CREATE)
    if ret_check_status and job_status is 1:
        status = ActionStatus.SUCCSESS
        message = "创建存储池 %s 成功" % uuid
        return status, message
    else:
        if not ret_check_status:
            add_instance_actions(uuid, request_id, user_id, InstaceActions.STORAGE_POOL_CREATE, 'start')
        # 创建目标文件夹
        destdir_path = '/app/image/' + uuid
        Check_Flag = False
        retry_count = 0
        while not Check_Flag and retry_count <8:
            ret_create_dir, create_dir_msg = ansibleCmdV2.create_destdir(host_ip, destdir_path)
            if not ret_create_dir:
                retry_count = retry_count +1
                time.sleep(2)
            else:
                Check_Flag = True
        if not Check_Flag:
            status = ActionStatus.FAILD
            message = "创建虚拟机 %s 出错,创建目标文件夹失败" % uuid
            update_instance_actions(uuid, request_id, user_id, InstaceActions.STORAGE_POOL_CREATE, status,
                                    message,
                                    task_id)
            return status, message
        # 首先判断libvirt是否连接成功
        connect_storages = vmManager.libvirt_get_connect(host_ip, conn_type='storages')
        if not connect_storages:
            status = ActionStatus.FAILD
            message = "创建存储池 %s 失败,原因libvirt连接失败" % uuid
            update_instance_actions(uuid, request_id, user_id, InstaceActions.STORAGE_POOL_CREATE, status, message, task_id)
            return status, message
        pool_status, pool_name = vmManager.libvirt_create_storage_pool(connect_storages, uuid)
        if pool_status:
            status = ActionStatus.SUCCSESS
            message = "创建存储池 %s 成功" % uuid
        else:
            status = ActionStatus.FAILD
            message = "创建存储池 %s 失败" % uuid
        update_instance_actions(uuid, request_id, user_id, InstaceActions.STORAGE_POOL_CREATE, status, message, task_id)
        return status, message


# # 创建BT存储池
# def create_btfile_pool(request_id, host_ip, source_vm, user_id, task_id,uuid):
#     pool_name = source_vm + "_" + task_id
#     ret_check_status, job_status = _check_job_step_done(request_id, InstaceActions.INSTANCE_CLONE_CREATE_BTPOOL)
#     if ret_check_status and job_status is 1:
#         status = ActionStatus.SUCCSESS
#         message = "创建存储池 %s 成功" % pool_name
#         return status, message
#     else:
#         if not ret_check_status:
#             add_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CREATE_BTPOOL, 'start')
#         # 检查目标文件夹是否存在
#         destdir_path = '/app/clone/' + pool_name
#         ret_create_dir, create_dir_msg = ansibleCmd.create_destdir(host_ip, destdir_path)
#         if not ret_create_dir:
#             status = ActionStatus.FAILD
#             message = "克隆创建虚拟机 %s 出错,检查BT文件夹失败" % uuid
#             update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CREATE_BTPOOL, status,
#                                     message,
#                                     task_id)
#             return status, message
#         # 首先判断libvirt是否连接成功
#         connect_storages = vmManager.libvirt_get_connect(host_ip, conn_type='storages')
#         if not connect_storages:
#             status = ActionStatus.FAILD
#             message = "创建BT存储池 %s 失败,原因libvirt连接失败" % pool_name
#             update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CREATE_BTPOOL, status, message,
#                                     task_id)
#             return status, message
#
#         pool_status, pool_name = vmManager.libvirt_create_btstorage_pool(connect_storages, pool_name)
#         if pool_status:
#             status = ActionStatus.SUCCSESS
#             message = "创建BT存储池 %s 成功" % pool_name
#         else:
#             status = ActionStatus.FAILD
#             message = "创建BT存储池 %s 失败" % pool_name
#         update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CREATE_BTPOOL, status, message,
#                                 task_id)
#         return status, message
#
#
# # 删除BT存储池
# def del_btfile_pool(request_id, host_ip, source_vm, user_id, task_id,uuid):
#     pool_name = source_vm + "_" + task_id
#     ret_check_status, job_status = _check_job_step_done(request_id, InstaceActions.INSTANCE_CLONE_CREATE_DEL_BTPOOL)
#     if ret_check_status and job_status is 1:
#         status = ActionStatus.SUCCSESS
#         message = "删除BT存储池 %s 成功" % pool_name
#         return status, message
#     else:
#         if not ret_check_status:
#             add_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CREATE_DEL_BTPOOL, 'start')
#         # 首先判断libvirt是否连接成功
#         connect_storage = vmManager.libvirt_get_connect(host_ip, conn_type='storage',poolname=pool_name)
#         if not connect_storage:
#             status = ActionStatus.FAILD
#             message = "删除BT存储池 %s 失败,原因libvirt连接失败" % pool_name
#             update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CREATE_DEL_BTPOOL, status,
#                                     message,task_id)
#             return status, message
#         else:
#             connect_storage.delete()
#             status = ActionStatus.SUCCSESS
#             message = "创建BT存储池 %s 成功" % pool_name
#         update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CREATE_DEL_BTPOOL, status, message,
#                                 task_id)
#         return status, message


# 检测虚拟机创建指定步骤是否已经完成
def _check_job_step_done(_request_id, _action_name):
    return ins_a_s.get_instance_action_service_status(_request_id, _action_name)


def update_instance_actions(uuid, request_id, user_id, action, status, message, task_id):
    return ins_a_s.update_instance_actions_when_vm_create(request_id, action, status, message, task_id)


def add_instance_actions(uuid, request_id, user_id, action, message):
    data = {'action': action,
            'instance_uuid': uuid,
            'request_id': request_id,
            'user_id': user_id,
            'message': message
            }
    return ins_a_s.add_instance_actions(data)


# 克隆镜像
def create_clone_image(request_id, host_ip, uuid, user_id, task_id,instance_id,source_vm,clone_image_num):
    ret_check_status, job_status = _check_job_step_done(request_id, InstaceActions.INSTANCE_CLONE_CREATE_CP_IMAGE)
    if ret_check_status and job_status is 1:
        status = ActionStatus.SUCCSESS
        message = 'clone all images successful'
        return status, message
    else:
        if not ret_check_status:
            add_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CREATE_CP_IMAGE, 'start')
        # 拼装image数据对象
        instance_info = ins_s.InstanceService().get_instance_info(instance_id)
        instance_name = instance_info['name']
        instance_uuid = instance_info['uuid']
        dest_disk_dir = '/app/image/'+ uuid
        image_info = []
        sys_disk_tag = int(clone_image_num) -1
        sys_disk_data = {
            'image_path': '/app/clone/' + source_vm + '_' + task_id + '_' + str(sys_disk_tag),
            'dest_disk': instance_name + '.' +'img',
            'disk_dir_path': dest_disk_dir
        }
        image_info.append(sys_disk_data)
        for i in range(0,int(clone_image_num)-1):
            data_disk_data = {
                'image_path': '/app/clone/' + source_vm + '_' + task_id + '_' + str(i),
                'dest_disk': instance_name + '.' + 'disk' + str(i+1),
                'disk_dir_path': dest_disk_dir
            }
            image_info.append(data_disk_data)
        for image_info_data in image_info:
            disk_name = image_info_data['dest_disk']
            image_path = image_info_data['image_path']
            disk_dir_path = image_info_data['disk_dir_path']
            connect_create = vmManager.libvirt_get_connect(host_ip, conn_type='create')
            if not connect_create:
                status = ActionStatus.FAILD
                message = 'can not connect to libvirt'
                update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CREATE_CP_IMAGE, status, message, task_id)
                return status, message
            disk_status, disk_dir = vmManager.libvirt_clone_image(connect_create, disk_name, image_path, uuid,
                                                                  disk_dir_path)
            if not disk_status:
                status = ActionStatus.FAILD
                message = 'cp image files fail'
                update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CREATE_CP_IMAGE,
                                        status, message, task_id)
                return status, message
        connect_create = vmManager.libvirt_get_connect(host_ip, conn_type='create')
        if connect_create:
            connect_create.refresh_storage_pool_by_name(uuid)
            status = ActionStatus.SUCCSESS
            message = 'success'
        else:
            status = ActionStatus.FAILD
            message = '拷贝镜像后刷新存储池失败'
        update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CREATE_CP_IMAGE,
                                status, message, task_id)
        return status, message


# 拷贝镜像文件到/app/image下
def copy_torrent_file(host_ip,clone_dir,uuid):
    torr_dir = clone_dir
    ret_copy_disk,copy_dsk_msg = ansibleCmdV2.copy_torr_file(host_ip,torr_dir,uuid)
    return ret_copy_disk,copy_dsk_msg




# 创建虚拟机
def create_instance_first(request_id, host_ip, uuid, user_id, hostname, memory_mb, vcpu, volumes_d, net_card_name, mac, task_id):
    ret_check_status, job_status = _check_job_step_done(request_id, InstaceActions.INSTANCE_CREATE)
    if ret_check_status and job_status is 1:
        status = ActionStatus.SUCCSESS
        message = "create instance  %s %s success! cpu:%s mem:%s " % (hostname, uuid, vcpu, memory_mb)
        return status, message
    else:
        if not ret_check_status:
            add_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CREATE, 'start')
        connect_create = vmManager.libvirt_get_connect(host_ip)
        if not connect_create:
            status = ActionStatus.FAILD
            message = 'can not connect to libvirt'
            update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CREATE, status, message, task_id)
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

        update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CREATE, status, message, task_id)
        return status, message


# 创建虚拟机完成后注入数据
def inject_data(request_id, networks, host_ip, uuid, user_id, hostname, ostype, user_passwd, image_name, task_id):
    ret_check_status, job_status = _check_job_step_done(request_id, InstaceActions.INSTANCE_INJECT_DATA)
    if ret_check_status and job_status is 1:
        status = ActionStatus.SUCCSESS
        message = 'success'
        return status, message
    else:
        if not ret_check_status:
            add_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_INJECT_DATA, 'start')
        net_card_name = networks['net_card_name']
        ip = networks.get('ip')
        dns1 = networks.get('dns1')
        dns2 = networks.get('dns2')
        mask_int = networks.get('netmask', '255.255.255.0')
        gateway = networks.get('gateway')
        env_int = networks.get('env')
        if int(env_int) == DataCenterType.TENCENTDR:
            env_int = DataCenterType.DR

        mask = exchange_maskint(int(mask_int))
        env = DataCenterTypeTransform.MSG_DICT.get(int(env_int))

        connect_instance = vmManager.libvirt_get_connect(host_ip, conn_type='instance', vmname=hostname)
        if not connect_instance:
            status = ActionStatus.FAILD
            message = 'can not connect to libvirt'
            return update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_INJECT_DATA, status, message,
                                           task_id)
        inject_stauts, mesg = vmManager.libvirt_inject_init_data_and_start(connect_instance, host_ip, hostname, env, ip,
                                                                           gateway, dns1, dns2, user_passwd, image_name,
                                                                           mask, ostype)
        if inject_stauts:
            # TO　DO
            status = ActionStatus.SUCCSESS
            message = "create inject data  instance  %s  success! %s " % (uuid, mesg)
        else:
            # TO DO
            status = ActionStatus.FAILD
            message = "create inject data  failed! %s ,time" % (mesg)
        return update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_INJECT_DATA, status, message, task_id)

#vm克隆创建预配置
def vm_pre_conf(request_id, networks, host_ip, uuid, user_id, hostname, ostype, task_id):
    ret_check_status, job_status = _check_job_step_done(request_id, InstaceActions.INSTANCE_CLONE_CREATE_PRE_CONF)
    if ret_check_status and job_status is 1:
        status = ActionStatus.SUCCSESS
        message = 'success'
        return status, message
    else:
        if not ret_check_status:
            add_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CREATE_PRE_CONF, 'start')
        connect_instance = vmManager.libvirt_get_connect(host_ip, conn_type='instance', vmname=hostname)
        if not connect_instance:
            status = ActionStatus.FAILD
            message = 'can not connect to libvirt'
            return update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CREATE_PRE_CONF, status,
                                           message,
                                           task_id)
        #------------------------------------inject_data_prep-------------------------------------------------#
        ip = networks.get('ip')
        mask_int = networks.get('netmask', '255.255.255.0')
        netmask = exchange_maskint(int(mask_int))
        gateway = networks.get('gateway')
        change_gw = "sed -i 's/GATEWAY.*/GATEWAY=" + gateway + "/g' /etc/sysconfig/network"
        change_hostname = "sed -i 's/HOSTNAME.*/HOSTNAME=/g' /etc/sysconfig/network"
        change_ip = "sed -i 's/IPADDR.*/IPADDR=" + ip + "/g' /etc/sysconfig/network-scripts/ifcfg-eth0"
        change_netmask = "sed -i 's/NETMASK.*/NETMASK=" + netmask + "/g' /etc/sysconfig/network-scripts/ifcfg-eth0"
        change_network = change_gw +";"+change_hostname +";"+change_ip+";"+change_netmask
        change_tsagent1 = "sed -i 's/state.*/state = 0/g' /opt/tsagent/conf/agentlocal.ini"
        change_tsagent2 = "sed -i 's/agentid.*/agentid = 0/g' /opt/tsagent/conf/agentlocal.ini"
        change_tsagent3 = "sed -i 's/credential.*/credential = techsure/g' /opt/tsagent/conf/agentlocal.ini"
        change_tsagent = change_tsagent1 +';'+change_tsagent2+';'+change_tsagent3
        change_exagent1 = "sed -i 's/agentid.*/agentid = 0/g' /opt/exagent/conf/agentlocal.ini"
        change_exagent2 = "sed -i 's/credential.*/credential = techsure/g' /opt/exagent/conf/agentlocal.ini"
        change_exagent = change_exagent1 + ';' + change_exagent2
        injectdata = "rm -rf /etc/udev/rules.d/70-persistent-ipoib.rules;rm -rf /etc/udev/rules.d/70-persistent-net.rules;"+ change_network +";"+change_tsagent + ";" \
                     +change_exagent +";reboot"
        # ------------------------------------------------------------------------------------------------------#

        inject_stauts, mesg = vmManager.libvirt_inject_data(connect_instance, injectdata, host_ip, hostname, ostype)
        if inject_stauts:
            # TO　DO
            status = ActionStatus.SUCCSESS
            message = "pre inject data  instance  %s  success!" % (uuid)
        else:
            # TO DO
            status = ActionStatus.FAILD
            message = "pre inject data %s  failed!" % (uuid)
        update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CREATE_PRE_CONF, status, message,
                                task_id)
        return status,message




# 子网掩码计算
def exchange_maskint(mask_int):
    bin_arr = ['0' for i in range(32)]
    for i in range(mask_int):
        bin_arr[i] = '1'
    tmpmask = [''.join(bin_arr[i * 8:i * 8 + 8]) for i in range(4)]
    tmpmask = [str(int(tmpstr, 2)) for tmpstr in tmpmask]
    return '.'.join(tmpmask)

#目标host开启bt传输
def bt_trans_start(host_ip,source_vm,task_id,speed_limit,i):
    instance_name = source_vm
    torrent_file = '/app/clone/'+instance_name + '_' + task_id + '_'+ str(i) +'.torrent'
    ret_bt_trans,bt_trans_msg = ansibleCmdV2.bt_trans_images(host_ip, torrent_file, speed_limit)
    return ret_bt_trans,bt_trans_msg

#获取镜像拷贝速度
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
        return True, 20
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


# 目标host上开启BT传输
def image_bt_trans(host_ip, source_vm, task_id, i, speed):
    # # 获取传输限速
    # trans_speed, speed_data = _confirm_image_get_speed(host_ip)
    # if not trans_speed:
    #     speed = 20
    # else:
    #     speed = speed_data
    # 开启BT传输
    speed_limit = str(int(float(speed) * 1024 / 8))
    ret_bt_trans, bt_trans_msg = bt_trans_start(host_ip, source_vm, task_id, speed_limit,i)
    time.sleep(5)
    return ret_bt_trans, bt_trans_msg


#判断目标host上BT传输是否完成
def check_host_bt_stat(host_ip,source_vm,task_id,i):
    instance_name = source_vm
    grep_parr = instance_name + '_' + task_id + '_'+ str(i)
    ret_bt_trans_stat, bt_trans_stat_msg = ansibleCmdV2.grep_bt_stat(host_ip, grep_parr)
    time.sleep(5)
    return ret_bt_trans_stat, bt_trans_stat_msg


#BT传输及检测函数
def bt_trans_check(host_ip,task_id,source_ip,uuid,request_id,user_id,source_vm,clone_image_num, total_size):
    # 判断该步骤是否完成
    ret_check_status, job_status = _check_job_step_done(request_id, InstaceActions.INSTANCE_CLONE_BT_TRANS_IMAGE)
    if ret_check_status and job_status is 1:
        message = "success"
        logging.info(message)
        return ActionStatus.SUCCSESS, message
    else:
        if not ret_check_status:
            start_msg = 'start,host ip %s' % host_ip
            add_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_BT_TRANS_IMAGE, start_msg)
        if host_ip == source_ip:
            status = ActionStatus.SUCCSESS
            message = "源host %s 与目标host为同一台，pass" % host_ip
            update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_BT_TRANS_IMAGE, status,
                                    message,
                                    task_id)
            return ActionStatus.SUCCSESS, 'pass'
        else:
            # 获取该task_id下是否有其他线程在同host上进行bt传输
            action = InstaceActions.INSTANCE_CLONE_BT_TRANS_IMAGE
            ret_bt_check = ins_s.get_clonecreate_bt_status(task_id,host_ip,action,request_id)
            # 不存在则开启BT传输并在完成后刷新存储池
            if not ret_bt_check:
                # 获取传输限速
                trans_speed, speed_data = _confirm_image_get_speed(host_ip)
                if not trans_speed:
                    speed = 20
                else:
                    speed = float(speed_data)
                timeout = int(total_size*8/1024/1024/speed + 3600)
                msg = "instance %s clone create timeout is %s s and speed is %s MB" % (source_vm, str(timeout), str(speed))
                logging.info(msg)
                timecount = 0
                fail_list = []
                for i in range(int(clone_image_num)):
                    check_result = False
                    # 当传输未完成且时间小于20min时,每隔20s下发BT任务
                    while not check_result and timecount < timeout:
                        ret_check_bt, check_bt_msg = check_host_bt_stat(host_ip, source_vm, task_id,i)
                        if not ret_check_bt:
                            image_bt_trans(host_ip, source_vm, task_id, i, speed)
                            time.sleep(20)
                            timecount += 20
                        else:
                            check_result = True
                    if not check_result:
                        fail_list.append(i)
                if fail_list != []:
                    status = ActionStatus.FAILD
                    message = "目标HOST %s BT获取镜像文件失败" % host_ip
                else:
                    connect_create = vmManager.libvirt_get_connect(host_ip)
                    if not connect_create:
                        status = ActionStatus.FAILD
                        message = '连接libvirt失败'
                    else:
                        ret_refresh = False
                        retry_count = 0
                        while not ret_refresh and retry_count < 20:
                            try:
                                connect_create.refresh_storage_pool_by_name('clone')
                                ret_refresh = True
                            except libvirtError as err:
                                time.sleep(5)
                                retry_count = retry_count +1
                        if not ret_refresh:
                            status = ActionStatus.FAILD
                            message = "目标HOST %s BT获取镜像文件成功,刷新clone池失败" % host_ip
                        else:
                            status = ActionStatus.SUCCSESS
                            message = "目标HOST %s BT获取镜像文件成功,刷新clone池成功" % host_ip
                update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_BT_TRANS_IMAGE, status, message,
                                            task_id)
                return status, message
            #如存在则查看是否已完成
            else:
                check_bt_wait = True
                while check_bt_wait:
                    ret_bt_done = ins_s.get_clonecreate_bt_done(task_id,host_ip,action,request_id)
                    if not ret_bt_done:
                        time.sleep(10)
                    else:
                        check_bt_wait = False
                        status = ActionStatus.SUCCSESS
                        message = "该host %s 上bt传输已完成,pass" % host_ip
                        update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_BT_TRANS_IMAGE,
                                                status,
                                                message,
                                                task_id)
                        return ActionStatus.SUCCSESS, 'pass'



#vm网络配置更改
def change_instance_configure(task_id,host_ip, instance_id, **params):
    instance = ins_s.InstanceService().get_instance_info(instance_id)
    # 连接libvirtd查询虚拟机网卡状态信息
    _net_online = []
    connect_instance = vmManager.libvirt_get_connect(host_ip, conn_type='instance', vmname=instance['name'])
    if not connect_instance:
        return False, 'libvirt connection error'
    else:
        timeout = 1800
        poll_seconds = 10
        deadline = time.time() + timeout
        while time.time() < deadline and not connect_instance.getqemuagentstuats():
            time.sleep(poll_seconds)
        if not connect_instance.getqemuagentstuats():
            return False, 'qemu agent status not ready'
        _libvirt_net_ret, _libvirt_net_info = vmManager.libvirt_get_instance_net_info(connect_instance, instance['name'])
        if not _libvirt_net_ret:
            return False, 'libvirt get nic status fail'
        else:
            if len(_libvirt_net_info) == 0:
                pass
            else:
                for _p_libvirt_net_info in _libvirt_net_info:
                    _net_online.append(_p_libvirt_net_info['mac'])

    print '_net_online list is ' + str(_net_online)

    # 修改网络配置
    _net_status_list = params.get('net_status_list')
    print 'now in network change func,the mac list is ' + str(_net_status_list)
    if params.get('net_status_list'):
        for _per_net_status_list in _net_status_list:
            if str(_per_net_status_list['nic_status']):
                # 获取mac对应ip的vlan信息
                net_info_ret = ins_s.get_net_info_of_instance_by_mac_addr(_per_net_status_list['mac_addr'])
                if not net_info_ret:
                    return False, 'get vlan id fail'
                net_dev = 'br_bond0.' + net_info_ret['vlan']
                _xml_backup_dir = DIR_INSTANCE_XML_BACKUP
                if _per_net_status_list['mac_addr'] in _net_online and str(_per_net_status_list['nic_status']) == '1':
                    pass
                elif _per_net_status_list['mac_addr'] in _net_online and str(_per_net_status_list['nic_status']) == '0':
                    # 备份xml文件
                    instance_xml_backup_status, _msg = _instance_xml_dump(instance['name'], _xml_backup_dir, host_ip)
                    if not instance_xml_backup_status:
                        return False, 'dump xml file fail'

                    # 虚拟机网卡断开
                    net_down_status, _msg = _instance_net_down(instance['name'], _per_net_status_list['mac_addr'],
                                                               host_ip, net_dev)
                    if not net_down_status:
                        return False, 'nic down failed'
                elif _per_net_status_list['mac_addr'] not in _net_online and str(_per_net_status_list['nic_status']) == '0':
                    pass
                elif _per_net_status_list['mac_addr'] not in _net_online and str(_per_net_status_list['nic_status']) == '1':
                    # 虚拟机网卡连接
                    net_on_status, _msg = _instance_net_on(instance['name'], _per_net_status_list['mac_addr'],
                                                           host_ip, net_dev)
                    print 'do net up!'
                    if not net_on_status:
                        return False, 'nic up failed ,msg:' + _msg
    return True, 'nic operation success'


def _update_config_msg_to_db(task_id, msg, job_status):
    update_data = {
        'message': msg,
        'status': job_status,
        'finish_time': get_datetime_str()
    }
    where_data = {
        'task_id': task_id
    }
    return ins_a_s.InstanceActionsServices().update_instance_action_status(update_data, where_data)

# #vm断网
# def clonevm_net_down(task_id,user_id,uuid,request_id,host_ip, instance_id):
#     # 判断该步骤是否完成
#     ret_check_status, job_status = _check_job_step_done(request_id, InstaceActions.INSTANCE_CLONE_CREATE_PRE_NET_DOWN)
#     if ret_check_status and job_status is 1:
#         message = ""
#         logging.info(message)
#         return ActionStatus.SUCCSESS, message
#     else:
#         if not ret_check_status:
#             add_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CREATE_PRE_NET_DOWN, 'start')
#         instance_mac_list = ins_ip_s.get_instance_mac_list(instance_id)
#         n_net_conf_list = []
#         params = {}
#         for mac in instance_mac_list:
#             insert_data = {
#                 "ip_addr": 0,
#                 "mac_addr": mac,
#                 "nic_status": 0
#             }
#             n_net_conf_list.append(insert_data)
#         print "network down list " + str(n_net_conf_list)
#         params['net_status_list'] = n_net_conf_list
#         vm_net_down = change_instance_configure(task_id,host_ip, instance_id, **params)
#         if not vm_net_down:
#             status = ActionStatus.FAILD
#             message = 'vm network down fail'
#         else:
#             message = 'vm network down success'
#             status = ActionStatus.SUCCSESS
#         update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CREATE_PRE_NET_DOWN, status, message, task_id)
#         return status, message


# vm联网
def clonevm_net_up(task_id, user_id, uuid, request_id, host_ip, instance_id):
    # 判断该步骤是否完成
    ret_check_status, job_status = _check_job_step_done(request_id,
                                                        InstaceActions.INSTANCE_CLONE_CREATE_NET_UP)
    if ret_check_status and job_status is 1:
        message = "success"
        logging.info(message)
        return ActionStatus.SUCCSESS, message
    else:
        if not ret_check_status:
            add_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CREATE_NET_UP,
                                 'start')
        # 设置超时规则，每250ms去获取返回结果，结果为空或者查询未超过10min，继续等待250ms
        instance_name = ins_s.InstanceService().get_instance_info(instance_id)['name']
        connect_instance = vmManager.libvirt_get_connect(host_ip, conn_type='instance', vmname=instance_name)
        if not connect_instance:
            status = ActionStatus.FAILD
            message = 'can not connect to libvirt'
            update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_INJECT_DATA, status,
                                           message,
                                           task_id)
            return status, message
        timeout = 1800
        poll_seconds = 10
        deadline = time.time() + timeout
        while time.time() < deadline and not connect_instance.getqemuagentstuats():
            time.sleep(poll_seconds)
        if not connect_instance.getqemuagentstuats():
            status = ActionStatus.FAILD
            message = 'qemu agent connect timeout'
            update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_INJECT_DATA, status,
                                    message,
                                    task_id)
            return status, message
        instance_mac_list = ins_ip_s.get_instance_mac_list(instance_id)
        n_net_conf_list = []
        params = {}
        for mac in instance_mac_list:
            insert_data = {
                "ip_addr": 0,
                "mac_addr": mac,
                "nic_status": 1
            }
            n_net_conf_list.append(insert_data)
        print "network up list " + str(n_net_conf_list)
        params['net_status_list'] = n_net_conf_list
        vm_net_up, net_up_msg = change_instance_configure(task_id, host_ip, instance_id, **params)
        if not vm_net_up:
            status = ActionStatus.FAILD
            message = net_up_msg
        else:
            message = '连通vm网络成功'
            status = ActionStatus.SUCCSESS
        update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CREATE_NET_UP, status, message, task_id)
        return status, message


# 修改images的权限
def change_image_mod(task_id, user_id, uuid, request_id, host_ip, images):
    # 判断该步骤是否完成
    ret_check_status, job_status = _check_job_step_done(request_id,
                                                        InstaceActions.INSTANCE_CLONE_CREATE_CHMOD)
    if ret_check_status and job_status is 1:
        message = "success"
        logging.info(message)
        return ActionStatus.SUCCSESS, message
    else:
        if not ret_check_status:
            add_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CREATE_CHMOD,
                                 'start')
        check_tag = False
        retry_count = 0
        while not check_tag and retry_count  < 8:
            ret_ch_mod, ch_mod_msg = ansibleCmdV2.ch_images_mod( host_ip,images)
            if not ret_ch_mod:
                retry_count = retry_count + 1
                time.sleep(2)
            else:
                check_tag = True
        if not check_tag:
            status = ActionStatus.FAILD
            message = ch_mod_msg
        else:
            message = ch_mod_msg
            status = ActionStatus.SUCCSESS
        update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_CREATE_CHMOD, status, message, task_id)
        return status, message


# WGET获取镜像文件
def wget_image_list(task_id, user_id, uuid, request_id, host_ip, source_image_list, http_port, total_size, source_ip, md5_check):
    # 判断该步骤是否完成
    ret_check_status, job_status = _check_job_step_done(request_id,
                                                        InstaceActions.INSTANCE_CLONE_TRANS_IMAGE)
    if ret_check_status and job_status is 1:
        message = "success"
        logging.info(message)
        return ActionStatus.SUCCSESS, message
    else:
        if not ret_check_status:
            add_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_TRANS_IMAGE,
                                 'start')
        # 获取传输限速
        trans_speed, speed_data = _confirm_image_get_speed(host_ip)
        if not trans_speed:
            speed = 200
        else:
            speed = float(speed_data)
        timeout = int(total_size * 8 / 1024 / 1024 / speed + 600)
        wget_tag = True
        for image in source_image_list:
            ret_send_wget, wget_msg = ansibleCmdV2.wget_clone_image(host_ip, source_ip, http_port, image, speed)
            if not ret_send_wget:
                wget_tag = False
                break
        # wget下发失败则返回
        if not wget_tag:
            status = ActionStatus.FAILD
            message = "wget下发失败%s" % task_id
        else:
            timecount = 0
            wget_finish_tag = False
            vm_tag = source_image_list[0].split("_task")[0]
            while timecount < timeout:
                ret, msg = ansibleCmdV2.check_wget_finish(host_ip, vm_tag)
                if not ret:
                    time.sleep(60)
                    timecount += 60
                else:
                    wget_finish_tag = True
                    break
            if not wget_finish_tag:
                status = ActionStatus.FAILD
                message = "wget下载文件超时%s" % task_id
            else:
                ret, md5_data = ansibleCmdV2.get_clonefile_md5(host_ip, source_image_list[0])
                if not ret:
                    status = ActionStatus.FAILD
                    message = "获取下载后文件%s MD5失败"  % source_image_list[0]
                else:
                    if md5_data != md5_check:
                        status = ActionStatus.FAILD
                        message = "下载后文件md5值 %s与原文件md5值 %s不一致" % (md5_data, md5_check)
                    else:
                        message = "task %s MD5比对成功" % task_id
                        logging.info(message)
                        connect_create = vmManager.libvirt_get_connect(host_ip)
                        if not connect_create:
                            status = ActionStatus.FAILD
                            message = '连接libvirt失败'
                        else:
                            ret_refresh = False
                            retry_count = 0
                            while not ret_refresh and retry_count < 20:
                                try:
                                    connect_create.refresh_storage_pool_by_name('clone')
                                    ret_refresh = True
                                except libvirtError as err:
                                    time.sleep(5)
                                    retry_count = retry_count + 1
                            if not ret_refresh:
                                status = ActionStatus.FAILD
                                message = "目标HOST %s WGET获取镜像文件成功,刷新clone池失败" % host_ip
                            else:
                                status = ActionStatus.SUCCSESS
                                message = "目标HOST %s WGET获取镜像文件成功,刷新clone池成功" % host_ip
        # 源HOST关闭http
        ansibleCmdV2.clone_http_kill(source_ip, str(http_port))
        update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_CLONE_TRANS_IMAGE, status, message, task_id)
        return status, message
