# coding=utf8
'''
    虚拟机操作
'''


from service.s_instance import instance_service as ins_s, instance_action_service as ins_a_s, \
    instance_group_service as ins_g_s, instance_ip_service as ins_ip_s
from service.s_host import host_schedule_service as host_s_s, host_service as host_s
from service.s_flavor import flavor_service as fla_s
from service.s_group import group_service as group_s
from service.s_instance import v2v_instance_service as v2v_ins_s
from service.s_ip.segment_service import SegmentService as ip_segment_s
from service.s_ip import ip_service
from service.s_user.user_service import current_user_group_ids, get_user, current_user_groups
from lib.vrtManager import instanceManager as vmManager
from lib.vrtManager.util import randomMAC
import logging
import json_helper
from model.const_define import ErrorCode, VMStatus, DataCenterType, CentOS_Version, InstaceActions, ActionStatus, \
    OperationObject, OperationAction, NetCardStatus, InstanceNicType
from flask import request
from common_data_struct import base_define, flavor_init_info, group_info
from helper.time_helper import get_datetime_str
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
from service.s_operation.operation_service import add_operation_vm
from config.default import INSTANCE_NETCARD_NUMS


class ConfigureInitInfoResp(base_define.Base):
    def __init__(self):
        self.c_instance_name = None
        self.c_flavor_id = None
        self.c_app_info = None
        self.c_group_id = None
        self.c_owner = None
        self.c_system = None
        self.flavors = []
        self.groups = []
        self.c_net = []
        self.c_ips = []


