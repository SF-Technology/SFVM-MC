# coding=utf8
'''
    虚拟机管理-创建(外接平台,由外部接口指定ip创建虚拟机)
'''
# __author__ =  ""

import logging
import os
from flask import request
from config.default import INSTANCE_MAX_CREATE, DATA_DISK_GB, ST_ENVIRONMENT
from helper import encrypt_helper, json_helper, string_random_helper
from helper.time_helper import get_datetime_str
from lib.mq.kafka_client import send_async_msg
from lib.vrtManager.util import randomUUID, randomMAC
from model.const_define import ErrorCode, IPStatus, VMStatus, VMTypeStatus, ImageType, VMCreateSource, \
    EnvType, VsJobStatus, DataCenterTypeForVishnu, AuditType, ApiOrigin, ApiOriginString, InstanceNicType, \
    DataCenterTypeTransformCapital
from service.s_flavor import flavor_service
from service.s_host import host_service as host_s, host_schedule_service as host_s_s
from service.s_hostpool import hostpool_service
from service.s_image import image_service
from service.s_increment import increment_service
from service.s_instance import instance_host_service as ins_h_s, instance_ip_service as ins_ip_s, \
    instance_image_service as ins_img_s, instance_disk_service as ins_d_s, instance_service as ins_s, \
    instance_flavor_service as ins_f_s, instance_group_service as ins_g_s
from service.s_ip import ip_service, vip_service, segment_service
from service.s_user.user_service import get_user
from service.s_user import user_service as user_s
from service.s_group import group_service as group_s
from service.s_area import area_service as area_s
from service.s_user_group import user_group_service as user_g_s
from service.s_request_record import request_record as request_r_s
from instance_retry_create import instance_msg_send_to_kafka
import threading
from config.default import ENV
from config import KAFKA_TOPIC_NAME
# from flask.ext.httpauth import HTTPBasicAuth
from flask_httpauth import HTTPBasicAuth
from helper.log_helper import CloudLogger, add_timed_rotating_file_handler
from service.s_access import access_service
from controller.web_api.ip_filter_decorator import ip_filter_from_other_platform

auth_api_user = HTTPBasicAuth()


# 日志格式化
def _init_log(service_name):
    log_basic_path = os.path.dirname(os.path.abspath(__file__))[0:-29]
    log_name = log_basic_path + 'log/' + str(service_name) + '.log'
    add_timed_rotating_file_handler(log_name, logLevel='INFO')


