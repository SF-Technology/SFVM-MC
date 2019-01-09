# coding=utf8
'''
    Openstack导入excel批量迁移
'''
# __author__ = 'lisiyuan'

from pyexcel_xls import get_data
from helper import json_helper
from flask import request, send_from_directory
from model.const_define import ErrorCode, v2vActions, VMStatus, VMTypeStatus, VMCreateSource, IPStatus, InstanceNicType
from config.default import OPENSTACK_DEV_PASS, OPENSTACK_SIT_PASS, OPENSTACK_DEV_USER, DIR_DEFAULT
from helper.encrypt_helper import decrypt
from lib.shell.ansibleCmdV2 import ansible_run
import logging
from helper.time_helper import get_datetime_str
from lib.vrtManager.util import randomUUID, randomMAC
from service.v2v_task import v2v_task_service as v2v_op
from service.s_host import host_service as ho_s
from service.s_instance_action import instance_action as in_a_s
from service.s_instance import instance_host_service as ins_h_s, instance_ip_service as ins_ip_s, \
    instance_disk_service as ins_d_s, instance_service as ins_s, \
    instance_flavor_service as ins_f_s, instance_group_service as ins_g_s
from service.v2v_task import v2v_instance_info as v2v_in_i
from service.s_ip import ip_service as ip_s, segment_service as segment_s
from service.s_flavor import flavor_service as flavor_s
from service.s_group import group_service as group_s
from service.s_user.user_service import get_user
from service.s_hostpool import hostpool_service as hostpool_s
from cal_dest_host_batch import calc_dest_host_batch as cal_host_batch
import os
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
import threading
import Queue
import sys
sys.setdefaultencoding('utf8')

q = Queue.Queue()


@login_required
def import_excel_openstack():
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
    # 将入参的list按照group_id进行list分组
    group_list = _task_into_list(v2v_list)
    total_num = len(v2v_list)
    return_list = []
    # 针对group分组后的list套用host筛选算法
    for task_list in group_list:

        tag1, task_list = _cal_group_host(task_list)
        # 如果同group下list套用host算法失败，则将这部分task存入returnlist
        for task in task_list:
            if task.get('error_message'):
                return_list.append(task)

        """
        tag1, res1 = _cal_group_host(task_list)
        # 如果同group下list套用host算法失败，则将这部分task存入returnlist
        if not tag1:
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=res1)
        else:
            # host筛选完成，进行入库操作
            for task in task_list:
                tag2, res2 = _task_into_db(task)
                # 如果入库失败，则存入returnlist
                if not tag2:
                    error_num += 1
        """

    # 统计总错误数
    error_num = len(return_list)
    if error_num == total_num:
        message = "全部失败"
        return_code = ErrorCode.ALL_FAIL
    elif error_num == 0:
        message = "全部成功"
        return_code = ErrorCode.SUCCESS
    else:
        message = "部分成功"
        return_code = ErrorCode.SUCCESS_PART
    return json_helper.format_api_resp(code=return_code, msg=message, data=return_list)