@login_required
def configure_init(instance_id):
    '''
        修改配置时获取初始数据
    :param instance_id:
    :return:
    '''
    if not instance_id:
        logging.info('no instance id when get configure info')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="参数错误")

    resp = ConfigureInitInfoResp()

    ins_data = ins_s.InstanceService().get_instance_info(instance_id)

    host_ip = ins_s.get_hostip_of_instance(instance_id)
    if not ins_data or not host_ip:
        logging.info('instance %s data is no exist in db when get configure info', instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    resp.c_instance_name = ins_data['name']
    resp.c_app_info = ins_data['app_info']
    resp.c_owner = ins_data['owner']
    ins_status = ins_data['status']
    if ins_status != VMStatus.STARTUP and ins_status != VMStatus.SHUTDOWN:
        logging.error('instance status %s is invalid when get instance configure init info', ins_status)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='只能在开机或关机状态下修改配置')

    if ins_data['create_source'] == '0':
        ins_images_data = ins_s.get_images_of_instance(instance_id)

        if ins_images_data:
            resp.c_system = ins_images_data[0]['system']
    else:
        ins_images_data = v2v_ins_s.V2VInstanceService().get_v2v_instance_info(instance_id)
        if ins_images_data:
            resp.c_system = ins_images_data['os_type']

    """
    ins_disks_data = ins_s.get_disks_of_instance(instance_id)
    if not ins_disks_data:
        logging.error('instance %s has no disk info when change instance configure', instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    # 关机状态、windows系统都不能修改数据盘
    if ins_status != VMStatus.SHUTDOWN and resp.c_system == 'linux':
        for _disk in ins_disks_data:
            _disk_info = {
                'size_gb': _disk['size_gb'],
                'mount_point': _disk['mount_point']
            }
            resp.c_disk_gb_list.append(_disk_info)
    """

    ins_flavor_data = ins_s.get_flavor_of_instance(instance_id)
    if not ins_flavor_data:
        logging.error('instance %s has no flavor info when change instance configure', instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    resp.c_flavor_id = ins_flavor_data['flavor_id']

    # flavor信息
    flavors_nums, flavors_data = fla_s.FlavorService().get_all_flavors()
    for _flavor in flavors_data:
        # 系统盘容量不能修改
        if _flavor['root_disk_gb'] == ins_flavor_data['root_disk_gb']:
            # 开机状态不能修改内存
            if ins_status == VMStatus.STARTUP:
                if _flavor['memory_mb'] == ins_flavor_data['memory_mb']:
                    _flavor_info = flavor_init_info.FlavorInitInfo().init_from_db(_flavor)
                    resp.flavors.append(_flavor_info)
            else:
                _flavor_info = flavor_init_info.FlavorInitInfo().init_from_db(_flavor)
                resp.flavors.append(_flavor_info)

    ins_group_data = ins_s.get_group_of_instance(instance_id)
    if ins_group_data:
        resp.c_group_id = ins_group_data['group_id']

    # user_group_ids_list = current_user_group_ids()
    # # 超级管理员组
    # if 1 in user_group_ids_list:
    #     is_super_group = True
    # else:
    #     is_super_group = False

    # group信息
    user_groups = current_user_groups()
    user_group_ids_list = []
    is_super_group = False
    for _groups in user_groups:
        user_group_ids_list.append(_groups['id'])
        # 超级管理员组
        if _groups['name'] == "supergroup":
            is_super_group = True

    # group信息
    groups_params = {
        'WHERE_AND': {
            '=': {
                'dc_type': ins_group_data['dc_type'],
                'isdeleted': '0'
            }
        },
    }
    groups_nums, groups_data = group_s.GroupService().query_data(**groups_params)
    for _group in groups_data:
        # 管理员组的成员可以显示所有组，而非管理员组的只显示当前用户所在应用组
        if not is_super_group and _group['id'] not in user_group_ids_list:
            continue

        _group_info = {
            'group_id': _group['id'],
            'group_name': _group['name']
        }
        resp.groups.append(_group_info)

    # 连接libvirtd查询虚拟机网卡状态信息
    _net_online = []
    _net_offline = []
    _libvirt_net_ret, _libvirt_net_info = vmManager.libvirt_get_netcard_state(host_ip, ins_data['name'])
    if _libvirt_net_ret != 0:
        _nic_status = False
    else:
        _nic_status = True
        for _p_libvirt_net_info in _libvirt_net_info:
            if _p_libvirt_net_info['state'] == NetCardStatus.UP:
                _net_online.append(_p_libvirt_net_info['mac'])
            else:
                _net_offline.append(_p_libvirt_net_info['mac'])

    # 虚拟机网卡信息返回前端
    _db_net_card_data = ins_s.get_net_info_of_instance(instance_id)
    if _db_net_card_data:
        for _p_db_net_card_data in _db_net_card_data:
            if not _nic_status:
                _p_ins_nic_status = ''
            else:
                if _p_db_net_card_data['mac'] in _net_online:
                    _p_ins_nic_status = '1'
                elif _p_db_net_card_data['mac'] in _net_offline:
                    _p_ins_nic_status = '0'
                else:
                    _p_ins_nic_status = '2'
            if not _p_db_net_card_data['segment_type']:
                _ip_type = '-1'
            else:
                _ip_type = _p_db_net_card_data['segment_type']
            _i_net_info = {
                'ip_addr': _p_db_net_card_data['ip_address'],
                'vlan': _p_db_net_card_data['vlan'],
                'mac_addr': _p_db_net_card_data['mac'],
                'nic_status': _p_ins_nic_status,
                'ip_type': _ip_type,
                'nic_type': _p_db_net_card_data['nic_type']
            }
            resp.c_net.append(_i_net_info)

    # 获取虚拟机所在网络区域下所有ip信息
    resp.c_ips = []
    ins_netarea_info = ins_s.get_netarea_of_instance(instance_id)
    ins_datacenter_info = ins_s.get_datacenter_of_instance(instance_id)
    if ins_datacenter_info and ins_datacenter_info['dc_type']:
        if ins_netarea_info and ins_netarea_info['id']:
            ip_segment_num, ip_segment_datas = ip_segment_s().get_segment_datas_in_net_area(ins_netarea_info['id'])
            if ip_segment_num > 0:
                # 获取可用ip
                ips_available = ip_service.get_all_available_ips(ip_segment_datas, ins_datacenter_info['dc_type'])
                if len(ips_available) > 0:
                    ip_list = []
                    for ip_info in ips_available:
                        ip_params = {
                            "value": ip_info['ip_address'],
                            "vlan": ip_info['vlan'],
                            "ip_type": ip_info['ip_type']
                        }
                        ip_list.append(ip_params)
                    resp.c_ips = ip_list

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp.to_json())


