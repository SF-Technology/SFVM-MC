# -*- coding:utf-8 -*-
#

#   Date    :   2018/2/06
from flask import request

from lib.shell import ansibleCmdV2
from model.const_define import ErrorCode
from lib.vrtManager import instanceManager as vmManager
import logging
import socket
import random
import time

from config.default import IMAGE_OS_TYPE, IMAGE_SERVER, IMAGE_EDIT_SERVER, IMAGE_SERVER_PORT


def img_edit():
    return


def img_checkout():
    return


def img_publish():
    return


def img_fix():
    return


# 镜像模板机开机
def _img_tem_start(image_name):
    host_ip = IMAGE_EDIT_SERVER
    ret, msg = ansibleCmdV2.start_tem_vm(host_ip, image_name)
    if not ret:
        return False, msg
    else:
        connect_instance = vmManager.libvirt_get_connect(host_ip, conn_type='instance', vmname=image_name)
        timeout = 600
        poll_seconds = 10
        deadline = time.time() + timeout
        while time.time() < deadline and connect_instance.get_status() != 1:
            time.sleep(poll_seconds)
        if connect_instance.get_status() != 1:
            err_msg = 'template vm %s start up time out!' % image_name
            logging.error(err_msg)
            return False, err_msg
        else:
            msg = 'template vm %s start up success' % image_name
            logging.info(msg)
            return True, msg


# 镜像模板机创建
def _img_tem_define(image_name):
    host_ip = IMAGE_EDIT_SERVER
    res, image_list_info = ansibleCmdV2.get_image_disk_list(host_ip, image_name)
    if not res:
        return False, image_list_info
    ostype = IMAGE_OS_TYPE
    dir = '/app/image/' + image_name
    res, tem_create_msg = ansibleCmdV2.image_tmp_vm_define(host_ip, dir, image_name, ostype)
    return res, tem_create_msg


# 镜像模板机IP注入
def _img_tem_inject(image_name, ipaddr, netmask, gateway, os_type, os_ver, dns1, dns2):
    host_ip = IMAGE_EDIT_SERVER
    # get libvirt connection
    connect_instance = vmManager.libvirt_get_connect(host_ip, conn_type='instance', vmname=image_name)
    if not connect_instance:
        message = 'image tmp %s inject failed,because libvirt connection error'
        logging.info(message)
        return False, message
    if os_type == 'linux':
        # assemble inject command
        sed_eth0_ip_com = "sed -i 's/IPADDR.*/IPADDR=" + ipaddr + "/g' /etc/sysconfig/network-scripts/ifcfg-eth0"
        sed_eth0_mask_com = "sed -i 's/NETMASK.*/NETMASK=" + netmask + "/g' /etc/sysconfig/network-scripts/ifcfg-eth0"
        sed_gw_com = "sed -i 's/GATEWAY.*/GATEWAY=" + gateway + "/g' /etc/sysconfig/network"
        restart_network = '/etc/init.d/network restart'
        inject_data = sed_eth0_ip_com + ';' + sed_eth0_mask_com + ';' + sed_gw_com + ';' + restart_network
        timeout = 300
        poll_seconds = 10
        deadline = time.time() + timeout
        while time.time() < deadline and not connect_instance.getqemuagentstuats():
            time.sleep(poll_seconds)
        ostype = IMAGE_OS_TYPE
        inject_stauts, mesg = vmManager.image_inject_data(connect_instance, inject_data, host_ip, image_name, ostype)
        if inject_stauts:
            message = "image tmp %s ip inject success!" % image_name
            return True, message
        else:
            message = "image tmp %s ip inject failed!" % image_name
            return False, message
    elif os_type == 'windows':
        if os_ver == '2008':
            set_ip_comm = 'netsh interface ip set address name=\\"Local Area Connection\\" source=static addr=%s mask=%s gateway=%s' % (ipaddr, netmask, gateway)
            set_dns1_comm = 'netsh interface IP set dns name=\\"Local Area Connection\\" source=static %s' % dns1
            set_dns2_comm = 'netsh interface ip add dns name=\\"Local Area Connection\\" %s index=2' % dns2
            inject_data = set_ip_comm + ' && ' + set_dns1_comm + ' && ' + set_dns2_comm
        elif os_ver == '2012':
            set_ip_comm = 'netsh interface ip set address name=Ethernet source=static addr=%s mask=%s gateway=%s' % (ipaddr, netmask, gateway)
            set_dns1_comm = 'netsh interface IP set dns Ethernet source=static %s' % dns1
            set_dns2_comm = 'netsh interface ip add dns Ethernet %s index=2' % dns2
            inject_data = set_ip_comm + ' && ' + set_dns1_comm + ' && ' + set_dns2_comm
        else:
            err_msg = 'the windows template os ver is %s which ip inject is not support!' % os_ver
            return False, err_msg
        #time.sleep(300)
        timeout = 600
        poll_seconds = 10
        deadline = time.time() + timeout
        while time.time() < deadline and not connect_instance.getqemuagentstuats():
            time.sleep(poll_seconds)
        ostype = IMAGE_OS_TYPE
        inject_stauts, mesg = vmManager.image_inject_data(connect_instance, inject_data, host_ip, image_name, ostype)
        if inject_stauts:
            message = "image tmp %s ip inject success!" % image_name
            return True, message
        else:
            message = "image tmp %s ip inject failed!" % image_name
            return False, message
    else:
        err_msg = 'unknown image os type %s!' % os_type
        return False, err_msg


