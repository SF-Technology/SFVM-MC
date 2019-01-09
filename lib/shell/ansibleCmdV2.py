# -*- coding:utf-8 -*-

import sys

from config import default, ANSIABLE_REMOTE_USER, IMAGE_EDIT_SERVER


from helper.time_helper import get_datatime_one_str

reload(sys)
sys.setdefaultencoding('utf-8')
from lib.shell.ansible_v2_base import AnsibleShell
from helper.encrypt_helper import decrypt


def ansible_run_shell(remote_ip_str, command, timeout=60, remote_password=None):

    '''

    :param remote_ip_str: '10.202.118.186'或者'10.202.118.186,10.202.118.187'
    :param command: 'ls /'
    :param timeout:
    :return: ansible_code 0 运行成功
                           3 无法连接目标主机
                           1/2 执行错误
             ansible_msg  命令运行结果（成功）或者报错信息（失败）

    '''
    remote_ip_list = []
    if ',' in remote_ip_str:
        remote_ip_list = remote_ip_str.split(',')
    else:
        remote_ip_list.append(remote_ip_str)
    ansible_shell = AnsibleShell(remote_ip_str, timeout)
    return ansible_shell.run(command, remote_password)


def ansible_run_copy(remote_ip_str, src_file_dir, dest_file_dir, timeout=60, remote_password=None):
    '''
    :param remote_ip_str: '10.202.118.186'或者'10.202.118.186,10.202.118.187'
    :param remote_ip_str:
    :param src_file_dir: HOST_STANDARD_DIR + '/change_bridge.sh'
    :param dest_file_dir: '/root'
    :param timeout:
    :return: ansible_code 0 运行成功
                          3 无法连接目标主机
                          1/2 执行错误
             ansible_msg  拷贝运行结果（成功）或者报错信息（失败）
    '''

    ansible_shell = AnsibleShell(remote_ip_str, timeout)
    return ansible_shell.copy_file_run(src_file_dir, dest_file_dir, remote_password)


def check_host_bond_connection(host_ip, command):
    '''
        检查指定物理机网桥是否存在
    :param host_ip:
    :param command:
    :return:
    '''
    ansible_code, ansible_msg = ansible_run_shell(host_ip, command, 60)
    if ansible_code == 0:
        std_out = ansible_msg['np_fact_cache'][host_ip]['shell_out']['stdout']
        if not std_out:
            log_msg = 'HOST %s 上主网所在网桥未创建' % host_ip
            return False, True, log_msg
        else:
            return True, True, '获取HOST上主网网桥成功'
    if ansible_code == 3:
        log_msg = "无法连接目标主机，获取HOST：%s主网网桥失败" % host_ip
        return False, False, log_msg
    if ansible_code == 1:
        if ansible_msg['np_fact_cache'][host_ip]['shell_out'].get('failed') and 'stderr' not in \
                ansible_msg['np_fact_cache'][host_ip]['shell_out']:
            log_msg = 'HOST认证失败，获取HOST：%s上主网网桥失败' % host_ip
            return False, False, log_msg
    fail_msg = ansible_msg['np_fact_cache'][host_ip]['shell_out']['stderr']
    if fail_msg:
        log_msg = "获取HOST上主网网桥失败, 失败原因：" + fail_msg
        return False, False, log_msg

    log_msg = '获取HOST上主网网桥失败, 未识别的ansible返回状态:%s, 详细信息:%s' % (str(ansible_code), ansible_msg)
    return False, False, "获取HOST上主网网桥失败, 未识别的ansible返回状态"


def host_std_checklist(host_ip):
    '''
        检查指定物理机初始化执行结果
    :param host_ip:
    :return:
    '''
    command = "cd /root;/bin/bash host_checklist.sh %s" % host_ip
    ansible_code, ansible_msg = ansible_run_shell(host_ip, command, 120)

    if ansible_code == 0:
        return True, 'HOST %s 运行checklist成功' % host_ip
    if ansible_code == 3:
        log_msg = 'HOST无法连接, HOST %s 运行checklist检测失败' % host_ip
        return False, log_msg
    if ansible_code == 1:
        if ansible_msg['np_fact_cache'][host_ip]['shell_out'].get('failed') and 'stderr' not in \
                ansible_msg['np_fact_cache'][host_ip]['shell_out']:
            log_msg = 'HOST认证失败, HOST %s 运行checklist检测失败' % host_ip
            return False, log_msg
    fail_msg = ansible_msg['np_fact_cache'][host_ip]['shell_out']['stderr']
    if fail_msg:
        log_msg = 'HOST %s 运行checklist失败，错误原因:%s' % (host_ip, fail_msg)
        return False, log_msg
    check_code = ansible_msg['np_fact_cache'][host_ip]['shell_out']['rc']
    if check_code == 1:
        std_out = ansible_msg['np_fact_cache'][host_ip]['shell_out']['stdout']
        log_msg = 'HOST %s 运行checklist失败，错误原因%s' % (host_ip, std_out)
        return False, std_out

    log_msg = '未识别的ansible返回状态:%s, 详细信息:%s' % (str(ansible_code), ansible_msg)
    return False, "未识别的ansible返回状态"


def send_file_to_host(host_ip, src_file_dir, dest_file_dir):
    '''
        拷贝文件到指定物理机上指定目录
    :param host_ip:
    :param src_file_dir:
    :param dest_file_dir:
    :return:
    '''
    ansible_copy_code, ansible_copy_msg = ansible_run_copy(host_ip, src_file_dir, dest_file_dir, 30)
    print ansible_copy_code
    if ansible_copy_code == 3:
        log_msg = 'HOST无法连接, 拷贝文件到HOST %s 失败' % host_ip
        return False, log_msg
    if ansible_copy_msg['np_fact_cache'][host_ip]['shell_out'].get('failed'):
        log_msg = '拷贝文件到HOST %s 失败, 原因：%s' % (host_ip,
                                              ansible_copy_msg['np_fact_cache'][host_ip]['shell_out'].get('msg', ''))
        return False, log_msg
    else:
        return True, '拷贝文件到HOST %s 成功' % host_ip


def run_change_host_bridge_shell(host_ip, source_bridge, dest_bridge, vlan_nic):
    '''
        执行修改物理机主网网桥脚本
    :param host_ip:
    :param source_bridge:
    :param dest_bridge:
    :param vlan_nic:
    :return:
    '''
    command = "/usr/bin/sh /root/change_bridge.sh %s %s %s" % (source_bridge, dest_bridge, vlan_nic)
    ansible_code, ansible_msg = ansible_run_shell(host_ip, command, 60)
    # 由于执行此操作会断网，所以命令下发后不对结果做判断
    return True


