# -*- coding:utf-8 -*-
# __author__ =  ""

import os
import time
import threading
import env
import logging
import requests
import json

env.init_env()

from helper.log_helper import add_timed_rotating_file_handler
from service.s_request_record import request_record as request_r_s
from service.s_instance_action import instance_action as instance_a_s
from service.s_instance import instance_service as instance_s
from service.s_ip import ip_lock_service as ip_l_s
from collect_data.base import check_collect_time_out_interval
from helper.time_helper import get_datetime_str
from helper.encrypt_helper import decrypt
from config.default import REQUEST_STATUS_COLLECT_INTERVAL, REQUEST_STATUS_COLLECT_NUMS, \
    REQUEST_STATUS_COLLECT_WORK_INTERVAL, MSG_TO_VS_URL, MSG_TO_SFSLB_URL, MSG_TO_SFSLB_LOGIN_URL, SLB_AUTH_USER, \
    SLB_AUTH_PASSWD, VMStatus, MSG_TO_FWAF_URL
from model.const_define import ErrorCode, VsJobStatus, ApiOrigin, IpLockStatus


# 日志格式化
def _init_log(service_name):
    log_basic_path = os.path.dirname(os.path.abspath(__file__))[0:-28]
    log_name = log_basic_path + 'log/' + str(service_name) + '.log'
    add_timed_rotating_file_handler(log_name, logLevel='ERROR')


# 回调维石接口
def msg_to_vishnu(task_idapi, job_status, detail,request_ip):
    msg = {'jobStepNodeId': task_idapi, 'status': job_status, 'detail': detail}
    data = json.dumps(msg)
    headers = {"Content-Type": "application/json;charset=UTF-8"}

    url = MSG_TO_VS_URL.format(request_ip)

    try:
        # requests模块本身有超时机制，无需自己去编写
        r = requests.post(url, data=data, headers=headers)
        # 设置超时规则，每1s去获取返回结果，结果为空或者查询未超过3s，继续等待1
        timeout = 5
        poll_seconds = 1
        deadline = time.time() + timeout
        while time.time() < deadline and not r.status_code:
            time.sleep(poll_seconds)
        if not r.status_code:
            return str(ErrorCode.SYS_ERR)
        # logging.info("requests to /vishnu-web/restservices/jobcallback data:{},status_code:{}".format(data,r.status_code))
        return str(r.status_code)
    except Exception as err:
        logging.error('post to vs error because:%s' % err)
        return str(ErrorCode.SYS_ERR)


# 回调维石接口
def msg_to_fwaf(task_idapi, job_status, detail,request_ip):
    msg = {'jobStepNodeId': task_idapi, 'status': job_status, 'detail': detail, 'key': '7669657773'}
    data = json.dumps(msg)
    headers = {"Content-Type": "application/json;charset=UTF-8"}

    url = MSG_TO_FWAF_URL.format(request_ip)

    try:
        # requests模块本身有超时机制，无需自己去编写
        r = requests.post(url, data=data, headers=headers, verify=False)
        # 设置超时规则，每1s去获取返回结果，结果为空或者查询未超过3s，继续等待1
        timeout = 5
        poll_seconds = 1
        deadline = time.time() + timeout
        while time.time() < deadline and not r.status_code:
            time.sleep(poll_seconds)
        if not r.status_code:
            return str(ErrorCode.SYS_ERR)
        # logging.info("requests to /api/v1/kvm data:{},status_code:{}".format(data, r.status_code))
        return str(r.status_code)
    except Exception as err:
        logging.error('post to fwaf error because:%s' % err)
        return str(ErrorCode.SYS_ERR)


