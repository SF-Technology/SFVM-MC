# coding=utf8
'''
    虚拟机操作
'''


from service.s_instance import instance_service as ins_s, instance_action_service as ins_a_s
from controller.web_api.e_instance.instance_create import check_group_quota
import logging
import json_helper
from model.const_define import ErrorCode, VMStatus, OperationObject, OperationAction
from flask import request
from config.default import INSTANCE_MAX_SHUTDOWN, INSTANCE_MAX_STARTUP
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
from service.s_operation.operation_service import add_operation_vm


@login_required
@add_operation_vm(OperationObject.VM, OperationAction.SHUTDOWN)
def instance_shutdown():
    '''
        虚机关机/强制关机
    :return:
    '''
    ins_ids = request.values.get('instance_ids')
    # 区分关机和强制关机
    flag = request.values.get('flag')
    if not ins_ids or not flag:
        logging.info('no instance_ids or flag when shutdown instance')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    ins_ids_list = ins_ids.split(',')
    # 操作的instance数
    all_num = len(ins_ids_list)
    if all_num > int(INSTANCE_MAX_SHUTDOWN):
        logging.info('shutdown nums %s is greater than max %s', all_num, INSTANCE_MAX_SHUTDOWN)
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    msg = None
    fail_num = 0
    for _ins_id in ins_ids_list:
        _ins_data = ins_s.InstanceService().get_instance_info(_ins_id)
        if _ins_data:
            # 本身是关机状态的不能再关机
            # if _ins_data['status'] == VMStatus.SHUTDOWN or _ins_data['status'] == VMStatus.SHUTDOWN_ING:
            #     logging.info('the instance status %s is invalid when shutdown instance', _ins_data['status'])
            #     fail_num += 1
            #     # 单台操作且已失败则直接跳出循环
            #     if all_num == 1:
            #         msg = '该虚拟机已经关机，请勿重复关机'
            #         break
            #     continue
            # else:
            #     _ret_shut, _ret_msg = ins_a_s.shutdown_instance(_ins_data, int(flag))
            #     if not _ret_shut:
            #         fail_num += 1
            #         # 单台操作且已失败则直接跳出循环
            #         if all_num == 1:
            #             msg = _ret_msg
            #             break
            #         continue

            if _ins_data['status'] == VMStatus.SHUTDOWN:
                logging.info('the instance status %s is invalid when shutdown instance', _ins_data['status'])
                fail_num += 1
                # 单台操作且已失败则直接跳出循环
                if all_num == 1:
                    msg = '该虚拟机已经关机，请勿重复关机'
                    break
                continue
            elif _ins_data['status'] == VMStatus.SHUTDOWN_ING and int(flag) == 1:
                logging.info('the instance status %s is invalid when shutdown instance', _ins_data['status'])
                fail_num += 1
                # 单台操作且已失败则直接跳出循环
                if all_num == 1:
                    msg = '该虚拟机正在关机中，请勿重复关机'
                    break
                continue
            else:
                _ret_shut, _ret_msg = ins_a_s.shutdown_instance(_ins_data, int(flag))
                if not _ret_shut:
                    fail_num += 1
                    # 单台操作且已失败则直接跳出循环
                    if all_num == 1:
                        msg = _ret_msg
                        break
                    continue
        else:
            logging.info('the instance is not exist in db when shutdown instance')
            fail_num += 1
            continue

    # 全失败
    if fail_num == all_num:
        logging.error("shutdown instance all failed")
        if msg:
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=msg)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    # 部分成功
    if 0 < fail_num < all_num:
        logging.error("shutdown instance part failed")
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS_PART, msg="部分虚拟机关机成功")
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


@login_required
@add_operation_vm(OperationObject.VM, OperationAction.STARTUP)
def instance_startup():
    '''
        虚机开机
    :return:
    '''
    ins_ids = request.values.get('instance_ids')
    if not ins_ids:
        logging.info('no instance_ids when startup instance')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    ins_ids_list = ins_ids.split(',')
    # 操作的instance数
    all_num = len(ins_ids_list)
    if all_num > int(INSTANCE_MAX_STARTUP):
        logging.info('startup nums %s is greater than max %s', all_num, INSTANCE_MAX_STARTUP)
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    msg = None
    fail_num = 0
    for _ins_id in ins_ids_list:
        _ins_data = ins_s.InstanceService().get_instance_info(_ins_id)
        if _ins_data:
            # 本身是开机状态的不能再开机
            if _ins_data['status'] == VMStatus.STARTUP or _ins_data['status'] == VMStatus.STARTUP_ING:
                logging.info('the instance status %s is invalid when startup instance', _ins_data['status'])
                fail_num += 1
                # 单台操作且已失败则直接跳出循环
                if all_num == 1:
                    msg = '该虚拟机已经开机，请勿重复开机'
                    break
                continue
            else:
                _ret_start = ins_a_s.startup_instance(_ins_data)
                if not _ret_start:
                    fail_num += 1
                    continue
        else:
            logging.info('the instance is not exist in db when startup instance')
            fail_num += 1
            continue

    # 全失败
    if fail_num == all_num:
        logging.error("startup instance all failed")
        if msg:
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=msg)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    # 部分成功
    if 0 < fail_num < all_num:
        logging.error("startup instance part failed")
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS_PART, msg="部分虚拟机开机成功")
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


@login_required
def instance_reboot():
    '''
        虚机重启/强制重启
    :return:
    '''
    ins_ids = request.values.get('instance_ids')
    # 区分重启和强制重启
    flag = request.values.get('flag')
    if not ins_ids or not flag:
        logging.error('no instance_ids or flag when reboot instance')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    ins_ids_list = ins_ids.split(',')
    # 操作的instance数
    all_num = len(ins_ids_list)
    fail_num = 0
    for _ins_id in ins_ids_list:
        _ins_data = ins_s.InstanceService().get_instance_info(_ins_id)
        if _ins_data:
            _ret_start = ins_a_s.reboot_instance(_ins_data)
            if not _ret_start:
                fail_num += 1
                continue
        else:
            logging.info('the instance is not exist in db when reboot instance')
            fail_num += 1
            continue

    # 全失败
    if fail_num == all_num:
        logging.error("reboot instance all failed")
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    # 部分成功
    if 0 < fail_num < all_num:
        logging.error("reboot instance part failed")
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS_PART, msg="部分虚拟机重启成功")
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


@login_required
def instance_clone(instance_id):
    '''
        虚机克隆
    :param instance_id:
    :return:
    '''
    instance_newname = request.values.get('instance_newname')
    if not instance_id:
        logging.info('no instance_id when clone instance')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    ins_data = ins_s.InstanceService().get_instance_info(instance_id)
    if not ins_data:
        logging.error('instance %s data is no exist in db when clone instance', instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    ins_status = ins_data['status']
    if ins_status != VMStatus.SHUTDOWN:
        logging.error('instance %s status %s is invalid when clone instance', instance_id, ins_status)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='只能在关机状态下克隆虚机')

    ins_group = ins_s.get_group_of_instance(instance_id)
    if not ins_group:
        logging.error('instance %s group data is no exist in db when clone instance', instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    ins_flavor = ins_s.get_flavor_of_instance(instance_id)
    if not ins_flavor:
        logging.error('instance %s flavor data is no exist in db when clone instance', instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    # 检查应用组配额
    ins_group_id = ins_group['group_id']
    is_quota_enough, quota_msg = check_group_quota(ins_group_id, ins_flavor, 1)
    if not is_quota_enough:
        logging.error('group %s is no enough quota when clone instance', ins_group_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=quota_msg)

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)
