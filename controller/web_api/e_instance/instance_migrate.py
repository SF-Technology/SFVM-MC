# coding=utf8
'''
    虚拟机操作
'''


from service.s_host import host_service as host_s, host_schedule_service as host_s_s
from service.s_instance import instance_service as ins_s
from service.s_instance import instance_host_service as ins_h_s
from service.s_instance import instance_migrate_service as ins_m_s
from service.s_instance import instance_group_service as ins_g_s
import logging
import json_helper
from model.const_define import ErrorCode, VMStatus, VMTypeStatus, HostTypeStatus, MigrateStatus, \
    OperationObject, OperationAction
from common_data_struct import base_define
from flask import request
from lib.mq.kafka_client import send_async_msg
from helper.time_helper import get_datetime_str
from service.s_user.user_service import get_user
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
from config import KAFKA_TOPIC_NAME
from service.s_operation.operation_service import add_operation_vm


class MigrateHostsResp(base_define.Base):

    def __init__(self):
        self.instance_name = None
        self.instance_ip = None
        self.instance_status = None
        self.instance_cpu = None
        self.instance_mem = None
        self.instance_disk = None
        self.host_list = []


@login_required
def migrate_init(instance_id):
    '''
        获取迁移时满足条件的目标主机
    :param instance_id:
    :return:
    '''

    def _check_mem(host, instance_mem):
        '''
            检测host是否有足够的内存资源
        :param host:
        :param instance_mem:
        :return:
        '''
        # host已分配内存
        assign_mem = host_s.get_vm_assign_mem_of_host(host['host_id'])
        # 已分配 + 预分配 > 总大小
        if assign_mem + int(instance_mem) >= int(host['mem_size']):
            logging.error('host %s assign mem %s + instance mem %s > mem size %s',
                          host['host_id'], assign_mem, instance_mem, host['mem_size'])
            return False
        return True

    if not instance_id:
        logging.info('no instance id when get migrate hosts')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="参数错误")

    resp = MigrateHostsResp()

    ins_data = ins_s.InstanceService().get_instance_info(instance_id)
    if ins_data:
        resp.instance_name = ins_data['name']
        resp.instance_status = ins_data['status']

    ins_flavor_data = ins_s.get_flavor_of_instance(instance_id)
    if ins_flavor_data:
        resp.instance_cpu = ins_flavor_data['vcpu']
        resp.instance_mem = ins_flavor_data['memory_mb']
        resp.instance_disk = ins_flavor_data['root_disk_gb']

    ins_ip_data = ins_s.get_ip_of_instance(instance_id)
    if ins_ip_data:
        resp.instance_ip = ins_ip_data['ip_address']

    ins_host = ins_s.get_host_of_instance(instance_id)
    if not ins_host:
        logging.error('instance %s of host is not exist in db when get migrate host', instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="无法获取虚拟机所在物理机信息")

    ins_group = ins_g_s.InstanceGroupService().get_instance_group_info(instance_id)
    if not ins_group:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="无法获取虚拟机所在应用组信息")

    data_disk_status, data_disk_size = ins_s.get_data_disk_size_of_instance(instance_id)
    if not data_disk_status:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="无法获取被迁移虚拟机磁盘配置信息")
    instance_disk_size = int(ins_flavor_data['root_disk_gb']) + int(data_disk_size)

    # 同一集群
    all_hosts_nums, all_hosts_data = host_s.HostService().get_hosts_of_hostpool(ins_host['hostpool_id'])
    if all_hosts_nums <= 0:
        logging.error('no host in hostpool %s when get migrate host', ins_host['hostpool_id'])
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data={}, msg="集群下没有一台可用物理机")

    # 过滤host
    hosts_after_filter = host_s_s.migrate_filter_hosts(all_hosts_data, int(all_hosts_nums))
    if len(hosts_after_filter) == 0:
        logging.info('no available host when get migrate host')
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data={}, msg="集群内其他物理机cpu、内存使用率超过阀值，暂时不能迁移")

    # VM分配给HOST看是否满足迁移
    vm = {
        "vcpu": ins_flavor_data['vcpu'],
        "mem_MB": ins_flavor_data['memory_mb'],
        "disk_GB": instance_disk_size,
    }
    host_after_match = host_s_s.migrate_match_hosts(hosts_after_filter, vm, ins_group['group_id'], least_host_num=1,
                                                    max_disk=2000)
    if len(host_after_match) == 0:
        logging.info('no available host when get migrate host')
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data={}, msg="集群内其他物理机cpu、内存资源不足或者应用互斥，暂时不能迁移")

    ins_flavor = ins_s.get_flavor_of_instance(instance_id)
    if not ins_flavor:
        logging.error('instance %s flavor is not exist in db when get migrate host', instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="kvm平台未找到指定配置规格")

    for _host in host_after_match:
        # 去除本身host / 内存分配足够
        if _host['host_id'] != ins_host['id']:
            _h = {
                'host_id': _host['host_id'],
                'host_name': _host['name'],
                'current_cpu_used': _host['current_cpu_used'],
                'current_mem_used': _host['current_mem_used'],
                'free_disk_space': int(_host["disk_size"]) * (100 - int(_host["current_disk_used"])) / 100
            }
            resp.host_list.append(_h)

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp.to_json())