# 回调软负载接口
def msg_to_sfslb(task_idapi, job_status, detail,request_ip):
    msg = {'jobStepNodeId': task_idapi, 'status': job_status, 'detail': detail}
    data = json.dumps(msg)
    headers = {"Content-Type": "application/json;charset=UTF-8"}
    # 软负载不需要了，所有未更改
    url = MSG_TO_SFSLB_URL

    try:
        r = requests.post(url, data=data, headers=headers, verify=False)
        # 设置超时规则，每1s去获取返回结果，结果为空或者查询未超过3s，继续等待1
        timeout = 5
        poll_seconds = 1
        deadline = time.time() + timeout
        while time.time() < deadline and not r.status_code:
            time.sleep(poll_seconds)

        if not r.status_code:
            return str(ErrorCode.SYS_ERR)

        # logging.info("requests to /slb_instance/jobcallback data:{},status_code:{}".format(data, r.status_code))
        if r.status_code == 401:
            auth_msg = {'userId': SLB_AUTH_USER, 'passWord': decrypt(SLB_AUTH_PASSWD), 'opruserRole': 4}
            try:
                r_auth = requests.post(MSG_TO_SFSLB_LOGIN_URL, params=auth_msg, headers=headers)
                # 设置超时规则，每1s去获取返回结果，结果为空或者查询未超过3s，继续等待1
                timeout = 5
                poll_seconds = 1
                deadline = time.time() + timeout
                while time.time() < deadline and not r_auth.status_code:
                    time.sleep(poll_seconds)
                if not r_auth.status_code:
                    return str(ErrorCode.SYS_ERR)

                # 认证成功后再次请求sfslb接口推送虚拟机创建信息
                try:
                    r = requests.post(url, data=data, headers=headers, cookies=r_auth.cookies)
                    # 设置超时规则，每1s去获取返回结果，结果为空或者查询未超过3s，继续等待1
                    timeout = 5
                    poll_seconds = 1
                    deadline = time.time() + timeout
                    while time.time() < deadline and not r.status_code:
                        time.sleep(poll_seconds)
                    if not r.status_code:
                        return str(ErrorCode.SYS_ERR)
                    return str(r.status_code)

                except Exception as err:
                    logging.error('post to sfslb again error because:%s' % err)
                    return str(ErrorCode.SYS_ERR)

            except Exception as err:
                logging.error('post to vs error because:%s' % err)
                return str(ErrorCode.SYS_ERR)

        return str(r.status_code)
    except Exception as err:
        logging.error('post to sfslb error because:%s' % err)
        return str(ErrorCode.SYS_ERR)


