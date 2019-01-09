# -*- coding:utf-8 -*-
# __author__ =  ""

# from flask.ext.httpauth import HTTPBasicAuth
from flask_httpauth import HTTPBasicAuth
from service.s_user import user_service as user_s
from service.s_ip import segment_service
from service.s_net_area import net_area
from service.s_datacenter import datacenter_service
from service.s_ip import ip_service, vip_service
from service.s_datacenter.datacenter_service import DataCenterService as dc_s
from service.s_net_area.net_area import NetAreaService as net_area_s
from service.s_ip.segment_service import SegmentService as ip_segment_s
from service.s_ip import segment_service as segment_s
from service.s_ip import segment_match as segment_m
from service.s_ip import ip_lock_service as ip_l_s
from service.s_group import group_service as group_s
from model.const_define import VsJobStatus, IPStatus, DataCenterTypeForVishnu, DataCenterTypeTransform, \
    DataCenterType, ErrorCode, IpLockStatus, NetCardType
from helper import json_helper
from helper.time_helper import get_datetime_str
from flask import request
import threading
import logging
import time
from controller.web_api.ip_filter_decorator import ip_filter_from_other_platform

auth_api_user = HTTPBasicAuth()

SEGMENT_DATA_THREADINGLOCK = threading.Lock()


# 子网掩码计算
def __exchange_maskint(mask_int):
    bin_arr = ['0' for i in range(32)]
    for i in range(mask_int):
        bin_arr[i] = '1'
    tmpmask = [''.join(bin_arr[i * 8:i * 8 + 8]) for i in range(4)]
    tmpmask = [str(int(tmpstr, 2)) for tmpstr in tmpmask]
    return '.'.join(tmpmask)


def __get_segment_datas_multithreading(one_ip_segment):
    '''
        多线程获取每个网段可用ip数量
    :param one_ip_segment:
    :return:
    '''
    global SEGMENT_DATA_THREADINGLOCK
    global SEGMENT_DATAS_LIST
    ip_ret, ip_num = ip_service.get_available_ip_by_segment_id(one_ip_segment['id'])
    if ip_ret:
        ip_segment_with_netmask = one_ip_segment['segment'] + '/' + one_ip_segment['netmask']
        segment_params = {
            "segment": ip_segment_with_netmask,
            "ip_num": ip_num
        }
        SEGMENT_DATA_THREADINGLOCK.acquire()
        try:
            SEGMENT_DATAS_LIST.append(segment_params)
        finally:
            SEGMENT_DATA_THREADINGLOCK.release()


@ip_filter_from_other_platform
@auth_api_user.login_required
def ip_resource_display_to_other_platform():
    '''
        将kvm已有的网段展示给其他平台
    :return:
    '''
    global SEGMENT_DATAS_LIST
    dc_num, dc_datas = dc_s().get_all_datacenter_in_db()
    if dc_num <= 0:
        return json_helper.format_api_resp_msg_to_vishnu_resource(job_status=VsJobStatus.FAILED, detail='平台中没有机房')

    # 获取指定机房下所有网络区域信息
    ip_detail = []
    for per_dc in dc_datas:
        net_area_ip_datas = []
        net_area_num, net_area_datas = net_area_s().get_net_area_datas_in_dc(per_dc['id'])
        if net_area_num <= 0:
            dc_params = {
                "datacenter": per_dc['name'],
                "env_ip_resources": [
                    {
                        "env": DataCenterTypeTransform.MSG_DICT.get(int(per_dc['dc_type'])),
                        "net_area_ip_resources": []
                    }
                ]
            }
            ip_detail.append(dc_params)
            continue
        for one_net_area_data in net_area_datas:
            SEGMENT_DATAS_LIST = []
            ip_segment_num, ip_segment_datas = ip_segment_s().get_segment_datas_in_net_area(one_net_area_data['id'])
            if ip_segment_num <= 0:
                net_area_params = {
                    "net_area_name": one_net_area_data['name'],
                    "segment_datas": []
                }
                net_area_ip_datas.append(net_area_params)
                continue

            threads = []
            for one_ip_segment in ip_segment_datas:
                segment_thread = threading.Thread(target=__get_segment_datas_multithreading,
                                                  args=(one_ip_segment, ))
                threads.append(segment_thread)
                segment_thread.start()
            # 判断多线程是否结束
            for t in threads:
                t.join()

            net_area_params = {
                "net_area_name": one_net_area_data['name'],
                "segment_datas": SEGMENT_DATAS_LIST
            }
            net_area_ip_datas.append(net_area_params)

        dc_params = {
            "datacenter": per_dc['name'],
            "env_ip_resources": [
                {
                    "env": DataCenterTypeTransform.MSG_DICT.get(int(per_dc['dc_type'])),
                    "net_area_ip_resources": net_area_ip_datas
                }
            ]
        }
        ip_detail.append(dc_params)
    return json_helper.format_api_resp_msg_to_vishnu_resource(job_status=VsJobStatus.SUCCEED,
                                                              detail=ip_detail)


