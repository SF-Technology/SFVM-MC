# coding=utf8

'''
    虚拟机创建任务消费者
'''
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
from service.s_instance.instance_service import InstanceService
from service.s_instance.instance_service import get_hostip_of_instance
from service.s_instance import instance_disk_service as ins_d_s
from service.s_imagecache import imagecache_service as imca_s
from service.s_instance_action import instance_action as ins_a_s
from service.s_host import host_schedule_service as host_s_s
from service.s_image import image_service as image_s
from model.const_define import InstaceActions, ActionStatus, DataCenterTypeTransform, VMStatus, ErrorCode, DataCenterType
from config import default
from helper import json_helper
from helper.encrypt_helper import decrypt
from helper.time_helper import get_datetime_str
from helper.time_helper import get_datetime_str, get_timestamp, change_datetime_to_timestamp
import logging
import traceback
import threading
import socket
import time

INSTANCE_CREATE_THREADINGLOCK = threading.Lock()


def create_instance(msg_data):
    try:
        global INSTANCE_CREATE_THREADINGLOCK
        logging.info("--" * 25)
        logging.info("kafka create instance msg:{}".format(msg_data))
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
        disk_size = data.get('disk_size')
        image_name = data.get('image_name')
        networks = data.get('networks')[0]
        user_id = data.get('user_id')
        net_area_id = data.get('net_area_id')
        pool_status = False
        ostype = data.get('ostype')
        if host_ip is None or request_id is None or not net_area_id:
            logging.error("empty input of host_ip or net_area_id or request_id")
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="empty input of host_ip or net_area_id "
                                                                           "or request_id")

        # 获取前端用户输入root密码用于注入修改
        ins_info = InstanceService().get_instance_info_by_uuid(uuid)
        if ins_info:
            if ins_info['password']:
                user_passwd = decrypt(ins_info['password'])
            else:
                user_passwd = None
        else:
            user_passwd = None

        # 检查镜像和虚拟机目录
        logging.info("start download image or check image status %s " % hostname)
        INSTANCE_CREATE_THREADINGLOCK.acquire()
        try:
            image_status, image_error_msg = check_image_sync_status(request_id, host_ip, uuid, user_id, images,
                                                                    net_area_id, task_id)
            if image_status is ActionStatus.FAILD:
                logging.error(images)
                logging.error("create or download image is failed ! because %s" % image_error_msg)
                vm_create_status = VMStatus.CREATE_ERROR
                _update_instance_status(uuid, vm_create_status)
                INSTANCE_CREATE_THREADINGLOCK.release()
                return 0
        finally:
            INSTANCE_CREATE_THREADINGLOCK.release()
        # 创建存储池
        logging.info("start create pool %s " % uuid)
        create_stg_pool_ret, create_stg_pool_msg = create_storage_pool(request_id, host_ip, uuid, user_id, task_id)
        if create_stg_pool_ret is ActionStatus.FAILD:
            logging.error("create storage pool %s failed because %s" % (uuid, create_stg_pool_msg))
            vm_create_status = VMStatus.CREATE_ERROR
            _update_instance_status(uuid, vm_create_status)
            return 0
        volumes_d = {}
        # 开始克隆镜像
        logging.info("start clone image %s " % images)
        # INSTANCE_CREATE_THREADINGLOCK.acquire()
        clone_image_ret, clone_image_msg = create_clone_image(request_id, host_ip, uuid, user_id, images, task_id)
        if clone_image_ret is ActionStatus.FAILD:
            logging.error("instance %s clone image failed because %s" % (uuid, clone_image_msg))
            vm_create_status = VMStatus.CREATE_ERROR
            _update_instance_status(uuid, vm_create_status)
            return 0
        disk_number = len(images)
        if disk_number == 1:
            disk_name = hostname + '.disk1'
            create_data_disk_ret, create_data_disk_msg = create_data_disk(request_id, host_ip, uuid, user_id, disk_name, 'vdb',
                                                                          int(disk_size), 'qcow2', task_id)
            if create_data_disk_ret is ActionStatus.FAILD:
                logging.error("instance %s create date disk failed because %s" % (uuid, create_data_disk_msg))
                vm_create_status = VMStatus.CREATE_ERROR
                _update_instance_status(uuid, vm_create_status)
                return 0

            """
            # 挂载点
            if ostype == 'linux':
                mount_point = '/app'
            else:
                mount_point = 'E'

            # 对创建的数据盘入库
            instance_disk_data = {
                'instance_id': ins_info['id'],
                'size_gb': int(disk_size),
                'mount_point': mount_point,
                'dev_name': 'vdb',
                'isdeleted': '0',
                'created_at': get_datetime_str()
            }
            disk_db_ret = ins_d_s.InstanceDiskService().add_instance_disk_info(instance_disk_data)
            if disk_db_ret.get('row_num') <= 0:
                logging.info('add instance_disk info error when create instance disk, insert_data: %s',
                             instance_disk_data)
                vm_create_status = VMStatus.CREATE_ERROR
                _update_instance_status(uuid, vm_create_status)
                return 0
            """
            disk_dir = default.INSTANCE_DISK_PATH % (uuid, hostname + ".disk1")
            volumes_d['image_dir_path'] = disk_dir
            volumes_d['dev_name'] = 'vdb'
            images.append(volumes_d)
        # INSTANCE_CREATE_THREADINGLOCK.release()

        # 创建虚拟机xml文件
        networks_name = networks.get('net_card_name')
        mac = networks.get('mac')

        """
        image_count = 0
        for image in images:
            if image_count >= 1:
                dir = default.INSTANCE_DISK_PATH % (uuid, hostname+".disk"+str(image_count))
                volumes_d[dir] = "qcow2"
            else:
                volumes_d[image["image_dir_path"]] = "qcow2"
            image_count = image_count + 1
        """
        create_instance_xml_ret, create_instance_xml_msg = create_instance_first(request_id, host_ip, uuid, user_id,
                                                                                 hostname, memory_mb, vcpu, images,
                                                                                 networks_name, mac, task_id)

        if create_instance_xml_ret is ActionStatus.FAILD:
            logging.error("instance %s create xml failed because %s" % (uuid, create_instance_xml_msg))
            vm_create_status = VMStatus.CREATE_ERROR
            _update_instance_status(uuid, vm_create_status)
            return 0

        # 完成以上操作后开启虚拟机
        """
        ret_check_status, job_status = _check_job_step_done(request_id, InstaceActions.INSTANCE_INJECT_DATA)
        if ret_check_status and job_status is 1:
            pass
        elif ret_check_status and job_status is 2:
            pass
        else:
            if not ret_check_status:
                if not vmManager.libvirt_instance_startup(host_ip, hostname):
                    logging.error("instance %s power on failed" % uuid)
                    vm_create_status = VMStatus.CREATE_ERROR
                    _update_instance_status(uuid, vm_create_status)
                    return 0
        """
        if not vmManager.libvirt_instance_startup(host_ip, hostname):
            logging.error("instance %s power on failed" % uuid)
            vm_create_status = VMStatus.CREATE_ERROR
            _update_instance_status(uuid, vm_create_status)
            return 0

        # 虚拟机初始化注入
        inject_data(request_id, networks, host_ip, uuid, user_id, hostname, ostype, user_passwd, image_name, task_id)
        ret_check_inject_status, job_inject_status = _check_job_step_done(request_id, InstaceActions.INSTANCE_INJECT_DATA)
        if ret_check_inject_status and job_inject_status is 1:
            vm_create_status = VMStatus.STARTUP
            _update_instance_status(uuid, vm_create_status)
            return 0
        else:
            vm_create_status = VMStatus.CREATE_ERROR
            _update_instance_status(uuid, vm_create_status)
            return 0

        """
        # prd、dr环境虚拟机创建完成后需要重启
        if int(networks['env']) == DataCenterType.PRD or int(networks['env']) == DataCenterType.DR:
            if ostype == 'linux':
                if not vmManager.libvirt_instance_force_shutdown(host_ip, hostname):
                    logging.error("instance %s destroy failed" % uuid)
                    vm_create_status = VMStatus.CREATE_ERROR
                    _update_instance_status(uuid, vm_create_status)
                    return 0

                if not vmManager.libvirt_instance_startup(host_ip, hostname):
                    logging.error("instance %s start failed" % uuid)
                    vm_create_status = VMStatus.CREATE_ERROR
                    _update_instance_status(uuid, vm_create_status)
                    return 0

                time.sleep(5)
        """

        """
        if ins_a_s.whether_vm_create_step_error(request_id):
            vm_create_status = VMStatus.CREATE_ERROR
            _update_instance_status(uuid, vm_create_status)
            return 0
        else:
            vm_create_status = VMStatus.STARTUP
            _update_instance_status(uuid, vm_create_status)
            return 0
        """
    except:
        err = traceback.format_exc()
        logging.info(traceback.format_exc())
        vm_create_status = VMStatus.CREATE_ERROR
        _update_instance_status(uuid, vm_create_status)
        return 0


