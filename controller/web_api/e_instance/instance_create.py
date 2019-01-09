# coding=utf8
'''
    虚拟机管理-创建
'''


import logging

from flask import request
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
from config.default import INSTANCE_MAX_CREATE, DATA_DISK_GB
from helper import encrypt_helper, json_helper
from helper.time_helper import get_datetime_str
from lib.mq.kafka_client import send_async_msg
from lib.vrtManager.util import randomUUID, randomMAC
from model.const_define import ErrorCode, IPStatus, VMStatus, VMTypeStatus, ImageType, VMCreateSource, \
    EnvType, DataCenterType, OperationObject, OperationAction, IpLockStatus, NetCardType, InstanceNicType
from service.s_flavor import flavor_service
from service.s_host import host_service as host_s, host_schedule_service as host_s_s
from service.s_hostpool import hostpool_service
from service.s_image import image_service
from service.s_increment import increment_service
from service.s_instance import instance_host_service as ins_h_s, instance_ip_service as ins_ip_s, \
    instance_image_service as ins_img_s, instance_disk_service as ins_d_s, instance_service as ins_s, \
    instance_flavor_service as ins_f_s, instance_group_service as ins_g_s
from service.s_ip import ip_service
from service.s_user.user_service import get_user
from service.s_user import user_service as user_s
from service.s_group import group_service as group_s
from service.s_ip import segment_match as segment_m
from service.s_ip import segment_service as segment_s
from service.s_ip import ip_lock_service as ip_l_s
import threading
from config.default import ENV, ST_ENVIRONMENT
from config import KAFKA_TOPIC_NAME
from service.s_operation.operation_service import add_operation_vm
import time


