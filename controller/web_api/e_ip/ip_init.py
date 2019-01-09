# coding=utf8
'''
    IP管理-初始化IP
'''
# __author__ =  ""

from flask import request
import logging
import time
from service.s_ip import ip_service
from service.s_ip import segment_service as segment_service
from service.s_ip import ip_lock_service as ip_l_s
from model.const_define import IPStatus, ErrorCode, OperationObject, OperationAction, IpLockStatus
import json_helper
from helper.time_helper import get_datetime_str
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
from service.s_operation.operation_service import add_operation_ip


@login_required
@add_operation_ip(OperationObject.IP, OperationAction.INIT_IP)
def init_ip(segment_id):
    '''
        初始化IP
    :param segment_id:
    :return:
    '''
    ip_address = request.values.get('ip_address')
    if not ip_address or not segment_id:
        logging.info('no ip_address or segment_id when init ip')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    # 获取IP资源，先判断是否有人也在分配IP资源，有则等待1s，时间之后再优化
    ip_lock_unused = False
    while not ip_lock_unused:
        ret_ip_lock_status = ip_l_s.IpLockService().get_ip_lock_info('ip')
        if not ret_ip_lock_status:
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='初始化IP时无法获取资源锁状态,请稍后再试')
        if ret_ip_lock_status['istraceing'] == IpLockStatus.USED:
            time.sleep(1)
        else:
            ip_lock_unused = True

    # 更新ip_lock表istraceing字段为1
    ret_ip_lock_used_status, ret_ip_lock_used_datas = __update_ip_lock_used()
    if not ret_ip_lock_used_status:
        logging.error(ret_ip_lock_used_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_used_datas)

    # 要确保该IP没有被初始化
    try:
        ip_info = ip_service.IPService().get_ip_by_ip_address(ip_address)
        if ip_info:
            logging.info('the IP has inited in db when init ip')
            ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
            if not ret_ip_lock_unused_status:
                logging.error(ret_ip_lock_unused_datas)
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="该IP已经初始化")

        ip_info_from_segment = segment_service.ip_info_in_segment(segment_id)
        if not ip_info_from_segment:
            logging.info('no segment: %s in db when init ip', segment_id)
            ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
            if not ret_ip_lock_unused_status:
                logging.error(ret_ip_lock_unused_datas)
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
        ip_vlan = ip_info_from_segment['vlan']
        ip_netmask = ip_info_from_segment['netmask']
        ip_segment_id = ip_info_from_segment['id']
        ip_gateway_ip = ip_info_from_segment['gateway_ip']
        ip_dns1 = ip_info_from_segment['dns1']
        ip_dns2 = ip_info_from_segment['dns2']

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
    except Exception as e:
        _msg = '初始化IP：ip初始化时出现异常 网段%s IP%s:ip init exception when ip init，err：%s' % (segment_id,ip_address,e)
        logging.error(_msg)
        ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
        if not ret_ip_lock_unused_status:
            logging.error(ret_ip_lock_unused_datas)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=_msg)

    # 更新ip_lock表istraceing字段为0
    ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
    if not ret_ip_lock_unused_status:
        logging.error(ret_ip_lock_unused_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)

    if ret == -1:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


