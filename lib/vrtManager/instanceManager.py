# !/usr/bin/env python2.7
# -*- coding:utf-8 -*-
#
from lib import utils
from libvirt import libvirtError, VIR_DOMAIN_XML_SECURE
from config import default
from model.const_define import VMLibvirtStatus
from helper.time_helper import get_datetime_str
from lib.vrtManager import connection as vrtConnect
from lib.vrtManager import create as vrtCreate
from lib.vrtManager import storage as vrtStorage
from lib.vrtManager import instance as vrtInstance
from lib.vrtManager import IPy
from lib.vrtManager import instance
from lib.vrtManager import util

from helper.encrypt_helper import decrypt
from libvirt import VIR_MIGRATE_UNDEFINE_SOURCE, VIR_MIGRATE_LIVE, VIR_MIGRATE_PERSIST_DEST,VIR_MIGRATE_NON_SHARED_DISK
import logging
import time
# from connection import *
import threading
from model.const_define import CentOS_Version
import libvirt_qemu


# 创建连接
@utils.retry(times=3, sleep_time=3)
def libvirt_get_connect(host, conn_type='create', vmname="", poolname=""):
    user = default.HOST_LIBVIRT_USER
    password = decrypt(default.HOST_LIBVIRT_PWD)
    type = default.HOST_LIBVIRT_LOGIN_TYPE
    try:
        if conn_type == 'create':
            conn = vrtCreate.wvmCreate(host, user, password, type)
        elif conn_type == 'storage':
            conn = vrtStorage.wvmStorage(host, user, password, type, poolname)
        elif conn_type == 'storages':
            conn = vrtStorage.wvmStorages(host, user, password, type)
        elif conn_type == 'instance':
            conn = vrtInstance.wvmInstance(host, user, password, type, vmname)
        elif conn_type == 'instances':
            conn = vrtInstance.wvmInstances(host, user, password, type)
        else:
            conn = vrtCreate.wvmCreate(host, user, password, type)

    except libvirtError as err:
        logging.error(err)
        return None
    return conn


# 获取指定主机上的虚拟机清单
def libvirt_get_all_instances_by_host(libvirt_connect_instance, host):
    get_instances = libvirt_connect_instance.get_instances()
    instances = []
    for instance in get_instances:
        try:
            conn = libvirt_get_connect(host, conn_type='instance', vmname=instance)
            network = conn.get_networks()
        except libvirtError as err:
            logging.error(err)
            network = None

        try:
            interfaces = conn.get_net_device()
        except libvirtError as err:
            logging.error(err)
            interfaces = None

        try:
            disks = conn.get_disk_device()
        except libvirtError as err:
            logging.error(err)
            disks = None

        instances.append({'name': instance,
                          'status': libvirt_connect_instance.get_instance_status(instance),
                          'uuid': libvirt_connect_instance.get_uuid(instance),
                          'memory_mb': libvirt_connect_instance.get_instance_memory(instance),
                          'vcpu': libvirt_connect_instance.get_instance_vcpu(instance),
                          'diskcount': libvirt_connect_instance.get_instance_vcpu(instance),
                          'network': network,
                          'interfaces': interfaces,
                          'disks': disks,
                          'has_managed_save_image': libvirt_connect_instance.get_instance_managed_save_image(instance)}
                         )
    return instances


def libvirt_get_instance_info(libvirt_connect_instances, host_ip, instance_name):
    '''
        获取指定虚拟机的信息
    :param libvirt_connect_instances:
    :param host_ip:
    :param instance_name:
    :return:
    '''
    conn = libvirt_get_connect(host_ip, conn_type='instance', vmname=instance_name)
    return {
        'name': instance_name,
        'status': libvirt_connect_instances.get_instance_status(instance_name),
        'uuid': libvirt_connect_instances.get_uuid(instance_name),
        'memory_mb': libvirt_connect_instances.get_instance_memory(instance_name),
        'vcpu': libvirt_connect_instances.get_instance_vcpu(instance_name),
        'diskcount': libvirt_connect_instances.get_instance_vcpu(instance_name),
        'network': conn.get_networks(),
        'interfaces': conn.get_net_device(),
        'disks': conn.get_disk_device(),
        'has_managed_save_image': libvirt_connect_instances.get_instance_managed_save_image(instance_name)
    }


# 获取虚拟机vnc端口
def libvirt_get_vnc_port(libvirt_connect_instance, vnc_instance_name):
    try:
        vnc_port = libvirt_connect_instance.get_console_port()
        if vnc_port:
            return True, vnc_port
        else:
            return False, 'instance %s do not has vnc port' % vnc_instance_name
    except libvirtError as err:
        logging.error("get instance %s vnc port error" % vnc_instance_name)
        logging.error(err)
        return False, err


# 创建存储池
def libvirt_create_storage_pool(libvirt_connect_storages, pool_name_uuid):
    '''
     创建存储池
    :param libvirt_connect:
    :param pool_name_uuid:
    :return:
    '''
    succeed_storage_pool_create = False
    retry_pool_create = 0
    while retry_pool_create < 3 and not succeed_storage_pool_create:
        try:
            get_pools = libvirt_connect_storages.get_storages()
            if pool_name_uuid not in get_pools:
                libvirt_connect_storages.create_storage_uuid(pool_name_uuid)
            succeed_storage_pool_create = True
        except libvirtError as err:
            logging.error("create storage pool failed, name: %s ,because %s" % (pool_name_uuid, err))
            retry_pool_create += 1
            time.sleep(5)

    if retry_pool_create == 3:
        return False, err
    else:
        return True, pool_name_uuid