@ip_filter_from_other_platform
@auth_api_user.login_required
def ip_resource_display_to_other_platform_new():
    '''
        将kvm已有的网段展示给其他平台新接口，查询指定网段可用的ip数量
    :return:
    '''
    data_from_vishnu = request.data
    logging.info(data_from_vishnu)
    data_requset = json_helper.loads(data_from_vishnu)
    req_datacenter = data_requset['dataCenter']
    req_env = data_requset['env']
    req_net_area = data_requset['netArea']
    req_net_name = data_requset['netName']
    # 校验入参是否为空
    if not req_env or not req_net_area or not req_net_name or not req_datacenter:
        return json_helper.format_api_resp_msg_to_vishnu_resource(job_status=VsJobStatus.FAILED, detail='入参有空值')

    # 查询指定环境、网络区域是否有所需网段
    ret_segment = segment_service.SegmentService().get_segment_info_bysegment(req_net_name.split('/')[0])
    if not ret_segment:
        return json_helper.format_api_resp_msg_to_vishnu_resource(job_status=VsJobStatus.FAILED, detail="无法找到需要申请的网段")

    ret_net_area_info = net_area.NetAreaService().get_net_area_info(ret_segment['net_area_id'])
    if not ret_net_area_info:
        return json_helper.format_api_resp_msg_to_vishnu_resource(job_status=VsJobStatus.FAILED, detail="无法找到指定网段所属网络区域信息")

    ret_datacenter_info = datacenter_service.DataCenterService().get_datacenter_info(
        ret_net_area_info['datacenter_id'])
    if not ret_datacenter_info:
        return json_helper.format_api_resp_msg_to_vishnu_resource(job_status=VsJobStatus.FAILED, detail="无法找到指定机房信息")
    if req_env not in DataCenterTypeForVishnu.TYPE_DICT:
        return json_helper.format_api_resp_msg_to_vishnu_resource(job_status=VsJobStatus.FAILED, detail="无法找到指定机房类型信息")
    if str(DataCenterTypeForVishnu.TYPE_DICT[req_env]) != ret_datacenter_info['dc_type']:
        return json_helper.format_api_resp_msg_to_vishnu_resource(job_status=VsJobStatus.FAILED, detail="无法找到指定网络区域对应网段信息")

    # 获取可用ip
    ret_ip_available_status, ret_ip_available = ip_service.get_all_available_segment_ip(ret_segment['id'], str(
        DataCenterTypeForVishnu.TYPE_DICT[req_env]))

    if not ret_ip_available_status:
        ret_params = {
            "ip_num": 0
        }
        return json_helper.format_api_resp_msg_to_vishnu_resource(job_status=VsJobStatus.SUCCEED, detail=ret_params)
    ret_params = {
        "ip_num": len(ret_ip_available)
    }
    return json_helper.format_api_resp_msg_to_vishnu_resource(job_status=VsJobStatus.SUCCEED, detail=ret_params)