# 多线程收集工单状态并返回外部接口执行结果(原接口，若更改的接口可用，则删除)
def get_collect_request_multithreading(task_idapi, task_idkvm, vm_count, request_opr_user, request_api_origin):
    # 判断此工单是否有线程在追踪
    try:
        params = {
            'WHERE_AND': {
                '=': {
                    'taskid_kvm': task_idkvm,
                    'taskid_api': task_idapi,
                    'istraceing': '1'
                },
            }
        }
        ret_traceing_nums, ret_traceing_data = request_r_s.RequestRecordService().request_db_query_data(**params)
        if ret_traceing_nums > 0:
            return

        # 标记工单为跟踪中
        _update_data = {
            'istraceing': '1',
        }
        _where_data = {
            'taskid_kvm': task_idkvm,
        }
        ret = request_r_s.RequestRecordService().update_request_status(_update_data, _where_data)
        if ret <= 0:
            logging.error('update request %s status to db failed' % task_idkvm)

        ret_request_re = request_r_s.RequestRecordService().get_request_record_info_by_taskid_kvm(task_idkvm)
        request_ip = ret_request_re["request_ip"]

        succeed_http_code = ['200', '500']
        instance_actions_succeed_params = {
            'WHERE_AND': {
                '=': {
                    'task_id': task_idkvm,
                    'action': 'instance_inject_data',
                    'status': 1
                },
            },
        }
        # instance_actions_failed_params = {
        #     'WHERE_AND': {
        #         '=': {
        #             'task_id': task_idkvm,
        #             'status': 2
        #         },
        #         '!=': {
        #             'action': 'image_sync_status'
        #         },
        #     },
        # }
        instance_timeout_failed_params = {
            'WHERE_AND': {
                '=': {
                    'task_id': task_idkvm,
                    'status': VMStatus.CREATE_ERROR
                },
            },
        }
        vm_succeed_count_db_ret, vm_succeed_data = instance_a_s.InstanceActionsServices().query_data(
            **instance_actions_succeed_params)
        # vm_failed_count_db_ret, vm_failed_data =
        # instance_a_s.InstanceActionsServices().query_data(**instance_actions_failed_params)
        vm_createtimeout_count_db_ret, vm_createtimeout_failed_data = instance_s.InstanceService().query_data(
            **instance_timeout_failed_params)
        if not vm_succeed_count_db_ret:
            vm_succeed_count_db_ret = 0

        if not vm_createtimeout_count_db_ret:
            vm_createtimeout_count_db_ret = 0

        instances_uuid = []
        if vm_succeed_count_db_ret > 0:
            for per_request_data in vm_succeed_data:
                instances_uuid.append(per_request_data['instance_uuid'])

            if vm_count == vm_succeed_count_db_ret:
                # 通过虚拟机uuid查询主机名、ip、物理机序列号
                vm_datas = []
                for instance_uuid in instances_uuid:
                    ret_ins = instance_s.InstanceService().get_instance_info_by_uuid(instance_uuid)
                    if ret_ins:
                        ret_ins_host = instance_s.get_host_of_instance(ret_ins['id'])
                        ret_ins_ip = instance_s.get_net_segment_info_of_instance(ret_ins['id'])
                        if ret_ins_host and ret_ins_ip:
                            vm_data = {
                                'instance_ids': ret_ins['id'],
                                'host_name': ret_ins['name'],
                                'ip': ret_ins_ip['ip_address'],
                                'ip_type': ret_ins_ip['segment_type'],
                                'sn': ret_ins_host['sn'],
                                'UUID': instance_uuid,
                                'net_name': ret_ins_ip['segment'],
                                'subnet_mask': ret_ins_ip['netmask'],
                                'gateway': ret_ins_ip['gateway_ip'],
                                'vlan_id': ret_ins_ip['vlan'],
                                'passWord': decrypt(ret_ins['password'])
                            }
                            vm_datas.append(vm_data)

                msg_detail = {'opUser': request_opr_user, 'vm': vm_datas}
                # 回调外部接口
                response_to_api_status = '1'
                if request_api_origin == ApiOrigin.VISHNU:
                    ret_code = msg_to_vishnu(task_idapi, VsJobStatus.SUCCEED, msg_detail,request_ip)
                elif request_api_origin == ApiOrigin.SFSLB:
                    ret_code = msg_to_sfslb(task_idapi, VsJobStatus.SUCCEED, msg_detail,request_ip)
                elif request_api_origin == ApiOrigin.FWAF:
                    ret_code = msg_to_fwaf(task_idapi, VsJobStatus.SUCCEED, msg_detail,request_ip)
                else:
                    ret_code = msg_to_vishnu(task_idapi, VsJobStatus.SUCCEED, msg_detail,request_ip)
                if ret_code not in succeed_http_code:
                    response_to_api_status = '0'
                update_db_time = get_datetime_str()
                _update_data = {
                    'task_status': '1',
                    'response_to_api': response_to_api_status,
                    'finish_time': update_db_time,
                    'request_status_collect_time': update_db_time,
                }
                _where_data = {
                    'taskid_kvm': task_idkvm,
                }
                ret = request_r_s.RequestRecordService().update_request_status(_update_data, _where_data)
                if ret <= 0:
                    logging.error('update request %s status to db failed' % task_idkvm)
            elif (vm_createtimeout_count_db_ret + vm_succeed_count_db_ret) == vm_count \
                    and vm_createtimeout_count_db_ret > vm_count * 0.2:
                # 回调外部接口
                response_to_api_status = '1'

                if request_api_origin == ApiOrigin.VISHNU:
                    ret_code = msg_to_vishnu(task_idapi, VsJobStatus.FAILED, 'all kvm instance create failed',request_ip)
                elif request_api_origin == ApiOrigin.SFSLB:
                    ret_code = msg_to_sfslb(task_idapi, VsJobStatus.FAILED, 'all kvm instance create failed',request_ip)
                elif request_api_origin == ApiOrigin.FWAF:
                    ret_code = msg_to_fwaf(task_idapi, VsJobStatus.FAILED, 'all kvm instance create failed',request_ip)
                else:
                    ret_code = msg_to_vishnu(task_idapi, VsJobStatus.FAILED, 'all kvm instance create failed',request_ip)

                if ret_code not in succeed_http_code:
                    response_to_api_status = '0'
                update_db_time = get_datetime_str()
                _update_data = {
                    'task_status': '2',
                    'response_to_api': response_to_api_status,
                    'finish_time': update_db_time,
                    'request_status_collect_time': update_db_time,
                }
                _where_data = {
                    'taskid_kvm': task_idkvm,
                }
                ret = request_r_s.RequestRecordService().update_request_status(_update_data, _where_data)
                if ret <= 0:
                    logging.error('update request %s status to db failed' % task_idkvm)
            else:
                if (vm_createtimeout_count_db_ret + vm_succeed_count_db_ret) == vm_count:
                    # 把成功创建的虚拟机返回外部接口
                    """
                    vm_datas = []
                    for instance_uuid in instances_uuid:
                        ret_ins = instance_s.InstanceService().get_instance_info_by_uuid(instance_uuid)
                        if ret_ins:
                            ret_ins_host = instance_s.get_host_of_instance(ret_ins['id'])
                            ret_ins_ip = instance_s.get_net_segment_info_of_instance(ret_ins['id'])
                            if ret_ins_host and ret_ins_ip:
                                vm_data = {
                                    'host_name': ret_ins['name'],
                                    'ip': ret_ins_ip['ip_address'],
                                    'sn': ret_ins_host['sn'],
                                    'UUID': instance_uuid,
                                    'net_name': ret_ins_ip['segment'],
                                    'subnet_mask': ret_ins_ip['netmask'],
                                    'gateway': ret_ins_ip['gateway_ip'],
                                    'vlan_id': ret_ins_ip['vlan']
                                }
                                vm_datas.append(vm_data)

                    msg_detail = {'opUser': request_opr_user, 'vm': vm_datas}
                    """
                    # 回调外部接口
                    response_to_api_status = '1'
                    if request_api_origin == ApiOrigin.VISHNU:
                        ret_code = msg_to_vishnu(task_idapi, VsJobStatus.FAILED, 'part of kvm instance create failed',request_ip)
                    elif request_api_origin == ApiOrigin.SFSLB:
                        ret_code = msg_to_sfslb(task_idapi, VsJobStatus.FAILED, 'part of kvm instance create failed',request_ip)
                    elif request_api_origin == ApiOrigin.FWAF:
                        ret_code = msg_to_fwaf(task_idapi, VsJobStatus.FAILED, 'part of kvm instance create failed',request_ip)
                    else:
                        ret_code = msg_to_vishnu(task_idapi, VsJobStatus.FAILED, 'part of kvm instance create failed',request_ip)

                    if ret_code not in succeed_http_code:
                        response_to_api_status = '0'

                    update_db_time = get_datetime_str()
                    _update_data = {
                        'task_status': '2',
                        'response_to_api': response_to_api_status,
                        'finish_time': update_db_time,
                        'request_status_collect_time': update_db_time,
                    }
                    _where_data = {
                        'taskid_kvm': task_idkvm,
                    }
                    ret = request_r_s.RequestRecordService().update_request_status(_update_data, _where_data)
                    if ret <= 0:
                        logging.error('update request %s status to db failed' % task_idkvm)
                else:
                    # 成功失败的总数量未等于count
                    pass

        elif vm_createtimeout_count_db_ret > 0:
            # 全部虚拟机创建失败
            if (vm_createtimeout_count_db_ret + vm_succeed_count_db_ret) == vm_count \
                    and vm_createtimeout_count_db_ret > vm_count * 0.2:
                # 回调外部接口
                response_to_api_status = '1'
                if request_api_origin == ApiOrigin.VISHNU:
                    ret_code = msg_to_vishnu(task_idapi, VsJobStatus.FAILED, 'all kvm instance create failed',request_ip)
                elif request_api_origin == ApiOrigin.SFSLB:
                    ret_code = msg_to_sfslb(task_idapi, VsJobStatus.FAILED, 'all kvm instance create failed',request_ip)
                elif request_api_origin == ApiOrigin.FWAF:
                    ret_code = msg_to_fwaf(task_idapi, VsJobStatus.FAILED, 'all kvm instance create failed',request_ip)
                else:
                    ret_code = msg_to_vishnu(task_idapi, VsJobStatus.FAILED, 'all kvm instance create failed',request_ip)

                if ret_code not in succeed_http_code:
                    response_to_api_status = '0'
                update_db_time = get_datetime_str()
                _update_data = {
                    'task_status': '2',
                    'response_to_api': response_to_api_status,
                    'finish_time': update_db_time,
                    'request_status_collect_time': update_db_time,
                }
                _where_data = {
                    'taskid_kvm': task_idkvm,
                }
                ret = request_r_s.RequestRecordService().update_request_status(_update_data, _where_data)
                if ret <= 0:
                    logging.error('update request %s status to db failed' % task_idkvm)
        else:
            update_db_time = get_datetime_str()
            _update_data = {
                'request_status_collect_time': update_db_time
            }
            _where_data = {
                'taskid_kvm': task_idkvm,
            }
            ret = request_r_s.RequestRecordService().update_request_status(_update_data, _where_data)
            if ret <= 0:
                logging.error('update request %s status to db failed' % task_idkvm)

        # 标记工单为完成追踪
        _update_data = {
            'istraceing': '0',
        }
        _where_data = {
            'taskid_kvm': task_idkvm,
        }
        ret = request_r_s.RequestRecordService().update_request_status(_update_data, _where_data)
        if ret <= 0:
            logging.error('update request %s status to db failed when mark istraceing 1' % task_idkvm)

        return
    except Exception  as e:
        logging.error('request {} threading exception error: {}'.format(task_idkvm,e))
        return