# 创建BT存储池
def libvirt_create_btstorage_pool(libvirt_connect_storages, pool_name):
    '''
     创建存储池
    :param libvirt_connect:
    :param pool_name_uuid:
    :return:
    '''
    succeed_storage_pool_create = False
    retry_pool_create = 0
    while retry_pool_create < 3 and not succeed_storage_pool_create:
        try:
            get_pools = libvirt_connect_storages.get_storages()
            if pool_name not in get_pools:
                libvirt_connect_storages.create_bt_storage_pool(pool_name)
            succeed_storage_pool_create = True
        except libvirtError as err:
            logging.error("create storage pool failed, name: %s ,because %s" % (pool_name, err))
            retry_pool_create += 1
            time.sleep(5)

    if retry_pool_create == 3:
        return False, err
    else:
        return True, pool_name


# 物理机初始化创建镜像池
def libvirt_create_image_pool(libvirt_connect_storages, pool_name_uuid):
    '''
     创建存储池
    :param libvirt_connect:
    :param pool_name_uuid:
    :return:
    '''
    succeed_storage_pool_create = False
    retry_pool_create = 0
    while retry_pool_create < 3 and not succeed_storage_pool_create:
        try:
            get_pools = libvirt_connect_storages.get_storages()
            if pool_name_uuid not in get_pools:
                libvirt_connect_storages.create_image_pool()
            succeed_storage_pool_create = True
        except libvirtError as err:
            logging.error("create storage pool failed, name: %s ,because %s" % (pool_name_uuid, err))
            retry_pool_create += 1
            time.sleep(5)

    if retry_pool_create == 3:
        return False, err
    else:
        return True, pool_name_uuid


# 物理机初始化创建clone池
def libvirt_create_clone_pool(libvirt_connect_storages, pool_name_uuid):
    '''
     创建存储池
    :param libvirt_connect:
    :param pool_name_uuid:
    :return:
    '''
    succeed_storage_pool_create = False
    retry_pool_create = 0
    while retry_pool_create < 3 and not succeed_storage_pool_create:
        try:
            get_pools = libvirt_connect_storages.get_storages()
            if pool_name_uuid not in get_pools:
                libvirt_connect_storages.create_clone_pool()
            succeed_storage_pool_create = True
        except libvirtError as err:
            logging.error("create storage pool failed, name: %s ,because %s" % (pool_name_uuid, err))
            retry_pool_create += 1
            time.sleep(5)

    if retry_pool_create == 3:
        return False, err
    else:
        return True, pool_name_uuid


# 刷新镜像池
def libvirt_refresh_image_pool(libvirt_connect_create):
    succeed_refresh_image_storage_pool = False
    retry = 0
    while retry < 3 and not succeed_refresh_image_storage_pool:
        try:
            libvirt_connect_create.refresh_image_storage_pool()
            succeed_refresh_image_storage_pool = True
        except libvirtError as err:
            time.sleep(5)
            retry += 1
    if retry == 3:
        return False
    else:
        return True


# 创建镜像盘
def libvirt_clone_image(libvirt_connect_create, image_name, template_path, uuid, disk_dir_path, meta_prealloc=False):
    '''
        克隆镜像磁盘，并生成系统盘和数据盘
    :param libvirt_connect_create: libvirt 连接
    :param image_name: 磁盘的名称 可以为 hostname.img hnostname.disk1 hostname.disk2 hostname
    :param template_path: 镜像的路径
    :param uuid: 主机的UUID：存储pool的名称
    :param disk_num: 通过disk_num 为0，生成的磁盘文件的名称为 .img ，其他的后缀 .disk{disk_num}
    :param meta_prealloc:
    :return:
    '''
    # global LIBVIRT_THREADINGLOCK
    # libvirt_threadinglock = threading.Lock()
    succeed_refresh_image_storage_pool = False
    retry_clone = 0
    while retry_clone < 3 and not succeed_refresh_image_storage_pool:
        try:
            # 镜像存在先删除
            try:
                if libvirt_connect_create.get_vol_by_path(disk_dir_path):
                    libvirt_connect_create.delete_volume(disk_dir_path)
                    libvirt_connect_create.refresh_storage_pool_by_name(uuid)
            except libvirtError as err:
                pass

            clone_path = libvirt_connect_create.clone_from_template_uuid(image_name,
                                                                         template_path,
                                                                         uuid,
                                                                         metadata=meta_prealloc)
            succeed_refresh_image_storage_pool = True
        except libvirtError as err:
            logging.error("clone image failed ,name: %s, because %s" % (template_path, err))
            time.sleep(5)
            retry_clone += 1

    if retry_clone == 3:
        return False, err
    else:
        return True, clone_path


# 获取磁盘信息
def libvirt_get_volumes_info(libvirt_connect, volume_name):
    dict_volumes = {}
    dict_volumes[volume_name] = libvirt_connect.get_volume_type(volume_name)
    return dict_volumes


# 创建磁盘xml
def libvirt_create_data_disk(libvirt_connect_storage, uuid, disk_name,
                             disk_size_gb, disk_format='qcow2', metadata=False):
    '''

    :param libvirt_connect_storage:
    :param uuid:  instance uuid
    :param disk_name: hostname.disk1
    :param dev_name: vdb
    :param disk_size_gb: 80
    :param disk_format: qcow2
    :param metadata:
    :return:
    '''
    succeed_create_data_disk = False
    retry_create_data_disk = 0
    while retry_create_data_disk < 3 and not succeed_create_data_disk:
        try:
            disk_size = disk_size_gb if disk_size_gb >= 50 else 50
            libvirt_connect_storage.refresh()
            disk_names = libvirt_connect_storage.get_volumes()
            # 镜像存在先删除
            try:
                if libvirt_connect_storage.get_volume(disk_name):
                    libvirt_connect_storage.del_volume(disk_name)
                    libvirt_connect_storage.refresh()
            except libvirtError as err:
                pass

            if disk_name not in disk_names:
                disk_xml = libvirt_connect_storage.create_disk(disk_name, disk_size,
                                                               uuid, disk_format,
                                                               metadata)
                succeed_create_data_disk = True
            else:
                logging.info("disk %s is existed" % disk_name)
                succeed_create_data_disk = True

        except libvirtError as err:
            logging.error("create data disk  failed ,name: %s " % disk_name)
            logging.error(err)
            retry_create_data_disk += 1
            time.sleep(5)

    if retry_create_data_disk == 3:
        return False, err
    else:
        return True, disk_name


