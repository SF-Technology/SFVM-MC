# coding=utf8
'''
    ESX导入excel批量迁移
'''
# __author__ = 'lisiyuan'

# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
from flask import request, send_from_directory
from helper import json_helper
from model.const_define import ErrorCode, VMStatus, VMTypeStatus, VMCreateSource, esx_v2vActions, InstanceNicType
from config.default import OPENSTACK_DEV_USER, DIR_DEFAULT
import os
from pyexcel_xls import get_data
from service.s_flavor import flavor_service as flavor_s
from service.s_group import group_service as group_s
from service.s_hostpool import hostpool_service as hostpool_s
from service.s_instance import instance_host_service as ins_h_s, instance_ip_service as ins_ip_s, \
    instance_disk_service as ins_d_s, instance_service as ins_s, \
    instance_flavor_service as ins_f_s, instance_group_service as ins_g_s
from service.s_ip import ip_service as ip_s ,segment_service as seg_s
from service.s_instance_action import instance_action as in_a_s
from service.s_host import host_service as ho_s
from service.v2v_task import v2v_instance_info as v2v_in_i
from service.v2v_task import v2v_task_service as v2v_op
from pyVim.connect import SmartConnectNoSSL, Disconnect
from cal_dest_host_batch import calc_dest_host_batch as cal_host_batch
from helper.time_helper import get_datetime_str
import logging
import base64
from lib.vrtManager.util import randomUUID, randomMAC
from service.s_user.user_service import get_user
import threading
import Queue

q = Queue.Queue()


@login_required
def import_excel_esx():
    '''
        批量导入excel
    :return:
    '''
    f = request.files['file']

    # 判断是excel文件
    file_name = f.filename
    (file_shortname, file_suffix) = os.path.splitext(file_name)
    if file_suffix != ".xls" and file_suffix != ".xlsx":
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR,
                                           msg="v2v批量操作只支持excel文件，请选择excel文件")

    xls_data = get_data(f)
    xls_noempty_data = 0
    for sheet_n in xls_data.keys():
        # 只处理一个sheet数据
        if xls_data[sheet_n]:
            all_data_list = xls_data[sheet_n]
            xls_noempty_data += 1
            break

    if xls_noempty_data == 0:
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="不能上传空excel文件")

    all_data_num = len(all_data_list)
    if all_data_num < 2:
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="请填写相关v2v信息后再提交该excel文件")

    user_id = get_user()['user_id']
    # todo:处理空列
    threads = []
    for i, row in enumerate(all_data_list):
        # 默认第一行是标题，跳过
        if i == 0:
            continue

        _check_thread = threading.Thread(target=_check_task, args=(i, row, user_id))
        threads.append(_check_thread)
        _check_thread.start()

    # 判断多线程是否结束
    for t in threads:
        t.join()

    return_msg_list = []
    while not q.empty():
        return_msg_list.append(q.get())

    # 检测返回值有无错误信息
    v2v_list = []
    return_error_num = 0
    return_error_msg_list = []
    for _return_msg in return_msg_list:
        if _return_msg[0] is False:
            return_error_num += 1
            return_error_msg_list.append(_return_msg[1])
        else:
            v2v_list.append(_return_msg[1])
    # 只要有一个任务有错误，就返回
    if return_error_num > 0:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="任务检测有错误，无法进行v2v操作",
                                           data=return_error_msg_list)

    error_num = 0
    total_num = len(v2v_list)
    # 将入参的list按照group_id进行list分组
    group_list = _task_into_list(v2v_list)
    # 针对group分组后的list套用host筛选算法
    for task_list in group_list:
        tag1, res1 = _cal_group_host(task_list)
        # 算法分配失败
        if not tag1:
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=res1)
        else:
            # host筛选完成，进行入库操作
            for task in task_list:
                tag2, res2 = _task_esx_intodb(task)
                # 入库失败
                if not tag2:
                    error_num += 1

    # 统计总错误数
    if error_num == total_num:
        message = "全部失败"
        return_code = ErrorCode.ALL_FAIL
    elif error_num == 0:
        message = "全部成功"
        return_code = ErrorCode.SUCCESS
    else:
        message = "部分成功"
        return_code = ErrorCode.SUCCESS_PART
    return json_helper.format_api_resp(code=return_code, msg=message)