# 检查镜像和同步镜像
def check_image_sync_status(request_id, host_ip, uuid, user_id, imags, net_area_id, task_id):
    # -------------------以下为虚拟机目录检查和创建函数---------------------------------------------------
    # INSTANCE_CREATE_THREADINGLOCK.acquire()
    ret_check_status, job_status = _check_job_step_done(request_id, InstaceActions.INSTANCE_DIRECTORY_CREATE)
    if ret_check_status and job_status is 1:
        pass
    else:
        if not ret_check_status:
            add_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_DIRECTORY_CREATE, 'start')
        instance_directory_create_status = ActionStatus.SUCCSESS
        retry_directory_create = 0
        directory_create_success = False
        while retry_directory_create < 8 and not directory_create_success:
            is_dir_existed = ansibleCmdV2.ansible_remote_check_instance_dir(host_ip, uuid)
            if not is_dir_existed:
                logging.info("instance %s dir is not existed, start to create" % uuid)
                _message = "instance dir %s create successful" % uuid
                instance_directory_create_ret = ansibleCmdV2.ansible_remote_mkdir_instance_dir(host_ip, uuid)
                if not instance_directory_create_ret:
                    instance_directory_create_status = ActionStatus.FAILD
                    _message = "instance dir %s create failed because directory has been exist" % uuid
                    logging.info(_message)
                elif instance_directory_create_ret is 1:
                    instance_directory_create_status = ActionStatus.FAILD
                    _message = "instance dir %s create failed because ansible not available" % uuid
                    logging.info(_message)
                else:
                    directory_create_success = True
                    instance_directory_create_status = ActionStatus.SUCCSESS
                    _message = "instance dir %s create successful" % uuid
            elif is_dir_existed is 1:
                _message = "instance dir %s check error because ansible not available" % uuid
                instance_directory_create_status = ActionStatus.FAILD
                logging.info(_message)
            else:
                directory_create_success = True
                instance_directory_create_status = ActionStatus.SUCCSESS
                _message = "instance dir %s create successful" % uuid
            retry_directory_create += 1
            if not directory_create_success:
                time.sleep(5)
        update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_DIRECTORY_CREATE,
                                instance_directory_create_status, _message, task_id)
        # INSTANCE_CREATE_THREADINGLOCK.release()
        if instance_directory_create_status is ActionStatus.FAILD:
            return instance_directory_create_status, _message

    # -------------------以下为镜像检查和同步函数---------------------------------------------------
    ret_check_status, job_status = _check_job_step_done(request_id, InstaceActions.IMAGE_SYNC_STATUS)
    if ret_check_status and job_status is 1:
        _message = "instance %s all images create successful" % uuid
        return ActionStatus.SUCCSESS, _message
    else:
        if not ret_check_status:
            add_instance_actions(uuid, request_id, user_id, InstaceActions.IMAGE_SYNC_STATUS, 'start')
        delete_instance_action(uuid, request_id, InstaceActions.IMAGE_STATUS)
        image_status = ActionStatus.SUCCSESS
        _message = "instance %s all images create successful" % uuid
        for image in imags:
            retry_image_check = 0
            image_check_success = False
            image_has_ready = False
            status = ActionStatus.SUCCSESS
            disk_name = image['disk_name']
            image_url = image['url']
            image_name = image_url.split('/')[-1]

            # 查询instance_action表中是否有其他consumer在相同物理机上面做镜像检查操作，有则等待
            wait_for_image_check = True
            while wait_for_image_check:
                match_image_check = 0
                image_message = 'check whether image %s is new' % image_name
                action_ret_status, action_ret_data = get_instance_actions_by_message(image_message)
                if action_ret_status:
                    for per_action_data in action_ret_data:
                        # if per_action_data['action'] == 'image_status':
                            # if 'check whether image' in per_action_data['message']:
                        _ins_info = InstanceService().get_instance_info_by_uuid(per_action_data['instance_uuid'])
                        if _ins_info:
                            des_ins_host_ip\
                                = get_hostip_of_instance(_ins_info['id'])
                            if des_ins_host_ip:
                                if des_ins_host_ip == host_ip:
                                    if not _check_vm_action_time(per_action_data['start_time']):
                                        match_image_check += 1
                    if match_image_check == 0:
                        wait_for_image_check = False
                    else:
                        time.sleep(30)
                else:
                    wait_for_image_check = False

            add_instance_actions_status, action_id = add_instance_actions_return_action_id(uuid, request_id,
                                                                                           user_id,
                                                                                           InstaceActions.IMAGE_STATUS,
                                                                                           'check whether image is new',
                                                                                           task_id)

            # 查询数据库表instance_action中相同工单中是否有虚拟机已经完成了相同物理机上面镜像校验操作，有则跳过校验步骤
            action_ret_status, action_ret_data = get_instance_actions_by_taskid(task_id)
            if action_ret_status:
                for per_action_data in action_ret_data:
                    if per_action_data['action'] == 'image_status':
                        if per_action_data['message'] == image_name:
                            # 通过虚拟机uuid找到虚拟机所在物理机
                            _ins_info = InstanceService().get_instance_info_by_uuid(per_action_data['instance_uuid'])
                            if _ins_info:
                                des_ins_host_ip = get_hostip_of_instance(_ins_info['id'])
                                if des_ins_host_ip:
                                    if des_ins_host_ip == host_ip:
                                        image_has_ready = True
                                        continue

            if image_has_ready:
                status = ActionStatus.SUCCSESS
                image_status = ActionStatus.SUCCSESS
                # 把拷贝镜像后的存储池刷新一遍，否则下面镜像克隆会找不到新的镜像
                connect_create = vmManager.libvirt_get_connect(host_ip, conn_type='create')
                if connect_create:
                    vmManager.libvirt_refresh_image_pool(connect_create)
            else:
                while retry_image_check < 8 and not image_check_success:
                    # 获取数据库中最新的md5信息
                    image_db_info = image_s.ImageService().get_image_info_by_url(image_url)
                    if not image_db_info:
                        md5sum = ''
                    md5sum = image_db_info['md5']
                    is_image_existed = ansibleCmdV2.ansible_remote_check_instance_dir(host_ip, image_name)
                    if not is_image_existed:
                        # 获取可用镜像服务器、镜像缓存服务器地址
                        get_img_server_ret, image_server, image_cache_server = _confirm_image_copy_url(str(net_area_id))
                        if not get_img_server_ret:
                            status = ActionStatus.FAILD
                            image_status = ActionStatus.FAILD
                            _one_image_message = "image file %s get failed because %s" % (image_name, image_server)
                        else:
                            # 获取镜像拷贝速度
                            g_flag, g_speed = _confirm_image_get_speed(host_ip)
                            ansibleCmdV2.ansible_remote_download_instance_image(host_ip, image_url, image_name, image_server,
                                                                              image_cache_server, rate_size_mb=g_speed)
                            if not ansibleCmdV2.ansible_remote_check_image_md5sum(host_ip, image_name, md5sum):
                                status = ActionStatus.FAILD
                                image_status = ActionStatus.FAILD
                                _one_image_message = "image file md5sum %s not equ remote image " % md5sum
                            else:
                                image_check_success = True
                                status = ActionStatus.SUCCSESS
                                image_status = ActionStatus.SUCCSESS
                                _one_image_message = "image %s create successful" % image_name
                                # 把拷贝镜像后的存储池刷新一遍，否则下面镜像克隆会找不到新的镜像
                                connect_create = vmManager.libvirt_get_connect(host_ip, conn_type='create')
                                if connect_create:
                                    vmManager.libvirt_refresh_image_pool(connect_create)
                    elif is_image_existed is 1:
                        status = ActionStatus.FAILD
                        image_status = ActionStatus.FAILD
                        _one_image_message = "image file %s check failed because ansible not available" % image_name
                    else:
                        if not ansibleCmdV2.ansible_remote_check_image_md5sum(host_ip, image_name, md5sum):
                            # 获取可用镜像服务器、镜像缓存服务器地址
                            get_img_server_ret, image_server, image_cache_server = _confirm_image_copy_url(str(net_area_id))
                            if not get_img_server_ret:
                                status = ActionStatus.FAILD
                                image_status = ActionStatus.FAILD
                                _one_image_message = "image file %s get failed because %s" % (image_name, image_server)
                            else:
                                g_flag, g_speed = _confirm_image_get_speed(host_ip)
                                ansibleCmdV2.ansible_remote_delete_and_download_instance_image(host_ip, image_url, image_name,
                                                                                             image_server, image_cache_server,
                                                                                             rate_size_mb=g_speed)
                                if not ansibleCmdV2.ansible_remote_check_image_md5sum(host_ip, image_name, md5sum):
                                    status = ActionStatus.FAILD
                                    image_status = ActionStatus.FAILD
                                    _one_image_message = "image file md5sum %s not equ remote image " % md5sum
                                else:
                                    image_check_success = True
                                    status = ActionStatus.SUCCSESS
                                    image_status = ActionStatus.SUCCSESS
                                    _one_image_message = "image %s create successful" % image_name
                                    # 把拷贝镜像后的存储池刷新一遍，否则下面镜像克隆会找不到新的镜像
                                    connect_create = vmManager.libvirt_get_connect(host_ip, conn_type='create')
                                    if connect_create:
                                        vmManager.libvirt_refresh_image_pool(connect_create)
                        else:
                            image_check_success = True
                            status = ActionStatus.SUCCSESS
                            image_status = ActionStatus.SUCCSESS
                            _one_image_message = "image %s create successful" % image_name
                            # 把拷贝镜像后的存储池刷新一遍，否则下面镜像克隆会找不到新的镜像
                            connect_create = vmManager.libvirt_get_connect(host_ip, conn_type='create')
                            if connect_create:
                                vmManager.libvirt_refresh_image_pool(connect_create)
                    retry_image_check += 1
                    if not image_check_success:
                        time.sleep(30)
            if status is ActionStatus.FAILD:
                update_instance_actions_when_image_check(uuid, request_id, user_id, InstaceActions.IMAGE_STATUS, status, _one_image_message, task_id, action_id)
                update_instance_actions(uuid, request_id, user_id, InstaceActions.IMAGE_SYNC_STATUS, image_status,
                                        _one_image_message, task_id)
                return image_status, _one_image_message
            update_instance_actions_when_image_check(uuid, request_id, user_id, InstaceActions.IMAGE_STATUS, status, image_name, task_id, action_id)

        update_instance_actions(uuid, request_id, user_id, InstaceActions.IMAGE_SYNC_STATUS, ActionStatus.SUCCSESS, _message, task_id)
        return ActionStatus.SUCCSESS, _message