# 获取满足条件request列表
def get_collect_request(interval=120, nums=20):
    '''
        获取前20个上次收集时间最久远并且超过了时间间隔的host
    :param interval:
    :param nums:
    :return:
    '''
    params = {
        'WHERE_AND': {
            '=': {
                'response_to_api': '0',
                'istraceing': '0'
            },
        },
        'ORDER': [
            ['request_status_collect_time', 'asc']
        ],
    }
    requests_list = []
    requests_nums, requests_data = request_r_s.RequestRecordService().request_db_query_data(**params)
    if requests_nums > 0:
        for _request in requests_data:
            if check_collect_time_out_interval(_request['request_status_collect_time'], interval) and len(
                    requests_list) <= nums:
                requests_list.append(_request)

    return requests_list


def __update_table_lock_unused():
    '''
        更新ip_lock表istraceing字段为0
    :return:
    '''

    update_ip_lock_data = {
        'istraceing': IpLockStatus.UNUSED
    }
    where_ip_lock_data = {
        'table_name': 'request_record'
    }
    ret_update_ip_lock = ip_l_s.IpLockService().update_ip_lock_info(update_ip_lock_data, where_ip_lock_data)
    if not ret_update_ip_lock:
        return False, '工单追踪：无法更新数据库表request_record资源锁状态为未使用中'
    return True, '工单追踪：更新数据库表request_record资源锁状态为未使用中成功'