@login_required
def download_excel_esx():
    '''
        下载excel模板
    :return:
    '''
    file_name = "ESX批量迁移模板.xlsx"
    file_dir = DIR_DEFAULT + "/doc/v2v/esx/"
    return send_from_directory(file_dir, file_name, as_attachment=True)


def _check_task(i, row, user_id):
    # 当前行数
    cur_line = str(i + 1)

    # ESX ROOT密码
    esx_passwd = row[0]
    # ESX环境
    esx_env_name = row[1]
    # ESX IP
    esx_ip = row[2]
    # VM WARE虚拟机名称
    vmware_vm = row[3]
    # VM OS名称
    vm_os_name = row[4]
    # VM OS版本
    vm_os_version = row[5]
    # VM IP
    vm_ip = row[6]
    # 区域名
    area_name = row[7]
    # 机房名
    datacenter_name = row[8]
    # 网络区域名
    netarea_name = row[9]
    # 集群名
    hostpool_name = row[10]
    # VM网段
    vm_segment = row[11]
    # VM系统类型
    vm_ostype = row[12]
    # 应用系统信息
    vm_app_info = row[13]
    # 应用组
    group_name = row[14]
    # 应用管理员
    vm_owner = row[15]
    # CPU数量
    cpu_num = row[16]
    # 内存容量
    mem_size = row[17]
    # 内存容量单位
    mem_size_unit = row[18]

    if not esx_passwd or not esx_env_name or not esx_ip or not vmware_vm or not vm_os_name or not vm_os_version \
            or not vm_ip or not area_name or not datacenter_name or not netarea_name or not hostpool_name \
            or not vm_segment or not vm_ostype or not vm_app_info or not group_name or not vm_owner \
            or not cpu_num or not mem_size or not mem_size_unit:
        result = False, "第" + cur_line + "行：参数不正确"
        q.put(result)
        return

    # 1.判断flavor信息
    if mem_size_unit == 'G':
        mem_size_mb = int(mem_size) * 1024
    elif mem_size_unit == 'M':
        mem_size_mb = mem_size
    else:
        result = False, "第" + cur_line + "行：内存容量单位不正确"
        q.put(result)
        return

    flavor_info = flavor_s.get_flavor_by_vcpu_and_memory(cpu_num, mem_size_mb)
    if not flavor_info:
        result = False, "第" + cur_line + "行：实例规格数据有误"
        q.put(result)
        return

    # 2.根据机房类型、网络区域和集群名来判断集群信息
    if esx_env_name == "DEV":
        esx_env = "3"
    elif esx_env_name == "SIT":
        esx_env = "1"
    elif esx_env_name == "STG":
        esx_env = "2"
    elif esx_env_name == "PRD":
        esx_env = "4"
    elif esx_env_name == "DR":
        esx_env = "5"
    else:
        result = False, "第" + cur_line + "行：ESX环境数据有误"
        q.put(result)
        return

    hostpool_data = hostpool_s.get_hostpool_by_area_dc_env_netarea_hostpool(area_name, datacenter_name, esx_env,
                                                                            netarea_name, hostpool_name)
    if not hostpool_data:
        result = False, "第" + cur_line + "行：VM集群数据有误"
        q.put(result)
        return

    # 3.判断应用组信息
    group_info = group_s.get_group_info_by_name_and_env(group_name, esx_env)
    if not group_info:
        result = False, "第" + cur_line + "行：应用组数据有误"
        q.put(result)
        return

    # 4.开关机状态判断
    tag1, res1 = _vm_power_state(esx_ip, esx_passwd, vmware_vm)
    if not tag1:
        result = False, "第" + cur_line + "行：" + res1
        q.put(result)
        return

    # 5.vm磁盘大小获取
    tag2, res2 = _vm_disksize(esx_ip, esx_passwd, vmware_vm)
    if not tag2:
        result = False, "第" + cur_line + "行：" + res2
        q.put(result)
        return
    else:
        if vm_ostype == "Windows":
            vm_disk_temp = int(res2) - 50
            vm_disk = vm_disk_temp if vm_disk_temp >= 0 else 0
        else:
            vm_disk_temp = int(res2) - 30
            vm_disk = vm_disk_temp if vm_disk_temp >= 0 else 0

    # 6.组装信息
    _task = {
        'flavor_id': flavor_info['id'],
        'group_id': group_info['id'],
        'vm_disk': vm_disk,
        'vm_cpu': cpu_num,
        'vm_mem_mb': mem_size_mb,
        'hostpool_id': hostpool_data['hostpool_id'],
        'user_id': user_id,
        'vm_name': vm_os_name,
        'vm_segment': vm_segment,
        'vm_ip': vm_ip,
        'vm_owner': vm_owner,
        'vm_app_info': vm_app_info,
        'vm_ostype': vm_ostype,
        'esx_ip': esx_ip,
        'esx_passwd': esx_passwd,
        'esx_env': esx_env,
        'vmware_vm': vmware_vm,
        'vm_os_version': vm_os_version
    }
    result = True, _task
    q.put(result)


