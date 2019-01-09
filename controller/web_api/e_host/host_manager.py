# coding=utf8
'''
    物理机管理
'''
# __author__ =  ""

from flask import request
import logging
import json_helper
import time
from config.default import HOST_NET_CARD
from lib.vrtManager.connection import CONN_SSH
from lib.vrtManager.connection import connection_manager
from model.const_define import ErrorCode, OperationObject, OperationAction, DataCenterType
from service.s_host import host_service as host_s, host_schedule_service as host_s_s
from service.s_instance import instance_service as ins_s
from service.s_hostpool import hostpool_service as hostpool_s
from common_data_struct import host_info
import datetime
from helper.time_helper import get_datetime_str
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
from service.s_operation.operation_service import add_operation_host
from lib.shell.ansibleCmdV2 import check_host_bond_connection, host_std_checklist, send_file_to_host, \
    run_change_host_bridge_shell, host_run_shell
from lib.shell.ansiblePlaybookV2 import run_standard_host


@login_required
@add_operation_host(OperationObject.HOST, OperationAction.ADD)
def add_host(hostpool_id):
    '''
        新增host
    :param hostpool_id:
    :return:
    '''
    name = request.values.get('name')
    # 序列号
    sn = request.values.get('sn')
    ip_address = request.values.get('ip_address')
    hold_mem_gb = request.values.get('hold_mem_gb')
    manage_ip = request.values.get('manage_ip')
    vlan_id = request.values.get('vlan_id')

    if not name or not hostpool_id or not sn or not ip_address or not hold_mem_gb \
            or not manage_ip or not vlan_id:
        logging.info('the params is invalid when add host')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="入参缺失")

    # 管理IP对应的host数据已存在
    host_data = host_s.HostService().get_host_info_by_manage_ip(manage_ip)
    if host_data:
        logging.info('manage ip %s to host is exist', manage_ip)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="该HOST数据已存在，不能重复创建")

    # # 检查host上主网初始化配置是否ready，微应用物理机略过
    # dc_type = hostpool_s.get_env_of_hostpool(hostpool_id)
    # if not dc_type:
    #     return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="无法获取机房类型信息")
    # if int(dc_type) == DataCenterType.PRD or int(dc_type) == DataCenterType.DR:
    #     bond_res, bond_msg = host_s.check_bond_connection(ip_address)
    #     if not bond_res:
    #         logging.info(bond_msg)
    #         return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=bond_msg)
    # else:
    #     pass

    # 将bridge改名脚本下发到host
    res, msg =__send_change_bridge_shell(ip_address)
    if not res:
        logging.error(msg)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=msg)

    # 将检测vlan脚本下发到host
    res, msg = host_s.send_check_vlan(ip_address)
    if not res:
        logging.error(msg)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=msg)

    # 检查HOST上主网网桥是否为brvlan,存在则修改
    bond_res, tag, bond_msg = host_s.check_bond_connection(ip_address, vlan_id)
    if not bond_res:
        if tag:
            source_bridge = 'brvlan' + vlan_id
            dest_bridge = 'br_' + HOST_NET_CARD + '.' + vlan_id
            vlan_nic = HOST_NET_CARD + '.' + vlan_id
            # 如果br_bond0.xx主网不存在,则执行修改网桥脚本
            run_change_host_bridge_shell(ip_address, source_bridge, dest_bridge, vlan_nic)
            time.sleep(10)
            host_network_available = False
            try_count = 0
            while try_count < 3 and not host_network_available:
                try_result = connection_manager.host_is_up(CONN_SSH, ip_address)
                if try_result is True:
                    host_network_available = True
                try_count += 1

            if not host_network_available:
                err_msg = '修改HOST %s 网桥名称失败' % ip_address
                logging.error(err_msg)
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=err_msg)
            info_msg = '修改HOST %s 网桥名称成功' % ip_address
        else:
            logging.error(bond_msg)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=bond_msg )
    else:
        info_msg = 'HOST %s 网桥名称正确,无需修改' % ip_address
    logging.info(info_msg)

    # 检查HOST OS版本是否为7.3
    ver_res, ver_msg = host_s.check_host_os_ver(ip_address)
    if not ver_res:
        logging.info(ver_msg)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ver_msg)

    ret_stand, de_msg = host_s.standard_host(ip_address, hostpool_id)
    if not ret_stand:
        logging.info('ansible standard host %s failed', manage_ip)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=de_msg)

    insert_data = {
        'name': name,
        'displayname': name,
        'sn': sn,
        'ipaddress': ip_address,
        'hold_mem_gb': hold_mem_gb,
        'manage_ip': manage_ip,
        'isdeleted': '0',
        'hostpool_id': hostpool_id,
        'created_at': get_datetime_str(),
        'instances_collect_time': get_datetime_str(),
        'host_collect_time': get_datetime_str(),
        'host_performance_collect_time': get_datetime_str(),
        'host_clone_status':'0'
    }
    ret = host_s.HostService().add_host_info(insert_data)
    if ret.get('row_num') < 1:
        logging.info('add host info to db error when standard host, insert_data:%s', insert_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR,msg="host信息入库失败")

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