# 镜像模板机清除ip
def img_tem_rm_ip(image_name, os_type):
    host_ip = IMAGE_EDIT_SERVER
    # get libvirt connection
    connect_instance = vmManager.libvirt_get_connect(host_ip, conn_type='instance', vmname=image_name)
    if not connect_instance:
        message = 'image tmp %s inject failed,because libvirt connection error'
        logging.info(message)
        return False, message
    if os_type == 'linux':
        # assemble inject command
        rm_udev_com = "rm -rf /etc/udev/rules.d/70-persistent-ipoib.rules;rm -rf /etc/udev/rules.d/70-persistent-net.rules"
        sed_eth0_com = "sed -i 's/IPADDR.*/IPADDR=/g' /etc/sysconfig/network-scripts/ifcfg-eth0"
        sed_gw_com = "sed -i 's/GATEWAY.*/GATEWAY=/g' /etc/sysconfig/network"
        inject_data = rm_udev_com + ';' + sed_eth0_com + ';' + sed_gw_com
    elif os_type == 'windows':
        inject_data = 'c:\\\windows\\\system32\\\sysprep \\/generalize \\/oobe \\/shutdown \\/unattend:Unattend.xml'
    else:
        err_msg = 'unknown image os type %s' % os_type
        return False, err_msg
    timeout = 300
    poll_seconds = 10
    deadline = time.time() + timeout
    while time.time() < deadline and not connect_instance.getqemuagentstuats():
        time.sleep(poll_seconds)
    ostype = IMAGE_OS_TYPE
    inject_stauts, mesg = vmManager.image_inject_data(connect_instance, inject_data, host_ip, image_name, ostype)
    if inject_stauts:
        message = "image tmp %s ip inject success!" % image_name
        return True, message
    else:
        message = "image tmp %s ip inject failed!" % image_name
        return False, message


# 镜像模板机关机
def _img_tem_shutdown(image_name):
    host_ip = IMAGE_EDIT_SERVER
    # get libvirt connection
    if not vmManager.libvirt_instance_shutdown(host_ip, image_name):
        message = 'image tmp %s shutdown failed' % image_name
        logging.info(message)
        return False, message
    else:
        message = 'image tmp %s exec shutdown successed' % image_name
        logging.info(message)
        connect_instance = vmManager.libvirt_get_connect(host_ip, conn_type='instance', vmname=image_name)
        timeout = 600
        poll_seconds = 10
        deadline = time.time() + timeout
        while time.time() < deadline and connect_instance.get_status() != 5:
            time.sleep(poll_seconds)
        if connect_instance.get_status() != 5:
            msg = 'template exec shutdown time out!please check'
            logging.error(msg)
            return False, msg
        msg = 'template shutdown success'
        return True, msg



# # 镜像同步到image server
# def _sync_image_to_imgserver(image_name):
#     # 镜像编辑服务器本地开启http
#     host_ip = IMAGE_EDIT_SERVER
#     ret, http_port = http_server_start(image_name)
#     if not ret:
#         msg = 'image edit server %s start http service failed' % host_ip
#         return False, msg

# 从已有镜像生成新镜像文件
def _img_create_from_exist(source_img_name, new_img_name):
    # 获取镜像服务器
    avail_imgserver_list = _get_avail_imgserver()
    if avail_imgserver_list == []:
        return False, "无可用镜像服务器获取镜像"
    img_server = avail_imgserver_list[0]
    # 获取镜像文件的list
    ret, image_list_info = ansibleCmdV2.get_image_disk_list(img_server, source_img_name)
    if not ret:
        return False, image_list_info
    # 拉取源镜像文件并改名
    for source_img_disk in image_list_info:
        ret, message = ansibleCmdV2.editserver_get_img(img_server, source_img_name, new_img_name, source_img_disk)
        if not ret:
            logging.error(message)
            return False, message
    message = '获取更新所有镜像文件成功'
    logging.info(message)
    return True, message



# 判断服务端口是否正常
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

# 获取可用镜像服务器
def _get_avail_imgserver():
    avail_list = []
    port = IMAGE_SERVER_PORT
    imgserver_list = IMAGE_SERVER
    for imgserver in imgserver_list:
        ret = _check_server_is_up(imgserver, port)
        if ret:
            avail_list.append(imgserver)
    return avail_list








# 启动本地http服务
def http_server_start(image_name):
    host_ip = IMAGE_EDIT_SERVER
    http_port = http_portget(host_ip)
    dest_dir = '/app/image/' + image_name
    check_result = False
    timecount = 0
    while not check_result and timecount < 3:
        ret_http, http_msg = ansibleCmdV2.python_clone_http(host_ip, dest_dir, http_port)
        logging.info(http_msg)
        time.sleep(1)
        ret_check, ret_msg = ansibleCmdV2.check_port_is_up(host_ip, str(http_port))
        if not ret_check:
            timecount = timecount + 1
        else:
            check_result = True
    return check_result, http_port


# 获取可用的http端口
def http_portget(host_ip):
    i = 1
    while i < 1000:
        randport = random.randint(11000, 12000)
        rand_res = _check_server_is_up(host_ip, randport)
        if rand_res == False:
            return randport
        else:
            i += 1

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

#克隆源服务器本地开启http服务
def clone_source_http(host_ip,image_name,http_port):
    dest_dir = '/app/image/'+ image_name
    check_result = False
    timecount = 0
    while not check_result and timecount < 3:
        ret_http,http_msg = ansibleCmdV2.python_clone_http(host_ip,dest_dir,http_port)
        print http_msg
        time.sleep(1)
        ret_check,ret_msg = ansibleCmdV2.check_port_is_up(host_ip, str(http_port))
        if not ret_check:
            timecount = timecount +1
        else:
            check_result = True
    return check_result\







