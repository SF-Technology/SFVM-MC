# coding=utf8
'''
    IP管理-保留IP
'''
# __author__ =  ""


from flask import request
from service.s_ip import ip_service
from model.const_define import IPStatus, ErrorCode, OperationObject, OperationAction
import json_helper
import logging
from helper.time_helper import get_datetime_str
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
from service.s_operation.operation_service import add_operation_ip


@login_required
@add_operation_ip(OperationObject.IP, OperationAction.HOLD_IP)
def hold_ip():
    '''
        保留IP
    :return:
    '''
    ip_address = request.values.get('ip_address')
    if not ip_address:
        logging.info('no ip_address when hold ip')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    ip_info = ip_service.IPService().get_ip_info_by_ipaddress(ip_address)
    # 已初始化且未使用的IP才能保留
    if not (ip_info and ip_info['status'] == IPStatus.UNUSED):
        logging.info('IP status is wrong when hold ip')
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="只能保留已初始化且未使用的IP")

    update_data = {
        'status': IPStatus.HOLD,
        'updated_at': get_datetime_str(),
    }
    where_data = {
        'ip_address': ip_address,
    }
    ret = ip_service.IPService().update_ip_info(update_data, where_data)
    if ret <= 0:
        logging.error("hold ip error, update_data:%s, where_data:%s", str(update_data), str(where_data))
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


@login_required
@add_operation_ip(OperationObject.IP, OperationAction.HOLD_IP)
def hold_ips():
    '''
        批量保留IP
    :return:
    '''
    begin_ip = request.values.get('begin_ip')
    end_ip = request.values.get('end_ip')

    if not begin_ip or not end_ip:
        logging.info('begin or end ip is empty when hold ips')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    # 截取IP地址最后一位
    begin_ip_org = begin_ip.split('.')[3]
    end_ip_org = end_ip.split('.')[3]
    # 起始IP不能大于结束IP
    if int(begin_ip_org) > int(end_ip_org) or int(begin_ip_org) > 254 or int(begin_ip_org) < 1 \
            or int(end_ip_org) > 254 or int(end_ip_org) < 1:
        logging.info('begin or end ip is invalid when hold ips')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    ips_hold_list = []
    for i in range(int(begin_ip_org), int(end_ip_org) + 1):
        ips_hold_list.append(i)

    if not ips_hold_list:
        logging.info('no ip can hold when hold ips, begin: %s, end: %s', begin_ip, end_ip)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    # 截取IP地址前三位
    ip_c = begin_ip.split('.')[0] + '.' + begin_ip.split('.')[1] + '.' + begin_ip.split('.')[2] + '.'
    # 操作的IP数
    all_num = len(ips_hold_list)
    fail_num = 0
    for _hold_ip in ips_hold_list:
        hold_ip_address = str(ip_c) + str(_hold_ip)
        ip_info = ip_service.IPService().get_ip_by_ip_address(hold_ip_address)
        # 已初始化且未使用的IP才能保留
        if not (ip_info and ip_info['status'] == IPStatus.UNUSED):
            fail_num += 1
            continue

        update_data = {
            'status': IPStatus.HOLD,
            'updated_at': get_datetime_str(),
        }
        where_data = {
            'ip_address': hold_ip_address,
        }
        ret = ip_service.IPService().update_ip_info(update_data, where_data)
        if ret <= 0:
            logging.error("hold ips error, update_data:%s, where_data:%s", str(update_data), str(where_data))
            fail_num += 1
            continue

    # 全失败
    if fail_num == all_num:
        logging.error("hold ips all failed")
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    # 部分成功
    if 0 < fail_num < all_num:
        logging.error("hold ips part failed")
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS_PART, msg="部分IP保留成功")
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


@login_required
@add_operation_ip(OperationObject.IP, OperationAction.CANCEL_HOLD_IP)
def cancel_hold_ip():
    '''
        取消保留IP
    :return:
    '''
    ip_address = request.values.get('ip_address')
    if not ip_address:
        logging.info('no ip_address when cancel hold ip')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    ip_info = ip_service.IPService().get_ip_info_by_ipaddress(ip_address)
    # 已保留的IP才能取消保留
    if not (ip_info and ip_info['status'] == IPStatus.HOLD):
        logging.info('IP status is wrong when cancel hold ip')
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="只能取消保留已被保留的IP")

    update_data = {
        'status': IPStatus.UNUSED,
        'updated_at': get_datetime_str(),
    }
    where_data = {
        'ip_address': ip_address,
    }
    ret = ip_service.IPService().update_ip_info(update_data, where_data)
    if ret <= 0:
        logging.error("cancel hold ip error, update_data:%s, where_data:%s", str(update_data), str(where_data))
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


@login_required
@add_operation_ip(OperationObject.IP, OperationAction.CANCEL_HOLD_IP)
def cancel_hold_ips():
    '''
        批量取消保留IP
    :return:
    '''
    begin_ip = request.values.get('begin_ip')
    end_ip = request.values.get('end_ip')

    if not begin_ip or not end_ip:
        logging.info('begin or end ip is empty when cancel hold ips')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    # 截取IP地址最后一位
    begin_ip_org = begin_ip.split('.')[3]
    end_ip_org = end_ip.split('.')[3]
    # 起始IP不能大于结束IP
    if int(begin_ip_org) > int(end_ip_org) or int(begin_ip_org) > 254 or int(begin_ip_org) < 1 \
            or int(end_ip_org) > 254 or int(end_ip_org) < 1:
        logging.info('begin or end ip is invalid when cancel hold ips')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    ips_cancel_list = []
    for i in range(int(begin_ip_org), int(end_ip_org) + 1):
        ips_cancel_list.append(i)

    if not ips_cancel_list:
        logging.info('no ip can cancel hold when cancel hold ips, begin: %s, end: %s', begin_ip, end_ip)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    # 截取IP地址前三位
    ip_c = begin_ip.split('.')[0] + '.' + begin_ip.split('.')[1] + '.' + begin_ip.split('.')[2] + '.'
    # 操作的IP数
    all_num = len(ips_cancel_list)
    fail_num = 0
    for _cancel_ip in ips_cancel_list:
        cancel_ip_address = str(ip_c) + str(_cancel_ip)
        ip_info = ip_service.IPService().get_ip_by_ip_address(cancel_ip_address)
        # 已保留的IP才能取消保留
        if not (ip_info and ip_info['status'] == IPStatus.HOLD):
            fail_num += 1
            continue

        update_data = {
            'status': IPStatus.UNUSED,
            'updated_at': get_datetime_str(),
        }
        where_data = {
            'ip_address': cancel_ip_address,
        }
        ret = ip_service.IPService().update_ip_info(update_data, where_data)
        if ret <= 0:
            logging.error("cancel hold ips error, update_data:%s, where_data:%s", str(update_data), str(where_data))
            fail_num += 1
            continue

    # 全失败
    if fail_num == all_num:
        logging.error("hold ips all failed")
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    # 部分成功
    if 0 < fail_num < all_num:
        logging.error("hold ips part failed")
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS_PART, msg="部分IP取消保留成功")
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)