# 创建存储池
def create_storage_pool(request_id, host_ip, uuid, user_id, task_id):
    ret_check_status, job_status = _check_job_step_done(request_id, InstaceActions.STORAGE_POOL_CREATE)
    if ret_check_status and job_status is 1:
        status = ActionStatus.SUCCSESS
        message = "create storage pool %s  success!" % uuid
        return status, message
    else:
        if not ret_check_status:
            add_instance_actions(uuid, request_id, user_id, InstaceActions.STORAGE_POOL_CREATE, 'start')
        # 首先判断libvirt是否连接成功
        connect_storages = vmManager.libvirt_get_connect(host_ip, conn_type='storages')
        if not connect_storages:
            status = ActionStatus.FAILD
            message = "create storage pool %s  failed because libvirt connect error" % uuid
            update_instance_actions(uuid, request_id, user_id, InstaceActions.STORAGE_POOL_CREATE, status, message, task_id)
            return status, message
        pool_status, pool_name = vmManager.libvirt_create_storage_pool(connect_storages, uuid)
        if pool_status:
            status = ActionStatus.SUCCSESS
            message = "create storage pool %s  success!" % uuid
        else:
            status = ActionStatus.FAILD
            message = "create storage pool %s  failed!" % uuid
        update_instance_actions(uuid, request_id, user_id, InstaceActions.STORAGE_POOL_CREATE, status, message, task_id)
        return status, message


