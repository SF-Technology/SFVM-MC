# coding=utf8
'''
    首页信息-V2
'''


from service.s_user.user_service import current_user_groups
from service.s_group.group_service import get_group_quota_used
from service.s_instance.instance_service import get_instances_in_group
from common_data_struct import base_define
from model.const_define import ErrorCode, VMStatus
import logging
import json_helper
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user


class DashboardV2Resp(base_define.Base):

    def __init__(self):
        self.info_list = []


@login_required
def dashboard_v2():
    resp = DashboardV2Resp()
    user_groups = current_user_groups()
    for _group in user_groups:
        # 应用组已使用资源
        _quota_used = get_group_quota_used(_group['id'])
        if _quota_used:
            _used_cpu = _quota_used['all_vcpu']
            _used_mem_mb = _quota_used['all_mem_mb']
            _used_disk_gb = _quota_used['all_disk_gb']
            _used_vm = _quota_used['instance_num']
        else:
            _used_cpu = 0
            _used_mem_mb = 0
            _used_disk_gb = 0
            _used_vm = 0

        # 应用组所有资源
        _all_cpu = _group['cpu']
        _all_mem_gb = _group['mem']
        _all_disk_gb = _group['disk']
        _all_vm = _group['vm']

        if _all_cpu != 0:
            _cpu_usable_per = float(_all_cpu - _used_cpu) / _all_cpu * 100
        else:
            logging.warn('group %s all cpu = 0 when get dashboard v2 info', _group['id'])
            _cpu_usable_per = 0

        if _all_mem_gb != 0:
            _all_mem_mb = _all_mem_gb * 1024
            _mem_usable_per = float(_all_mem_mb - _used_mem_mb) / _all_mem_mb * 100
        else:
            logging.warn('group %s all mem = 0 when get dashboard v2 info', _group['id'])
            _mem_usable_per = 0

        if _all_disk_gb != 0:
            _disk_usable_per = float(_all_disk_gb - _used_disk_gb) / _all_disk_gb * 100
        else:
            logging.warn('group %s all disk = 0 when get dashboard v2 info', _group['id'])
            _disk_usable_per = 0

        if _all_vm != 0:
            _vm_usable_per = float(_all_vm - _used_vm) / _all_vm * 100
        else:
            logging.warn('group %s all vm = 0 when get dashboard v2 info', _group['id'])
            _vm_usable_per = 0

        # 应用组下所有VM
        _instances = get_instances_in_group(_group['id'])
        _running_vms = 0
        _stop_vms = 0
        for _ins in _instances:
            if _ins['status'] == VMStatus.STARTUP:
                _running_vms += 1
            elif _ins['status'] == VMStatus.SHUTDOWN:
                _stop_vms += 1

        _info = {
            'group_name': _group['name'],
            'group_id':_group['id'],
            'cpu_used': long(_used_cpu),
            'mem_used': long(_used_mem_mb),
            'disk_used': long(_used_disk_gb),
            'vm_used': long(_used_vm),
            'cpu_all': _all_cpu,
            'mem_all': _all_mem_mb,
            'disk_all': _all_disk_gb,
            'cpu_usable_per': _cpu_usable_per,
            'mem_usable_per': _mem_usable_per,
            'disk_usable_per': _disk_usable_per,
            'vm_usable_per': _vm_usable_per,
            'all_vms': _all_vm,
            'running_vms': _running_vms,
            'stop_vms': _stop_vms
        }

        resp.info_list.append(_info)

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp.to_json())