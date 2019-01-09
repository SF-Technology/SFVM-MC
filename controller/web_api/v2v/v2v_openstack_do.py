# coding=utf8
'''
    v2v_openstack
'''
# __author__ = 'anke'


import env
from lib.shell.ansibleCmdV2 import ansible_run_shell

env.init_env()
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
from model.const_define import v2vActions,ActionStatus,VMCreateSource
from service.v2v_task import v2v_task_service as v2v_op
from service.s_instance_action import instance_action as in_a_s
from service.s_instance import instance_service as ins_s
from service.s_flavor import flavor_service
from service.s_ip import ip_service as ip_s
import logging
import time
import random
import threading
from lib.vrtManager import instanceManager as vmManager
import traceback
from lib.vrtManager import instanceManager
from config.default import OPENSTACK_DEV_PASS,OPENSTACK_SIT_PASS,KVMHOST_LOGIN_PASS,\
    KVMHOST_SU_PASS,ANSIABLE_REMOTE_USER,OPENSTACK_SIT_USER
from helper.encrypt_helper import decrypt
from service.s_host import host_schedule_service as host_s_s
import string



def do_task():

        #获取当前在进行的任务清单
        list_working = v2v_op.get_v2v_todo()

        if not list_working:
            time.sleep(60)
            return 0

        for i in list_working:
            #获取当前任务信息
            request_id = i['request_id']
            vm_ip =i['vm_ip']
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
            if status == 0 and on_task == '0' and source == VMCreateSource.OPENSTACK:
                #更新任务执行中
                # 获取对应openstack环境的管理节点及ssh账户信息
                if cloud_area == "SIT":
                    ctr_host = '10.202.83.12'
                    ctr_pass = decrypt(OPENSTACK_SIT_PASS)
                elif cloud_area == "DEV":
                    ctr_host = '10.202.123.4'
                    ctr_pass = decrypt(OPENSTACK_DEV_PASS)
                else:
                    message = "openstack环境参数错误，无法进行v2v操作"
                    v2v_op.updata_v2v_message(request_id,message)
                    v2v_op.updata_v2v_status(request_id,2)

                # 获取flavor信息
                flavor_info = flavor_service.FlavorService().get_flavor_info(flavor_id)
                vmcpu_int = flavor_info['vcpu']
                vmcpu = str(vmcpu_int)
                vmmem = flavor_info['memory_mb']
                vmmem_kB_int = vmmem * 1024
                vmmem_kB = str(vmmem_kB_int)

                # 判断任务是否可操作
                v2v_sta1 = v2v_op.get_v2v_running_by_reqid(request_id)
                if v2v_sta1 == True:
                    # 判断任务当前已完成步骤
                    if step_done == "begin":
                        # 判断待转化vm是否关机
                        threadlock = threading.Lock()
                        threadlock.acquire()
                        v2v_op.updata_v2v_ontask(request_id, '1')
                        threadlock.release()
                        vm_stat(vm_ip, ctr_host, ctr_pass,request_id,"command")

                        #判断任务是否可操作
                        v2v_sta2 = v2v_op.get_v2v_running_by_reqid(request_id)
                        if v2v_sta2 == True:
                            threadlock = threading.Lock()
                            threadlock.acquire()
                            v2v_op.updata_v2v_ontask(request_id, '1')
                            threadlock.release()
                            #在目标服务器上创建文件夹
                            createdir(dest_host,request_id,"command",dest_dir)

                    # 判断任务是否可操作
                    v2v_sta10 = v2v_op.get_v2v_running_by_reqid(request_id)
                    if v2v_sta10 == True:
                        step_done8 = v2v_op.get_v2v_step(request_id)
                        if step_done8 == "create_destination_dir":
                            threadlock = threading.Lock()
                            threadlock.acquire()
                            v2v_op.updata_v2v_ontask(request_id, '1')
                            threadlock.release()
                            # 创建存储池
                            host_ip = dest_host
                            dir = v2v_op.get_v2v_destdir(request_id)
                            dir_uuid = dir.replace('/app/image/', '')
                            _create_storage_pool(host_ip, dir_uuid, request_id)

                    #判断任务是否可操作
                    v2v_sta3 = v2v_op.get_v2v_running_by_reqid(request_id)
                    if v2v_sta3 == True:
                        #获取任务
                        step_done1 = v2v_op.get_v2v_step(request_id)
                        if step_done1 == "create_storage_pool":
                            threadlock = threading.Lock()
                            threadlock.acquire()
                            v2v_op.updata_v2v_ontask(request_id, '1')
                            threadlock.release()
                            #获取待转化vm文件
                            get_vm_file(vm_name,vm_ip,ctr_host,ctr_pass,request_id,"command")


                    #判断任务是否可操作
                    v2v_sta5 = v2v_op.get_v2v_running_by_reqid(request_id)
                    if v2v_sta5 == True:
                        step_done2 = v2v_op.get_v2v_step(request_id)
                        if step_done2 == "get_vm_file":
                            threadlock = threading.Lock()
                            threadlock.acquire()
                            v2v_op.updata_v2v_ontask(request_id, '1')
                            threadlock.release()
                            #拷贝vmdisk文件
                            dir = v2v_op.get_v2v_destdir(request_id)
                            print dir
                            _copy_disk(request_id, ctr_host, ctr_pass, vm_ip, dir, dest_host)

                    # #判断任务是否可操作
                    # v2v_sta6 = v2v_op.get_v2v_running_by_reqid(request_id)
                    # if v2v_sta6 == True:
                    #     step_done3 = v2v_op.get_v2v_step(request_id)
                    #     if step_done3 == "copy_vm_disk_to_desthost":
                    #         v2v_op.updata_v2v_ontask(request_id, '1')
                    #         #拷贝vmxml文件
                    #         dir = v2v_op.get_v2v_destdir(request_id)
                    #         _copy_xml(request_id, ctr_host, ctr_pass, vm_ip, dir, dest_host)

                    # 判断任务是否可操作
                    v2v_sta12 = v2v_op.get_v2v_running_by_reqid(request_id)
                    if v2v_sta12 == True:
                        step_done10 = v2v_op.get_v2v_step(request_id)
                        if step_done10 == "copy_vm_disk_to_desthost":
                            v2v_op.updata_v2v_ontask(request_id, '1')
                            # vm文件标准化
                            dir = v2v_op.get_v2v_destdir(request_id)
                            vm_standardlize(dest_host, vm_ip, dir, vm_vlan, vm_name, vm_mac, vm_uuid, vmcpu, vmmem_kB,
                                            request_id, ostype, "raw")


                    #判断vm注册是否执行
                    v2v_sta8 = v2v_op.get_v2v_running_by_reqid(request_id)
                    if v2v_sta8 == True:
                        step_done5 = v2v_op.get_v2v_step(request_id)
                        if step_done5 == "standardlize_target_vm":
                            v2v_op.updata_v2v_ontask(request_id, '1')
                            #vm注册
                            dir = v2v_op.get_v2v_destdir(request_id)
                            vm_define(dest_host,vm_ip,dir,request_id,"command")

                    #判断vm开机是否执行
                    v2v_sta9 = v2v_op.get_v2v_running_by_reqid(request_id)
                    if v2v_sta9 == True:
                        step_done6 = v2v_op.get_v2v_step(request_id)
                        if step_done6 == "define_target_vm":
                            v2v_op.updata_v2v_ontask(request_id, '1')
                            #vm开机
                            vm_start(dest_host, vm_name,request_id,"command")


                    #判断ip注入是否执行
                    v2v_sta0 = v2v_op.get_v2v_running_by_reqid(request_id)
                    if v2v_sta0 == True:
                        step_done7 = v2v_op.get_v2v_step(request_id)
                        if step_done7 == "start_target_vm":
                            v2v_op.updata_v2v_ontask(request_id, '1')
                            #IP信息注入
                            ip_inject(request_id, vm_ip, ctr_host, ctr_pass)