# 克隆镜像
def create_clone_image(request_id, host_ip, uuid, user_id, imags, task_id):
    ret_check_status, job_status = _check_job_step_done(request_id, InstaceActions.IMAGE_CLONE)
    if ret_check_status and job_status is 1:
        status = ActionStatus.SUCCSESS
        message = 'clone all images successful'
        return status, message
    else:
        if not ret_check_status:
            add_instance_actions(uuid, request_id, user_id, InstaceActions.IMAGE_CLONE, 'start')
        status = ActionStatus.SUCCSESS
        message = 'clone all images successful'
        for image in imags:
            disk_size = image['disk_size_gb']
            image_size = image['image_size_gb']
            disk_name = image['disk_name']
            disk_dir_path = default.INSTANCE_DISK_PATH % (uuid, disk_name)
            image_url = image['url']
            image_name = image_url.split('/')[-1]
            image_path = default.IMAGE_PATH % image_name  # /app/image/centos7.2
            connect_create = vmManager.libvirt_get_connect(host_ip, conn_type='create')
            if not connect_create:
                status = ActionStatus.FAILD
                message = 'can not connect to libvirt'
                update_instance_actions(uuid, request_id, user_id, InstaceActions.IMAGE_CLONE, status, message, task_id)
                return status, message
            disk_status, disk_dir = vmManager.libvirt_clone_image(connect_create, disk_name, image_path, uuid, disk_dir_path)

            if disk_status:
                # 判断数据盘是否需要扩容
                if "disk" in image_name:
                    if not disk_size or not image_size:
                        status = ActionStatus.FAILD
                        message = "empty input of disk_size or image_size for disk %s" % image_name
                        logging.info(message)
                    elif int(disk_size) - int(image_size) > 0:
                        connect_create = vmManager.libvirt_get_connect(host_ip, conn_type='create')
                        if not connect_create:
                            status = ActionStatus.FAILD
                            message = 'can not connect to libvirt'
                            update_instance_actions(uuid, request_id, user_id, InstaceActions.IMAGE_CLONE, status, message,
                                                    task_id)
                            return status, message
                        disk_resize_status, disk_resize_msg = vmManager.libvirt_create_disk_resize(connect_create, uuid,
                                                                                                   disk_dir_path,
                                                                                                   int(disk_size) * 1073741824)
                        if not disk_resize_status:
                            status = ActionStatus.FAILD
                            message = disk_resize_msg
                            logging.info(disk_resize_msg)
            else:
                status = ActionStatus.FAILD
                message = "clone image %s|%s > %s|%s faild! " % (image_name, image_path, disk_name, disk_dir_path)

            if status is ActionStatus.FAILD:
                update_instance_actions(uuid, request_id, user_id, InstaceActions.IMAGE_CLONE, status, message, task_id)
                return status, message
        update_instance_actions(uuid, request_id, user_id, InstaceActions.IMAGE_CLONE, status, message, task_id)
        return status, message


