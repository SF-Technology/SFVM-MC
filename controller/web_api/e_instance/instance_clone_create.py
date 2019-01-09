# coding=utf8
'''
    clone_create_intodb
'''
# __author__ =  ""

from flask import request
import threading
from libvirt import libvirtError
from helper import encrypt_helper, json_helper
from config.default import INSTANCE_MAX_CREATE
import logging
import time
import Queue
import random
from lib.other import fileLock
from lib.shell import ansibleCmdV2
from model.const_define import ErrorCode, IPStatus, VMStatus, VMTypeStatus, ImageType, VMCreateSource, DataCenterType,\
    OperationObject, OperationAction, IpLockStatus, NetCardType, InstanceNicType, InstanceCloneCreateTransType
from lib.vrtManager import instanceManager as vmManager
from helper.time_helper import get_datetime_str
from lib.mq.kafka_client import send_async_msg
from lib.vrtManager.util import randomUUID, randomMAC
from service.s_instance import instance_service as ins_s
from service.s_instance import instance_disk_service as ins_d_s
from service.s_instance import instance_flavor_service as ins_f_s
from service.s_instance import instance_group_service as ins_g_s
from service.s_instance import instance_host_service as ins_h_s
from service.s_instance import instance_image_service as ins_i_s
from service.s_instance import instance_ip_service as ins_ip_s
from service.s_instance import instance_clone_create as ins_c_c
from service.s_ip import ip_service
from service.s_host import host_service as host_s, host_schedule_service as host_s_s
from service.s_hostpool import hostpool_service
from service.s_user import user_service as user_s
from service.s_image import image_service
from service.s_user.user_service import get_user
from service.s_flavor import flavor_service as flavor_s
from web_api.e_instance.instance_create import _check_instance_name_resource
from service.s_ip import segment_match as segment_m
from service.s_ip import segment_service as segment_s
from service.s_ip import ip_lock_service as ip_l_s
from web_api.e_instance.instance_clone import _check_group_quota
import paramiko
from config import KAFKA_TOPIC_NAME
import socket
from config.default import ANSIABLE_REMOTE_USER,CLONE_TORR_PORT,\
    ANSIABLE_REMOTE_PWD,TRACKER_SERVER,TRACKER_SERVER_PORT,TORRENT_DIR
from service.s_operation.operation_service import add_operation_vm

# #定义MyThread类用于接收每个子线程的返回值
# class MyThread(threading.Thread):
#
#     def __init__(self,func,args=()):
#         super(MyThread,self).__init__()
#         self.func = func
#         self.args = args
#
#     def run(self):
#         self.result = self.func(*self.args)
#
#     def get_result(self):
#         try:
#             return self.result  # 如果子线程不使用join方法，此处可能会报没有self.result的错误
#         except Exception:
#             return None

q = Queue.Queue()


