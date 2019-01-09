# coding=utf8
'''
    虚拟机热迁移的实际函数
'''
from lib.shell.ansibleCmdV2 import ansible_remote_mkdir_instance_dir, ansible_remote_mkdir_and_dns
from service.s_host import host_schedule_service as host_s_s
from lib.thread import thread_pool
from lib.vrtManager import instanceManager as vmManager
from libvirt import virDomain
from service.s_instance import instance_host_service as ins_h_s, instance_service as ins_s, \
    instance_migrate_service as ins_m_s
# from service.s_instance_action.instance_action import update_instance_actions
from service.s_instance.instance_service import InstanceService
from helper.time_helper import get_datetime_str
from lib.shell.modules.migrateAnsibleCmd import ansible_change_migrate_dir
from service.s_instance_action import instance_action as ins_a_s
from config import default
import logging
import time
import json_helper
from model.const_define import InstaceActions, ActionStatus, MigrateStatus, VMStatus
from lib.vrtManager import instanceManager
import libvirt
import threading


def hot_migrate(msg_data):
    '''
        虚机热迁移
    :param msg_data:
    :return:
    '''
    msg = json_helper.read(msg_data)
    data = msg.get('data')
    request_id = data.get('request_id')
    user_id = data.get('user_id')
    task_id = data.get('task_id')
    migrate_tab_id = data.get('migrate_tab_id')
    ins_data_s = data.get('ins_data_s')
    uuid = data['ins_data_s'].get('uuid')
    instance_id = data['ins_data_s'].get('id')
    instance_name = data['ins_data_s'].get('name')
    # speed_limit = data.get('speed_limit')  暂时不用这个字段
    dst_host_ip = data['host_data_d'].get('ipaddress')
    dst_host_name = data['host_data_d'].get('name')
    dst_host_id = data['host_data_d'].get('id')

    src_host_ip = data['host_data_s'].get('ipaddress')
    src_host_name = data['host_data_s'].get('name')
    src_host_id = data['host_data_s'].get('id')
    pool_status = False

    if dst_host_ip is None or request_id is None:
        logging.error("empty input of host_ip or request_id")
        _update_instance_status(uuid, VMStatus.STARTUP)
        _change_migrate_host(dst_host_id, instance_id)
        ins_m_s.InstanceMigrateService().change_migrate_status(migrate_tab_id, MigrateStatus.SUCCESS)
        return

    # 开始热迁移前获取vm磁盘的大小、名称
    # 热迁移过程中任意一步发生错误都执行以下操作:
    # 1:将instance表中的status值改为运行中，
    # 2:删除instance_host表中新增的instance_dsthost记录
    # 3:将instance_actions表中操作status值改为2（失败）
    # 4:将instance_migrate表中的migrate_status只改为2(失败)
    add_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_HOT_MIGRATE_DISK_INFO, 'start')
    list_instance_status = get_instance_disks_size(src_host_ip, instance_name, uuid)
    if not list_instance_status:
        message = 'instance %s get migrate stats error' % instance_name
        logging.error(message)
        _update_instance_status(uuid, VMStatus.STARTUP)
        _change_migrate_host(dst_host_id, instance_id)
        update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_HOT_MIGRATE_DISK_INFO,
                                ActionStatus.FAILD, message, task_id)
        ins_m_s.InstanceMigrateService().change_migrate_status(migrate_tab_id, MigrateStatus.FAILED)
        return
    else:
        message = 'instance %s get migrate stats success' % instance_name
        update_instance_actions(uuid, request_id, user_id,InstaceActions.INSTANCE_HOT_MIGRATE_DISK_INFO,
                                ActionStatus.SUCCSESS, message, task_id)

    # 在源主机上的Hosts文件中添加目标主机的(IP和名称)记录
    add_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_HOT_MIGRATE_HOSTS_ADD, 'start')
    logging.info('add dst_host record in src_host %s' % uuid)
    retry_directory_create = 0
    while retry_directory_create < 8:
        # ret_d = ansible_remote_check_instance_dir(dst_host_ip, uuid)
        ret_d = ansible_remote_mkdir_and_dns(src_host_ip, dst_host_ip, dst_host_name)
        if ret_d:
            message = 'host %s add dst_host record successful %s' % (dst_host_ip, uuid)
            update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_HOT_MIGRATE_HOSTS_ADD,
                                    ActionStatus.SUCCSESS, message, task_id)
            break
        retry_directory_create += 1
        time.sleep(5)
    else:
        message = "host %s add dst_host record error %s" % (src_host_ip, uuid)
        logging.error(message)
        _update_instance_status(uuid, VMStatus.STARTUP)
        _change_migrate_host(dst_host_id, instance_id)
        update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_HOT_MIGRATE_HOSTS_ADD,
                                ActionStatus.FAILD, message, task_id)
        ins_m_s.InstanceMigrateService().change_migrate_status(migrate_tab_id, MigrateStatus.FAILED)
        return


    # 在目标主机上新建虚拟机镜像存储目录
    add_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_HOT_MIGRATE_MKDIR_DIR, 'start')
    logging.info('get instance disk info %s' % uuid)
    # 设置重试次数8
    retry_directory_create = 0
    while retry_directory_create < 8:
        try:
            ret_d = ansible_remote_mkdir_instance_dir(dst_host_ip, uuid)
            if ret_d:
                message = 'host %s remote mkdir instance %s dir successful' % (dst_host_ip, uuid)
                update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_HOT_MIGRATE_MKDIR_DIR,
                                        ActionStatus.SUCCSESS, message, task_id)
                break
        except libvirt.libvirtError as err:
            logging.error("vm %s create data disk in %s failed because %s" % (instance_name, dst_host_ip, err))
            logging.error(err)
        retry_directory_create += 1
        time.sleep(5)
    else:
        message = 'host %s remote mkdir instance %s dir error' % (dst_host_ip, uuid)
        logging.error(message)
        _update_instance_status(uuid, VMStatus.STARTUP)
        _change_migrate_host(dst_host_id, instance_id)
        update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_HOT_MIGRATE_MKDIR_DIR,
                                ActionStatus.FAILD, message, task_id)
        ins_m_s.InstanceMigrateService().change_migrate_status(migrate_tab_id, MigrateStatus.FAILED)
        return

    # 在目标主机新建虚拟机池
    add_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_HOT_MIGRATE_STORAGE_POOL, message)
    logging.info('start create storage pool %s', uuid)
    ret_p = _create_storage_pool(dst_host_ip, uuid)
    if not ret_p:
        message = 'host %s create storage pool error' % dst_host_ip
        logging.error(message)
        _change_migrate_host(dst_host_id, instance_id)
        _update_instance_status(uuid, VMStatus.STARTUP)
        update_instance_actions(uuid, request_id, user_id,InstaceActions.INSTANCE_HOT_MIGRATE_STORAGE_POOL,
                                ActionStatus.FAILD, message, task_id)
        ins_m_s.InstanceMigrateService().change_migrate_status(migrate_tab_id, MigrateStatus.FAILED)
        return
    else:
        message = 'host %s create storage pool successful' % dst_host_ip
        update_instance_actions(uuid, request_id, user_id,InstaceActions.INSTANCE_HOT_MIGRATE_STORAGE_POOL,
                                ActionStatus.SUCCSESS, message, task_id)

    # 在目标host上创建同样大小、名称的磁盘
    disks_dir_path = []
    for instance_status in list_instance_status:
        disk_name = instance_status['image']
        dev_name = instance_status['dev']
        disk_size = instance_status['disk_size']
        # 记录创建的磁盘的路径
        add_instance_actions(uuid, request_id, user_id, "disk " + dev_name + " create", 'start')
        logging.info('start create disk %s, %s', disk_name, uuid)
        create_data_disk_ret, create_data_disk_msg, disk_dir_path = create_data_disk(request_id, dst_host_ip, uuid, user_id,
                                                                      disk_name, dev_name, int(disk_size/1073741824), 'qcow2', task_id)
        disks_dir_path.append(disk_dir_path)
        if create_data_disk_ret is ActionStatus.FAILD:
            logging.error("instance %s create date disk failed because %s" % (uuid, create_data_disk_msg))
            _change_migrate_host(dst_host_id, instance_id)
            _update_instance_status(uuid, VMStatus.STARTUP)
            update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_HOT_MIGRATE_CHECK_DISK,
                                    ActionStatus.FAILD, message, task_id)
            ins_m_s.InstanceMigrateService().change_migrate_status(migrate_tab_id, MigrateStatus.FAILED)
            return
    # add_instance_actions(uuid,request_id,user_id,InstaceActions.INSTANCE_HOT_MIGRATE_CHECK_DISK,'start')
    # if create_data_disk_ret is ActionStatus.FAILD:
    #     logging.error("instance %s create date disk failed because %s" % (uuid, create_data_disk_msg))
    #     _change_migrate_host(dst_host_id, instance_id)
    #     _update_instance_status(uuid, VMStatus.STARTUP)
    #     update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_HOT_MIGRATE_CHECK_DISK,
    #                             ActionStatus.FAILD, message, task_id)
    #     ins_m_s.InstanceMigrateService().change_migrate_status(migrate_tab_id, MigrateStatus.FAILED)
    #     return
        else:
            message = 'instance %s create disk successful' % (uuid)
            update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_HOT_MIGRATE_CHECK_DISK,
                            ActionStatus.SUCCSESS, message, task_id)

    # libvirt执行实际迁移操作
    add_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_HOT_MIGRATE_START_MOVE, 'start')
    logging.info('start hot migrate %s to destination host', uuid)
    # 加入定时器，move_to_host执行超过40分钟时认定为迁移失败，终止迁移
    move_timer = threading.Timer(7200, cancel_move_to, args=(src_host_ip, instance_name))
    # setDaemon为False表示主线程会等待子线程move_timer执行完才继续执行
    move_timer.setDaemon = False
    move_timer.start()

    # 执行迁移
    move_to_host, move_to_msg = vmManager.instance_migrate_speed_limit(src_host_ip, dst_host_ip, instance_name)
    if move_to_host == True:
    # 迁移成功返回True
        message = 'instance %s moving to host %s successful' % (instance_name, dst_host_ip)
        update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_HOT_MIGRATE_START_MOVE,
                                ActionStatus.SUCCSESS, message, task_id)
    elif move_to_host == -1:
        # 迁移超时被中止
        # message = 'instance %s hot migrate canceled because overtime' % (instance_name)
        _change_migrate_host(dst_host_id, instance_id)
        _update_instance_status(uuid, VMStatus.STARTUP)
        update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_HOT_MIGRATE_START_MOVE,
                                ActionStatus.FAILD, move_to_msg, task_id)
        ins_m_s.InstanceMigrateService().change_migrate_status(migrate_tab_id, MigrateStatus.FAILED)
        # 迁移失败，删除目标Host上刚创建的磁盘
        connect_create = vmManager.libvirt_get_connect(dst_host_ip, conn_type='create')
        try:
            for disk_dir_path in disks_dir_path:
                connect_create.delete_volume(disk_dir_path)
        except libvirt.libvirtError as err:
            logging.error('host %s delete instance %s disk error because %s' % (dst_host_ip, instance_name, err))
        return
    else:
        # move_to_host有返回值时表示迁移失败
        logging.error('instance %s moving to host %s error' % (instance_name, dst_host_ip))
        message = 'instance %s hot migrate moving faild' % (instance_name)
        _change_migrate_host(dst_host_id, instance_id)
        _update_instance_status(uuid, VMStatus.STARTUP)
        update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_HOT_MIGRATE_START_MOVE,
                                ActionStatus.FAILD, message, task_id)
        ins_m_s.InstanceMigrateService().change_migrate_status(migrate_tab_id, MigrateStatus.FAILED)
        # 迁移失败，删除目标Host上刚创建的磁盘
        connect_create = vmManager.libvirt_get_connect(dst_host_ip, conn_type='create')
        try:
            for disk_dir_path in disks_dir_path:
                connect_create.delete_volume(disk_dir_path)
        except libvirt.libvirtError as err:
            logging.error('host %s delete instance %s disk error, because %s' % (dst_host_ip, instance_name, err))
        return

    # 迁移结束之后的操作，以下操作如果出错，都至在LOG中提示，而不作为热迁移失败处理
    # 将存储池在源主机上undefined
    add_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_HOT_MIGRATE_UNDEFINE_S, 'start')
    logging.info('source host %s undefined instance', src_host_ip)
    ret_u = vmManager.libvirt_instance_undefined(src_host_ip, ins_data_s)
    if not ret_u:
        message = 'source host %s undefined instance error' % src_host_ip
        logging.error(message)
        update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_HOT_MIGRATE_UNDEFINE_S,
                                ActionStatus.FAILD, message, task_id)
        return
    else:
        message = 'source host %s undefined instance successful' % src_host_ip
        update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_HOT_MIGRATE_UNDEFINE_S,
                                ActionStatus.SUCCSESS, message, task_id)

    # 修改原虚拟机存储目录名字
    add_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_HOT_MIGRATE_BACKUP_NAME, 'start')
    logging.info('start backup %s name in sourse host', uuid)
    ret_d = ansible_change_migrate_dir(src_host_ip, dst_host_ip, uuid)
    if not ret_d:
        message = 'source host %s backup dir after migrate error' % src_host_ip
        logging.error(message)
        update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_HOT_MIGRATE_BACKUP_NAME, ActionStatus.FAILD, message, task_id)
        return
    else:
        message = 'source host %s backup dir after migrate successful' % src_host_ip
        update_instance_actions(uuid, request_id, user_id, InstaceActions.INSTANCE_HOT_MIGRATE_BACKUP_NAME, ActionStatus.SUCCSESS, message, task_id)

        # 迁移后修改虚拟机状态为运行中
        vm_hot_migrate_status = VMStatus.STARTUP
        ret_v = _update_instance_status(uuid, vm_hot_migrate_status)
        if ret_v != 1:
            logging.error('update instance status error when after hot migrate instance')

        # 迁移完成后删除instance_host表中vm对应源host的记录
        ret_i = _change_migrate_host(src_host_id, instance_id)
        if ret_i <= 0:
            logging.error('delete instance_src_host error when after hot migrate instance')

        # 修改instance_migrate中迁移状态为1，迁移完成
        ret_u = ins_m_s.InstanceMigrateService().change_migrate_status(migrate_tab_id, MigrateStatus.SUCCESS)
        if ret_u != 1:
            logging.error('update instance migrate info error when after hot migrate instance')