# 使用ansible克隆镜像
def create_clone_image_by_ansible(request_id, host_ip, uuid, user_id, imags, task_id):
    add_instance_actions(uuid, request_id, user_id, InstaceActions.IMAGE_CLONE, 'start')
    status = ActionStatus.SUCCSESS
    message = 'clone all images successful'
    for image in imags:
        disk_size = image['disk_size_gb']
        image_size = image['image_size_gb']
        disk_name = image['disk_name']
        image_url = image['url']
        image_name = image_url.split('/')[-1]
        image_path = default.IMAGE_PATH % image_name  # /app/image/centos7.2
        # connect_create = vmManager.libvirt_get_connect(host_ip, conn_type='create')
        # disk_status, disk_dir = vmManager.libvirt_clone_image(connect_create, disk_name, image_path, uuid)
        disk_status = ansibleCmdV2.ansible_remote_clone_image(host_ip, uuid, image_name, disk_name)
        disk_dir_path = default.INSTANCE_DISK_PATH % (uuid, disk_name)
        if disk_status:
            # 判断数据盘是否需要扩容
            if "disk" in image_name:
                if not disk_size or not image_size:
                    status = ActionStatus.FAILD
                    message = "empty input of disk_size or image_size for disk %s" % image_name
                    logging.info(message)
                elif int(disk_size) - int(image_size) > 0:
                    connect_create = vmManager.libvirt_get_connect(host_ip, conn_type='create')
                    if not connect_create:
                        status = ActionStatus.FAILD
                        message = 'can not connect to libvirt'
                        update_instance_actions(uuid, request_id, user_id, InstaceActions.IMAGE_CLONE, status, message,
                                                task_id)
                        return status, message

                    disk_resize_status, disk_resize_msg = vmManager.libvirt_create_disk_resize(connect_create, uuid,
                                                                                               disk_dir_path,
                                                                                               int(disk_size) * 1073741824)
                    if not disk_resize_status:
                        status = ActionStatus.FAILD
                        message = disk_resize_msg
                        logging.info(disk_resize_msg)
        else:
            status = ActionStatus.FAILD
            message = "clone image %s|%s > %s|%s faild! " % (image_name, image_path, disk_name, disk_dir_path)

        if status is ActionStatus.FAILD:
            update_instance_actions(uuid, request_id, user_id, InstaceActions.IMAGE_CLONE, status, message, task_id)
            return status, message
    update_instance_actions(uuid, request_id, user_id, InstaceActions.IMAGE_CLONE, status, message, task_id)
    return status, message