#在目标kvm host上创建uuid文件夹
def createdir(kvmhost,request_id,modulename,dir):

    command = 'mkdir -p '+dir
    remote_user = ANSIABLE_REMOTE_USER
    remote_pass = decrypt(KVMHOST_LOGIN_PASS)
    become_user = OPENSTACK_SIT_USER
    become_pass = decrypt(KVMHOST_SU_PASS)
    dir_result = ansible_run_shell(kvmhost,command)
    if 'contacted' not in dir_result:
        message = '创建vm目录失败'
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, v2vActions.CREATE_DEST_DIR, ActionStatus.FAILD,
                                       message)
    elif dir_result['contacted'] == {}:
        message = '创建vm目录失败'
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, v2vActions.CREATE_DEST_DIR, ActionStatus.FAILD,
                                       message)
    elif 'failed' in dir_result['contacted'][kvmhost]:
        message = '创建vm目录失败'
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, v2vActions.CREATE_DEST_DIR, ActionStatus.FAILD,
                                       message)
    else:
        data = dir
        message = '创建vm目录成功'
        v2v_op.updata_v2v_message(request_id, message)
        in_a_s.update_instance_actions(request_id, v2vActions.CREATE_DEST_DIR, ActionStatus.SUCCSESS,
                                       message)
        v2v_op.update_v2v_step(request_id,v2vActions.CREATE_DEST_DIR)

        v2v_op.updata_v2v_ontask(request_id, '0')
        v2v_op.update_v2v_destdir(request_id,data)