# 创建虚拟机
def libvirt_create_instance_xml(libvirt_connect_create, hostname, memory_mb,
                                vcpu, uuid, volumes_d, net_card, mac):
    '''

    :param libvirt_connect_create:
    :param hostname: 主机名
    :param memory_mb: 内存大小
    :param vcpu: cpu个数
    :param uuid: instance uuid
    :param volumes_d: 磁盘的字典
    :param net_card:
    :param mac: mac地址
    :param disk_xml: 磁盘的xml文件
    :return:
    '''
    succeed_create_xml = False
    retry_create_xml = 0
    while retry_create_xml < 3 and not succeed_create_xml:
        try:
            instances = libvirt_connect_create.get_instances()
            if hostname in instances:
                logging.info("hostname  %s is existed "% hostname)
                succeed_create_xml = True
            else:
                instance_xml = libvirt_connect_create.create_instance(hostname, memory_mb, vcpu, False, \
                                                       uuid, volumes_d, 'default', net_card, True,  mac)
                succeed_create_xml = True
        except libvirtError as err:
            logging.error("create host connect failed ,name: %s ;because %s" % (hostname, err))
            retry_create_xml += 1
            time.sleep(5)

    if retry_create_xml == 3:
        return False, err
    else:
        return True, 'done'

# 创建虚拟机-无网卡
def libvirt_create_instance_xml_no_nic(libvirt_connect_create, hostname, memory_mb,
                                vcpu, uuid, volumes_d, net_card, mac):
    '''

    :param libvirt_connect_create:
    :param hostname: 主机名
    :param memory_mb: 内存大小
    :param vcpu: cpu个数
    :param uuid: instance uuid
    :param volumes_d: 磁盘的字典
    :param net_card:
    :param mac: mac地址
    :param disk_xml: 磁盘的xml文件
    :return:
    '''
    succeed_create_xml = False
    retry_create_xml = 0
    while retry_create_xml < 3 and not succeed_create_xml:
        try:
            instances = libvirt_connect_create.get_instances()
            if hostname in instances:
                logging.info("hostname  %s is existed " % hostname)
                succeed_create_xml = True
            else:
                instance_xml = libvirt_connect_create.create_instance_no_nic(hostname, memory_mb, vcpu, False, \
                                                                      uuid, volumes_d, 'default', net_card, True,
                                                                      mac)
                succeed_create_xml = True
        except libvirtError as err:
            logging.error("create host connect failed ,name: %s ;because %s" % (hostname, err))
            retry_create_xml += 1
            time.sleep(5)

    if retry_create_xml == 3:
        return False, err
    else:
        return True, 'done'
# 创建虚拟机时对数据盘扩容
def libvirt_create_disk_resize(libvirt_connect_create, stg_pool, disk_path, disk_size):
    succeed_disk_resize = False
    retry_disk_resize = 0
    while retry_disk_resize < 3 and not succeed_disk_resize:
        try:
            libvirt_connect_create.refresh_storage_pool_by_name(stg_pool)
            disk_name = libvirt_connect_create.get_volume_by_path(disk_path)
            if disk_name:
                libvirt_connect_create.resize_vol(disk_path, disk_size)
                succeed_disk_resize = True
            else:
                err = 'can not find disk %s' % disk_path
                retry_disk_resize += 1
        except libvirtError as err:
            logging.error("resize disk failed ,name: %s ,because %s" % (disk_path, err))
            retry_disk_resize += 1
            time.sleep(5)

    if retry_disk_resize == 3:
        return False, err
    else:
        return True, "resize disk successful, name: %s" % disk_path


# 前端配置修改数据盘扩容
def libvirt_config_disk_resize(libvirt_connect_instance, disk_path, disk_size):
    try:
        disk_name = libvirt_connect_instance.get_volume_by_path(disk_path).name()
        if disk_name:
            libvirt_connect_instance.resize_disk(disk_name, disk_size)
            return True, "resize disk successful, name: %s" % disk_path
        return False, "resize disk not find, name: %s" % disk_path

    except libvirtError as err:
        logging.error("resize disk failed ,name: %s " % disk_path)
        logging.error(err)
        return False, err


# 返回虚拟机vnc端口
def libvirt_get_vnc_console(libvirt_connect_instance, vm_name):
    try:
        port = libvirt_connect_instance.get_console_port()
        if not port:
            return False, ''
        return True, port
    except libvirtError as err:
        logging.error("get intance %s name failed because libvirt error" % vm_name)
        logging.error(err)
        return False, err


# 返回虚拟机网卡信息
def libvirt_get_instance_net_info(libvirt_connect_instance, vm_name):
    try:
        _net_data = libvirt_connect_instance.get_config_net_device()
        return True, _net_data
    except libvirtError as err:
        logging.error("get intance %s net info failed because libvirt error" % vm_name)
        logging.error(err)
        return False, err


# 获取指定虚拟机dev名称，如vda、vdb
def libvirt_get_disk_device_by_path(libvirt_connect_instance, disk_path):
    try:
        disk_name = libvirt_connect_instance.get_volume_by_path(disk_path)
        if disk_name:
            disks = libvirt_connect_instance.get_disk_device()
            for disk in disks:
                if disk['path'] == disk_path:
                    disk_device = disk['dev']
                    return True, disk_device
        return False, "disk device not find, name: %s" % disk_path

    except libvirtError as err:
        logging.error("get disk device info failed ,name: %s " % disk_path)
        logging.error(err)
        return False, err