def get_instance_disks_size(src_host_ip, instance_name, uuid, action=None):
    '''
    # 获取vm的各个磁盘名称以及大小
    :return: type:list   [{'disk_size': 85899345920L, 'format': 'qcow2', 'image': 'hostname.img', 'storage': 'e14f606d-db1a-491f-6f6f-830750924e6a', 'dev': 'vda', 'path': '/app/image/e14f606d-db1a-491f-6f6f-830750924e6a/hostname.img'}]
    '''
    instances_result = vmManager.libvirt_get_instance_device(src_host_ip, instance_name)
    list_instance_status = instances_result[1]
    # 使用vm的image的名称入参，通过下面函数获取volume的大小
    conn = vmManager.libvirt_get_connect(host=src_host_ip, conn_type="storage",poolname=uuid)
    if not conn:
        return False
    try:
        conn.refresh()
        for disk_name in list_instance_status:
            ret = conn.get_volume_size(disk_name['image'])
            disk_name['disk_size'] = ret
    except libvirt.libvirtError as err:
        logging.error('instance %s get disk info error, because %s' % (instance_name, err))
        return
    return list_instance_status


def create_data_disk(request_id, dst_host_ip, uuid, user_id, disk_name, dev_name, disk_size_gb, disk_format, task_id):
    '''
    # 在目标host上创建磁盘
    :return:
    '''
    if not disk_format:
        disk_format = 'qcow2'
    connect_storage = vmManager.libvirt_get_connect(dst_host_ip, conn_type='storage', poolname=uuid)
    if not connect_storage:
        status = ActionStatus.FAILD
        message = 'can not connect to libvirt'
        update_instance_actions(uuid, request_id, user_id, disk_name + "create", status, message, task_id)
        return status, message, None
    disk_status, disk_xml = vmManager.libvirt_create_disk_hotmigrate(connect_storage, uuid,
                                                               disk_name, disk_size_gb, disk_format)
    disk_dir_path = default.INSTANCE_DISK_PATH % (uuid, disk_name)
    if disk_status:
        status = ActionStatus.SUCCSESS
        message = "create disk %s  success! %s " % (disk_name, disk_dir_path)
    else:
        status = ActionStatus.FAILD
        message = "create disk  %s  failed! %s " % (disk_name, disk_dir_path)
    update_instance_actions(uuid, request_id, user_id, "disk " + dev_name + " create", status, message, task_id)
    return status, message, disk_dir_path


