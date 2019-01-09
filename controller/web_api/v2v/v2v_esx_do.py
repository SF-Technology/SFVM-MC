# coding=utf8
'''
    v2v_esx
'''
# __author__ = 'anke'


import env
from lib.shell.ansibleCmdV2 import ansible_run_shell

env.init_env()
from model.const_define import ActionStatus,esx_v2vActions,VMCreateSource
from service.v2v_task import v2v_task_service as v2v_op
from service.s_instance_action import instance_action as in_a_s
from service.s_instance import instance_service as ins_s
from service.s_flavor import flavor_service
from config.default import ANSIABLE_REMOTE_USER,OPENSTACK_DEV_USER
from service.s_ip import ip_service as ip_s
import logging
import time
import threading
from lib.vrtManager import instanceManager
from config.default import KVMHOST_LOGIN_PASS,KVMHOST_SU_PASS
from helper.encrypt_helper import decrypt
from libvirt import libvirtError

def esx_do_task():
    # 获取当前在进行的任务清单
    list_working = v2v_op.get_v2v_todo()

    if not list_working:
        time.sleep(60)
        return 0

    for i in list_working:
        # 获取当前任务信息
        request_id = i['request_id']
        vm_ip = i['vm_ip']
        vm_name = i['vm_name']
        vm_vlan = i['vmvlan']
        flavor_id = i['flavor_id']
        cloud_area = i['cloud_area']
        vm_mac = i['vm_mac']
        vm_uuid = i['vm_uuid']
        step_done = i['step_done']
        dest_host = i['dest_host']
        status = i['status']
        ostype = i['vm_ostype']
        dest_dir = i['dest_dir']
        on_task = i['on_task']
        source = i['source']
        esx_ip = i['esx_ip']
        esx_passwd = i['esx_passwd']
        vmware_vm = i['vmware_vm']
        if status == 0 and on_task == '0' and source == VMCreateSource.ESX:

            # 获取flavor信息
            flavor_info = flavor_service.FlavorService().get_flavor_info(flavor_id)
            vmcpu = str(flavor_info['vcpu'])
            vmmem = flavor_info['memory_mb']


            # 创建目标文件夹
            esx_v2v_sta1 = v2v_op.get_v2v_running_by_reqid(request_id)
            if esx_v2v_sta1 == True:
                step_done1 = v2v_op.get_v2v_step(request_id)
                if step_done1 == esx_v2vActions.BEGIN:
                    threadlock = threading.Lock()
                    threadlock.acquire()
                    v2v_op.updata_v2v_ontask(request_id, '1')
                    threadlock.release()
                    # 在目标服务器上创建文件夹
                    createdir(dest_host, request_id, "command", dest_dir)

            # 创建存储池
            esx_v2v_sta2 = v2v_op.get_v2v_running_by_reqid(request_id)
            if esx_v2v_sta2 == True:
                step_done2 = v2v_op.get_v2v_step(request_id)
                if step_done2 == esx_v2vActions.CREATE_DEST_DIR:
                    threadlock = threading.Lock()
                    threadlock.acquire()
                    v2v_op.updata_v2v_ontask(request_id, '1')
                    threadlock.release()
                    # 创建存储池
                    host_ip = dest_host
                    dir = v2v_op.get_v2v_destdir(request_id)
                    dir_uuid = dir.replace('/app/image/', '')
                    _create_storage_pool(host_ip, dir_uuid, request_id)

            # 拷贝vm文件至目标host
            esx_v2v_sta3 = v2v_op.get_v2v_running_by_reqid(request_id)
            if esx_v2v_sta3 == True:
                # 获取任务
                step_done3 = v2v_op.get_v2v_step(request_id)
                if step_done3 == esx_v2vActions.CREATE_STOR_POOL:
                    threadlock = threading.Lock()
                    threadlock.acquire()
                    v2v_op.updata_v2v_ontask(request_id, '1')
                    threadlock.release()
                    # 将vm磁盘文件拷贝至kvmhost本地
                    virt_v2v_copy_to_local(dest_dir,dest_host,esx_ip,esx_passwd,vmware_vm,request_id)

            # v2v拷贝后的vm文件
            esx_v2v_sta4 = v2v_op.get_v2v_running_by_reqid(request_id)
            if esx_v2v_sta4 == True:
                step_done4 = v2v_op.get_v2v_step(request_id)
                if step_done4 == esx_v2vActions.COPY_FILE_TO_LOCAL:
                    threadlock = threading.Lock()
                    threadlock.acquire()
                    v2v_op.updata_v2v_ontask(request_id, '1')
                    threadlock.release()
                    # 将获取到的vm文件v2v
                    virt_v2v(dest_dir, dest_host, request_id, vmware_vm)

            # 删除v2v过程中的临时文件
            esx_v2v_sta5 = v2v_op.get_v2v_running_by_reqid(request_id)
            if esx_v2v_sta5 == True:
                step_done5 = v2v_op.get_v2v_step(request_id)
                if step_done5 == esx_v2vActions.VIRT_V2V_FILES:
                    v2v_op.updata_v2v_ontask(request_id, '1')
                    # 删除v2v过程中的临时文件
                    rmrawfile(dest_host, vmware_vm, request_id)

            # vm系统盘标准化
            esx_v2v_sta6 = v2v_op.get_v2v_running_by_reqid(request_id)
            if esx_v2v_sta6 == True:
                step_done6 = v2v_op.get_v2v_step(request_id)
                if step_done6 == esx_v2vActions.DELETE_TMP_FILE:
                    v2v_op.updata_v2v_ontask(request_id, '1')
                    # vm系统盘标准化
                    ch_sys_disk_name(dest_dir, dest_host, vmware_vm, vm_name, request_id)

            # vm数据盘标准化
            esx_v2v_sta7 = v2v_op.get_v2v_running_by_reqid(request_id)
            if esx_v2v_sta7 == True:
                step_done7 = v2v_op.get_v2v_step(request_id)
                if step_done7 == esx_v2vActions.VM_SYS_DISK_STD:
                    v2v_op.updata_v2v_ontask(request_id, '1')
                    vm_data_disk_std(dest_dir, dest_host, vm_name, request_id,vmware_vm)

            # vm注册
            esx_v2v_sta8 = v2v_op.get_v2v_running_by_reqid(request_id)
            if esx_v2v_sta8 == True:
                step_done8 = v2v_op.get_v2v_step(request_id)
                if step_done8 == esx_v2vActions.VM_DATA_DISK_STD:
                    v2v_op.updata_v2v_ontask(request_id, '1')
                    vmlistdata = v2v_op.v2vTaskService().get_v2v_task_by_requestid(request_id)['volumelist']
                    volumes_d = []
                    vmsysdisk = dest_dir + '/' + vm_name + '.img'
                    volumes_d.append(vmsysdisk)
                    if int(vmlistdata) > 0:
                        tag =1
                        while tag <= int(vmlistdata):
                            vmdatadisk = dest_dir + '/' + vm_name + '_disk' + str(tag)
                            tag =tag + 1
                            volumes_d.append(vmdatadisk)
                    print volumes_d
                    vm_define(request_id,ostype , dest_host, vm_name, vmmem,
                              vmcpu, vm_uuid, volumes_d, vm_vlan, vm_mac)

            # vm开机1
            esx_v2v_sta9 = v2v_op.get_v2v_running_by_reqid(request_id)
            if esx_v2v_sta9 == True:
                step_done9 = v2v_op.get_v2v_step(request_id)
                if step_done9 == esx_v2vActions.VM_DEFINE1:
                    v2v_op.updata_v2v_ontask(request_id, '1')
                    vm_start1(dest_host, vm_name, request_id, 'shell', ostype)

            # 添加临时盘
            esx_v2v_sta10 = v2v_op.get_v2v_running_by_reqid(request_id)
            if esx_v2v_sta10 == True:
                step_done10 = v2v_op.get_v2v_step(request_id)
                if step_done10 == esx_v2vActions.VM_START1:
                    v2v_op.updata_v2v_ontask(request_id, '1')
                    v2v_esx_disk_attach_static(vm_name, dest_host, request_id)



            #win vm磁盘格式修改
            esx_v2v_sta12 = v2v_op.get_v2v_running_by_reqid(request_id)
            if esx_v2v_sta12 == True:
                step_done12 = v2v_op.get_v2v_step(request_id)
                if step_done12 == esx_v2vActions.ATTACH_DISK:
                    v2v_op.updata_v2v_ontask(request_id, '1')
                    win_disk_ch(vm_name, dest_host, request_id)

            #vm 开机2
            esx_v2v_sta13 = v2v_op.get_v2v_running_by_reqid(request_id)
            if esx_v2v_sta13 == True:
                step_done13 = v2v_op.get_v2v_step(request_id)
                if step_done13 == esx_v2vActions.WINDOWS_DISK_CH:
                    v2v_op.updata_v2v_ontask(request_id, '1')
                    vm_start2(dest_host, vm_name, request_id, 'shell',vm_uuid)

            # win vm 标准化
            esx_v2v_sta11 = v2v_op.get_v2v_running_by_reqid(request_id)
            if esx_v2v_sta11 == True:
                step_done11 = v2v_op.get_v2v_step(request_id)
                if step_done11 == esx_v2vActions.VM_START2:
                    v2v_op.updata_v2v_ontask(request_id, '1')
                    win_vm_std(request_id)