# vm电源状态判断
def _vm_power_state(esx_ip, esx_passwd, vm_name):
    try:
        c = SmartConnectNoSSL(host=esx_ip, user=OPENSTACK_DEV_USER, pwd=esx_passwd)
    except Exception as e:
        return False, "连接目标esxi失败"
    datacenter = c.content.rootFolder.childEntity[0]
    vms = datacenter.vmFolder.childEntity
    vmlist = []
    for i in vms:
        vmlist.append(i.name)
    if vm_name not in vmlist:
        return False, "ESXi中未找到目标vm"
    else:
        index = vmlist.index(vm_name)
        index_int = int(index)
        vm_state = vms[index_int].summary.runtime.powerState
        if not vm_state:
            Disconnect(c)
            return False, "获取vm状态失败"
        elif vm_state != "poweredOff":
            Disconnect(c)
            return False, "vm未关机"
        else:
            Disconnect(c)
            return True, "VM已关机"


# vm磁盘大小获取
def _vm_disksize(esx_ip, esx_passwd, vm_name):
    try:
        c = SmartConnectNoSSL(host=esx_ip, user=OPENSTACK_DEV_USER, pwd=esx_passwd)
    except Exception as e:
        return False, "连接目标esxi失败"
    datacenter = c.content.rootFolder.childEntity[0]
    vms = datacenter.vmFolder.childEntity
    vmlist = []
    for i in vms:
        vmlist.append(i.name)
    if vm_name not in vmlist:
        return False, "ESXi中未找到目标vm"
    else:
        index = vmlist.index(vm_name)
        index_int = int(index)
        vm_disk = vms[index_int].summary.storage.committed + vms[index_int].summary.storage.uncommitted
        if not vm_disk:
            Disconnect(c)
            return False, "获取vm磁盘大小失败"
        else:
            vm_disk_GB = vm_disk / 1024 / 1024 / 1024 + 1
            Disconnect(c)
            return True, vm_disk_GB


# 将入参list按照group_id分组函数
def _task_into_list(task_list):
    # 获取所有不重复的组ID
    group_id_list = []
    for _list in task_list:
        group_id_list.append(_list['group_id'])
    for value in group_id_list:
        while group_id_list.count(value) > 1:
            del group_id_list[group_id_list.index(value)]

    # 预先根据组数量初始化N个数组
    same_group_list = []
    for i in range(len(group_id_list)):
        temp_list = []
        same_group_list.append(temp_list)

    return_list = []
    num = 0
    for _group_id in group_id_list:
        # todo:改为只循环task_list
        for _task in task_list:
            if _task['group_id'] == long(_group_id):
                same_group_list[num].append(_task)
        return_list.append(same_group_list[num])
        num += 1

    return return_list


# 针对同一group_id的task list计算host list
def _cal_group_host(task_list):
    vm_mem_count = 0
    vm_disk_count = 0
    count = len(task_list)
    # 针对每个分组内的list，计算可用host list
    for task in task_list:
        flavor_id = task['flavor_id']
        vm_group_id = task['group_id']
        vm_disk = task["vm_disk"]
        hostpool_id = task['hostpool_id']
        vm_disk_total = int(vm_disk) + 50
        flavor_info = flavor_s.FlavorService().get_flavor_info(flavor_id)
        vmmem = flavor_info['memory_mb']
        vm_mem_count += int(vmmem)
        vm_disk_count += vm_disk_total
    code, data, msg = cal_host_batch(hostpool_id, vm_mem_count, vm_disk_count, vm_group_id, count)
    if code < 0:
        return False, msg
    else:
        host_list = data
        host_len = len(host_list)
        # 获取host list后，针对每个vm分配host
        task_len = len(task_list)
        for i in range(task_len):
            task_info = task_list[i]
            host_index = i % host_len
            vm_host = host_list[host_index]
            vm_host_ip = vm_host["ip"]
            task_info['dest_host'] = vm_host_ip
        return True, host_list


