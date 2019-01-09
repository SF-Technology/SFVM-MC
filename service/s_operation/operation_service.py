# coding=utf8
'''
    操作记录
'''


import model.operation as operation_db
from collect_data.base import Global_define
from lib.dbs.mysql import Mysql
import logging
import traceback
from flask import request
from model.const_define import ErrorCode, OperationObject, OperationAction
import logging
import json
from helper import time_helper
import datetime
from service.s_user import user_service
from functools import wraps
from service.s_instance import instance_service as ins_s
from service.s_host import host_service
from service.s_host import host_service as host_s
from flask import request

class OperationService:
    def __init__(self):
        self.operation_db = operation_db.Operation(db_flag='kvm', table_name='operation_records')

    def query_data(self, **params):
        return self.operation_db.simple_query(**params)

    def insert_operation(self, insert_data):
        return self.operation_db.insert(insert_data)

    def get_operation_record(self, **params):
        return self.operation_db.query_operation_record(**params)

    def get_operation_list(self, **params):
        return self.operation_db.query_operation_list(**params)


def add_operation(operation_object, operation_action):
    def _add_operation(func):
        @wraps(func)
        def insert_log(*argv, **kwargs):
            user = user_service.get_user()
            res = func(*argv, **kwargs)
            try:
                tmp = json.loads(res.data)
            except:
                return res

            if tmp["code"] == ErrorCode.SUCCESS:
                operation_result = "SUCCESS"
            elif tmp["code"] == ErrorCode.SUCCESS_PART:
                operation_result = "SUCCESS_PART"
            else:
                operation_result = "FAILED"

            client_ip = request.headers.get('X-Forwarded-For', '')

            insert_data = {
                "operator": user["user_id"],
                "operator_ip": client_ip,
                "operation_object": operation_object,
                "operation_action": operation_action,
                "operation_date": time_helper.get_datetime_str(),
                "operation_result": operation_result,
                "extra_data": ""
            }
            OperationService().insert_operation(insert_data)
            return res

        return insert_log

    return _add_operation


def add_operation_login(operation_object, operation_action):
    def _add_operation(func):
        @wraps(func)
        def insert_log(*argv, **kwargs):
            res = func(*argv, **kwargs)
            try:
                userid = request.values.get('userid')
                tmp = json.loads(res.data)
                msg = tmp['msg']
            except:
                return res

            if tmp["code"] == ErrorCode.SUCCESS:
                operation_result = "SUCCESS"
                msg = ""
            else:
                operation_result = "FAILED"

            client_ip = request.headers.get('X-Forwarded-For', '')

            insert_data = {
                "operator": userid,
                "operator_ip": client_ip,
                "operation_object": operation_object,
                "operation_action": operation_action,
                "operation_date": time_helper.get_datetime_str(),
                "operation_result": operation_result,
                "extra_data": msg
            }
            OperationService().insert_operation(insert_data)
            return res

        return insert_log

    return _add_operation


def add_operation_area(operation_object, operation_action):
    def _add_operation(func):
        @wraps(func)
        def insert_log(*argv, **kwargs):
            user = user_service.get_user()
            res = func(*argv, **kwargs)
            area_data = ""
            try:
                tmp = json.loads(res.data)
                if operation_action == OperationAction.ADD:  # 新增区域
                    name = request.values.get('name')
                    manager = request.values.get('manager')
                    parent_id = request.values.get('parent_id')
                    area_data += "name:" + name + "," + "manager:" + manager + "," + "parent_id:" + parent_id + ";"
                elif operation_action == OperationAction.ALTER:  # 修改区域
                    name = request.values.get('name')
                    manager = request.values.get('manager')
                    area_id = json.dumps(kwargs['area_id'])
                    area_data += "name:" + name + "," + "manager:" + manager + "," + "area_id:" + area_id + ";"
                elif operation_action == OperationAction.DELETE:  # 删除区域
                    area_ids = request.values.get('area_ids')
                    area_data += "area_ids:" + area_ids + ";"
                else:
                    pass
            except:
                return res

            if tmp["code"] == ErrorCode.SUCCESS:
                operation_result = "SUCCESS"
            elif tmp["code"] == ErrorCode.SUCCESS_PART:
                operation_result = "SUCCESS_PART"
            else:
                operation_result = "FAILED"
                try:
                    area_data += " ErrorMsg:" + tmp["msg"]
                except:
                    pass

            client_ip = request.headers.get('X-Forwarded-For', '')
            insert_data = {
                "operator": user["user_id"],
                "operator_ip": client_ip,
                "operation_object": operation_object,
                "operation_action": operation_action,
                "operation_date": time_helper.get_datetime_str(),
                "operation_result": operation_result,
                "extra_data": "" + area_data
            }
            OperationService().insert_operation(insert_data)
            return res

        return insert_log

    return _add_operation