#在目标kvm host上创建uuid文件夹
def createdir(kvmhost,request_id,modulename,dir):

    command = 'mkdir -p '+dir
    remote_user = ANSIABLE_REMOTE_USER
    remote_pass = decrypt(KVMHOST_LOGIN_PASS)
    become_user = OPENSTACK_DEV_USER
    become_pass = decrypt(KVMHOST_SU_PASS)
    dir_result = ansible_run_shell(kvmhost,command)
    if 'contacted' not in dir_result:
        message = '创建vm目录失败'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.CREATE_DEST_DIR, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    elif dir_result['contacted'] == {}:
        message = '创建vm目录失败'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.CREATE_DEST_DIR, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    elif 'failed' in dir_result['contacted'][kvmhost]:
        message = '创建vm目录失败'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.CREATE_DEST_DIR, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    else:
        data = dir
        message = '创建vm目录成功'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        in_a_s.update_instance_actions(request_id, esx_v2vActions.CREATE_DEST_DIR, ActionStatus.SUCCSESS,
                                       message)
        v2v_op.update_v2v_step(request_id,esx_v2vActions.CREATE_DEST_DIR)

        v2v_op.updata_v2v_ontask(request_id, '0')
        v2v_op.update_v2v_destdir(request_id,data)
        threadlock.release()