# vm单台入库函数
def _task_esx_intodb(task):
    # 获取vm入参
    vmname = task['vm_name']
    vmip = task['vm_ip']
    flavor_id = task['flavor_id']
    vm_ostype = task['vm_ostype']
    vm_app_info = task['vm_app_info']
    vm_owner = task['vm_owner']
    vm_segment = task['vm_segment']
    vm_group_id = task['group_id']
    dest_host = task['dest_host']

    vmhost = ho_s.HostService().get_host_info_by_hostip(dest_host)
    ret_4 = ho_s.pre_allocate_host_resource(vmhost['id'], task['vm_cpu'], task['vm_mem_mb'], 50)
    if ret_4 != 1:
        logging.error('资源预分配失败')
        message = '资源预分配失败'
        return False, message

    # 获取并录入IP信息
    vm_segment = seg_s.SegmentService().get_segment_info_bysegment(vm_segment)
    if vm_segment is None:
        message = '网段信息有误，无法进行v2v操作'
        return False, message
    else:
        segment_id = vm_segment['id']
        vm_netmask = vm_segment['netmask']
        vm_gateway = vm_segment['gateway_ip']
        vm_dns1 = vm_segment['dns1']
        vm_dns2 = vm_segment['dns2']
        vmvlan = vm_segment['vlan']
        ip_data = ip_s.IPService().get_ip_info_by_ipaddress(vmip)
        if ip_data is None:
            ip_data = {
                'ip_address': vmip,
                'segment_id': segment_id,
                'netmask': vm_netmask,
                'vlan': vmvlan,
                'gateway_ip': vm_gateway,
                'dns1': vm_dns1,
                'dns2': vm_dns2,
                'created_at': get_datetime_str(),
                'status': '1'
            }
            ret = ip_s.IPService().add_ip_info(ip_data)
            if ret.get('row_num') <= 0:
                logging.info('add ip info error when create v2v task, insert_data: %s', ip_data)
                message = "录入IP信息失败"
                return False, message
            else:
                ip_id = ret.get('last_id')
        else:
            ip_data_status = ip_data['status']
            vmvlan = ip_data['vlan']
            if ip_data_status != '0':
                message = "IP与现有环境冲突,无法进行v2v操作"
                return False, message
            else:
                ip_id = ip_data['id']
                where_data = {
                    'id': ip_id
                }
                updata_data = {
                    'status': '1',
                    'updated_at': get_datetime_str()
                }
                ret1 = ip_s.IPService().update_ip_info(updata_data, where_data)
                if not ret1:
                    logging.info('update ip info error when create v2v task, update_data: %s', updata_data)
                    message = "更新IP状态失败"
                    return False, message

        # 生成request_id
        request_id = v2v_op.generate_req_id()

        # 生成vm的uuid和mac
        vmuuid = randomUUID()
        vmmac = randomMAC()

        # 信息入instance相关库表
        instance_tag, instance_info = _instance_db_info(vmuuid, vmname, vm_app_info, vm_owner, flavor_id, vm_group_id,
                                                        dest_host, vmmac, task['vm_disk'], ip_id, vm_ostype, request_id,
                                                        task['vm_os_version'])
        if not instance_tag:
            message = instance_info
            return False, message

        # 将步骤信息存入instance_action表
        v2v_cd_d1 = {
            'action': esx_v2vActions.CREATE_DEST_DIR,
            'request_id': request_id,
            'message': 'start',
            'start_time': get_datetime_str()
        }
        in_a_s.InstanceActionsServices().add_instance_action_info(v2v_cd_d1)

        v2v_cr_pl = {
            'action': esx_v2vActions.CREATE_STOR_POOL,
            'request_id': request_id,
            'message': 'other',
            'start_time': get_datetime_str()
        }
        in_a_s.InstanceActionsServices().add_instance_action_info(v2v_cr_pl)

        v2v_cp_fl = {
            'action': esx_v2vActions.COPY_FILE_TO_LOCAL,
            'request_id': request_id,
            'message': 'other',
            'start_time': get_datetime_str()
        }
        in_a_s.InstanceActionsServices().add_instance_action_info(v2v_cp_fl)

        v2v_file = {
            'action': esx_v2vActions.VIRT_V2V_FILES,
            'request_id': request_id,
            'message': 'other',
            'start_time': get_datetime_str()
        }
        in_a_s.InstanceActionsServices().add_instance_action_info(v2v_file)

        v2v_del_tmp = {
            'action': esx_v2vActions.DELETE_TMP_FILE,
            'request_id': request_id,
            'message': 'other',
            'start_time': get_datetime_str()
        }
        in_a_s.InstanceActionsServices().add_instance_action_info(v2v_del_tmp)

        v2v_sysdisk_std = {
            'action': esx_v2vActions.VM_SYS_DISK_STD,
            'request_id': request_id,
            'message': 'other',
            'start_time': get_datetime_str()
        }
        in_a_s.InstanceActionsServices().add_instance_action_info(v2v_sysdisk_std)

        v2v_datadisk_std = {
            'action': esx_v2vActions.VM_DATA_DISK_STD,
            'request_id': request_id,
            'message': 'other',
            'start_time': get_datetime_str()
        }
        in_a_s.InstanceActionsServices().add_instance_action_info(v2v_datadisk_std)

        v2v_def_1 = {
            'action': esx_v2vActions.VM_DEFINE1,
            'request_id': request_id,
            'message': 'other',
            'start_time': get_datetime_str()
        }
        in_a_s.InstanceActionsServices().add_instance_action_info(v2v_def_1)

        v2v_star_1 = {
            'action': esx_v2vActions.VM_START1,
            'request_id': request_id,
            'message': 'other',
            'start_time': get_datetime_str()
        }
        in_a_s.InstanceActionsServices().add_instance_action_info(v2v_star_1)

        if vm_ostype == "Windows":
            v2v_att_disk = {
                'action': esx_v2vActions.ATTACH_DISK,
                'request_id': request_id,
                'message': 'other',
                'start_time': get_datetime_str()
            }
            in_a_s.InstanceActionsServices().add_instance_action_info(v2v_att_disk)

            v2v_win_std = {
                'action': esx_v2vActions.WINDOWS_STD,
                'request_id': request_id,
                'message': 'other',
                'start_time': get_datetime_str()
            }
            in_a_s.InstanceActionsServices().add_instance_action_info(v2v_win_std)

            v2v_vm_def2 = {
                'action': esx_v2vActions.WINDOWS_DISK_CH,
                'request_id': request_id,
                'message': 'other',
                'start_time': get_datetime_str()
            }
            in_a_s.InstanceActionsServices().add_instance_action_info(v2v_vm_def2)

            v2v_vm_star2 = {
                'action': esx_v2vActions.VM_START2,
                'request_id': request_id,
                'message': 'other',
                'start_time': get_datetime_str()
            }
            in_a_s.InstanceActionsServices().add_instance_action_info(v2v_vm_star2)

        # 将v2v信息存入v2v_task表
        v2v_data = {
            'source': VMCreateSource.ESX,
            'request_id': request_id,
            'destory': '0',
            'start_time': get_datetime_str(),
            'status': 0,
            'vm_ip': vmip,
            'vm_name': vmname,
            'vmvlan': vmvlan,
            'flavor_id': flavor_id,
            'cloud_area': task['esx_env'],
            'vm_ostype': vm_ostype,
            'vm_app_info': vm_app_info,
            'vm_owner': vm_owner,
            'vm_group_id': vm_group_id,
            'user_id': task['user_id'],
            'vm_mac': vmmac,
            'vm_uuid': vmuuid,
            'cancel': '0',
            'dest_dir': '/app/image/' + vmuuid,
            'on_task': '0',
            'dest_host': dest_host,
            'esx_ip': task['esx_ip'],
            'esx_passwd': task['esx_passwd'],
            'vmware_vm': task['vmware_vm'],
            'step_done': esx_v2vActions.BEGIN
        }
        v2v_insert = v2v_op.v2vTaskService().add_v2v_task_info(v2v_data)

        if v2v_insert.get('row_num') <= 0:
            logging.info('insert info to v2v_task failed! %s', v2v_data)
            message = '信息入库失败'
            return False, message

        message = '信息已添加至任务队列'
        return True, message


