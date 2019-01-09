# coding=utf8
'''
    虚拟机管理-创建(外接平台生产容灾虚拟机创建)
'''


import logging
import os
from flask import request
from config.default import INSTANCE_MAX_CREATE, DATA_DISK_GB
from helper import encrypt_helper, json_helper
from helper.time_helper import get_datetime_str
from lib.mq.kafka_client import send_async_msg
from lib.vrtManager.util import randomUUID, randomMAC
from model.const_define import ErrorCode, IPStatus, VMStatus, VMTypeStatus, ImageType, VMCreateSource, \
    EnvType, VsJobStatus, DataCenterTypeForVishnu, AuditType, DataCenterType
from service.s_flavor import flavor_service
from service.s_host import host_service as host_s, host_schedule_service as host_s_s
from service.s_hostpool import hostpool_service
from service.s_image import image_service
from service.s_increment import increment_service
from service.s_instance import instance_host_service as ins_h_s, instance_ip_service as ins_ip_s, \
    instance_image_service as ins_img_s, instance_disk_service as ins_d_s, instance_service as ins_s, \
    instance_flavor_service as ins_f_s, instance_group_service as ins_g_s
from service.s_ip import ip_service, vip_service, segment_match, segment_service
from service.s_user.user_service import get_user
from service.s_user import user_service as user_s
from service.s_group import group_service as group_s
from service.s_area import area_service as area_s
from service.s_user_group import user_group_service as user_g_s
from service.s_request_record import request_record as request_r_s
from service.s_instance_action import instance_action as instance_a_s
from instance_retry_create import instance_msg_send_to_kafka
import threading
from config.default import ENV
from config import KAFKA_TOPIC_NAME
# from flask.ext.httpauth import HTTPBasicAuth
from flask_httpauth import HTTPBasicAuth
from helper.log_helper import CloudLogger, add_timed_rotating_file_handler
from service.s_access import access_service

auth_api_user = HTTPBasicAuth()


# 日志格式化
def _init_log(service_name):
    log_basic_path = os.path.dirname(os.path.abspath(__file__))[0:-29]
    log_name = log_basic_path + 'log/' + str(service_name) + '.log'
    add_timed_rotating_file_handler(log_name, logLevel='INFO')