#在目标kvm host上创建存储池
def _create_storage_pool(host_ip, uuid, request_id):
    '''
        创建存储池
    :param host_ip:
    :param uuid:
    :return:
    '''
    connect_storages = instanceManager.libvirt_get_connect(host_ip, conn_type='storages')
    pool_status, pool_name = instanceManager.libvirt_create_storage_pool(connect_storages, uuid)
    if pool_status:
        logging.info('create storage pool successful')
        message = '创建存储池成功'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.CREATE_STOR_POOL, ActionStatus.SUCCSESS,
                                       message)
        v2v_op.update_v2v_step(request_id, esx_v2vActions.CREATE_STOR_POOL)
        threadlock.release()
    else:
        msg = "创建存储池失败"
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, msg)
        v2v_op.updata_v2v_ontask(request_id, '0')
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        in_a_s.update_instance_actions(request_id, esx_v2vActions.CREATE_STOR_POOL, ActionStatus.FAILD,
                                       msg)
        threadlock.release()

#将待转化vm文件拷贝至本地
def virt_v2v_copy_to_local(dest_dir,kvmhost,esx_ip,esx_passwd,vmware_vm,request_id):
    echopass_command = 'mkdir -p /tmp/'+ esx_ip +';echo ' + esx_passwd + ' >> /tmp/'+ esx_ip + '/passwd'
    remote_user = ANSIABLE_REMOTE_USER
    remote_pass = decrypt(KVMHOST_LOGIN_PASS)
    become_user = OPENSTACK_DEV_USER
    become_pass = decrypt(KVMHOST_SU_PASS)
    echopass = ansible_run_shell(kvmhost,echopass_command)
    if 'contacted' not in echopass:
        message = '无法连接kvmhost'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.COPY_FILE_TO_LOCAL, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    elif echopass['contacted'] == {}:
        message = '无法连接kvmhost'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.COPY_FILE_TO_LOCAL, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    elif "error" in echopass['contacted'][kvmhost]['stderr']:
        message = '记录esxi密码失败'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.COPY_FILE_TO_LOCAL, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    else:
        rmfilefirst = 'rm -f /app/tmp/' + vmware_vm + '/' + vmware_vm +'*'
        rmfile_first = ansible_run_shell(kvmhost,rmfilefirst)
        if rmfile_first['contacted'] == {} or "error" in rmfile_first['contacted'][kvmhost]['stderr']:
            message = "清除临时文件失败"
            threadlock = threading.Lock()
            threadlock.acquire()
            v2v_op.updata_v2v_message(request_id, message)
            v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
            v2v_op.updata_v2v_ontask(request_id, '0')
            in_a_s.update_instance_actions(request_id, esx_v2vActions.COPY_FILE_TO_LOCAL, ActionStatus.FAILD,
                                           message)
            threadlock.release()
        else:
            copy_to_local_command = 'mkdir -p /app/tmp/'+ vmware_vm +'/;export TMPDIR=/app/tmp;cd /app/tmp/'+ vmware_vm +'/;virt-v2v-copy-to-local -ic esx://root@' \
                                    + esx_ip + '?no_verify=1 ' + vmware_vm  + ' --password-file ' + '/tmp/' + esx_ip + '/passwd'
            copy_local = ansible_run_shell(kvmhost,copy_to_local_command)
            if copy_local['contacted'] == {}:
                message = '无法连接kvmhost'
                threadlock = threading.Lock()
                threadlock.acquire()
                v2v_op.updata_v2v_message(request_id, message)
                v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
                v2v_op.updata_v2v_ontask(request_id, '0')
                in_a_s.update_instance_actions(request_id, esx_v2vActions.COPY_FILE_TO_LOCAL, ActionStatus.FAILD,
                                               message)
                threadlock.release()
            elif 'error' in copy_local['contacted'][kvmhost]['stderr']:
                message = '拷贝vm文件到目标host失败'
                threadlock = threading.Lock()
                threadlock.acquire()
                v2v_op.updata_v2v_message(request_id, message)
                v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
                v2v_op.updata_v2v_ontask(request_id, '0')
                in_a_s.update_instance_actions(request_id, esx_v2vActions.COPY_FILE_TO_LOCAL, ActionStatus.FAILD,
                                               message)
                threadlock.release()
            else:
                rm_esxpass_com = "rm -f /tmp/" + esx_ip +'/passwd;rmdir /tmp/'+ esx_ip
                rmesxpass_com =  ansible_run_shell(kvmhost,rm_esxpass_com)
                if rmesxpass_com['contacted'] == {} or 'error' in rmesxpass_com['contacted'][kvmhost]['stderr']:
                    message = 'vm文件拷贝成功,删除esxi密码文件失败'
                else:
                    message = 'vm文件拷贝成功,删除esxi密码文件成功'
                threadlock = threading.Lock()
                threadlock.acquire()
                v2v_op.updata_v2v_message(request_id, message)
                in_a_s.update_instance_actions(request_id, esx_v2vActions.COPY_FILE_TO_LOCAL, ActionStatus.SUCCSESS,
                                               message)
                v2v_op.update_v2v_step(request_id, esx_v2vActions.COPY_FILE_TO_LOCAL)
                v2v_op.updata_v2v_ontask(request_id, '0')
                threadlock.release()