# 修改数据盘配置注入
def libvirt_inject_resize_disk(libvirt_connect_instance, disk_dev, disk_vg_lv, disk_size):
    # 设置超时规则，每250ms去获取返回结果，结果为空或者查询未超过1min，继续等待250ms
    timeout = 60
    poll_seconds = 1
    deadline = time.time() + timeout
    while time.time() < deadline and not libvirt_connect_instance.getqemuagentstuats():
        time.sleep(poll_seconds)
    if not libvirt_connect_instance.getqemuagentstuats():
        return False, 'qemu agent connect timeout'
    try:
        libvirt_connect_instance.resize_disk_by_qemu_agent(disk_dev, disk_vg_lv, disk_size)
        return True, disk_vg_lv
    except libvirtError as err:
        logging.error("use qemu agent to resize disk failed")
        logging.error(err)
        return False, err


# 注入初始化信息并开机
def libvirt_inject_init_data_and_start(libvirt_connect_instance, host_ip, hostname,
                                       env, ip, gateway, dns1, dns2, user_passwd, image_name, mask='255.255.255.0',
                                       ostype="linux", stimeout=200):
    # 设置超时规则，每250ms去获取返回结果，结果为空或者查询未超过10min，继续等待250ms
    timeout = 600
    poll_seconds = 10
    deadline = time.time() + timeout
    while time.time() < deadline and not libvirt_connect_instance.getqemuagentstuats():
        time.sleep(poll_seconds)
    if not libvirt_connect_instance.getqemuagentstuats():
        return False, 'qemu agent connect timeout'
    try:
        access = str(IPy.IP(ip).make_net(mask))
        libvirt_connect_instance.startwcreate(hostname, env, ip, gateway, mask,
                                              dns1, dns2, user_passwd, image_name, access, stimeout, ostype)
        # libvirt_connect_instance.close()
        return True, hostname
    except libvirtError as err:
        logging.error('first inject data error of %s' % hostname)
        logging.error(err)
        try:
            connect_instance = libvirt_get_connect(host_ip, conn_type='instance', vmname=hostname)
            connect_instance.startwcreate(hostname, env, ip, gateway, mask,
                                          dns1, dns2, user_passwd, image_name, access, stimeout, ostype)
            return True, hostname
        except libvirtError as err:
            logging.error("create host and inject init data is failed"
                          " ,data: hostname:%s env:%s ip:%s gateway:%s"
                          " mask:%s dns1:%s dns2:%s stimeout:%s vmtype:%s " %
                          (hostname, env, ip, gateway, mask, dns1, dns2, stimeout, ostype))
            logging.error('second inject data error of %s' % hostname)
            logging.error(err)
            return False, err

#vm自定义注入信息
def libvirt_inject_data(libvirt_connect_instance, injectdata,host_ip, hostname,ostype="linux"):
    # 设置超时规则，每250ms去获取返回结果，结果为空或者查询未超过10min，继续等待250ms
    timeout = 600
    poll_seconds = 10
    deadline = time.time() + timeout
    if ostype == 'windows':
        return False,'not support windows vm'
    while time.time() < deadline and not libvirt_connect_instance.getqemuagentstuats():
        time.sleep(poll_seconds)
    if not libvirt_connect_instance.getqemuagentstuats():
        return False, 'qemu agent connect timeout'
    try:
        libvirt_connect_instance.spec_inject(injectdata, ostype)
        return True, hostname
    except libvirtError as err:
        logging.error('first inject data error of %s' % hostname)
        logging.error(err)
        try:
            connect_instance = libvirt_get_connect(host_ip, conn_type='instance', vmname=hostname)
            connect_instance.spec_inject(injectdata, ostype)
            return True, hostname
        except libvirtError as err:
            logging.error("clone create instance %s failed" %hostname)
            logging.error('second inject data error of %s' % hostname)
            logging.error(err)
            return False, err


# 模板机的信息注入
def image_inject_data(libvirt_connect_instance, injectdata,host_ip, hostname,ostype="linux"):
    # 设置超时规则，每250ms去获取返回结果，结果为空或者查询未超过10min，继续等待250ms
    timeout = 600
    poll_seconds = 10
    deadline = time.time() + timeout
    while time.time() < deadline and not libvirt_connect_instance.getqemuagentstuats():
        time.sleep(poll_seconds)
    if not libvirt_connect_instance.getqemuagentstuats():
        return False, 'qemu agent connect timeout'
    try:
        libvirt_connect_instance.image_inject(injectdata)
        return True, hostname
    except libvirtError as err:
        logging.error('first inject data error of %s' % hostname)
        logging.error(err)
        try:
            connect_instance = libvirt_get_connect(host_ip, conn_type='instance', vmname=hostname)
            connect_instance.image_inject(injectdata)
            return True, hostname
        except libvirtError as err:
            logging.error("clone create instance %s failed" %hostname)
            logging.error('second inject data error of %s' % hostname)
            logging.error(err)
            return False, err


def libvirt_change_instance_ip(libvirt_connect_instance, net_data, vlan_new=False, net_card_new=False):
    if net_card_new:
        ret_status, ret_data = libvirt_connect_instance.add_instance_ip(net_data)
        return ret_status, ret_data
    if not vlan_new:
        ret_status, ret_data = libvirt_connect_instance.change_instance_ip(net_data['mac_addr'], net_data['ip_addr'], net_data['ip_addr_new'])
    else:
        ret_status, ret_data = libvirt_connect_instance.change_instance_ip_netmask_gateway(net_data)
    return ret_status, ret_data