# instance信息入库函数
def _instance_db_info(uuid, vmname, vm_app_info, owner, flavor_id, group_id, host, mac, vmdisk, ip_id,
                     vmostype, requestid, ver_data):
    vm_ostype_todb = ''
    vmhost = ho_s.HostService().get_host_info_by_hostip(host)
    # 往instance表添加记录
    instance_data = {
        'uuid': uuid,
        'name': vmname,
        'displayname': vmname,
        'description': '',
        'status': VMStatus.CONVERTING,
        'typestatus': VMTypeStatus.NORMAL,
        'isdeleted': '0',
        'app_info': vm_app_info,
        'owner': owner,
        'created_at': get_datetime_str(),
        'create_source': VMCreateSource.ESX
    }
    ret = ins_s.InstanceService().add_instance_info(instance_data)
    if ret.get('row_num') <= 0:
        message = 'add instance info error when create instance'
        logging.info('add instance info error when create instance, insert_data: %s', instance_data)
        return False, message

    instance_id = ret.get('last_id')

    if vmostype == 'Windows':
        vm_ostype_todb = 'windows'
    elif vmostype == 'Linux':
        vm_ostype_todb = 'linux'

    # 往v2v_instance_info表添加记录
    v2v_instance_data = {
        'instance_id': instance_id,
        'os_type': vm_ostype_todb,
        'isdeleted': '0',
        'created_at': get_datetime_str(),
        'request_id': requestid,
        'os_version': ver_data
    }
    ret_v2v_instance = v2v_in_i.v2vInstanceinfo().add_v2v_instance_info(v2v_instance_data)
    if ret_v2v_instance.get('row_num') <= 0:
        logging.info('add v2v_instance info error when create instance, v2v_instance_data: %s',
                     v2v_instance_data)
        message = 'add v2v_instance info error when create instance'
        return False, message

    # 往instance_flavor表添加记录
    instance_flavor_data = {
        'instance_id': instance_id,
        'flavor_id': flavor_id,
        'created_at': get_datetime_str()
    }
    ret1 = ins_f_s.InstanceFlavorService().add_instance_flavor_info(instance_flavor_data)
    if ret1.get('row_num') <= 0:
        logging.info('add instance_flavor info error when create instance, insert_data: %s',
                     instance_flavor_data)
        message = 'add instance_flavor info error when create instance'
        return False, message

    # 往instance_group表添加记录
    instance_group_data = {
        'instance_id': instance_id,
        'group_id': group_id,
        'created_at': get_datetime_str()
    }
    ret2 = ins_g_s.InstanceGroupService().add_instance_group_info(instance_group_data)
    if ret2.get('row_num') <= 0:
        logging.info('add instance_group info error when create instance, insert_data: %s', instance_group_data)
        message = 'add instance_group info error when create instance'
        return False, message

    # 往instance_host表添加记录
    instance_host_data = {
            'instance_id': instance_id,
            'instance_name': vmname,
            'host_id': vmhost['id'],
            'host_name': vmhost['name'],
            'isdeleted': '0',
            'created_at': get_datetime_str()
    }
    ret3 = ins_h_s.InstanceHostService().add_instance_host_info(instance_host_data)
    if ret3.get('row_num') <= 0:
        logging.info('add instance_host info error when create instance, insert_data: %s', instance_host_data)
        message = 'add instance_host info error when create instance'
        return False, message

    # 往instance_ip表添加记录
    instance_ip_data = {
            'instance_id': instance_id,
            'ip_id': ip_id,
            'mac': mac,
            'type': InstanceNicType.MAIN_NETWORK_NIC,
            'isdeleted': '0',
            'created_at': get_datetime_str()
    }
    ret4= ins_ip_s.InstanceIPService().add_instance_ip_info(instance_ip_data)
    if ret4.get('row_num') <= 0:
        logging.info('add instance_ip info error when create instance, insert_data: %s', instance_ip_data)
        message = 'add instance_ip info error when create instance'
        return False, message

    # 往instance_disk表添加记录
    instance_disk_data = {
            'instance_id': instance_id,
            'size_gb': vmdisk,
            'mount_point': '',
            'dev_name': '',
            'isdeleted': '0',
            'created_at': get_datetime_str()
    }
    ret5 = ins_d_s.InstanceDiskService().add_instance_disk_info(instance_disk_data)
    if ret5.get('row_num') <= 0:
        logging.info('add instance_disk info error when create instance, insert_data: %s',
                     instance_disk_data)
        message = 'add instance_disk info error when create instance'
        return False, message
    message = "信息入库完成"
    return True, message