#v2v拷贝后的vm文件
def virt_v2v(dest_dir,kvmhost,request_id,vmware_vm):
    virtv2v_command = 'cd '+ dest_dir +';virt-v2v -i libvirtxml /app/tmp/'+\
                      vmware_vm + '/'+vmware_vm+'.xml -o local -os ' + dest_dir +' -of qcow2 --network bond0'
    remote_user = ANSIABLE_REMOTE_USER
    remote_pass = decrypt(KVMHOST_LOGIN_PASS)
    become_user = OPENSTACK_DEV_USER
    become_pass = decrypt(KVMHOST_SU_PASS)
    virtv2v = ansible_run_shell(kvmhost,virtv2v_command)
    if 'contacted' not in virtv2v:
        message = '无法连接kvmhost'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.VIRT_V2V_FILES, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    elif virtv2v['contacted'] == {}:
        message = '无法连接kvmhost'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.VIRT_V2V_FILES, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    elif 'error' in virtv2v['contacted'][kvmhost]['stderr']:
        message = '转化vm文件失败'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.VIRT_V2V_FILES, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    else:
        message = '转化vm文件成功'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        in_a_s.update_instance_actions(request_id, esx_v2vActions.VIRT_V2V_FILES, ActionStatus.SUCCSESS,
                                       message)
        v2v_op.update_v2v_step(request_id, esx_v2vActions.VIRT_V2V_FILES)
        v2v_op.updata_v2v_ontask(request_id, '0')
        threadlock.release()


#删除v2v产生的临时raw文件
def rmrawfile(kvmhost,vmware_vm,request_id):
    remote_user = ANSIABLE_REMOTE_USER
    remote_pass = decrypt(KVMHOST_LOGIN_PASS)
    become_user = OPENSTACK_DEV_USER
    become_pass = decrypt(KVMHOST_SU_PASS)
    rm_raw_file = 'cd /app/tmp/' + vmware_vm + '/;rm -f ' + vmware_vm + '*;rmdir /app/tmp/' + vmware_vm
    rmrawfile = ansible_run_shell(kvmhost, rm_raw_file)
    if 'contacted' not in rmrawfile:
        message = '无法连接kvmhost'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.DELETE_TMP_FILE, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    elif rmrawfile['contacted'] == {}:
        message = '无法连接kvmhost'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.DELETE_TMP_FILE, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    elif 'error' in rmrawfile['contacted'][kvmhost]['stderr']:
        message = '删除转化临时文件失败'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.DELETE_TMP_FILE, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    else:
        message = '删除转化临时文件完成'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        in_a_s.update_instance_actions(request_id, esx_v2vActions.DELETE_TMP_FILE, ActionStatus.SUCCSESS,
                                       message)
        v2v_op.update_v2v_step(request_id, esx_v2vActions.DELETE_TMP_FILE)
        v2v_op.updata_v2v_ontask(request_id, '0')
        threadlock.release()