@add_operation_vm(OperationObject.VM, OperationAction.CLONE_CREATE)
def clone_create_intodb():
    '''
            克隆创建vm
        :param :
        :return:
        '''
    instance_name = request.values.get('instance_name')
    hostpool_id = request.values.get('hostpool_id')
    instance_id = request.values.get('instance_id')
    flavor_id = request.values.get('flavor_id')
    count = request.values.get('count')
    app_info = request.values.get('app_info')
    group_id = request.values.get('group_id')
    owner = request.values.get('owner')
    task_id = ins_s.generate_task_id()
    password_en = request.values.get('password')
    #------------------------------------入参完整性判断------------------------------------------
    if not instance_name or not hostpool_id or not instance_id or not flavor_id \
        or not count or not app_info or not group_id or not owner or int(count) < 1:
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg='入参缺失')
    instance_info = ins_s.InstanceService().get_instance_info(instance_id)
    instance_status = instance_info['status']
    source_vm_uuid = instance_info['uuid']
    if instance_status != '1':
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='VM未关机无法用于克隆创建')
    instance_source = instance_info['create_source']
    if instance_source != '0':
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='V2V机器无法用于克隆创建')

    instance_image1 = ins_i_s.get_ins_image_info_by_ins_id(instance_id)
    image_id1 = instance_image1['image_id']
    image_data_t1 = image_service.ImageService().get_image_info(image_id1)
    instance_system1 = image_data_t1['system']
    if instance_system1 != "linux":
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='非linux系统vm无法用于克隆创建')

    if password_en != '':
        password_de = str(password_en)
    else:
        password_de = ''

    #将克隆源vm状态改成被克隆中
    where_data = {
        'id': int(instance_id)
    }
    update_data = {
        'status': '103'
    }
    ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)


    #---------------------------------------资源分配-----------------------------------------------
    ins_flavor_data = ins_s.get_flavor_of_instance(instance_id)
    if ins_flavor_data:
        # 需要统计系统盘和数据盘总大小
        src_instance_sys_disk_size = ins_flavor_data['root_disk_gb']
        data_disk_status, src_instance_data_disk_size = ins_s.get_data_disk_size_of_instance(instance_id)
        if data_disk_status:
            src_instance_disk_size = int(src_instance_data_disk_size) + int(src_instance_sys_disk_size)
            ins_flavor_data['src_instance_disk_size'] = src_instance_disk_size
        else:
            logging.info('get instance data disk size error when clone instance')
            # 将克隆源vm状态改成关机
            where_data = {
                'id': int(instance_id)
            }
            update_data = {
                'status': '1'
            }
            ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
            return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="参数错误")
    else:
        logging.info('no instance flavor information find in db when clone instance')
        # 将克隆源vm状态改成关机
        where_data = {
            'id': int(instance_id)
        }
        update_data = {
            'status': '1'
        }
        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="参数错误")

    if int(count) > int(INSTANCE_MAX_CREATE):
        logging.error('克隆准备步骤：检查参数失败 批量创建数超过最大数 '
                      'task %s : create count %s > max num %s when clone instance',
                      task_id, count, INSTANCE_MAX_CREATE)
        # 将克隆源vm状态改成关机
        where_data = {
            'id': int(instance_id)
        }
        update_data = {
            'status': '1'
        }
        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
        err_msg = "批量创建最大实例数不能超过" + str(INSTANCE_MAX_CREATE)
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR,msg=err_msg)

    owner_exist = user_s.UserService().check_userid_exist(owner)
    if not owner_exist:
        logging.error('克隆准备步骤：检查参数失败 应用管理员工号不存在 '
                      'task %s : no such user %s in db when clone instance', task_id, owner)
        # 将克隆源vm状态改成关机
        where_data = {
            'id': int(instance_id)
        }
        update_data = {
            'status': '1'
        }
        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='应用管理员工号不存在，无法创建实例')
    vm_disk_gb = int(src_instance_disk_size) if int(src_instance_disk_size) > 50 else 50
    # 实例操作系统
    instance_image = ins_i_s.get_ins_image_info_by_ins_id(instance_id)
    if not instance_image:
        logging.info('克隆准备步骤：获取VM镜像信息失败 '
                     'task %s : get instance %s image info failed', task_id, instance_name)
        # 将克隆源vm状态改成关机
        where_data = {
            'id': int(instance_id)
        }
        update_data = {
            'status': '1'
        }
        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='获取VM镜像信息失败')


    # 获取镜像信息
    image_id = instance_image['image_id']
    image_data_t = image_service.ImageService().get_image_info(image_id)
    image_name =  image_data_t['name']
    image_nums, image_data = image_service.ImageService().get_images_by_name(image_name)
    if not image_data :
        logging.info('克隆准备步骤：获取VM镜像信息失败 '
                     'task %s : get instance %s image info failed', task_id, instance_name)
        # 将克隆源vm状态改成关机
        where_data = {
            'id': int(instance_id)
        }
        update_data = {
            'status': '1'
        }
        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='获取VM镜像信息失败')
    instance_system = image_data_t['system']
    logging.info('克隆准备步骤：VM信息获取成功 task %s : get vm info success', task_id)

    # 获取hostpool的net area信息
    hostpool_info = hostpool_service.HostPoolService().get_hostpool_info(hostpool_id)
    if not hostpool_info:
        logging.error('克隆准备步骤：获取必需信息失败 物理机池所属网络区域信息有误 '
                      'task %s : hostpool %s info not in db when create instance', task_id, hostpool_id)
        # 将克隆源vm状态改成关机
        where_data = {
            'id': int(instance_id)
        }
        update_data = {
            'status': '1'
        }
        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='物理机池所属网络区域信息有误，无法创建实例')

    net_area_id = hostpool_info['net_area_id']
    logging.info('创建VM 步骤4：获取必需信息成功 task %s : get need info successful when create instance', task_id)

    # 组配额控制
    is_quota_enough = _check_group_quota(group_id, ins_flavor_data, int(count))
    if not is_quota_enough:
        logging.error('group %s is no enough quota when create instance', group_id)
        # 将克隆源vm状态改成关机
        where_data = {
            'id': int(instance_id)
        }
        update_data = {
            'status': '1'
        }
        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='应用组配额已不够，无法创建实例')

    logging.info('创建VM 步骤5：检查组配额成功 task %s : check group quota successful when create instance', task_id)

    instance_db_info = ins_s.InstanceService().get_instance_info(instance_id)
    instance_host_db_info = ins_s.get_host_of_instance(instance_id)
    instance_image_db_info = ins_s.get_images_of_clone_instance(instance_id)
    instance_disks_db_info = ins_s.get_full_disks_info_of_instance(instance_id)


    if not instance_db_info or not instance_host_db_info or not instance_image_db_info or not instance_disks_db_info:
        logging.error('can not get instance %s info', instance_id)
        # 将克隆源vm状态改成关机
        where_data = {
            'id': int(instance_id)
        }
        update_data = {
            'status': '1'
        }
        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='无法获取待克隆虚拟机信息')

    # 查看原虚拟机是否关机
    src_instance_name = instance_db_info['name']
    host_ip = instance_host_db_info['ipaddress']
    vm_status = vmManager.libvirt_instance_status(host_ip, src_instance_name)
    if vm_status == -100 or vm_status != 5:
        logging.error('instance %s is not in poweroff status', instance_id)
        # 将克隆源vm状态改成关机
        where_data = {
            'id': int(instance_id)
        }
        update_data = {
            'status': '1'
        }
        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='虚拟机未关机，请确定虚拟机状态')



    logging.info('克隆准备步骤：获取并分配HOST资源 task %s : begin to prep host resource', task_id)
    # 获取主机列表(不包括锁定、维护状态)
    logging.info('克隆准备步骤：获取集群所有HOST列表 '
                 'task %s : get all hosts in hostpool %s start when create instance', task_id, hostpool_id)
    all_hosts_nums, all_hosts_data = host_s.HostService().get_available_hosts_of_hostpool(hostpool_id)
    # 可用物理机数量不足
    least_host_num = hostpool_service.HostPoolService().get_least_host_num(hostpool_id)
    if all_hosts_nums < least_host_num or all_hosts_nums < 1:
        logging.error('克隆准备步骤：获取集群所有HOST列表失败 集群不够资源 '
                      'task %s : available host resource not enough when create instance', task_id)
        # 将克隆源vm状态改成关机
        where_data = {
            'id': int(instance_id)
        }
        update_data = {
            'status': '1'
        }
        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='集群不够资源，无法创建实例')
    logging.info('克隆准备步骤：获取集群所有HOST列表成功，总host数：%s '
                 'task %s : get all hosts in hostpool %s successful, all hosts nums %s when create instance',
                 all_hosts_nums, task_id, hostpool_id, all_hosts_nums)

    # 过滤host
    logging.info('克隆准备步骤：HOST过滤 task %s : filter hosts start when create instance', task_id)
    hosts_after_filter = host_s_s.filter_hosts(all_hosts_data)
    if len(hosts_after_filter) == 0 or len(hosts_after_filter) < least_host_num:
        logging.error('克隆准备步骤：HOST过滤失败 没有合适主机 '
                      'task %s : no available host when create instance', task_id)
        # 将克隆源vm状态改成关机
        where_data = {
            'id': int(instance_id)
        }
        update_data = {
            'status': '1'
        }
        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='没有适合的主机，无法创建实例')
    logging.info('克隆准备步骤：HOST过滤成功 task %s : filter hosts successful when create instance', task_id)

    req_flavor_data = flavor_s.FlavorService().get_flavor_info(flavor_id)
    if not req_flavor_data:
        logging.error('克隆准备步骤：获取新配置信息失败 '
                      'task %s : flavor %s can not find in db', task_id, str(flavor_id))
        # 将克隆源vm状态改成关机
        where_data = {
            'id': int(instance_id)
        }
        update_data = {
            'status': '1'
        }
        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='获取新配置信息失败')

    # VM分配给HOST
    logging.info('克隆准备步骤：HOST分配 task %s : match hosts start when create instance', task_id)
    vm = {
        "vcpu": req_flavor_data['vcpu'],
        "mem_MB": req_flavor_data['memory_mb'],
        "disk_GB": ins_flavor_data['src_instance_disk_size'],  # 系统盘加数据盘
        "group_id": group_id,
        "count": count
    }
    host_list = host_s_s.match_hosts(hosts_after_filter, vm, least_host_num=least_host_num, max_disk=2000)
    host_len = len(host_list)
    if host_len == 0:
        logging.error('克隆准备步骤：HOST分配失败 没有合适主机 '
                      'task %s : match host resource not enough when create instance', task_id)
        # 将克隆源vm状态改成关机
        where_data = {
            'id': int(instance_id)
        }
        update_data = {
            'status': '1'
        }
        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='没有适合的主机，无法创建实例')
    logging.info('克隆准备步骤：HOST分配成功 task %s : match hosts successful when create instance', task_id)

    # 获取集群所在的环境
    vm_env = hostpool_service.get_env_of_hostpool(hostpool_id)
    # hostpool对应的机房名
    dc_name = hostpool_service.get_dc_name_of_hostpool(hostpool_id)
    # 获取集群所在网络区域名
    net_area_name = hostpool_service.get_level_info_by_id(hostpool_id).get('net_area_name', '')

    # 获取IP资源，先判断是否有人也在分配IP资源，有则等待1s，时间之后再优化
    ip_lock_unused = False
    while not ip_lock_unused:
        ret_ip_lock_status = ip_l_s.IpLockService().get_ip_lock_info('ip')
        if not ret_ip_lock_status:
            logging.error('克隆准备步骤：检查IP时无法获取资源锁状态'
                          'task %s : check ip resource can not get lock', task_id)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='检查IP时无法获取资源锁状态')
        if ret_ip_lock_status['istraceing'] == IpLockStatus.USED:
            time.sleep(1)
        else:
            ip_lock_unused = True

    # 更新ip_lock表istraceing字段为1
    ret_ip_lock_used_status, ret_ip_lock_used_datas = __update_ip_lock_used()
    if not ret_ip_lock_used_status:
        logging.error(ret_ip_lock_used_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_used_datas)
    try:
        ret_ips_status, ret_ips_data, ret_segment = __check_ip_resource(vm_env, dc_name, net_area_name, count)
    except Exception as e:
        _msg = '克隆准备步骤：检查IP资源出现异常 task %s : check ip resource exception when create instance，err：%s'%(task_id,e)
        logging.error(_msg)
        ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
        if not ret_ip_lock_unused_status:
            logging.error(ret_ip_lock_unused_datas)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=_msg)
    if not ret_ips_status:
        # 将克隆源vm状态改成关机
        where_data = {
            'id': int(instance_id)
        }
        update_data = {
            'status': '1'
        }
        try:
            ins_s.InstanceService().update_instance_info(update_data, where_data)
        finally:
            ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
        if not ret_ip_lock_unused_status:
            logging.error(ret_ip_lock_unused_datas)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ips_data)

    # 更新ip_lock表istraceing字段为0
    ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
    if not ret_ip_lock_unused_status:
        logging.error(ret_ip_lock_unused_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)
    logging.info('克隆准备步骤：检查IP资源 task %s : check ip resource start when create instance', task_id)

    ips_list = ret_ips_data
    segment_data = ret_segment
    logging.info('克隆准备步骤：检查IP资源成功 task %s : check ip resource successful when create instance', task_id)

    # 获取虚机名资源
    logging.info('克隆准备步骤：获取主机名资源 '
                 'task %s : check instance name resource start when create instance', task_id)
    is_name_enough, instance_name_list = _check_instance_name_resource(vm_env, dc_name, instance_system, count)
    if not is_name_enough:
        logging.error('克隆准备步骤：获取主机名资源失败 主机名资源不足 '
                      'task %s : datacenter %s has no enough instance name resource', task_id, dc_name)
        # 将克隆源vm状态改成关机
        where_data = {
            'id': int(instance_id)
        }
        update_data = {
            'status': '1'
        }
        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='主机名资源不足，无法创建实例')
    logging.info('克隆准备步骤：获取主机名资源成功 '
                 'task %s : check instance name resource successful when create instance', task_id)

    ###------------------------bt相关操作-----------------------------------------------------------------------\

    # 获取待克隆文件list
    ret_get_clone_images, clone_images_data = get_source_vm_image_num(source_vm_uuid, host_ip)
    if not ret_get_clone_images:
        # 将克隆源vm状态改成关机
        where_data = {
            'id': int(instance_id)
        }
        update_data = {
            'status': '1'
        }
        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=clone_images_data)
    clone_image_list = clone_images_data.split('\n')
    clone_image_num = len(clone_image_list)

    # 获取待克隆vm的总大小
    src_instance_uuid = instance_db_info['uuid']
    total_size = 0
    fail_num = 0
    for clone_image in clone_image_list:
        src_dir = '/app/image/' + src_instance_uuid
        ret, instance_disk_data = ansibleCmdV2.get_file_size(host_ip, clone_image, src_dir)
        if not ret:
            fail_num += 1
            break
        else:
            msg = 'now instance_disk_data is %s' % instance_disk_data
            logging.info(msg)
            total_size += float(instance_disk_data)
    if fail_num > 0:
        # 将克隆源vm状态改成关机
        where_data = {
            'id': int(instance_id)
        }
        update_data = {
            'status': '1'
        }
        err_msg = '获取源vm磁盘文件总大小失败'
        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=err_msg)

    # 获取cp后image的list
    source_disk_list = []
    for i in range(int(clone_image_num)):
        clone_image_name = instance_name + '_' + task_id + '_' + str(i)
        source_disk_list.append(clone_image_name)



    # 拷贝待克隆vm至指定文件夹
    ret_clonefile,copy_message = cp_clonefile(instance_id,host_ip,task_id,clone_image_list)
    if not ret_clonefile:
        # 将克隆源vm状态改成关机
        where_data = {
            'id': int(instance_id)
        }
        update_data = {
            'status': '1'
        }
        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=copy_message)

    # 获取MD5_check值
    ret_md5, md5_data = ansibleCmdV2.get_clonefile_md5(host_ip, source_disk_list[0])
    if not ret_md5:
        # 将克隆源vm状态改成关机
        where_data = {
            'id': int(instance_id)
        }
        update_data = {
            'status': '1'
        }
        err_msg = '获取源vm磁盘文件MD5失败'
        ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=err_msg)
    md5_check = md5_data

    if int(count) > 1:

        # 获取可用的bt tracker地址
        ret_get_tracker, tracker_msg = _confirm_trackerlist_addr()
        if not ret_get_tracker:
            logging.error(tracker_msg)
            # 将克隆源vm状态改成关机
            where_data = {
                'id': int(instance_id)
            }
            update_data = {
                'status': '1'
            }
            ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=tracker_msg)
        tracker_iplist = tracker_msg

        # 生成种子文件
        ret_torr_mk,torr_mk_msg = gener_clonefile_torr(instance_id,host_ip,tracker_iplist,task_id,clone_image_num)
        if not ret_torr_mk:
            logging.error(torr_mk_msg)
            # 将克隆源vm状态改成关机
            where_data = {
                'id': int(instance_id)
            }
            update_data = {
                'status': '1'
            }
            ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=torr_mk_msg)

        # 克隆源服务器将种子文件传输到队列
        ret_upload_torr,upload_torr_message = upload_torr(instance_id,host_ip,task_id,clone_image_num)
        if not ret_upload_torr:
            logging.error(upload_torr_message)
            # 将克隆源vm状态改成关机
            where_data = {
                'id': int(instance_id)
            }
            update_data = {
                'status': '1'
            }
            ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=upload_torr_message)

        # 克隆源服务器本地开启http服务
        http_port = torr_transport(host_ip)
        ret_http_start = clone_source_http(host_ip,task_id,instance_id,http_port)
        if not ret_http_start:
            logging.error('开启HTTP服务失败')
            # 将克隆源vm状态改成关机
            where_data = {
                'id': int(instance_id)
            }
            update_data = {
                'status': '1'
            }
            ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='开启HTTP服务失败')

        # 将host_list去重
        host_ip_list = []
        for host in host_list:
            host_ip_list.append(host['ipaddress'])
        host_list_sp = sorted(set(host_ip_list),key=host_ip_list.index)

        logging.info("--" * 25)
        logging.info("host after uniq")
        logging.info(host_list_sp)
        logging.info("--" * 25)

        # 传输种子文件到目标host
        ret_spread_torr,message = get_torr_file(instance_id,host_list_sp,task_id,host_ip,http_port,clone_image_num)
        if not ret_spread_torr:
            logging.error(message)
            # 将克隆源vm状态改成关机
            where_data = {
                'id': int(instance_id)
            }
            update_data = {
                'status': '1'
            }
            ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=message)

        time.sleep(2)

        # 源HOST关闭http
        ansibleCmdV2.clone_http_kill(host_ip,str(http_port))

    else:
        # 克隆源服务器本地开启http服务
        http_port = torr_transport(host_ip)
        ret_http_start = clone_source_http(host_ip, task_id, instance_id, http_port)
        if not ret_http_start:
            logging.error('开启HTTP服务失败')
            # 将克隆源vm状态改成关机
            where_data = {
                'id': int(instance_id)
            }
            update_data = {
                'status': '1'
            }
            ret_change_vm_status = ins_s.InstanceService().update_instance_info(update_data, where_data)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='开启HTTP服务失败')

    # #去重后的hosts上开启BT传输
    # ret_start_bt,start_bt_msg = host_bt_trans(host_list_sp,instance_id,task_id,host_ip)
    # if not ret_start_bt:
    #     return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=start_bt_msg)
    #
    # #判断目标host上bt传输是否完成
    # threads = []
    # for host in host_list_sp:
    #     # 多线程获取bt传输状态
    #     request_thread = MyThread(test_host_bt_done,args=(host,instance_id,task_id,host_ip))
    #     threads.append(request_thread)
    #     request_thread.start()
    #
    # bt_done_list = []
    # # 判断多线程是否结束
    # for t in threads:
    #     t.join()
    #     bt_done_list.append(t.get_result())
    # if False in bt_done_list:
    #     message = '部分host上BT传输失败'
    #     logging.error(message)
    #     return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=message)
    # else:
    #     message = '所有HOST上BT传输完成'
    #     logging.info(message)

    #-------------------------------------入库及消息发送至kafka----------------------------------------------------------

    source_vm_name = ins_s.InstanceService().get_instance_info(instance_id)['name']
    # 将克隆源vm状态改成关机
    where_data = {
        'id': int(instance_id)
    }
    update_data = {
        'status': '1'
    }
    ins_s.InstanceService().update_instance_info(update_data, where_data)

    logging.info('克隆准备步骤：多线程发送创建信息 task %s : create thread start when create instance', task_id)
    if int(count) > 1:
        trans_type = InstanceCloneCreateTransType.BT
    else:
        trans_type = InstanceCloneCreateTransType.WGET
    user_id = get_user()['user_id']
    all_threads = []
    for i in range(int(count)):
        instance_name = str(instance_name_list[i])
        ip_data = ips_list[i]

        # 轮询host
        index = i % host_len
        vm_host = host_list[index]

        create_ins_t = threading.Thread(target=_create_instance_info,
                                        args=(
                                        task_id, instance_name, app_info, owner, password_de, flavor_id, group_id, vm_host,
                                        ins_flavor_data, ip_data, vm_disk_gb, instance_system,
                                        net_area_id, segment_data, vm_env, user_id,image_data,instance_disks_db_info,
                                        source_disk_list,host_ip,source_vm_name,clone_image_num, total_size, http_port,trans_type, md5_check),
                                        name='thread-instance-clone-create-' + task_id)
        all_threads.append(create_ins_t)

    for thread in all_threads:
        thread.start()
    logging.info('克隆准备步骤：多线程发送创建信息成功 '
                 'task %s : create thread successful when create instance', task_id)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