@ip_filter_from_other_platform
@auth_api_user.login_required
def ip_apply_from_other_platform():
    '''
        外部平台申请ip
    :return:
    '''
    data_from_vishnu = request.data
    logging.info(data_from_vishnu)
    data_requset = json_helper.loads(data_from_vishnu)
    req_datacenter = data_requset['datacenter']
    req_env = data_requset['env']
    req_net_area = data_requset['net_area']
    req_net_name = data_requset['net_name']
    cluster_id = data_requset['cluster_id']
    opuser = data_requset['opUser']
    sys_code = data_requset['sys_code']
    taskid_vs = data_requset['taskid']
    ip_count = data_requset['ipCount']
    prd_dr_ip_all_needed = data_requset['prdDrAllNeeded']  # '0'代表普通申请，'1'需要同时申请prd、dr环境的ip

    # 校验入参是否为空
    if not req_env or not req_net_area or not req_net_name or not req_datacenter:
        return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                               detail='empty input of env, net area information or net name '
                                                      'when apply ip')
    if not cluster_id or not opuser or not sys_code or not taskid_vs:
        return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                               detail='empty input of cluster_id, opuser, '
                                                      'task id or sys_code when apply ip')

    if not str(ip_count) or not str(prd_dr_ip_all_needed):
        return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                               detail='empty input of ipCount or prdDrAllNeeded when apply ip')

    # 查询指定环境、网络区域是否有所需网段
    ret_segment = segment_service.SegmentService().get_segment_info_bysegment(req_net_name.split('/')[0])
    if not ret_segment:
        return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                               detail="无法找到需要申请的网段")

    ret_net_area_info = net_area.NetAreaService().get_net_area_info(ret_segment['net_area_id'])
    if not ret_net_area_info:
        return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                               detail="无法找到指定网段所属网络区域信息")

    ret_datacenter_info = datacenter_service.DataCenterService().get_datacenter_info(ret_net_area_info['datacenter_id'])
    if not ret_datacenter_info:
        return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                               detail="无法找到指定机房信息")
    if req_env not in DataCenterTypeForVishnu.TYPE_DICT:
        return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                               detail="无法找到指定机房类型信息")
    if str(DataCenterTypeForVishnu.TYPE_DICT[req_env]) != ret_datacenter_info['dc_type']:
        return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                               detail="无法找到指定网络区域对应网段信息")

    # 如果是申请生产或者容灾环境ip，需判断网段对应关系表中是否有记录
    if req_env == 'PRD':
        segment_dr = segment_m.SegmentMatchService().get_segment_match_info_by_prd_segment_id(
            ret_segment['id'])
        if not segment_dr:
            return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                                   detail='指定机房、网络区域下无法找到生产网段对应的容灾网段ID')
        segment_dr_data = segment_s.SegmentService().get_segment_info(segment_dr['dr_segment_id'])
        if not segment_dr_data:
            return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                                   detail='指定机房、网络区域下无法找到生产网段对应的容灾网段详细信息')

    elif req_env == 'DR':
        segment_prd = segment_m.SegmentMatchService().get_segment_match_info_by_dr_segment_id(
            ret_segment['id'])
        if not segment_prd:
            return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                                   detail='指定机房、网络区域下无法找到容灾网段对应的生产网段ID')
        segment_prd_data = segment_s.SegmentService().get_segment_info(segment_prd['prd_segment_id'])
        if not segment_prd_data:
            return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                                   detail='指定机房、网络区域下无法找到容灾网段对应的生产网段详细信息')

    # 获取IP资源，先判断是否有人也在分配IP资源，有则等待1s，时间之后再优化
    ip_lock_unused = False
    while not ip_lock_unused:
        ret_ip_lock_status = ip_l_s.IpLockService().get_ip_lock_info('ip')
        if not ret_ip_lock_status:
            logging.error('外部接口分配vip：检查IP时无法获取资源锁状态')
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
    try:
        segments_data_list = []
        segments_data_list.append(ret_segment)
        # 获取可用ip
        ret_ip_datas, ret_ip_segment_datas = ip_service.get_available_ips(segments_data_list, int(ip_count), str(
            DataCenterTypeForVishnu.TYPE_DICT[req_env]))
        if not ret_ip_datas:
            ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
            if not ret_ip_lock_unused_status:
                logging.error(ret_ip_lock_unused_datas)
                return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                                       detail=ret_ip_lock_unused_datas)
            return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                                   detail='指定机房、网络区域下无法找到%s个可用IP' % str(ip_count))

        # 标记ip为预分配
        logging.info(ret_ip_datas)
        ips_list = []
        prd_ips_list = []
        dr_ips_list = []
        ip_details = {}
        for ip in ret_ip_datas:
            update_data = {
                'status': IPStatus.USED
            }
            where_data = {
                'id': ip['id']
            }
            ret_mark_ip = ip_service.IPService().update_ip_info(update_data, where_data)
            if ret_mark_ip <= 0:
                continue

            # 录入vip信息到数据库中
            insert_vip_data = {
                'ip_id': ip['id'],
                'cluster_id': cluster_id,
                'apply_user_id': opuser,
                'sys_code': sys_code,
                'isdeleted': '0',
                'created_at': get_datetime_str()
            }
            ret_vip = vip_service.VIPService().add_vip_info(insert_vip_data)
            if ret_vip.get('row_num') <= 0:
                continue

            ip_datas = {
                'ip': ip['ip_address'],
                'vlanId': ip['vlan'],
                'subnetMask': __exchange_maskint(int(ip['netmask'])),
                'gateway': ip['gateway_ip']
            }
            ips_list.append(ip_datas)

            # 生产环境需要预分配对应容灾环境ip，容灾环境需要预分配生产环境ip
            if req_env == 'PRD':
                # 拼凑虚拟机容灾ip并预分配ip
                dr_ip = segment_dr_data['segment'].split('.')[0] + '.' + segment_dr_data['segment'].split('.')[1] + \
                        '.' + ip['ip_address'].split('.')[2] + '.' + ip['ip_address'].split('.')[3]
                dr_ip_info = ip_service.IPService().get_ip_by_ip_address(dr_ip)
                # 如果容灾环境ip未初始化，默认初始化
                if not dr_ip_info:
                    if not __init_ip(segment_dr_data, dr_ip):
                        continue
                    dr_ip_info = ip_service.IPService().get_ip_by_ip_address(dr_ip)

                if prd_dr_ip_all_needed == '1':
                    update_data = {
                        'status': IPStatus.USED
                    }
                    where_data = {
                        'id': dr_ip_info['id']
                    }
                    ret_mark_ip = ip_service.IPService().update_ip_info(update_data, where_data)
                    if ret_mark_ip <= 0:
                        continue

                    # 录入vip信息到数据库中
                    insert_vip_data = {
                        'ip_id': dr_ip_info['id'],
                        'cluster_id': cluster_id,
                        'apply_user_id': opuser,
                        'sys_code': sys_code,
                        'isdeleted': '0',
                        'created_at': get_datetime_str()
                    }
                    ret_vip = vip_service.VIPService().add_vip_info(insert_vip_data)
                    if ret_vip.get('row_num') <= 0:
                        continue
                else:
                    update_data = {
                        'status': IPStatus.PRE_ALLOCATION
                    }
                    where_data = {
                        'ip_address': dr_ip
                    }
                    ret_mark_ip = ip_service.IPService().update_ip_info(update_data, where_data)
                    if ret_mark_ip <= 0:
                        continue

                # 拼装容灾ip信息
                dr_ip_datas = {
                    'ip': dr_ip_info['ip_address'],
                    'vlanId': dr_ip_info['vlan'],
                    'subnetMask': __exchange_maskint(int(dr_ip_info['netmask'])),
                    'gateway': dr_ip_info['gateway_ip']
                }
                dr_ips_list.append(dr_ip_datas)
            elif req_env == 'DR':
                # 拼凑虚拟机生产ip并预分配ip
                prd_ip = segment_prd_data['segment'].split('.')[0] + '.' + segment_prd_data['segment'].split('.')[1] + \
                         '.' + ip['ip_address'].split('.')[2] + '.' + ip['ip_address'].split('.')[3]
                prd_ip_info = ip_service.IPService().get_ip_by_ip_address(prd_ip)
                # 如果生产环境ip未初始化，默认初始化
                if not prd_ip_info:
                    if not __init_ip(segment_prd_data, prd_ip):
                        continue
                    prd_ip_info = ip_service.IPService().get_ip_by_ip_address(prd_ip)

                if prd_dr_ip_all_needed == '1':
                    update_data = {
                        'status': IPStatus.USED
                    }
                    where_data = {
                        'id': prd_ip_info['id']
                    }
                    ret_mark_ip = ip_service.IPService().update_ip_info(update_data, where_data)
                    if ret_mark_ip <= 0:
                        continue

                    # 录入vip信息到数据库中
                    insert_vip_data = {
                        'ip_id': prd_ip_info['id'],
                        'cluster_id': cluster_id,
                        'apply_user_id': opuser,
                        'sys_code': sys_code,
                        'isdeleted': '0',
                        'created_at': get_datetime_str()
                    }
                    ret_vip = vip_service.VIPService().add_vip_info(insert_vip_data)
                    if ret_vip.get('row_num') <= 0:
                        continue
                else:
                    update_data = {
                        'status': IPStatus.PRE_ALLOCATION
                    }
                    where_data = {
                        'ip_address': prd_ip
                    }
                    ret_mark_ip = ip_service.IPService().update_ip_info(update_data, where_data)
                    if ret_mark_ip <= 0:
                        continue

                # 拼装生产ip信息
                prd_ip_datas = {
                    'ip': prd_ip_info['ip_address'],
                    'vlanId': prd_ip_info['vlan'],
                    'subnetMask': __exchange_maskint(int(prd_ip_info['netmask'])),
                    'gateway': prd_ip_info['gateway_ip']
                }
                prd_ips_list.append(prd_ip_datas)
    except Exception as e:
        _msg = '外部平台申请IP：预分配ip出现异常: distribution ip exception，err：%s'%e
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
        return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                               detail=ret_ip_lock_unused_datas)

    if len(ips_list) <= 0:
        return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                               detail='指定机房、网络区域下%s个可用IP修改为预分配状态全部失败' % str(ip_count))
    elif req_env == 'PRD' and (len(ips_list) + len(dr_ips_list)) < int(ip_count) * 2:
        return json_helper.format_api_resp_msg(code=ErrorCode.SUCCESS_PART, job_status=VsJobStatus.FAILED,
                                               detail='生产环境指定机房、网络区域下%s个可用IP修改为预分配状态部分失败' % str(ip_count))
    elif req_env == 'DR' and (len(ips_list) + len(prd_ips_list)) < int(ip_count) * 2:
        return json_helper.format_api_resp_msg(code=ErrorCode.SUCCESS_PART, job_status=VsJobStatus.FAILED,
                                               detail='容灾环境指定机房、网络区域下%s个可用IP修改为预分配状态部分失败' % str(ip_count))
    elif len(ips_list) < int(ip_count):
        return json_helper.format_api_resp_msg(code=ErrorCode.SUCCESS_PART, job_status=VsJobStatus.FAILED,
                                               detail='指定机房、网络区域下%s个可用IP修改为预分配状态部分失败' % str(ip_count))
    else:
        if req_env == 'PRD':
            ip_details['prd'] = ips_list
            ip_details['dr'] = dr_ips_list
        elif req_env == 'DR':
            ip_details['dr'] = ips_list
            ip_details['prd'] = prd_ips_list
        else:
            ip_details['default'] = ips_list
        return json_helper.format_api_resp_msg(code=ErrorCode.SUCCESS, job_status=VsJobStatus.SUCCEED,
                                               detail=ip_details)