@login_required
@add_operation_vm(OperationObject.VM, OperationAction.ALTER)
def instance_configure(instance_id):
    '''
        虚机修改配置
        规则：
            热修改（开机状态）：cpu disk 加
            冷修改（关机状态）：cpu mem 加减  disk 加
    :param instance_id:
    :return:
    '''
    n_flavor_id = request.values.get('flavor_id')
    n_app_info = request.values.get('app_info')
    n_owner = request.values.get('owner')
    n_group_id = request.values.get('group_id')
    n_net_conf_list_req = request.values.get('net_status_list')

    # start
    n_extend_list_req = request.values.get('extend_list')
    n_qemu_ga_update_req = request.values.get('qemu_ga_update')
    c_system = ''
    c_version = None
    # end

    if not instance_id or not n_flavor_id or not n_group_id:
        logging.error('params is invalid when change instance configure')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    ins_data = ins_s.InstanceService().get_instance_info(instance_id)

    ###################################add 2017/09/29#############################3
    uuid = ins_data['uuid']
    user_id = get_user()['user_id']
    request_id = ins_s.generate_req_id()

    if not ins_data:
        logging.error('the instance %s is not exist in db when change instance configure', instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    # --------------------edit 2017/11/13-----------------------
    if ins_data['create_source'] == '0':
        ins_images_data = ins_s.get_images_of_instance(instance_id)

        if ins_images_data:
            c_system = ins_images_data[0]['system']
    else:
        ins_images_data = v2v_ins_s.V2VInstanceService().get_v2v_instance_info(instance_id)
        if ins_images_data:
            c_system = ins_images_data['os_type']

    ins_status = ins_data['status']

    # 获取虚拟机所在物理机信息
    host_data = ins_s.get_host_of_instance(instance_id)
    ins_datacenter_info = ins_s.get_datacenter_of_instance(instance_id)
    if not host_data or not ins_datacenter_info:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="无法获取虚拟机所在物理机信息、机房信息")

    ins_data['dc_type'] = ins_datacenter_info['dc_type']

    # 新flavor信息
    n_flavor_data = fla_s.FlavorService().get_flavor_info(n_flavor_id)
    if not n_flavor_data:
        logging.error('flavor %s is invalid in db when change instance configure', n_flavor_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='新的配置数据有误，无法修改配置')

    # 虚机现有flavor信息
    c_flavor_data = ins_s.get_flavor_of_instance(instance_id)
    if not c_flavor_data:
        logging.error('instance %s flavor is invalid in db when change instance configure', instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    c_group_data = ins_s.get_group_of_instance(instance_id)
    if c_group_data and int(c_group_data['group_id']) != int(n_group_id):
        # 检查新应用组的配额
        is_group_enough, req_msg = _check_change_group_quota(n_group_id, n_flavor_data, c_flavor_data)
        if not is_group_enough:
            logging.error('new group %s quota is not enough to change new flavor', n_group_id)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=req_msg)

    params = {}

    if json_helper.loads(n_extend_list_req):

        # 检查当前应用组的配额
        is_group_enough, req_msg = _check_change_group_quota(n_group_id, n_flavor_data, c_flavor_data,
                                                             json_helper.loads(n_extend_list_req))
        if not is_group_enough:
            logging.error('new group %s quota is not enough to change new flavor', n_group_id)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=req_msg)

        # 检查物理机当前使用率情况是否满足扩容
        is_host_available, ret_msg = __check_host_capacity(host_data, n_flavor_data, c_flavor_data
                                                           , json_helper.loads(n_extend_list_req))
        if not is_host_available:
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_msg)

        vmname = ins_data['name']
        uuid = ''
        host_ip = ''
        n_extend_list_req = json_helper.loads(n_extend_list_req)
        try:
            uuid = ins_data['uuid']
            host_ip = ins_s.get_hostip_of_instance(instance_id)
        except:
            pass

        connect_instance = vmManager.libvirt_get_connect(host_ip, conn_type='instance', vmname=ins_data['name'])
        if not connect_instance:
            pass
        # 添加扩容开始action
        ins_a_s.update_instance_status(VMStatus.CONFIGURE_ING, instance_id)
        ins_a_s.add_disk_extend_action_to_database(uuid, request_id, user_id,
                                                   InstaceActions.INSTANCE_DISK_EXTEND, ActionStatus.START, 'start')
        # 满足扩容条件
        if n_qemu_ga_update_req:
            if c_system.strip() == 'linux':
                flag, msg = connect_instance.exec_qemu_command(
                    "cat /proc/self/mounts | grep -w / | grep -v rootfs | awk '{print $3}'")
                if not flag:
                    c_version = None
                c_version = CentOS_Version.CentOS_6 if msg.strip() == 'ext4' else CentOS_Version.CentOS_7
                flag, result = ins_a_s.extend_mount_size(n_extend_list_req, host_ip, vmname, uuid, c_version, instance_id)
            elif c_system.strip() == 'windows':
                flag, result = ins_a_s.extend_dev_size(n_extend_list_req, host_ip, vmname, uuid, instance_id)
            else:
                flag = False
            if flag:
                msg = "扩容成功"
                ins_a_s.update_disk_action_to_database(request_id, InstaceActions.INSTANCE_DISK_EXTEND,
                                                       ActionStatus.SUCCSESS, msg)
                ins_a_s.update_instance_status(VMStatus.STARTUP, instance_id)
            else:
                msg = "扩容失败,{}".format(result)
                ins_a_s.update_disk_action_to_database(request_id, InstaceActions.INSTANCE_DISK_EXTEND,
                                                       ActionStatus.FAILD, msg)
                ins_a_s.update_instance_status(VMStatus.STARTUP, instance_id)
                return json_helper.format_api_resp(code=ErrorCode.ALL_FAIL, msg=msg)
        else :
            # 非linux系统，关机状态，qemu-guest-agent没有更新成功
            msg = "非linux系统，扩容失败"
            ins_a_s.update_disk_action_to_database(request_id, InstaceActions.INSTANCE_DISK_EXTEND, ActionStatus.FAILD,
                                                   msg)
            ins_a_s.update_instance_status(VMStatus.STARTUP, instance_id)
            return json_helper.format_api_resp(code=ErrorCode.ALL_FAIL, msg=msg)
    else:
        pass

    if c_flavor_data['vcpu'] != n_flavor_data['vcpu'] or c_flavor_data['memory_mb'] != n_flavor_data['memory_mb']:

        # 检查当前应用组的配额
        is_group_enough, req_msg = _check_change_group_quota(n_group_id, n_flavor_data, c_flavor_data)
        if not is_group_enough:
            logging.error('new group %s quota is not enough to change new flavor', n_group_id)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=req_msg)

        # 检查物理机当前使用率情况是否满足扩容
        is_host_available, ret_msg = __check_host_capacity(host_data, n_flavor_data, c_flavor_data)
        if not is_host_available:
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_msg)

        # 关机状态
        if ins_status == VMStatus.SHUTDOWN:
            pass
        elif ins_status == VMStatus.STARTUP:
            # 开机状态
            # cpu只能增
            if c_flavor_data['vcpu'] > n_flavor_data['vcpu']:
                logging.error('vcpu only be increase in startup status, now vcpu %s > new vcpu %s',
                              c_flavor_data['vcpu'], n_flavor_data['vcpu'])
                ins_a_s.update_instance_status(VMStatus.STARTUP, instance_id)
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='开机状态下，CPU数量只能增加不能减少')

            # 内存不能修改
            if c_flavor_data['memory_mb'] != n_flavor_data['memory_mb']:
                logging.error('memory only no allow be change in startup status, now mem %s, new mem %s',
                              c_flavor_data['memory_mb'], n_flavor_data['memory_mb'])
                ins_a_s.update_instance_status(VMStatus.STARTUP, instance_id)
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='开机状态下，不能修改内存容量')
        else:
            logging.error('instance status %s is invalid when change instance configure', ins_status)
            ins_a_s.update_instance_status(VMStatus.STARTUP, instance_id)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='只能在开机或关机状态下修改配置')

    if n_flavor_data['vcpu'] == c_flavor_data['vcpu']:
        pass
    else:
        params['new_vcpu'] = n_flavor_data['vcpu']
        params['old_vcpu'] = c_flavor_data['vcpu']

    new_mem = n_flavor_data['memory_mb']
    old_mem = c_flavor_data['memory_mb']

    if new_mem == old_mem:
        pass
    else:
        # 检查内存是否超分
        if not _check_mem_allocation(instance_id, new_mem, old_mem):
            logging.error('instance %s mem has over allocation, new mem %s, old mem %s', instance_id, new_mem, old_mem)
            ins_a_s.update_instance_status(VMStatus.STARTUP, instance_id)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='物理内存不能超分')
        params['new_mem'] = new_mem
        params['old_mem'] = old_mem

    # 检查网络配置是否需要修改
    n_net_conf_list = json_helper.loads(n_net_conf_list_req)
    if n_net_conf_list:
        params['net_status_list'] = n_net_conf_list

    # 没有一个指标可以修改
    if not params:
        logging.error('vcpu, mem, disk no one can change when change instance configure')
    else:
        host_ip = ins_s.get_hostip_of_instance(ins_data['id'])
        if not host_ip:
            logging.error('instance %s has no host ip when change instance configure', ins_data['id'])
            ins_a_s.update_instance_status(VMStatus.STARTUP, instance_id)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

        ret_flavor = ins_a_s.change_instance_configure(host_ip, ins_data, c_flavor_data['flavor_id'], n_flavor_id,
                                                       ins_status, **params)
        if not ret_flavor:
            ins_a_s.update_instance_status(VMStatus.STARTUP, instance_id)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    update_data_i = {
        'app_info': n_app_info,
        'owner': n_owner,
        'updated_at': get_datetime_str()
    }
    where_data_i = {
        'id': instance_id
    }
    ret_i = ins_s.InstanceService().update_instance_info(update_data_i, where_data_i)
    # if ret_i != 1:
    #     logging.error('update instance info error when configure, update_data:%s, where_data:%s',
    #                   update_data_i, where_data_i)
    #     return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    update_data_g = {
        'group_id': n_group_id,
        'updated_at': get_datetime_str()
    }
    where_data_g = {
        'instance_id': instance_id
    }
    ret_g = ins_g_s.InstanceGroupService().update_instance_group_info(update_data_g, where_data_g)
    # if ret_g != 1:
    #     logging.error('update group info error when configure, update_data:%s, where_data:%s',
    #                   update_data_g, where_data_g)
    #     return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    # if 'disk_gb_list' in params:
    #    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, msg='硬盘扩容任务发送成功')

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, msg='修改配置成功')