def host_run_shell(host_ip, command, timeout=60):
    '''
        对指定物理机执行执行shell命令
    :param host_ip:
    :param command:
    :param timeout:
    :return:
        中间值 0：执行成功
               3：目标机器无法连接
               1：目标机器因为用户名密码不对连接失败
               2：由于命令本身原因导致执行失败
               4：命令执行成功，但是没有返回
               5：没有见过的ansible返回结果
    '''
    ansible_code, ansible_msg = ansible_run_shell(host_ip, command, timeout)
    if ansible_code == 0:
        return True, 0, ansible_msg['np_fact_cache'][host_ip]['shell_out']['stdout']
    if ansible_code == 4:
        shell_out = ansible_msg['np_fact_cache'][host_ip]['shell_out']
        if shell_out['unreachable']:
            log_msg = 'HOST SSH 连接失败'
            return False, 3, log_msg
        elif not shell_out['stderr'] and not shell_out['stdout']:
            return True, 0, ''
        else:
            log_msg = '未知的ansible错误'
            return False, 5, log_msg
    # if ansible_code == 2:
    #     log_msg = 'ansible执行失败,%s' % ansible_msg['np_fact_cache'][host_ip]['shell_out']['module_stdout']
    #     init_log(LogType.ANSIBLE_RUN_MESSAGE, log_msg, LogLevel.ERROR)
    #     return False, 1, log_msg
    if ansible_code == 3:
        log_msg = 'HOST %s 无法连接, 命令%s执行失败' % (host_ip, command)
        return False, 3, log_msg
    if ansible_code == 1:
        if ansible_msg['np_fact_cache'][host_ip]['shell_out'].get('failed') and 'stderr' not in \
                ansible_msg['np_fact_cache'][host_ip]['shell_out']:
            log_msg = 'HOST %s 认证失败, 命令%s执行失败' % (host_ip, command)
            return False, 1, log_msg
    try:
        err = ansible_msg['np_fact_cache'][host_ip]['shell_out']['module_stdout']
        log_msg = 'ansible执行失败,%s' % err
        return False, 1, log_msg
    except:
        print "fail msg: {}".format(ansible_msg)
        shell_out = ansible_msg['np_fact_cache'][host_ip]['shell_out']
        check_code = ansible_msg['np_fact_cache'][host_ip]['shell_out']['rc']
        if 'stderr' in shell_out.keys():
            fail_msg = shell_out['stderr']
        elif 'msg' in shell_out.keys():
            fail_msg = shell_out['stderr']
        else:
            fail_msg = "fail msg empty"
        if check_code == 1:
            std_out = ansible_msg['np_fact_cache'][host_ip]['shell_out']['stdout']
            log_msg = 'HOST %s 执行命令%s失败，错误原因:%s' % (host_ip, command, std_out)
            return False, 4, std_out
        if fail_msg:
            log_msg = 'HOST %s 执行命令%s失败，错误原因:%s' % (host_ip, command, fail_msg)
            return False, 2, log_msg

        log_msg = 'HOST %s 执行命令%s失败，未识别的ansible返回状态:%s, 详细信息:%s' % (host_ip, command, str(ansible_code), ansible_msg)
        return False, 5, "未识别的ansible返回状态"




def ansible_remote_backup_instance_xml(host, instance_name, xml, bak_time, backup_dir):
    '''
        备份虚拟机xml文件到指定物理机上的/app/instance_xml_bak目录中
    :param host:
    :param instance_name:
    :param xml:
    :param bak_time:
    :return:
    '''
    instance_xml = "/bin/mkdir -p %s;cd %s;/bin/echo \"%s\" > %s.xml%s" \
                   % (backup_dir, backup_dir, xml, instance_name, bak_time)
    ansible_code, ansible_msg = ansible_run_shell(host, instance_xml)
    if ansible_code == 0:
        return True, '备份虚拟机xml文件到指定物理机上成功'
    elif ansible_code == 1 or ansible_code == 2:
        log_msg = '备份虚拟机xml文件到指定物理机时，执行错误'
        return False, log_msg
    else:
        log_msg = '备份虚拟机xml文件到指定物理机时，无法连接目标主机' + ansible_msg
        return False, log_msg

def ansible_remote_check_host_bridge(host_ip, host_bond):
    '''
        检查远端物理机网桥是否存在
    :param host_ip:
    :param host_bond:
    :return:
    '''
    try:

        check_command = "/sbin/ip a | grep -w %s" % host_bond
        ansible_code, ansible_msg = ansible_run_shell(host_ip, check_command)
        if ansible_code == 0:
            msg = '网桥所关联设备%s存在，物理机ip：%s' % (host_bond, host_ip)
            return True, msg
        elif ansible_code == 1 or ansible_code == 2:
            msg = 'ansible执行命令到指定物理机时，执行错误，物理机ip：%s' % host_ip
            return False, msg
        else:
            msg = '无法连接目标服务器，物理机ip：%s' % host_ip
            return True, msg
    except Exception  as e:
        msg = 'ansible执行失败，物理机ip：%s，报错：%s' % (host_ip, e)
        return False, msg


# ansible调取标准函数
def ansible_run(host, command, r_uer, r_pass, b_user, b_pass, timeout):
    '''v2v迁移pass'''
    return ''

# 下发wget脚本_ansible
def send_wget_sh(host_ip,task_id,check_dir):

    #send_wget_sh_comm = 'scr=' + check_dir +'/deploy/wgetdir/sync_task_' +str(task_id) + ' dest=/root'
    send_wget_sh_comm = {
        'src':check_dir + '/deploy/wgetdir/sync_task_' +str(task_id) +'.sh',
        'dest':'/root'
    }
    ansible_code, ansible_msg = ansible_run_copy(host_ip,send_wget_sh_comm['src'],send_wget_sh_comm['dest'])

    if ansible_code == 3:
        log_msg = 'HOST无法连接, 下发wget脚本到HOST %s 失败' % host_ip
        return False, log_msg
    if ansible_code == 0 :
        return True,'下发wget脚本到HOST成功'
    else:
        log_msg = '下发wget脚本到HOST时，执行错误'
        return False, log_msg

# 获取后台wget进程的pid
def get_wget_pid(host_ip, task_url):
    grep_param = "grep '%s'" % task_url
    get_wget_comm = 'ps -ef|grep wget|' + grep_param + " |cut -d ' ' -f 7"
    ansible_code, ansible_msg = ansible_run_shell(host_ip, get_wget_comm)
    if ansible_code == 3:
        log_msg = 'HOST无法连接, HOST %s 获取后台wget进程的pid失败' % host_ip
        return False, log_msg
    if ansible_code == 0 :
        return True,'获取后台wget进程的pid成功'
    else:
        log_msg = '获取后台wget进程的pid，执行错误'
        return False, log_msg


# 检查远端是否存在wget脚本文件
def wget_file_check(host_ip,task_id):
    check_wget_comm = 'ls /root/sync_task_' + str(task_id) +'.sh'
    ansible_code, ansible_msg = ansible_run_shell(host_ip, check_wget_comm)
    if ansible_code == 3:
        log_msg = 'HOST无法连接, HOST %s 检查远端是否存在wget脚本文件失败' % host_ip
        return False, log_msg
    if ansible_code == 0 :
        return True,'检查远端是否存在wget脚本文件成功'
    else:
        log_msg = '检查远端是否存在wget脚本文件，执行错误'
        return False, log_msg