#获取vm磁盘和xml文件函数
def get_vm_file(vmname,vmip,host,host_pass,request_id,modulename):
    command1 = 'cd /var/lib/mongo/tempraw/' + vmip +';rm -f *.ok;rm -f *.qcow2;rm -f *.xml;rm -f *.log'
    command2 = 'rmdir /var/lib/mongo/tempraw/' + vmip
    command = 'sh /var/lib/mongo/tempraw/get_disk_and_xml.sh ' + vmname + ' ' + vmip
    remote_user = OPENSTACK_SIT_USER
    become_user = OPENSTACK_SIT_USER
    remote_pass = host_pass
    become_pass = host_pass
    ctrhost = host
    rmfile =ansible_run_shell(ctrhost,command1)
    if 'contacted' not in rmfile:
        message = '连接openstack控制节点失败'
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, v2vActions.GET_VM_FILE, ActionStatus.FAILD,
                                       message)
    elif rmfile['contacted'] == {}:
        message = '连接openstack控制节点失败'
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, v2vActions.GET_VM_FILE, ActionStatus.FAILD,
                                       message)
    elif 'failed' in rmfile['contacted'][ctrhost]:
        message = '清除无效文件失败'
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, v2vActions.GET_VM_FILE, ActionStatus.FAILD,
                                       message)
    else:
        time.sleep(3)
        rmdir = ansible_run_shell(ctrhost,command2)
        if rmdir['contacted'] == {}:
            message = '连接openstack控制节点失败'
            v2v_op.updata_v2v_message(request_id, message)
            v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
            v2v_op.updata_v2v_ontask(request_id, '0')
            in_a_s.update_instance_actions(request_id, v2vActions.GET_VM_FILE, ActionStatus.FAILD,
                                           message)
        elif 'failed' in rmdir['contacted'][ctrhost]:
            message = '清除无效文件失败'
            v2v_op.updata_v2v_message(request_id, message)
            v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
            v2v_op.updata_v2v_ontask(request_id, '0')
            in_a_s.update_instance_actions(request_id, v2vActions.GET_VM_FILE, ActionStatus.FAILD,
                                           message)
        else:
            getvmfile = ansible_run_shell(ctrhost,command)
            if getvmfile['contacted'] == {}:
                message = '连接openstack控制节点失败'
                v2v_op.updata_v2v_message(request_id, message)
                v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
                v2v_op.updata_v2v_ontask(request_id, '0')
                in_a_s.update_instance_actions(request_id, v2vActions.GET_VM_FILE, ActionStatus.FAILD,
                                               message)
            elif 'failed' in getvmfile['contacted'][ctrhost]:
                message = '获取vm文件失败'
                v2v_op.updata_v2v_message(request_id, message)
                v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
                v2v_op.updata_v2v_ontask(request_id, '0')
                in_a_s.update_instance_actions(request_id, v2vActions.GET_VM_FILE, ActionStatus.FAILD,
                                               message)
            elif 'confirm' in getvmfile['contacted'][ctrhost]['stdout']:
                message = '获取vm文件失败'
                v2v_op.updata_v2v_message(request_id, message)
                v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
                v2v_op.updata_v2v_ontask(request_id, '0')
                in_a_s.update_instance_actions(request_id, v2vActions.GET_VM_FILE, ActionStatus.FAILD,
                                               message)
            else:
                # 循环判断文件是否获取成功
                logging.info('shell run success!')
                datacheck = '/var/lib/mongo/tempraw/' + vmip + '/Done_volume_disk.ok'
                syscheck = '/var/lib/mongo/tempraw/' + vmip + '/Done_system_disk.ok'
                checksys = file_exist(syscheck, host, host_pass, "command",vmip,vmname)
                checkdata = file_exist(datacheck, host, host_pass, "command",vmip,vmname)
                checkall = checksys + checkdata
                if checkall != 0:
                    message = '获取vm文件失败'
                    # 获取文件超时失败则清除openstack端的残余文件
                    ret_del_tempfile, del_tempfile_msg = del_openstack_files(ctrhost, vmip, host_pass)
                    v2v_op.updata_v2v_message(request_id, message)
                    v2v_op.updata_v2v_ontask(request_id, '0')
                    v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
                    in_a_s.update_instance_actions(request_id, v2vActions.GET_VM_FILE, ActionStatus.FAILD,
                                                   message)
                else:
                    message = '获取vm文件成功'
                    v2v_op.updata_v2v_message(request_id, message)
                    in_a_s.update_instance_actions(request_id, v2vActions.GET_VM_FILE,
                                                   ActionStatus.SUCCSESS,
                                                   message)
                    v2v_op.updata_v2v_ontask(request_id, '0')
                    v2v_op.update_v2v_step(request_id, v2vActions.GET_VM_FILE)




#拷贝vm的disk文件到目标kvm host
def copy_vm_disk(vmip,host,destdir,host_pass,kvmhost,request_id,modulename):
    disk_dir = '/var/lib/mongo/tempraw/'+ vmip +'/'
    command = 'scp ' +disk_dir +'*.qcow2 root@'+ kvmhost +':'+ destdir
    print command
    ctrhost = host
    remote_user = OPENSTACK_SIT_USER
    remote_pass = host_pass
    become_user = OPENSTACK_SIT_USER
    become_pass = host_pass
    diskdir = ansible_run_shell(ctrhost,command)
    if 'contacted' not in diskdir:
        message = '连接openstack控制节点失败'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, v2vActions.COPY_VM_DISK, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    elif diskdir['contacted'] == {}:
        message = '连接openstack控制节点失败'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, v2vActions.COPY_VM_DISK, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    elif 'failed' in diskdir['contacted'][ctrhost]:
        message = '拷贝vm磁盘文件失败'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, v2vActions.COPY_VM_DISK, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    else:
        message = '拷贝vm磁盘文件成功'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        in_a_s.update_instance_actions(request_id, v2vActions.COPY_VM_DISK, ActionStatus.SUCCSESS,
                                       message)
        v2v_op.updata_v2v_ontask(request_id, '0')
        v2v_op.update_v2v_step(request_id, v2vActions.COPY_VM_DISK)
        threadlock.release()