@login_required
def extend_disk(instance_id):
    """
      扩展磁盘接口
    :param instance_id:
    :return:
    """
    c_system = ''
    c_version = None
    qemu_ga_update = False
    mount_point_list = []

    if not instance_id:
        logging.info('no instance id when get configure info')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="参数错误")

    ins_data = ins_s.InstanceService().get_instance_info(instance_id)
    uuid = ins_data['uuid']
    user_id = get_user()['user_id']
    request_id = ins_s.generate_req_id()

    host_ip = ins_s.get_hostip_of_instance(instance_id)

    if not ins_data or not host_ip:
        data_params = {'mount_point_list': mount_point_list, "qemu_ga_update": qemu_ga_update}
        logging.info('instance %s data is no exist in db when get configure info', instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, data=data_params, msg='数据库查询错误')

    if ins_data['create_source'] == '0':
        ins_images_data = ins_s.get_images_of_instance(instance_id)

        if ins_images_data:
            c_system = ins_images_data[0]['system']
            c_version = ins_images_data[0]['version']
    else:
        ins_images_data = v2v_ins_s.V2VInstanceService().get_v2v_instance_info(instance_id)
        if ins_images_data:
            c_system = ins_images_data['os_type']
            if ins_images_data['os_version'] and '6.6' in ins_images_data['os_version']:
                c_version = '6.6'
            elif ins_images_data['os_version'] and '7.2' in ins_images_data['os_version']:
                c_version = '7.2'

    # 更新qemu-guest-agent action到数据库，zitong wang 29th,9,2017
    ins_a_s.add_disk_display_action_to_database(uuid, request_id, user_id, InstaceActions.INSTANCE_DISK_INFO_DISPLAY,
                                        ActionStatus.START, 'start')

    # 更新qemu-guest-agent,获取所有挂载点的信息,add by zitongwang in 21th,9,2017
    if c_system == "linux" and c_version:
        c_version = CentOS_Version.CentOS_7 if c_version >= '7.0' else CentOS_Version.CentOS_6
        ins_a_s.add_disk_display_action_to_database(uuid, request_id, user_id,
                                            InstaceActions.INSTANCE_UPDATE_QEMU_AGENT, ActionStatus.START, 'start')
        # 更新qemu-ga版本
        vmManager.update_qemu_ga_instance(c_version,host_ip,ins_data['name'])
        connect_instance = vmManager.libvirt_get_connect(host_ip, conn_type='instance', vmname=ins_data['name'])
        if not connect_instance:
            data_params = {'mount_point_list': mount_point_list, "qemu_ga_update": qemu_ga_update}
            msg = "libvirt连接建立失败，无法使用libvirt管理虚拟机"
            ins_a_s.add_disk_display_action_to_database(uuid, request_id, ActionStatus.FAILD,
                                                InstaceActions.INSTANCE_LIBVIRT_ERROR, msg)
            return json_helper.format_api_resp(code=ErrorCode.ALL_FAIL, data=data_params, msg=msg)

        # 重新建立连接判断是否更新成功
        flag, msg = connect_instance.test_update_command()
        qemu_ga_update = flag
        if flag:
            # 更新action数据库状态：更新成功
            _message = "qemu_agent update successfully"
            ins_a_s.update_disk_action_to_database(request_id, InstaceActions.INSTANCE_UPDATE_QEMU_AGENT,
                                                   ActionStatus.SUCCSESS, _message)

            # 针对v2v机器，pvs显示的LV名称有问题
            connect_instance.exec_qemu_command("pvscan")

            # 获得所有挂载点信息
            command = "lsblk -r | awk '{print $7}' | awk NF | grep  '^/' | grep -v '^/boot'"
            flag, msg = connect_instance.exec_qemu_command(command)
            mount_point = msg.splitlines()
            # 获取挂载点文件系统，大小，类型，挂载点信息
            command = "lsblk -r | awk '{print $1" + "\\\" " + "\\\"" + "$4" + "\\\" " + "\\\"" + "$6" + "\\\" " + "\\\"" + "$7}'"
            flag, msg = connect_instance.exec_qemu_command(command)
            parts_info = msg.split('\n')
            parts_info.pop()

            mount_point_list = []
            mount_list = []
            for mount in mount_point:
                disk_info = {}

                mount_data = filter(lambda x: x.split(' ')[-1] == mount, parts_info)
                data = mount_data[0].split(' ')
                disk_info['mount_point'] = data[-1]

                # 存在数据就返回
                if disk_info['mount_point'] in mount_list:
                    continue
                else:
                    mount_list.append(disk_info['mount_point'])
                disk_info['mount_partition_name'] = data[0]
                disk_info['mount_point_size'] = float(data[1][0:-1]) if data[1][-1].endswith('G') else float(
                    data[1][0:-1]) / 1024
                disk_info['mount_partition_type'] = data[2]
                command = "df -P '%s'| awk 'NR==2 {print $5}'" % mount
                flag, msg = connect_instance.exec_qemu_command(command)
                disk_info['mount_point_use'] = msg.strip()

                mount_point_list.append(disk_info)
            data_params = {'mount_point_list': mount_point_list, "qemu_ga_update": qemu_ga_update}

            _message = "linux os disk information display successfully"
            ins_a_s.update_disk_action_to_database(request_id, InstaceActions.INSTANCE_DISK_INFO_DISPLAY,
                                                   ActionStatus.SUCCSESS, _message)
            return json_helper.format_api_resp(code=ErrorCode.SUCCESS,
                                               data=data_params)
        else:
            # 更新qmeu-ga失败
            _message = "qemu_agent update failed"
            ins_a_s.update_disk_action_to_database(request_id, InstaceActions.INSTANCE_UPDATE_QEMU_AGENT,
                                                   ActionStatus.FAILD, _message)
            data_params = {'mount_point_list': mount_point_list, "qemu_ga_update": qemu_ga_update}
            return json_helper.format_api_resp(code=ErrorCode.ALL_FAIL,
                                               data=data_params, msg='qemu update fail')
    elif c_system == "windows":
        connect_instance = vmManager.libvirt_get_connect(host_ip, conn_type='instance', vmname=ins_data['name'])
        disk_info = connect_instance.get_configure_disk_device(uuid)
        storage_instance = vmManager.libvirt_get_connect(host_ip, conn_type='storage', vmname=ins_data['name'],
                                                         poolname=uuid)
        mount_point_list = []
        for x in disk_info:
            d = {}
            block_info = storage_instance.get_disk_size(x['image'])
            d.setdefault('mount_point', x['dev'])
            d.setdefault('mount_point_size', '%.1f' % (float(block_info[0]) / 1073741824))
            d.setdefault('mount_point_use', '%.2f' % (float(block_info[1]) / block_info[0] * 100))
            d.setdefault('mount_partition_name', "")
            d.setdefault('mount_partition_type', "")
            mount_point_list.append(d)

        qemu_ga_update = True
        data_params = {'mount_point_list': mount_point_list, "qemu_ga_update": qemu_ga_update}
        _message = "disk information display successfully"
        ins_a_s.update_disk_action_to_database(request_id, InstaceActions.INSTANCE_DISK_INFO_DISPLAY,
                                               ActionStatus.SUCCSESS, _message)
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS,
                                           data=data_params, msg=_message)
    else:
        data_params = {'mount_point_list': mount_point_list, "qemu_ga_update": qemu_ga_update}
        _message = "os type unknown, please call kvm administrators"
        ins_a_s.update_disk_action_to_database(request_id, InstaceActions.INSTANCE_DISK_INFO_DISPLAY,
                                               ActionStatus.FAILD, _message)
        return json_helper.format_api_resp(code=ErrorCode.ALL_FAIL,
                                           data=data_params, msg=_message)