def libvirt_instance_startup(host_ip, instance_name):
    '''
        虚拟机开机
    :param host_ip:
    :param instance_name:
    :return:
    '''
    try:
        conn = libvirt_get_connect(host_ip, conn_type='instances', vmname=instance_name)
        if conn.get_instance_status(instance_name) == VMLibvirtStatus.STARTUP:
            return True
        conn.start(instance_name)
    except libvirtError as err:
        logging.error(err)
        return False
    return True


# 虚拟机外部磁盘快照创建
def ex_disk_snapshot(host_ip, instance_name, image_disk_list):
    try:
        conn = libvirt_get_connect(host_ip, conn_type='instance', vmname=instance_name)
        nowtime = get_datetime_str()
        conn.create_disk_snapshot(image_disk_list, nowtime)
        time.sleep(3)
    except libvirtError as err:
        logging.error(err)
        return False
    return True


# 虚拟机外部磁盘快照整合
def ex_disksnap_commit(host_ip, instance_name, snap_data_list):
    try:
        conn = libvirt_get_connect(host_ip, conn_type='instance', vmname=instance_name)
        for snap_data in snap_data_list:
            disk_tag = snap_data[0]
            snap_url = snap_data[1]
            conn.ex_disk_snapshot_commit(disk_tag, snap_url)
    except libvirtError as err:
        logging.error(err)
        return False
    return True


# def libvirt_instance_start_bypass(host_ip, instance_name):
#     '''
#         虚拟机开机
#     :param host_ip:
#     :param instance_name:
#     :return:
#     '''
#     try:
#         conn = libvirt_get_connect(host_ip, conn_type='instances', vmname=instance_name)
#         if conn.get_instance_status(instance_name) == VMLibvirtStatus.STARTUP:
#             return True
#         conn.start(instance_name)
#     except libvirtError as err:
#         if 'already' in err:
#             return True
#         else:
#             logging.error(err)
#             return False
#     return True

'''
def libvirt_instance_status(host, instance_name):
    try:
        conn = libvirt_get_connect(host,conn_type='instances', vmname=instance_name)
        return conn.get_status(instance_name)
    except libvirtError as err:
        logging.error(err)
        return False
'''


def libvirt_instance_shutdown(host_ip, instance_name):
    '''
        虚拟机关机
    :param host_ip:
    :param instance_name:
    :return:
    '''
    try:
        conn = libvirt_get_connect(host_ip, conn_type='instances', vmname=instance_name)
        conn.shutdown(instance_name)
    except libvirtError as err:
        logging.error(err)
        return False
    return True


def libvirt_instance_force_shutdown(host, instance_name):
    '''
    虚拟机强制关机
    :param host:
    :param instance_name:
    :return:
    '''
    try:
        conn=libvirt_get_connect(host,conn_type='instances',vmname=instance_name)
        conn.force_shutdown(instance_name)
    except libvirtError as err:
        logging.error(err)
        return False
    return True


def libvirt_instance_reboot(host_ip, instance_name):
    '''
        虚拟机重启
    :param host_ip:
    :param instance_name:
    :return:
    '''
    try:
        conn = libvirt_get_connect(host_ip, conn_type='instances', vmname=instance_name)
        conn.reboot(instance_name)
    except libvirtError as err:
        logging.error(err)
        return False
    return True


def libvirt_instance_force_reboot(host_ip, instance_name):
    '''
        虚拟机强制重启
    :param host_ip:
    :param instance_name:
    :return:
    '''
    try:
        conn = libvirt_get_connect(host_ip, conn_type='instances', vmname=instance_name)
        conn.forcereboot(instance_name)
    except libvirtError as err:
        logging.error(err)
        return False
    return True


def libvirt_instance_change_cpu(host_ip, instance_name, cur_vcpu, vcpu):
    '''
        修改虚机CPU
    :param host_ip:
    :param instance_name:
    :param cur_vcpu:
    :param vcpu:
    :return:
    '''
    try:
        conn_instance = libvirt_get_connect(host_ip, conn_type='instance', vmname=instance_name)
        conn_instance.change_vm_cpu(str(vcpu), str(16))
    except libvirtError as err:
        logging.error(err)
        return False
    return True


def libvirt_instance_change_cpu_active(host_ip, instance_name, vcpu):
    '''
        热修改虚机CPU
    :param host_ip:
    :param instance_name:
    :param vcpu:
    :return:
    '''
    try:
        conn_instance = libvirt_get_connect(host_ip, conn_type='instance', vmname=instance_name)
        conn_instance.change_vm_cpu_active(int(vcpu))
    except libvirtError as err:
        logging.error(err)
        return False
    return True


def libvirt_instance_change_memory(host_ip, instance_name, cur_memory, memory):
    '''
        修改虚机内存
    :param host_ip:
    :param instance_name:
    :param cur_memory:
    :param memory:
    :return:
    '''
    try:
        conn_instance = libvirt_get_connect(host_ip, conn_type='instance', vmname=instance_name)
        conn_instance.change_vm_memory(int(memory), int(memory))
    except libvirtError as err:
        logging.error(err)
        return False
    return True



def libvirt_instance_change_memory_active(host_ip, instance_name, memory):
    '''
        热修改虚机内存
    :param host_ip:
    :param instance_name:
    :param memory:
    :return:
    '''
    try:
        conn_instance = libvirt_get_connect(host_ip, conn_type='instance', vmname=instance_name)
        conn_instance.change_vm_memory_active(int(memory))
    except libvirtError as err:
        logging.error(err)
        return False
    return True


def libvirt_instance_status(host_ip, instance_name):
    '''
        获取虚机状态
    :param host_ip:
    :param instance_name:

    '''
    try:
        conn_instance = libvirt_get_connect(host_ip, conn_type='instance', vmname=instance_name)
        if not conn_instance:
            return -100
        status = conn_instance.get_status()
    except libvirtError as err:
        logging.error(err)
        return -100
    return status