# 执行wget脚本_ansible
def exec_wget_com(host_ip,task_id):
    wget_command = 'cd /app/image;sh /root/sync_task_' + str(task_id) +'.sh &'
    print wget_command
    ansible_code, ansible_msg = ansible_run_shell(host_ip, wget_command)
    print ansible_code
    if ansible_code == 3:
        log_msg = 'HOST无法连接, HOST %s 执行wget脚失败' % host_ip
        return False, log_msg
    if ansible_code == 0 :
        return True,'执行wget脚成功'
    else:
        log_msg = '执行wget脚，执行错误'
        return False, log_msg

# 检查后台是否有wget在运行
def wget_confirm(host_ip,image_url):
    wget_com = 'grep wget|grep -v grep|grep '+ image_url
    wget_conf = "ps -ef|" + wget_com
    ansible_code, ansible_msg = ansible_run_shell(host_ip, wget_conf)
    print ansible_code
    if ansible_code == 3:
        log_msg = 'HOST无法连接, HOST %s 检查后台是否有wget在运行' % host_ip
        return False, log_msg
    if ansible_code == 0:
        return True, '检查后台是否有wget在运行成功'
    else:
        log_msg = '检查后台是否有wget在运行，执行错误'
        return False, log_msg

# 判断远端文件是否存在
def check_file_exists(host_ip,file_dir):

    check_com = 'ls ' + file_dir
    ansible_code, ansible_msg = ansible_run_shell(host_ip,check_com)
    print 'now check remote file exist or not#######################################'
    print ansible_code
    if ansible_code == 3:
        log_msg = 'HOST无法连接, HOST %s 判断远端文件是否存在' % host_ip
        return False, log_msg
    if ansible_code == 0:
        return True, '判断远端文件是否存在'
    else:
        log_msg = '判断远端文件是否存在，执行错误'
        return False, log_msg

# 下发快照整合脚本到host
def cp_snapshot_commit_shell(source_host, task_id):
    # 下发脚本文件到host
    send_wget_sh_comm = {
        'src': default.DIR_DEFAULT + '/deploy/wgetdir/snapshot_commit_' + str(task_id) + '.sh',
        'dest': '/root'
    }
    ansible_code, ansible_msg = ansible_run_copy(source_host, send_wget_sh_comm['src'],send_wget_sh_comm['dest'])
    print ansible_code
    if ansible_code == 3:
        log_msg = 'HOST无法连接, 下发快照整合脚本到host %s 失败' % source_host
        return False, log_msg
    if ansible_code == 0 :
        return True,'下发快照整合脚本到host成功'
    else:
        log_msg = '下发快照整合脚本到host时，执行错误'
        return False, log_msg

def ansible_remote_check_instance_dir(host_ip, dir_name):
    '''
        检查虚拟机存储目录或者kvm物理机镜像是否存在
    :param host:
    :param dir_name:
    :return:
    '''
    command = "/bin/ls /app/image/ | /bin/grep -x %s" % dir_name
    ret_status, ret_middle_status, ret_msg = host_run_shell(host_ip, command)
    if ret_status:
        return True
    elif not ret_status and ret_middle_status == 4:
        log_msg = '下检查虚拟机存储目录或者kvm物理机镜像是否存在，执行错误,{},{},{}'.format(ret_status, ret_middle_status, ret_msg )
        return False
    else:
        return 1


def ansible_remote_clone_image(host, dir_name, image_name, disk_name):
    '''
        检查虚拟机存储目录或者kvm物理机镜像是否存在
    :param host:
    :param dir_name:
    :return:
    '''
    hostlist = []
    if ','in host:
        hostlist = host.split(',')
    else:
        hostlist.append(host)
    clone_image = "cd /app/image;/usr/bin/qemu-img convert -f qcow2 -O qcow2 %s %s/%s" \
                  % (image_name, dir_name, disk_name)
    ansible_code, ansible_msg = ansible_run_shell(host, clone_image)
    print ansible_code
    if ansible_code == 3:
        log_msg = 'HOST无法连接, 检查虚拟机存储目录或者kvm物理机镜像是否存在 host %s 失败' % host
        return False, log_msg
    if ansible_code == 0:
        return True, '检查虚拟机存储目录或者kvm物理机镜像是否存在 成功'
    else:
        log_msg = '检查虚拟机存储目录或者kvm物理机镜像是否存在，执行错误'
        return False, log_msg

def ansible_remote_mkdir_instance_dir(host, dir_name):
    '''
        创建虚拟机存储目录
    :param host:
    :param dir_name:
    :return:
    '''
    command = "/bin/mkdir -p /app/image/%s" % dir_name
    ret_status, ret_middle_status, ret_msg = host_run_shell(host, command)
    if ret_status:
        return True
    elif not ret_status and ret_middle_status == 2:
        return False
    else:
        return 1


def ansible_remote_download_instance_image(host_ip, image_url, image_name, image_server, image_cache_server, rate_size_mb="60M"):
    '''
        从远端下载镜像
    :param host:
    :param image_url:
    :param image_name:
    :param rate_size_mb:
    :return:
    '''
    image_url_full = image_server + image_url
    command = "export http_proxy\='%s';cd /app/image/;/usr/bin/wget -c -q --limit-rate %s %s" % \
              (image_cache_server, rate_size_mb, image_url_full)
    ret_status, ret_middle_status, ret_msg = host_run_shell(host_ip, command)
    if ret_status:
        return True
    elif not ret_status and ret_middle_status == 2:
        log_msg = '从远端下载镜像，执行错误'
        return False
    else:
        return 1

    # try:
    #     hostlist = []
    #     if ',' in host_ip:
    #         hostlist = host_ip.split(',')
    #     else:
    #         hostlist.append(host_ip)
    #     image_url_full = image_server + image_url
    #     down_cmd = "export http_proxy='%s';cd /app/image/;/usr/bin/wget -c -q --limit-rate=%s %s" \
    #                % (image_cache_server, rate_size_mb, image_url_full)
    #     ansible_code, ansible_msg = ansible_run_shell(host_ip, down_cmd)
    #
    #     print ansible_code
    #     if ansible_code == 3:
    #         log_msg = 'HOST无法连接, 从远端下载镜像 host %s 失败' % host_ip
    #         return False, log_msg
    #     if ansible_code == 0:
    #         return True, '从远端下载镜像 成功'
    #     else:
    #         log_msg = '从远端下载镜像，执行错误'
    #         return False, log_msg
    # except Exception as e:
    #     return False