def add_operation_datacenter(operation_object, operation_action):
    def _add_operation(func):
        @wraps(func)
        def insert_log(*argv, **kwargs):
            user = user_service.get_user()
            res = func(*argv, **kwargs)
            datacenter_data = ""
            try:
                tmp = json.loads(res.data)
                if operation_action == OperationAction.ADD:  # 新增机房
                    area_id = json.dumps(kwargs['area_id'])
                    name = request.values.get('name')
                    address = request.values.get('address')
                    description = request.values.get('description')
                    dc_type = request.values.get('dc_type')
                    province = request.values.get('province')
                    datacenter_data += "name:" + name + "," + "area_id:" + area_id + "," + "dc_type:" + dc_type + "," \
                                       + "province:" + province + "," + "address:" + address + "," \
                                       + "description:" + description + ";"
                elif operation_action == OperationAction.ALTER:  # 修改机房
                    datacenter_id = json.dumps(kwargs['datacenter_id'])
                    name = request.values.get('name')
                    province = request.values.get('province')
                    address = request.values.get('address')
                    description = request.values.get('description')
                    datacenter_data += "name:" + name + "," + "datacenter_id:" + datacenter_id + ","  \
                                       + "province:" + province + "," + "address:" + address + "," \
                                       + "description:" + description + ";"
                elif operation_action == OperationAction.DELETE:  # 删除机房
                    datacenter_ids = request.values.get('datacenter_ids')
                    datacenter_data += "datacenter_ids:" + datacenter_ids + ";"
                else:
                    pass
            except:
                return res

            if tmp["code"] == ErrorCode.SUCCESS:
                operation_result = "SUCCESS"
            elif tmp["code"] == ErrorCode.SUCCESS_PART:
                operation_result = "SUCCESS_PART"
            else:
                operation_result = "FAILED"
                try:
                    datacenter_data += " ErrorMsg:" + tmp["msg"]
                except:
                    pass

            client_ip = request.headers.get('X-Forwarded-For', '')
            insert_data = {
                "operator": user["user_id"],
                "operator_ip": client_ip,
                "operation_object": operation_object,
                "operation_action": operation_action,
                "operation_date": time_helper.get_datetime_str(),
                "operation_result": operation_result,
                "extra_data": "" + datacenter_data
            }
            OperationService().insert_operation(insert_data)
            return res

        return insert_log

    return _add_operation