def _check_task(i, row, user_id):
    # 当前行数
    cur_line = str(i + 1)

    # Openstack环境
    cloud_area = row[0]
    cloud_area = cloud_area.strip()
    # VM名称
    vm_name = row[1]
    vm_name = vm_name.strip()
    # VM IP
    vm_ip = row[2]
    vm_ip = vm_ip.strip()
    # VM所在网段
    vm_segment = row[3]
    vm_segment = vm_segment.strip()
    # 应用系统信息
    vm_app_info = row[4]
    vm_app_info = vm_app_info.strip()
    # 应用管理员
    vm_owner = row[5]
    vm_owner = vm_owner.strip()
    # VM环境
    vm_env_name = row[6]
    vm_env_name = vm_env_name.strip()
    # VM网络区域
    netarea_name = row[7]
    netarea_name = netarea_name.strip()
    # VM集群
    hostpool_name = row[8]
    hostpool_name = hostpool_name.strip()
    # VM系统版本
    vm_ostype = row[9]
    vm_ostype = vm_ostype.strip()
    # 应用组
    group_name = row[10]
    group_name = group_name.strip()
    # CPU数量
    cpu_num = row[11]
    cpu_num = cpu_num.strip()
    # 内存容量
    mem_size = row[12]
    mem_size = mem_size.strip()
    # 内存容量单位
    mem_size_unit = row[13]
    mem_size_unit = mem_size_unit.strip()

    if not cloud_area or not vm_name or not vm_ip or not vm_segment or not vm_app_info or not vm_owner \
            or not vm_env_name or not netarea_name or not hostpool_name or not vm_ostype or not group_name \
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
    if vm_env_name == "DEV":
        vm_env = "3"
    elif vm_env_name == "SIT":
        vm_env = "1"
    elif vm_env_name == "STG":
        vm_env = "2"
    else:
        result = False, "第" + cur_line + "行：VM环境数据有误"
        q.put(result)
        return

    hostpool_data = hostpool_s.get_hostpool_by_vmenv_netarea_hostpool(vm_env, netarea_name, hostpool_name)
    if not hostpool_data:
        result = False, "第" + cur_line + "行：VM集群数据有误"
        q.put(result)
        return

    # 3.判断应用组信息

    group_info = group_s.get_group_info_by_name_and_env(group_name,vm_env)
    if not group_info:
        result = False, "第" + cur_line + "行：应用组数据有误"
        q.put(result)
        return

    # 4.获取并录入IP信息
    vm_segment_info = segment_s.SegmentService().get_segment_info_bysegment(vm_segment)
    if vm_segment_info is None:
        result = False, "第" + cur_line + "行：网段信息有误"
        q.put(result)
        return
    else:
        ip_data = ip_s.IPService().get_ip_info_by_ipaddress(vm_ip)
        if ip_data:
            if str(ip_data['status']) != IPStatus.UNUSED:
                result = False, "第" + cur_line + "行：IP与现有环境冲突"
                q.put(result)
                return

    # 5.获取对应openstack环境的管理节点及ssh账户信息
    if cloud_area == "SIT":
        ctr_host = "10.202.83.12"
        ctr_pass = decrypt(OPENSTACK_SIT_PASS)
    elif cloud_area == "DEV":
        ctr_host = "10.202.123.4"
        ctr_pass = decrypt(OPENSTACK_DEV_PASS)
    else:
        result = False, "第" + cur_line + "行：openstack环境参数错误"
        q.put(result)
        return

    # 6.判断vm信息是否输入错误
    vmexist = _vm_exist(vm_ip, ctr_host, ctr_pass)
    if not vmexist:
        result = False, "第" + cur_line + "行：获取vm信息失败"
        q.put(result)
        return

    # 7.获取OS版本失败
    osstat, verdata = _get_vm_version(ctr_host, ctr_pass, vm_ostype, vm_ip)
    if not osstat:
        result = False, "第" + cur_line + "行：获取vm OS版本失败"
        q.put(result)
        return

    # 8.获取待迁移vm磁盘大小
    vdiskdata = _vm_disk_size(vm_ip, ctr_host, ctr_pass)
    if not vdiskdata:
        result = False, "第" + cur_line + "行：获取vm磁盘信息失败"
        q.put(result)
        return

    data_disk = vdiskdata - 80

    # 9.判断待转化vm是否关机
    vmshutdown = _vm_state(vm_ip, ctr_host, ctr_pass)
    if not vmshutdown:
        result = False, "第" + cur_line + "行：待转化vm未关机"
        q.put(result)
        return

    # 10.判断主机名是否包含中文
    check_chinese,msg = _check_chinese(vm_name)
    if not check_chinese:
        err_msg = "第" + cur_line + "行:"+ msg
        result = False, err_msg
        q.put(result)
        return



    # 11.组装信息
    _task = {
        'vm_name': vm_name,
        'vm_ip': vm_ip,
        'flavor_id': flavor_info['id'],
        'cloud_area': cloud_area,
        'vm_ostype': vm_ostype,
        'vm_app_info': vm_app_info,
        'vm_owner': vm_owner,
        'hostpool_id': hostpool_data['hostpool_id'],
        'group_id': group_info['id'],
        'user_id': user_id,
        'segment': vm_segment,
        'vm_disk': data_disk,
        'vm_osver': verdata,
    }
    result = True, _task
    q.put(result)