#拷贝vm的xml文件至目标kvmhost
def copy_vm_xml(vmip,host,destdir,host_pass,kvmhost,request_id,modulename):
    disk_dir = '/var/lib/mongo/tempraw/'+ vmip +'/'
    command = 'scp ' +disk_dir +'libvirt.xml root@'+ kvmhost +':'+ destdir
    ctrhost = host
    remote_user = OPENSTACK_SIT_USER
    remote_pass = host_pass
    become_user = OPENSTACK_SIT_USER
    become_pass = host_pass
    diskdir = ansible_run_shell(ctrhost,command)
    if 'contacted' not in diskdir:
        message = '连接openstack控制节点失败'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.updata_v2v_ontask(request_id, '0')
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        in_a_s.update_instance_actions(request_id, v2vActions.COPY_VM_XML, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    elif diskdir['contacted'] == {}:
        message = '连接openstack控制节点失败'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.updata_v2v_ontask(request_id, '0')
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        in_a_s.update_instance_actions(request_id, v2vActions.COPY_VM_XML, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    elif 'failed' in diskdir['contacted'][ctrhost]:
        message = '拷贝vm配置文件失败'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, v2vActions.COPY_VM_XML, ActionStatus.FAILD,
                                       message)
        threadlock.release()
    else:
        message = '拷贝vm配置文件成功'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        in_a_s.update_instance_actions(request_id, v2vActions.COPY_VM_XML, ActionStatus.SUCCSESS,
                                       message)
        v2v_op.updata_v2v_ontask(request_id, '0')
        v2v_op.update_v2v_step(request_id, v2vActions.COPY_VM_XML)
        threadlock.release()


#vm磁盘文件和xml文件标准化
def vm_standardlize(kvmhost,vmip,dir,vm_vlan,vm_name,vmmac,uuid,vmcpu,vmmem,request_id,ostype,modulename):
    command = 'sh /home/cloudlog/vm_standardlize.sh '+ vmip + ' ' + dir + ' ' + vm_vlan + ' '+ vm_name + ' '+ vmmac + ' '+uuid + ' ' + vmcpu + ' ' + vmmem +' '+ostype
    remote_user = ANSIABLE_REMOTE_USER
    remote_pass = decrypt(KVMHOST_LOGIN_PASS)
    become_user = OPENSTACK_SIT_USER
    become_pass = decrypt(KVMHOST_SU_PASS)
    vmstd = ansible_run_shell(kvmhost,command)
    if 'contacted' not in vmstd:
        message = 'vm文件标准化失败'
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.updata_v2v_ontask(request_id, '0')
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        in_a_s.update_instance_actions(request_id, v2vActions.VM_STANDARDLIZE, ActionStatus.FAILD,
                                       message)
    elif vmstd['contacted'] == {}:
        message = 'vm文件标准化失败'
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.updata_v2v_ontask(request_id, '0')
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        in_a_s.update_instance_actions(request_id, v2vActions.VM_STANDARDLIZE, ActionStatus.FAILD,
                                       message)
    elif 'failed' in vmstd['contacted'][kvmhost]:
        message = 'vm文件标准化失败'
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.updata_v2v_ontask(request_id, '0')
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        in_a_s.update_instance_actions(request_id, v2vActions.VM_STANDARDLIZE, ActionStatus.FAILD,
                                       message)
    elif vmstd['contacted'][kvmhost]['stdout']== '':
        message = 'vm文件标准化失败'
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.updata_v2v_ontask(request_id, '0')
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        in_a_s.update_instance_actions(request_id, v2vActions.VM_STANDARDLIZE, ActionStatus.FAILD,
                                       message)
    else:
        message = 'vm文件标准化成功'
        v2v_op.updata_v2v_message(request_id, message)
        in_a_s.update_instance_actions(request_id, v2vActions.VM_STANDARDLIZE, ActionStatus.SUCCSESS,
                                       message)
        v2v_op.updata_v2v_ontask(request_id, '0')
        v2v_op.update_v2v_step(request_id, v2vActions.VM_STANDARDLIZE)


#kvm host上注册v2v后的vm
def vm_define(kvmhost,vmip,dir,request_id,modulename):
    vm_xml = dir+'/'+ vmip +'.xml'
    command = 'virsh define '+ vm_xml
    remote_user = ANSIABLE_REMOTE_USER
    remote_pass = decrypt(KVMHOST_LOGIN_PASS)
    become_user = OPENSTACK_SIT_USER
    become_pass = decrypt(KVMHOST_SU_PASS)
    vmdefine = ansible_run_shell(kvmhost, command)
    if 'contacted' not in vmdefine:
        message = 'vm注册失败'
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, v2vActions.VM_DEFINE, ActionStatus.FAILD,
                                       message)
    elif vmdefine['contacted'] == {}:
        message = 'vm注册失败'
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, v2vActions.VM_DEFINE, ActionStatus.FAILD,
                                       message)
    elif 'failed' in vmdefine['contacted'][kvmhost]:
        message = 'vm注册失败'
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, v2vActions.VM_DEFINE, ActionStatus.FAILD,
                                       message)
    elif vmdefine['contacted'][kvmhost]['stdout'] == '':
        message = 'vm注册失败'
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, v2vActions.VM_DEFINE, ActionStatus.FAILD,
                                       message)
    else:
        message = 'vm注册成功'
        rmcommand = 'cd ' + dir +';rm diskfile;rm *.xml'
        ansible_run_shell(kvmhost,rmcommand)
        v2v_op.updata_v2v_message(request_id, message)
        in_a_s.update_instance_actions(request_id, v2vActions.VM_DEFINE, ActionStatus.SUCCSESS,
                                       message)
        v2v_op.updata_v2v_ontask(request_id, '0')
        v2v_op.update_v2v_step(request_id, v2vActions.VM_DEFINE)



#kvm host上启动虚拟机
def vm_start(kvmhost,vmname,request_id,modulename):
    command = 'virsh start '+ vmname
    remote_user = ANSIABLE_REMOTE_USER
    remote_pass = decrypt(KVMHOST_LOGIN_PASS)
    become_user = OPENSTACK_SIT_USER
    become_pass = decrypt(KVMHOST_SU_PASS)
    vmstart = ansible_run_shell(kvmhost, command)
    if 'contacted' not in vmstart:
        message = 'vm启动失败'
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, v2vActions.VM_START, ActionStatus.FAILD,
                                       message)
    elif vmstart['contacted'] == {}:
        message = 'vm启动失败'
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, v2vActions.VM_START, ActionStatus.FAILD,
                                       message)
    elif 'failed' in vmstart['contacted'][kvmhost]:
        message = 'vm启动失败'
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, v2vActions.VM_START, ActionStatus.FAILD,
                                       message)
    elif vmstart['contacted'][kvmhost]['stderr']:
        if 'already active' in vmstart['contacted'][kvmhost]['stderr']:
            message = 'vm已启动pass'
            v2v_op.updata_v2v_message(request_id, message)
            in_a_s.update_instance_actions(request_id, v2vActions.VM_START, ActionStatus.SUCCSESS,
                                           message)
            v2v_op.updata_v2v_ontask(request_id, '0')
            v2v_op.update_v2v_step(request_id, v2vActions.VM_START)
        else:
            message = 'vm启动失败'
            v2v_op.updata_v2v_message(request_id, message)
            v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
            v2v_op.updata_v2v_ontask(request_id, '0')
            in_a_s.update_instance_actions(request_id, v2vActions.VM_START, ActionStatus.FAILD,
                                           message)
    else:
        sleep_time = random.randint(5,10)
        time.sleep(sleep_time)
        message = 'vm启动成功'
        v2v_op.updata_v2v_message(request_id, message)
        in_a_s.update_instance_actions(request_id, v2vActions.VM_START, ActionStatus.SUCCSESS,
                                       message)
        v2v_op.updata_v2v_ontask(request_id, '0')
        v2v_op.update_v2v_step(request_id, v2vActions.VM_START)