def add_operation_netarea(operation_object, operation_action):
    def _add_operation(func):
        @wraps(func)
        def insert_log(*argv, **kwargs):
            user = user_service.get_user()
            res = func(*argv, **kwargs)
            netarea_data = ""
            try:
                tmp = json.loads(res.data)
                if operation_action == OperationAction.ADD:  # 新增网络区域
                    datacenter_id = request.values.get('datacenter_id')
                    name = request.values.get('name')
                    netarea_data += "name:" + name + "," + "datacenter_id:" + datacenter_id + ";"
                elif operation_action == OperationAction.ALTER:  # 修改网络区域
                    name = request.values.get('name')
                    net_area_id = json.dumps(kwargs['net_area_id'])
                    netarea_data += "name:" + name + "," + "net_area_id:" + net_area_id + ";"
                elif operation_action == OperationAction.DELETE:  # 删除网络区域
                    net_area_ids = request.values.get('net_area_ids')
                    netarea_data += "net_area_ids:" + net_area_ids + ";"
                else:
                    pass
            except:
                return res

            if tmp["code"] == ErrorCode.SUCCESS:
                operation_result = "SUCCESS"
            elif tmp["code"] == ErrorCode.SUCCESS_PART:
                operation_result = "SUCCESS_PART"
            else:
                operation_result = "FAILED"
                try:
                    netarea_data += " ErrorMsg:" + tmp["msg"]
                except:
                    pass

            client_ip = request.headers.get('X-Forwarded-For', '')
            insert_data = {
                "operator": user["user_id"],
                "operator_ip": client_ip,
                "operation_object": operation_object,
                "operation_action": operation_action,
                "operation_date": time_helper.get_datetime_str(),
                "operation_result": operation_result,
                "extra_data": "" + netarea_data
            }
            OperationService().insert_operation(insert_data)
            return res

        return insert_log

    return _add_operation


def add_operation_hostpool(operation_object, operation_action):
    def _add_operation(func):
        @wraps(func)
        def insert_log(*argv, **kwargs):
            user = user_service.get_user()
            res = func(*argv, **kwargs)
            hostpool_data = ""
            try:
                tmp = json.loads(res.data)
                if operation_action == OperationAction.ADD:  # 新增集群
                    net_area_id = json.dumps(kwargs['net_area_id'])
                    least_host_num = request.values.get('least_host_num')
                    name = request.values.get('name')
                    hostpool_data += "name:" + name + "," + "net_area_id:" + net_area_id + "," \
                                     + "least_host_num:" + least_host_num + ";"
                elif operation_action == OperationAction.ALTER:  # 修改集群
                    name = request.values.get('name')
                    least_host_num = request.values.get('least_host_num')
                    hostpool_id = json.dumps(kwargs['hostpool_id'])
                    hostpool_data += "name:" + name + "," + "hostpool_id:" + hostpool_id + "," \
                                     + "least_host_num:" + least_host_num + ";"
                elif operation_action == OperationAction.DELETE:  # 删除集群
                    hostpool_ids = request.values.get('hostpool_ids')
                    hostpool_data += "net_area_ids:" + hostpool_ids + ";"
                else:
                    pass
            except:
                return res

            if tmp["code"] == ErrorCode.SUCCESS:
                operation_result = "SUCCESS"
            elif tmp["code"] == ErrorCode.SUCCESS_PART:
                operation_result = "SUCCESS_PART"
            else:
                operation_result = "FAILED"
                try:
                    hostpool_data += " ErrorMsg:" + tmp["msg"]
                except:
                    pass

            client_ip = request.headers.get('X-Forwarded-For', '')
            insert_data = {
                "operator": user["user_id"],
                "operator_ip": client_ip,
                "operation_object": operation_object,
                "operation_action": operation_action,
                "operation_date": time_helper.get_datetime_str(),
                "operation_result": operation_result,
                "extra_data": "" + hostpool_data
            }
            OperationService().insert_operation(insert_data)
            return res

        return insert_log

    return _add_operation