@login_required
def download_excel_openstack():
    '''
        下载excel模板
    :return:
    '''
    file_name = "Openstack批量迁移模板.xlsx"
    file_dir = DIR_DEFAULT + "/doc/v2v/openstack/"
    return send_from_directory(file_dir, file_name, as_attachment=True)


# 判断虚拟机是否输入错误
def _vm_exist(vmip, host, host_pass):
    command = "/usr/bin/vmop " + vmip + " |grep id"
    remote_user = OPENSTACK_DEV_USER
    become_user = OPENSTACK_DEV_USER
    remote_pass = host_pass
    become_pass = host_pass
    ctrhost = host
    vmexist = ansible_run(ctrhost, command, remote_user, remote_pass, become_user, become_pass, 10)
    if vmexist['contacted'] == {}:
        return False
    elif 'failed' in vmexist['contacted'][ctrhost]:
        return False
    elif vmexist['contacted'][ctrhost]['stdout'] == '':
        return False
    else:
        return True


# 获取vm os版本
def _get_vm_version(ctrhost, ctrpass, vmostype, vmip):
    command = "vmop " + vmip + "|grep image|cut -d '|' -f 3|cut -d ' ' -f 2"
    remote_user = OPENSTACK_DEV_USER
    become_user = OPENSTACK_DEV_USER
    remote_pass = ctrpass
    become_pass = ctrpass
    host = ctrhost
    osversion = ansible_run(host, command, remote_user, remote_pass, become_user, become_pass, 20)
    print osversion['contacted']
    if osversion['contacted'] == {}:
        msg = '获取vmOS版本失败'
        return False, msg
    elif 'failed' in osversion['contacted'][host]:
        msg = '获取vmOS版本失败'
        return False, msg
    else:
        osversion_s = osversion['contacted'][host]['stdout']
        if vmostype == "Windows":
            if '2008' in osversion_s:
                version_res = '2008'
            elif '2012' in osversion_s:
                version_res = '2012'
            elif 'win7' in osversion_s:
                version_res = 'win7'
            else:
                version_res = 'windows'
            return True, version_res
        elif vmostype == "Linux":
            if ('centos' or 'RHEL') in osversion_s:
                if '6.6' in osversion_s:
                    version_res = '6.6'
                elif '7.2'in osversion_s:
                    version_res = '7.2'
                else:
                    version_res = 'centos'

            elif 'ubuntu' in osversion_s:
                version_res = 'ubuntu'
            elif 'debian' in osversion_s:
                version_res = 'debian'
            else:
                version_res = 'unknown'
            return True, version_res


# 获取待转化vm的数据盘大小
def _vm_disk_size(vmip, host, host_pass):
    command = "/usr/bin/vmop " + vmip + " data_volume"
    remote_user = OPENSTACK_DEV_USER
    become_user = OPENSTACK_DEV_USER
    remote_pass = host_pass
    become_pass = host_pass
    ctrhost = host
    vmdisksize = ansible_run(ctrhost, command, remote_user, remote_pass, become_user, become_pass, 10)
    if vmdisksize['contacted'] == {}:
        return False
    elif 'failed' in vmdisksize['contacted'][ctrhost]:
        return False
    else:
        disk_size = int(vmdisksize['contacted'][ctrhost]['stdout']) + 80
        return disk_size


# 判断vm是否关机
def _vm_state(vmip, host, host_pass):
    command = "/usr/bin/vmop " + vmip + " |grep 'vm_state'|grep 'stopped'"
    remote_user = OPENSTACK_DEV_USER
    become_user = OPENSTACK_DEV_USER
    remote_pass = host_pass
    become_pass = host_pass
    ctrhost = host
    vmstat = ansible_run(ctrhost, command, remote_user, remote_pass, become_user, become_pass, 10)
    if vmstat['contacted'] == {}:
        return False
    elif 'failed' in vmstat['contacted'][ctrhost]:
        return False
    elif vmstat['contacted'][ctrhost]['stdout'] == '':
        return False
    else:
        return True