def _create_instance_info(task_id, instance_name, app_info, owner, password, flavor_id, group_id, vm_host,
                                        flavor_info, ip_data, vm_disk_gb, instance_system,
                                        net_area_id, segment_data, vm_env, user_id,image_data,instance_disks_db_info,
                          source_disk_list,source_ip,source_vm_name,clone_image_num, total_size, http_port, trans_type, md5_check):
    uuid = randomUUID()
    request_id = ins_s.generate_req_id()
    # 往instance表添加记录
    logging.info('克隆入库步骤：插入instance表 task %s : insert instance table start when create instance', task_id)
    instance_data = {
        'uuid': uuid,
        'name': instance_name,
        'displayname': instance_name,
        'description': '',
        'status': VMStatus.CREATING,
        'typestatus': VMTypeStatus.NORMAL,
        'create_source': VMCreateSource.CLOUD_SOURCE,
        'isdeleted': '0',
        'app_info': app_info,
        'owner': owner,
        'created_at': get_datetime_str(),
        'password': encrypt_helper.encrypt(str(password)),  # 密码加密
        'request_id': request_id,
        'task_id': task_id,
        'clone_source_host':source_ip,
        'clone_source_vm':source_vm_name
    }
    ret = ins_s.InstanceService().add_instance_info(instance_data)
    if ret.get('row_num') <= 0:
        logging.error('task %s : add instance info error when create instance, insert_data: %s', task_id, instance_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    logging.info('克隆准备步骤：插入instance表成功 '
                 'task %s : insert instance table successful when create instance', task_id)

    instance_id = ret.get('last_id')

    # 往instance_flavor表添加记录
    logging.info('克隆准备步骤：插入instance_flavor表 '
                 'task %s : insert instance_flavor table start when create instance', task_id)
    instance_flavor_data = {
        'instance_id': instance_id,
        'flavor_id': flavor_id,
        'created_at': get_datetime_str()
    }
    ret1 = ins_f_s.InstanceFlavorService().add_instance_flavor_info(instance_flavor_data)
    if ret1.get('row_num') <= 0:
        logging.error('task %s : add instance_flavor info error when create instance, insert_data: %s',
                      task_id, instance_flavor_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    logging.info('克隆准备步骤：插入instance_flavor表成功 '
                 'task %s : insert instance_flavor table successful when create instance', task_id)

    # 往instance_group表添加记录
    logging.info('克隆准备步骤：插入instance_group表 task %s : insert instance_group table start when create instance', task_id)
    instance_group_data = {
        'instance_id': instance_id,
        'group_id': group_id,
        'created_at': get_datetime_str()
    }
    ret2 = ins_g_s.InstanceGroupService().add_instance_group_info(instance_group_data)
    if ret2.get('row_num') <= 0:
        logging.error('task %s : add instance_group info error when create instance, insert_data: %s',
                      task_id, instance_group_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    logging.info('克隆入库步骤：插入instance_group表成功 task %s : insert instance_group table successful when create instance', task_id)

    # 往instance_host表添加记录
    logging.info('克隆入库步骤：插入instance_host表 task %s : insert instance_host table start when create instance', task_id)
    instance_host_data = {
        'instance_id': instance_id,
        'instance_name': instance_name,
        'host_id': vm_host['host_id'],
        'host_name': vm_host['name'],
        'isdeleted': '0',
        'created_at': get_datetime_str()
    }
    ret3 = ins_h_s.InstanceHostService().add_instance_host_info(instance_host_data)
    if ret3.get('row_num') <= 0:
        logging.error('task %s : add instance_host info error when create instance, insert_data: %s',
                      task_id, instance_host_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    logging.info('克隆入库步骤：插入instance_host表成功 '
                 'task %s : insert instance_host table successful when create instance', task_id)

    # host预分配资源
    logging.info('克隆入库步骤：host预分配资源 task %s : pre allocate host resource start when create instance', task_id)
    ret4 = host_s.pre_allocate_host_resource(
        vm_host['host_id'], flavor_info['vcpu'], flavor_info['memory_mb'], flavor_info['root_disk_gb'])
    if ret4 != 1:
        logging.error('task %s : pre allocate host resource to db error when create instance', task_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    logging.info('克隆入库步骤：host预分配资源成功 '
                 'task %s : pre allocate host resource successful when create instance', task_id)

    # 往instance_image表添加记录
    logging.info('克隆入库步骤：插入instance_image表 task %s : insert instance_image table start when create instance', task_id)
    for _image in image_data:
        instance_image_data = {
            'instance_id': instance_id,
            'image_id': _image['id'],
            'created_at': get_datetime_str()
        }
        ret5 = ins_i_s.InstanceImageService().add_instance_image_info(instance_image_data)
        if ret5.get('row_num') <= 0:
            logging.error('task %s : add instance_image info error when create instance, insert_data: %s',
                          task_id, instance_image_data)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    logging.info('克隆入库步骤：插入instance_image表成功 '
                 'task %s : insert instance_image table successful when create instance', task_id)

    # 往instance_ip表添加记录
    logging.info('克隆入库步骤：插入instance_ip表 '
                 'task %s : insert instance_ip table start when create instance', task_id)
    mac = randomMAC()
    data_ip_address = ip_data['ip_address']
    instance_ip_data = {
        'instance_id': instance_id,
        'ip_id': ip_data['id'],
        'mac': mac,
        'type': InstanceNicType.MAIN_NETWORK_NIC,
        'isdeleted': '0',
        'created_at': get_datetime_str()
    }
    ret6 = ins_ip_s.InstanceIPService().add_instance_ip_info(instance_ip_data)
    if ret6.get('row_num') <= 0:
        logging.error('task %s : add instance_ip info error when create instance, insert_data: %s',
                      task_id, instance_ip_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    logging.info('克隆入库步骤：插入instance_ip表成功 '
                 'task %s : insert instance_ip table successful when create instance', task_id)

    # 标识该IP为已使用
    logging.info('克隆入库步骤：设置IP为已使用 task %s : set ip used start when create instance', task_id)
    update_data = {
        'status': IPStatus.USED
    }
    where_data = {
        'id': ip_data['id']
    }
    ret7 = ip_service.IPService().update_ip_info(update_data, where_data)
    if ret7 <= 0:
        logging.info('task %s : update ip info error when create instance, update_data: %s, where_data: %s',
                     task_id, update_data, where_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    logging.info('克隆入库步骤：设置IP为已使用成功 task %s : set ip used successful when create instance', task_id)

    # 往instance_disk表添加记录
    for src_instance_disk in instance_disks_db_info:
        instance_disk_data = {
            'instance_id': instance_id,
            'size_gb': src_instance_disk['size_gb'],
            'mount_point': src_instance_disk['mount_point'],
            'dev_name': src_instance_disk['dev_name'],
            'isdeleted': '0',
            'created_at': get_datetime_str()
        }
        ret6 = ins_d_s.InstanceDiskService().add_instance_disk_info(instance_disk_data)
        if ret6.get('row_num') <= 0:
            logging.info('add instance_disk info error when create instance, insert_data: %s',
                         instance_disk_data)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    logging.info('克隆入库步骤：将instance的disk信息入库成功 task %s : set ip used successful when create instance', task_id)

    # 往instance_clone_create表添加记录
    logging.info('克隆准备步骤：插入instance_clone_create表 '
                 'task %s : insert instance_clone_create table start when clone create instance', task_id)
    insert_data_clone_create = {
        'task_id': task_id,
        'source_vm_name': source_vm_name,
        'source_host_ip': source_ip,
        'torrent_num':clone_image_num,
        'create_time':get_datetime_str(),
        'instance_id':instance_id,
        "trans_type": trans_type,
        "total_size": total_size,
        "http_port": http_port,
        "md5_check": md5_check
    }
    ret1 = ins_c_c.InstanceCloneCreateService().add_instance_clone_create_info(insert_data_clone_create)
    if ret1.get('row_num') <= 0:
        logging.error('task %s : add instance_clone_create info error when clone create instance, insert_data: %s',
                      task_id, insert_data_clone_create)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    logging.info('克隆准备步骤：插入instance_clone_create表成功 '
                 'task %s : insert instance_clone_create table successful when create instance', task_id)

    # 发送异步消息到队列
    logging.info('克隆创建步骤,消息异步发送至kafka '
                 'task %s : send kafka message start when create instance', task_id)
    data = {
        "routing_key": "INSTANCE.CLONECREATE",
        "send_time": get_datetime_str(),
        "data": {
            "task_id": task_id,
            "source_ip":source_ip,
            "request_id": request_id,
            "instance_id":instance_id,
            "host_ip": vm_host['ipaddress'],
            "uuid": uuid,
            'source_vm':source_vm_name,
            "hostname": instance_name,  # 实例名
            "memory_mb": flavor_info['memory_mb'],
            "vcpu": flavor_info['vcpu'],
            "ostype": instance_system,
            "total_size": total_size,
            "trans_type": trans_type,
            "user_id": user_id,
            "disk_size": vm_disk_gb,
            "md5_check": md5_check,
            "http_port": http_port,
            "disks": source_disk_list,
            "image_name": _image['name'],
            "net_area_id": net_area_id,
            'clone_image_num':clone_image_num,
            "networks": [
                {
                    "net_card_name": "br_bond0." + segment_data['vlan'],
                    "ip": data_ip_address,
                    "netmask": segment_data['netmask'],
                    "dns1": segment_data['dns1'],
                    "dns2": segment_data['dns2'],
                    "mac": mac,
                    "gateway": segment_data['gateway_ip'],
                    "env": vm_env  # SIT STG PRD DR
                }
            ]
        }
    }
    ret_kafka = send_async_msg(KAFKA_TOPIC_NAME, data)


def _get_vd_map(vd_index):
    '''
        处理vd设备映射
    :param vd_index:
    :return:
    '''
    vd_arr = ['b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't']
    return 'vd' + vd_arr[vd_index]

#拷贝待克隆vm磁盘文件至目标文件夹
def cp_clonefile(instance_id,host_ip,task_id,clone_image_list):
    instance_info = ins_s.InstanceService().get_instance_info(instance_id)
    instance_uuid = instance_info['uuid']
    instance_name = instance_info['name']
    tag = 0
    check_result = True
    for clone_image in clone_image_list:
        source_file = '/app/image/'+ instance_uuid + '/' + clone_image
        dest_file = '/app/clone/'+ instance_name + '_' + task_id + "_" + str(tag)
        tag = tag + 1
        ret_copy_file,message = ansibleCmdV2.copy_clonefile(host_ip,source_file,dest_file)
        if not ret_copy_file:
            check_result = False
            return False,"拷贝待克隆vm镜像文件失败"
    if not check_result:
        message = "拷贝待克隆vm镜像文件失败"
        return False,message
    else:
        message = "拷贝待克隆vm镜像文件成功"
        return True,message


# 生成种子文件
def gener_clonefile_torr(instance_id,host_ip,tracker_iplist,task_id,clone_image_num):
    instance_info = ins_s.InstanceService().get_instance_info(instance_id)
    instance_name = instance_info['name']
    instance_uuid = instance_info['uuid']
    check_result = True
    for i in range(int(clone_image_num)):
        clone_file = '/app/clone/'+ instance_name + "_" + task_id + "_" + str(i)
        ret_torr_mk,message = ansibleCmdV2.torrnet_clonefile(host_ip, clone_file, tracker_iplist)
        if not ret_torr_mk:
            check_result = False
            return False,message
    if not check_result:
        return False,"生成种子文件失败"
    else:
        connect_create = vmManager.libvirt_get_connect(host_ip)
        if not connect_create:
            return False, "连接libvirt失败"
        else:
            check_tag = False
            retry_count = 0
            while not check_tag and retry_count < 8:
                try:
                    connect_create.refresh_storage_pool_by_name('clone')
                    check_tag = True
                except libvirtError as err:
                    retry_count = retry_count + 1
                    time.sleep(1)
            if not check_tag:
                return False, "生成种子文件成功,刷新clone池失败"
            else:
                return True,"生成种子文件成功,刷新clone池成功"



#本地上传种子文件
def upload_torr(instance_id,host_ip,task_id,clone_image_num):
    instance_info = ins_s.InstanceService().get_instance_info(instance_id)
    instance_name = instance_info['name']
    check_result = True
    for i in range(int(clone_image_num)):
        torr_file = '/app/clone/'+ instance_name +'_'+task_id + '_'+ str(i) +'.torrent'
        ret_upl_torr,message = ansibleCmdV2.upload_local_torr(torr_file,host_ip)
        if not ret_upl_torr:
            check_result = False
            return False,"上传种子文件至本地队列失败"
    if not check_result:
        return False,"上传种子文件至本地队列失败"
    else:
        return True,"上传种子文件至本地队列成功"


# 单个HOST下载种子文件函数
def spread_torr_file(instance_id,dest_host,task_id,source_ip,torr_port,clone_image_num):
    instance_info = ins_s.InstanceService().get_instance_info(instance_id)
    instance_name = instance_info['name']
    fail_list = []
    fail_list2 = []
    dest_dir = '/app/clone/'

    if dest_host == source_ip:
        result = True, "pass", instance_info['name']
        q.put(result)
        return
    else:
        fail_list = []
        for i in range(int(clone_image_num)):
            http_port = str(torr_port)
            check_torr = check_torrent_exist(dest_host,instance_id,task_id,source_ip,http_port,i)
            if not check_torr:
                fail_list.append(i)
        if fail_list != []:
            result = False, "下载种子文件失败", dest_host
            q.put(result)
            return
        else:
            result = True, "下载种子文件成功", dest_host
            q.put(result)
            return


#hosts_list获取种子文件
def get_torr_file(instance_id,host_list,task_id,source_ip,torr_port,clone_image_num):
    threads = []
    for host in host_list:
        wget_torr_thread = threading.Thread(target=spread_torr_file, args=(instance_id,host,task_id,source_ip,torr_port,clone_image_num))
        threads.append(wget_torr_thread)
        wget_torr_thread.start()

    for t in threads:
        t.join()

    return_msg_list = []
    while not q.empty():
        return_msg_list.append(q.get())
    error_list = []
    for msg_list in return_msg_list:
        if msg_list[0] is False:
            error_list.append(msg_list[2])
    if error_list == []:
        return True,'wget种子文件成功'
    else:
        return False,'以下host获取种子文件失败 %s ' % error_list


#文件上传函数
def pari_upload(host_ip,source_file,dest_dir):
    dest_host = host_ip
    port = 22
    username1 = ANSIABLE_REMOTE_USER
    password1 = ANSIABLE_REMOTE_PWD
    try:
        t = paramiko.Transport(dest_host,port)
        t.connect(username = username1, password = password1)
        sftp = paramiko.SFTPClient.from_transport(t)
        remotepath = dest_dir
        localpath = source_file
        sftp.put(localpath,remotepath)
        t.close()
        return True
    except:
        return False


#文件下载函数
def pari_download(host_ip,remote_file,local_patch):
    dest_host = host_ip
    port = 22
    username1 = ANSIABLE_REMOTE_USER
    password1 = ANSIABLE_REMOTE_PWD
    try:
        t = paramiko.Transport(dest_host,port)
        t.connect(username = username1, password = password1)
        sftp = paramiko.SFTPClient.from_transport(t)
        remotepath = remote_file
        localpath = local_patch
        sftp.get(remotepath,localpath)
        t.close()
        return True
    except:
        return False


#获取tracker_ip
def _confirm_tracker_addr():
    '''
        返回tracker服务器地址
    :return:
    '''
    available_tracker = []
    # 通过net_area_id获取镜像服务器、镜像缓存服务器信息
    if not TRACKER_SERVER:
        _msg = '未找到TRACKER SERVER'
        logging.error(_msg)
        return False, _msg

    if not TRACKER_SERVER_PORT:
        _msg = '未找到TRACKER SERVER PORT参数'
        logging.error(_msg)
        return False, _msg

    for tracker in TRACKER_SERVER:
        if _check_server_is_up(tracker, TRACKER_SERVER_PORT):
            available_tracker.append(tracker)

    if len(available_tracker) == 0:
        _msg = '未找到合适的tracker服务器'
        logging.error(_msg)
        return False, _msg

    return True, available_tracker[0]

#获取tracker_ip
def _confirm_trackerlist_addr():
    '''
        返回tracker服务器地址
    :return:
    '''
    available_tracker = []
    # 通过net_area_id获取镜像服务器、镜像缓存服务器信息
    if not TRACKER_SERVER:
        _msg = '未找到TRACKER SERVER'
        logging.error(_msg)
        return False, _msg

    if not TRACKER_SERVER_PORT:
        _msg = '未找到TRACKER SERVER PORT参数'
        logging.error(_msg)
        return False, _msg

    for tracker in TRACKER_SERVER:
        if _check_server_is_up(tracker, TRACKER_SERVER_PORT):
            available_tracker.append(tracker)

    if len(available_tracker) == 0:
        _msg = '未找到合适的tracker服务器'
        logging.error(_msg)
        return False, _msg

    return True, available_tracker


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
def clone_source_http(host_ip,task_id,instance_id,http_port):
    instance_info = ins_s.InstanceService().get_instance_info(instance_id)
    instance_name = instance_info['name']
    dest_dir = '/app/clone'
    check_result = False
    timecount = 0
    while not check_result and timecount < 3:
        ret_http,http_msg = ansibleCmdV2.python_clone_http(host_ip,dest_dir,http_port)
        print http_msg
        time.sleep(1)
        ret_check,ret_msg = ansibleCmdV2.check_port_is_up(host_ip, str(http_port))
        #ret_check =  _check_server_is_up(host_ip,int(http_port))
        if not ret_check:
            timecount = timecount +1
        else:
            check_result = True
    return check_result


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
        return True, 200
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


#目标host开启bt传输
def bt_trans_start(host_ip,instance_id,task_id,speed_limit):
    instance_info = ins_s.InstanceService().get_instance_info(instance_id)
    instance_name = instance_info['name']
    instance_uuid = instance_info['uuid']
    torrent_file = '/app/clone/'+instance_name + '_' + task_id +'.torrent'
    ret_bt_trans,bt_trans_msg = ansibleCmdV2.bt_trans_images(host_ip, torrent_file, speed_limit)
    return ret_bt_trans,bt_trans_msg


#对去重后的hosts清单开启BT传输
def host_bt_trans(host_list,instance_id,task_id,source_ip):
    bt_trans_fail_list = []
    #获取bt传输限速
    for host in host_list:
        if host == source_ip:
            pass
        else:
            #获取传输限速
            trans_speed, speed_data = _confirm_image_get_speed(host)
            if not trans_speed:
                speed = 200
            else:
                speed = speed_data
            #开启BT传输
            speed_limit = str(int(float(speed) * 1024 / 8))
            ret_bt_trans, bt_trans_msg = bt_trans_start(host, instance_id, task_id, speed_limit)
            if not ret_bt_trans:
                bt_trans_fail_list.append(host)
    if bt_trans_fail_list != []:
        fail_msg = '以下host %s 上开启bt传输失败' % bt_trans_fail_list
        logging.error(fail_msg)
        return False,fail_msg
    else:
        msg = '任务hosts上BT传输开启成功'
        logging.info(msg)
        return True,msg

#单台host上抓取当前bt传输进度
def test_host_bt_done(host_ip,instance_id,task_id,source_ip):
    instance_info = ins_s.InstanceService().get_instance_info(instance_id)
    instance_name = instance_info['name']
    grep_parr = instance_name + '_' + task_id
    check_stat = False
    time_count = 0
    if host_ip == source_ip:
        return True
    while not check_stat and time_count < 600:
        ret_bt_trans_stat,bt_trans_stat_msg = ansibleCmdV2.grep_bt_stat(host_ip,grep_parr)
        if ret_bt_trans_stat:
            check_stat = True
            break
        time.sleep(10)
        time_count = time_count + 10
    if check_stat:
        return True
    else:
        return False


# 判断种子文件是否存在
def check_torrent_exist(host_ip,instance_id,task_id,source_ip,http_port,i):
    instance_info = ins_s.InstanceService().get_instance_info(instance_id)
    instance_name = instance_info['name']
    torr_file = '/app/clone/'+ instance_name + '_' + task_id + '_' + str(i) + '.torrent'
    torr_exist = False
    check_tag = 0
    while not torr_exist and check_tag < 60:
        ret_check_file,check_file_msg = ansibleCmdV2.check_file_exists(host_ip,torr_file)
        if  ret_check_file:
            torr_exist = True
        else:
            dest_dir = '/app/clone/'
            dest_file = dest_dir + instance_name + '_' + task_id + '_' + str(i)+'.torrent'
            dest_file1 = '/' + instance_name + '_' + task_id + '_' + str(i)+'.torrent'
            ansibleCmdV2.get_clone_image(host_ip, dest_dir, dest_file, source_ip, http_port, dest_file1)
            check_tag = check_tag + 5
            time.sleep(5)
    return torr_exist



def torr_transport(host_ip):
     i=1
     while i< 1000:
         randport = random.randint(11000,12000)
         rand_res = _check_server_is_up(host_ip,randport)
         if rand_res == False:
             return randport
         else:
             i += 1


# 获取待克隆vm的镜像文件数量
def get_source_vm_image_num(vm_uuid, host_ip):
    dest_dir = '/app/image/' + vm_uuid
    ret_image_num, image_num = ansibleCmdV2.get_dir_image_num(host_ip, dest_dir)
    return ret_image_num, image_num


def __check_ip_resource(env, dc_name, net_area, count):
    '''
        判断IP资源是否足够
    :param hostpool_id:
    :param count:
    :return:
    '''
    # 查询指定环境、网络区域是否有所需网段
    ret_segment_datas = segment_s.get_segments_data_by_type(net_area, dc_name, env, NetCardType.INTERNAL)
    if not ret_segment_datas:
        return False, '集群所在机房、网络区域下没有可用网段用于分配IP', ''

    # 获取可用ip
    ret_ip_datas, ret_ip_segment_datas = ip_service.get_available_ips(ret_segment_datas, int(count), env)
    if not ret_ip_datas:
        return False, '集群所在机房、网络区域下无法找到%s个可用IP' % str(count), ''

    # 如果是申请生产或者容灾环境ip，需判断网段对应关系表中是否有记录
    if int(env) == DataCenterType.PRD:
        segment_dr = segment_m.SegmentMatchService().get_segment_match_info_by_prd_segment_id(
            ret_ip_segment_datas['id'])
        if not segment_dr:
            return False, '集群所在机房、网络区域下无法找到生产网段对应的容灾网段ID', ''
        segment_dr_data = segment_s.SegmentService().get_segment_info(segment_dr['dr_segment_id'])
        if not segment_dr_data:
            return False, '集群所在机房、网络区域下无法找到生产网段对应的容灾网段详细信息', ''

    elif int(env) == DataCenterType.DR:
        segment_prd = segment_m.SegmentMatchService().get_segment_match_info_by_dr_segment_id(
            ret_ip_segment_datas['id'])
        if not segment_prd:
            return False, '指定机房、网络区域下无法找到容灾网段对应的生产网段ID', ''
        segment_prd_data = segment_s.SegmentService().get_segment_info(segment_prd['prd_segment_id'])
        if not segment_prd_data:
            return False, '指定机房、网络区域下无法找到容灾网段对应的生产网段详细信息', ''

    # 标记ip为预分配
    ips_list = []
    prd_ips_list = []
    dr_ips_list = []
    for ip in ret_ip_datas:
        update_data = {
            'status': IPStatus.PRE_ALLOCATION
        }
        where_data = {
            'id': ip['id']
        }
        ret_mark_ip = ip_service.IPService().update_ip_info(update_data, where_data)
        if ret_mark_ip <= 0:
            continue
        ips_list.append(ip)

        # 生产环境需要预分配对应容灾环境ip，容灾环境需要预分配生产环境ip
        if int(env) == DataCenterType.PRD:
            # 拼凑虚拟机容灾ip并预分配ip
            dr_ip = segment_dr_data['segment'].split('.')[0] + '.' + segment_dr_data['segment'].split('.')[1] + \
                    '.' + ip['ip_address'].split('.')[2] + '.' + ip['ip_address'].split('.')[3]
            dr_ip_info = ip_service.IPService().get_ip_by_ip_address(dr_ip)
            # 如果容灾环境ip未初始化，默认初始化
            if not dr_ip_info:
                if not __init_ip(segment_dr_data, dr_ip):
                    continue
                dr_ip_info = ip_service.IPService().get_ip_by_ip_address(dr_ip)

            update_data = {
                'status': IPStatus.PRE_ALLOCATION
            }
            where_data = {
                'ip_address': dr_ip
            }
            ret_mark_ip = ip_service.IPService().update_ip_info(update_data, where_data)
            if ret_mark_ip <= 0:
                continue
            dr_ips_list.append(dr_ip_info)
        elif int(env) == DataCenterType.DR:
            # 拼凑虚拟机生产ip并预分配ip
            prd_ip = segment_prd_data['segment'].split('.')[0] + '.' + segment_prd_data['segment'].split('.')[1] + \
                     '.' + ip['ip_address'].split('.')[2] + '.' + ip['ip_address'].split('.')[3]
            prd_ip_info = ip_service.IPService().get_ip_by_ip_address(prd_ip)
            # 如果生产环境ip未初始化，默认初始化
            if not prd_ip_info:
                if not __init_ip(segment_prd_data, prd_ip):
                    continue
                prd_ip_info = ip_service.IPService().get_ip_by_ip_address(prd_ip)
            update_data = {
                'status': IPStatus.PRE_ALLOCATION
            }
            where_data = {
                'ip_address': prd_ip
            }
            ret_mark_ip = ip_service.IPService().update_ip_info(update_data, where_data)
            if ret_mark_ip <= 0:
                continue
            prd_ips_list.append(prd_ip_info)

    if len(ips_list) <= 0:
        return False, '虚拟机创建所需%s个可用IP修改为预分配状态全部失败' % str(count), ''
    elif int(env) == DataCenterType.PRD and (len(ips_list) + len(dr_ips_list)) < int(count) * 2:
        return False, '生产环境虚拟机创建所需%s个可用IP修改为预分配状态部分失败' % str(count), ''
    elif int(env) == DataCenterType.DR and (len(ips_list) + len(prd_ips_list)) < int(count) * 2:
        return False, '容灾环境虚拟机创建所需%s个可用IP修改为预分配状态部分失败' % str(count), ''
    elif len(ips_list) < int(count):
        return False, '虚拟机创建所需%s个可用IP修改为预分配状态部分失败' % str(count), ''
    else:
        return True, ret_ip_datas, ret_ip_segment_datas


def __init_ip(segment_datas, ip_address):
    '''
        IP初始化
    :param segment_datas:
    :param ip_address:
    :return:
    '''
    ip_vlan = segment_datas['vlan']
    ip_netmask = segment_datas['netmask']
    ip_segment_id = segment_datas['id']
    ip_gateway_ip = segment_datas['gateway_ip']
    ip_dns1 = segment_datas['dns1']
    ip_dns2 = segment_datas['dns2']

    insert_data = {
        'ip_address': ip_address,
        'segment_id': ip_segment_id,
        'netmask': ip_netmask,
        'vlan': ip_vlan,
        'gateway_ip': ip_gateway_ip,
        'dns1': ip_dns1,
        'dns2': ip_dns2,
        'status': IPStatus.UNUSED,
        'created_at': get_datetime_str()
    }
    ret = ip_service.IPService().add_ip_info(insert_data)
    if ret == -1:
        return False
    return True


def __update_ip_lock_unused():
    '''
        更新ip_lock表istraceing字段为0
    :return:
    '''

    update_ip_lock_data = {
        'istraceing': IpLockStatus.UNUSED
    }
    where_ip_lock_data = {
        'table_name': 'ip'
    }
    ret_update_ip_lock = ip_l_s.IpLockService().update_ip_lock_info(update_ip_lock_data, where_ip_lock_data)
    if not ret_update_ip_lock:
        return False, '克隆准备步骤：检查IP时无法更新资源锁状态为未使用中'
    return True, '克隆准备步骤：检查IP时更新资源锁状态为未使用中成功'


def __update_ip_lock_used():
    '''
        更新ip_lock表istraceing字段为1
    :return:
    '''

    update_ip_lock_data = {
        'istraceing': IpLockStatus.USED
    }
    where_ip_lock_data = {
        'table_name': 'ip'
    }
    ret_update_ip_lock = ip_l_s.IpLockService().update_ip_lock_info(update_ip_lock_data, where_ip_lock_data)
    if not ret_update_ip_lock:
        return False, '克隆准备步骤：检查IP时无法更新资源锁状态为使用中'
    return True, '克隆准备步骤：检查IP时更新资源锁状态为使用中成功'