def ansible_remote_delete_and_download_instance_image(host_ip, image_url, image_name, image_server, image_cache_server, rate_size_mb="60M"):
    '''
        删除非最新镜像文件并从远端下载镜像
    :param host:
    :param image_url:
    :param image_name:
    :param rate_size_mb:
    :return:
    '''
    image_url_full = image_server + image_url
    command = "export http_proxy\='%s';cd /app/image/;/usr/bin/rm -rf %s;/usr/bin/wget -c -q --limit-rate %s %s" % \
              (image_cache_server, image_name, rate_size_mb, image_url_full)
    ret_status, ret_middle_status, ret_msg = host_run_shell(host_ip, command)
    if ret_status:
        return True
    elif not ret_status and ret_middle_status == 2:
        return False
    else:
        return 1


def ansible_remote_get_image_md5sum(host, image_name):
    '''
        检查远端镜像MD5
    :param host:
    :param image_name:
    :return:
    '''
    try:
        hostlist = []
        if ',' in host:
            hostlist = host.split(',')
        else:
            hostlist.append(host)
        down_cmd = "cd /app/image;/usr/bin/md5sum %s " % image_name
        ansible_code, ansible_msg = ansible_run_shell(host, down_cmd)

        print ansible_code, ansible_msg
        if ansible_code == 3:
            log_msg = 'HOST无法连接, 检查远端镜像MD5 host %s 失败' % host
            return {"md5sum": "", "image": image_name}
        if ansible_code == 0:
            res = ansible_msg['np_fact_cache'][host]['shell_out']['stdout'].split()
            return {"md5sum": res[0], "image": res[1]}
        else:
            log_msg = '检查远端镜像MD5，执行错误'
            return {"md5sum": "", "image": image_name}
    except Exception as e:
        return {"md5sum": "", "image": image_name}

def ansible_remote_check_image_md5sum(host_ip, image_name, md5sum):
    '''
            检查远端镜像MD5
        :param host:
        :param image_name:
        :param md5sum: md5sum
        :return:
        '''
    check_command = '/bin/md5sum /app/image/' + image_name + " |cut -d ' ' -f 1"
    check_ret, check_middle_status, image_local_md5 = host_run_shell(host_ip, check_command)
    if not check_ret:
        return False
    else:
        if image_local_md5 == md5sum:
            return True
        else:
            return False


def ansible_remote_check_disk_mount_point(host_ip, vm_uuid, vm_name, mount_point):
    hostlist = [host_ip]
    check_mount_point = "/bin/virt-cat -a /app/image/" + str(vm_uuid) + "/" + str(vm_name) + ".img" \
                        + " /etc/fstab | grep '^/dev'"
    ansible_code, ansible_msg = ansible_run_shell(host_ip, check_mount_point)
    if ansible_code == 3:
        return 1, '', ''
    elif ansible_code != 0:
        return False, '', ''
    else:
        for vm_mount_point in ansible_msg['np_fact_cache'][host_ip]['shell_out']['stdout'].split('\n'):
            if vm_mount_point.split()[1] and mount_point == vm_mount_point.split()[1]:
                if vm_mount_point.split()[0].split('-')[1]:
                    vm_lv_name_in_fstab = vm_mount_point.split()[0].split('-')[1]
                    vm_vg_lv = vm_mount_point.split()[0]
                    return True, vm_lv_name_in_fstab, vm_vg_lv
                else:
                    return True, '', ''
        return True, '', ''



def ansible_remote_check_vm_lv_size(host_ip, vm_disks, vm_lv_name):
    hostlist = [host_ip]
    disk_has_lv = []
    for vm_disk in vm_disks:
        check_disk_size = "/bin/virt-df -h -a " + vm_disk
        ansible_code, ansible_msg = ansible_run_shell(host_ip, check_disk_size)
        if ansible_code != 0:
            pass
        else:
            if vm_lv_name in  ansible_msg['np_fact_cache'][host_ip]['shell_out']['stdout']:
                disk_has_lv.append(vm_disk)
    if len(disk_has_lv) <= 0:
        return False, ''
    else:
        return True, disk_has_lv



def ansible_remote_check_disk(host_ip, vm_uuid, vm_name):
    hostlist = [host_ip]
    disk_num = 0
    _disks = []
    check_disk = "/bin/ls /app/image/" + str(vm_uuid) + "/" + str(vm_name) + ".disk*"
    ansible_code, ansible_msg = ansible_run_shell(host_ip, check_disk)
    if ansible_code == 3:
        return 1, ''
    elif ansible_code != 0:
        return False, ''
    else:
        for _disk in ansible_msg['np_fact_cache'][host_ip]['shell_out']['stdout'].split('\n'):
            if _disk:
               _disks.append(_disk)
        return True, _disks


def ansible_remote_check_vm_lv_in_disk_size(host_ip, vm_disk):
    hostlist = [host_ip]
    check_disk_size = "/bin/qemu-img info " + vm_disk + \
                      " | grep 'virtual size' | awk '{print $3}' | awk -F \"G\" '{print $1}'"
    ansible_code, ansible_msg = ansible_run_shell(host_ip, check_disk_size)
    if ansible_code != 0:
        return False, ''
    else:
        disk_size = ansible_msg['np_fact_cache'][host_ip]['shell_out']['stdout']
        if disk_size.isdigit():
            return True, disk_size
        else:
            return False, ''

def ansible_remote_backup_instance_xml(host, instance_name, xml, bak_time, backup_dir):
    '''
        备份虚拟机xml文件到指定物理机上的/app/instance_xml_bak目录中
    :param host:
    :param instance_name:
    :param xml:
    :param bak_time:
    :return:
    '''
    hostlist = []
    if ','in host:
        hostlist = host.split(',')
    else:
        hostlist.append(host)
    instance_xml = "/bin/mkdir -p %s;cd %s;/bin/echo \"%s\" > %s.xml%s" \
                   % (backup_dir, backup_dir, xml, instance_name, bak_time)
    ansible_code, ansible_msg = ansible_run_shell(host, instance_xml)
    if ansible_code == 3:
        return 1

    elif ansible_code != 0:
        return False
    else:
        return True


def ansible_check_instance_shutdown_time(host_ip, vm_name):
    '''
        检查虚拟机关机时间是否超过一天
    :param host_ip:
    :param vm_name:
    :return:
    '''
    return True

# 获取目标host指定镜像名的md5值
def image_md5_get(host_ip,image_name):
    hostlist = []
    hostlist.append(host_ip)
    image_dir =  '/app/image/' +image_name
    command = 'md5sum ' + image_dir + " |cut -d ' ' -f 1"
    ansible_code, ansible_msg = ansible_run_shell(host_ip, command)
    print 'get local image md5############################'
    print ansible_msg
    if ansible_code == 3:
        message = '连接目标kvm host失败'
        return False,message
    elif ansible_code != 0:
        message = '获取vm md5失败'
        return False, message
    else:
        message = '获取vm md5成功'
        md5 = ansible_msg['np_fact_cache'][host_ip]['shell_out']['stdout']
        return md5,message