@login_required
def instance_add_netcard(instance_id):
    '''
        kvm平台虚拟机添加网卡接口
    :param instance_id:
    :return:
    '''
    # 判断指定虚拟机是否存在
    if not instance_id:
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="instance_id为空，添加网卡失败")

    ins_data = ins_s.InstanceService().get_instance_info(instance_id)
    if not ins_data:
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="无法找到待添加网卡虚拟机")

    # 查询指定虚拟机网卡数量，目前不能超过3块
    instance_net_card = ins_s.get_net_info_of_instance(instance_id)
    if instance_net_card:
        if len(instance_net_card) >= INSTANCE_NETCARD_NUMS:
            return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="虚拟机网卡数量不能超过%s张" % str(INSTANCE_NETCARD_NUMS))

    # 往instance_ip表添加记录
    mac = randomMAC()
    instance_ip_data = {
        'instance_id': instance_id,
        'mac': mac,
        'type': InstanceNicType.NORMAL_NETWORK_NIC,
        'isdeleted': '0',
        'created_at': get_datetime_str()
    }
    ret_add = ins_ip_s.InstanceIPService().add_instance_ip_info(instance_ip_data)
    if ret_add.get('row_num') <= 0:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="虚拟机网卡创建失败")

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, msg="虚拟机网卡创建成功")