def add_operation_vm(operation_object, operation_action):
    def _add_operation(func):
        @wraps(func)
        def insert_log(*argv, **kwargs):
            user = user_service.get_user()
            res = func(*argv, **kwargs)
            instance_data = ""
            try:
                tmp = json.loads(res.data)
                # 根据不同action拼接extra_data
                if request.values.get('instance_ids'):  # 删除VM、开机、关机
                    try:
                        # instance_ids = json.dumps(request.values.get('instance_ids'))
                        ins_ids = request.values.get('instance_ids')
                        ins_ids_list = ins_ids.split(',')
                        for _ins_id in ins_ids_list:
                            _ins_data = ins_s.InstanceService().get_instance_info(_ins_id)
                            instance_data += "name:" + _ins_data['name'] + "," + "uuid:" + _ins_data['uuid'] + "; "
                    except:
                        pass

                elif operation_action == OperationAction.ADD:  # 创建VM
                    try:
                        hostpool_id = json.dumps(kwargs['hostpool_id'])
                        image_name = request.values.get('image_name')
                        flavor_id = request.values.get('flavor_id')
                        count = request.values.get('count')
                        app_info = request.values.get('app_info')
                        group_id = request.values.get('group_id')
                        owner = request.values.get('owner')
                        instance_data += "hostpool_id:" + hostpool_id + "," + "image_name:" + image_name + "," \
                                         + "flavor_id:" + flavor_id + "," + "count:" + count + "," \
                                         + "app_info:" + app_info + "," + "group_id:" + group_id + "," \
                                         + "owner:" + owner + ";"
                    except:
                        pass

                elif operation_action == OperationAction.MIGRATE or operation_action == OperationAction.HOT_MIGRATE:  # 冷迁移、热迁移
                    try:
                        _ins_id = json.dumps(kwargs['instance_id'])
                        _host_id = json.dumps(kwargs['host_id'])
                        host_data_d = host_s.HostService().get_host_info(_host_id)
                        # host_data_s = ins_s.get_host_of_instance(_ins_id)  # str(host_data_s['name'])
                        _ins_data = ins_s.InstanceService().get_instance_info(_ins_id)
                        # TODO: add src_host
                        instance_data += "name:" + _ins_data['name'] + "," + "uuid:" + _ins_data['uuid'] + "," \
                                         + "src_host:" + "," + "dst_host:" + str(host_data_d['name']) + ";"
                    except:
                        pass

                elif operation_action == OperationAction.CLONE_CREATE:  # 克隆创建
                    try:
                        _ins_id = request.values.get('instance_id')
                        _ins_data = ins_s.InstanceService().get_instance_info(_ins_id)
                        instance_data += "name:" + _ins_data['name'] + "," + "uuid:" + _ins_data['uuid'] + "; "
                    except:
                        pass

                elif operation_action == OperationAction.ALTER:  # 修改VM配置
                    try:
                        _flavor_id = request.values.get('flavor_id')
                        # _disk_gb_list_req = request.values.get('disk_gb_list')
                        _app_info = request.values.get('app_info')
                        _owner = request.values.get('owner')
                        _group_id = request.values.get('group_id')
                        _net_conf_list_req = request.values.get('net_status_list')
                        # _ins_id = request.values.get('instance_id')
                        _ins_id = json.dumps(kwargs['instance_id'])
                        _extend_list_req = request.values.get('extend_list')
                        # _qemu_ga_update_req = request.values.get('qemu_ga_update')
                        _ins_data = ins_s.InstanceService().get_instance_info(_ins_id)
                        instance_data += "name:" + _ins_data['name'] + "," + "uuid:" + _ins_data['uuid'] + "," \
                                         + "owner:" + _owner + "," + "group_id:" + _group_id + "," \
                                         + "flavor_id:" + _flavor_id + "," + "app_info:" + _app_info + "," \
                                         + "extend_list:" + _extend_list_req + "," \
                                         + "net_conf_list_req:" + _net_conf_list_req + ";"
                    except:
                        pass

                elif kwargs:  # 克隆备份
                    try:
                        _ins_id = json.dumps(kwargs['instance_id'])
                        _ins_data = ins_s.InstanceService().get_instance_info(_ins_id)
                        instance_data += "name:" + _ins_data['name'] + "," + "uuid:" + _ins_data['uuid'] + "; "
                    except:
                        pass
                else:
                    pass
            except:
                return res

            if tmp["code"] == ErrorCode.SUCCESS:
                operation_result = "SUCCESS"
            elif tmp["code"] == ErrorCode.SUCCESS_PART:
                operation_result = "SUCCESS_PART"
            else:
                operation_result = "FAILED"
                try:
                    instance_data += " ErrorMsg:" + tmp["msg"]
                except:
                    pass

            client_ip = request.headers.get('X-Forwarded-For', '')
            insert_data = {
                "operator": user["user_id"],
                "operator_ip": client_ip,
                "operation_object": operation_object,
                "operation_action": operation_action,
                "operation_date": time_helper.get_datetime_str(),
                "operation_result": operation_result,
                "extra_data": "" + instance_data
            }
            OperationService().insert_operation(insert_data)
            return res

        return insert_log

    return _add_operation


