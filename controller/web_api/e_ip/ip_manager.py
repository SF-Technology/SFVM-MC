# coding=utf8
'''
    IP管理
'''


from flask import request
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
import json_helper
from model.const_define import ErrorCode, IPStatus
import logging
from service.s_ip import ip_service as ip_s
from service.s_ip import vip_service as vip_s
from service.s_ip import segment_service as segment_s
from service.s_net_area import net_area
from service.s_datacenter import datacenter_service


@login_required
def ip_instance_info():
    '''
        获取IP分配给VM的详细信息
    :return:
    '''
    ip_address = request.values.get('ip_address')
    if not ip_address:
        logging.info('no ip_address when get ip info')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    ip_info = ip_s.IPService().get_ip_info_by_ipaddress(ip_address)
    if not ip_info:
        logging.error('IP %s info no exist in db when get ip info', ip_address)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    # 检查ip是否为应用vip
    vip_info = vip_s.VIPService().get_vip_by_id(ip_info['id'])
    if not vip_info:
        if ip_info['status'] != IPStatus.USED:
            logging.info('IP %s status %s is not used when get ip info', ip_address, ip_info['status'])
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="IP状态不对，不能查看IP详细信息")

        ip_instance_data = ip_s.get_instance_info_by_ip(ip_address)
        if ip_instance_data:
            instance_name = ip_instance_data.get('instance_name', None)
            datacenter_name = ip_instance_data.get('datacenter_name', None)
            net_area_name = ip_instance_data.get('net_area_name', None)
        else:
            instance_name = None
            datacenter_name = None
            net_area_name = None

        ip_data = {
            'ip_address': ip_address,
            'datacenter': datacenter_name,
            'net_area': net_area_name,
            'instance_name': instance_name,
            'gateway': ip_info['gateway_ip'],
            'netmask': ip_info['netmask'],
            'vlan': ip_info['vlan'],
            'service_id': '',
            'is_vip': '0'
        }
    else:
        segment_info = segment_s.SegmentService().get_segment_info(ip_info['segment_id'])
        if not segment_info:
            _msg = '无法获取IP：%s的网段信息' % ip_address
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=_msg)

        net_area_info = net_area.NetAreaService().get_net_area_info(segment_info['net_area_id'])
        if not net_area_info:
            net_area_name = ''
        net_area_name = net_area_info['name']
        datacenter_info = datacenter_service.DataCenterService().get_datacenter_info(net_area_info['datacenter_id'])
        if not datacenter_info:
            datacenter_name = ''
        datacenter_name = datacenter_info['name']

        ip_data = {
            'ip_address': ip_address,
            'datacenter': datacenter_name,
            'net_area': net_area_name,
            'instance_name': '',
            'gateway': ip_info['gateway_ip'],
            'netmask': ip_info['netmask'],
            'vlan': ip_info['vlan'],
            'sys_code': vip_info['sys_code'],
            'is_vip': '1'
        }

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=ip_data)
