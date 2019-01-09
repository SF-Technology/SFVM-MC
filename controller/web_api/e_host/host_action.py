# coding=utf8
'''
    物理机操作
'''
# __author__ =  ""

from service.s_host import host_service
from service.s_instance import instance_service as ins_s
from flask import request
import logging
import json_helper
from model.const_define import ErrorCode, HostTypeStatus, HostStatus, HostOperate, VMStatus, OperationObject, OperationAction
import threading
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
from service.s_operation.operation_service import add_operation_host
from config import default
from model.const_define import EnvType


@login_required
@add_operation_host(OperationObject.HOST, OperationAction.LOCK)
def lock(host_id):
    '''
        锁定物理机，即虚机不分配到该物理机上
    :param host_id:
    :return:
    '''
    # flag:'1' 锁定  flag:'0' 解除锁定
    flag = request.values.get("flag")
    if not host_id or not flag:
        logging.info('no host_id or flag when lock/unlock host')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="参数错误")

    host_data = host_service.HostService().get_host_info(host_id)
    if not (host_data and host_data['isdeleted'] == '0'):
        logging.info('the host %s is invalid when lock/unlock host', host_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    if host_data['typestatus'] == flag:
        logging.info('the host %s is done before when lock/unlock host', host_id)
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS)

    update_data = {
        "typestatus": flag
    }
    where_data = {
        "id": host_id
    }
    ret = host_service.HostService().update_host_info(update_data, where_data)
    if ret != 1:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


@login_required
@add_operation_host(OperationObject.HOST, OperationAction.MAINTAIN)
def maintain(host_id):
    '''
        维护物理机
    :param host_id:
    :return:
    '''

    def _check_all_instance_shutdown(instance_list):
        '''
            检查是否所有VM都是关机状态
        :param instance_list:
        :return:
        '''
        shutdown_flag = True
        for _ins in instance_list:
            if _ins['status'] != VMStatus.SHUTDOWN:
                shutdown_flag = False
                break
        return shutdown_flag

    # flag:'2' 维护  flag:'0' 结束维护
    flag = request.values.get("flag")
    if not host_id or not flag:
        logging.info('no host_id or flag when maintain/unmaintain host')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="参数错误")

    host_data = host_service.HostService().get_host_info(host_id)
    if not (host_data and host_data['isdeleted'] == '0'):
        logging.info('the host %s is invalid when maintain/unmaintain host', host_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    if host_data['typestatus'] == flag:
        logging.info('the host %s is done before when maintain/unmaintain host', host_id)
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS)

    # 需要该host没有vm，或者所有vm都关机时才能维护
    if flag == HostTypeStatus.MAINTAIN:
        vm_list = ins_s.get_instances_in_host(host_data['id'])
        if len(vm_list) > 0 and not _check_all_instance_shutdown(vm_list):
            logging.info('no allow maintain host which has instances that no shutdown when maintain host')
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR,
                                               msg="该HOST下存在着非关机状态的虚拟机，不能维护该HOST")

    update_data = {
        "typestatus": flag
    }
    where_data = {
        "id": host_id
    }
    ret = host_service.HostService().update_host_info(update_data, where_data)
    if ret != 1:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