def add_operation_ip(operation_object, operation_action):
    def _add_operation(func):
        @wraps(func)
        def insert_log(*argv, **kwargs):
            user = user_service.get_user()
            res = func(*argv, **kwargs)
            ip_data = ""
            try:
                tmp = json.loads(res.data)
                if operation_action == OperationAction.IP_APPLY:  # 申请IP
                    env = request.values.get('env')
                    net_area = request.values.get('net_area')
                    net_name = request.values.get('segment')
                    cluster_id = request.values.get('cluster_id')
                    opuser = request.values.get('opUser')
                    sys_code = request.values.get('sys_code')
                    datacenter = request.values.get('datacenter')
                    ip_data += "env:" + env + "," + "net_area:" + net_area + "," \
                               + "net_name:" + net_name + "," + "cluster_id:" + cluster_id + "," \
                               + "opuser:" + opuser + "," + "sys_code:" + sys_code + "," \
                               + "datacenter:" + datacenter + "," + "vip:" + tmp["data"]["vip"] + ";"
                elif request.values.get('ip_address'):  # 初始化IP、取消初始化IP、保留IP、取消保留IP
                    ip_address = request.values.get('ip_address')
                    ip_data += "ip_address:" + ip_address + ";"
                elif request.values.get('begin_ip') and request.values.get('end_ip'):  # 批量操作（4种）
                    begin_ip = request.values.get('begin_ip')
                    end_ip = request.values.get('end_ip')
                    ip_data += "begin_ip:" + begin_ip + "," + "end_ip:" + end_ip + ";"
                else:
                    pass
            except:
                return res

            if tmp["code"] == ErrorCode.SUCCESS:
                operation_result = "SUCCESS"
            elif tmp["code"] == ErrorCode.SUCCESS_PART:
                operation_result = "SUCCESS_PART"
            else:
                operation_result = "FAILED"
                try:
                    ip_data += " ErrorMsg:" + tmp["msg"]
                except:
                    pass

            client_ip = request.headers.get('X-Forwarded-For', '')
            insert_data = {
                "operator": user["user_id"],
                "operator_ip": client_ip,
                "operation_object": operation_object,
                "operation_action": operation_action,
                "operation_date": time_helper.get_datetime_str(),
                "operation_result": operation_result,
                "extra_data": "" + ip_data
            }
            OperationService().insert_operation(insert_data)
            return res

        return insert_log

    return _add_operation