# 创建磁盘
def create_data_disk(request_id, host_ip, uuid, user_id, disk_name, dev_name, disk_size_gb, disk_format, task_id):
    ret_check_status, job_status = _check_job_step_done(request_id, InstaceActions.DISK_XML_CREATE)
    if ret_check_status and job_status is 1:
        status = ActionStatus.SUCCSESS
        return status, 'create disk success'
    else:
        if not ret_check_status:
            add_instance_actions(uuid, request_id, user_id, InstaceActions.DISK_XML_CREATE, 'start')
        connect_storage = vmManager.libvirt_get_connect(host_ip, conn_type='storage', poolname=uuid)
        if not connect_storage:
            status = ActionStatus.FAILD
            message = 'can not connect to libvirt'
            update_instance_actions(uuid, request_id, user_id, InstaceActions.DISK_XML_CREATE, status, message, task_id)
            return status, message
        disk_status, disk_xml = vmManager.libvirt_create_data_disk(connect_storage, uuid,
                                                                   disk_name, disk_size_gb, disk_format)
        disk_dir_path = default.INSTANCE_DISK_PATH % (uuid, disk_name)
        if disk_status:
            status = ActionStatus.SUCCSESS
            message = "create disk %s  success! %s " % (disk_name, disk_dir_path)
        else:
            status = ActionStatus.FAILD
            message = "create disk  %s  failed! %s " % (disk_name, disk_dir_path)
        update_instance_actions(uuid, request_id, user_id, InstaceActions.DISK_XML_CREATE, status, message, task_id)
        return status, message


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
        refresh_nums = 0
        refresh_status = False
        while refresh_nums < 3 and not refresh_status:
            try:
                connect_create.refresh_storage_pool_by_name(uuid)
                refresh_status = True
            except Exception  as e:
                refresh_nums += 1
                logging.error("instance {} refresh_storage_pool_by_name failed,err_info:{},err_nums: {}".format(uuid,e,refresh_nums))
                time.sleep(1)

        create_status, instance_hostname = vmManager.libvirt_create_instance_xml(connect_create, hostname, memory_mb, vcpu,
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


# 子网掩码计算
def exchange_maskint(mask_int):
    bin_arr = ['0' for i in range(32)]
    for i in range(mask_int):
        bin_arr[i] = '1'
    tmpmask = [''.join(bin_arr[i * 8:i * 8 + 8]) for i in range(4)]
    tmpmask = [str(int(tmpstr, 2)) for tmpstr in tmpmask]
    return '.'.join(tmpmask)


# 创建虚拟机完成后注入数据
def inject_data(request_id, networks, host_ip, uuid, user_id, hostname, ostype, user_passwd, image_name, task_id):
    ret_check_status, job_status = _check_job_step_done(request_id, InstaceActions.INSTANCE_INJECT_DATA)
    if ret_check_status and job_status is 1:
        return 'already done'
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
        if int(env_int) == 4 and ostype == 'windows':
            dns1 = '10.116.56.96'
            dns2 = '10.116.56.97'
        if int(env_int) == 5 and ostype == 'windows':
            dns1 = '10.116.56.96'
            dns2 = '10.116.56.97'

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
            time.sleep(80)
            status = ActionStatus.SUCCSESS
            message = "create inject data  instance  %s  success! %s " % (uuid, mesg)
        else:
            # TO DO
            status = ActionStatus.FAILD
            message = "create inject data %s  failed! %s " % (uuid, mesg)
        return update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_INJECT_DATA, status, message, task_id)


