# -*- coding:utf-8 -*-
# __author__ =  ""
import os
import logging
import time
from flask import request
# from flask.ext.httpauth import HTTPBasicAuth
from flask_httpauth import HTTPBasicAuth
from helper.log_helper import add_timed_rotating_file_handler
from helper import json_helper
from helper.time_helper import get_datetime_str
from model.const_define import ErrorCode, VsJobStatus, VMLibvirtStatus, NetCardType, IpLockStatus, DataCenterType, \
    IPStatus, ActionStatus, InstaceActions, InstanceNicType
from config.default import INSTANCE_NETCARD_NUMS
from lib.vrtManager import instanceManager as vmManager
from lib.vrtManager.util import randomMAC
from service.s_user import user_service as user_s
from service.s_ip import ip_service as ip_s, ip_lock_service as ip_l_s, segment_service as segment_s, \
    segment_match as segment_match_s
from service.s_instance import instance_service as instance_s, instance_ip_service as instance_ip_s
from service.s_instance_action import instance_action as instance_action_s
from controller.web_api.ip_filter_decorator import ip_filter_from_other_platform

auth_api_user = HTTPBasicAuth()


# 日志格式化
def _init_log(service_name):
    log_basic_path = os.path.dirname(os.path.abspath(__file__))[0:-29]
    log_name = log_basic_path + 'log/' + str(service_name) + '.log'
    add_timed_rotating_file_handler(log_name, logLevel='INFO')