@login_required
@add_operation_vm(OperationObject.VM, OperationAction.ADD)
def instance_create(hostpool_id):
    '''
        创建虚机
    :param hostpool_id:
    :return:
    '''
    image_name = request.values.get('image_name')
    flavor_id = request.values.get('flavor_id')
    disk_gb = request.values.get('disk_gb')
    count = request.values.get('count')
    app_info = request.values.get('app_info')
    group_id = request.values.get('group_id')
    owner = request.values.get('owner')
    password = request.values.get('password')
    task_id = ins_s.generate_task_id()

    logging.info('创建VM 步骤1：检查参数 task %s : check params start when create instance', task_id)

    if not hostpool_id or not image_name or not flavor_id or not disk_gb or not group_id \
            or not count or int(count) < 1:
        logging.error('创建VM 步骤1：检查参数失败 参数错误 task %s : params are invalid when create instance', task_id)
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg='参数错误')

    if int(count) > int(INSTANCE_MAX_CREATE):
        logging.error('创建VM 步骤1：检查参数失败 批量创建数超过最大数 '
                      'task %s : create count %s > max num %s when create instance',
                      task_id, count, INSTANCE_MAX_CREATE)
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR,
                                           msg='批量创建最大实例数不能超过' + INSTANCE_MAX_CREATE + '个')

    owner_exist = user_s.UserService().check_userid_exist(owner)
    if not owner_exist:
        logging.error('创建VM 步骤1：检查参数失败 应用管理员工号不存在 '
                      'task %s : no such user %s in db when create instance', task_id, owner)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='应用管理员工号不存在，无法创建实例')

    logging.info('创建VM 步骤1：检查参数成功 task %s : check params successful when create instance', task_id)

    # 数据盘最少50GB
    # todo:这里只是一个数据盘，后面有多个数据盘
    vm_disk_gb = int(disk_gb) if int(disk_gb) > DATA_DISK_GB else DATA_DISK_GB

    # 获取主机列表(不包括锁定、维护状态)
    logging.info('创建VM 步骤2：获取集群所有HOST列表 '
                 'task %s : get all hosts in hostpool %s start when create instance', task_id, hostpool_id)
    all_hosts_nums, all_hosts_data = host_s.HostService().get_available_hosts_of_hostpool(hostpool_id)
    # 可用物理机数量不足
    least_host_num = hostpool_service.HostPoolService().get_least_host_num(hostpool_id)
    if all_hosts_nums < least_host_num or all_hosts_nums < 1:
        logging.error('创建VM 步骤2：获取集群所有HOST列表失败 集群不够资源 '
                      'task %s : available host resource not enough when create instance', task_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='集群不够资源，无法创建实例')
    logging.info('创建VM 步骤2：获取集群所有HOST列表成功，总host数：%s '
                 'task %s : get all hosts in hostpool %s successful, all hosts nums %s when create instance',
                 all_hosts_nums, task_id, hostpool_id, all_hosts_nums)

    # 过滤host
    logging.info('创建VM 步骤3：HOST过滤 task %s : filter hosts start when create instance', task_id)
    hosts_after_filter = host_s_s.filter_hosts(all_hosts_data)
    if len(hosts_after_filter) == 0 or len(hosts_after_filter) < least_host_num:
        logging.error('创建VM 步骤3：HOST过滤失败 没有合适主机 '
                      'task %s : no available host when create instance', task_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='集群物理机资源无法满足你的申请需求，请联系系统组同事')
    logging.info('创建VM 步骤3：HOST过滤成功 task %s : filter hosts successful when create instance', task_id)

    # 获取flavor信息
    logging.info('创建VM 步骤4：获取必需信息 task %s : get need info start when create instance', task_id)
    flavor_info = flavor_service.FlavorService().get_flavor_info(flavor_id)
    if not flavor_info:
        logging.error('创建VM 步骤4：获取必需信息失败 实例规格数据有误 '
                      'task %s : flavor %s info not in db when create instance', task_id, flavor_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='实例规格数据有误，无法创建实例')

    # VM分配给HOST
    logging.info('创建VM 步骤5：HOST分配 task %s : match hosts start when create instance', task_id)
    vm = {
        "vcpu": flavor_info['vcpu'],
        "mem_MB": flavor_info['memory_mb'],
        "disk_GB": flavor_info['root_disk_gb'] + vm_disk_gb,  # 系统盘加数据盘
        "group_id": group_id,
        "count": count
    }
    host_list = host_s_s.match_hosts(hosts_after_filter, vm, least_host_num=least_host_num, max_disk=2000)
    host_len = len(host_list)
    if host_len == 0:
        logging.error('创建VM 步骤5：HOST分配失败 没有合适主机 '
                      'task %s : match host resource not enough when create instance', task_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='集群物理机资源无法满足你的申请需求，请联系系统组同事')
    logging.info('创建VM 步骤5：HOST分配成功 task %s : match hosts successful when create instance', task_id)

    # 获取hostpool的net area信息
    hostpool_info = hostpool_service.HostPoolService().get_hostpool_info(hostpool_id)
    if not hostpool_info:
        logging.error('创建VM 步骤6：获取必需信息失败 物理机池所属网络区域信息有误 '
                      'task %s : hostpool %s info not in db when create instance', task_id, hostpool_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='物理机池所属网络区域信息有误，无法创建实例')

    net_area_id = hostpool_info['net_area_id']
    logging.info('创建VM 步骤6：获取必需信息成功 task %s : get need info successful when create instance', task_id)

    # 组配额控制
    logging.info('创建VM 步骤7：检查组配额 task %s : check group quota start when create instance', task_id)
    is_quota_enough, quota_msg = check_group_quota(group_id, flavor_info, vm_disk_gb, count)
    if not is_quota_enough:
        logging.error('创建VM 步骤7：检查组配额失败 配额不足 '
                      'task %s : group %s is no enough quota when create instance', task_id, group_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=quota_msg)
    logging.info('创建VM 步骤7：检查组配额成功 task %s : check group quota successful when create instance', task_id)

    logging.info('创建VM 步骤8：获取必需信息 task %s : get need 1 info start when create instance', task_id)
    # 获取镜像信息，一个image_name可能对应多个id
    image_nums, image_data = image_service.ImageService().get_images_by_name(image_name)
    if image_nums <= 0:
        logging.info('创建VM 步骤8：获取必需信息失败 镜像资源不足 '
                     'task %s : no image %s info in db when create instance', task_id, image_name)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='没有镜像资源，无法创建实例')

    # 实例操作系统
    instance_system = image_data[0]['system']
    logging.info('创建VM 步骤8：获取必需信息成功 '
                 'task %s : get need 1 info successful when create instance', task_id)

    # 获取集群所在的环境
    vm_env = hostpool_service.get_env_of_hostpool(hostpool_id)
    # hostpool对应的机房名
    dc_name = hostpool_service.get_dc_name_of_hostpool(hostpool_id)
    # 获取集群所在网络区域名
    net_area_name = hostpool_service.get_level_info_by_id(hostpool_id).get('net_area_name', '')

    # 获取虚机名资源
    logging.info('创建VM 步骤9：获取主机名资源 '
                 'task %s : check instance name resource start when create instance', task_id)
    is_name_enough, instance_name_list = _check_instance_name_resource(vm_env, dc_name, instance_system, count)
    if not is_name_enough:
        logging.error('创建VM 步骤9：获取主机名资源失败 主机名资源不足 '
                      'task %s : datacenter %s has no enough instance name resource', task_id, dc_name)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='主机名资源不足，无法创建实例')
    logging.info('创建VM 步骤9：获取主机名资源成功 '
                 'task %s : check instance name resource successful when create instance', task_id)

    # 获取IP资源，先判断是否有人也在分配IP资源，有则等待1s，时间之后再优化
    ip_lock_unused = False
    while not ip_lock_unused:
        ret_ip_lock_status = ip_l_s.IpLockService().get_ip_lock_info('ip')
        if not ret_ip_lock_status:
            logging.error('创建VM 步骤10：检查IP时无法获取资源锁状态'
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
        _msg = '创建VM 步骤10：检查IP资源是否足够出现异常task_id %s: check ip resource exception when instance create，err：%s'%(
            task_id, e)
        logging.error(_msg)
        ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
        if not ret_ip_lock_unused_status:
            logging.error(ret_ip_lock_unused_datas)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=_msg)

    if not ret_ips_status:
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

    ips_list = ret_ips_data
    segment_data = ret_segment
    logging.info('创建VM 步骤10：检查IP资源成功 task %s : check ip resource successful when create instance', task_id)

    # 挂载点
    if instance_system == 'linux':
        mount_point = '/app'
    else:
        mount_point = 'E'

    logging.info('创建VM 步骤11：多线程发送创建信息 task %s : create thread start when create instance', task_id)
    user_id = get_user()['user_id']
    all_threads = []
    for i in range(int(count)):
        instance_name = str(instance_name_list[i])
        ip_data = ips_list[i]

        # 轮询host
        index = i % host_len
        vm_host = host_list[index]

        create_ins_t = threading.Thread(target=_create_instance_info,
                                        args=(task_id, instance_name, app_info, owner, password, flavor_id, group_id,
                                              vm_host, flavor_info, image_data, ip_data, vm_disk_gb, mount_point,
                                              instance_system, net_area_id, segment_data, vm_env, user_id),
                                        name='thread-instance-create-' + task_id)
        all_threads.append(create_ins_t)
        create_ins_t.start()

    for thread in all_threads:
        thread.join()

    logging.info('创建VM 步骤11：多线程发送创建信息成功 '
                 'task %s : create thread successful when create instance', task_id)

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