#标准化v2v后的vm系统盘文件
def ch_sys_disk_name(dest_dir,kvmhost,vmware_vm,vm_name,request_id):
    remote_user = ANSIABLE_REMOTE_USER
    remote_pass = decrypt(KVMHOST_LOGIN_PASS)
    become_user = OPENSTACK_DEV_USER
    become_pass = decrypt(KVMHOST_SU_PASS)
    change_sysdisk_name = 'cd '+dest_dir + ';mv '+ vmware_vm +'-sda '+ vm_name + '.img'
    chsysdiskname = ansible_run_shell(kvmhost, change_sysdisk_name)
    if 'contacted' not in chsysdiskname:
        message = '无法连接kvmhost'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.VM_SYS_DISK_STD, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    elif chsysdiskname['contacted'] == {}:
        message = '无法连接kvmhost'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.VM_SYS_DISK_STD, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    elif 'error' in chsysdiskname['contacted'][kvmhost]['stderr']:
        message = '标准化vm系统盘文件失败'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.VM_SYS_DISK_STD, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    else:
        message = '标准化vm系统盘文件成功'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        in_a_s.update_instance_actions(request_id, esx_v2vActions.VM_SYS_DISK_STD, ActionStatus.SUCCSESS,
                                       message)
        v2v_op.update_v2v_step(request_id, esx_v2vActions.VM_SYS_DISK_STD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        threadlock.release()


#获取vm数据盘文件数量
def get_vm_data_disk(dest_dir,kvmhost):
    remote_user = ANSIABLE_REMOTE_USER
    remote_pass = decrypt(KVMHOST_LOGIN_PASS)
    become_user = OPENSTACK_DEV_USER
    become_pass = decrypt(KVMHOST_SU_PASS)
    get_vm_data_list = 'cd '+ dest_dir + ";ls |grep -e '-sd'|grep -v .img|grep -v .xml|wc -l"
    getvmdatadisk = ansible_run_shell(kvmhost,get_vm_data_list)
    if 'contacted' not in getvmdatadisk:
        message = '连接目标host失败'
        logging.info(message)
        return False, message
    elif getvmdatadisk['contacted'] == {}:
        message = '连接目标host失败'
        logging.info(message)
        return False,message
    elif 'failed' in getvmdatadisk['contacted'][kvmhost]:
        message = '获取vm数据盘清单失败'
        logging.info(message)
        return False, message
    elif getvmdatadisk['contacted'][kvmhost]['stderr']:
        message = '获取vm数据盘清单失败'
        logging.info(message)
        return False, message
    else:
        message= "获取vm磁盘文件清单成功"
        logging.info(message)
        return True, getvmdatadisk['contacted'][kvmhost]['stdout']


#标准化vm数据盘文件名称
def vm_data_disk_std(dest_dir,kvmhost,vm_name,request_id,vmware_vm):
    datadisk_tag,datadisk_res = get_vm_data_disk(dest_dir,kvmhost)
    if not datadisk_tag:
        fail_msg = datadisk_res
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, fail_msg)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.VM_DATA_DISK_STD, ActionStatus.FAILD,
                                       fail_msg)
        threadlock.release()
    else:
        if int(datadisk_res) == 0:
            message = "该vm无数据盘"
            vmlistdata = '0'
            v2v_op.up_esxv2v_vlist(request_id, vmlistdata)
            rm_vmfolder_res, rm_vmfolder_msg = del_vm_folder_file(dest_dir, kvmhost, vmware_vm)
            if not rm_vmfolder_res:
                message = "重命名vm数据盘成功,临时文件清理失败"
            else:
                message = "重命名vm数据盘成功"
            threadlock = threading.Lock()
            threadlock.acquire()
            v2v_op.updata_v2v_message(request_id, message)
            in_a_s.update_instance_actions(request_id, esx_v2vActions.VM_DATA_DISK_STD, ActionStatus.SUCCSESS,
                                           message)
            v2v_op.update_v2v_step(request_id, esx_v2vActions.VM_DATA_DISK_STD)
            v2v_op.updata_v2v_ontask(request_id, '0')
            threadlock.release()

        else:
            total = 0
            datanum = int(datadisk_res)
            tag= 1
            volumetag = ['tag','-sdb','-sdc','-sdd','-sde','-sdf','-sdg','-sdh','-sdi','-sdj']
            while tag <= datanum:
                datadisk = vmware_vm + volumetag[tag]
                res,res_msg = vm_data_disk_rename(datadisk,dest_dir,tag,vm_name,kvmhost)
                tag =tag + 1
                total = total + res
            if total > 0:
                message = "重命名vm数据盘失败"
                threadlock = threading.Lock()
                threadlock.acquire()
                v2v_op.updata_v2v_message(request_id, message)
                v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
                v2v_op.updata_v2v_ontask(request_id, '0')
                in_a_s.update_instance_actions(request_id, esx_v2vActions.VM_DATA_DISK_STD, ActionStatus.FAILD,
                                               message)
                threadlock.release()
            else:
                v2v_op.up_esxv2v_vlist(request_id, str(datanum))
                rm_vmfolder_res,rm_vmfolder_msg = del_vm_folder_file(dest_dir,kvmhost,vmware_vm)
                if not rm_vmfolder_res:
                    message = "重命名vm数据盘成功,临时文件清理失败"
                else:
                    message = "重命名vm数据盘成功"
                threadlock = threading.Lock()
                threadlock.acquire()
                v2v_op.updata_v2v_message(request_id, message)
                in_a_s.update_instance_actions(request_id, esx_v2vActions.VM_DATA_DISK_STD, ActionStatus.SUCCSESS,
                                               message)
                v2v_op.update_v2v_step(request_id, esx_v2vActions.VM_DATA_DISK_STD)
                v2v_op.updata_v2v_ontask(request_id, '0')
                threadlock.release()