def _check_mem_allocation(instance_id, new_mem, old_mem):
    '''
        物理机内存不超分（包括已经分配出去的内存）
    :param instance_id:
    :param new_mem:
    :param old_mem:
    :return:
    '''
    host_data = ins_s.get_host_of_instance(instance_id)
    if not host_data:
        return False

    host_all_data = host_s_s.get_host_used(host_data)
    if host_all_data:
        # 保留内存GB -> MB
        hold_mem = host_data['hold_mem_gb'] * 1024
        mem_size = host_all_data['mem_size']
        allocate_mem = host_s.get_vm_assign_mem_of_host(host_data['id'])
        # 增量 < 总量 - 已分配(flavor的mem) - 保留
        if long(new_mem) - long(old_mem) < long(mem_size) - long(allocate_mem) - long(hold_mem):
            return True
    return False


def _check_change_group_quota(n_group_id, n_flavor, c_flavor,extend_list=None):
    '''
        检查修改新应用组后的配额是否足够
    :param n_group_id:
    :param n_flavor:
    :param c_flavor:
    :return:
    '''
    quota_used = group_s.get_group_quota_used(n_group_id)
    if not quota_used:
        logging.error('group %s has no quota used info when check change group quota', n_group_id)
        return False

    group_num, group_data = group_s.GroupService().get_group_info(n_group_id)
    if group_num < 1:
        logging.error('no group %s info when check change group quota', n_group_id)
        return False

    # 新应用组的总配额情况
    all_cpu_g = group_data[0]['cpu']
    all_mem_gb_g = group_data[0]['mem']
    all_vm_g = group_data[0]['vm']
    all_disk_g = group_data[0]['disk']
    # 新应用组的配额使用情况
    used_cpu_g = quota_used['all_vcpu']
    used_mem_mb_g = quota_used['all_mem_mb']
    used_vm_g = quota_used['instance_num']
    used_disk_g = quota_used['all_disk_gb']



    # 新配额信息
    n_cpu = n_flavor['vcpu']
    n_mem_mb = n_flavor['memory_mb']
    # 旧配额信息
    c_cpu = c_flavor['vcpu']
    c_mem_mb = c_flavor['memory_mb']

    if int(used_vm_g) + 1 > int(all_vm_g):
        logging.error('group %s: vm used %s + 1 > all num %s', n_group_id, used_vm_g, all_vm_g)
        return False, '新应用组的实例数目配额不足，无法修改应用组'

    if int(used_cpu_g) - int(c_cpu) + int(n_cpu) > int(all_cpu_g):
        logging.error('group %s: cpu used %s - old cpu %s + new cpu %s > all cpu %s',
                      n_group_id, used_cpu_g, c_cpu, n_cpu, all_cpu_g)
        return False, '新应用组的CPU配额不足，无法修改应用组'

    all_mem_mb_g = int(all_mem_gb_g) * 1024
    if int(used_mem_mb_g) - int(c_mem_mb) + int(n_mem_mb) > all_mem_mb_g:
        logging.error('group %s: mem used %s - old mem %s + new mem %s > all mem %s',
                      n_group_id, used_mem_mb_g, c_mem_mb, n_mem_mb, all_mem_mb_g)
        return False, '新应用组的内存配额不足，无法修改应用组'

    if extend_list:
        sum_extend_size = sum([int(i['mount_extend_size']) for i in extend_list])
    else:
        sum_extend_size = 0
    if int(used_disk_g) + sum_extend_size > int(all_disk_g):
        logging.error('group %s: disk used %s + extend_size %s > all disk_size %s',
                      used_disk_g, sum_extend_size, all_disk_g)
        return False, '新应用组的磁盘空间配额不足，无法修改应用组'

    return True, None