def libvirt_get_instance_device(host_ip, instance_name):
    '''
        获取虚拟机磁盘信息用于克隆
    :param host_ip:
    :param instance_name:
    :return:<type 'tuple'>:
    (0,
    [
    {'path': '/app/image/e14f606d-db1a-491f-6f6f-830750924e6a/hostname.img',
    'image': 'hostname.img',
    'storage': 'e14f606d-db1a-491f-6f6f-830750924e6a',
    'dev': 'vda',
    'format': 'qcow2'},
    {'path': '/app/image/e14f606d-db1a-491f-6f6f-830750924e6a/hostname.disk1',
    'image': 'hostname.disk1',
    'storage': 'e14f606d-db1a-491f-6f6f-830750924e6a',
    'dev': 'vdb',
    'format': 'qcow2'}
    ]
    )
    '''
    try:
        conn_instance = libvirt_get_connect(host_ip, conn_type='instance', vmname=instance_name)
        if not conn_instance:
            return -100, 'can not connect libvirtd'
        disks = conn_instance.get_disk_device()
    except libvirtError as err:
        logging.error(err)
        return -100, err
    return 0, disks


def libvirt_instance_clone_create(host_ip, instance_name, clone_data):
    '''
        虚拟机克隆
    :param host_ip:
    :param instance_name:
    :return:
    '''
    try:
        conn_instance = libvirt_get_connect(host_ip, conn_type='instance', vmname=instance_name)
        if not conn_instance:
            return -100, 'can not connect libvirtd'
        _ret_msg = conn_instance.clone_instance(clone_data)
    except libvirtError as err:
        logging.error(err)
        return -100, err
    return 0, _ret_msg


def libvirt_instance_delete(host_ip, instance):
    '''
        删除虚拟机
    :param host_ip:
    :param instance:
    :return:
    '''
    try:
        conn = libvirt_get_connect(host_ip, conn_type='instance', vmname=instance['name'])
        vm_snapshot_count = conn.instance.snapshotNum()
        if vm_snapshot_count != 0:
            logging.error('instance %s has snapshot,please delete snapshot and retry delete instance', instance['name'])
            return False

        vm_all_disk_info = conn.get_delete_disk_device(instance['uuid'])
        for _disk in vm_all_disk_info:
            _stg_pool = _disk['storage']
            _stg = conn.get_storage(_stg_pool)
            _stg.refresh(0)
            _vol = _stg.storageVolLookupByName(_disk['image'])
            # logging.info('start to delete volume %s', str(_disk['image']))
            _vol.delete(0)
            # logging.info('succeed to delete volume %s', str(_disk['image']))

        _stg = conn.get_storage(_stg_pool)
        logging.info('start to stop storage pool %s', str(_disk['storage']))
        _stg.destroy()
        logging.info('succeed to stop storage pool %s', str(_disk['storage']))
        logging.info('start to delete storage pool %s', str(_disk['storage']))
        _stg.delete()
        logging.info('succeed to delete storage pool %s', str(_disk['storage']))
        logging.info('start to undefine storage pool %s', str(_disk['storage']))
        _stg.undefine()
        logging.info('succeed to undefine storage pool %s', str(_disk['storage']))
        conn.delete()
    except libvirtError as err:
        logging.error(err)
        return False
    return True


# 删除指定mac对应网卡
def libvirt_instance_net_down(libvirt_connect_instance, mac, dev):
    net_xml = """
    <interface type='bridge'>
      <mac address='%s'/>
      <source bridge='%s'/>
    </interface>
    """ % (mac, dev)
    succeed_net_down = False
    retry_net_down = 0
    while retry_net_down < 3 and not succeed_net_down:
        try:
            libvirt_connect_instance.detach_net(net_xml)
            succeed_net_down = True
        except libvirtError as err:
            logging.error(err)
            retry_net_down += 1
            time.sleep(5)

    if retry_net_down == 3:
        return False, 'detach net configure because libvirt error'
    else:
        return True, 'detach net successful'


# 添加指定mac对应网卡
def libvirt_instance_net_on(libvirt_connect_instance, mac, dev):
    net_xml = """
    <interface type='bridge'>
      <mac address='%s'/>
      <source bridge='%s'/>
      <model type='virtio'/>
    </interface>
    """ % (mac, dev)
    succeed_net_on = False
    retry_net_on = 0
    while retry_net_on < 3 and not succeed_net_on:
        try:
            libvirt_connect_instance.attach_net(net_xml)
            time.sleep(5)
            succeed_net_on = True
        except libvirtError as err:
            logging.error(err)
            retry_net_on += 1
            time.sleep(5)

    if retry_net_on == 3:
        return False, 'attach net configure because libvirt error'
    else:
        net_up_status, net_up_msg = libvirt_connect_instance.instance_net_up(mac)
        if not net_up_status:
            return False, '无法使用libvirt进行虚拟机ip配置，请联系管理员'
        return True, 'net up successful'


# 修改指定mac对应网卡的bridge值
def libvirt_instance_net_update(libvirt_connect_instance, mac, dev):
    net_xml = """
    <interface type='bridge'>
      <mac address='%s'/>
      <source bridge='%s'/>
      <model type='virtio'/>
    </interface>
    """ % (mac, dev)
    succeed_net_update = False
    retry_net_update = 0
    while retry_net_update < 3 and not succeed_net_update:
        try:
            libvirt_connect_instance.update_net(net_xml)
            succeed_net_update = True
        except libvirtError as err:
            logging.error(err)
            retry_net_update += 1
            time.sleep(5)

    if retry_net_update == 3:
        return False, 'update net configure because libvirt error'
    else:
        return True, 'update net successful'