@ip_filter_from_other_platform
@auth_api_user.login_required
def instance_add_netcard_from_other_platform():
    '''
        kvm平台虚拟机添加网卡外部接口
        入参说明：
            {
                "instanceMainIp": "虚拟机主网ip列表"
                "apiOrigin": "",
                "netCardType": ""
            }
    :return:
    '''
    _init_log('instance_add_netcard_from_other_platform')
    logging.info(request.data)
    logging.info(request.values)
    logging.info(request.form)
    req_json = request.data
    req_data = json_helper.loads(req_json)

    instance_ip_list = req_data["instanceMainIp"]
    req_origin = req_data["apiOrigin"]
    netcard_type = req_data["netCardType"]

    # 判断需要配置网卡所有虚拟机是否存在
    if not instance_ip_list or not req_origin or not netcard_type:
        return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                               detail='入参有空值，请检查')

    _ip_datas_list = []
    instance_data_list = []
    env_list = []
    dc_list = []
    net_area_list = []
    ip_str = ""
    # 判断ip列表中是否有不存在于kvm平台的
    for _ip in instance_ip_list:
        _instance_info = ip_s.get_instance_info_by_ip(_ip['ip'])
        if not _instance_info:
            ip_str += _ip['ip'] + " "
        else:
            _instance_params = {
                "instance_ip": _ip['ip'],
                "instance_uuid": _instance_info['instance_uuid'],
                "instance_id": _instance_info['instance_id'],
                "instance_name": _instance_info['instance_name'],
                "host_ip": _instance_info['host_ip'],
                "env": _instance_info['env'],
                "net_area": _instance_info['net_area_name'],
                "dc_name": _instance_info['datacenter_name'],
            }
            instance_data_list.append(_instance_params)
            env_list.append(_instance_info['env'])
            dc_list.append(_instance_info['datacenter_name'])
            net_area_list.append(_instance_info['net_area_name'])

    if ip_str:
        return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                               detail='ip:%s无法在kvm平台中找到' % ip_str)

    if len(set(env_list)) > 1:
        return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                               detail='需要配置网卡的虚拟机属于不同环境，不允许同时配置')

    if len(set(dc_list)) > 1:
        return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                               detail='需要配置网卡的虚拟机属于不同机房，不允许同时配置')

    if len(set(net_area_list)) > 1:
        return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                               detail='需要配置网卡的虚拟机属于不同网络区域，不允许同时配置')

    instance_str = ""
    instance_data_filter_list = []
    # 查询指定虚拟机网卡数量，目前不能超过3块，同一类型网卡只能有一块
    for _instance in instance_data_list:
        instance_same_netcard_type_str = ""
        instance_net_card = instance_s.get_net_info_of_instance(_instance['instance_id'])
        if instance_net_card:
            for _net_card in instance_net_card:
                if _net_card['segment_type'] == netcard_type:
                    instance_same_netcard_type_str += _instance['instance_ip'] + " "
                    _ip_datas = {
                        "instanceIp": _instance['instance_ip'],
                        "nasIp": _net_card['ip_address']
                    }
                    _ip_datas_list.append(_ip_datas)

            if not instance_same_netcard_type_str:
                instance_data_filter_list.append(_instance)

            if len(instance_net_card) >= INSTANCE_NETCARD_NUMS:
                instance_str += _instance['instance_ip'] + " "

    if instance_str:
        return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                               detail='虚拟机:%s网卡数量不能大于%s' % (ip_str, str(INSTANCE_NETCARD_NUMS)))

    # if instance_same_netcar_type_str:
    #     return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
    #                                            detail='虚拟机:%s已配置相同类型网卡，不可重复申请' % ip_str)

    if len(instance_data_filter_list) == 0:
        return json_helper.format_api_resp_msg(code=ErrorCode.SUCCESS, job_status=VsJobStatus.SUCCEED,
                                               detail=_ip_datas_list)

    # 判断虚拟机虚拟机是否开机中
    instance_unstarting_str = ""
    for _instance in instance_data_filter_list:
        vm_status = vmManager.libvirt_instance_status(_instance['host_ip'], _instance['instance_name'])
        # 虚拟机开机状态才可以做网卡配置
        if vm_status != VMLibvirtStatus.STARTUP:
            instance_unstarting_str += _instance['instance_ip'] + " "

    if instance_unstarting_str:
        return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                               detail='虚拟机:%s非运行中状态，无法添加网卡' % ip_str)

    # 识别需要创建的网卡类型并分配ip
    net_type = [NetCardType.INTERNAL, NetCardType.INTERNEL_TELECOM, NetCardType.INTERNEL_UNICOM,
                NetCardType.INTERNAL_IMAGE, NetCardType.INTERNAL_NAS]
    if netcard_type not in net_type:
        return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                               detail='KVM虚拟机没有网卡类型:%s ' % netcard_type)

    # 获取IP资源，先判断是否有人也在分配IP资源，有则等待1s，时间之后再优化
    ip_lock_unused = False
    while not ip_lock_unused:
        ret_ip_lock_status = ip_l_s.IpLockService().get_ip_lock_info('ip')
        if not ret_ip_lock_status:
            logging.error('外部接口新增网卡分配ip：检查IP时无法获取资源锁状态')
            return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                                   detail='检查IP时无法获取资源锁状态')
        if ret_ip_lock_status['istraceing'] == IpLockStatus.USED:
            time.sleep(1)
        else:
            ip_lock_unused = True

    # 更新ip_lock表istraceing字段为1
    ret_ip_lock_used_status, ret_ip_lock_used_datas = __update_ip_lock_used()
    if not ret_ip_lock_used_status:
        logging.error(ret_ip_lock_used_datas)
        return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                               detail=ret_ip_lock_used_datas)

    # 查询指定环境、网络区域是否有所需网段
    try:
        ret_segment_datas = segment_s.get_segments_data_by_type(net_area_list[0], dc_list[0], str(env_list[0]),
                                                                str(netcard_type))
        if not ret_segment_datas:
            ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
            if not ret_ip_lock_unused_status:
                logging.error(ret_ip_lock_unused_datas)
                return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                                       detail=ret_ip_lock_unused_datas)
            return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                                   detail='虚拟机所在网络区域没有指定网卡类型可用网段')

        # 获取可用ip并标记为已使用
        ret_ip_status, ret_ip_data, ret_ip_msg = __check_ip_resource(ret_segment_datas, str(env_list[0]),
                                                                     len(instance_data_filter_list))
        if not ret_ip_status:
            _change_db_ip_unused(ret_ip_data)
            ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
            if not ret_ip_lock_unused_status:
                logging.error(ret_ip_lock_unused_datas)
                return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                                       detail=ret_ip_lock_unused_datas)
            return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED, detail=ret_ip_msg)
    except Exception  as e:
        _msg = '添加网卡外部接口：获取网段标记ip出现异常 %s: check ip resource exception when instance add nic from platform，err：%s' % (
            ip_str, e)
        logging.error(_msg)
        ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
        if not ret_ip_lock_unused_status:
            logging.error(ret_ip_lock_unused_datas)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=_msg)

    # 更新ip_lock表istraceing字段为0
    ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
    if not ret_ip_lock_unused_status:
        _change_db_ip_unused(ret_ip_data)
        logging.error(ret_ip_lock_unused_datas)
        return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                               detail=ret_ip_lock_unused_datas)

    error_msg = []
    # 拼装虚拟机网卡信息用于配置网卡
    i = 0
    for _instance in instance_data_filter_list:
        mac = randomMAC()
        _instance['ip_addr_new'] = ret_ip_data[i]['ip_address']
        _instance['mac_addr'] = mac
        i += 1
        ret_status, ret_error_msg = __instance_add_netcard(_instance)
        if not ret_status:
            _msg = {
                "ip": _instance['instance_ip'],
                "error_msg": ret_error_msg
            }
            error_msg.append(_msg)
        else:
            _ip_datas = {
                "instanceIp": _instance['instance_ip'],
                "nasIp": _instance['ip_addr_new']
            }
            _ip_datas_list.append(_ip_datas)

    if error_msg:
        return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                               detail=error_msg)

    return json_helper.format_api_resp_msg(code=ErrorCode.SUCCESS, job_status=VsJobStatus.SUCCEED,
                                           detail=_ip_datas_list)


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
        return False, '外部接口新增网卡分配ip：无法更新资源锁状态为未使用中'
    return True, '外部接口新增网卡分配ip：更新资源锁状态为未使用中成功'


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
        return False, '外部接口新增网卡分配ip：无法更新资源锁状态为使用中'
    return True, '外部接口新增网卡分配ip：更新资源锁状态为使用中成功'