@login_required
def get_host_detail(host_id):
    '''
        获取host详情
    :param host_id:
    :return:
    '''
    if not host_id:
        logging.info('no host_id when get host detail')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    host_db = host_s.HostService().get_host_info(host_id)
    if not host_db:
        logging.info('host %s no exist in db when get host detail', host_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="不存在该物理机信息")

    host = host_info.HostInfo()
    host.displayname = host_db['displayname']
    host.ipaddress = host_db['ipaddress']
    host.manage_ip = host_db['manage_ip']
    host.status = host_db['status']
    host.hold_mem_gb = host_db['hold_mem_gb']
    host.sn = host_db['sn']
    host.ostype = host_db['ostype']

    # host性能数据
    host_perform_info = host_s_s.get_host_used(host_db, expire=False)
    if host_perform_info:
        host.cpu_core = host_perform_info.get('cpu_core', 'unknown')
        host.current_cpu_used = host_perform_info.get('current_cpu_used', 'unknown')
        host.mem_size = host_perform_info.get('mem_size', 'unknown')
        host.current_mem_used = host_perform_info.get('current_mem_used', 'unknown')
        host.disk_size = host_perform_info.get('disk_size', 'unknown')
        host.current_disk_used = host_perform_info.get('current_disk_used', 'unknown')
        host.collect_time = host_perform_info['collect_time']
        host.start_time = host_perform_info['start_time']
        host.images = host_perform_info.get('images', 'unknown')
        host.libvirt_status = host_perform_info.get('libvirt_status', 'unknown')
        host.libvirt_port = host_perform_info.get('libvirt_port', 'unknown')

    host_level_info = host_s.get_level_info(host_db['id'])
    if host_level_info:
        host.hostpool = host_level_info['hostpool_name']
        host.net_area = host_level_info['net_area_name']
        host.datacenter = host_level_info['datacenter_name']
    host.instance_nums = ins_s.get_instances_nums_in_host(host_db['id'])

    # todo: libvirtd状态、服务端口，物理机开机时间、os版本、镜像数量、卷存储路径、序列号
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=host.to_json())


@login_required
@add_operation_host(OperationObject.HOST, OperationAction.DELETE)
def delete_host():
    ERR_RET = 0
    all_host_id = request.values.get("host_id")
    if not all_host_id:
        logging.info('no host_id input when delete host')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="参数错误")
    for host_id in all_host_id.split(','):
        host_data = host_s.HostService().get_host_info(host_id)
        if not host_data:
            ERR_RET += 1
            continue

        if host_data['isdeleted'] == '1':
            ERR_RET += 1
            continue

        instance_nums = ins_s.get_instances_nums_in_host(host_id)
        if instance_nums == None:
            ERR_RET += 1
            continue
        elif instance_nums > 0:
            ERR_RET += 1
            continue
        elif instance_nums == 0:
            host_ip = host_data['ipaddress']
            host_s._pool_delete(host_ip)
            update_data = {
                "isdeleted": '1',
                "deleted_at": datetime.datetime.now()
            }
            where_data = {
                "id": host_id
            }
            db_ret = host_s.HostService().update_host_info(update_data, where_data)
            if db_ret != 1:
                ERR_RET += 1
                continue
            else:
                logging.info('host ' + str(host_id) + ' delete successful')
                continue

        else:
            ERR_RET += 1
            continue

    if ERR_RET == 0:
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS)
    elif len(all_host_id.split(',')) == 1 and ERR_RET == 1:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    elif len(all_host_id.split(',')) == ERR_RET:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    else:
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS_PART)


@login_required
@add_operation_host(OperationObject.HOST, OperationAction.ALTER)
def host_update(host_id):
    name = request.values.get('name')
    ip_address = request.values.get('ip_address')
    hold_mem_gb = request.values.get('hold_mem_gb')
    manage_ip = request.values.get('manage_ip')

    if not host_id or not name or not ip_address or not hold_mem_gb or not manage_ip:
        logging.error('the params is invalid when update host')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    host_data = host_s.HostService().get_host_info(host_id)
    if not host_data:
        logging.error('the host %s is no exist in db when update host', host_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    if host_data['manage_ip'] != manage_ip:
        # 管理IP对应的host数据已存在
        host_data = host_s.HostService().get_host_info_by_manage_ip(manage_ip)
        if host_data:
            logging.info('manage ip %s to host is exist', manage_ip)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="该HOST数据已存在，不能重复创建")

    update_data = {
        'name': name,
        'displayname': name,
        'ipaddress': ip_address,
        'hold_mem_gb': hold_mem_gb,
        'manage_ip': manage_ip,
        'updated_at': get_datetime_str()
    }
    where_data = {
        'id': host_id,
    }
    ret = host_s.HostService().update_host_info(update_data, where_data)
    if ret < 0:
        logging.error("update host error, update_data:%s, where_data:%s", str(update_data), str(where_data))
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)




def __send_change_bridge_shell(host_ip):
    '''
        下发host网桥改名脚本到物理机上
    :param host_ip:
    :return:
    '''
    src_file_dir = HOST_STANDARD_DIR + '/change_bridge.sh',
    dest_file_dir = '/root'
    return send_file_to_host(host_ip, src_file_dir, dest_file_dir)