# 拷贝待克隆vm到指定目录
def copy_clonefile(host_ip,source_file,dest_file):
    hostlist = []
    hostlist.append(host_ip)
    cp_comm = 'cp '+ source_file + ' ' + dest_file
    ansible_code, ansible_msg = ansible_run_shell(host_ip,cp_comm)
    if ansible_code == 3:
        message = '连接目标kvm host失败'
        return False,message
    elif ansible_code != 0:
        message = '创建克隆目标文件夹失败'
        return False, message
    else:
        message = '拷贝待克隆vm磁盘文件成功'
        return True,message


# 生成克隆源文件的种子文件
def torrnet_clonefile(host_ip, clone_file, tracker_iplist):
    hostlist = []
    hostlist.append(host_ip)
    clone_tarfile = clone_file
    owner_parr = ANSIABLE_REMOTE_USER + '.usr01'
    param1 = ""
    for tracker in tracker_iplist:
        add_param = '-t http://'+ tracker + ':2710/announce'
        param1 =  add_param  + ' ' + param1
    mk_torr_comm ='cd /app/clone;transmission-create ' + param1 + clone_tarfile +';chown -R ' \
                  + owner_parr + ' ' + clone_tarfile +'.torrent'
    ansible_code, ansible_msg = ansible_run_shell(host_ip, mk_torr_comm)
    if ansible_code == 3:
        message = '连接目标kvm host失败'
        return False,message
    elif ansible_code != 0:
        message = '生成种子文件失败'
        return False, message
    else:
        message = '生成种子文件成功'
        return True, message


# 本地将torrent加入队列
def upload_local_torr(torrent_file,host_ip):
    hostlist = []
    hostlist.append(host_ip)
    upload_torr_comm = 'cd /app/clone;transmission-remote -a '+ torrent_file
    ansible_code, ansible_msg = ansible_run_shell(host_ip, upload_torr_comm)
    if ansible_code == 3:
        message = '连接目标kvm host失败'
        return False,message
    elif ansible_code != 0:
        message = '本地上传种子到队列失败'
        return False, message
    else:
        message = '本地上传种子到队列成功'
        return True, message

# python本地起http服务
def python_clone_http(dest_host,dest_dir,http_port):
    hostlist = []
    hostlist.append(dest_host)
    start_http_comm = 'cd ' + dest_dir + ';nohup python -m SimpleHTTPServer ' + str(http_port) + ' >/dev/null 2>&1 &'
    ansible_code, ansible_msg = ansible_run_shell(dest_host, start_http_comm)
    if ansible_code == 3:
        message = '连接目标kvm host失败'
        return False,message
    elif ansible_code != 0:
        message = '本地启动http服务失败'
        return False, message
    else:
        message = '本地启动http服务成功'
        return True, message


#关闭本地http服务
def clone_http_kill(dest_host,http_port):
    hostlist = []
    hostlist.append(dest_host)
    get_http_process = "ps -ef|grep SimpleHTTP|grep -v grep|grep " + http_port +"|awk '{print $2}'"
    kill_http_comm = "kill -9 `%s`" % get_http_process
    ansible_code, ansible_msg = ansible_run_shell(dest_host, kill_http_comm)
    if ansible_code == 3:
        message = '连接目标kvm host失败'
        return False,message
    elif ansible_code != 0:
        message = '本地关闭http服务失败'
        return False, message
    else:
        message = '本地关闭http服务成功'
        return True, message


#下载种子文件
def get_clone_image(host_ip,dest_dir,dest_file,source_ip,http_port,dest_file1):
    print source_ip
    print http_port
    print dest_file
    print dest_dir
    hostlist = []

    hostlist.append(host_ip)
    down_url = "http://%s:%s%s" %(source_ip,http_port,dest_file1)
    print down_url
    get_clone_file_comm = 'cd '+ dest_dir +';rm -f '+ dest_file +';wget ' + down_url +  ' >/dev/null 2>&1 &'
    print get_clone_file_comm
    ansible_code, ansible_msg = ansible_run_shell(host_ip, get_clone_file_comm)
    if ansible_code == 3:
        message = '连接目标kvm host失败'
        return False,message
    elif ansible_code != 0:
        message = '获取克隆种子文件失败'
        return False, message
    else:
        message = '获取克隆种子文件成功'
        return True, message


# wget下载镜像文件
def wget_clone_image(host_ip, source_ip, http_port, image, speed_limit):
    print source_ip
    hostlist = []
    hostlist.append(host_ip)
    image_url = '/' + image
    speed_str = str(float(speed_limit)/8) + 'm'
    down_com = "cd /app/clone;rm -rf %s;wget --limit-rate %s http://%s:%s%s >/dev/null 2>&1 &" \
               % (image, speed_str, source_ip, http_port, image_url)
    print down_com
    ansible_code, ansible_msg = ansible_run_shell(host_ip, down_com)
    if ansible_code == 3:
        message = '连接目标kvm host失败'
        return False,message
    elif ansible_code != 0:
        message = '连接目标kvm host %s 失败' % (host_ip)
        return False, message
    else:
        message = '下发wget获取镜像文件成功'
        return True, message

# 检查是否有wget进程
def check_wget_finish(host_ip, image_disk):
    hostlist = []
    hostlist.append(host_ip)
    wget_check = 'ps -ef|grep wget|grep %s|grep -v grep' % image_disk
    ansible_code, ansible_msg = ansible_run_shell(host_ip, wget_check)
    if ansible_code == 3:
        message = '连接目标kvm host失败'
        return False,message
    elif ansible_msg['np_fact_cache'][host_ip]['shell_out']['stdout'] == "":
        message = '目标host %s wget完成' % host_ip
        return True, message
    else:
        message = '目标host %s wget未完成' % host_ip
        return False, message


# 获取文件md5值
def get_clonefile_md5(host_ip, image_url):
    hostlist = []
    hostlist.append(host_ip)
    wget_check = "cd /app/clone;md5sum %s|awk '{print $1}'" % image_url
    ansible_code, ansible_msg = ansible_run_shell(host_ip, wget_check)
    if ansible_code == 3:
        message = '连接目标KVM HOST %s 失败' % (host_ip)
        return False, message
    elif ansible_code != 0:
        message = '获取%s md5失败' % image_url
        return False, message
    else:
        md5 = ansible_msg['np_fact_cache'][host_ip]['shell_out']['stdout']
        return True, md5

# 目标host开启bt传输
def bt_trans_images(host_ip,torr_file,trans_speed):
    hostlist = []
    hostlist.append(host_ip)
    bt_trans_images_comm = 'transmission-remote -a ' + torr_file + ' -d ' +  trans_speed + ' -u ' + trans_speed
    ansible_code, ansible_msg = ansible_run_shell(host_ip,bt_trans_images_comm)
    if ansible_code == 3:
        message = '连接目标KVM HOST %s 失败' % (host_ip)
        return False, message
    elif ansible_code != 0:
        message = '目标host %s 开启BT传输失败' % host_ip
        return False, message
    else:
        message = '目标host %s 开启BT传输成功' % host_ip
        return True, message