# 修改指定mac对应网卡的bridge值
def libvirt_instance_net_state_change(libvirt_connect_instance, mac, dev, state):
    net_xml = """
    <interface type='bridge'>
      <mac address='%s'/>
      <source bridge='%s'/>
      <link state='%s'/>
      <model type='virtio'/>
    </interface>
    """ % (mac, dev, state)
    succeed_net_update = False
    retry_net_update = 0
    while retry_net_update < 3 and not succeed_net_update:
        try:
            libvirt_connect_instance.update_net(net_xml)
            succeed_net_update = True
        except libvirtError as err:
            logging.error(err)
            retry_net_update += 1
            time.sleep(1)

    if retry_net_update == 3:
        return False, 'update net configure because libvirt error'
    else:
        return True, 'update net successful'


# 获取指定虚拟机xml文件
def libvirt_instance_xml(libvirt_connect_instance):
    succeed_get_instance_xml = False
    retry_get_instance_xml = 0
    while retry_get_instance_xml < 3 and not succeed_get_instance_xml:
        try:
            instance_xml = libvirt_connect_instance.instance_xml()
            succeed_get_instance_xml = True
        except libvirtError as err:
            logging.error(err)
            retry_get_instance_xml += 1
            time.sleep(5)

    if retry_get_instance_xml == 3:
        return False, 'get instance xml failed because libvirt error'
    else:
        return True, instance_xml


def libvirt_host_instances(host_ip):
    '''
        获取host下所有虚机
    :param host_ip:
    :return:
    '''
    try:
        conn = libvirt_get_connect(host_ip)
        if not conn:
            return None
        instances = conn.get_instances()
    except libvirtError as err:
        logging.error(err)
        return None
    return instances


def libvirt_instance_undefined(host_ip, instance):
    '''
        清除虚拟机和存储池的数据
    :param host_ip:
    :param instance:
    :return:
    '''
    try:
        conn = libvirt_get_connect(host_ip, conn_type='instance', vmname=instance['name'])
        ins = conn.get_instance(instance['name'])
        ins.undefine()

        stg = conn.get_storage(instance['uuid'])
        stg.destroy()
        stg.undefine()
    except libvirtError as err:
        logging.error(err)
        return False
    return True


def v2v_esx_attach_device(host_ip,instance_name,xml):
    try:
        conn_instance = libvirt_get_connect(host_ip, conn_type='instance', vmname=instance_name)
        conn_instance.attach_disk_for_v2v(xml)
    except libvirtError as err:
        logging.error(err)
        return False
    return True

def v2v_win_disk_ch(host_ip,instance_name,disktype):
    try:
        conn_instance = libvirt_get_connect(host_ip, conn_type='instance', vmname=instance_name)
        conn_instance.v2v_set_disk_type_virtio(disktype)
    except libvirtError as err:
        logging.error(err)
        return False
    return True


def v2v_openstack_ipinject(libvirt_connect_instance, hostname, ip, gateway,
                           dns1, dns2, mask='255.255.255.0',ostype="linux", cloudarea="DEV"):
    # 设置超时规则，每10ms去获取返回结果，结果为空或者查询未超过10min，继续等待250ms
    timeout = 300
    poll_seconds = 10
    deadline = time.time() + timeout
    while time.time() < deadline and not libvirt_connect_instance.getqemuagentstuats():
        time.sleep(poll_seconds)
    if not libvirt_connect_instance.getqemuagentstuats():
        return False, 'qemu agent连接超时'
    try:
        libvirt_connect_instance.ip_inject(hostname, ip, gateway, mask, dns1, dns2, ostype, cloudarea)
        return True, hostname
    except libvirtError as err:
        logging.error("IP信息注入失败"" ,data: hostname:%s cloudarea:%s ip:%s gateway:%s"
                      " mask:%s dns1:%s dns2:%s vmtype:%s " %
                      (hostname, cloudarea, ip, gateway, mask, dns1, dns2, ostype))
        logging.error(err)
        return False, err

def v2v_esx_win_inject(libvirt_connect_instance, hostname, ip, gateway,
                           dns1, dns2, mask='255.255.255.0',ostype="linux", cloudarea="DEV"):
    # 设置超时规则，每10ms去获取返回结果，结果为空或者查询未超过10min，继续等待250ms
    timeout = 300
    poll_seconds = 10
    deadline = time.time() + timeout
    while time.time() < deadline and not libvirt_connect_instance.getqemuagentstuats():
        time.sleep(poll_seconds)
    if not libvirt_connect_instance.getqemuagentstuats():
        return False, 'qemu agent连接超时'
    try:
        libvirt_connect_instance.esx_ip_inject(hostname, ip, gateway, mask, dns1, dns2, ostype, cloudarea)
        libvirt_connect_instance.win_disk_online()
        return True, hostname
    except libvirtError as err:
        logging.error("信息注入失败")
        logging.error(err)
        return False, err

# 创建磁盘xml
def libvirt_create_disk(libvirt_connect_storage, uuid, disk_name,
                             disk_size_gb, disk_format='qcow2', metadata=False):
    '''

    :param libvirt_connect_storage:
    :param uuid:  instance uuid
    :param disk_name: hostname.disk1
    :param dev_name: vdb
    :param disk_size_gb: 80
    :param disk_format: qcow2
    :param metadata:
    :return:
    '''
    succeed_create_data_disk = False
    retry_create_data_disk = 0
    disk_xml = ''
    while retry_create_data_disk < 3 and not succeed_create_data_disk:
        try:
            disk_size = disk_size_gb if disk_size_gb >= 50 else 50
            disk_names = libvirt_connect_storage.get_volumes()
            if disk_name not in disk_names:
                print 'ok'
                disk_xml = libvirt_connect_storage.create_disk(disk_name, disk_size,
                                                               uuid, disk_format,
                                                               metadata)
                succeed_create_data_disk = True
            else:
                logging.info("disk %s is existed" % disk_name)
                return False, disk_name

        except libvirtError as err:
            logging.error("create data disk  failed ,name: %s " % disk_name)
            logging.error(err)
            retry_create_data_disk += 1
            time.sleep(5)

    if retry_create_data_disk == 3:
        return False, err
    else:
        return True, disk_xml