def add_operation_host(operation_object, operation_action):
    def _add_operation(func):
        @wraps(func)
        def insert_log(*argv, **kwargs):
            user = user_service.get_user()
            res = func(*argv, **kwargs)
            host_data = ""
            try:
                tmp = json.loads(res.data)
                # 根据不同action拼接extra_data
                if operation_action == OperationAction.DELETE:  # 删除HOST
                    try:
                        all_host_id = request.values.get("host_id")
                        for _host_id in all_host_id.split(','):
                            _host_data = host_service.HostService().get_host_info(_host_id)
                            host_data += "name:" + _host_data['name'] + "," + "sn:" + _host_data['sn'] + "," + \
                                         "ipaddress:" + _host_data['ipaddress'] + "; "
                    except:
                        pass

                elif operation_action == OperationAction.ADD:  # 新增HOST
                    try:
                        name = request.values.get('name')
                        # 序列号
                        sn = request.values.get('sn')
                        ip_address = request.values.get('ip_address')
                        hold_mem_gb = request.values.get('hold_mem_gb')
                        manage_ip = request.values.get('manage_ip')
                        hostpool_id = json.dumps(kwargs['hostpool_id'])
                        host_data += "name:" + name + "," + "sn:" + sn + "," + "ip_address:" + ip_address + "," \
                                     + "manage_ip:" + manage_ip + "," + "hold_mem_gb:" + hold_mem_gb + "," \
                                     + "hostpool_id:" + str(hostpool_id) + ";"
                    except:
                        pass

                elif operation_action == OperationAction.OPERATE:  # 操作HOST
                    try:
                        all_host_id = request.values.get("host_id")
                        flag = request.values.get("flag")
                        if int(flag) == 0:
                            action = "开机"
                        elif int(flag) == 1:
                            action = "硬关机"
                        elif int(flag) == 2:
                            action = "软关机"
                        elif int(flag) == 3:
                            action = "硬重启"
                        elif int(flag) == 4:
                            action = "软重启"
                        else:
                            pass
                        for _host_id in all_host_id.split(','):
                            _host_data = host_service.HostService().get_host_info(_host_id)
                            host_data += "name:" + _host_data['name'] + "," + "sn:" + _host_data['sn'] + "," + \
                                         "ipaddress:" + _host_data['ipaddress'] + "," + "action:" + action + "; "
                    except:
                        pass
                elif operation_action == OperationAction.ALTER:  # 更新HOST
                    name = request.values.get('name')
                    ip_address = request.values.get('ip_address')
                    hold_mem_gb = request.values.get('hold_mem_gb')
                    manage_ip = request.values.get('manage_ip')
                    host_data += "name:" + name + "," + "ipaddress:" + ip_address + ","\
                                 + "manage_ip:" + manage_ip + "," + "hold_mem_gb:" + hold_mem_gb + "; "

                elif kwargs['host_id']:  # 锁定、维护
                    try:
                        flag = request.values.get("flag")
                        if operation_action == OperationAction.LOCK:
                            if int(flag) == 0:
                                action = "解除锁定"
                            elif int(flag) == 1:
                                action = "锁定"
                            else:
                                pass
                        elif operation_action == OperationAction.MAINTAIN:
                            if int(flag) == 0:
                                action = "结束维护"
                            elif int(flag) == 2:
                                action = "维护"
                            else:
                                pass
                        else:
                            pass
                        _host_id = json.dumps(kwargs['host_id'])
                        _host_data = host_service.HostService().get_host_info(_host_id)
                        host_data += "name:" + _host_data['name'] + "," + "sn:" + _host_data['sn'] + "," + \
                                     "ipaddress:" + _host_data['ipaddress'] + "," + "action:" + action + "; "
                    except:
                        pass

                else:
                    pass
            except:
                return res

            if tmp["code"] == ErrorCode.SUCCESS:
                operation_result = "SUCCESS"
            elif tmp["code"] == ErrorCode.SUCCESS_PART:
                operation_result = "SUCCESS_PART"
            else:
                operation_result = "FAILED"
                try:
                    host_data += " ErrorMsg:" + tmp["msg"]
                except:
                    pass

            client_ip = request.headers.get('X-Forwarded-For', '')
            insert_data = {
                "operator": user["user_id"],
                "operator_ip": client_ip,
                "operation_object": operation_object,
                "operation_action": operation_action,
                "operation_date": time_helper.get_datetime_str(),
                "operation_result": operation_result,
                "extra_data": "" + host_data
            }
            OperationService().insert_operation(insert_data)
            return res

        return insert_log

    return _add_operation