def operate_host_multithreading(manage_ip, flag, host_id, status, passwd_back):
    global ERR_RET
    global DB_ERR_RET
    global HOST_OPERATE_RETURN_DATA
    threadlock = threading.Lock()
    opr_ret = host_service.operate_host_flag(manage_ip, flag, passwd_back)
    # 返回1: ipmi无法使用，请联系管理员查看
    if opr_ret == 1:
        threadlock.acquire()
        try:
            ERR_RET += 1
            HOST_OPERATE_RETURN_DATA[manage_ip] = "ipmi无法使用，请稍后重试或手动操作"
        finally:
            threadlock.release()
        return 0
    # 返回0: 操作成功
    elif opr_ret == 0:
        # 执行操作成功，更改数据库记录
        undo_db_update = False
        if flag == HostOperate.START:
            HOST_OPERATE_RETURN_DATA[manage_ip] = "开机操作下发成功"
            if status == HostStatus.RUNNING:
                undo_db_update = True
            else:
                status = HostStatus.RUNNING
        elif flag == HostOperate.STOP:
            HOST_OPERATE_RETURN_DATA[manage_ip] = "强制关机操作下发成功"
            if status == HostStatus.STOP:
                undo_db_update = True
            else:
                status = HostStatus.STOP
        elif flag == HostOperate.SOFT_STOP:
            HOST_OPERATE_RETURN_DATA[manage_ip] = "正常关机操作下发成功"
            if status == HostStatus.STOP:
                undo_db_update = True
            else:
                status = HostStatus.STOP
        elif flag == HostOperate.RESET:
            HOST_OPERATE_RETURN_DATA[manage_ip] = "强制重启操作下发成功"
            if status == HostStatus.RUNNING:
                undo_db_update = True
            else:
                status = HostStatus.RUNNING
        elif flag == HostOperate.SOFT_RESET:
            HOST_OPERATE_RETURN_DATA[manage_ip] = "正常重启操作下发成功"
            if status == HostStatus.RUNNING:
                undo_db_update = True
            else:
                status = HostStatus.RUNNING

        if not undo_db_update:
            update_data = {
                "status": status
            }
            where_data = {
                "id": host_id
            }
            db_ret = host_service.HostService().update_host_info(update_data, where_data)
            if db_ret != 1:
                DB_ERR_RET += 1
        threadlock.acquire()
        HOST_OPERATE_RETURN_DATA[manage_ip] = "操作已经下发，请关注物理机状态变化"
        threadlock.release()
        return 0
    # 返回3: 机器状态已经为操作预期状态
    elif opr_ret == 3:
        # 重复操作不执行返回错误
        threadlock.acquire()
        ERR_RET += 1
        HOST_OPERATE_RETURN_DATA[manage_ip] = "物理机状态已经为操作预期状态，请执行其他操作"
        threadlock.release()
        return 0
    # 返回2: ipmi操作超时，请重新下发指令；
    else:
        threadlock.acquire()
        ERR_RET += 1
        HOST_OPERATE_RETURN_DATA[manage_ip] = "ipmi无法使用，请稍后重试或手动操作"
        threadlock.release()
        return 0


@login_required
@add_operation_host(OperationObject.HOST, OperationAction.OPERATE)
def operate_host():
    global ERR_RET
    global DB_ERR_RET
    global HOST_OPERATE_RETURN_DATA
    ERR_RET = 0
    DB_ERR_RET = 0
    HOST_OPERATE_RETURN_DATA = {}
    threads = []
    threadlock = threading.Lock()
    all_host_id = request.values.get("host_id")
    flag = request.values.get("flag")
    if not all_host_id or not flag:
        logging.info('no host_id or flag when operate host')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="前端输入参数错误")
    elif all_host_id == '' or flag == '':
        logging.info('empty input host_id or flag when operate host')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="前端输入参数为空")

    for host_id in all_host_id.split(','):
        host_data = host_service.HostService().get_host_info(host_id)
        if not host_data:
            threadlock.acquire()
            ERR_RET += 1
            threadlock.release()
            logging.info('host %s info is error in db when operate host', host_id)
            continue

        # 生产机房生产环境物理机密码后半部分取自配置文件
        if default.ENV == EnvType.PRO_2:
            from config.default import HOST_PASSWD_BACK
            passwd_back = HOST_PASSWD_BACK
        else:
            passwd_back = host_data['sn'][-4:]

        host_thread = threading.Thread(target=operate_host_multithreading, args=(host_data['manage_ip'], int(flag), host_id, host_data['status'], passwd_back))
        threads.append(host_thread)
        host_thread.start()

    # 判断多线程是否结束
    for t in threads:
        t.join()

    if len(all_host_id.split(',')) == 1 and ERR_RET == 0:
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS, msg=HOST_OPERATE_RETURN_DATA[host_data['manage_ip']])
    elif ERR_RET == 0:
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS, msg="所有物理机操作成功")
    elif len(all_host_id.split(',')) == 1 and ERR_RET == 1:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=HOST_OPERATE_RETURN_DATA[host_data['manage_ip']])
    elif len(all_host_id.split(',')) == ERR_RET:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="所有物理机操作全部失败")
    else:
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS_PART, msg="所有物理机操作部分成功，请检查物理机状态变化")