#重命名vm数据盘具体函数
def vm_data_disk_rename(datadisk,dest_dir,tag,vm_name,kvmhost):
    remote_user = ANSIABLE_REMOTE_USER
    remote_pass = decrypt(KVMHOST_LOGIN_PASS)
    become_user = OPENSTACK_DEV_USER
    become_pass = decrypt(KVMHOST_SU_PASS)
    mv_command = 'cd '+ dest_dir +';cp -f '+datadisk +' '+ vm_name + '_disk' + str(tag)
    mvcommand = ansible_run_shell(kvmhost, mv_command)
    if 'contacted' not in mvcommand:
        message = '连接目标host失败'
        logging.info(message)
        return 1, message
    elif mvcommand['contacted'] == {}:
        message = '连接目标host失败'
        logging.info(message)
        return 1,message
    elif 'failed' in mvcommand['contacted'][kvmhost]:
        message = '重命名vm数据盘失败'
        logging.info(message)
        return 1, message
    elif mvcommand['contacted'][kvmhost]['stderr']:
        message = '重命名vm数据盘失败'
        logging.info(message)
        return 1, message
    else:
        message = '重命名vm数据盘成功'
        logging.info(message)
        datadisk = vm_name + '_disk'+str(tag)
        return 0,datadisk


#删除vm目录下无效文件
def del_vm_folder_file(dest_dir,kvmhost,vmware_vm):
    remote_user = ANSIABLE_REMOTE_USER
    remote_pass = decrypt(KVMHOST_LOGIN_PASS)
    become_user = OPENSTACK_DEV_USER
    become_pass = decrypt(KVMHOST_SU_PASS)
    del_vm_com = 'cd '+ dest_dir +';rm -f '+ vmware_vm + '-sd*;rm -f ' + vmware_vm + '.xml'
    delvmfolderfile = ansible_run_shell(kvmhost, del_vm_com)
    if 'contacted' not in delvmfolderfile:
        message = '连接目标host失败'
        logging.info(message)
        return False, message
    elif delvmfolderfile['contacted'] == {}:
        message = '连接目标host失败'
        logging.info(message)
        return False,message
    elif 'failed' in delvmfolderfile['contacted'][kvmhost]:
        message = '删除'
        logging.info(message)
        return False, message
    elif delvmfolderfile['contacted'][kvmhost]['stderr']:
        message = '重命名vm数据盘失败'
        logging.info(message)
        return False, message
    else:
        message = '重命名vm数据盘成功'
        logging.info(message)
        return True,message

#vm注册1
def vm_define(request_id,vm_ostype,kvmhost, hostname, memory_mb,
                                vcpu, uuid, volumes_d, vlan, mac):
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
    connect_create = instanceManager.libvirt_get_connect(kvmhost)
    if not connect_create:
        message = '连接kvmhost libvirt失败'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.VM_DEFINE1, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    else:
        vm_vlan = 'br_bond0.' + vlan
        connect_create.refresh_storage_pool_by_name(uuid)
        succeed_create_xml = False
        retry_create_xml = 0
        while retry_create_xml < 3 and not succeed_create_xml:
            try:
                if vm_ostype == "Linux":
                    instance_xml = connect_create.v2v_esx_xml(hostname, memory_mb, vcpu, False,
                                                                                  uuid, volumes_d, 'default', vm_vlan,
                                                                                  True, mac)
                else:
                    instance_xml = connect_create.v2v_esx_xml(hostname, memory_mb, vcpu, False,
                                                                                  uuid, volumes_d, 'default', vm_vlan,
                                                                                  False,
                                                                                  mac)

                succeed_create_xml = True
            except libvirtError as err:
                logging.error("create host connect failed ,name: %s ;because %s" % (hostname, err))
                retry_create_xml += 1
                time.sleep(5)

        if retry_create_xml == 3:
            message = "vm注册失败"
            threadlock = threading.Lock()
            threadlock.acquire()
            v2v_op.updata_v2v_message(request_id, message)
            v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
            v2v_op.updata_v2v_ontask(request_id, '0')
            in_a_s.update_instance_actions(request_id, esx_v2vActions.VM_DEFINE1, ActionStatus.FAILD,
                                           message)
            threadlock.release()
            return False, err
        else:
            message = 'vm注册成功'
            threadlock = threading.Lock()
            threadlock.acquire()
            v2v_op.updata_v2v_message(request_id, message)
            in_a_s.update_instance_actions(request_id, esx_v2vActions.VM_DEFINE1, ActionStatus.SUCCSESS,
                                           message)
            v2v_op.update_v2v_step(request_id, esx_v2vActions.VM_DEFINE1)
            v2v_op.updata_v2v_ontask(request_id, '0')
            threadlock.release()
            return True, instance_xml