def add_disk(libvirt_connect_storage, uuid, disk_name,
                             disk_size_gb, disk_format='qcow2', metadata=False):
    '''

    :param libvirt_connect_storage:
    :param uuid:  instance uuid
    :param disk_name: hostname.disk1
    :param dev_name: vdb
    :param disk_size_gb: 80
    :param disk_format: qcow2
    :param metadata:
    :return:
    '''
    succeed_create_data_disk = False
    retry_create_data_disk = 0
    disk_xml = ''
    while retry_create_data_disk < 3 and not succeed_create_data_disk:
        try:
            # disk_size = disk_size_gb if disk_size_gb > 10 else 10
            disk_size = disk_size_gb + 1 if disk_size_gb > 10 else 10
            disk_names = libvirt_connect_storage.get_volumes()
            if disk_name not in disk_names:
                disk_xml = libvirt_connect_storage.create_disk(disk_name, disk_size,
                                                               uuid, disk_format,
                                                               metadata)
                succeed_create_data_disk = True
            else:
                logging.info("disk %s is existed" % disk_name)
                return False, disk_name

        except libvirtError as err:
            logging.error("create data disk  failed ,name: %s " % disk_name)
            logging.error(err)
            retry_create_data_disk += 1
            time.sleep(5)

    if retry_create_data_disk == 3:
        return False, err
    else:
        # return True, disk_xml
        return True, disk_size


def update_qemu_ga_instance(centostype,host_ip,vmname):
    _instance_connect = libvirt_get_connect(host_ip, conn_type='instance', vmname=vmname)
    return _instance_connect.update_qemu_agent_version(centostype)





def init_env():
    import sys
    import os
    reload(sys)
    sys.setdefaultencoding('utf-8')
    file_basic_path = os.path.dirname(os.path.abspath(__file__))

    basic_path = file_basic_path[0:-4]
    os.environ["BASIC_PATH"] = basic_path  # basic path 放到全局的一个变量当中去
    sys.path.append(basic_path)
    sys.path.append(basic_path + '/config')
    sys.path.append(basic_path + '/helper')
    sys.path.append(basic_path + '/lib')
    sys.path.append(basic_path + '/model')
    sys.path.append(basic_path + '/controller')
    sys.path.append(basic_path + '/service')



def instance_migrate_speed_limit(src_host_ip, dst_host_ip, vmname):
    '''
    热迁移的迁移函数
    :param src_host_ip: 源host的ip
    :param vmname:
    :return:
    '''
    conn = libvirt_get_connect(dst_host_ip, conn_type='instances')
    conn1 = libvirt_get_connect(src_host_ip, conn_type='instance', vmname=vmname)
    if not conn or not conn1:
        return False, '迁移无法连接libvirt'

    dom = conn1.get_instance(vmname)
    try:
        dom.migrate(conn.wvm, VIR_MIGRATE_LIVE | VIR_MIGRATE_PERSIST_DEST | VIR_MIGRATE_NON_SHARED_DISK, vmname, None, 500)
    except libvirtError as err:
        return -1, err

    return True,'SUCCESS'


# 创建磁盘xml
def libvirt_create_disk_hotmigrate(libvirt_connect_storage, uuid, disk_name,
                             disk_size_gb, disk_format='qcow2', metadata=False):
    '''

    :param libvirt_connect_storage:
    :param uuid:  instance uuid
    :param disk_name: hostname.disk
    :param dev_name: vdb
    :param disk_size_gb: 80
    :param disk_format: qcow2
    :param metadata:
    :return:
    '''
    succeed_create_data_disk = False
    retry_create_data_disk = 0
    while retry_create_data_disk < 3 and not succeed_create_data_disk:
        try:
            disk_names = libvirt_connect_storage.get_volumes()
            if disk_name not in disk_names:
                disk_xml = libvirt_connect_storage.create_disk(disk_name, disk_size_gb,
                                                               uuid, disk_format,
                                                               metadata)
                succeed_create_data_disk = True
            else:
                logging.info("disk %s is existed" % disk_name)
                succeed_create_data_disk = True

        except libvirtError as err:
            logging.error("create data disk  failed ,name: %s " % disk_name)
            logging.error(err)
            retry_create_data_disk += 1
            time.sleep(5)

    if retry_create_data_disk == 3:
        return False, err
    else:
        return True, disk_name


def instance_migrate_cancel(libvirt_connect_instance):
    # 设置超时规则，每10ms去获取返回结果，结果为空或者查询未超过10min，继续等待250ms
    try:
        libvirt_connect_instance.cancel_move_to()
    except libvirtError as err:
        logging.error("信息注入失败")
        logging.error(err)
        return False, err
    return True, '取消迁移任务成功'


def libvirt_get_netcard_state(host_ip, instance_name):
    '''
        获取指定虚拟机网卡状态
    :param host_ip:
    :param instance_name:
    :return:
        {'mac': '52:54:00:32:11:30', 'bridge': 'br_bond0.118', 'state': up}
    '''
    try:
        conn_instance = libvirt_get_connect(host_ip, conn_type='instance', vmname=instance_name)
        if not conn_instance:
            return -100, 'can not connect libvirtd'
        netcard = conn_instance.get_netcard_state()
    except libvirtError as err:
        logging.error(err)
        return -100, err
    return 0, netcard