@login_required
@add_operation_ip(OperationObject.IP, OperationAction.INIT_IP)
def init_ips(segment_id):
    '''
        批量初始化IP
    :param segment_id:
    :return:
    '''
    begin_ip = request.values.get('begin_ip')
    end_ip = request.values.get('end_ip')

    if not begin_ip or not end_ip:
        logging.info('begin or end ip is empty when init ips')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    # 获取IP资源，先判断是否有人也在分配IP资源，有则等待1s，时间之后再优化
    ip_lock_unused = False
    while not ip_lock_unused:
        ret_ip_lock_status = ip_l_s.IpLockService().get_ip_lock_info('ip')
        if not ret_ip_lock_status:
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='批量初始化IP时无法获取资源锁状态,请稍后再试')
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
        # 截取IP地址最后一位
        begin_ip_org = begin_ip.split('.')[3]
        end_ip_org = end_ip.split('.')[3]
        # 起始IP不能大于结束IP
        if int(begin_ip_org) > int(end_ip_org) or int(begin_ip_org) > 254 or int(begin_ip_org) < 1 \
                or int(end_ip_org) > 254 or int(end_ip_org) < 1:
            logging.info('begin or end ip is invalid when init ips')
            ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
            if not ret_ip_lock_unused_status:
                logging.error(ret_ip_lock_unused_datas)
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)
            return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

        inited_ips_list = []
        ips_init_list = []
        # 查询该网段下已初始化的IP数量
        ips_inited_db = ip_service.ip_inited_in_segment(segment_id)

        ip_info_db = segment_service.ip_info_in_segment(segment_id)
        if not ip_info_db:
            logging.info('segment info is invalid in db when init ips')
            ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
            if not ret_ip_lock_unused_status:
                logging.error(ret_ip_lock_unused_datas)
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
        ip_vlan = ip_info_db['vlan']
        ip_netmask = ip_info_db['netmask']
        ip_segment_id = ip_info_db['id']
        ip_gateway_ip = ip_info_db['gateway_ip']
        ip_dns1 = ip_info_db['dns1']
        ip_dns2 = ip_info_db['dns2']

        for i in range(len(ips_inited_db)):
            inited_ips_list.append(str(ips_inited_db[i]['ip_address']))

        # 截取IP地址前三位
        ip_c = begin_ip.split('.')[0] + '.' + begin_ip.split('.')[1] + '.' + begin_ip.split('.')[2] + '.'
        for i in range(int(begin_ip_org), int(end_ip_org)+1):
            ip_for_insert_to_sql = str(ip_c) + str(i)
            if ip_for_insert_to_sql in inited_ips_list:
                continue
            else:
                ips_init_list.append(i)

        if not ips_init_list:
            logging.info('no ip can init when init ips')
            ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
            if not ret_ip_lock_unused_status:
                logging.error(ret_ip_lock_unused_datas)
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

        # 操作的IP数
        all_num = len(ips_init_list)
        fail_num = 0
        for _ip_init in ips_init_list:
            ip_init_address = str(ip_c) + str(_ip_init)
            insert_data = {
                'ip_address': ip_init_address,
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
            if ret <= 0:
                logging.error("init ips error, insert_data: %s", str(insert_data))
                fail_num += 1
                continue
    except Exception as e:
        _msg = '批量初始化IP：初始化ip出现异常begin_ip %s，end_ip%s: batch ip init exception when ips init，err：%s'%(begin_ip,end_ip,e)
        logging.error(_msg)
        ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
        if not ret_ip_lock_unused_status:
            logging.error(ret_ip_lock_unused_datas)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=_msg)

    # 更新ip_lock表istraceing字段为0
    ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
    if not ret_ip_lock_unused_status:
        logging.error(ret_ip_lock_unused_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)

    # 全失败
    if fail_num == all_num:
        logging.error("init ips all failed")
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    # 部分成功
    if 0 < fail_num < all_num:
        logging.error("init ips part failed")
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS_PART, msg="部分IP初始化成功")
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


@login_required
@add_operation_ip(OperationObject.IP, OperationAction.CANCEL_INIT_IP)
def cancel_init_ip():
    '''
        取消初始化IP
    :return:
    '''
    ip_address = request.values.get('ip_address')
    if not ip_address:
        logging.info('no ip_address when cancel init ip')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    # 获取IP资源，先判断是否有人也在分配IP资源，有则等待1s，时间之后再优化
    ip_lock_unused = False
    while not ip_lock_unused:
        ret_ip_lock_status = ip_l_s.IpLockService().get_ip_lock_info('ip')
        if not ret_ip_lock_status:
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='去初始化IP时无法获取资源锁状态,请稍后再试')
        if ret_ip_lock_status['istraceing'] == IpLockStatus.USED:
            time.sleep(1)
        else:
            ip_lock_unused = True

    # 更新ip_lock表istraceing字段为1
    ret_ip_lock_used_status, ret_ip_lock_used_datas = __update_ip_lock_used()
    if not ret_ip_lock_used_status:
        logging.error(ret_ip_lock_used_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_used_datas)

    # 要确保该IP未使用
    try:
        ip_info = ip_service.IPService().get_ip_info_by_ipaddress(ip_address)
        if not (ip_info and ip_info['status'] == IPStatus.UNUSED):
            logging.info('only unused ip can do when cancel init ip')
            ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
            if not ret_ip_lock_unused_status:
                logging.error(ret_ip_lock_unused_datas)
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="只有未使用的IP才能取消初始化")

        ret = ip_service.del_ip_info(ip_info['id'])
    except  Exception  as e:
        _msg = '取消初始化IP：取消初始化ip出现异常ip%s: cancel ip init exception，err：%s' %(ip_address,e)
        logging.error(_msg)
        ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
        if not ret_ip_lock_unused_status:
            logging.error(ret_ip_lock_unused_datas)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=_msg)

    # 更新ip_lock表istraceing字段为0
    ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
    if not ret_ip_lock_unused_status:
        logging.error(ret_ip_lock_unused_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)

    if ret == -1:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


