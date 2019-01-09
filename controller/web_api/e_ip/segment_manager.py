# coding=utf8
'''
    网段管理
'''
from lib.shell.ansibleCmdV2 import ansible_remote_check_host_bridge
from lib.shell.ansiblePlaybookV2 import run_standard_host
from service.s_ip import segment_match
from model import network_segment
from service.s_datacenter import datacenter_service
from service.s_ip import segment_service
from model.const_define import ErrorCode, NetCardTypeToDevice, NetworkSegmentStatus
from config.default import HOST_STANDARD_DIR
import json_helper
import time
import logging
from IPy import IP
from service.s_user.user_service import current_user_all_area_ids
from service.s_host import host_service as host_s
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
from flask import request
from helper.time_helper import get_datetime_str


@login_required
def init_segment():
    '''
        获取网段-网络区域-机房的层级信息
    :return:
    '''
    user_all_area_ids = current_user_all_area_ids()

    segments_list = []
    segments_data = segment_service.get_level_info()
    for _segment in segments_data:
        # 只显示当前用户所属的区域
        if user_all_area_ids and _segment['area_id'] not in user_all_area_ids:
            continue
        segments_list.append(_segment)

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=segments_list)


@login_required
def get_ips_segment(segment_id, page):
    '''
        获取指定网段下所有IP地址
    :return:
    '''
    if not segment_id or not page:
        logging.info('no segment_id or page when get ips segment')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    flag, ips_data = segment_service.get_ips_page(segment_id, page)
    if flag == -1:
        logging.info('no segment: %s in db when get ips segment', segment_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    # 通过指定的网段输出该网段的IP个数
    if flag == 1:
        try:
            ip = IP(ips_data[0]["segment"] + "/" + ips_data[0]["netmask"])
            ip_len = ip.len()
        except:
            logging.info('the segment %s/%s is invalid', ips_data["segment"], ips_data["netmask"])
            ip_len = 0
        ips = ips_data
        segment_id = ips_data[0]["segment_id"]
        segment = ips_data[0]["segment"]
        netmask = ips_data[0]["netmask"]
    elif flag == 2:
        # 该网段下暂时无IP信息在db
        try:
            ip = IP(ips_data["segment"] + "/" + ips_data["netmask"])
            ip_len = ip.len()
        except:
            logging.info('the segment %s/%s is invalid', ips_data["segment"], ips_data["netmask"])
            ip_len = 0
        ips = None
        segment_id = ips_data["id"]
        segment = ips_data["segment"]
        netmask = ips_data["netmask"]

    ip_dic = {
        "ips": ips,
        "segment_id": segment_id,
        "segment": segment,
        "netmask": netmask,
        "len": ip_len,
        "pages": ip_len / 256
    }
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=ip_dic)


@login_required
def add_segment():
    '''
        录入一个新网段
    '''
    network_segment_match = request.json.get("network_segment_match",[])
    segment_match_dic = {}
    for index, item in enumerate(network_segment_match):
        status, res = check_prdr(item)
        if not status:
            return json_helper.format_api_resp(ErrorCode.ALL_FAIL, msg=res)
        bond_dev = NetCardTypeToDevice.MSG_DICT.get(item['segment_type'])
        insert_data = {
            'net_area_id': int(item['net_area_id']),
            'segment': item['segment'],
            'segment_type': item['segment_type'],
            'host_bridge_name': 'br_' + bond_dev,
            'netmask': str(item['netmask']),
            'vlan': str(item['vlan']),
            'gateway_ip': item['gateway'],
            'dns1': item['dns1'],
            'dns2': item['dns2'],
            'status': NetworkSegmentStatus.ENABLE,
            'created_at': get_datetime_str()
        }
        ret = segment_service.SegmentService().add_segment_info(insert_data)
        if ret['row_num'] <= 0:
            return json_helper.format_api_resp(code=ErrorCode.ALL_FAIL, msg="网段入库失败")
        if len(network_segment_match) == 2:
            dc_type = datacenter_service.DataCenterService().get_dctype_by_net_area_id(item['net_area_id'])
            if dc_type == '4':
                segment_match_dic['prd_segment_id'] = network_segment.get_network_segment_id_info_by_network_segment(
                    item['net_area_id'], item['segment'],
                    item['vlan'], item['gateway'],
                    'br_' + bond_dev)
            elif dc_type == '5':
                segment_match_dic['dr_segment_id'] = network_segment.get_network_segment_id_info_by_network_segment(
                    item['net_area_id'], item['segment'],
                    item['vlan'], item['gateway'],
                    'br_' + bond_dev)
    if len(network_segment_match) == 2:
        insert_data_match = {
            'prd_segment_id': int(segment_match_dic['prd_segment_id']['id']),
            'dr_segment_id': int(segment_match_dic['dr_segment_id']['id']),
            'isdeleted': '0'
        }
        ret_match = segment_match.SegmentMatchService().add_segment_match_info(insert_data_match)
        if ret_match['row_num'] <= 0:
            return json_helper.format_api_resp(code=ErrorCode.ALL_FAIL, msg="匹配网段入库失败")

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, msg="匹配网段已成功加入")