def __update_table_lock_used():
    '''
        更新ip_lock表istraceing字段为1
    :return:
    '''

    update_ip_lock_data = {
        'istraceing': IpLockStatus.USED
    }
    where_ip_lock_data = {
        'table_name': 'request_record'
    }
    ret_update_ip_lock = ip_l_s.IpLockService().update_ip_lock_info(update_ip_lock_data, where_ip_lock_data)
    if not ret_update_ip_lock:
        return False, '工单追踪：无法更新数据库表request_record资源锁状态为使用中'
    return True, '工单追踪：更新数据库表request_record资源锁状态为使用中成功'


if __name__ == '__main__':
    _init_log('trace_and_update_request_status')
    while True:
        threads = []

        # 获取工单信息，先判断是否有人也在操作工单表格，有则等待1s，时间之后再优化
        request_lock_unused = False
        while not request_lock_unused:
            ret_request_lock_status = ip_l_s.IpLockService().get_ip_lock_info('request_record')
            if not ret_request_lock_status:
                logging.error('工单追踪：无法获取资源锁状态')
                time.sleep(2)
                continue

            if ret_request_lock_status['istraceing'] == IpLockStatus.USED:
                time.sleep(1)
            else:
                request_lock_unused = True

        # 更新ip_lock表istraceing字段为1
        ret_request_lock_used_status, ret_request_lock_used_datas = __update_table_lock_used()
        if not ret_request_lock_used_status:
            logging.error(ret_request_lock_used_datas)
            continue

        requests_data = get_collect_request(interval=REQUEST_STATUS_COLLECT_INTERVAL,
                                            nums=REQUEST_STATUS_COLLECT_NUMS)
        logging.info(requests_data)
        if not requests_data:
            print 'no collect requests now, please wait'
            # 更新ip_lock表istraceing字段为0
            ret_request_lock_unused_status, ret_request_lock_unused_datas = __update_table_lock_unused()
            if not ret_request_lock_unused_status:
                logging.error(ret_request_lock_unused_datas)
            # 任务休息
            time.sleep(REQUEST_STATUS_COLLECT_WORK_INTERVAL)
        else:
            for _request in requests_data:
                request_taskidapi = _request['taskid_api']
                request_taskidkvm = _request['taskid_kvm']
                request_vm_count = _request['vm_count']
                request_opr_user = _request['user_id']
                request_api_origin = _request['api_origin']
                request_thread = threading.Thread(target=get_collect_request_multithreading,
                                                  args=(request_taskidapi, request_taskidkvm, request_vm_count,
                                                        request_opr_user, request_api_origin,))
                threads.append(request_thread)
                request_thread.start()

            # 判断多线程是否结束
            for t in threads:
                t.join()

            # 更新ip_lock表istraceing字段为0
            ret_request_lock_unused_status, ret_request_lock_unused_datas = __update_table_lock_unused()
            if not ret_request_lock_unused_status:
                logging.error(ret_request_lock_unused_datas)

            # 任务休息
            time.sleep(REQUEST_STATUS_COLLECT_WORK_INTERVAL)