#判断vm是否关机
def vm_stat(vmip,host,host_pass,request_id,modulename):
    command = "/usr/bin/vmop " + vmip + " |grep 'vm_state'|grep 'stopped'"
    command_data_vol = "/usr/bin/vmop " + vmip + " data_volume"
    remote_user = OPENSTACK_SIT_USER
    become_user = OPENSTACK_SIT_USER
    remote_pass = host_pass
    become_pass = host_pass
    ctrhost = host
    vmstat = ansible_run_shell(ctrhost,command)
    if 'contacted' not in vmstat:
        message = "无法连接目标vm所在控制节点，无法完成v2v操作"
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, v2vActions.BEGIN, ActionStatus.FAILD,
                                       message)
    elif vmstat['contacted'] == {}:
        message = "无法连接目标vm所在控制节点，无法完成v2v操作"
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, v2vActions.BEGIN, ActionStatus.FAILD,
                                       message)
    elif 'failed' in vmstat['contacted'][ctrhost]:
        message = '获取待转化vm当前状态失败，无法完成v2v操作'
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, v2vActions.BEGIN, ActionStatus.FAILD,
                                       message)
    elif vmstat['contacted'][ctrhost]['stdout'] == '':
        message = '待转化vm未关机，无法完成v2v操作'
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, v2vActions.BEGIN, ActionStatus.FAILD,
                                       message)
    else :
        message = '待转化vm已关机，进行后续v2v步骤'
        logging.info(message)
        data_disk_res = ansible_run_shell(ctrhost, command_data_vol)
        vm_data_disk = data_disk_res['contacted'][ctrhost]['stdout']
        if not vm_data_disk:
            message = '获取待转化vm数据盘大小失败，无法完成v2v操作'
            v2v_op.updata_v2v_message(request_id, message)
            v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
            v2v_op.updata_v2v_ontask(request_id, '0')
            in_a_s.update_instance_actions(request_id, v2vActions.BEGIN, ActionStatus.FAILD,
                                           message)
        else:
            vm_disk = float(vm_data_disk)
            if vm_disk < 0 or vm_disk > 500:
                message = '待转化的vm数据盘大小过大，为%sG，请后续手动处理' % vm_disk
                v2v_op.updata_v2v_message(request_id, message)
                v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
                v2v_op.updata_v2v_ontask(request_id, '0')
                in_a_s.update_instance_actions(request_id, v2vActions.BEGIN, ActionStatus.FAILD,
                                               message)
            else:
                message = '待转化vm已关机，数据盘大小符合迁移要求'
                v2v_op.updata_v2v_message(request_id, message)
                v2v_op.updata_v2v_ontask(request_id, '0')
                in_a_s.update_instance_actions(request_id, v2vActions.BEGIN, ActionStatus.SUCCSESS,
                                               message)


#判断远端文件是否存在
def file_exist_one(r_user,r_pass,b_user,b_pass,dir,host,modulename):
    command = "ls -al " +dir
    remote_user = r_user
    become_user = b_user
    remote_pass = r_pass
    become_pass = b_pass
    ctrhost = host
    testfile = ansible_run_shell(ctrhost, command)
    print testfile['contacted']
    if 'contacted' not in testfile:
        return False
    elif testfile['contacted'] == {}:
        return False
    elif 'failed' in testfile['contacted'][ctrhost]:
        return False
    elif testfile['contacted'][ctrhost]['stdout'] == '':
        return False
    else:
        return True

#循环判断5 hour超时
def file_exist(dir,host,host_pass,modulename,vmip,vmname):
    i=0
    while i<60:
        time.sleep(300)
        r_user= OPENSTACK_SIT_USER
        b_user = OPENSTACK_SIT_USER
        r_pass = host_pass
        b_pass = host_pass
        resp = file_exist_one(r_user,r_pass,b_user,b_pass,dir,host,modulename)
        if resp == True:
            return 0
        else:
            # 判断远端是否有生成vm磁盘文件
            vm_disk_check = check_vm_disk_create(vmip, host, host_pass)
            # 如果远端没有生成vmdisk文件，则删除文件夹重新下发命令
            if not vm_disk_check:
                get_vm_file_retry(vmname, vmip, host, host_pass)
            i+=1
    return 1


#IP信息注入
def ip_inject(request_id,vm_ip,openstack_ip,openstack_pass):
    v2v_task = v2v_op.v2vTaskService().get_v2v_task_by_requestid(request_id)
    vmip = v2v_task['vm_ip']
    ostype = v2v_task['vm_ostype']
    ip_data = ip_s.IPService().get_ip_by_ip_address(vmip)
    vmmask_int = int(ip_data['netmask'])
    vmmask = exchange_maskint(vmmask_int)
    vmgateway = ip_data['gateway_ip']
    vmname = v2v_task['vm_name']
    dns1 = ip_data['dns1']
    dns2 = ip_data['dns2']
    host_ip = v2v_task['dest_host']
    cloudarea = v2v_task['cloud_area']
    count = 0
    connect_instance = False
    if not connect_instance and count < 3:
        connect_instance = vmManager.libvirt_get_connect(host_ip, conn_type='instance', vmname=vmname)
        count += 1
        time.sleep(10)
    if not connect_instance:
        message = "IP信息注入失败,libvirt连接vm超时"
        del_openstack_files(openstack_ip, vm_ip, openstack_pass)
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, v2vActions.IP_INJECT, ActionStatus.FAILD,
                                       message)
    else:
        inject_stauts, mesg = vmManager.v2v_openstack_ipinject(connect_instance, vmname, vmip, vmgateway,
                                                               dns1, dns2, vmmask, ostype, cloudarea)
        if inject_stauts:
            ret_del_tempfile,del_tempfile_msg = del_openstack_files(openstack_ip, vm_ip,openstack_pass)
            v2v_op.updata_v2v_message(request_id, del_tempfile_msg)
            in_a_s.update_instance_actions(request_id, v2vActions.IP_INJECT, ActionStatus.SUCCSESS,
                                           del_tempfile_msg)
            v2v_op.update_v2v_step(request_id, v2vActions.IP_INJECT)
            v2v_op.updata_v2v_ontask(request_id, '0')
            v2v_op.update_v2v_actions(request_id, 1)
            vm_uuid = v2v_op.v2vTaskService().get_v2v_task_by_requestid(request_id)['vm_uuid']
            where_data = {
                'uuid': vm_uuid
            }
            update_data = {
                'status': '3'
            }
            ins_s.InstanceService().update_instance_info(update_data, where_data)
        else:
            message = "IP信息注入失败"
            del_openstack_files(openstack_ip, vm_ip, openstack_pass)
            v2v_op.updata_v2v_message(request_id, message)
            v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
            v2v_op.updata_v2v_ontask(request_id, '0')
            in_a_s.update_instance_actions(request_id, v2vActions.IP_INJECT, ActionStatus.FAILD,
                                           message)