@ip_filter_from_other_platform
@auth_api_user.login_required
def instance_create_from_other_platform_with_ip():
    '''
      外部平台虚拟机创建
    :return:
    '''
    _init_log('instanc_create_request_from_other_platform')
    data_from_other_platform = request.data
    logging.info(data_from_other_platform)
    data_requset = json_helper.loads(data_from_other_platform)
    image_name = data_requset['image']
    vcpu = data_requset['vcpu']
    mem_mb = data_requset['mem_MB']
    disk_gb = data_requset['disk_GB']
    count = data_requset['count']
    sys_code = data_requset['sys_code']
    opuser = data_requset['opUser']
    taskid_vs = data_requset['taskid']
    req_env = data_requset['env']
    req_net_area = data_requset['net_area']
    req_datacenter = data_requset['datacenter']
    task_id_kvm = ins_s.generate_task_id()
    sys_opr_name = data_requset['Op_Main_Engineer_Primary']
    sys_opr_id = data_requset['Op_Main_Engineer_Prim']
    cluster_id = data_requset['cluster_id']
    vip_needed = data_requset['vip_needed']  # 是否需要vip，0为不需要，1需要
    vm_ip_info = data_requset['vm_info']
    vip_info = data_requset['vip_info']
    api_origin = data_requset['apiOrigin']  # api名称，维石为vishnu, 软负载为sfslb, 其他的需要定义
    # 前端暂时不是传虚拟机root密码过来
    password = None
    app_info = data_requset['application_info']
    # hostpool_id = int(data_requset['hostpool_id'])  # 特殊类型应用，返回集群id
    hostpool_id = ''

    logging.info('task %s : check params start when create instance', task_id_kvm)

    if not taskid_vs or not api_origin:
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                         detail='empty input of taskid or api_origin when create '
                                                                'instance')

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

    if api_origin == ApiOriginString.VISHNU:
        api_origin = ApiOrigin.VISHNU
    elif api_origin == ApiOriginString.SFSLB:
        api_origin = ApiOrigin.SFSLB
    elif api_origin == ApiOriginString.FWAF:
        api_origin = ApiOrigin.FWAF
    else:
        api_origin = ApiOrigin.VISHNU

    if vip_needed == '1' and len(vip_info) <= 0:
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                         detail='empty input of vip datas when create instance')

    # 校验前端vip是否存在数据库中且ip为预保留状态
    if vip_needed == '1':
        vip_available = 0
        vip_info_list = []
        for per_vip in vip_info:
            per_vip_info = ip_service.IPService().get_ip_by_ip_address(per_vip['ip'])
            if per_vip_info and per_vip_info['status'] == IPStatus.PRE_ALLOCATION:
                vip_info_list.append(per_vip_info)
                vip_available += 1

        if vip_available != len(vip_info):
            return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                             detail='vip nums from vishnu not equal apply vip nums '
                                                                    'when create instance')

    # 校验前端ip是否存在数据库中且ip为预保留状态
    ip_available = 0
    ip_info_list = []
    for per_ip in vm_ip_info:
        per_ip_info = ip_service.IPService().get_ip_by_ip_address(per_ip['ip'])
        if per_ip_info and per_ip_info['status'] == IPStatus.PRE_ALLOCATION:
            ip_info_list.append(per_ip_info)
            ip_available += 1

    if ip_available != int(count):
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                         detail='vm ip nums from vishnu not equal apply vm nums '
                                                                'when create instance')

    # 获取ip对应的网段信息
    segment_info = segment_service.SegmentService().get_segment_info(ip_info_list[0]['segment_id'])
    if not segment_info:
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                         detail='can not find segment infomation for ip '
                                                                'when create instance')

    # 根据维石平台输入的虚拟机cpu、内存选择模板
    if not vcpu or not mem_mb:
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                         detail='empty input of vcpu or mem_MB when create instance')
    flavor_query = flavor_service.get_flavor_by_vcpu_and_memory(vcpu, mem_mb)
    if not flavor_query:
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                         detail='can not get flavor information when create instance')
    flavor_id = flavor_query['id']

    # 根据维石平台输入的环境、网络区域查找对应的物理集群
    if not req_env or not req_net_area:
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                         detail='empty input of req_net_area or req_env '
                                                                'when create instance')
    if not hostpool_id:
        hostpool_query = hostpool_service.get_hostpool_info_by_name(str(DataCenterTypeForVishnu.TYPE_DICT[req_env]),
                                                                    req_datacenter, req_net_area)
        if not hostpool_query:
            return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                             detail='can not get host_pool information '
                                                                    'when create instance')
        hostpool_id = hostpool_query['hostpool_id']

    # 根据维石平台输入的系统运维人员工号维护对应应用组信息
    if not sys_opr_id or not cluster_id:
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                         detail='empty input of sys_opr_name, sys_opr_id '
                                                                'or cluster_id when create instance')

    ret_group, group_id = _user_group_check(str(DataCenterTypeForVishnu.TYPE_DICT[req_env]), sys_code, sys_opr_name, sys_opr_id, cluster_id)
    if not ret_group:
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                         detail=group_id)

    if not hostpool_id or not image_name or not flavor_id or not disk_gb or not group_id \
            or not count or int(count) < 1:
        logging.error('task %s : params are invalid when create instance', task_id_kvm)
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                         detail='empty input of image_name, disk_gb '
                                                                'or count when create instance')

    if int(count) > int(INSTANCE_MAX_CREATE):
        logging.error('task %s : create count %s > max num %s when create instance',
                      task_id_kvm, count, INSTANCE_MAX_CREATE)
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                         detail='批量创建最大实例数不能超过32个')

    logging.info('task %s : check params successful when create instance', task_id_kvm)

    # 数据盘最少50GB
    # 这里只是一个数据盘，后面有多个数据盘
    vm_disk_gb = int(disk_gb) if int(disk_gb) > DATA_DISK_GB else DATA_DISK_GB

    # 获取主机列表(不包括锁定、维护状态)
    logging.info('task %s : get all hosts in hostpool %s start when create instance', task_id_kvm, hostpool_id)
    all_hosts_nums, all_hosts_data = host_s.HostService().get_available_hosts_of_hostpool(hostpool_id)
    # 可用物理机数量不足
    least_host_num = hostpool_service.HostPoolService().get_least_host_num(hostpool_id)
    if all_hosts_nums < least_host_num or all_hosts_nums < 1:
        logging.error('task %s : available host resource not enough when create instance', task_id_kvm)
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                         detail='集群不够资源，无法创建实例')
    logging.info('task %s : get all hosts in hostpool %s successful, all hosts nums %s when create instance',
                 task_id_kvm, hostpool_id, all_hosts_nums)

    # 过滤host
    logging.info('task %s : filter hosts start when create instance', task_id_kvm)
    hosts_after_filter = host_s_s.filter_hosts(all_hosts_data)
    if len(hosts_after_filter) == 0 or len(hosts_after_filter) < least_host_num:
        logging.error('task %s : no available host when create instance', task_id_kvm)
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                         detail='没有适合的主机，无法创建实例')
    logging.info('task %s : filter hosts successful when create instance', task_id_kvm)

    logging.info('task %s : get need info start when create instance', task_id_kvm)
    # 获取flavor信息
    flavor_info = flavor_service.FlavorService().get_flavor_info(flavor_id)
    if not flavor_info:
        logging.error('task %s : flavor %s info not in db when create instance', task_id_kvm, flavor_id)
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                         detail='实例规格数据有误，无法创建实例')

    # VM分配给HOST
    logging.info('task %s : match hosts start when create instance', task_id_kvm)
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
        logging.error('task %s : match host resource not enough when create instance', task_id_kvm)
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                         detail='没有适合的主机，无法创建实例')
    logging.info('task %s : match hosts successful when create instance', task_id_kvm)

    # 获取hostpool的net area信息
    hostpool_info = hostpool_service.HostPoolService().get_hostpool_info(hostpool_id)
    if not hostpool_info:
        logging.error('task %s : hostpool %s info not in db when create instance', task_id_kvm, hostpool_id)
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                         detail='物理机池所属网络区域信息有误，无法创建实例')

    net_area_id = hostpool_info['net_area_id']
    logging.info('task %s : get need info successful when create instance', task_id_kvm)

    # 组配额控制
    logging.info('task %s : check group quota start when create instance', task_id_kvm)
    is_quota_enough, quota_msg = check_group_quota(group_id, flavor_info, vm_disk_gb, count)
    if not is_quota_enough:
        logging.error('task %s : group %s is no enough quota when create instance', task_id_kvm, group_id)
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                         detail='资源组配额不足，无法创建实例')
    logging.info('task %s : check group quota successful when create instance', task_id_kvm)

    ips_list = ip_info_list
    segment_data = segment_info
    logging.info('task %s : check ip resource start when create instance', task_id_kvm)

    logging.info('task %s : get need 1 info start when create instance', task_id_kvm)
    # 获取镜像信息，一个image_name可能对应多个id
    image_nums, image_data = image_service.ImageService().get_images_by_name(image_name)
    if image_nums <= 0:
        logging.info('task %s : no image %s info in db when create instance', task_id_kvm, image_name)
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                         detail='没有镜像资源，无法创建实例')

    # 获取集群所在的环境
    vm_env = hostpool_service.get_env_of_hostpool(hostpool_id)
    # hostpool对应的机房名
    dc_name = hostpool_service.get_dc_name_of_hostpool(hostpool_id)
    # 实例操作系统
    instance_system = image_data[0]['system']
    logging.info('task %s : get need 1 info successful when create instance', task_id_kvm)

    # 获取虚机名资源
    logging.info('task %s : check instance name resource start when create instance', task_id_kvm)
    is_name_enough, instance_name_list = _check_instance_name_resource(vm_env, dc_name, instance_system, count)
    if not is_name_enough:
        logging.error('task %s : datacenter %s has no enough instance name resource', task_id_kvm, dc_name)
        return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                         detail='主机名资源不足，无法创建实例')
    logging.info('task %s : check instance name resource successful when create instance', task_id_kvm)

    # 如果需要vip，分配第‘count + 1’个同时记录vip_info表格
    if vip_needed == '1':
        for per_avalible_vip in vip_info_list:
            # 标记ip已使用
            update_vip_data = {
                'status': IPStatus.USED
            }
            where_vip_data = {
                'id': per_avalible_vip['id']
            }
            ret_mark_ip = ip_service.IPService().update_ip_info(update_vip_data, where_vip_data)
            if ret_mark_ip <= 0:
                return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                                 detail="标记ip为已使用状态失败，请重新申请")
            # 录入vip信息到数据库中
            insert_vip_data = {
                'ip_id': per_avalible_vip['id'],
                'cluster_id': cluster_id,
                'apply_user_id': opuser,
                'sys_code': sys_code,
                'isdeleted': '0',
                'created_at': get_datetime_str()
            }
            ret_vip = vip_service.VIPService().add_vip_info(insert_vip_data)
            if ret_vip.get('row_num') <= 0:
                return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.FAILED,
                                                                 detail="录入ip信息失败，请联系系统管理员")

    # 挂载点
    if instance_system == 'linux':
        mount_point = '/app'
    else:
        mount_point = 'E'

    logging.info('task %s : create thread start when create instance', task_id_kvm)
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
                                              flavor_info, image_data, ip_data, vm_disk_gb, mount_point, instance_system,
                                              net_area_id, segment_data, vm_env, user_id, cluster_id),
                                        name='thread-instance-create-' + task_id_kvm)
        all_threads.append(create_ins_t)
        create_ins_t.start()

    for thread in all_threads:
        thread.join()

    logging.info('task %s : create thread successful when create instance', task_id_kvm)
    # 录入外应用的taskid到工单表格中
    time_now_for_insert_request_to_db = get_datetime_str()
    request_info_data = {
        "taskid_api": taskid_vs,
        "api_origin": api_origin,
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

    return json_helper.format_api_resp_msg_to_vishnu(req_id=taskid_vs, job_status=VsJobStatus.SUCCEED,
                                                     detail='start to create vm')


def hostpool_info_init():
    hostpool_info = hostpool_service.get_hostpool_info()
    for each in hostpool_info:
        dc_type = each["env"]
        each["env"] = DataCenterTypeTransformCapital.MSG_DICT[int(dc_type)]

    return json_helper.format_api_resp(ErrorCode.SUCCESS, data=hostpool_info)


def _create_instance_info(task_id, instance_name, app_info, owner, password, flavor_id, group_id, vm_host, flavor_info,
                          image_data, ip_data, vm_disk_gb, mount_point, instance_system, net_area_id, segment_data,
                          vm_env, user_id, cluster_id):
    uuid = randomUUID()
    request_id = ins_s.generate_req_id()

    # 判断虚拟机root密码是否为None，是则随机生成root密码，否则使用用户输入的密码
    if not password:
        # 对密码进行加密
        password = encrypt_helper.encrypt(str(string_random_helper.get_password_strings(10)))
    else:
        password = encrypt_helper.encrypt(str(password))

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
        # 'password': None,
        'p_cluster_id': cluster_id,
        'request_id': request_id,
        'task_id': task_id,
        'password': password
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
        'type': InstanceNicType.MAIN_NETWORK_NIC,
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


def _check_instance_name_resource(vm_env, dc_name, instance_system, count):
    '''
        判断虚机名资源是否足够
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
        new_name = prex_str + _generate_4_num(value)
        instance_name_list.append(new_name)
        value += 1

    increment_service.increase_increment_value(prex_str, int(count))
    return True, instance_name_list


def _user_group_check(env, sys_code, sys_opr_name, sys_opr_id, cluster_id):
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
    group = group_s.get_group_info_by_name_and_env(sys_code, env)
    if not group:
        group_data = {
            'name': sys_code,
            'displayname': sys_code,
            'isdeleted': '0',
            'dc_type': env,
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