def _update_instance_status(uuid, vm_status):
    update_data = {
        'status': vm_status,
        'updated_at': get_datetime_str()
    }
    where_data = {
        'uuid': uuid
    }
    return InstanceService().update_instance_info(update_data, where_data)


def _confirm_migrate_speed(speed_limit, host_s):
    '''
        热迁移暂时不做速度限制确认，这个函数后续使用
    :param speed_limit:
    :param host_s:
    :return:
    '''
    # 目标主机的性能数据
    host_used_d = host_s_s.get_host_used(host_s)
    # 迁移前限速，根据网络使用率调整迁移速率为（网络带宽-当前使用上传带宽）* 0.8
    # 总带宽 - 已使用带宽 = 剩余带宽，然后只使用80%，这相当最大理论值
    net_speed = (int(host_used_d["net_size"]) -
                 int(host_used_d["current_net_tx_used"]) * int(host_used_d["net_size"])) * 0.8
    # 取两者最小值
    migrate_speed = int(net_speed) if int(speed_limit) > int(net_speed) else int(speed_limit)
    # 迁移速度最小确保20MByte = 160 Mbit
    migrate_speed = migrate_speed if migrate_speed > 160 else 160

    return True, migrate_speed


def _create_storage_pool(host_ip, uuid):
    '''
        创建存储池
    :param host_ip:
    :param uuid:
    :return:
    '''
    connect_storages = instanceManager.libvirt_get_connect(host_ip, conn_type='storages')
    pool_status, pool_name = instanceManager.libvirt_create_storage_pool(connect_storages, uuid)
    if pool_status:
        return True
    return False