def __check_host_capacity(host_data, n_flavor, c_flavor, extend_list=None):
    '''
        检查物理机容量是否满足扩容
    :param host_data:
    :param n_flavor:
    :param c_flavor:
    :param extend_list:
    :return:
    '''

    # 新配额信息
    n_cpu = int(n_flavor['vcpu'])
    n_mem_mb = int(n_flavor['memory_mb'])
    # 旧配额信息
    c_cpu = int(c_flavor['vcpu'])
    c_mem_mb = int(c_flavor['memory_mb'])

    # 虚拟机配额增量赋值
    increase_cpu = 0
    increase_mem_mb = 0

    if n_cpu > c_cpu:
        increase_cpu = n_cpu - c_cpu

    if n_mem_mb > c_mem_mb:
        increase_mem_mb = n_mem_mb - c_mem_mb

    if extend_list:
        increase_disk_gb = sum([int(i['mount_extend_size']) for i in extend_list])
    else:
        increase_disk_gb = 0

    # VM分配给HOST看是否满足迁移
    vm = {
        "vcpu": increase_cpu,
        "mem_MB": increase_mem_mb,
        "disk_GB": increase_disk_gb,
    }

    # 获取物理机所在资源池可用物理机数量
    all_hosts_nums, all_hosts_data = host_s.HostService().get_available_hosts_of_hostpool(host_data["hostpool_id"])
    if all_hosts_nums < 1:
        return False, '物理机资源不足，无法满足虚拟机配置修改'
    host_datas = []
    host_datas.append(host_data)
    host_after_match, ret_msg = host_s_s.configuare_filter_host(host_datas, vm, all_hosts_nums, max_disk=2000)
    if len(host_after_match) == 0:
        return False, ret_msg

    return True, ret_msg