#抓取当前host上BT传输状态
def grep_bt_stat(host_ip,grep_para):
    hostlist = []
    hostlist.append(host_ip)
    grep_comm = 'transmission-remote -l|grep ' + grep_para + "|awk '{print $2}'"
    ansible_code, ansible_msg = ansible_run_shell(host_ip,grep_comm)
    if ansible_code == 3:
        message = '连接目标KVM HOST %s 失败' % (host_ip)
        return False, message
    elif ansible_code != 0:
        message = '获取目标host %s BT传输状态失败' % host_ip
        return False, message

    elif ansible_msg['np_fact_cache'][host_ip]['shell_out']['stdout'] != '100%':
        message = '目标host %s 开启BT传输成功' % host_ip
        return False, message
    else:
        message = '目标host 上bt传输已完成'
        return True,message

#拷贝bt下载文件到/app/image
def copy_torr_file(host_ip,torr_dir,uuid):
    hostlist = []
    hostlist.append(host_ip)
    copy_torr_comm = 'cd ' + torr_dir +';cp * /app/image/'+uuid
    ansible_code, ansible_msg = ansible_run_shell(host_ip,copy_torr_comm)
    if ansible_code == 3:
        message = '连接目标KVM HOST %s 失败' % (host_ip)
        return False, message
    elif ansible_code != 0:
        message = '拷贝bt镜像文件失败'
        return False, message
    else:
        message = '拷贝bt镜像文件成功'
        return True,message

#将克隆后的镜像文件重命名
def rename_clone_image(host_ip,old_im_name,new_im_name,dest_dir):
    hostlist = []
    hostlist.append(host_ip)
    rename_clone_imge_comm = 'cd ' + dest_dir + ';mv /app/clone/'+ old_im_name + ' ' + new_im_name
    ansible_code, ansible_msg = ansible_run_shell(host_ip, rename_clone_imge_comm)
    if ansible_code == 3:
        message = '连接目标KVM HOST %s 失败' % (host_ip)
        return False, message
    elif ansible_code != 0:
        message = '镜像文件重命名失败'
        return False, message
    elif ansible_msg['np_fact_cache'][host_ip]['shell_out'].get('rc',-1) == 1:
        message = '镜像文件重命名失败'
        return False, message
    else:
        message = '镜像文件重命名成功'
        return True,message

# 创建目标文件夹
def create_destdir(dest_host, dest_dir):
    hostlist = []
    hostlist.append(dest_host)
    mk_destdir_comm = 'mkdir -p ' + dest_dir
    ansible_code, ansible_msg = ansible_run_shell(dest_host, mk_destdir_comm)
    if ansible_code == 3:
        message = '连接目标KVM HOST %s 失败' % (dest_host)
        return False, message
    elif ansible_code != 0:
        message = '创建目标文件夹失败'
        return False, message
    else:
        message = '创建目标文件夹成功'
        return True, message



# ansible修改文件权限
def ch_images_mod(dest_host,images):
    ret_param = ''
    for image in images:
        param = 'chmod 644 ' + '/app/clone/' + image + ';'
        ret_param = ret_param + param
    hostlist = []
    hostlist.append(dest_host)
    ansible_comm = ret_param
    ansible_code, ansible_msg = ansible_run_shell(dest_host, ansible_comm)
    if ansible_code == 3:
        message = '连接目标KVM HOST %s 失败' % (dest_host)
        return False, message
    elif ansible_code != 0:
        message = '修改文件权限失败'
        return False, message
    else:
        message = '修改文件权限成功'
        # image_files = ansible_msg['np_fact_cache'][dest_host]['shell_out']['stdout']
        return True, message

# 获取文件夹下镜像文件
def get_dir_image_num(dest_host, dest_dir):
    hostlist = []
    hostlist.append(dest_host)
    get_dir_file_num_comm = 'cd ' + dest_dir +";ls |grep -E 'img|disk'"
    ansible_code, ansible_msg = ansible_run_shell(dest_host, get_dir_file_num_comm)
    if ansible_code == 3:
        message = '连接目标KVM HOST %s 失败' % (dest_host)
        return False, message
    elif ansible_code != 0:
        message = '获取待拷贝镜像文件数量失败'
        return False, message
    else:
        message = '创建目标文件夹成功'
        image_files = ansible_msg['np_fact_cache'][dest_host]['shell_out']['stdout']
        return True, image_files


# 检查HOST上指定端口是否开启
def check_port_is_up(dest_host, http_port):
    hostlist = []
    hostlist.append(dest_host)
    check_port_comm = "netstat -antlp|grep " + http_port
    ansible_code, ansible_msg = ansible_run_shell(dest_host, check_port_comm)
    if ansible_code == 3:
        message = '连接目标KVM HOST %s 失败' % (dest_host)
        return False, message
    elif ansible_code != 0:
        message = '获取HTTP开启状态失败'
        return False, message
    elif ansible_msg['np_fact_cache'][dest_host]['shell_out']['stdout'] == "":
        message = '目标HOST上http服务未开启'
        return False, message
    else:
        message = '目标HOST上http服务已开启'
        return True, message

def ansible_remote_mkdir_and_dns(src_host_ip, dst_host_ip, dst_host_name):
    '''
    热迁移使用
    创建虚拟机存储目录，同时在host文件中添加IP和目标主机名
    :param host: dst_host_ip
    :param dir_name:
    :return:
    '''
    hostlist = []
    if ',' in src_host_ip:
        hostlist = src_host_ip.split(',')
    else:
        hostlist.append(src_host_ip)
    check_dir = "sed -i '/%s/d' /etc/hosts;sed -i '/%s/d' /etc/hosts;echo '%s %s' >>/etc/hosts" % (dst_host_ip, dst_host_name, dst_host_ip, dst_host_name)
    ansible_code, ansible_msg = ansible_run_shell(src_host_ip, check_dir)
    if ansible_code == 3:
        message = '连接目标KVM HOST %s 失败' % (src_host_ip)
        return False, message
    elif ansible_code != 0:
        return False
    else:
        return True

def ansible_migrate_qos_speed(host_ip_s, host_ip_d, migrate_speed,):
    '''
        设置目标主机的迁移速度
    :param host_ip_s:
    :param host_ip_d:
    :param migrate_speed:
    :return:

    '''
    hostlist = []
    hostlist.append(host_ip_s)
    try:
        speed_cmd = 'cd /root;/bin/bash migratespeedQos ' + host_ip_d + ' ' + str(migrate_speed)
        ansible_code, ansible_msg = ansible_run_shell(host_ip_s,speed_cmd)
        if ansible_code == 3:
            message = '连接目标KVM HOST %s 失败' % (host_ip_s)
            return False, message
        elif ansible_code != 0:
            return False
        else:
            return True
    except Exception as e:
        return False