@login_required
@add_operation_ip(OperationObject.IP, OperationAction.CANCEL_INIT_IP)
def cancel_init_ips():
    '''
        批量取消初始化IP
    :return:
    '''
    begin_ip = request.values.get('begin_ip')
    end_ip = request.values.get('end_ip')

    if not begin_ip or not end_ip:
        logging.info('begin or end ip is empty when cancel init ips')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    # 获取IP资源，先判断是否有人也在分配IP资源，有则等待1s，时间之后再优化
    ip_lock_unused = False
    while not ip_lock_unused:
        ret_ip_lock_status = ip_l_s.IpLockService().get_ip_lock_info('ip')
        if not ret_ip_lock_status:
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='批量去初始化IP时无法获取资源锁状态,请稍后再试')
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
        # 截取IP地址最后一位
        begin_ip_org = begin_ip.split('.')[3]
        end_ip_org = end_ip.split('.')[3]
        # 起始IP不能大于结束IP
        if int(begin_ip_org) > int(end_ip_org) or int(begin_ip_org) > 254 or int(begin_ip_org) < 1 \
                or int(end_ip_org) > 254 or int(end_ip_org) < 1:
            logging.info('begin or end ip is invalid when cancel init ips')
            ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
            if not ret_ip_lock_unused_status:
                logging.error(ret_ip_lock_unused_datas)
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)
            return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

        ips_cancel_list = []
        for i in range(int(begin_ip_org), int(end_ip_org) + 1):
            ips_cancel_list.append(i)

        if not ips_cancel_list:
            logging.info('no ip can cancel init when cancel init ips, begin: %s, end: %s', begin_ip, end_ip)
            ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
            if not ret_ip_lock_unused_status:
                logging.error(ret_ip_lock_unused_datas)
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

        # 截取IP地址前三位
        ip_c = begin_ip.split('.')[0] + '.' + begin_ip.split('.')[1] + '.' + begin_ip.split('.')[2] + '.'
        # 操作的IP数
        all_num = len(ips_cancel_list)
        fail_num = 0
        for _cancel_ip in ips_cancel_list:
            cancel_ip_address = str(ip_c) + str(_cancel_ip)
            # 要确保该IP未使用
            ip_info = ip_service.IPService().get_ip_info_by_ipaddress(cancel_ip_address)
            if not (ip_info and ip_info['status'] == IPStatus.UNUSED):
                logging.info('only unused ip can do when cancel init ip')
                fail_num += 1
                continue

            ret = ip_service.del_ip_info(ip_info['id'])
            if ret == -1:
                logging.info('del ip info error when cancel init ip')
                fail_num += 1
                continue
    except Exception as e:
        _msg = '批量取消初始化IP：取消初始化ip出现异常begin_ip %s，end_ip%s: cancel ips init exception，err：%s'%(begin_ip,end_ip,e)
        logging.error(_msg)
        ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
        if not ret_ip_lock_unused_status:
            logging.error(ret_ip_lock_unused_datas)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=_msg)

    # 更新ip_lock表istraceing字段为0
    ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
    if not ret_ip_lock_unused_status:
        logging.error(ret_ip_lock_unused_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)

    # 全失败
    if fail_num == all_num:
        logging.error("cancel init ips all failed")
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    # 部分成功
    if 0 < fail_num < all_num:
        logging.error("cancel init ips part failed")
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS_PART, msg="部分IP取消初始化成功")
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


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
        return False, '无法更新资源锁状态为未使用中'
    return True, '更新资源锁状态为未使用中成功'


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
        return False, '无法更新资源锁状态为使用中'
    return True, '更新资源锁状态为使用中成功'