#vm开机1
def vm_start1(kvmhost,vmname,request_id,modulename,vm_ostype):
    command = 'virsh start '+ vmname
    remote_user = ANSIABLE_REMOTE_USER
    remote_pass = decrypt(KVMHOST_LOGIN_PASS)
    become_user = OPENSTACK_DEV_USER
    become_pass = decrypt(KVMHOST_SU_PASS)
    vmstart = ansible_run_shell(kvmhost, command)
    if 'contacted' not in vmstart:
        message = 'vm启动失败'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.VM_START1, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    elif vmstart['contacted'] == {}:
        message = 'vm启动失败'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.VM_START1, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    elif 'failed' in vmstart['contacted'][kvmhost]:
        message = 'vm启动失败'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.VM_START1, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    elif vmstart['contacted'][kvmhost]['stdout'] == '':
        message = 'vm启动失败'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.VM_START1, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    else:
        message = 'vm启动成功'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        in_a_s.update_instance_actions(request_id, esx_v2vActions.VM_START1, ActionStatus.SUCCSESS,
                                       message)
        v2v_op.updata_v2v_ontask(request_id, '0')
        v2v_op.update_v2v_step(request_id, esx_v2vActions.VM_START1)
        if vm_ostype == "Linux":
            vm_uuid = v2v_op.v2vTaskService().get_v2v_task_by_requestid(request_id)['vm_uuid']
            where_data = {
                'uuid': vm_uuid
            }
            update_data = {
                'status': '3'
            }
            ins_s.InstanceService().update_instance_info(update_data, where_data)
            v2v_op.update_v2v_actions(request_id, 1)
        threadlock.release()


#vm在线添加磁盘
def v2v_esx_disk_attach_static(vm_name,kvmhost,request_id):
    create_disk = 'cd /tmp;rm -f diskimg;qemu-img create -f qcow2 diskimg 20G'
    remote_user = ANSIABLE_REMOTE_USER
    remote_pass = decrypt(KVMHOST_LOGIN_PASS)
    become_user = OPENSTACK_DEV_USER
    become_pass = decrypt(KVMHOST_SU_PASS)
    createdisk = ansible_run_shell(kvmhost, create_disk)
    if 'contacted' not in createdisk:
        message = '连接目标kvmhost失败'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.ATTACH_DISK, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    elif createdisk['contacted'] == {}:
        message = '连接目标kvmhost失败'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.ATTACH_DISK, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    elif 'failed' in createdisk['contacted'][kvmhost]:
        message = '创建临时磁盘失败'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.ATTACH_DISK, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    else:
        time.sleep(200)
        xml = """
                    <disk type='file' device='disk'>
                        <driver name='qemu' type='qcow2'/>
                        <source file='/tmp/diskimg'/>
                        <target dev='vdi' bus='virtio'/>
                    </disk>"""
        att_device =  instanceManager.v2v_esx_attach_device(kvmhost,vm_name,xml)
        if not att_device:
            message = '添加临时磁盘失败'
            threadlock = threading.Lock()
            threadlock.acquire()
            v2v_op.updata_v2v_message(request_id, message)
            v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
            v2v_op.updata_v2v_ontask(request_id, '0')
            in_a_s.update_instance_actions(request_id, esx_v2vActions.ATTACH_DISK, ActionStatus.FAILD,
                                           message)
            threadlock.release()
        else:
            message = '添加临时磁盘成功'
            time.sleep(15)
            threadlock = threading.Lock()
            threadlock.acquire()
            v2v_op.updata_v2v_message(request_id, message)
            in_a_s.update_instance_actions(request_id, esx_v2vActions.ATTACH_DISK, ActionStatus.SUCCSESS,
                                           message)
            v2v_op.updata_v2v_ontask(request_id, '0')
            v2v_op.update_v2v_step(request_id, esx_v2vActions.ATTACH_DISK)
            threadlock.release()


#windows_vm_std函数
def win_vm_std(request_id):
    v2v_task = v2v_op.v2vTaskService().get_v2v_task_by_requestid(request_id)
    vmip = v2v_task['vm_ip']
    ostype = 'Windows'
    ip_data = ip_s.IPService().get_ip_by_ip_address(vmip)
    vmmask_int = int(ip_data['netmask'])
    vmmask = exchange_maskint(vmmask_int)
    vmgateway = ip_data['gateway_ip']
    vmname = v2v_task['vm_name']
    dns1 = ip_data['dns1']
    dns2 = ip_data['dns2']
    host_ip = v2v_task['dest_host']
    cloudarea = v2v_task['cloud_area']
    connect_instance = instanceManager.libvirt_get_connect(host_ip, conn_type='instance', vmname=vmname)
    inject_stauts, mesg = instanceManager.v2v_esx_win_inject(connect_instance, vmname, vmip, vmgateway,
                                                           dns1, dns2, vmmask, ostype, cloudarea)
    if inject_stauts:
        message = "信息注入成功"
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        in_a_s.update_instance_actions(request_id, esx_v2vActions.WINDOWS_STD, ActionStatus.SUCCSESS,
                                       message)
        v2v_op.update_v2v_step(request_id, esx_v2vActions.WINDOWS_STD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        vm_uuid = v2v_op.v2vTaskService().get_v2v_task_by_requestid(request_id)['vm_uuid']
        v2v_op.update_v2v_actions(request_id, 1)
        v2v_op.update_v2v_step(request_id, esx_v2vActions.WINDOWS_STD)
        where_data = {
            'uuid': vm_uuid
        }
        update_data = {
            'status': '3'
        }
        ins_s.InstanceService().update_instance_info(update_data, where_data)
        threadlock.release()
    else:
        message = "信息注入失败"
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.WINDOWS_STD, ActionStatus.FAILD,
                                       message)
        threadlock.release()