def _update_instance_status(uuid, vm_status):
    update_data = {
        'status': vm_status,
        'updated_at': get_datetime_str()
    }
    where_data = {
        'uuid': uuid
    }
    return InstanceService().update_instance_info(update_data, where_data)


def add_instance_actions(uuid, request_id, user_id, action, message):
    data = {'action': action,
            'instance_uuid': uuid,
            'request_id': request_id,
            'user_id': user_id,
            'message': message
            }
    return ins_a_s.add_instance_actions(data)


def delete_instance_action(uuid, request_id, action):
    return ins_a_s.InstanceActionsServices().delete_instance_action(request_id, action, uuid)


def add_instance_actions_return_action_id(uuid, request_id, user_id, action, message, task_id):
    data = {'action': action,
            'instance_uuid': uuid,
            'request_id': request_id,
            'user_id': user_id,
            'message': message,
            'task_id': task_id
            }
    return ins_a_s.add_instance_actions_when_vm_image_check(data)


def update_instance_actions(uuid, request_id, user_id, action, status, message, task_id):
    return ins_a_s.update_instance_actions_when_vm_create(request_id, action, status, message, task_id)


def update_instance_actions_when_image_check(uuid, request_id, user_id, action, status, message, task_id, action_id):
    return ins_a_s.update_instance_actions_when_image_check(request_id, action, status, message, task_id, action_id)


