# -*- coding:utf-8 -*-


'''
    IP管理-申请ip
'''


from flask import request
from service.s_ip import segment_service
from service.s_net_area import net_area
from service.s_datacenter import datacenter_service
from service.s_ip import ip_service, vip_service
from service.s_group import group_service as group_s
from model.const_define import IPStatus, ErrorCode, DataCenterTypeForVishnu, DataCenterType
from model.const_define import IPStatus, ErrorCode, DataCenterTypeForVishnu, OperationObject, OperationAction, \
    IpLockStatus
import json_helper
from helper.time_helper import get_datetime_str
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
from service.s_operation.operation_service import add_operation_ip
from service.s_ip import ip_lock_service as ip_l_s
import logging
import time


@login_required
@add_operation_ip(OperationObject.IP, OperationAction.IP_APPLY)
def ip_apply():
    '''
        IP申请
    :return:
    '''
    req_env = request.values.get('env')
    req_net_area = request.values.get('net_area')
    req_net_name = request.values.get('segment')
    cluster_id = request.values.get('cluster_id')
    opuser = request.values.get('opUser')
    sys_code = request.values.get('sys_code')

    # 校验入参是否为空
    if not req_env or not req_net_area or not req_net_name:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="环境、网络区域、网段名输入为空")
    if not cluster_id or not opuser or not sys_code:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="物理集群、操作用户、系统编码为空输入为空")

    # 查询指定环境、网络区域是否有所需网段
    ret_segment = segment_service.SegmentService().get_segment_info_bysegment(req_net_name)
    if not ret_segment:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="无法找到需要申请的网段")

    ret_net_area_info = net_area.NetAreaService().get_net_area_info(ret_segment['net_area_id'])
    if not ret_net_area_info:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="无法找到指定网络区域信息")
    ret_datacenter_info = datacenter_service.DataCenterService().get_datacenter_info(ret_net_area_info['datacenter_id'])
    if not ret_datacenter_info:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="无法找到指定机房信息")
    if req_env not in DataCenterTypeForVishnu.TYPE_DICT:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="无法找到指定机房类型信息")
    if str(DataCenterTypeForVishnu.TYPE_DICT[req_env]) != ret_datacenter_info['dc_type']:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="无法找到指定网络区域对应网段信息")

    # 获取IP资源，先判断是否有人也在分配IP资源，有则等待1s，时间之后再优化
    ip_lock_unused = False
    while not ip_lock_unused:
        ret_ip_lock_status = ip_l_s.IpLockService().get_ip_lock_info('ip')
        if not ret_ip_lock_status:
            logging.error('kvm平台分配vip：检查IP时无法获取资源锁状态')
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
    # 获取可用ip
    try:
        ret_ip_available_status, ret_ip_available = ip_service.get_available_segment_ip(ret_segment['id'], str(
            DataCenterTypeForVishnu.TYPE_DICT[req_env]))
    except Exception as e:
        _msg = 'IP申请ip_apply：获取指定网段可用ip出现异常 : get segment available ip exception when ip apply，err：%s' %e
        logging.error(_msg)
        ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
        if not ret_ip_lock_unused_status:
            logging.error(ret_ip_lock_unused_datas)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=_msg)

    if not ret_ip_available_status:
        ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
        if not ret_ip_lock_unused_status:
            logging.error(ret_ip_lock_unused_datas)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="指定网段没有可用ip")

    # 标记ip已使用
    update_data = {
        'status': IPStatus.USED
    }
    where_data = {
        'id': ret_ip_available['id']
    }
    ret_mark_ip = ip_service.IPService().update_ip_info(update_data, where_data)
    if ret_mark_ip <= 0:
        ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
        if not ret_ip_lock_unused_status:
            logging.error(ret_ip_lock_unused_datas)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="标记ip为已使用状态失败，请重新申请")

    # 更新ip_lock表istraceing字段为0
    ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
    if not ret_ip_lock_unused_status:
        logging.error(ret_ip_lock_unused_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)

    # 录入vip信息到数据库中
    insert_vip_data = {
        'ip_id': ret_ip_available['id'],
        'cluster_id': cluster_id,
        'apply_user_id': opuser,
        'sys_code': sys_code,
        'isdeleted': '0',
        'created_at': get_datetime_str()
    }
    ret_vip = vip_service.VIPService().add_vip_info(insert_vip_data)
    if ret_vip.get('row_num') <= 0:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="录入ip信息失败，请联系系统管理员")

    ip_msg = {
        "vip": ret_ip_available['ip_address']
    }

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=ip_msg)


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
        return False, 'kvm平台分配VIP：检查IP时无法更新资源锁状态为未使用中'
    return True, 'kvm平台分配VIP：检查IP时更新资源锁状态为未使用中成功'


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
        return False, 'kvm平台分配VIP：检查IP时无法更新资源锁状态为使用中'
    return True, 'kvm平台分配VIP：检查IP时更新资源锁状态为使用中成功'