#根据子网掩码位数计算子网掩码值
def exchange_maskint(mask_int):
  bin_arr = ['0' for i in range(32)]
  for i in range(mask_int):
    bin_arr[i] = '1'
  tmpmask = [''.join(bin_arr[i * 8:i * 8 + 8]) for i in range(4)]
  tmpmask = [str(int(tmpstr, 2)) for tmpstr in tmpmask]
  return '.'.join(tmpmask)


#获取待迁移的磁盘文件
def ansible_migrate_vol_get(request_id,ctr_host,ctr_pass):
    '''
        获取迁移目标主机卷名称
    :param request_id:
    :param
    :return:
    '''
    v2v_task = v2v_op.v2vTaskService().get_v2v_task_by_requestid(request_id)
    vmip = v2v_task["vm_ip"]
    r_user = OPENSTACK_SIT_USER
    r_pass = ctr_pass
    b_user = OPENSTACK_SIT_USER
    b_pass = ctr_pass

    vol_cmd = 'cd /var/lib/mongo/tempraw/' + vmip + ';ls|grep qcow2'
    hostlist = ctr_host
    modulename =  "shell"
    run_result = ansible_run_shell(hostlist,vol_cmd)
    logging.info(run_result)
    if 'contacted' not in run_result:
        message = '获取vm磁盘文件清单失败'
        logging.info(message)
        return False, None
    elif run_result['contacted'] == {}:
        message = '获取vm磁盘文件清单失败'
        logging.info(message)
        return False,None
    elif 'failed' in run_result['contacted'][ctr_host]:
        message = '获取vm磁盘文件清单失败'
        logging.info(message)
        return False, None
    if run_result['contacted'][ctr_host]['stderr']:
        logging.info("获取vm磁盘文件清单失败")
        return False, None
    else:
        logging.info('获取vm磁盘文件清单成功 ')
        return True, run_result['contacted'][ctr_host]['stdout'].split('\n')



def ansible_migrate_file_get(host, command,r_user,r_pass,b_user,b_pass,request_id):
    '''
        获取迁移文件
    :param host_ip:
    :param cmd:
    :return:
    '''
    r_user = r_user
    b_user = b_user
    r_pass = r_pass
    b_pass = b_pass
    modulename = "shell"
    try:
        hostlist = host
        run_result = ansible_run_shell(hostlist,command)
        logging.info(run_result)

        if run_result['contacted'][host]['stderr']:
            logging.info("get migrate file return: %s" % run_result['contacted'][host]['stderr'])
            logging.info('exec %s   failed ' % command)
            msg = "拷贝vm文件失败"
            threadlock = threading.Lock()
            threadlock.acquire()
            v2v_op.updata_v2v_message(request_id, msg)
            v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
            v2v_op.updata_v2v_ontask(request_id, '0')
            in_a_s.update_instance_actions(request_id, v2vActions.COPY_VM_DISK, ActionStatus.FAILD,
                                           msg)
            threadlock.release()
            return False
        elif 'failed' in run_result['contacted'][host]:
            msg = "拷贝vm文件失败"
            threadlock = threading.Lock()
            threadlock.acquire()
            v2v_op.updata_v2v_message(request_id, msg)
            v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
            v2v_op.updata_v2v_ontask(request_id, '0')
            in_a_s.update_instance_actions(request_id, v2vActions.COPY_VM_DISK, ActionStatus.FAILD,
                                           msg)
            threadlock.release()
        else:
            logging.info('exec %s   success ' % command)
            return True
    except:
        logging.error(traceback.format_exc())
        msg = "拷贝vm文件失败"
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, msg)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, v2vActions.COPY_VM_DISK, ActionStatus.FAILD,
                                       msg)
        threadlock.release()
        return False