def check_prdr(in_env):
    if not all(in_env):
        return False, "请求入参缺失"

    # 校验网段是否合法
    try:
        IP(in_env['segment'] + "/" + str(in_env['netmask']))
    except:
        return False, "非法网段，请重新检查后录入"

    # 查询网段是否存在于数据库中.

    query_params = {
        'WHERE_AND': {
            '=': {
                'segment': in_env['segment'],
                'netmask': str(in_env['netmask'])
            }
        },
    }
    segment_nums, segment_datas = segment_service.SegmentService().query_data(**query_params)
    if segment_nums > 0:
        return False, "指定网段已存在于平台中，请确认"

    # 拉取网络区域下所有集群所有虚拟机列表
    db_host_data = host_s._get_hosts_of_net_area(int(in_env['net_area_id']))
    if not db_host_data:
        return False, "指定网络区域下没有一台物理机"

    # 判断物理机上是否有指定网桥对应的bond设备
    bond_dev = NetCardTypeToDevice.MSG_DICT.get(in_env['segment_type'])
    if not bond_dev:
        return False, "不支持已选网络类型录入"

    ret_check_msg = ""
    for _host in db_host_data:
        ret_run_status, ret_run_msg = ansible_remote_check_host_bridge(_host['ipaddress'], bond_dev)
        if not ret_run_status:
            return False, ret_run_msg
        elif ret_run_status is 1:
            ret_check_msg += ret_run_msg

    if ret_check_msg:
        return False, ret_check_msg

    # 建桥，脚本满足已经创建过的跳过
    ret_check_msg = ""
    for _host in db_host_data:
        host_list = [_host['ipaddress']]
        vlan_list = [int(in_env['vlan'])]
        host_bridge_dict = {
            "srcdir": HOST_STANDARD_DIR,
            "host_vlan_list": vlan_list,
            "br_bond": bond_dev
        }
        br_bond_create_shell_url = HOST_STANDARD_DIR + '/host_std_br_bond_create.yaml'
        run_result, run_message = run_standard_host(br_bond_create_shell_url, _host['ipaddress'], host_bridge_dict)
        if not run_result:
            logging.info('物理机%s初始化新增内网vlan执行playbook失败，原因:%s' % (_host['ipaddress'], run_message))

            return False, run_message

        time.sleep(2)

    if ret_check_msg:
        return False, ret_check_msg

    # 判断物理机上指定网桥可用性，暂时使用for循环减少并发，有不通的反馈出来
    host_test_bridge = {
        "bridge": 'br_' + bond_dev + '.' + str(in_env['vlan']),
        "gateway": in_env['gateway'],
        "vlan": in_env['vlan']
    }
    host_test_bridge_list = [host_test_bridge]

    ret_check_msg = ""
    for _host in db_host_data:
        res, message = host_s.check_vlan_connection(_host['ipaddress'], host_test_bridge_list)
        if not res:
            ret_check_msg += message

    if ret_check_msg:
        return False, ret_check_msg

    return True, ''