def get_instance_actions_by_taskid(task_id):
    ret_status, ret_data = ins_a_s.get_instance_action_by_task_id(task_id)
    return ret_status, ret_data


def get_instance_actions_by_message(create_message):
    ret_status, ret_data = ins_a_s.get_instance_action_by_message(create_message)
    return ret_status, ret_data


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

    # 判断性能数据是否有效
    if 'net_size' not in host_used_d:
        return True, "20M"
    if 'current_net_rx_used' not in host_used_d:
        return True, "20M"

    if float(host_used_d["current_net_rx_used"]) < 1:
        current_net_rx_used = 0
    else:
        current_net_rx_used = int(host_used_d["current_net_rx_used"])

    # 获取镜像前限速，根据网络使用率调整迁移速率为（网络带宽-当前使用上传带宽）* 0.8
    # 总带宽 - 已使用带宽 = 剩余带宽，然后只使用80%，这相当最大理论值
    net_speed = (int(host_used_d["net_size"]) - (current_net_rx_used / 100) * int(host_used_d["net_size"])) \
                * 0.8
    # 迁移速度最小确保20MByte = 160 Mbit
    image_get_speed = net_speed if net_speed > 160 else 160

    return True, str(image_get_speed/8) + "M"


def _check_vm_action_time(action_started_time):
    '''
    :param start_creating_time:
    :return: True 虚拟机处于镜像检查时间超过2小时
    :return: False 虚拟机处于镜像检查时间小于等于2小时
    '''
    current_timestamp = get_timestamp() * 1000
    vm_create_start_timestamp = change_datetime_to_timestamp(action_started_time.strftime("%Y-%m-%d %H:%M:%S"))
    if (current_timestamp - vm_create_start_timestamp)/1000 > 2 * 3600:
        return True
    else:
        return False


def _confirm_image_copy_url(net_area_id):
    '''
        返回镜像拷贝地址
    :param speed_limit:
    :param host_s:
    :return:
    '''
    available_image_server = []
    available_cache_image_server = []
    # 通过net_area_id获取镜像服务器、镜像缓存服务器信息
    if not default.IMAGE_SERVER:
        _msg = 'can not find image server'
        logging.error(_msg)
        return False, _msg, ''
    elif len(default.IMAGE_SERVER) <= 0:
        _msg = 'can not find image server'
        logging.error(_msg)
        return False, _msg, ''

    for image_server in default.IMAGE_SERVER:
        if _check_server_is_up(image_server, default.IMAGE_SERVER_PORT):
            available_image_server.append(image_server)

    if len(available_image_server) == 0:
        _msg = 'can not find available image server'
        logging.error(_msg)
        return False, _msg, ''

    imagecache_data = imca_s.ImageCacheService().get_imagecache_info_by_net_area_id(net_area_id)
    if not imagecache_data:
        _msg = 'can not find image cache server'
        logging.error(_msg)
        return False, _msg, ''
    elif len(imagecache_data) <= 0:
        _msg = 'can not find image cache server'
        logging.error(_msg)
        return False, _msg, ''

    for image_cache_server in imagecache_data:
        if _check_server_is_up(image_cache_server['imagecache_ip'], default.NET_AREA_IMAGE_CACHE_SERVER_PORT):
            available_cache_image_server.append(image_cache_server['imagecache_ip'])

    if len(available_cache_image_server) == 0:
        _msg = 'can not find available image cache server'
        logging.error(_msg)
        return False, _msg, ''

    _image_server = 'http://' + available_image_server[0] + ':' + str(default.IMAGE_SERVER_PORT)
    _image_cache_server = 'http://' + available_cache_image_server[0] + ':' \
                          + str(default.NET_AREA_IMAGE_CACHE_SERVER_PORT)
    return True, _image_server, _image_cache_server


# 查看服务器是否可用
def _check_server_is_up(host_ip, host_port):
    """
    returns True if the given host is up and we are able to establish
    a connection using the given credentials.
    """
    try:
        socket_host = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_host.settimeout(0.5)
        socket_host.connect((host_ip, host_port))
        socket_host.close()
        return True
    except Exception as err:
        logging.info(err)
        return False


# 检测虚拟机创建指定步骤是否已经完成
def _check_job_step_done(_request_id, _action_name):
    return ins_a_s.get_instance_action_service_status(_request_id, _action_name)