#使用nc拷贝disk文件
def _copy_disk(request_id,ctr_host,ctr_pass,vm_ip,dest_dir,dest_host):
    g_flag, g_speed = _confirm_image_get_speed(dest_host)
    if not g_flag:
        msg = "获取迁移用网速失败"
        v2v_op.updata_v2v_message(request_id, msg)
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, v2vActions.COPY_VM_DISK, ActionStatus.FAILD,
                                       msg)
    else:
        ret_s = ansible_migrate_qos_speed(ctr_host, dest_host, g_speed,ctr_pass)
        if not ret_s:
            msg = "配置迁移限速失败"
            v2v_op.updata_v2v_message(request_id, msg)
            v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
            v2v_op.updata_v2v_ontask(request_id, '0')
            in_a_s.update_instance_actions(request_id, v2vActions.COPY_VM_DISK, ActionStatus.FAILD,
                                           msg)
        else:
            # 迁移端口
            nc_transfer_port = v2v_op.v2v_ncport(request_id)
            threads = []
            host_ip_d = dest_host

            # 获取源物理机上虚拟机卷名称，用于下面一步的数据拷贝
            ret_flag_g, ins_vol_s = ansible_migrate_vol_get(request_id, ctr_host,ctr_pass)
            if not ret_flag_g:
                msg = "获取待拷贝磁盘文件失败"
                v2v_op.updata_v2v_message(request_id, msg)
                v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
                v2v_op.updata_v2v_ontask(request_id, '0')
                in_a_s.update_instance_actions(request_id, v2vActions.COPY_VM_DISK, ActionStatus.FAILD,
                                               msg)
            else:
                logging.info('开始拷贝vm磁盘文件到目标主机')
                for _ins_vol in ins_vol_s:
                    ins_vol_server_get_d = 'cd ' + dest_dir +  ';nc -l -4 ' + str(nc_transfer_port) + ' > ' + _ins_vol
                    ins_vol_server_send_s = 'cd /var/lib/mongo/tempraw/' + vm_ip + ';nc -4 ' + dest_host + ' ' + str(
                        nc_transfer_port) \
                                            + ' < ' + _ins_vol
                    # 多线程启动nc拷贝镜像文件
                    t_vol_host_d = threading.Thread(target=ansible_migrate_file_get, args=(host_ip_d, ins_vol_server_get_d,
                                                                                           ANSIABLE_REMOTE_USER,decrypt(KVMHOST_LOGIN_PASS),OPENSTACK_SIT_USER,decrypt(KVMHOST_SU_PASS),request_id))
                    threads.append(t_vol_host_d)
                    t_vol_host_d.start()

                    time.sleep(5)

                    t_vol_host_s = threading.Thread(target=ansible_migrate_file_get, args=(ctr_host, ins_vol_server_send_s,
                                                                                           OPENSTACK_SIT_USER,ctr_pass,OPENSTACK_SIT_USER,ctr_pass,request_id))
                    threads.append(t_vol_host_s)
                    t_vol_host_s.start()

                    # 判断多线程是否结束
                    for t in threads:
                        t.join()
                # 判断远端是否有disk文件
                dest_file = dest_dir + '/*.qcow2'
                filetest = file_exist_one(ANSIABLE_REMOTE_USER,decrypt(KVMHOST_LOGIN_PASS),OPENSTACK_SIT_USER,decrypt(KVMHOST_SU_PASS),dest_file,host_ip_d,'raw')
                if filetest == False:
                    msg = "获取待拷贝磁盘文件失败"
                    v2v_op.updata_v2v_message(request_id, msg)
                    v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
                    v2v_op.updata_v2v_ontask(request_id, '0')
                    in_a_s.update_instance_actions(request_id, v2vActions.COPY_VM_DISK, ActionStatus.FAILD,
                                                   msg)

                else:
                    speed_cal = ansible_migrate_cancel_qos_speed(ctr_host,ctr_pass)
                    if not speed_cal:
                        msg = "取消限速失败"
                        v2v_op.updata_v2v_message(request_id, msg)
                        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
                        v2v_op.updata_v2v_ontask(request_id, '0')
                        in_a_s.update_instance_actions(request_id, v2vActions.COPY_VM_DISK, ActionStatus.FAILD,
                                                       msg)
                    else:
                        logging.info('copy img disk from source host to destination host successful')
                        message = '拷贝vm磁盘文件成功'
                        ret_del_tempfile, del_tempfile_msg = del_openstack_files(ctr_host, vm_ip, ctr_pass)
                        v2v_op.updata_v2v_message(request_id, message)
                        in_a_s.update_instance_actions(request_id, v2vActions.COPY_VM_DISK, ActionStatus.SUCCSESS,
                                                   message)
                        v2v_op.updata_v2v_ontask(request_id, '0')
                        v2v_op.update_v2v_step(request_id, v2vActions.COPY_VM_DISK)


#使用nc拷贝xml文件
def _copy_xml(request_id,ctr_host,ctr_pass,vm_ip,dest_dir,dest_host):
    # 迁移端口
    nc_transfer_port = v2v_op.v2v_ncport(request_id)
    threads = []
    host_ip_d = dest_host
    ins_vol_server_get_d = 'cd ' + dest_dir +  ';nc -l -4 ' + str(nc_transfer_port) + ' > libvirt.xml'
    ins_vol_server_send_s = 'cd /var/lib/mongo/tempraw/' + vm_ip + ';nc -4 ' + dest_host + ' ' + str(
                nc_transfer_port) \
                                    + ' < libvirt.xml'
    # 多线程启动nc拷贝镜像文件
    t_vol_host_d = threading.Thread(target=ansible_migrate_file_get, args=(host_ip_d, ins_vol_server_get_d,
                                                                                   ANSIABLE_REMOTE_USER,decrypt(KVMHOST_LOGIN_PASS),OPENSTACK_SIT_USER,decrypt(KVMHOST_SU_PASS),request_id))
    threads.append(t_vol_host_d)
    t_vol_host_d.start()

    time.sleep(5)

    t_vol_host_s = threading.Thread(target=ansible_migrate_file_get, args=(ctr_host, ins_vol_server_send_s,
                                                                                   OPENSTACK_SIT_USER,ctr_pass,OPENSTACK_SIT_USER,ctr_pass,request_id))
    threads.append(t_vol_host_s)
    t_vol_host_s.start()

    # 判断多线程是否结束
    for t in threads:
        t.join()
    # 判断远端是否有disk文件
    dest_file = dest_dir + '/libvirt.xml'
    filetest = file_exist_one(ANSIABLE_REMOTE_USER,decrypt(KVMHOST_LOGIN_PASS),OPENSTACK_SIT_USER,decrypt(KVMHOST_SU_PASS),dest_file,host_ip_d,'raw')
    if filetest == False:
        msg = "获取待拷贝xml文件失败"
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, msg)
        v2v_op.updata_v2v_ontask(request_id, '0')
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        in_a_s.update_instance_actions(request_id, v2vActions.COPY_VM_XML, ActionStatus.FAILD,
                                           msg)
        threadlock.release()
    else:
        logging.info('copy img disk from source host to destination host successful')
        message = '拷贝vm xml文件成功'
        threadlock = threading.Lock()
        threadlock.acquire()
        v2v_op.updata_v2v_message(request_id, message)
        in_a_s.update_instance_actions(request_id, v2vActions.COPY_VM_XML, ActionStatus.SUCCSESS,
                                           message)
        v2v_op.updata_v2v_ontask(request_id, '0')
        v2v_op.update_v2v_step(request_id, v2vActions.COPY_VM_XML)
        threadlock.release()