# 单个task的入库函数
def _task_into_db(task):
    # 入参赋值
    vmname = task['vm_name']
    vmip = task['vm_ip']
    flavor_id = task['flavor_id']
    cloudarea = task['cloud_area']
    vm_ostype = task['vm_ostype']
    vm_app_info = task['vm_app_info']
    vm_owner = task['vm_owner']
    vm_group_id = task['group_id']
    user_id = task['user_id']
    vm_segment = task['segment']
    vm_disk = task['vm_disk']
    vm_osver = task['vm_osver']
    host = task['dest_host']

    # 入参完全性判断
    if not vmname or not vmip or not flavor_id or not cloudarea or not vm_ostype \
            or not vm_app_info or not vm_owner or not vm_group_id or not user_id or not vm_segment:
        logging.info('params are invalid or missing')
        message = '入参缺失'
        return False, message
    else:
        # 获取flavor信息
        flavor_info = flavor_s.FlavorService().get_flavor_info(flavor_id)
        if not flavor_info:
            logging.info('id: %s flavor info not in db when create instance', flavor_id)
            message = '实例规格数据有误，无法进行v2v'
            return False, message
        vmcpu = flavor_info['vcpu']
        vmmem = flavor_info['memory_mb']

        vmhost = ho_s.HostService().get_host_info_by_hostip(host)
        ret_4 = ho_s.pre_allocate_host_resource(vmhost['id'], vmcpu, vmmem, 50)
        if ret_4 != 1:
            logging.error('资源预分配失败')
            message = '资源预分频失败'
            return False, message

        # 获取并录入IP信息
        vm_segment = segment_s.SegmentService().get_segment_info_bysegment(vm_segment)
        if vm_segment is None:
            message = '网段信息有误，无法进行v2v'
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
                    message = "IP与现有环境冲突,无法进行v2v"
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
                                                        host, vmmac, vm_disk, ip_id, vm_ostype, request_id, vm_osver)
        if not instance_tag:
            message = instance_info
            return False, message

        # 将步骤信息存入instance_action表
        # 将createdir信息存入instance_action表
        v2v_cd_d1 = {
            'action': v2vActions.CREATE_DEST_DIR,
            'request_id': request_id,
            'message': 'start',
            'start_time': get_datetime_str()
        }
        in_a_s.InstanceActionsServices().add_instance_action_info(v2v_cd_d1)

        # 将getfile信息存入instance_action表
        v2v_gf_d1 = {
            'action': v2vActions.GET_VM_FILE,
            'request_id': request_id,
            'message': 'other',
            'start_time': get_datetime_str()
        }
        in_a_s.InstanceActionsServices().add_instance_action_info(v2v_gf_d1)

        # 将copy disk信息存入instance_action表
        v2v_cpd_d1 = {
            'action': v2vActions.COPY_VM_DISK,
            'request_id': request_id,
            'message': 'other',
            'start_time': get_datetime_str()
        }
        in_a_s.InstanceActionsServices().add_instance_action_info(v2v_cpd_d1)

        # 将copy xml信息存入instance_action表
        v2v_cpx_d1 = {
            'action': v2vActions.COPY_VM_XML,
            'request_id': request_id,
            'message': 'other',
            'start_time': get_datetime_str()
        }
        in_a_s.InstanceActionsServices().add_instance_action_info(v2v_cpx_d1)

        # 将创建存储池信息存入instance_action表
        v2v_csp_d1 = {
            'action': v2vActions.CREATE_STOR_POOL,
            'request_id': request_id,
            'message': 'other',
            'start_time': get_datetime_str()
        }
        in_a_s.InstanceActionsServices().add_instance_action_info(v2v_csp_d1)

        # 将vm标准化信息存入instance_action表
        v2v_vmd_d1 = {
            'action': v2vActions.VM_STANDARDLIZE,
            'request_id': request_id,
            'message': 'other',
            'start_time': get_datetime_str()
        }
        in_a_s.InstanceActionsServices().add_instance_action_info(v2v_vmd_d1)

        # 将vm注册信息存入instance_action表
        v2v_vmdef_d1 = {
            'action': v2vActions.VM_DEFINE,
            'request_id': request_id,
            'message': 'other',
            'start_time': get_datetime_str()
        }
        in_a_s.InstanceActionsServices().add_instance_action_info(v2v_vmdef_d1)

        # 将IP注入信息存入instance_action表
        v2v_vmipj_d1 = {
            'action': v2vActions.IP_INJECT,
            'request_id': request_id,
            'message': 'other',
            'start_time': get_datetime_str()
        }
        in_a_s.InstanceActionsServices().add_instance_action_info(v2v_vmipj_d1)

        # 将vm开机信息存入instance_action表
        v2v_vmstar_d1 = {
            'action': v2vActions.VM_START,
            'request_id': request_id,
            'message': 'other',
            'start_time': get_datetime_str()
        }
        in_a_s.InstanceActionsServices().add_instance_action_info(v2v_vmstar_d1)

        message = '信息已添加至任务队列,等待执行'

        # 将v2v信息存入v2v_task表
        v2v_data = {
            'request_id': request_id,
            'destory': '0',
            'start_time': get_datetime_str(),
            'status': 0,
            'vm_ip': vmip,
            'vm_name': vmname,
            'vmvlan': vmvlan,
            'flavor_id': flavor_id,
            'cloud_area': cloudarea,
            'vm_ostype': vm_ostype,
            'vm_app_info': vm_app_info,
            'vm_owner': vm_owner,
            'vm_group_id': vm_group_id,
            'user_id': user_id,
            'vm_mac': vmmac,
            'vm_uuid': vmuuid,
            'cancel': '0',
            'dest_dir': '/app/image/' + vmuuid,
            'on_task': '0',
            'port': '10000',
            'source': VMCreateSource.OPENSTACK
        }
        v2v_insert = v2v_op.v2vTaskService().add_v2v_task_info(v2v_data)

        if v2v_insert.get('row_num') <= 0:
            logging.info('insert info to v2v_task failed! %s', v2v_data)
            message = '信息入库失败'
            return False, message

        # 将目标kvmhost存入信息表
        v2v_op.update_v2v_desthost(request_id, host)

        v2v_op.update_v2v_step(request_id, v2vActions.BEGIN)
        return True, message