@login_required
@add_operation_vm(OperationObject.VM, OperationAction.MIGRATE)
def instance_migrate(instance_id, host_id):
    '''
        虚拟机迁移
    :param instance_id:
    :param host_id:
    :return:
    '''
    speed_limit = request.values.get('speed_limit')
    if not instance_id or not host_id or not speed_limit or int(speed_limit) < 0:
        logging.info('the params is invalid when migrate instance')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="参数错误")

    host_data_s = ins_s.get_host_of_instance(instance_id)
    if not host_data_s:
        logging.error('instance %s of host is not exist in db when migrate instance', instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    host_data_d = host_s.HostService().get_host_info(host_id)
    if not host_data_d:
        logging.error('target host %s is not exist in db when migrate instance', instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    if host_data_d['typestatus'] == HostTypeStatus.LOCK or host_data_d['typestatus'] == HostTypeStatus.MAINTAIN:
        logging.error('target host %s is in invalid status %s when migrate instance', host_id, host_data_d['typestatus'])
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='不能迁移到锁定或维护的主机上')

    ins_group = ins_g_s.InstanceGroupService().get_instance_group_info(instance_id)
    if not ins_group:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="无法获取虚拟机所在应用组信息")

    ins_flavor_data = ins_s.get_flavor_of_instance(instance_id)
    if not ins_flavor_data:
        logging.error('hot migrate can not get instance %s flavor info' % str(instance_id))
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='无法获取被迁移虚拟机的基础配置信息')

    data_disk_status, data_disk_size = ins_s.get_data_disk_size_of_instance(instance_id)
    if not data_disk_status:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="无法获取被迁移虚拟机磁盘配置信息")
    instance_disk_size = int(ins_flavor_data['root_disk_gb']) + int(data_disk_size)

    # 获取物理机所在资源池可用物理机数量
    all_hosts_nums, all_hosts_data = host_s.HostService().get_available_hosts_of_hostpool(host_data_d["hostpool_id"])
    if all_hosts_nums < 1:
        return False, '集群物理机资源不足，无法满足虚拟机迁移'

    host_data_d_before_match = []
    host_data_d_before_match.append(host_data_d)

    # 过滤host
    # 这里不核对host的cpu型号
    hosts_after_filter = host_s_s.migrate_filter_hosts(host_data_d_before_match, int(all_hosts_nums))
    if len(hosts_after_filter) == 0:
        logging.info('no available host when get migrate host')
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="集群内其他物理机cpu、内存使用率超过阀值，暂时不能迁移")

    # VM分配给HOST看是否满足迁移
    vm = {
        "vcpu": ins_flavor_data['vcpu'],
        "mem_MB": ins_flavor_data['memory_mb'],
        "disk_GB": instance_disk_size,
    }
    host_after_match = host_s_s.migrate_match_hosts(hosts_after_filter, vm, ins_group['group_id'], least_host_num=1,
                                                    max_disk=2000)
    if len(host_after_match) == 0:
        logging.info('no available host when get migrate host')
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="集群内其他物理机cpu、内存资源不足或者应用互斥，暂时不能迁移")

    # 不能本身
    if host_data_s['id'] == host_id:
        logging.error('no allow migrate to the same host %s', host_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="不能迁移到原主机上")

    ins_data_s = ins_s.InstanceService().get_instance_info(instance_id)
    if not ins_data_s:
        logging.error('instance %s is not exist in db when migrate instance')
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    # 排除非法状态
    if ins_data_s['status'] != VMStatus.SHUTDOWN or ins_data_s['typestatus'] != VMTypeStatus.NORMAL:
        logging.error('instance status %s, typestatus %s is invalid when migrate instance',
                      ins_data_s['status'], ins_data_s['typestatus'])
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='只能在关机状态下执行冷迁移')

    # 检测目标主机是否有迁入VM
    if not _check_has_migrate(host_id):
        logging.error('dest host %s has other migrating instance when migrate instance', host_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='目标主机现有正在迁入的虚机，不能迁移到该主机')

    update_data = {
       'status': VMStatus.COLD_MIGRATE,
       'updated_at': get_datetime_str()
    }
    where_data = {
        'id': instance_id
    }
    ret = ins_s.InstanceService().update_instance_info(update_data, where_data)
    if ret != 1:
        logging.error('update instance status error when cold migrate, update_data:%s, where_data:%s',
                      update_data, where_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    # 先修改成目标host是为了后续创建VM时，可继续使用host资源分配过滤策略
    update_data_h = {
        'host_id': host_id,
        'host_name': host_data_d['name'],
        'updated_at': get_datetime_str()
    }
    where_data_h = {
        'isdeleted': '0',
        'instance_id': instance_id
    }
    ret_h = ins_h_s.InstanceHostService().update_instance_host_info(update_data_h, where_data_h)
    if ret_h != 1:
        logging.error('update instance host info error when cold migrate, update_data:%s, where_data:%s',
                      update_data_h, where_data_h)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    insert_data = {
        'instance_id': instance_id,
        'src_host_id': host_data_s['id'],
        'dst_host_id': host_id,
        'migrate_status': MigrateStatus.DOING,
        'created_at': get_datetime_str()
    }
    ret_m = ins_m_s.InstanceMigrateService().add_instance_migrate_info(insert_data)
    if ret_m.get('row_num') <= 0:
        logging.error('add instance migrate info error when cold migrate, insert_data:%s', insert_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    # 发送异步消息到队列
    data = {
        "routing_key": "INSTANCE.COLDMIGRATE",
        "send_time": get_datetime_str(),
        "data": {
            "request_id": ins_s.generate_req_id(),
            "user_id": get_user()['user_id'],
            "migrate_tab_id": ret_m.get('last_id'),
            "speed_limit": speed_limit,
            "ins_data_s": {
                "id": ins_data_s['id'],
                "uuid": ins_data_s['uuid'],
                "name": ins_data_s['name']
            },
            "host_data_d": {
                "id": host_data_d['id'],
                "name": host_data_d['name'],
                "ipaddress": host_data_d['ipaddress']
            },
            "host_data_s": {
                "id": host_data_s['id'],
                "name": host_data_s['name'],
                "ipaddress": host_data_s['ipaddress'],
                "sn": host_data_s['sn']
            }
        }
    }
    # todo:这里有可能发送不成功
    ret_kafka = send_async_msg(KAFKA_TOPIC_NAME, data)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


def _check_has_migrate(host_id):
    '''
        检查目的物理机当前是否有正在迁入的VM
    :param host_id:
    :return:
    '''
    params = {
        'WHERE_AND': {
            '=': {
                'dst_host_id': host_id,
                'migrate_status': '0'
            }
        },
    }
    migrate_num, migrate_host = ins_m_s.InstanceMigrateService().query_data(**params)
    if migrate_num > 0:
        return False
    return True