def _create_storage_pool(host_ip, uuid,request_id):
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
        v2v_op.updata_v2v_message(request_id, message)
        v2v_op.updata_v2v_ontask(request_id, '0')
        in_a_s.update_instance_actions(request_id, v2vActions.CREATE_STOR_POOL, ActionStatus.SUCCSESS,
                                       message)
        v2v_op.update_v2v_step(request_id, v2vActions.CREATE_STOR_POOL)
    else:
        msg = "创建存储池失败"
        v2v_op.updata_v2v_message(request_id, msg)
        v2v_op.updata_v2v_ontask(request_id, '0')
        v2v_op.update_v2v_actions(request_id, ActionStatus.FAILD)
        in_a_s.update_instance_actions(request_id, v2vActions.CREATE_STOR_POOL, ActionStatus.FAILD,
                                           msg)



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



def ansible_migrate_qos_speed(host_ip_s, host_ip_d, migrate_speed,host_pass):
    '''
        设置目标主机的迁移速度
    :param host_ip_s:
    :param host_ip_d:
    :param migrate_speed:
    :return:

    '''
    remote_user = OPENSTACK_SIT_USER
    become_user = OPENSTACK_SIT_USER
    remote_pass = host_pass
    become_pass = host_pass
    try:
        speed_cmd = 'cd /root;/bin/bash migratespeedQos ' + host_ip_d + ' ' + str(migrate_speed)
        run_result = ansible_run_shell(host_ip_s,speed_cmd)
        if run_result['contacted'][host_ip_s]['stderr']:
            if 'File exists' in run_result['contacted'][host_ip_s]['stderr']:
                return True
            else:
                logging.info("set host migrate speed return: %s" % run_result['contacted'][host_ip_s]['stderr'])
                logging.info('exec %s   failed ' % speed_cmd)
                return False
        else:
            logging.info('exec %s   success ' % speed_cmd)
            return True
    except:
        logging.error(traceback.format_exc())
        return False



def ansible_migrate_cancel_qos_speed(host_ip_s,host_pass):
    '''
        取消host迁移速度限制
    :param host_ip:
    :param migrate_speed:
    :return:
    '''
    remote_user = OPENSTACK_SIT_USER
    become_user = OPENSTACK_SIT_USER
    remote_pass = host_pass
    become_pass = host_pass
    cancel_cmd = 'cd /root;/bin/bash deletemigratespeedQos'
    run_result = ansible_run_shell(host_ip_s, cancel_cmd)
    if 'contacted' not in run_result:
        return False
    else:
        return True

# 删除OPENSTACK控制节点上残余文件
def del_openstack_files(host_ip, vm_ip,host_pass):
    if not vm_ip:
        return False
    remote_user = OPENSTACK_SIT_USER
    become_user = OPENSTACK_SIT_USER
    remote_pass = host_pass
    become_pass = host_pass
    del_comm = 'cd /var/lib/mongo/tempraw;rm -rf '+ vm_ip
    run_result = ansible_run_shell(host_ip, del_comm)
    if 'contacted' not in run_result:
        message = '删除虚拟机v2v临时文件失败,请手动删除'
        logging.info(message)
        return True,message
    elif run_result['contacted'] == {}:
        message = '删除虚拟机v2v临时文件失败,请手动删除'
        logging.info(message)
        return True,message
    elif 'failed' in run_result['contacted'][host_ip]:
        message = '删除虚拟机v2v临时文件失败,请手动删除'
        logging.info(message)
        return True,message
    elif run_result['contacted'][host_ip]['stderr']:
        message = '删除虚拟机v2v临时文件失败,请手动删除'
        logging.info(message)
        return True,message
    else:
        message = '删除虚拟机v2v临时文件成功'
        logging.info(message)
        return True,message

# 删除openstack上的vm文件夹并重新生成
def get_vm_file_retry(vmname,vmip,host,host_pass):
    command = 'cd /var/lib/mongo/tempraw;rm -rf '\
              + vmip +';sh /var/lib/mongo/tempraw/get_disk_and_xml.sh ' + vmname + ' ' + vmip
    remote_user = OPENSTACK_SIT_USER
    become_user = OPENSTACK_SIT_USER
    remote_pass = host_pass
    become_pass = host_pass
    ansible_run_shell(host, command)

# 检测openstack上是否有生成vm磁盘文件
def check_vm_disk_create(vmip,host,host_pass):
    command = 'cd /var/lib/mongo/tempraw/' + vmip +';ls |grep -v libvirt|grep -v nohup'
    remote_user = OPENSTACK_SIT_USER
    become_user = OPENSTACK_SIT_USER
    remote_pass = host_pass
    become_pass = host_pass
    res_check = ansible_run_shell(host, command)
    if 'contacted' not in res_check:
        return False
    elif res_check['contacted'] == {}:
        return False
    elif 'failed' in res_check['contacted'][host]:
        return False
    elif res_check['contacted'][host]['stdout']!= '':
        return True
    else:
        return False





# def get_host_ondo_copytask(request_id):
#     task_info = v2v_op.v2vTaskService().get_v2v_task_by_requestid(request_id)
#     dest_host = task_info['dest_host']




if __name__ == '__main__':
   while True:
        do_task()