def add_operation_group(operation_object, operation_action):
    def _add_operation(func):
        @wraps(func)
        def insert_log(*argv, **kwargs):
            user = user_service.get_user()
            res = func(*argv, **kwargs)
            group_data = ""
            try:
                tmp = json.loads(res.data)
                # 根据不同action拼接extra_data
                if operation_action == OperationAction.ADD or operation_action == OperationAction.ALTER:  # 创建组、修改组信息
                    try:
                        name = request.values.get('name')
                        owner = request.values.get('owner')
                        p_cluster_id = request.values.get('p_cluster_id')
                        role_id = request.values.get('role_id')
                        cpu = request.values.get('cpu')
                        mem = request.values.get('mem')
                        disk = request.values.get('disk')
                        vm = request.values.get('vm')
                        area_str = request.values.get('area_str')
                        group_data += "group_name:" + name + "," + "owner:" + owner + "," + "p_cluster_id:" + p_cluster_id \
                                      + "," + "role_id:" + role_id + "," + "cpu:" + cpu + "," + "mem:" + mem + "," \
                                      + "disk:" + disk + "," + "vm:" + vm + "," + "area_str:" + area_str + "; "
                    except:
                        pass

                elif operation_action == OperationAction.REMOVE_USER:  # 移除用户
                    try:
                        user_id = request.values.get('user_id')
                        group_id = request.values.get('group_id')
                        group_data += "user_id:" + user_id + "," + "group_id:" + group_id + ";"
                    except:
                        pass

                elif operation_action == OperationAction.ADD_INSIDE_USER or \
                                operation_action == OperationAction.ADD_OUTER_USER:  # 新增域用户、新增外部用户
                    try:
                        user_id = request.values.get('user_id')
                        # group_name = request.values.get('group_name')
                        group_id = json.dumps(kwargs['group_id'])
                        group_data += "user_id:" + user_id + "," + "group_id:" + group_id + ";"
                    except:
                        pass

                elif operation_action == OperationAction.DELETE:  # 删除组
                    try:
                        group_data += "group_id:" + json.dumps(kwargs['group_id']) + "; "
                    except:
                        pass
                else:
                    pass
            except:
                return res

            if tmp["code"] == ErrorCode.SUCCESS:
                operation_result = "SUCCESS"
            elif tmp["code"] == ErrorCode.SUCCESS_PART:
                operation_result = "SUCCESS_PART"
            else:
                operation_result = "FAILED"
                try:
                    group_data += " ErrorMsg:" + tmp["msg"]
                except:
                    pass

            client_ip = request.headers.get('X-Forwarded-For', '')
            insert_data = {
                "operator": user["user_id"],
                "operator_ip": client_ip,
                "operation_object": operation_object,
                "operation_action": operation_action,
                "operation_date": time_helper.get_datetime_str(),
                "operation_result": operation_result,
                "extra_data": "" + group_data
            }
            OperationService().insert_operation(insert_data)
            return res

        return insert_log

    return _add_operation


def add_operation_other(operator, operation_object, operation_action, operation_result, extra_data=None):
    client_ip = request.headers.get('X-Forwarded-For', '')
    insert_data = {
        "operator": operator,
        "operator_ip": client_ip,
        "operation_object": operation_object,
        "operation_action": operation_action,
        "operation_date": datetime.datetime.now(),
        "operation_result": operation_result,
        "extra_data": extra_data
    }
    OperationService().insert_operation(insert_data)
    # ret = OperationService().insert_operation(insert_data)
    # if ret.get('row_num') <= 0:
    #     logging.error("add operation error, insert_data:%s", str(insert_data))
    #     return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    # return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


def add_operation_del_excel_vm(operation_object, operation_action):
    def _add_operation(func):
        @wraps(func)
        def insert_log(*argv, **kwargs):
            user = user_service.get_user()
            res = func(*argv, **kwargs)
            instance_data = ""
            try:
                tmp = json.loads(res.data)
                instance_data += (';').join(Global_define().get_value('vm_list'))
            except:
                return res

            if tmp["code"] == ErrorCode.SUCCESS:
                operation_result = "SUCCESS"
            elif tmp["code"] == ErrorCode.SUCCESS_PART:
                operation_result = "SUCCESS_PART"
            else:
                operation_result = "FAILED"
                try:
                    instance_data += " ErrorMsg:" + tmp["msg"]
                except:
                    pass

            client_ip = request.headers.get('X-Forwarded-For', '')
            insert_data = {
                "operator": user["user_id"],
                "operator_ip": client_ip,
                "operation_object": operation_object,
                "operation_action": operation_action,
                "operation_date": time_helper.get_datetime_str(),
                "operation_result": operation_result,
                "extra_data": "" + instance_data
            }
            OperationService().insert_operation(insert_data)
            return res

        return insert_log

    return _add_operation