def ansible_migrate_cancel_qos_speed(host_ip_s):
    '''
        取消host迁移速度限制
    :param host_ip:
    :param migrate_speed:
    :return:
    '''
    hostlist = []
    hostlist.append(host_ip_s)
    cancel_cmd = 'cd /root;/bin/bash deletemigratespeedQos'
    ansible_code, ansible_msg = ansible_run_shell(host_ip_s, cancel_cmd)
    if ansible_code == 3:
        message = '连接目标KVM HOST %s 失败' % (host_ip_s)
        return False, message
    elif ansible_code != 0:
        return False
    else:
        return True

def ansible_rm_file(host_ip,rm_file):
    hostlist = []
    hostlist.append(host_ip)
    rm_comm = 'rm -f ' + rm_file
    ansible_code, ansible_msg = ansible_run_shell(host_ip,rm_comm)
    if ansible_code == 3:
        message = '连接目标KVM HOST %s 失败' % (host_ip)
        return False, message
    elif ansible_code != 0:
        return False
    else:
        return True



# 获取对应image的disk清单
def get_image_disk_list(host_ip,image_name):
    command = 'cd /app/image/' + image_name +';ls |grep ' + image_name + '|wc -l'
    hostlist = []
    hostlist.append(host_ip)
    ansible_code, ansible_msg = ansible_run_shell(host_ip, command)
    if ansible_code == 3:
        message = '连接目标KVM HOST %s 失败' % (host_ip)
        return False, message
    elif ansible_code != 0:
        msg = '镜像编辑服务器%s获取镜像文件失败' % host_ip
        return False, msg

    elif ansible_msg['np_fact_cache'][host_ip]['shell_out']['stdout'] == '':
        msg = '镜像编辑服务器 %s 上未检测到磁盘文件，请检查' % host_ip
        return False, msg
    else:
        image_disk_list_num = ansible_msg['np_fact_cache'][host_ip]['shell_out']['stdout']
        image_disk_list =[]
        image_disk_list.append(image_name)
        for m in range(2,int(image_disk_list_num)+1):
            disk_name = image_name + '_disk'+ str(m)
            image_disk_list.append(disk_name)
        msg = '获取镜像磁盘清单成功'
        return True, image_disk_list


# image模板机创建函数
def image_tmp_vm_define(host_ip, dir, vmname, ostype):
    command = '/bin/bash /root/vm_create.sh %s %s %s' %(dir, vmname, ostype)
    hostlist = []
    hostlist.append(host_ip)
    ansible_code, ansible_msg = ansible_run_shell(host_ip, command)
    if ansible_code == 3:
        message = '连接目标KVM HOST %s 失败' % (host_ip)
        return False, message
    elif ansible_code != 0:
        msg = '连接镜像编辑服务器 %s 失败' % host_ip
        return False, msg
    else:
        msg = '创建镜像模板机 %s 成功' % vmname
        return True, msg

# image的磁盘大小
def image_actual_size(host_ip, image_name, disk_name):
    command = "cd /app/image/%s ;qemu-img info %s|grep \'disk size\'|awk '{print $3}'" %(image_name,disk_name)
    hostlist = []
    hostlist.append(host_ip)
    ansible_code, ansible_msg = ansible_run_shell(host_ip, command)
    if ansible_code == 3:
        message = '连接目标KVM HOST %s 失败' % (host_ip)
        return False, message
    elif ansible_code != 0:
        msg = u'连接镜像编辑服务器 %s 失败' % host_ip
        return False, msg

    else:
        msg = ansible_msg['np_fact_cache'][host_ip]['shell_out']['stdout']
        return True, msg

# 单个镜像盘的备份操作
def img_backup(host_ip, image_disk,image_name):
    hostlist = []
    hostlist.append(host_ip)
    dest_dir = '/app/image/' + image_name
    command_rm = 'cd /app/image/;rm -rf %s.bak-*'  % image_disk
    dest_file = image_disk + '.bak-'+get_datatime_one_str()
    command_cp = 'cd %s;cp %s %s;mv %s /app/image/' % (dest_dir, image_disk, dest_file, dest_file)
    command = command_rm + ';' + command_cp
    ansible_code, ansible_msg = ansible_run_shell(host_ip, command)
    if ansible_code == 3:
        message = '连接目标KVM HOST %s 失败' % (host_ip)
        return False, message
    elif ansible_code != 0:
        msg = '备份镜像 %s 失败' % image_disk
        return False, msg
    else:
        msg = '备份镜像 %s 成功' % image_disk
        return True, msg

# 下载镜像文件到imgserver
def download_img(host_ip, image_name, image_disk):
    hostlist = []
    hostlist.append(host_ip)
    edit_server = IMAGE_EDIT_SERVER
    command = 'cd /app/image/%s;rm -rf %s;wget http://%s/%s/%s' %(image_name, image_disk, edit_server, image_name, image_disk)
    ansible_code, ansible_msg = ansible_run_shell(host_ip, command)
    if ansible_code == 3:
        message = '连接目标KVM HOST %s 失败' % (host_ip)
        return False, message
    elif ansible_code != 0:
        msg = '更新镜像文件 %s 失败' % image_disk
        return False, msg
    else:
        msg = '更新镜像文件 %s 成功' % image_disk
        return True, msg

# 获取image的md5值
def get_image_md5(host_ip, image_name, disk_name):
    command = "cd /app/image/%s; md5sum %s|awk '{print $1}'" % (image_name, disk_name)
    hostlist = []
    hostlist.append(host_ip)
    ansible_code, ansible_msg = ansible_run_shell(host_ip, command)
    info_msg = 'publish image:gather image md5 info for image %s disk %s' % (image_name, disk_name)
    if ansible_code == 3:
        message = '连接目标KVM HOST %s 失败' % (host_ip)
        return False, message
    elif ansible_code != 0:
        msg = u'连接镜像编辑服务器 %s 失败,报错信息 %s' % (host_ip, ansible_msg)
        return False, msg
    else:
        msg = ansible_msg['np_fact_cache'][host_ip]['shell_out']['stdout']
        return True, msg

# 单台镜像缓存服务器更新url
def imgcache_update(image_name, image_disk_list, host_ip, image_server_list):
    hostlist = []
    hostlist.append(host_ip)
    command = ''
    for image_server in image_server_list:
        for image_disk in image_disk_list:
            command = command + 'squidclient -l 127.0.0.1 -p 3128 -m PURGE http://%s/%s/%s;' % (image_server, image_name, image_disk)
    ansible_code, ansible_msg = ansible_run_shell(host_ip, command)
    if ansible_code == 3:
        message = '连接目标KVM HOST %s 失败' % (host_ip)
        return False, message
    elif ansible_code != 0:
        msg = u'更新镜像缓存服务器 %s 失败' % host_ip
        return False, msg
    else:
        msg = '缓存服务器%s 更新镜像 %s 的缓存成功' % (host_ip, image_name)
        return True, msg