@ip_filter_from_other_platform
@auth_api_user.login_required
def ips_apply_from_other_platform():
    '''
        外部平台申请KVM IP, IP会置为预分配
    :return:
    '''
    data_from_api = request.data
    logging.info(data_from_api)
    data_requset = json_helper.loads(data_from_api)
    req_datacenter = data_requset['dataCenter']
    req_env = data_requset['env']
    req_net_area = data_requset['netArea']
    count = data_requset['ipNums']
    netcare_type = data_requset.get('netCardType', NetCardType.INTERNAL)

    # 校验入参是否为空
    if not req_net_area or not req_datacenter or not req_env or not count:
        return json_helper.format_api_resp_msg(code=ErrorCode.PARAM_ERR, job_status=VsJobStatus.FAILED,
                                               detail='机房、环境、网络区域或ip数量入参为空')

    # 查询指定环境、网络区域是否有所需网段，容灾微应用需要遍历联通、电信所有可用网段
    if DataCenterTypeForVishnu.TYPE_DICT[req_env] == DataCenterType.MINIARCHDR:
        ret_segment_datas_telecom = segment_s.get_segments_data_by_type(req_net_area, req_datacenter,
                                                                        str(DataCenterTypeForVishnu.TYPE_DICT[req_env]),
                                                                        NetCardType.INTERNEL_TELECOM)
        ret_segment_datas_unicom = segment_s.get_segments_data_by_type(req_net_area, req_datacenter,
                                                                       str(DataCenterTypeForVishnu.TYPE_DICT[req_env]),
                                                                       NetCardType.INTERNEL_UNICOM)
        ret_segment_datas = ret_segment_datas_telecom + ret_segment_datas_unicom

    else:
        ret_segment_datas = segment_s.get_segments_data_by_type(req_net_area, req_datacenter,
                                                                str(DataCenterTypeForVishnu.TYPE_DICT[req_env]),
                                                                netcare_type)
    if not ret_segment_datas:
        return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                               detail='指定机房、网络区域下没有可用网段用于分配IP')

    # 获取IP资源，先判断是否有人也在分配IP资源，有则等待1s，时间之后再优化
    ip_lock_unused = False
    while not ip_lock_unused:
        ret_ip_lock_status = ip_l_s.IpLockService().get_ip_lock_info('ip')
        if not ret_ip_lock_status:
            logging.error('外部接口分配vip：检查IP时无法获取资源锁状态')
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

    try:
        # 获取可用ip
        ret_ip_datas, ret_ip_segment_datas = ip_service.get_available_ips(ret_segment_datas, int(count), str(DataCenterTypeForVishnu.TYPE_DICT[req_env]))
        if not ret_ip_datas:
            ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
            if not ret_ip_lock_unused_status:
                logging.error(ret_ip_lock_unused_datas)
                return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                                       detail=ret_ip_lock_unused_datas)
            return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                                   detail='指定机房、网络区域下无法找到%s个可用IP' % str(count))

        # 如果是申请生产或者容灾环境ip，需判断网段对应关系表中是否有记录
        if req_env == 'PRD':
            segment_dr = segment_m.SegmentMatchService().get_segment_match_info_by_prd_segment_id(ret_ip_segment_datas['id'])
            if not segment_dr:
                ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
                if not ret_ip_lock_unused_status:
                    logging.error(ret_ip_lock_unused_datas)
                    return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                                           detail=ret_ip_lock_unused_datas)
                return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                                       detail='指定机房、网络区域下无法找到生产网段对应的容灾网段ID')
            segment_dr_data = segment_s.SegmentService().get_segment_info(segment_dr['dr_segment_id'])
            if not segment_dr_data:
                ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
                if not ret_ip_lock_unused_status:
                    logging.error(ret_ip_lock_unused_datas)
                    return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                                           detail=ret_ip_lock_unused_datas)
                return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                                       detail='指定机房、网络区域下无法找到生产网段对应的容灾网段详细信息')

        elif req_env == 'DR':
            segment_prd = segment_m.SegmentMatchService().get_segment_match_info_by_dr_segment_id(ret_ip_segment_datas['id'])
            if not segment_prd:
                ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
                if not ret_ip_lock_unused_status:
                    logging.error(ret_ip_lock_unused_datas)
                    return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                                           detail=ret_ip_lock_unused_datas)
                return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                                       detail='指定机房、网络区域下无法找到容灾网段对应的生产网段ID')
            segment_prd_data = segment_s.SegmentService().get_segment_info(segment_prd['prd_segment_id'])
            if not segment_prd_data:
                ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
                if not ret_ip_lock_unused_status:
                    logging.error(ret_ip_lock_unused_datas)
                    return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                                           detail=ret_ip_lock_unused_datas)
                return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                                       detail='指定机房、网络区域下无法找到容灾网段对应的生产网段详细信息')

        # 标记ip为预分配
        logging.info(ret_ip_datas)
        ips_list = []
        prd_ips_list = []
        dr_ips_list = []
        ip_details = {}
        for ip in ret_ip_datas:
            update_data = {
                'status': IPStatus.PRE_ALLOCATION,
                'updated_at': get_datetime_str()
            }
            where_data = {
                'id': ip['id']
            }
            ret_mark_ip = ip_service.IPService().update_ip_info(update_data, where_data)
            if ret_mark_ip <= 0:
                continue
            ip_datas = {
                'ip': ip['ip_address'],
                'vlanId': ip['vlan'],
                'subnetMask': __exchange_maskint(int(ip['netmask'])),
                'gateway': ip['gateway_ip'],
                'ip_type': ret_ip_segment_datas['segment_type']
            }
            ips_list.append(ip_datas)

            # 生产环境需要预分配对应容灾环境ip，容灾环境需要预分配生产环境ip
            if req_env == 'PRD':
                # 拼凑虚拟机容灾ip并预分配ip
                dr_ip = segment_dr_data['segment'].split('.')[0] + '.' + segment_dr_data['segment'].split('.')[1] + \
                        '.' + ip['ip_address'].split('.')[2] + '.' + ip['ip_address'].split('.')[3]
                dr_ip_info = ip_service.IPService().get_ip_by_ip_address(dr_ip)
                # 如果容灾环境ip未初始化，默认初始化
                if not dr_ip_info:
                    if not __init_ip(segment_dr_data, dr_ip):
                        continue
                    dr_ip_info = ip_service.IPService().get_ip_by_ip_address(dr_ip)

                update_data = {
                    'status': IPStatus.PRE_ALLOCATION
                }
                where_data = {
                    'ip_address': dr_ip
                }
                ret_mark_ip = ip_service.IPService().update_ip_info(update_data, where_data)
                if ret_mark_ip <= 0:
                    continue

                # 拼装容灾ip信息
                dr_ip_datas = {
                    'ip': dr_ip_info['ip_address'],
                    'vlanId': dr_ip_info['vlan'],
                    'subnetMask': __exchange_maskint(int(dr_ip_info['netmask'])),
                    'gateway': dr_ip_info['gateway_ip']
                }
                dr_ips_list.append(dr_ip_datas)
            elif req_env == 'DR':
                # 拼凑虚拟机生产ip并预分配ip
                prd_ip = segment_prd_data['segment'].split('.')[0] + '.' + segment_prd_data['segment'].split('.')[1] + \
                         '.' + ip['ip_address'].split('.')[2] + '.' + ip['ip_address'].split('.')[3]
                prd_ip_info = ip_service.IPService().get_ip_by_ip_address(prd_ip)
                # 如果生产环境ip未初始化，默认初始化
                if not prd_ip_info:
                    if not __init_ip(segment_prd_data, prd_ip):
                        continue
                    prd_ip_info = ip_service.IPService().get_ip_by_ip_address(prd_ip)
                update_data = {
                    'status': IPStatus.PRE_ALLOCATION
                }
                where_data = {
                    'ip_address': prd_ip
                }
                ret_mark_ip = ip_service.IPService().update_ip_info(update_data, where_data)
                if ret_mark_ip <= 0:
                    continue

                # 拼装生产ip信息
                prd_ip_datas = {
                    'ip': prd_ip_info['ip_address'],
                    'vlanId': prd_ip_info['vlan'],
                    'subnetMask': __exchange_maskint(int(prd_ip_info['netmask'])),
                    'gateway': prd_ip_info['gateway_ip']
                }
                prd_ips_list.append(prd_ip_datas)
    except Exception as e:
        _msg = '外部接口预分配IP：预分配ip出现异常: distribution ip exception，err：%s' %e
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
        return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                               detail=ret_ip_lock_unused_datas)

    if len(ips_list) <= 0:
        return json_helper.format_api_resp_msg(code=ErrorCode.SYS_ERR, job_status=VsJobStatus.FAILED,
                                               detail='指定机房、网络区域下%s个可用IP修改为预分配状态全部失败' % str(count))
    elif req_env == 'PRD' and (len(ips_list) + len(dr_ips_list)) < int(count)*2:
        return json_helper.format_api_resp_msg(code=ErrorCode.SUCCESS_PART, job_status=VsJobStatus.FAILED,
                                               detail='生产环境指定机房、网络区域下%s个可用IP修改为预分配状态部分失败' % str(count))
    elif req_env == 'DR' and (len(ips_list) + len(prd_ips_list)) < int(count)*2:
        return json_helper.format_api_resp_msg(code=ErrorCode.SUCCESS_PART, job_status=VsJobStatus.FAILED,
                                               detail='容灾环境指定机房、网络区域下%s个可用IP修改为预分配状态部分失败' % str(count))
    elif len(ips_list) < int(count):
        return json_helper.format_api_resp_msg(code=ErrorCode.SUCCESS_PART, job_status=VsJobStatus.FAILED,
                                               detail='指定机房、网络区域下%s个可用IP修改为预分配状态部分失败' % str(count))
    else:
        if req_env == 'PRD':
            ip_details['prd'] = ips_list
            ip_details['dr'] = dr_ips_list
        elif req_env == 'DR':
            ip_details['dr'] = ips_list
            ip_details['prd'] = prd_ips_list
        else:
            ip_details['default'] = ips_list
        logging.info(ip_details)
        return json_helper.format_api_resp_msg(code=ErrorCode.SUCCESS, job_status=VsJobStatus.SUCCEED,
                                               detail=ip_details)


def __init_ip(segment_datas, ip_address):
    '''
        IP初始化
    :param segment_datas:
    :param ip_address:
    :return:
    '''
    ip_vlan = segment_datas['vlan']
    ip_netmask = segment_datas['netmask']
    ip_segment_id = segment_datas['id']
    ip_gateway_ip = segment_datas['gateway_ip']
    ip_dns1 = segment_datas['dns1']
    ip_dns2 = segment_datas['dns2']

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
    if ret == -1:
        return False
    return True


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
        return False, '外部平台分配VIP：检查IP时无法更新资源锁状态为未使用中'
    return True, '外部平台分配VIP：检查IP时更新资源锁状态为未使用中成功'


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
        return False, '外部平台分配VIP：检查IP时无法更新资源锁状态为使用中'
    return True, '外部平台分配VIP：检查IP时更新资源锁状态为使用中成功'


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