def __check_ip_resource(segment_datas, env, count):
    '''
        判断IP资源是否足够
    :param segment_datas:
    :param env:
    :param count:
    :return:
    '''
    # 获取可用ip
    ret_ip_datas, ret_ip_segment_datas = ip_s.get_available_ips(segment_datas, int(count), env)
    if not ret_ip_datas:
        return False, [], '虚拟机所在机房、网络区域下无法找到%s个可用IP' % str(count)

    # 标记ip为预分配
    ips_list = []
    for ip in ret_ip_datas:
        update_data = {
            'status': IPStatus.USED,
            'updated_at': get_datetime_str()
        }
        where_data = {
            'id': ip['id']
        }
        ret_mark_ip = ip_s.IPService().update_ip_info(update_data, where_data)
        if ret_mark_ip <= 0:
            continue
        ips_list.append(ip)

    if len(ips_list) < int(count):
        return False, [], '虚拟机网卡配置ip所需%s个可用IP修改为使用中状态部分失败' % str(count)
    else:
        return True, ret_ip_datas, ret_ip_segment_datas


def _change_db_ip_unused(ip_info):
    '''
        修改数据库ip表中ip状态为未使用
    :param ip_info:
    :return:
    '''
    # 标记ip为预分配
    ip_change_succeed_list = []
    for ip in ip_info:
        update_data = {
            'status': IPStatus.UNUSED
        }
        where_data = {
            'id': ip['id']
        }
        ret_mark_ip = ip_s.IPService().update_ip_info(update_data, where_data)
        if ret_mark_ip <= 0:
            continue
        ip_change_succeed_list.append(ip)

    if len(ip_change_succeed_list) < len(ip_info):
        return False, '虚拟机网卡配置ip所需%s个可用IP修改为使用中状态部分失败' % len(ip_info)
    else:
        return True, '虚拟机网卡配置ip所需%s个可用IP修改为使用中全部成功' % len(ip_info)


