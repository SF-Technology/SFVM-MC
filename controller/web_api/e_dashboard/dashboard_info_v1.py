# coding=utf8
'''
    首页信息-V1
'''


from service.s_user.user_service import current_user_areas
from service.s_datacenter import datacenter_service as dc_s
from service.s_hostpool.hostpool_service import get_hostpool_nums_in_dcs
from service.s_host.host_service import get_host_nums_in_dcs, get_hosts_of_datacenter
from service.s_instance.instance_service import get_instances_in_dc
from service.s_dashboard.dashboard_service import get_cpu_mem_used_in_dc
from model.const_define import ErrorCode, VMStatus, HostStatus
import json_helper
from common_data_struct import base_define
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user


class DashboardV1Resp(base_define.Base):

    def __init__(self):
        self.overview = {}
        self.dc_vms = []
        self.dc_cpu = []
        self.dc_mem = []


@login_required
def dashboard_v1():
    resp = DashboardV1Resp()
    user_areas_ids = current_user_areas()
    resp.overview['area_nums'] = len(user_areas_ids)

    # 当前用户所有机房
    all_dc_num, all_dc_data = dc_s.DataCenterService().get_all_datacenters_of_areas(user_areas_ids)
    resp.overview['datacenter_nums'] = all_dc_num
    for _dc in all_dc_data:
        _all_ins = get_instances_in_dc(_dc['id'])
        _shutdown_num = 0
        _startup_num = 0
        _other_num = 0
        if _all_ins:
            for _ins in _all_ins:
                if _ins['status'] == VMStatus.STARTUP:
                    _startup_num += 1
                elif _ins['status'] == VMStatus.SHUTDOWN:
                    _shutdown_num += 1
                else:
                    _other_num += 1

        _dc_vms = {
            'dc_name': _dc['name'],
            'dc_type': _dc['dc_type'],
            'all_vms': len(_all_ins),
            'shutdown_vms': _shutdown_num,
            'startup_vms': _startup_num,
            'other_vms': _other_num
        }
        resp.dc_vms.append(_dc_vms)

        _used_data = get_cpu_mem_used_in_dc(_dc['id'])
        _dc_cpu = {
            'dc_name': _dc['name'],
            'dc_type': _dc['dc_type'],
            'used': _used_data['cpu_used'],
            'unused': _used_data['cpu_unused'],
            'used_per': _used_data['cpu_used_per'],
            'unused_per': _used_data['cpu_unused_per'],
        }
        resp.dc_cpu.append(_dc_cpu)

        _dc_mem = {
            'dc_name': _dc['name'],
            'dc_type': _dc['dc_type'],
            'used': _used_data['mem_used'],
            'unused': _used_data['mem_unused'],
            'used_per': _used_data['mem_used_per'],
            'unused_per': _used_data['mem_unused_per'],
        }
        resp.dc_mem.append(_dc_mem)

    resp.overview['hostpool_nums'] = get_hostpool_nums_in_dcs(all_dc_data)
    resp.overview['host_nums'] = get_host_nums_in_dcs(all_dc_data)

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp.to_json())


@login_required
def dashboard_v1_map():
    # 当前用户所有机房
    user_areas_ids = current_user_areas()
    all_dc_num, all_dc_data = dc_s.DataCenterService().get_all_datacenters_of_areas(user_areas_ids)

    province_data = [
        {'drilldown': 'beijing', 'name': '北京', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'tianjing', 'name': '天津', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'shanghai', 'name': '上海', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'chongqing', 'name': '重庆', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'hebei', 'name': '河北', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'henan', 'name': '河南', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'yunnan', 'name': '云南', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'liaoning', 'name': '辽宁', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'heilongjiang', 'name': '黑龙江', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'hunan', 'name': '湖南', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'anhui', 'name': '安徽', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'shandong', 'name': '山东', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'xinjiang', 'name': '新疆', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'jiangsu', 'name': '江苏', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'zhejiang', 'name': '浙江', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'jiangxi', 'name': '江西', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'hubei', 'name': '湖北', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'guangxi', 'name': '广西', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'gansu', 'name': '甘肃', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'shanxi', 'name': '山西', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'neimenggu', 'name': '内蒙古', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'shanxi', 'name': '陕西', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'jilin', 'name': '吉林', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'fujian', 'name': '福建', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'guizhou', 'name': '贵州', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'guangdong', 'name': '广东', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'qinghai', 'name': '青海', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'xizang', 'name': '西藏', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'sichuan', 'name': '四川', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'ningxia', 'name': '宁夏', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'hainan', 'name': '海南', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'taiwan', 'name': '台湾', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'xianggang', 'name': '香港', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0},
        {'drilldown': 'aomen', 'name': '澳门', 'value': 0, 'dc': 0, 'host': 0, 'vm': 0}
    ]

    for _dc in all_dc_data:
        _all_ins = get_instances_in_dc(_dc['id'])
        _all_host = get_hosts_of_datacenter(_dc['id'])
        # 统计错误host数
        _error_host_nums = 0
        for _host in _all_host:
            if _host['status'] == HostStatus.ERROR:
                _error_host_nums += 1

        # 机房所在省
        _dc_province = _dc['province']
        for _province in province_data:
            # 找到对应的省
            if _province['name'] == _dc_province:
                _province['dc'] += 1
                _province['host'] += len(_all_host)
                _province['vm'] += len(_all_ins)
                _province['value'] += _error_host_nums
                break

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=province_data)