# 信息入库函数
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
        'create_source':VMCreateSource.OPENSTACK
    }
    ret = ins_s.InstanceService().add_instance_info(instance_data)
    if ret.get('row_num') <= 0:
        logging.info('add instance info error when create instance, insert_data: %s', instance_data)
        message = 'add instance info error when create instance'
        return False,message

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
    ret4 = ins_ip_s.InstanceIPService().add_instance_ip_info(instance_ip_data)
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
        logging.info('add instance_disk info error when create instance, insert_data: %s', instance_disk_data)
        message = 'add instance_disk info error when create instance'
        return False, message

    message = "信息入库成功"
    return True, message


# 将入参list按照group_id分组函数
def _task_into_list(task_list):
    # 获取所有不重复的组ID
    group_id_list = []
    for _list in task_list:
        group_id_list.append(_list['group_id'])
    for _group_id in group_id_list:
        while group_id_list.count(_group_id) > 1:
            del group_id_list[group_id_list.index(_group_id)]

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
    # 针对每个分组内的list，计算可用host list
    for task in task_list:
        flavor_id = task['flavor_id']
        vm_group_id = task['group_id']
        vm_disk = task["vm_disk"]
        hostpool_id = task['hostpool_id']
        vm_disk_total = int(vm_disk) + 50
        flavor_info = flavor_s.FlavorService().get_flavor_info(flavor_id)
        vm_mem = flavor_info['memory_mb']
        code, data, msg = cal_host_batch(hostpool_id, vm_mem, vm_disk_total, vm_group_id, 1)
        if code < 0:
            task["error_message"] = msg
        else:
            host_list = data
            vm_host = host_list[0]
            task['dest_host'] = vm_host["ip"]
            res_task_intodb, msg_task_intodb = _task_into_db(task)
            if not res_task_intodb:
                task["error_message"] = msg_task_intodb

    return True, task_list


# 判断输入中是否包含中文
def _check_chinese(input_str):
    Chinese_tag = False
    for str in input_str.decode('utf-8'):
        if u'\u4e00' <= str <= u'\u9fff':
            Chinese_tag = True
            break
    if not Chinese_tag:
        message = '中文检测通过,不含中文'
        return True,message
    else:
        message = 'vm %s 名称含有中文字符,请修改后导入' %input_str
        return False,message