@auth_api_user.login_required
def instance_create_from_other_platform_prd_dr():
    '''
      外部平台生产、容灾虚拟机创建
    :return:
    '''
    _init_log('instanc_create_request_from_vishnu_prd_dr')
    data_from_vishnu = request.data
    logging.info(data_from_vishnu)
    data_requset = json_helper.loads(data_from_vishnu)
    image_name = data_requset['image']
    vcpu = data_requset['vcpu']
    mem_mb = data_requset['mem_MB']
    disk_gb = data_requset['disk_GB']
    count = data_requset['count']
    dr_count = data_requset['dr_count']
    sys_code = data_requset['sys_code']
    opuser = data_requset['opUser']
    taskid_vs = data_requset['taskid']
    req_env = data_requset['env']
    req_net_area = data_requset['net_area']
    task_id_kvm = ins_s.generate_task_id()
    sys_opr_name = data_requset['Op_Main_Engineer_Primary']
    sys_opr_id = data_requset['Op_Main_Engineer_Prim']
    cluster_id = data_requset['cluster_id']
    vip_needed = data_requset['vip_needed']  # 是否需要vip，0为不需要，1需要
    # 前端暂时不是传虚拟机root密码过来
    password = None
    app_info = data_requset['application_info']

    logging.info('task %s : check params start when create instance', task_id_kvm)

    if not taskid_vs:
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                         detail='empty input of taskid when create instance')

    # 判断工单是否为失败重做
    check_job_data = {
        'WHERE_AND': {
            '=': {
                'taskid_api': taskid_vs
            },
        },
    }
    ret_job_num, ret_job_data = request_r_s.RequestRecordService().request_db_query_data(**check_job_data)
    if ret_job_num == 1:
        for _job_data in ret_job_data:
            if _job_data['task_status'] == '0':
                return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                                 detail='task is now doing, wait a moment, '
                                                                        'do not repeat create')
            elif _job_data['task_status'] == '1':
                # 将request_record数据库表中“task_status”、“response_to_api”重置为0重启任务
                update_db_time = get_datetime_str()
                _update_data = {
                    'task_status': '0',
                    'response_to_api': '0',
                    'finish_time': update_db_time,
                    'request_status_collect_time': update_db_time,
                }
                _where_data = {
                    'taskid_api': taskid_vs,
                }
                ret = request_r_s.RequestRecordService().update_request_status(_update_data, _where_data)
                if ret <= 0:
                    return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                                     detail='update request status failed, '
                                                                            'please call kvm system manager '
                                                                            'or retry create again')
                return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.SUCCEED,
                                                                 detail='start to recreate vm')
            elif _job_data['task_status'] == '2':
                threads = []
                # 将request_record数据库表中“task_status”、“response_to_api”重置为0重启任务
                update_db_time = get_datetime_str()
                _update_data = {
                    'task_status': '0',
                    'response_to_api': '0',
                    'finish_time': update_db_time,
                    'request_status_collect_time': update_db_time,
                }
                _where_data = {
                    'taskid_api': taskid_vs,
                }
                ret = request_r_s.RequestRecordService().update_request_status(_update_data, _where_data)
                if ret <= 0:
                    return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                                     detail='update request status failed, '
                                                                            'please call kvm system manager '
                                                                            'or retry create again')
                # 找到工单对应的虚拟机，发送task_id、request_id到kafka重新创建
                ins_params = {
                    'WHERE_AND': {
                        "=": {
                            'task_id': _job_data['taskid_kvm'],
                            'isdeleted': '0',
                            'status': '100'
                        }
                    },
                }
                ins_num, ins_data = ins_s.InstanceService().query_data(**ins_params)
                if ins_num > 0:
                    for per_ins_data in ins_data:
                        kafka_send_thread = threading.Thread(target=instance_msg_send_to_kafka,
                                                             args=(per_ins_data['task_id'], per_ins_data['request_id'],))
                        threads.append(kafka_send_thread)
                        kafka_send_thread.start()
                    # 判断多线程是否结束
                    for t in threads:
                        t.join()
                return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.SUCCEED,
                                                                 detail='start to recreate vm')

    if int(count) > int(INSTANCE_MAX_CREATE):
        logging.error('task %s : create count %s > max num %s when create instance',
                      task_id_kvm, count, INSTANCE_MAX_CREATE)
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                         detail='批量创建最大实例数不能超过%s个' % INSTANCE_MAX_CREATE)

    # 根据维石平台输入的虚拟机cpu、内存选择模板
    if not vcpu or not mem_mb or not disk_gb:
        logging.error('task %s : empty input of vcpu or mem_MB or disk_GB when create instance', task_id_kvm, image_name)
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                         detail='empty input of vcpu or mem_MB when create instance')
    flavor_query = flavor_service.get_flavor_by_vcpu_and_memory(vcpu, mem_mb)
    if not flavor_query:
        logging.error('task %s : can not get flavor information when create instance', task_id_kvm, image_name)
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                         detail='can not get flavor information when create instance')
    flavor_id = flavor_query['id']

    # 获取flavor详细信息
    flavor_info = flavor_service.FlavorService().get_flavor_info(flavor_id)
    if not flavor_info:
        logging.error('task %s : flavor %s info not in db when create instance', task_id_kvm, flavor_id)
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                         detail='实例规格数据有误，无法创建实例')

    # 获取镜像信息，一个image_name可能对应多个id
    image_nums, image_data = image_service.ImageService().get_images_by_name(image_name)
    if image_nums <= 0:
        logging.error('task %s : no image %s info in db when create instance', task_id_kvm, image_name)
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                         detail='没有镜像资源，无法创建实例')

    # 根据维石平台输入的系统运维人员工号维护对应应用组信息
    if not sys_opr_name or not sys_opr_id or not cluster_id:
        logging.error('task %s : empty input of sys_opr_name, sys_opr_id or cluster_id when create instance', task_id_kvm)
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                         detail='empty input of sys_opr_name, sys_opr_id '
                                                                'or cluster_id when create instance')

    ret_group, group_id = _user_group_check(sys_code, sys_opr_name, sys_opr_id, cluster_id)
    if not ret_group:
        logging.error('task %s : %s' % (task_id_kvm, group_id))
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                         detail=group_id)

    # 数据盘大小由配置文件中定义
    vm_disk_gb = int(disk_gb) if int(disk_gb) > DATA_DISK_GB else DATA_DISK_GB

    # 生产、容灾环境虚拟机资源分配
    prd_ret_status, prd_ret_msg, prd_vip_info = __product_environment_vm_resource_assign(req_env, req_net_area
                                                                                         , image_name, flavor_id
                                                                                         , vm_disk_gb, group_id, count
                                                                                         , flavor_info, vip_needed
                                                                                         , cluster_id, opuser, sys_code
                                                                                         , image_data, task_id_kvm
                                                                                         , app_info, sys_opr_id
                                                                                         , password, dr_count)
    if not prd_ret_status:
        # logging.error('task %s : %s' % (task_id_kvm, prd_ret_msg))
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                         detail=prd_ret_msg)

    # 录入维石的taskid到工单表格中
    time_now_for_insert_request_to_db = get_datetime_str()
    request_info_data = {
        "taskid_api": taskid_vs,
        "taskid_kvm": task_id_kvm,
        "vm_count": count,
        "user_id": opuser,
        "start_time": time_now_for_insert_request_to_db,
        "task_status": "0",  # 代表任务执行中
        "response_to_api": "0",
        "istraceing": "0",
        "request_status_collect_time": time_now_for_insert_request_to_db
    }
    request_record_db_ret = request_r_s.RequestRecordService().add_request_record_info(request_info_data)
    if request_record_db_ret.get('row_num') <= 0:
        logging.error('task %s : can not add request record information to db when create instance', task_id_kvm)
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                         detail='录入工单信息到数据库失败')

    if vip_needed == '1':
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.SUCCEED,
                                                         detail=prd_vip_info['ip_address'])
    else:
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.SUCCEED,
                                                         detail='start to create vm')


