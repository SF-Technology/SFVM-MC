# -*- coding:utf-8 -*-


# from flask.ext.httpauth import HTTPBasicAuth
from flask_httpauth import HTTPBasicAuth
from service.s_user import user_service as user_s
from helper import json_helper
from model.const_define import VsJobStatus, DataCenterTypeForVishnu, DataCenterTypeTransformCapital, IpTypeTransform, \
    IpType
from service.s_ip.segment_service import get_network_segments_data_paging, get_network_segments_data_in_dc_paging, \
    get_network_segments_data_by_segment_name, get_ip_datas_by_segmentid
from service.s_ip import ip_service
from flask import request
import logging
import IPy
from controller.web_api.ip_filter_decorator import ip_filter_from_other_platform

auth_api_user = HTTPBasicAuth()


@ip_filter_from_other_platform
@auth_api_user.login_required
def segment_capacity_to_other_platform():
    '''
        外部平台获取kvm网段或IP资源使用信息
    :return:
    '''
    data_from_vishnu = request.data
    logging.info(data_from_vishnu)
    data_requset = json_helper.loads(data_from_vishnu)
    datacenter = data_requset['dataCenter']
    env = data_requset['env']
    net_area = data_requset['netArea']
    network_segment = data_requset['networkSegment']
    page_num = data_requset['currentPage']
    page_size = data_requset['pageSize']

    if not datacenter or not env:
        return json_helper.format_api_resp_msg_to_vishnu_resource(job_status=VsJobStatus.FAILED, detail='输入机房、环境信息为空')

    get_network_segment_detail = False
    if network_segment:
        get_network_segment_detail = True

    get_net_area_detail = False
    if net_area:
        get_net_area_detail = True

    if get_net_area_detail and get_network_segment_detail:
        db_network_segment_datas = get_network_segments_data_by_segment_name(datacenter,
                                                                             str(DataCenterTypeForVishnu.TYPE_DICT[env]),
                                                                             net_area, network_segment)
        if not db_network_segment_datas:
            network_segments_params = {
                "result": []
            }
            return json_helper.format_api_resp_msg_to_vishnu_resource(job_status=VsJobStatus.SUCCEED,
                                                                      detail=network_segments_params)

        ip_data_lists = []
        all_ip_datas = get_ip_datas_by_segmentid(db_network_segment_datas['id'])
        if not all_ip_datas:
            # 计算该网段应该有的所有ip
            for __per_calculate_ip in IPy.IP(
                                    db_network_segment_datas['segment'] + '/' + db_network_segment_datas['netmask']):
                ip_params = {
                    "ip": __per_calculate_ip,
                    "status": IpType.UNINIT
                }
                ip_data_lists.append(ip_params)
            all_ip_params = {
                "result": ip_data_lists
            }
            return json_helper.format_api_resp_msg_to_vishnu_resource(job_status=VsJobStatus.SUCCEED,
                                                                      detail=all_ip_params)

        # 计算该网段应该有的所有ip
        calculate_ip_lists = []
        calculate_ip_data_lists = []
        for __per_calculate_ip in IPy.IP(db_network_segment_datas['segment'] + '/' + db_network_segment_datas['netmask']):
            __per_calculate_ip_params = {
                "ip": str(__per_calculate_ip),
                "status": IpTypeTransform.MSG_DICT[IpType.UNINIT]
            }
            calculate_ip_data_lists.append(__per_calculate_ip_params)
            calculate_ip_lists.append(str(__per_calculate_ip))

        for per_ip in all_ip_datas:
            if str(per_ip['ip_address']) in calculate_ip_lists:
                for __per_calculate_ip_data in calculate_ip_data_lists:
                    if __per_calculate_ip_data['ip'] == str(per_ip['ip_address']):
                        __per_calculate_ip_data['status'] = IpTypeTransform.MSG_DICT[per_ip['status']]

        all_ip_params = {
            "result": calculate_ip_data_lists
        }
        return json_helper.format_api_resp_msg_to_vishnu_resource(job_status=VsJobStatus.SUCCEED,
                                                                  detail=all_ip_params)

    elif get_net_area_detail:
        # 获取指定机房、环境、网络环境下的所有网段信息，需要分页
        network_segment_nums, db_network_segment_datas = get_network_segments_data_paging(datacenter,
                                                                                          str(DataCenterTypeForVishnu.
                                                                                              TYPE_DICT[env]),
                                                                                          net_area, page_num, page_size)
        if network_segment_nums <= 0:
            network_segments_params = {
                "rows": [],
                "current": page_num,
                "rowCount": page_size,
                "total": 0
            }
            return json_helper.format_api_resp_msg_to_vishnu_resource(job_status=VsJobStatus.SUCCEED,
                                                                      detail=network_segments_params)
        network_segment_datas = []
        for network_segment in db_network_segment_datas:
            ip_init_datas = ip_service.ip_inited_in_segment(network_segment['id'])
            ret_ip_available_status, ip_availables = ip_service.get_available_ip_by_segment_id(network_segment['id'])
            if not ip_init_datas:
                ip_total = 0
                ip_canallocated = 0
                ip_usedrate = 0
            else:
                if len(ip_init_datas) <= 0:
                    ip_total = 0
                    ip_canallocated = 0
                    ip_usedrate = 0
                else:
                    ip_total = len(ip_init_datas)
                    if not ret_ip_available_status:
                        ip_canallocated = 0
                    ip_canallocated = ip_availables
                    ip_usedrate = float('%.4f' % (float(ip_total - ip_canallocated) / float(ip_total)))

            per_network_segment_datas = {
                "canAllocated": ip_canallocated,
                "environment": env,
                "gateway": network_segment['gateway_ip'],
                "netDomain": net_area,
                "netName": network_segment['segment'],
                "networkId": '',
                "outerId": '',
                "subnetMask": network_segment['netmask'],
                "total": ip_total,
                "usedRate": ip_usedrate,
                "userType": "KVM",
                "vlanId": network_segment['vlan']
            }
            network_segment_datas.append(per_network_segment_datas)

        network_segments_params = {
            "rows": network_segment_datas,
            "current": page_num,
            "rowCount": page_size,
            "total": network_segment_nums
        }
        return json_helper.format_api_resp_msg_to_vishnu_resource(job_status=VsJobStatus.SUCCEED,
                                                                  detail=network_segments_params)

    else:
        # 返回指定机房、环境下的所有网段信息，需要分页
        network_segment_nums, db_network_segment_datas = get_network_segments_data_in_dc_paging(datacenter,
                                                                                                str(DataCenterTypeForVishnu.TYPE_DICT[env]),
                                                                                                page_num, page_size)
        if network_segment_nums <= 0:
            network_segments_params = {
                "rows": [],
                "current": page_num,
                "rowCount": page_size,
                "total": 0
            }
            return json_helper.format_api_resp_msg_to_vishnu_resource(job_status=VsJobStatus.SUCCEED,
                                                                      detail=network_segments_params)
        network_segment_datas = []
        for network_segment in db_network_segment_datas:
            ip_init_datas = ip_service.ip_inited_in_segment(network_segment['id'])
            ret_ip_available_status, ip_availables = ip_service.get_available_ip_by_segment_id(network_segment['id'])
            if not ip_init_datas:
                ip_total = 0
                ip_canallocated = 0
                ip_usedrate = 0
            else:
                if len(ip_init_datas) <= 0:
                    ip_total = 0
                    ip_canallocated = 0
                    ip_usedrate = 0
                else:
                    ip_total = len(ip_init_datas)
                    if not ret_ip_available_status:
                        ip_canallocated = 0
                    ip_canallocated = ip_availables
                    ip_usedrate = float('%.4f' % (float(ip_total - ip_canallocated) / float(ip_total)))

            per_network_segment_datas = {
                "canAllocated": ip_canallocated,
                "environment": env,
                "gateway": network_segment['gateway_ip'],
                "netDomain": network_segment['net_area'],
                "netName": network_segment['segment'],
                "networkId": '',
                "outerId": '',
                "subnetMask": network_segment['netmask'],
                "total": ip_total,
                "usedRate": ip_usedrate,
                "userType": "KVM",
                "vlanId": network_segment['vlan']
            }
            network_segment_datas.append(per_network_segment_datas)

        network_segments_params = {
            "rows": network_segment_datas,
            "current": page_num,
            "rowCount": page_size,
            "total": network_segment_nums
        }
        return json_helper.format_api_resp_msg_to_vishnu_resource(job_status=VsJobStatus.SUCCEED,
                                                                  detail=network_segments_params)


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