def _change_migrate_host(host_id_d, ins_id_s):
    '''
        当迁移失败后将instance_dsthost这条记录删除
        或者迁移成功后将instance_srchost记录删除
    :param host_id_d: 热迁移目标host的id
    :param ins_id_s:
    :return:
    '''
    where_data = {
        'host_id': host_id_d,
        'instance_id': ins_id_s
    }
    return ins_h_s.InstanceHostService().delete_instance_host(where_data)


def add_instance_actions(uuid, request_id, user_id, action, message):
    data = {'action': action,
            'instance_uuid': uuid,
            'request_id': request_id,
            'user_id': user_id,
            'message': message
            }
    return ins_a_s.add_instance_actions(data)


def update_instance_actions(uuid, request_id, user_id, action, status, message, task_id):
    return ins_a_s.update_instance_actions_when_vm_create(request_id, action, status, message, task_id)


def backup_instance_status(instance_id):
    '''
    这个函数作用是当热迁移失败时，由于前端VM页面并没有热迁移失败的状态码，所以在迁移过程中失败后，都直接将VM状态改为运行中
    :return:
    '''
    update_data = {
        'status': VMStatus.STARTUP,
        'updated_at': get_datetime_str()
    }
    where_data = {
        'id': instance_id
    }
    return ins_s.InstanceService().update_instance_info(update_data, where_data)


def cancel_move_to(host_ip, instance_name):
    '''这个函数终止迁移流程'''
    logging.error('instance:%s hot migrate terminated because executing overtime(40min)', instance_name)
    conn = vmManager.libvirt_get_connect(host=host_ip, conn_type='instance', vmname=instance_name)
    if not conn:
        return False

    # ret为True表示取消迁移成功
    ret, message = vmManager.instance_migrate_cancel(conn)
    if ret:
        # 取消迁移成功
        return -1
    else:
        logging.error(message)
        return False