def _create_instance_info(task_id, instance_name, app_info, owner, password, flavor_id, group_id, vm_host, flavor_info,
                          image_data, ip_data, vm_disk_gb, mount_point, instance_system, net_area_id, segment_data,
                          vm_env, user_id, cluster_id):
    uuid = randomUUID()
    request_id = ins_s.generate_req_id()
    # 往instance表添加记录
    logging.info('task %s : insert instance table start when create instance', task_id)
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
        'password': None,
        'p_cluster_id': cluster_id,
        'request_id': request_id,
        'task_id': task_id
        # 'password': encrypt_helper.encrypt(str(password))  # 密码加密
    }
    ret = ins_s.InstanceService().add_instance_info(instance_data)
    if ret.get('row_num') <= 0:
        logging.error('task %s : add instance info error when create instance, insert_data: %s', task_id, instance_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    logging.info('task %s : insert instance table successful when create instance', task_id)

    instance_id = ret.get('last_id')

    # 往instance_flavor表添加记录
    logging.info('task %s : insert instance_flavor table start when create instance', task_id)
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
    logging.info('task %s : insert instance_flavor table successful when create instance', task_id)

    # 往instance_group表添加记录
    logging.info('task %s : insert instance_group table start when create instance', task_id)
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
    logging.info('task %s : insert instance_group table successful when create instance', task_id)

    # 往instance_host表添加记录
    logging.info('task %s : insert instance_host table start when create instance', task_id)
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
    logging.info('task %s : insert instance_host table successful when create instance', task_id)

    # host预分配资源
    logging.info('task %s : pre allocate host resource start when create instance', task_id)
    ret4 = host_s.pre_allocate_host_resource(
        vm_host['host_id'], flavor_info['vcpu'], flavor_info['memory_mb'], flavor_info['root_disk_gb'])
    if ret4 != 1:
        logging.error('task %s : pre allocate host resource to db error when create instance', task_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    logging.info('task %s : pre allocate host resource successful when create instance', task_id)

    # 往instance_image表添加记录
    logging.info('task %s : insert instance_image table start when create instance', task_id)
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
    logging.info('task %s : insert instance_image table successful when create instance', task_id)

    # 往instance_ip表添加记录
    logging.info('task %s : insert instance_ip table start when create instance', task_id)
    mac = randomMAC()
    data_ip_address = ip_data['ip_address']
    instance_ip_data = {
        'instance_id': instance_id,
        'ip_id': ip_data['id'],
        'mac': mac,
        'isdeleted': '0',
        'created_at': get_datetime_str()
    }
    ret6 = ins_ip_s.InstanceIPService().add_instance_ip_info(instance_ip_data)
    if ret6.get('row_num') <= 0:
        logging.error('task %s : add instance_ip info error when create instance, insert_data: %s',
                      task_id, instance_ip_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    logging.info('task %s : insert instance_ip table successful when create instance', task_id)

    # 标识该IP为已使用
    logging.info('task %s : set ip used start when create instance', task_id)
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
    logging.info('task %s : set ip used successful when create instance', task_id)

    # 拼装消息需要的镜像信息
    logging.info('task %s : piece together need image info start when create instance', task_id)
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
    logging.info('task %s : piece together need image info successful when create instance', task_id)

    # 发送异步消息到队列
    logging.info('task %s : send kafka message start when create instance', task_id)
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


def _generate_instance_name(dc_name, instance_system):
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

    # sit环境的主机名区分一下
    if ENV == EnvType.SIT:
        prex_str = 'SIT' + dc_name + 'V' + name_sys + 'K'
    else:
        prex_str = dc_name + 'V' + name_sys + 'K'
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
        return False, '该应用组信息不存在，无法创建实例'

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
        return False, '应用组VM配额已不够，无法创建实例'

    if int(used_cpu_g) + int(cpu) * int(vm_count) > int(all_cpu_g):
        logging.error('group %s: cpu used %s + flavor cpu %s * num %s > all cpu %s',
                      group_id, used_cpu_g, cpu, vm_count, all_cpu_g)
        return False, '应用组CPU配额已不够，无法创建实例'

    all_mem_mb_g = int(all_mem_gb_g) * 1024
    if int(used_mem_mb_g) + int(mem_mb) * int(vm_count) > all_mem_mb_g:
        logging.error('group %s: mem used %s + flavor mem %s * num %s > all mem %s',
                      group_id, used_mem_mb_g, mem_mb, vm_count, all_mem_mb_g)
        return False, '应用组MEM配额已不够，无法创建实例'

    if int(used_disk_gb_g) + (int(root_disk_gb) + int(data_disk_gb)) * int(vm_count) > int(all_disk_gb_g):
        logging.error('group %s: disk used %s + (flavor disk %s + data disk %s) * num %s > all disk %s',
                      group_id, used_disk_gb_g, root_disk_gb, data_disk_gb, vm_count, all_disk_gb_g)
        return False, '应用组DISK配额已不够，无法创建实例'

    return True, None


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
        logging.error('segment info is invalid in db when create instance, hostpool id: %s', hostpool_id)
        return False, {'msg': '该集群的网段资源不足，无法创建实例', 'ips': None, 'segment': None}

    ips_list, segment_data = ip_service.get_available_ips(segments_list, count)
    if not ips_list or len(ips_list) < int(count):
        logging.error('ip resource is not enough in db when create instance')
        return False, {'msg': 'IP资源不足，无法创建实例', 'ips': None, 'segment': segment_data}

    return True, {'msg': 'success', 'ips': ips_list, 'segment': segment_data}


def _check_vip_resource(hostpool_id, count=3):
    '''
        判断是否有一个网段足够需要三个分配ip
    :param hostpool_id:
    :param count:
    :return:
    '''
    # hostpool -> 网络区域 -> n个网段
    segments_list = hostpool_service.get_segment_info(hostpool_id)
    if not segments_list:
        logging.error('segment info is invalid in db when create instance, hostpool id: %s', hostpool_id)
        return False, {'msg': '该集群的网段资源不足，无法创建实例', 'ips': None, 'segment': None}

    ips_list, segment_data = ip_service.get_available_vips(segments_list, count)
    if not ips_list or len(ips_list) < int(count):
        logging.error('ip resource is not enough in db when create instance')
        return False, {'msg': 'IP资源不足，无法创建实例', 'ips': None, 'segment': segment_data}

    return True, {'msg': 'success', 'ips': ips_list, 'segment': segment_data}


def _check_instance_name_resource(dc_name, instance_system, count):
    '''
        判断虚机名资源是否足够
    :param dc_name:
    :param instance_system:
    :param count:
    :return:
    '''
    instance_name_list = []
    increment_value, prex_str = _generate_instance_name(dc_name, instance_system)
    # 控制4位数
    if int(increment_value) + int(count) - 1 >= 10000:
        logging.error('datacenter %s instance name is exceed 9999 when generate instance name', dc_name)
        return False, None

    value = int(increment_value)
    for i in range(int(count)):
        new_name = prex_str + _generate_4_num(value)
        instance_name_list.append(new_name)
        value += 1

    increment_service.increase_increment_value(prex_str, int(count))
    return True, instance_name_list


def _user_group_check(sys_code, sys_opr_name, sys_opr_id, cluster_id):
    # 检查应用系统管理员用户是否存在，不存在则新增
    user = user_s.UserService().get_user_info_by_user_id(sys_opr_id)
    if not user:
        # 用户不存在，新增，并将用户锁定，待后续开放用户运维在解锁
        user_data = {
            'userid': sys_opr_id,
            'username': sys_opr_name,
            'status': '1',
            'created_at': get_datetime_str()
        }
        user_ret = user_s.UserService().add_user(user_data)

        # 记录安全日志
        field_data = {
            'User_name': sys_opr_name or None,
            'Oper_type': 'add'
        }
        if user_ret.get('row_num') > 0:
            field_data.update({'Oper_result': '1 Success'})
            CloudLogger.audit(AuditType.USERMGR, field_data)
        else:
            field_data.update({'Oper_result': '0 Fail', 'fail_reason': 'insert new user info to db fail'})
            CloudLogger.audit(AuditType.USERMGR, field_data)
            return False, 'add new user info to db fail'

    # 检查应用组是否存在，不存在新建
    group = group_s.get_group_info_by_name(sys_code)
    if not group:
        group_data = {
            'name': sys_code,
            'displayname': sys_code,
            'isdeleted': '0',
            'owner': sys_opr_id,
            'cpu': 20000,
            'mem': 40000,
            'disk': 1000000,
            'vm': 5000,
            'p_cluster_id': cluster_id,
            'created_at': get_datetime_str()
        }
        group_ret = group_s.GroupService().add_group_info(group_data)
        if group_ret.get('row_num') <= 0:
            return False, 'add group info to db fail'

        group_id = group_ret.get('last_id')
        role_id = 2
        area_zb_ret = area_s.AreaService().get_area_zb_info()
        if not area_zb_ret:
            return False, 'get zongbu area id fail'
        area_zb_id = area_zb_ret['id']
        ret_result = access_service.add_access_list(int(group_id), int(role_id), str(area_zb_id))
        if ret_result.get('row_num') <= 0:
            return False, 'add access info to db fail'

        user_group_data = {
            'user_id': sys_opr_id,
            'user_name': sys_opr_name,
            'group_id': group_id,
            'group_name': sys_code,
            'role_id': role_id,
            'status': '0',
            'created_at': get_datetime_str(),
            'expire_at': get_datetime_str(),  # todo
        }
        ret_u_g = user_g_s.UserGroupService().add_user_group(user_group_data)
        if ret_u_g.get('row_num') <= 0:
            logging.error('add user group info error when add group, insert_data:%s', user_group_data)
            return False, 'add user group info to db fail'
    else:
        # 获取应用组对应用户信息
        role_id = 2
        opr_is_exist = False
        group_id = group['id']
        ret_num, ret_query_g_u = user_g_s.UserGroupService().get_alluser_group(group_id)
        for one_ret_query_g_u in ret_query_g_u:
            if one_ret_query_g_u['user_id'] == sys_opr_id:
                opr_is_exist = True
        if not opr_is_exist:
            # 将用户加入应用组中
            user_group_data = {
                'user_id': sys_opr_id,
                'user_name': sys_opr_name,
                'group_id': group_id,
                'group_name': sys_code,
                'role_id': role_id,
                'status': '0',
                'created_at': get_datetime_str(),
                'expire_at': get_datetime_str(),  # todo
            }
            ret_u_g = user_g_s.UserGroupService().add_user_group(user_group_data)
            if ret_u_g.get('row_num') <= 0:
                logging.error('add user group info error when add group, insert_data:%s', user_group_data)
                return False, 'add user group info to db fail'

            # 修改应用组owner
            update_data = {
                'owner': sys_opr_id
            }
            where_data = {
                'id': group_id,
            }
            ret_change_owner = group_s.update_group_info(update_data, where_data)
            if ret_change_owner < 0:
                logging.error("update group error, update_data:%s, where_data:%s", str(update_data), str(where_data))
                return False, 'update group owner to db fail'

    return True, group_id


def __product_environment_vm_resource_assign(req_env, req_net_area, image_name, flavor_id, disk_gb, group_id, count,
                                             flavor_info, vip_needed, cluster_id, opuser, sys_code, image_data,
                                             task_id_kvm, app_info, sys_opr_id, password, dr_count):
    '''
        生产环境虚拟机资源分配，返回的参数中ip信息将为容灾环境提供参考
    :param req_env:
    :param req_net_area:
    :param image_name:
    :param flavor_id:
    :param disk_gb:
    :param group_id:
    :param count:
    :param flavor_info:
    :param vip_needed:
    :param cluster_id:
    :param opuser:
    :param sys_code:
    :param image_data:
    :param task_id_kvm:
    :param app_info:
    :param sys_opr_id:
    :param password:
    :return:
    '''

    prd_vip_info = []
    # 组配额控制
    is_quota_enough, quota_msg = check_group_quota(group_id, flavor_info, disk_gb, count)
    if not is_quota_enough:
        return False, '资源组配额不足，无法创建实例', prd_vip_info

    # 根据维石平台输入的环境、网络区域查找对应的物理集群
    if not req_env or not req_net_area:
        return False, 'empty input of req_net_area or req_env when create product environment instance', prd_vip_info
    hostpool_query = hostpool_service.get_hostpool_info_zb(str(DataCenterTypeForVishnu.TYPE_DICT[req_env]), req_net_area)
    if not hostpool_query:
        return False, 'can not get host_pool information when create product environment instance', prd_vip_info
    hostpool_id = hostpool_query['hostpool_id']

    if not hostpool_id or not image_name or not flavor_id or not disk_gb or not group_id \
            or not count or int(count) < 1:
        return False, 'empty input of image_name, disk_gb or count when create product environment instance', prd_vip_info

    # 获取hostpool的net area信息
    hostpool_info = hostpool_service.HostPoolService().get_hostpool_info(hostpool_id)
    if not hostpool_info:
        return False, '生产环境物理机资源池所属网络区域信息有误，无法创建实例', prd_vip_info

    net_area_id = hostpool_info['net_area_id']

    # 获取集群所在的环境
    vm_env = hostpool_service.get_env_of_hostpool(hostpool_id)
    # hostpool对应的机房名
    dc_name = hostpool_service.get_dc_name_of_hostpool(hostpool_id)
    # 实例操作系统
    instance_system = image_data[0]['system']

    # 获取虚机名资源
    is_name_enough, instance_name_list = _check_instance_name_resource(dc_name, instance_system, count)
    if not is_name_enough:
        return False, '生产环境主机名资源不足，无法创建实例', prd_vip_info

    # 获取IP资源
    if vip_needed == '1':
        is_ips_enough, ips_req = _check_vip_resource(hostpool_id, int(count) + 1)
        if not is_ips_enough:
            return False, ips_req['msg'], prd_vip_info
    else:
        is_ips_enough, ips_req = _check_ip_resource(hostpool_id, count)
        if not is_ips_enough:
            return False, ips_req['msg'], prd_vip_info
    ips_list = ips_req['ips']
    segment_data = ips_req['segment']

    # 判断容灾是否有对应网段
    dr_segment_check_status, dr_segment_check_msg = __check_dr_segment_resource(ips_list)
    if not dr_segment_check_status:
        return False, "生产环境资源分配：" + dr_segment_check_msg, prd_vip_info

    # 将IP预先占用
    _ip_change_db_status, _change_db_ip_msg = __change_db_ip_used(ips_list)
    if not _ip_change_db_status:
        __change_db_ip_unused(ips_list)
        return False, "生产环境资源分配：" + _change_db_ip_msg, prd_vip_info

    # 如果需要vip，分配第‘count + 1’个同时记录vip_info表格
    vip = []
    if vip_needed == '1':
        vip = ips_list[count]
        # 录入vip信息到数据库中
        insert_vip_data = {
            'ip_id': vip['id'],
            'cluster_id': cluster_id,
            'apply_user_id': opuser,
            'sys_code': sys_code,
            'isdeleted': '0',
            'created_at': get_datetime_str()
        }
        ret_vip = vip_service.VIPService().add_vip_info(insert_vip_data)
        if ret_vip.get('row_num') <= 0:
            __change_db_ip_unused(ips_list)
            return False, "生产环境录入vip信息失败，请联系系统管理员", prd_vip_info

    # 获取主机列表(不包括锁定、维护状态)
    all_hosts_nums, all_hosts_data = host_s.HostService().get_available_hosts_of_hostpool(hostpool_id)
    # 可用物理机数量不足
    least_host_num = hostpool_service.HostPoolService().get_least_host_num(hostpool_id)
    if all_hosts_nums < least_host_num or all_hosts_nums < 1:
        __change_db_ip_unused(ips_list)
        return False, '生产环境集群物理机数量小于1，无法创建实例', prd_vip_info

    # 过滤host
    hosts_after_filter = host_s_s.filter_hosts(all_hosts_data)
    if len(hosts_after_filter) == 0 or len(hosts_after_filter) < least_host_num:
        __change_db_ip_unused(ips_list)
        return False, '生产环境没有满足过滤条件物理机，无法创建实例', prd_vip_info

    # VM分配给HOST
    vm = {
        "vcpu": flavor_info['vcpu'],
        "mem_MB": flavor_info['memory_mb'],
        "disk_GB": flavor_info['root_disk_gb'] + disk_gb,  # 系统盘加数据盘
        "group_id": group_id,
        "count": count
    }
    host_list = host_s_s.match_hosts(hosts_after_filter, vm, least_host_num=least_host_num, max_disk=2000)
    host_len = len(host_list)
    if host_len == 0:
        __change_db_ip_unused(ips_list)
        return False, '生产环境没有足够资源的物理机机，无法创建实例', prd_vip_info

    # 判断容灾物理机资源是否充足
    dr_ret_status, dr_ret_msg = __dr_environment_vm_resource_assign(DataCenterType.DR, req_net_area, image_name
                                                                    , flavor_id, disk_gb, group_id, dr_count
                                                                    , flavor_info, vip_needed, cluster_id, opuser
                                                                    , sys_code, image_data, task_id_kvm, app_info
                                                                    , sys_opr_id, password, ips_list, count)

    if not dr_ret_status:
        __change_db_ip_unused(ips_list)
        return False, dr_ret_msg

    # 挂载点
    if instance_system == 'linux':
        mount_point = '/app'
    else:
        mount_point = 'E'

    user_id = get_user()['user_id']
    all_threads = []
    for i in range(int(count)):
        instance_name = str(instance_name_list[i])
        ip_data = ips_list[i]

        # 轮询host
        index = i % host_len
        vm_host = host_list[index]

        create_ins_t = threading.Thread(target=_create_instance_info,
                                        args=(task_id_kvm, instance_name, app_info, sys_opr_id, password, flavor_id, group_id, vm_host,
                                              flavor_info, image_data, ip_data, disk_gb, mount_point, instance_system,
                                              net_area_id, segment_data, vm_env, user_id, cluster_id),
                                        name='thread-instance-create-' + task_id_kvm)
        all_threads.append(create_ins_t)

    for thread in all_threads:
        thread.start()

    return True, '生产环境资源分配成功', vip


def __dr_environment_vm_resource_assign(req_env, req_net_area, image_name, flavor_id, disk_gb, group_id, count
                                        , flavor_info, vip_needed, cluster_id, opuser, sys_code, image_data
                                        , task_id_kvm, app_info, sys_opr_id, password, prd_ips_info, prd_vm_count):
    '''
        容灾环境虚拟机资源分配，只有生产环境分配成功才会进入下面逻辑
    :param req_env:
    :param req_net_area:
    :param image_name:
    :param flavor_id:
    :param disk_gb:
    :param group_id:
    :param count:
    :param flavor_info:
    :param vip_needed:
    :param cluster_id:
    :param opuser:
    :param sys_code:
    :param image_data:
    :param task_id_kvm:
    :param app_info:
    :param sys_opr_id:
    :param password:
    :param prd_ips_info:
    :return:
    '''

    # 组配额控制
    is_quota_enough, quota_msg = check_group_quota(group_id, flavor_info, disk_gb, count)
    if not is_quota_enough:
        return False, '资源组配额不足，无法创建实例'

    # 根据维石平台输入的环境、网络区域查找对应的物理集群
    if not req_env or not req_net_area:
        return False, 'empty input of req_net_area or req_env when create dr environment instance'
    hostpool_query = hostpool_service.get_hostpool_info_zb(str(req_env), req_net_area)
    if not hostpool_query:
        return False, 'can not get host_pool information when create dr environment instance'
    hostpool_id = hostpool_query['hostpool_id']

    if not hostpool_id or not image_name or not flavor_id or not disk_gb or not group_id \
            or not count or int(count) < 1:
        return False, 'empty input of image_name, disk_gb or count when create dr environment instance'

    # 获取hostpool的net area信息
    hostpool_info = hostpool_service.HostPoolService().get_hostpool_info(hostpool_id)
    if not hostpool_info:
        return False, '容灾环境物理机资源池所属网络区域信息有误，无法创建实例'

    net_area_id = hostpool_info['net_area_id']

    # 获取集群所在的环境
    vm_env = hostpool_service.get_env_of_hostpool(hostpool_id)
    # hostpool对应的机房名
    dc_name = hostpool_service.get_dc_name_of_hostpool(hostpool_id)
    # 实例操作系统
    instance_system = image_data[0]['system']

    # 获取虚机名资源
    is_name_enough, instance_name_list = _check_instance_name_resource(dc_name, instance_system, count)
    if not is_name_enough:
        return False, '容灾环境主机名资源不足，无法创建实例'

    # 获取IP资源
    dr_segment_check_status, dr_segment_check_msg = __check_dr_segment_resource(prd_ips_info)
    is_ips_enough, ips_req = __assign_dr_ip_resource(prd_ips_info, dr_segment_check_msg)

    if not is_ips_enough:
        return False, ips_req['msg']

    ips_list = ips_req['ips']
    segment_data = ips_req['segment']

    # 将容灾IP标记应用组
    _ip_change_db_status, _change_db_ip_msg = __change_db_dr_ip_group_id(ips_list, group_id=group_id)
    if not _ip_change_db_status:
        __remove_db_dr_ip_group_id(ips_list)
        return False, "容灾环境" + _change_db_ip_msg

    # 如果需要vip，分配第‘count + 1’个同时记录vip_info表格
    if vip_needed == '1':
        vip = ips_list[prd_vm_count]
        # 录入vip信息到数据库中
        insert_vip_data = {
            'ip_id': vip['id'],
            'cluster_id': cluster_id,
            'apply_user_id': opuser,
            'sys_code': sys_code,
            'isdeleted': '0',
            'created_at': get_datetime_str()
        }
        ret_vip = vip_service.VIPService().add_vip_info(insert_vip_data)
        if ret_vip.get('row_num') <= 0:
            __remove_db_dr_ip_group_id(ips_list)
            return False, "容灾环境录入vip信息失败，请联系系统管理员"

    # 获取主机列表(不包括锁定、维护状态)
    all_hosts_nums, all_hosts_data = host_s.HostService().get_available_hosts_of_hostpool(hostpool_id)
    # 可用物理机数量不足
    least_host_num = hostpool_service.HostPoolService().get_least_host_num(hostpool_id)
    if all_hosts_nums < least_host_num or all_hosts_nums < 1:
        __remove_db_dr_ip_group_id(ips_list)
        return False, '容灾环境集群物理机数量小于1，无法创建实例'

    # 过滤host
    hosts_after_filter = host_s_s.filter_hosts(all_hosts_data)
    if len(hosts_after_filter) == 0 or len(hosts_after_filter) < least_host_num:
        __remove_db_dr_ip_group_id(ips_list)
        return False, '容灾环境没有满足过滤条件物理机，无法创建实例'

    # VM分配给HOST
    vm = {
        "vcpu": flavor_info['vcpu'],
        "mem_MB": flavor_info['memory_mb'],
        "disk_GB": flavor_info['root_disk_gb'] + disk_gb,  # 系统盘加数据盘
        "group_id": group_id,
        "count": count
    }
    host_list = host_s_s.match_hosts(hosts_after_filter, vm, least_host_num=least_host_num, max_disk=2000)
    host_len = len(host_list)
    if host_len == 0:
        __remove_db_dr_ip_group_id(ips_list)
        return False, '容灾环境没有足够资源的物理机机，无法创建实例'

    # 挂载点
    if instance_system == 'linux':
        mount_point = '/app'
    else:
        mount_point = 'E'

    user_id = get_user()['user_id']
    all_threads = []
    for i in range(int(count)):
        instance_name = str(instance_name_list[i])
        ip_data = ips_list[i]

        # 轮询host
        index = i % host_len
        vm_host = host_list[index]

        create_ins_t = threading.Thread(target=_create_instance_info,
                                        args=(task_id_kvm, instance_name, app_info, sys_opr_id, password, flavor_id
                                              , group_id, vm_host, flavor_info, image_data, ip_data, disk_gb
                                              , mount_point, instance_system, net_area_id, segment_data, vm_env, user_id
                                              , cluster_id),
                                        name='thread-instance-create-' + task_id_kvm)
        all_threads.append(create_ins_t)

    for thread in all_threads:
        thread.start()

    return True, '容灾环境资源分配成功', ips_list


def __change_db_ip_used(ips, group_id=None):
    '''
        修改数据库ip表中ip状态为已使用
    :param ips_info:
    :return:
    '''
    for ip in ips:
        update_data = {
            'status': IPStatus.USED,
            'group_id': group_id
        }
        where_data = {
            'id': ip['id']
        }
        ret_mark_ip = ip_service.IPService().update_ip_info(update_data, where_data)
        if ret_mark_ip <= 0:
            msg = "标记ip：%s 为已使用失败" % ip
            return False, msg
    return True, "标记所有IP已使用成功"


def __change_db_dr_ip_group_id(ips, group_id=None):
    '''
        修改数据库ip表中容灾ip所属应用组
    :param ips_info:
    :return:
    '''
    for ip in ips:
        update_data = {
            'group_id': group_id
        }
        where_data = {
            'id': ip['id']
        }
        ret_mark_ip = ip_service.IPService().update_ip_info(update_data, where_data)
        if ret_mark_ip <= 0:
            msg = "标记ip：%s 应用组失败" % ip
            return False, msg
    return True, "标记所有IP应用组成功"


def __change_db_ip_unused(ips, group_id=None):
    '''
        修改数据库ip表中ip状态为未使用
    :param ips_info:
    :return:
    '''
    for ip in ips:
        update_data = {
            'status': IPStatus.UNUSED,
            'group_id': group_id
        }
        where_data = {
            'id': ip['id']
        }
        ret_mark_ip = ip_service.IPService().update_ip_info(update_data, where_data)
        if ret_mark_ip <= 0:
            msg = "标记ip：%s 为未使用失败" % ip
            logging.error(msg)
            return False, msg
    return True, "标记所有ip为未使用成功"


def __remove_db_dr_ip_group_id(ips, group_id=None):
    '''
        取消数据库ip表中容灾ip所属应用组标记
    :param ips_info:
    :return:
    '''
    for ip in ips:
        update_data = {
            'group_id': group_id
        }
        where_data = {
            'id': ip['id']
        }
        ret_mark_ip = ip_service.IPService().update_ip_info(update_data, where_data)
        if ret_mark_ip <= 0:
            msg = "取消标记ip：%s 应用组失败" % ip
            logging.error(msg)
            return False, msg
    return True, "取消标记所有ip应用组成功"


def __check_dr_segment_resource(prd_ips_info):
    '''
        根据生产ip信息校验容灾环境是否有对应网段信息
    :param prd_ips_info:
    :return:
    '''
    dr_segment_id_info = segment_match.SegmentMatchService().get_segment_match_info_by_prd_segment_id(prd_ips_info[0]['segment_id'])
    if not dr_segment_id_info:
        logging.error('无法获取生产网段对应的容灾网段信息，请联系KVM管理员')
        return False, '无法获取生产网段对应的容灾网段信息，请联系KVM管理员'

    dr_segment_id = dr_segment_id_info['dr_segment_id']

    dr_segment_info = segment_service.SegmentService().get_segment_info(dr_segment_id)
    if not dr_segment_info:
        logging.error('无法获取容灾网段信息，请联系KVM管理员')
        return False, '无法获取容灾网段信息，请联系KVM管理员'

    return True, dr_segment_info


def __assign_dr_ip_resource(prd_ips_info, dr_segment_info):
    '''
        根据生产环境ip信息生成容灾环境ip
    :param prd_ips_info:
    :param dr_segment_info:
    :return:
    '''
    dr_ips_list = []
    for prd_ip in prd_ips_info:
        # 拼凑虚拟机容灾ip
        dr_ip = dr_segment_info['segment'].split('.')[0] + dr_segment_info['segment'].split('.')[1] \
                + prd_ip['ip_address'].split('.')[2] + prd_ip['ip_address'].split('.')[3]
        # 通过ip地址获取容灾环境ip详细信息
        dr_ip_data = ip_service.IPService().get_ip_info_by_ipaddress(dr_ip)
        if not dr_ip_data:
            # ip未初始化，默认把ip初始化，提高容灾创建成功率
            return False, {'msg': 'ip未初始化，请在kvm平台中把ip初始化后在重试创建', 'ips': dr_ips_list, 'segment': dr_segment_info}
        else:
            dr_ips_list.append(dr_ip_data)

    return True, {'msg': 'success', 'ips': dr_ips_list, 'segment': dr_segment_info}


@auth_api_user.verify_password
def verify_api_user_pwd(username_or_token, password):
    if not username_or_token:
        return False
    api_user = user_s.verify_api_auth_token(username_or_token)
    if not api_user:
        api_user = user_s.UserService().get_user_info_by_user_id(username_or_token)
        if not api_user or not user_s.verify_password(password, api_user['password']):
            return False
        if api_user['auth_type'] != 2:
            return False
    elif api_user['auth_type'] != 2:
        return False
    return True