#win_disk_ch函数
def win_disk_ch(vm_name,kvmhost,request_id):
    vmsd,msg = vm_shutdown(kvmhost,vm_name)
    if not vmsd:
        message = msg
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.WINDOWS_DISK_CH, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    else:
        disktype = 'virtio'
        v2v_win_disk_ch = instanceManager.v2v_win_disk_ch(kvmhost,vm_name,disktype)
        if not v2v_win_disk_ch:
            message = '修改磁盘格式失败'
            threadlock = threading.Lock()
            threadlock.acquire()
            v2v_op.updata_v2v_message(request_id, message)
            v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
            v2v_op.updata_v2v_ontask(request_id, '0')
            in_a_s.update_instance_actions(request_id, esx_v2vActions.WINDOWS_DISK_CH, ActionStatus.FAILD,
                                           message)
            threadlock.release()
        else:
            message = '修改磁盘格式成功'
            threadlock = threading.Lock()
            threadlock.acquire()
            v2v_op.updata_v2v_message(request_id, message)
            in_a_s.update_instance_actions(request_id, esx_v2vActions.WINDOWS_DISK_CH, ActionStatus.SUCCSESS,
                                           message)
            v2v_op.updata_v2v_ontask(request_id, '0')
            v2v_op.update_v2v_step(request_id, esx_v2vActions.WINDOWS_DISK_CH)
            threadlock.release()


#根据子网掩码位数计算子网掩码值
def exchange_maskint(mask_int):
  bin_arr = ['0' for i in range(32)]
  for i in range(mask_int):
    bin_arr[i] = '1'
  tmpmask = [''.join(bin_arr[i * 8:i * 8 + 8]) for i in range(4)]
  tmpmask = [str(int(tmpstr, 2)) for tmpstr in tmpmask]
  return '.'.join(tmpmask)


def vm_shutdown(kvmhost,vm_name):
    vmshutdown = instanceManager.libvirt_instance_shutdown(kvmhost,vm_name)
    if not vmshutdown:
        message = 'vm关机下发失败'
        return False,message
    else:
        vm_state = vmstate(kvmhost,vm_name)
        if vm_state == 0:
            message = "VM已关机"
            return True,message
        else:
            message = "VM关机失败"
            return False,message


#循环判断vm电源状态
def vmstate(kvmhost,vm_name):
    i=0
    while i<120:
        time.sleep(5)
        resp,msg = vm_powerstate(kvmhost,vm_name)
        if resp == True:
            return 0
        else:
            i+=1

def vm_powerstate(kvmhost,vm_name):
    vmpowersta = instanceManager.libvirt_instance_status(kvmhost,vm_name)
    if vmpowersta == -100 or vmpowersta != 5:
        logging.error('instance %s is not in poweroff status', vmpowersta)
        message = "虚拟机未关机，请确定虚拟机状态"
        return False,message
    else:
        message = "虚拟机已关机"
        return True,message

#vm二次开机
def vm_start2(kvmhost,vmname,request_id,modulename,vm_uuid):
    command = 'virsh start '+ vmname
    remote_user = ANSIABLE_REMOTE_USER
    remote_pass = decrypt(KVMHOST_LOGIN_PASS)
    become_user = OPENSTACK_DEV_USER
    become_pass = decrypt(KVMHOST_SU_PASS)
    vmstart = ansible_run_shell(kvmhost, command)
    if 'contacted' not in vmstart:
        message = 'vm启动失败'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.VM_START2, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    elif vmstart['contacted'] == {}:
        message = 'vm启动失败'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.VM_START2, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    elif 'failed' in vmstart['contacted'][kvmhost]:
        message = 'vm启动失败'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.VM_START2, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    elif vmstart['contacted'][kvmhost]['stdout'] == '':
        message = 'vm启动失败'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, esx_v2vActions.VM_START2, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    else:
        message = 'vm启动成功'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        in_a_s.update_instance_actions(request_id, esx_v2vActions.VM_START2, ActionStatus.SUCCSESS,
                                       message)
        v2v_op.updata_v2v_ontask(request_id, '0')
        v2v_op.update_v2v_step(request_id, esx_v2vActions.VM_START2)
        threadlock.release()


if __name__ == '__main__':
   while True:
       esx_do_task()