# 获取image的md5值
def get_image_size_gb(host_ip, image_name, disk_name):
    command = "cd /app/image/%s;qemu-img info %s|grep 'virtual size'|awk '{print $3}'" % (image_name, disk_name)
    hostlist = []
    hostlist.append(host_ip)
    ansible_code, ansible_msg = ansible_run_shell(host_ip, command)
    if ansible_code == 3:
        message = '连接目标KVM HOST %s 失败' % (host_ip)
        return False, message
    elif ansible_code != 0:
        msg = u'连接镜像编辑服务器 %s 失败,报错信息 %s' % (host_ip, ansible_msg)
        return False, msg
    elif ansible_msg['np_fact_cache'][host_ip]['shell_out']['stdout'] == None:
        msg = u'获取镜像md5值%s失败' % (disk_name)
        return False, msg
    else:
        msg = ansible_msg['np_fact_cache'][host_ip]['shell_out']['stdout']
        return True, msg


# 获取镜像文件数量
def get_image_file_num(host_ip, image_name):
    command = "cd /app/image/%s;ls |grep %s|wc -l" % (image_name, image_name)
    hostlist = []
    hostlist.append(host_ip)
    ansible_code, ansible_msg = ansible_run_shell(host_ip, command)
    if ansible_code == 3:
        message = '连接目标KVM HOST %s 失败' % (host_ip)
        return False, message
    elif ansible_code != 0:
        msg = u'连接镜像编辑服务器 %s 失败,报错信息 %s' % (host_ip, ansible_msg)
        return False, msg
    elif ansible_msg['np_fact_cache'][host_ip]['shell_out']['stdout'] == None:
        msg = u'获取镜像文件数量失败'
        return False, msg
    else:
        msg = ansible_msg['np_fact_cache'][host_ip]['shell_out']['stdout']
        return True, msg


# 开机镜像模板机
def start_tem_vm(host_ip, image_name):
    command = "virsh start %s" % image_name
    hostlist = []
    hostlist.append(host_ip)
    ansible_code, ansible_msg = ansible_run_shell(host_ip, command)
    if ansible_code == 3:
        message = '连接目标KVM HOST %s 失败' % (host_ip)
        return False, message
    elif 'failed' in ansible_msg['np_fact_cache'][host_ip]:
        fail_info = ansible_msg
        if 'already' in fail_info:
            msg = 'tem vm %s already start successed' % image_name
            return True, msg
        else:
            msg = u'启动模板 %s 失败' % image_name
            return False, msg
    elif ansible_code != 0:
        msg = u'启动模板 %s 失败,报错信息 %s  ' % (image_name, ansible_msg)
        return False, msg
    else:
        msg = ansible_msg['np_fact_cache'][host_ip]['shell_out']['stdout']
        return True, msg

# 下载镜像文件到editserver
def editserver_get_img(img_server, source_img_name, new_img_name, source_img_disk):
    host_ip = IMAGE_EDIT_SERVER
    hostlist = []
    hostlist.append(host_ip)
    new_disk_name_list = source_img_disk.split("_disk")
    if len(new_disk_name_list) == 1:
        new_disk_name = new_img_name
    else:
        new_disk_name = new_img_name + "_disk" + new_disk_name_list[1]
    # cd到新镜像文件夹下，从镜像服务器下载源镜像文件并重命名成新镜像的名称
    command = 'cd /app/image/%s;wget http://%s/%s/%s;mv %s %s' %(new_img_name, img_server, source_img_name,
                                                                 source_img_disk, source_img_disk, new_disk_name)
    ansible_code, ansible_msg = ansible_run_shell(host_ip, command)
    if ansible_code == 3:
        message = '连接目标KVM HOST %s 失败' % (host_ip)
        return False, message

    elif ansible_code != 0:
        msg = '下载镜像文件 %s 失败' % source_img_disk
        return False, msg
    elif 'failed' in ansible_msg['np_fact_cache'][host_ip]:
        msg = '下载镜像文件 %s 失败' % source_img_disk
        return False, msg
    else:
        msg = '下载更新镜像文件 %s 成功' % source_img_disk
        return True, msg


# 目标文件MD5获取
def get_file_md5(host_ip, dest_file):
    host_list = []
    host_list.append(host_ip)
    command = "md5sum %s |awk '{print $1}'" % dest_file
    msg = "now start to get md5 for %s" % dest_file
    ansible_code, ansible_msg = ansible_run_shell(host_ip, command)
    if ansible_code == 3:
        message = '连接目标KVM HOST %s 失败' % (host_ip)
        return False, message

    elif ansible_code != 0:
        msg = '获取目标文件 %s md5失败 ' % dest_file
        return False, msg
    elif 'failed' in ansible_msg['np_fact_cache'][host_ip]:
        msg = '获取目标文件 %s md5失败 ' % dest_file
        return False, msg
    else:
        msg = '获取目标文件 %s md5成功' % dest_file
        data = ansible_msg['np_fact_cache'][host_ip]['shell_out']['stdout']
        return True, data


# 获取目标文件大小
def get_file_size(host_ip, dest_file, src_dir):
    host_list = []
    host_list.append(host_ip)
    command = "cd %s;ls -al|grep %s|awk 'NR==1{print}'|awk '{print $5}'" % (src_dir, dest_file)
    msg = "now start to get file %s size " % dest_file
    ansible_code, ansible_msg = ansible_run_shell(host_ip, command)
    if ansible_code == 3:
        message = '连接目标KVM HOST %s 失败' % (host_ip)
        return False, message

    elif ansible_code != 0:
        msg = '获取目标文件 %s 大小失败 ' % dest_file
        return False, msg
    elif 'failed' in ansible_msg['np_fact_cache'][host_ip]:
        msg = '获取目标文件 %s 大小失败 ' % dest_file
        return False, msg
    else:
        msg = '获取目标文件 %s 大小成功' % dest_file
        data = ansible_msg['np_fact_cache'][host_ip]['shell_out']['stdout']
        return True, data

# 下发vm快照整合脚本
def exec_commit_shell(host_ip, task_id):
    host_list = []
    host_list.append(host_ip)
    commit_shell_name = 'snapshot_commit_' + str(task_id) + '.sh'
    command = '/bin/bash /root/' + commit_shell_name
    ansible_code, ansible_msg = ansible_run_shell(host_ip, command)
    if ansible_code == 3:
        message = '连接目标KVM HOST %s 失败' % (host_ip)
        return False, message

    elif ansible_code != 0:
        msg = '%s快照文件整合失败 ' % task_id
        return False, msg
    elif 'failed' in ansible_msg['np_fact_cache'][host_ip]:
        msg = '%s快照文件整合失败 ' % task_id
        return False, msg
    else:
        msg = '%s快照文件整合成功' % task_id
        return True, msg