def __instance_add_netcard(instance_netcard_datas):
    # 添加任务信息
    task_id = instance_s.generate_task_id()
    insert_data = {
        'action': InstaceActions.INSTANCE_ADD_NETCARD,
        'instance_uuid': instance_netcard_datas['instance_uuid'],
        'request_id': task_id,
        'task_id': task_id,
        'start_time': get_datetime_str()
    }
    ret_action = instance_action_s.InstanceActionsServices().add_instance_action_info(insert_data)
    if ret_action.get('row_num') < 1:
        logging.error('add instance change configure action info error, insert_data:%s', insert_data)
        return False, "添加操作步骤到instance_action表失败"
    # 判断要申请ip是否被分配了，如果是生产或容灾环境，需要判断其对应的容灾或生产ip是否为未使用状态
    net_ip_list = []
    new_ip_status = ip_s.IPService().get_ip_by_ip_address(instance_netcard_datas['ip_addr_new'])
    net_ip_list.append(new_ip_status)
    new_ip_segment_data = segment_s.SegmentService().get_segment_info(new_ip_status['segment_id'])
    if not new_ip_status or not new_ip_segment_data:
        _msg = '网卡配置ip：无法获取数据库中ip信息或ip对应的网段信息'
        _job_status = ActionStatus.FAILD
        __update_config_msg_to_db(task_id, _msg, _job_status)
        return False, "无法获取数据库中待使用ip信息或ip对应的网段信息"

    if new_ip_status['status'] != IPStatus.USED:
        _msg = '网卡配置ip：新ip：%s不是使用中状态' % instance_netcard_datas['ip_addr_new']
        _job_status = ActionStatus.FAILD
        __update_config_msg_to_db(task_id, _msg, _job_status)
        return False, "新ip：%s不是使用中状态" % instance_netcard_datas['ip_addr_new']
    # 需要修改xml配置，同时做ip、网关修改注入
    instance_netcard_datas['netmask_new'] = __exchange_maskint(int(new_ip_status['netmask']))
    instance_netcard_datas['gateway_new'] = new_ip_status['gateway_ip']

    dev_name = new_ip_segment_data['host_bridge_name'] + '.' + str(new_ip_segment_data['vlan'])
    net_on_status, _msg = _instance_net_on(instance_netcard_datas['instance_name'], instance_netcard_datas['mac_addr'],
                                           instance_netcard_datas['host_ip'], dev_name)
    if not net_on_status:
        _job_status = ActionStatus.FAILD
        __update_config_msg_to_db(task_id, _msg, _job_status)
        _change_db_ip_unused(net_ip_list)
        return False, _msg

    ret_status, ret_msg = __change_instance_network(instance_netcard_datas['host_ip'],
                                                    instance_netcard_datas['instance_name'],
                                                    instance_netcard_datas)
    if ret_status:
        db_ret_status, db_ret_msg = __instance_ip_configure_change_db(instance_netcard_datas['instance_id'],
                                                                      instance_netcard_datas,
                                                                      instance_netcard_datas['env'])
        if not db_ret_status:
            _job_status = ActionStatus.FAILD
            __update_config_msg_to_db(task_id, db_ret_msg, _job_status)
            _change_db_ip_unused(net_ip_list)
            return False, db_ret_msg

        _job_status = ActionStatus.SUCCSESS
        __update_config_msg_to_db(task_id, db_ret_msg, _job_status)
    else:
        _job_status = ActionStatus.FAILD
        __update_config_msg_to_db(task_id, ret_msg, _job_status)
        _change_db_ip_unused(net_ip_list)
        return False, ret_msg

    return True, "网卡配置成功"


def __instance_ip_configure_change_db(ins_id, net_info, env):
    '''
        编辑instance_ip表
    :param ins_id:
    :param net_info:
    :param env:
    :return:
    '''
    ip_id_new = ip_s.IPService().get_ip_by_ip_address(net_info['ip_addr_new'])
    if not ip_id_new:
        msg = '无法在数据库中找到ip：%s 记录' % ip_id_new
        return False, msg

    # 查找生产、容灾环境对应的容灾、生产环境IP
    ret_change_status, ret_change_detail = __change_drprd_status(env, ip_id_new)
    if not ret_change_status:
        return False, ret_change_detail

    instance_ip_data = {
        'instance_id': ins_id,
        'ip_id': ip_id_new['id'],
        'mac': net_info['mac_addr'],
        'type': InstanceNicType.NORMAL_NETWORK_NIC,
        'isdeleted': '0',
        'created_at': get_datetime_str()
    }
    ret_add_ip = instance_ip_s.InstanceIPService().add_instance_ip_info(instance_ip_data)
    if ret_add_ip.get('row_num') <= 0:
        msg = "新增虚拟机网卡ip：%s信息到数据库失败" % ip_id_new['ip_address']
        return False, msg

    return True, '数据库记录修改成功'