def _create_instance_info(task_id, instance_name, app_info, owner, password, flavor_id, group_id, vm_host, flavor_info,
                          image_data, ip_data, vm_disk_gb, mount_point, instance_system, net_area_id, segment_data,
                          vm_env, user_id):
    uuid = randomUUID()
    request_id = ins_s.generate_req_id()
    # 往instance表添加记录
    logging.info('创建VM 步骤10-1：插入instance表 task %s : insert instance table start when create instance', task_id)
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
        'task_id': task_id
    }
    ret = ins_s.InstanceService().add_instance_info(instance_data)
    if ret.get('row_num') <= 0:
        logging.error('task %s : add instance info error when create instance, insert_data: %s', task_id, instance_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    logging.info('创建VM 步骤10-1：插入instance表成功 '
                 'task %s : insert instance table successful when create instance', task_id)

    instance_id = ret.get('last_id')

    # 往instance_flavor表添加记录
    logging.info('创建VM 步骤10-2：插入instance_flavor表 '
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
    logging.info('创建VM 步骤10-2：插入instance_flavor表成功 '
                 'task %s : insert instance_flavor table successful when create instance', task_id)

    # 往instance_group表添加记录
    logging.info('创建VM 步骤10-3：插入instance_group表 task %s : insert instance_group table start when create instance', task_id)
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
    logging.info('创建VM 步骤10-3：插入instance_group表成功 task %s : insert instance_group table successful when create instance', task_id)

    # 往instance_host表添加记录
    logging.info('创建VM 步骤10-4：插入instance_host表 task %s : insert instance_host table start when create instance', task_id)
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
    logging.info('创建VM 步骤10-4：插入instance_host表成功 '
                 'task %s : insert instance_host table successful when create instance', task_id)

    # host预分配资源
    logging.info('创建VM 步骤10-5：host预分配资源 task %s : pre allocate host resource start when create instance', task_id)
    ret4 = host_s.pre_allocate_host_resource(
        vm_host['host_id'], flavor_info['vcpu'], flavor_info['memory_mb'], flavor_info['root_disk_gb'])
    if ret4 != 1:
        logging.error('task %s : pre allocate host resource to db error when create instance', task_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    logging.info('创建VM 步骤10-5：host预分配资源成功 '
                 'task %s : pre allocate host resource successful when create instance', task_id)

    # 往instance_image表添加记录
    logging.info('创建VM 步骤10-6：插入instance_image表 task %s : insert instance_image table start when create instance', task_id)
    for _image in image_data:
        instance_image_data = {
            'instance_id': instance_id,
            'image_id': _image['id'],
            'created_at': get_datetime_str()
        }
        ret5 = ins_img_s.InstanceImageService().add_instance_image_info(instance_image_data)
        if ret5.get('row_num') <= 0:
            logging.error('task %s : add instance_image info error when create instance, insert_data: %s',
                          task_id, instance_image_data)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    logging.info('创建VM 步骤10-6：插入instance_image表成功 '
                 'task %s : insert instance_image table successful when create instance', task_id)

    # 往instance_ip表添加记录
    logging.info('创建VM 步骤10-7：插入instance_ip表 '
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
    logging.info('创建VM 步骤10-7：插入instance_ip表成功 '
                 'task %s : insert instance_ip table successful when create instance', task_id)

    # 标识该IP为已使用
    logging.info('创建VM 步骤10-8：设置IP为已使用 task %s : set ip used start when create instance', task_id)
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
    logging.info('创建VM 步骤10-8：设置IP为已使用成功 task %s : set ip used successful when create instance', task_id)

    # 拼装消息需要的镜像信息
    logging.info('创建VM 步骤10-9：拼装所需的镜像信息 '
                 'task %s : piece together need image info start when create instance', task_id)
    image_list = []
    # 数据盘数量
    data_image_num = 0
    for _image in image_data:
        _image_type = _image['type']
        _info = {
            "disk_format": _image['format'],
            "url": _image['url'],
            # "md5sum": _image['md5'],
            "image_size_gb": _image['size_gb']  # 镜像预分配大小
        }
        # 系统盘
        if _image_type == ImageType.SYSTEMDISK:
            _disk_name = instance_name + '.img'
            _info['image_dir_path'] = '/app/image/' + uuid + '/' + _disk_name
            _info['disk_name'] = _disk_name
            _info['disk_size_gb'] = None
            _info['dev_name'] = 'vda'

            # 如果只有一块盘且为系统盘，则预先分配一块数据盘的数据存入instance_disk表
            if len(image_data) == 1:
                logging.info('task %s : pre insert instance_disk table that has only one system disk start when create '
                             'instance', task_id)
                instance_disk_data = {
                     'instance_id': instance_id,
                     'size_gb': vm_disk_gb,
                     'mount_point': mount_point,
                     'dev_name': 'vdb',
                     'isdeleted': '0',
                     'created_at': get_datetime_str()
                 }
                ret9 = ins_d_s.InstanceDiskService().add_instance_disk_info(instance_disk_data)
                if ret9.get('row_num') <= 0:
                    logging.info('task %s : pre add instance_disk info that has only one system disk error when create '
                                 'instance, insert_data: %s', task_id, instance_disk_data)
                    return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
                logging.info('task %s : pre insert instance_disk table that has only one system disk successful when '
                             'create instance', task_id)
        else:
            # 数据盘
            _disk_name = instance_name + '.disk' + str(data_image_num + 1)
            _disk_dev_name = _get_vd_map(data_image_num)
            _info['image_dir_path'] = '/app/image/' + uuid + '/' + _disk_name
            _info['disk_name'] = _disk_name
            _info['disk_size_gb'] = vm_disk_gb
            _info['dev_name'] = _disk_dev_name
            data_image_num += 1

            # 往instance_disk表添加记录
            logging.info('task %s : insert instance_disk table start when create instance', task_id)
            instance_disk_data = {
                'instance_id': instance_id,
                'size_gb': vm_disk_gb,
                'mount_point': mount_point,
                'dev_name': _disk_dev_name,
                'isdeleted': '0',
                'created_at': get_datetime_str()
            }
            ret8 = ins_d_s.InstanceDiskService().add_instance_disk_info(instance_disk_data)
            if ret8.get('row_num') <= 0:
                logging.info('task %s : add instance_disk info error when create instance, insert_data: %s',
                             task_id, instance_disk_data)
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
            logging.info('task %s : insert instance_disk table successful when create instance', task_id)

        image_list.append(_info)
    logging.info('创建VM 步骤10-9：拼装所需的镜像信息成功 '
                 'task %s : piece together need image info successful when create instance', task_id)

    # 发送异步消息到队列
    logging.info('创建VM 步骤10-10：发送异步消息给队列 '
                 'task %s : send kafka message start when create instance', task_id)
    data = {
        "routing_key": "INSTANCE.CREATE",
        "send_time": get_datetime_str(),
        "data": {
            "task_id": task_id,
            "request_id": request_id,
            "host_ip": vm_host['ipaddress'],
            "uuid": uuid,
            "hostname": instance_name,  # 实例名
            "memory_mb": flavor_info['memory_mb'],
            "vcpu": flavor_info['vcpu'],
            "ostype": instance_system,
            "user_id": user_id,
            "disks": image_list,
            "disk_size": vm_disk_gb,
            "image_name": _image['url'].split('/')[-1],
            "net_area_id": net_area_id,
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


def _generate_instance_name(vm_env, dc_name, instance_system):
    '''
        生成实例名
        规则：机房名 + V(虚拟机) + L/W(操作系统) + K(kvm) + 实例ID
    :param dc_name:
    :param instance_system: 镜像操作系统
    :return:
    '''
    if instance_system == 'linux':
        name_sys = 'L'
    else:
        name_sys = 'W'

    # 如果环境类型为IST、PST，字母最后一位取'T'
    if int(vm_env) in ST_ENVIRONMENT:
        last_char = 'T'
    else:
        last_char = 'K'

    # sit环境的主机名区分一下
    if ENV == EnvType.SIT:
        prex_str = 'SIT' + dc_name + 'V' + name_sys + last_char
    else:
        prex_str = dc_name + 'V' + name_sys + last_char
    increment_value = increment_service.get_increment_of_prex(prex_str)
    return increment_value, prex_str


def _generate_4_num(value):
    '''
        生成4位数的数字
        这里假定一个机房下VM数不超过4位数
    :param value:
    :return:
    '''
    _len = len(str(value))
    if _len >= 4:
        return str(value)
    else:
        _left = 4 - _len
        _str = ''
        for i in range(0, _left):
            _str += '0'
        return _str + str(value)


def _generate_num(value):
    '''
        虚拟机名数字部分小于9999，生成4为字符；大于等于9999，返回原数字
    :param value:
    :return:
    '''
    _len = len(str(value))
    if value >= 9999:
        return str(value)
    else:
        _left = 4 - _len
        _str = ''
        for i in range(0, _left):
            _str += '0'
        return _str + str(value)


def check_group_quota(group_id, flavor_info, data_disk_gb, vm_count):
    '''
        判断应用组配额是否足够
    :param group_id:
    :param flavor_info:
    :param data_disk_gb:
    :param vm_count:
    :return:
    '''
    quota_used = group_s.get_group_quota_used(group_id)
    if not quota_used:
        logging.error('group %s has no quota used info when check group quota', group_id)
        return False, '没有该应用组配额使用情况，无法创建实例'

    group_num, group_info = group_s.GroupService().get_group_info(group_id)
    if group_num < 1:
        logging.error('no group %s info when check group quota', group_id)
        return False, '该应用组信息不存在，无法创建实例，请联系系统组处理'

    all_cpu_g = group_info[0]['cpu']
    all_mem_gb_g = group_info[0]['mem']
    all_disk_gb_g = group_info[0]['disk']
    all_vm_g = group_info[0]['vm']

    used_cpu_g = quota_used['all_vcpu']
    used_mem_mb_g = quota_used['all_mem_mb']
    used_disk_gb_g = quota_used['all_disk_gb']
    used_vm_g = quota_used['instance_num']

    cpu = flavor_info['vcpu']
    mem_mb = flavor_info['memory_mb']
    root_disk_gb = flavor_info['root_disk_gb']

    if int(used_vm_g) + int(vm_count) > int(all_vm_g):
        logging.error('group %s: vm used %s + apply count %s > all num %s',
                      group_id, used_vm_g, vm_count, all_vm_g)
        return False, '应用组VM配额已不够，无法创建实例，请联系系统组处理'

    if int(used_cpu_g) + int(cpu) * int(vm_count) > int(all_cpu_g):
        logging.error('group %s: cpu used %s + flavor cpu %s * num %s > all cpu %s',
                      group_id, used_cpu_g, cpu, vm_count, all_cpu_g)
        return False, '应用组CPU配额已不够，无法创建实例，请联系系统组处理'

    all_mem_mb_g = int(all_mem_gb_g) * 1024
    if int(used_mem_mb_g) + int(mem_mb) * int(vm_count) > all_mem_mb_g:
        logging.error('group %s: mem used %s + flavor mem %s * num %s > all mem %s',
                      group_id, used_mem_mb_g, mem_mb, vm_count, all_mem_mb_g)
        return False, '应用组MEM配额已不够，无法创建实例，请联系系统组处理'

    if int(used_disk_gb_g) + (int(root_disk_gb) + int(data_disk_gb)) * int(vm_count) > int(all_disk_gb_g):
        logging.error('group %s: disk used %s + (flavor disk %s + data disk %s) * num %s > all disk %s',
                      group_id, used_disk_gb_g, root_disk_gb, data_disk_gb, vm_count, all_disk_gb_g)
        return False, '应用组DISK配额已不够，无法创建实例，请联系系统组处理'

    return True, None


"""
def _check_ip_resource(hostpool_id, count):
    '''
        判断IP资源是否足够
    :param hostpool_id:
    :param count:
    :return:
    '''
    # hostpool -> 网络区域 -> n个网段
    segments_list = hostpool_service.get_segment_info(hostpool_id)
    if not segments_list:
        logging.error('创建VM 步骤5：检查IP资源失败 网段资源有误 '
                      'segment info is invalid in db when create instance, hostpool id: %s', hostpool_id)
        return False, {'msg': '该集群的网段资源不足，无法创建实例', 'ips': None, 'segment': None}

    ips_list, segment_data = ip_service.get_available_ips(segments_list, count)
    if not ips_list or len(ips_list) < int(count):
        logging.error('创建VM 步骤6：检查IP资源失败 IP资源不足 '
                      'ip resource is not enough in db when create instance')
        return False, {'msg': 'IP资源不足，无法创建实例', 'ips': None, 'segment': segment_data}

    return True, {'msg': 'success', 'ips': ips_list, 'segment': segment_data}
"""


def __check_ip_resource(env, dc_name, net_area, count):
    '''
        判断IP资源是否足够
    :param hostpool_id:
    :param count:
    :return:
    '''
    # 查询指定环境、网络区域是否有所需网段，容灾微应用需要遍历联通、电信所有可用网段
    if env == str(DataCenterType.MINIARCHDR):
        ret_segment_datas_telecom = segment_s.get_segments_data_by_type(net_area, dc_name, env,
                                                                        NetCardType.INTERNEL_TELECOM)
        ret_segment_datas_unicom = segment_s.get_segments_data_by_type(net_area, dc_name, env,
                                                                       NetCardType.INTERNEL_UNICOM)
        ret_segment_datas = ret_segment_datas_telecom + ret_segment_datas_unicom
    else:
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


def _check_instance_name_resource(vm_env, dc_name, instance_system, count):
    '''
        判断虚机名资源是否足够
    :param vm_env:
    :param dc_name:
    :param instance_system:
    :param count:
    :return:
    '''
    instance_name_list = []
    increment_value, prex_str = _generate_instance_name(vm_env, dc_name, instance_system)
    # # 控制4位数
    # if int(increment_value) + int(count) - 1 >= 10000:
    #     logging.error('datacenter %s instance name is exceed 9999 when generate instance name', dc_name)
    #     return False, None

    value = int(increment_value)
    for i in range(int(count)):
        new_name = prex_str + _generate_num(value)
        instance_name_list.append(new_name)
        value += 1

    increment_service.increase_increment_value(prex_str, int(count))
    return True, instance_name_list


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
        return False, '创建VM 步骤10：检查IP时无法更新资源锁状态为未使用中'
    return True, '创建VM 步骤10：检查IP时更新资源锁状态为未使用中成功'


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
        return False, '创建VM 步骤10：检查IP时无法更新资源锁状态为使用中'
    return True, '创建VM 步骤10：检查IP时更新资源锁状态为使用中成功'