def __change_drprd_status(env, ip_new):
    '''
        编辑ip表
    :param env:
    :param ip_new:
    :return:
    '''
    # 更新新ip状态
    if int(env) == DataCenterType.PRD:
        segment_dr = segment_match_s.SegmentMatchService().get_segment_match_info_by_prd_segment_id(ip_new['segment_id'])
        if not segment_dr:
            return False, "无法获取当前生产IP对应容灾网段信息"
        segment_dr_data = segment_s.SegmentService().get_segment_info(segment_dr['dr_segment_id'])
        if not segment_dr_data:
            return False, "无法获取当前生产IP对应容灾网段详细信息"
        # 拼凑虚拟机容灾IP
        dr_ip = segment_dr_data['segment'].split('.')[0] + '.' + segment_dr_data['segment'].split('.')[1] + \
                '.' + ip_new['ip_address'].split('.')[2] + '.' + ip_new['ip_address'].split('.')[3]
        dr_ip_info = ip_s.IPService().get_ip_by_ip_address(dr_ip)
        # 如果容灾IP是未使用中状态，可以使用
        if dr_ip_info:
            if dr_ip_info['status'] == IPStatus.UNUSED:
                # 重置对应ip为未使用
                update_dr_ip_data = {
                    'status': IPStatus.PRE_ALLOCATION
                }
                where_dr_ip_data = {
                    'id': dr_ip_info['id']
                }
                ret_mark_ip = ip_s.IPService().update_ip_info(update_dr_ip_data, where_dr_ip_data)
                if ret_mark_ip <= 0:
                    return False, "当前生产IP对应容灾IP从预分配重置为未使用状态失败"

    elif int(env) == DataCenterType.DR:
        segment_prd = segment_match_s.SegmentMatchService().get_segment_match_info_by_dr_segment_id(ip_new['segment_id'])
        if not segment_prd:
            return False, "无法获取当前容灾IP对应生产网段信息"
        segment_prd_data = segment_s.SegmentService().get_segment_info(segment_prd['prd_segment_id'])
        if not segment_prd_data:
            return False, "无法获取当前容灾IP对应生产网段详细信息"
        # 拼凑虚拟机生产IP
        prd_ip = segment_prd_data['segment'].split('.')[0] + '.' + segment_prd_data['segment'].split('.')[
            1] + '.' + \
                 ip_new['ip_address'].split('.')[2] + '.' + ip_new['ip_address'].split('.')[3]
        prd_ip_info = ip_s.IPService().get_ip_by_ip_address(prd_ip)
        # 如果生产环境ip是未使用中状态，可以使用
        if prd_ip_info:
            if prd_ip_info['status'] == IPStatus.UNUSED:
                # 重置对应ip为未使用
                update_dr_ip_data = {
                    'status': IPStatus.PRE_ALLOCATION
                }
                where_dr_ip_data = {
                    'id': prd_ip_info['id']
                }
                ret_mark_ip = ip_s.IPService().update_ip_info(update_dr_ip_data, where_dr_ip_data)
                if ret_mark_ip <= 0:
                    return False, "当前容灾IP对应生产IP从预分配重置为未使用状态失败"

    return True, "生产、容灾IP状态重置成功"


def _instance_net_on(instance_name, instance_mac, host_ip, dev):

    connect_instance = vmManager.libvirt_get_connect(host_ip, conn_type='instance', vmname=instance_name)
    if not connect_instance:
        return False, 'can not connect to libvirtd'
    return vmManager.libvirt_instance_net_on(connect_instance, instance_mac, dev)


# 子网掩码计算
def __exchange_maskint(mask_int):
    bin_arr = ['0' for i in range(32)]
    for i in range(mask_int):
        bin_arr[i] = '1'
    tmpmask = [''.join(bin_arr[i * 8:i * 8 + 8]) for i in range(4)]
    tmpmask = [str(int(tmpstr, 2)) for tmpstr in tmpmask]
    return '.'.join(tmpmask)


def __update_config_msg_to_db(task_id, msg, job_status):
    update_data = {
        'message': msg,
        'status': job_status,
        'finish_time': get_datetime_str()
    }
    where_data = {
        'task_id': task_id
    }
    return instance_action_s.InstanceActionsServices().update_instance_action_status(update_data, where_data)


def __change_instance_network(host_ip, ins_name, net_info):
    '''
        修改虚拟机指定网卡ip、掩码并启动网卡
    :param host_ip:
    :param ins_name:
    :param net_info:
    :return:
    '''

    # 连接libvirt找到对应虚拟机
    connect_libivrt = vmManager.libvirt_get_connect(host_ip, conn_type='instance', vmname=ins_name)
    if not connect_libivrt:
        return False, '无法使用libvirt进行虚拟机新增网卡配置，请联系管理员'

    # 通过libvirt串口配置虚拟机ip
    inject_net_status, result_msg = vmManager.libvirt_change_instance_ip(connect_libivrt, net_info, net_card_new=True)
    if not inject_net_status:
        return False, '无法使用libvirt进行虚拟机ip配置，请联系管理员'
    # elif 'output' in result_msg:
    #     if eval(result_msg)['return']['cmd_ret'] != 0:
    #         return False, '无法找到mac地址对应的网卡配置文件'
    # elif result_msg != '{"return":0}':
    #     return False, '无法找到mac地址对应的网卡配置文件'
    return True, '网卡配置成功'


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
