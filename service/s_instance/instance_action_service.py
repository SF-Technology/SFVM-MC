# coding=utf8
'''
    虚拟机操作服务
'''


from vrtManager import instanceManager as vmManager
from lib.mq.kafka_client import send_async_msg
from lib.shell.ansibleCmdV2 import ansible_remote_backup_instance_xml, ansible_check_instance_shutdown_time
from service.s_instance import instance_service as ins_s, instance_flavor_service as ins_f_s, \
    instance_group_service as ins_g_s, instance_host_service as ins_h_s, instance_image_service as ins_i_s, \
    instance_ip_service as ins_ip_s, instance_disk_service as ins_d_s
from service.s_ip import ip_service as ip_s
from service.s_ip import segment_match as segment_m
from service.s_ip import segment_service as segment_s
from service.s_user.user_service import get_user
from service.s_instance_action import instance_action
from model.const_define import VMStatus, InstaceActions, VMLibvirtStatus, IPStatus, ActionStatus, \
    CentOS_Version, ErrorCode, DataCenterType, NetCardStatus, NetCardType
import logging
from helper.time_helper import get_datetime_str, get_datetime_str_link
from config.default import DIR_INSTANCE_XML_BACKUP
from config import KAFKA_TOPIC_NAME
from helper import time_helper,json_helper



def shutdown_instance(instance, flag):
    host_ip = ins_s.get_hostip_of_instance(instance['id'])
    if not host_ip:
        return False, None

    if flag == 1:
        # 关机
        ret_lib = vmManager.libvirt_instance_shutdown(host_ip, instance['name'])
    else:
        # 强制关机
        ret_lib = vmManager.libvirt_instance_force_shutdown(host_ip, instance['name'])
    if not ret_lib:
        logging.error('libvirt shutdown instance error, host_ip:%s, instance name:%s', host_ip, instance['name'])
        return False, '该虚拟机已无法管理，请联系管理员'

    update_data = {
        'status': VMStatus.SHUTDOWN_ING,
        'shut_down_time':get_datetime_str()
    }
    where_data = {
        'id': instance['id']
    }
    ret = ins_s.InstanceService().update_instance_info(update_data, where_data)
    if ret != 1:
        logging.info("update instance info error when shutdown instance, update_data:%s, where_data:%s",
                     update_data, where_data)
        return False, None

    # 添加任务信息
    insert_data = {
        'action': InstaceActions.INSTANCE_SHUTDOWN,
        'instance_uuid': instance['uuid'],
        'request_id': ins_s.generate_req_id(),
        'user_id': get_user()['user_id'],
        'start_time': get_datetime_str()
    }
    ret_action = instance_action.InstanceActionsServices().add_instance_action_info(insert_data)
    if ret_action.get('row_num') < 1:
        logging.error('add instance shutdown action info error, insert_data:%s', insert_data)
        return False, None

    return True, None


def startup_instance(instance):
    host_ip = ins_s.get_hostip_of_instance(instance['id'])
    if not host_ip:
        return False

    ret_lib = vmManager.libvirt_instance_startup(host_ip, instance['name'])
    if not ret_lib:
        logging.error('libvirt startup instance error, host_ip:%s, instance name:%s', host_ip, instance['name'])
        return False

    update_data = {
        'status': VMStatus.STARTUP_ING
    }
    where_data = {
        'id': instance['id']
    }
    ret = ins_s.InstanceService().update_instance_info(update_data, where_data)
    if ret != 1:
        logging.info('update instance info error when startup instance, update_data:%s, where_data:%s',
                     update_data, where_data)
        return False

    # 添加任务信息
    insert_data = {
        'action': InstaceActions.INSTANCE_STARTUP,
        'instance_uuid': instance['uuid'],
        'request_id': ins_s.generate_req_id(),
        'user_id': get_user()['user_id'],
        'start_time': get_datetime_str()
    }
    ret_action = instance_action.InstanceActionsServices().add_instance_action_info(insert_data)
    if ret_action.get('row_num') < 1:
        logging.error('add instance startup action info error, insert_data:%s', insert_data)
        return False
    return True


def reboot_instance(instance, flag):
    host_ip = ins_s.get_hostip_of_instance(instance['id'])
    if not host_ip:
        return False

    if flag == 1:
        # 重启
        ret_lib = vmManager.libvirt_instance_reboot(host_ip, instance['name'])
    else:
        # 强制重启
        ret_lib = vmManager.libvirt_instance_force_reboot(host_ip, instance['name'])
    if not ret_lib:
        logging.error('libvirt reboot instance error, host_ip:%s, instance name:%s', host_ip, instance['name'])
        return False

    update_data = {
        'status': VMStatus.SHUTDOWN_ING
    }
    where_data = {
        'id': instance['id']
    }
    ret = ins_s.InstanceService().update_instance_info(update_data, where_data)
    if ret != 1:
        logging.info("update instance info error when reboot instance, update_data:%s, where_data:%s",
                     update_data, where_data)
        return False

    # 添加任务信息
    insert_data = {
        'action': InstaceActions.INSTANCE_REBOOT,
        'instance_uuid': instance['uuid'],
        'request_id': ins_s.generate_req_id(),
        'user_id': get_user()['user_id'],
        'start_time': get_datetime_str()
    }
    ret_action = instance_action.InstanceActionsServices().add_instance_action_info(insert_data)
    if ret_action.get('row_num') < 1:
        logging.error('add instance reboot action info error, insert_data:%s', insert_data)
        return False

    return True


def change_instance_configure(host_ip, instance, c_flavor_id, n_flavor_id, ins_status, **params):
    # 添加任务信息
    task_id = ins_s.generate_task_id()
    insert_data = {
        'action': InstaceActions.INSTANCE_CHANGE_CONFIGURE,
        'instance_uuid': instance['uuid'],
        'request_id': ins_s.generate_req_id(),
        'task_id': task_id,
        'user_id': get_user()['user_id'],
        'start_time': get_datetime_str()
    }
    ret_action = instance_action.InstanceActionsServices().add_instance_action_info(insert_data)
    if ret_action.get('row_num') < 1:
        logging.error('add instance change configure action info error, insert_data:%s', insert_data)
        return False

    # 关机状态
    if ins_status == VMStatus.SHUTDOWN:
        # 修改CPU
        if params.get('old_vcpu') != params.get('new_vcpu'):
            ret_cpu = vmManager.libvirt_instance_change_cpu(
                host_ip, instance['name'], params.get('old_vcpu'), params.get('new_vcpu'))
            if not ret_cpu:
                _msg = 'host ip %s change cpu error' % host_ip
                logging.error(_msg)
                _job_status = ActionStatus.FAILD
                _update_config_msg_to_db(task_id, _msg, _job_status)
                return False
        else:
            logging.info('old vcpu %s = new vcpu in shutdown status, no need to change', params.get('old_vcpu'))

        # 修改MEM
        if params.get('old_mem') != params.get('new_mem'):
            ret_mem = vmManager.libvirt_instance_change_memory(
                host_ip, instance['name'], params.get('old_mem'), params.get('new_mem'))
            if not ret_mem:
                _msg = 'host ip %s change mem error' % host_ip
                logging.error(_msg)
                _job_status = ActionStatus.FAILD
                _update_config_msg_to_db(task_id, _msg, _job_status)
                return False
        else:
            logging.info('old mem %s = new mem in shutdown status, no need to change', params.get('old_mem'))
    elif ins_status == VMStatus.STARTUP:
        # 开机状态
        # 修改CPU
        if params.get('old_vcpu') != params.get('new_vcpu'):
            ret_cpu_a = vmManager.libvirt_instance_change_cpu_active(host_ip, instance['name'], params.get('new_vcpu'))
            if not ret_cpu_a:
                _msg = 'host ip %s change cpu active error' % host_ip
                logging.error(_msg)
                _job_status = ActionStatus.FAILD
                _update_config_msg_to_db(task_id, _msg, _job_status)
                return False
        else:
            logging.info('old vcpu %s = new vcpu in startup status, no need to change', params.get('old_vcpu'))

    else:
        _msg = 'instance status %s is invalid' % ins_status
        logging.error(_msg)
        _job_status = ActionStatus.FAILD
        _update_config_msg_to_db(task_id, _msg, _job_status)
        return False

    if int(c_flavor_id) != int(n_flavor_id):
        ret = ins_f_s.InstanceFlavorService().update_instance_flavor(n_flavor_id, instance['id'])
        if ret != 1:
            logging.info("update instance %s flavor %s error when change instance flavor", instance['id'], n_flavor_id)
            # 没有数据就新增
            insert_data = {
                'instance_id': instance['id'],
                'flavor_id': n_flavor_id,
                'created_at': get_datetime_str()
            }
            ins_f_s.InstanceFlavorService().add_instance_flavor_info(insert_data)

    # 连接libvirtd查询虚拟机网卡状态信息
    _net_online = []
    _net_offline = []
    vm_status = vmManager.libvirt_instance_status(host_ip, instance['name'])
    # 虚拟机开机状态才可以做网卡配置
    if vm_status == VMLibvirtStatus.STARTUP:
        _libvirt_net_ret, _libvirt_net_info = vmManager.libvirt_get_netcard_state(host_ip, instance['name'])
        if _libvirt_net_ret != 0:
            _msg = 'instance %s net information get failed because can not connect to libvirtd' % instance['name']
            _job_status = ActionStatus.FAILD
            _update_config_msg_to_db(task_id, _msg, _job_status)
            return False
        else:
            if len(_libvirt_net_info) == 0:
                pass
            else:
                for _p_libvirt_net_info in _libvirt_net_info:
                    if _p_libvirt_net_info['state'] == NetCardStatus.UP:
                        _net_online.append(_p_libvirt_net_info['mac'])
                    else:
                        _net_offline.append(_p_libvirt_net_info['mac'])

        # 修改网络配置
        _net_status_list = params.get('net_status_list')
        if params.get('net_status_list'):
            for _per_net_status_list in _net_status_list:
                if str(_per_net_status_list['nic_status']):
                    # 获取mac对应ip的vlan信息
                    net_info_ret = ins_s.get_net_info_of_instance_by_mac_addr(_per_net_status_list['mac_addr'])
                    if not net_info_ret:
                        _msg = 'can not get network vlan id from db when modify instance %s network' % instance['name']
                        _job_status = ActionStatus.FAILD
                        _update_config_msg_to_db(task_id, _msg, _job_status)
                        return False
                    if net_info_ret['ip_id'] and net_info_ret['ip_address'] and net_info_ret['vlan'] and \
                            net_info_ret['host_bridge_name']:
                        net_dev = net_info_ret['host_bridge_name'] + '.' + net_info_ret['vlan']
                        _xml_backup_dir = DIR_INSTANCE_XML_BACKUP
                        if _per_net_status_list['mac_addr'] in _net_online and str(_per_net_status_list['nic_status']) == '1':
                            pass
                        elif _per_net_status_list['mac_addr'] in _net_online and str(_per_net_status_list['nic_status']) == '0':
                            # 备份xml文件
                            instance_xml_backup_status, _msg = _instance_xml_dump(instance['name'], _xml_backup_dir, host_ip)
                            if not instance_xml_backup_status:
                                _job_status = ActionStatus.FAILD
                                _update_config_msg_to_db(task_id, _msg, _job_status)
                                return False

                            # 虚拟机网卡断开
                            net_down_status, _msg = _instance_net_offline(instance['name'],
                                                                          _per_net_status_list['mac_addr'], host_ip,
                                                                          net_dev)
                            if not net_down_status:
                                _job_status = ActionStatus.FAILD
                                _update_config_msg_to_db(task_id, _msg, _job_status)
                                return False
                        elif _per_net_status_list['mac_addr'] in _net_offline and str(_per_net_status_list['nic_status']) == '0':
                            pass
                        elif _per_net_status_list['mac_addr'] in _net_offline and str(_per_net_status_list['nic_status']) == '1':
                            # 虚拟机网卡连接
                            net_on_status, _msg = _instance_net_online(instance['name'],
                                                                       _per_net_status_list['mac_addr'], host_ip,
                                                                       net_dev)
                            if not net_on_status:
                                _job_status = ActionStatus.FAILD
                                _update_config_msg_to_db(task_id, _msg, _job_status)
                                return False
                if str(_per_net_status_list['ip_addr_new']):
                    # 获取虚拟机已有ip类型，新配置ip类型不能和已有重复
                    ip_type_list = []
                    ip_data_list = []
                    instance_all_ip_datas = ins_s.get_all_ip_of_instance(instance['id'])
                    if not instance_all_ip_datas:
                        _msg = 'can not get instance ip info from db when modify instance %s network' % instance[
                            'name']
                        _job_status = ActionStatus.FAILD
                        _update_config_msg_to_db(task_id, _msg, _job_status)
                        return False
                    for _instance_ip in instance_all_ip_datas:
                        ip_params = {
                            "ip": _instance_ip['ip_address'],
                            "type": _instance_ip['segment_type']
                        }
                        ip_type_list.append(_instance_ip['segment_type'])
                        ip_data_list.append(ip_params)

                    # 获取mac对应ip的vlan信息
                    net_info_ret = ins_s.get_net_info_of_instance_by_mac_addr(_per_net_status_list['mac_addr'])
                    if not net_info_ret:
                        _msg = 'can not get instance nic info from db when modify instance %s network' % instance['name']
                        _job_status = ActionStatus.FAILD
                        _update_config_msg_to_db(task_id, _msg, _job_status)
                        return False
                    if not _per_net_status_list['ip_addr']:
                        # 逻辑1：原先网卡没有ip
                        if _per_net_status_list['ip_type'] in ip_type_list:
                            _msg = '网卡配置ip：不能分配和已有相同类型ip'
                            _job_status = ActionStatus.FAILD
                            _update_config_msg_to_db(task_id, _msg, _job_status)
                            return False

                        if not _per_net_status_list['vlan_new']:
                            _msg = '网卡配置ip：前端传入后端vlan值为空'
                            _job_status = ActionStatus.FAILD
                            _update_config_msg_to_db(task_id, _msg, _job_status)
                            return False

                        # 判断要申请ip是否被分配了，如果是生产或容灾环境，需要判断其对应的容灾或生产ip是否为未使用状态
                        new_ip_status = ip_s.IPService().get_ip_by_ip_address(_per_net_status_list['ip_addr_new'])
                        new_ip_segment_data = segment_s.SegmentService().get_segment_info(new_ip_status['segment_id'])
                        if not new_ip_status or not new_ip_segment_data:
                            _msg = '网卡配置ip：无法获取数据库中ip信息或ip对应的网段信息'
                            _job_status = ActionStatus.FAILD
                            _update_config_msg_to_db(task_id, _msg, _job_status)
                            return False

                        if new_ip_status['status'] != IPStatus.UNUSED:
                            _msg = '网卡配置ip：新ip：%s已经被分配，请分配其他ip' % _per_net_status_list['ip_addr_new']
                            _job_status = ActionStatus.FAILD
                            _update_config_msg_to_db(task_id, _msg, _job_status)
                            return False

                        if int(instance['dc_type']) == DataCenterType.PRD:
                            segment_dr = segment_m.SegmentMatchService().get_segment_match_info_by_prd_segment_id(
                                new_ip_status['segment_id'])
                            if not segment_dr:
                                _msg = '网卡配置ip：无法获取数据库中生产网段与的容灾网段对应关系'
                                _job_status = ActionStatus.FAILD
                                _update_config_msg_to_db(task_id, _msg, _job_status)
                                return False
                            segment_dr_data = segment_s.SegmentService().get_segment_info(segment_dr['dr_segment_id'])
                            if not segment_dr_data:
                                _msg = '网卡配置ip：无法获取数据库中生产网段对应容灾网段信息'
                                _job_status = ActionStatus.FAILD
                                _update_config_msg_to_db(task_id, _msg, _job_status)
                                return False
                            # 拼凑虚拟机容灾IP
                            dr_ip = segment_dr_data['segment'].split('.')[0] + '.' + segment_dr_data['segment'].split('.')[1] + '.' + new_ip_status['ip_address'].split('.')[2] + '.' + new_ip_status['ip_address'].split('.')[3]
                            dr_ip_info = ip_s.IPService().get_ip_by_ip_address(dr_ip)
                            # 如果容灾IP是未使用中状态，可以使用
                            if dr_ip_info:
                                if dr_ip_info['status'] != IPStatus.UNUSED:
                                    _msg = '网卡配置ip：生产ip对应容灾ip非未使用状态'
                                    _job_status = ActionStatus.FAILD
                                    _update_config_msg_to_db(task_id, _msg, _job_status)
                                    return False
                            else:
                                _msg = '网卡配置ip：无法获取数据库中生产ip对应容灾ip信息'
                                _job_status = ActionStatus.FAILD
                                _update_config_msg_to_db(task_id, _msg, _job_status)
                                return False

                        elif int(instance['dc_type']) == DataCenterType.DR:
                            segment_prd = segment_m.SegmentMatchService().get_segment_match_info_by_dr_segment_id(
                                new_ip_status['segment_id'])
                            if not segment_prd:
                                _msg = '网卡配置ip步骤 4：无法获取数据库中生产网段与的容灾网段对应关系'
                                _job_status = ActionStatus.FAILD
                                _update_config_msg_to_db(task_id, _msg, _job_status)
                                return False
                            segment_prd_data = segment_s.SegmentService().get_segment_info(
                                segment_prd['prd_segment_id'])
                            if not segment_prd_data:
                                _msg = '网卡配置ip步骤 5：无法获取数据库中容灾网段对应生产网段信息'
                                _job_status = ActionStatus.FAILD
                                _update_config_msg_to_db(task_id, _msg, _job_status)
                                return False
                            # 拼凑虚拟机生产IP
                            prd_ip = segment_prd_data['segment'].split('.')[0] + '.' + segment_prd_data['segment'].split('.')[1] + '.' + new_ip_status['ip_address'].split('.')[2] + '.' + new_ip_status['ip_address'].split('.')[3]
                            prd_ip_info = ip_s.IPService().get_ip_by_ip_address(prd_ip)
                            # 如果生产环境ip是未使用中状态，可以使用
                            if prd_ip_info:
                                if prd_ip_info['status'] != IPStatus.UNUSED:
                                    _msg = '网卡配置ip：生产ip对应容灾ip非未使用状态'
                                    _job_status = ActionStatus.FAILD
                                    _update_config_msg_to_db(task_id, _msg, _job_status)
                                    return False
                            else:
                                _msg = '网卡配置ip：无法获取数据库中容灾ip对应生产ip信息'
                                _job_status = ActionStatus.FAILD
                                _update_config_msg_to_db(task_id, _msg, _job_status)
                                return False

                        # 将新ip置为已使用
                        _ip_change_db_status, _change_db_ip_msg = _change_db_ip_used(new_ip_status)
                        if not _ip_change_db_status:
                            _job_status = ActionStatus.FAILD
                            _update_config_msg_to_db(task_id, _change_db_ip_msg, _job_status)
                            return False

                        # 需要修改xml配置，同时做ip、网关修改注入
                        _per_net_status_list['netmask_new'] = _exchange_maskint(int(new_ip_status['netmask']))
                        _per_net_status_list['gateway_new'] = new_ip_status['gateway_ip']

                        dev_name = new_ip_segment_data['host_bridge_name'] + '.' + str(new_ip_segment_data['vlan'])
                        net_on_status, _msg = _instance_net_on(instance['name'], _per_net_status_list['mac_addr'],
                                                               host_ip, dev_name)
                        if not net_on_status:
                            _job_status = ActionStatus.FAILD
                            _update_config_msg_to_db(task_id, _msg, _job_status)
                            _change_db_ip_unused(new_ip_status)
                            return False

                        ret_status, ret_msg = _change_instance_network(host_ip, instance['name'],
                                                                       _per_net_status_list, vlan_new=True,
                                                                       net_card_new=True)
                        if ret_status:
                            db_ret_status, db_ret_msg = _instance_ip_configure_change_db(instance['id'],
                                                                                         _per_net_status_list,
                                                                                         instance['dc_type'])
                            if not db_ret_status:
                                _job_status = ActionStatus.FAILD
                                _update_config_msg_to_db(task_id, db_ret_msg, _job_status)
                                _change_db_ip_unused(new_ip_status)
                                return False

                            _job_status = ActionStatus.SUCCSESS
                            _update_config_msg_to_db(task_id, db_ret_msg, _job_status)
                        else:
                            _job_status = ActionStatus.FAILD
                            _update_config_msg_to_db(task_id, ret_msg, _job_status)
                            _change_db_ip_unused(new_ip_status)
                            return False
                    else:
                        ip_type_list = []
                        for _ip_data in ip_data_list:
                            if _ip_data['ip'] != _per_net_status_list['ip_addr']:
                                ip_type_list.append(_ip_data['type'])

                        if _per_net_status_list['ip_type'] in ip_type_list:
                            _msg = '网卡修改ip：不能分配和已有相同类型ip'
                            _job_status = ActionStatus.FAILD
                            _update_config_msg_to_db(task_id, _msg, _job_status)
                            return False

                        # todo:如果是主网网卡不能修改不同类型网段

                        # 判断要申请ip是否被分配了
                        new_ip_status = ip_s.IPService().get_ip_by_ip_address(_per_net_status_list['ip_addr_new'])
                        cur_ip_status = ip_s.IPService().get_ip_by_ip_address(_per_net_status_list['ip_addr'])
                        if not new_ip_status or not cur_ip_status:
                            _msg = '网卡修改ip：无法获取数据库中原有和新ip信息'
                            _job_status = ActionStatus.FAILD
                            _update_config_msg_to_db(task_id, _msg, _job_status)
                            return False

                        if new_ip_status['status'] != IPStatus.UNUSED:
                            _msg = '网卡修改ip：新ip：%s已经被分配，请分配其他ip' % _per_net_status_list['ip_addr_new']
                            _job_status = ActionStatus.FAILD
                            _update_config_msg_to_db(task_id, _msg, _job_status)
                            return False

                        if int(instance['dc_type']) == DataCenterType.PRD:
                            segment_dr = segment_m.SegmentMatchService().get_segment_match_info_by_prd_segment_id(
                                new_ip_status['segment_id'])
                            if not segment_dr:
                                _msg = '网卡修改ip：无法获取数据库中生产网段与的容灾网段对应关系'
                                _job_status = ActionStatus.FAILD
                                _update_config_msg_to_db(task_id, _msg, _job_status)
                                return False
                            segment_dr_data = segment_s.SegmentService().get_segment_info(segment_dr['dr_segment_id'])
                            if not segment_dr_data:
                                _msg = '网卡修改ip：无法获取数据库中生产网段对应容灾网段信息'
                                _job_status = ActionStatus.FAILD
                                _update_config_msg_to_db(task_id, _msg, _job_status)
                                return False
                            # 拼凑虚拟机容灾IP
                            dr_ip = segment_dr_data['segment'].split('.')[0] + '.' + segment_dr_data['segment'].split('.')[1] + '.' + new_ip_status['ip_address'].split('.')[2] + '.' + new_ip_status['ip_address'].split('.')[3]
                            dr_ip_info = ip_s.IPService().get_ip_by_ip_address(dr_ip)
                            # 如果容灾IP是未使用中状态，可以使用
                            if dr_ip_info:
                                if dr_ip_info['status'] != IPStatus.UNUSED:
                                    _msg = '网卡修改ip：生产ip对应容灾ip非未使用状态'
                                    _job_status = ActionStatus.FAILD
                                    _update_config_msg_to_db(task_id, _msg, _job_status)
                                    return False
                            else:
                                _msg = '网卡修改ip：无法获取数据库中生产ip对应容灾ip信息'
                                _job_status = ActionStatus.FAILD
                                _update_config_msg_to_db(task_id, _msg, _job_status)
                                return False

                        elif int(instance['dc_type']) == DataCenterType.DR:
                            segment_prd = segment_m.SegmentMatchService().get_segment_match_info_by_dr_segment_id(
                                new_ip_status['segment_id'])
                            if not segment_prd:
                                _msg = '网卡修改ip：无法获取数据库中生产网段与的容灾网段对应关系'
                                _job_status = ActionStatus.FAILD
                                _update_config_msg_to_db(task_id, _msg, _job_status)
                                return False
                            segment_prd_data = segment_s.SegmentService().get_segment_info(
                                segment_prd['prd_segment_id'])
                            if not segment_prd_data:
                                _msg = '网卡修改ip：无法获取数据库中容灾网段对应生产网段信息'
                                _job_status = ActionStatus.FAILD
                                _update_config_msg_to_db(task_id, _msg, _job_status)
                                return False
                            # 拼凑虚拟机生产IP
                            prd_ip = segment_prd_data['segment'].split('.')[0] + '.' + segment_prd_data['segment'].split('.')[1] + '.' + new_ip_status['ip_address'].split('.')[2] + '.' + new_ip_status['ip_address'].split('.')[3]
                            prd_ip_info = ip_s.IPService().get_ip_by_ip_address(prd_ip)
                            # 如果生产环境ip是未使用中状态，可以使用
                            if prd_ip_info:
                                if prd_ip_info['status'] != IPStatus.UNUSED:
                                    _msg = '网卡修改ip：生产ip对应容灾ip非未使用状态'
                                    _job_status = ActionStatus.FAILD
                                    _update_config_msg_to_db(task_id, _msg, _job_status)
                                    return False
                            else:
                                _msg = '网卡修改ip：无法获取数据库中容灾ip对应生产ip信息'
                                _job_status = ActionStatus.FAILD
                                _update_config_msg_to_db(task_id, _msg, _job_status)
                                return False

                        # 将新ip置为已使用
                        _ip_change_db_status, _change_db_ip_msg = _change_db_ip_used(new_ip_status)
                        if not _ip_change_db_status:
                            _job_status = ActionStatus.FAILD
                            _update_config_msg_to_db(task_id, _change_db_ip_msg, _job_status)
                            return False

                        if not _per_net_status_list['vlan'] or not _per_net_status_list['vlan_new']:
                            _msg = '网卡修改ip：前端传入后端vlan值为空'
                            _job_status = ActionStatus.FAILD
                            _update_config_msg_to_db(task_id, _msg, _job_status)
                            _change_db_ip_unused(new_ip_status)
                            return False

                        if new_ip_status['segment_id'] == cur_ip_status['segment_id']:
                            # 新ip网段和原有ip一样，不需要修改xml配置，只做ip修改注入
                            ret_status, ret_msg = _change_instance_network(host_ip, instance['name'], _per_net_status_list)
                            if ret_status:
                                db_ret_status, db_ret_msg = _instance_ip_configure_change_db(instance['id'], _per_net_status_list, instance['dc_type'])
                                if not db_ret_status:
                                    _job_status = ActionStatus.FAILD
                                    _update_config_msg_to_db(task_id, db_ret_msg, _job_status)
                                    _change_db_ip_unused(new_ip_status)
                                    return False

                                _job_status = ActionStatus.SUCCSESS
                                _update_config_msg_to_db(task_id, db_ret_msg, _job_status)
                            else:
                                _job_status = ActionStatus.FAILD
                                _update_config_msg_to_db(task_id, ret_msg, _job_status)
                                _change_db_ip_unused(new_ip_status)
                                return False
                        else:
                            # 新ip网段和原有ip不一样，需要修改xml配置，同时做ip、网关修改注入
                            _per_net_status_list['netmask_new'] = _exchange_maskint(int(new_ip_status['netmask']))
                            _per_net_status_list['gateway_new'] = new_ip_status['gateway_ip']
                            ret_status, ret_msg = _change_instance_network(host_ip, instance['name'], _per_net_status_list, vlan_new=True)
                            if ret_status:
                                db_ret_status, db_ret_msg = _instance_ip_configure_change_db(instance['id'], _per_net_status_list, instance['dc_type'])
                                if not db_ret_status:
                                    _job_status = ActionStatus.FAILD
                                    _update_config_msg_to_db(task_id, db_ret_msg, _job_status)
                                    _change_db_ip_unused(new_ip_status)
                                    return False

                                _job_status = ActionStatus.SUCCSESS
                                _update_config_msg_to_db(task_id, db_ret_msg, _job_status)
                            else:
                                _job_status = ActionStatus.FAILD
                                _update_config_msg_to_db(task_id, ret_msg, _job_status)
                                _change_db_ip_unused(new_ip_status)
                                return False

    _msg = 'instance %s cpu or mem configure successful' % instance['name']
    _job_status = ActionStatus.SUCCSESS
    _update_config_msg_to_db(task_id, _msg, _job_status)
    return True


def delete_instance(instance, instance_status):
    host_ip = ins_s.get_hostip_of_instance(instance['id'])
    ins_datacenter_info = ins_s.get_datacenter_of_instance(instance['id'])
    if not host_ip:
        return False

    instances = vmManager.libvirt_host_instances(host_ip)
    # 当对应host上没有VM或者VM不在该host上，也直接删除表数据
    if not instances or instance['name'] not in instances:
        logging.info('instance %s data in db, but not in libvirt instances, delete db data', instance['name'])
        # 处理所有与instance关联的表数据
        ret_db = _del_instance_data_db(instance['id'], ins_datacenter_info['dc_type'], instance_status)
        if not ret_db:
            logging.error('delete instance %s data in db error', instance['name'])
            return False
        return True

    vm_status = vmManager.libvirt_instance_status(host_ip, instance['name'])
    # 关机状态
    if vm_status != VMLibvirtStatus.SHUTDOWN:
        # 创建失败的vm就强制关机删除
        if vm_status == VMLibvirtStatus.STARTUP and (instance['status'] == VMStatus.CREATE_ERROR or instance['status'] == VMStatus.CLONE_CREATE_ERROR):
            # 强制关机
            ret_lib = vmManager.libvirt_instance_force_shutdown(host_ip, instance['name'])
            if not ret_lib:
                logging.error('delete instance and libvirt shutdown instance error, host_ip:%s, instance name:%s',
                              host_ip, instance['name'])
                return False
        else:
            logging.error('instance status %s is invalid when libvirt delete instance', vm_status)
            return False

    # 查看虚拟机是否关机超过一天
    # todo:后期要db管理关机时间
    ret_check = ansible_check_instance_shutdown_time(host_ip, instance['name'])
    if not ret_check:
        logging.error('instance shutdown time is not meet the need when libvirt delete instance')
        return False

    ret_lib = vmManager.libvirt_instance_delete(host_ip, instance)
    if not ret_lib:
        logging.error('libvirt delete instance error, host_ip:%s, instance name:%s', host_ip, instance['name'])
        return False

    # 处理所有与instance关联的表数据
    ret_db = _del_instance_data_db(instance['id'], ins_datacenter_info['dc_type'], instance_status)
    if not ret_db:
        logging.error('delete instance %s data in db error', instance['name'])
        return False
    return True


def extend_mount_size(mount_extend_list,host_ip,vmname,uuid,c_version, instance_id):
    """
    :param mount_extend_list:
    :param vname:
    :param uuid:
    :param c_system:
    :param c_version:
    :param connect_instance:
    :param storage_instance:
    :return:
    """
    data_list = []
    # 分别是实例连接和存储连接
    connect_instance = vmManager.libvirt_get_connect(host_ip, conn_type='instance', vmname=vmname)
    storage_instance = vmManager.libvirt_get_connect(host_ip, conn_type='storage', vmname=vmname,poolname=uuid)

    user_id = get_user()['user_id']
    request_id = ins_s.generate_req_id()

    if not connect_instance or not storage_instance:
        msg = "connect或者storage连接失败，无法使用libvirt管理虚拟机"
        add_disk_display_action_to_database(uuid, request_id, user_id,
                                    InstaceActions.INSTANCE_LIBVIRT_ERROR, ActionStatus.FAILD, msg)
        return False,json_helper.write({'code':ActionStatus.FAILD,'msg':msg,'data':data_list})


    # 同时处理多个任务
    for _mount_extend in mount_extend_list:
        extend_size = int(_mount_extend['mount_extend_size'])
        extend_type = _mount_extend['mount_partition_type']
        extend_mount = _mount_extend['mount_point']
        disk_devices = connect_instance.get_disk_device()

        # 如果是挂载点文件系统为空,那么是添加一块盘挂载。
        if not _mount_extend['mount_partition_name']:
            if extend_size < 50:
                return False, "新增挂载点的大小必须大于等于50"
            if extend_size > 1024:
                return False, "新增挂载点的大小不能大于1T"
            add_disk_extend_action_to_database(uuid, request_id, user_id, InstaceActions.INSTANCE_CREATE_MOUNT_POINT,
                                               ActionStatus.START, "start mount the disk on new mount_point {}".format(extend_mount))
            flag, msg = create_mount_point(extend_mount, disk_devices, extend_size, uuid, c_version, connect_instance,
                               storage_instance, request_id, user_id, instance_id)
            if flag:
                data_list.append(msg)
                update_disk_action_to_database(request_id, InstaceActions.INSTANCE_CREATE_MOUNT_POINT,
                                               ActionStatus.SUCCSESS, msg)
            else:
                data_list.append(msg)
                update_disk_action_to_database(request_id, InstaceActions.INSTANCE_CREATE_MOUNT_POINT,
                                               ActionStatus.FAILD, msg)
                return False, msg
            continue
        if extend_size < 0:
            return False, "扩容的大小必须大于等于0"

        # 获取文件系统，（lv_path，vg_name，vg_size）, 挂载设备或分区名，设备或分区对应大小，设备或分区对应的空余
        flag, extend_disk_info = __get_extend_info(_mount_extend,connect_instance)
        if not flag:
            data_list.append(" info query error, " + extend_disk_info)
            continue

        # part_name和lv_path都是软连接到/dev下某个文件
        part_name = extend_disk_info[0]
        lv_path = extend_disk_info[1]
        vg_name = extend_disk_info[2]
        vg_free = extend_disk_info[3]
        pvs_list = extend_disk_info[4]
        pvs_size = extend_disk_info[5]
        pvs_free = extend_disk_info[6]

        #  磁盘的扩容不能超过500G
        if (extend_size + pvs_size[0]) > 1024:
            return False, "挂载点的大小不能大于1T"
        # params : pvs_list , pvs_free , vg_free , lv_path
        # 查询对应哪一种扩容类型
        flag,extend_size = __get_extend_flag([pvs_list,pvs_free,vg_free,lv_path],extend_size,c_version,connect_instance)

        # 查询出错
        if flag == 0:
            data_list.append(extend_mount + ' error')
        # 对应设备的情况
        elif flag == 1:
            for i, dev in enumerate(pvs_list):
                flag, msg = get_info_by_mount_and_disk(extend_mount, dev, instance_id)
                if flag:
                    for disk in disk_devices:
                        if disk['dev'] == dev:
                            output = connect_instance.resize_disk(disk['path'].split('/')[-1],
                                                                  extend_size + pvs_size[i])
                            extend_dev = dev
                            update_disk_extend_to_database(extend_size + pvs_size[i], extend_dev, instance_id)
                    break
            else:
                for disk in disk_devices:
                    if disk['dev'] == pvs_list[0]:
                        output = connect_instance.resize_disk(disk['path'].split('/')[-1], extend_size + pvs_size[0])
                        extend_dev = disk['dev']
                        update_disk_extend_to_database(extend_size + pvs_size[0], extend_dev, instance_id)
            if output == -1 or output == 1:
                _msg = "disk {} blockresize error".format(extend_dev)
                data_list.append(_msg)
                add_disk_extend_action_to_database(uuid, request_id, user_id, InstaceActions.INSTANCE_DISK_DEV_EXTEND,
                                                   ActionStatus.FAILD, _msg)
                break
            if extend_type == 'lvm':
                connect_instance.exec_qemu_command('pvresize ' + '/dev/' + extend_dev)
                connect_instance.exec_qemu_command('lvextend ' + str(lv_path) + ' -l +100%free')
                if c_version == CentOS_Version.CentOS_7:
                    connect_instance.exec_qemu_command('xfs_growfs ' + lv_path)
                else:
                    connect_instance.exec_qemu_command('resize2fs ' + lv_path)

                _msg = "lvextend {} successfully".format(str(lv_path))
                add_disk_extend_action_to_database(uuid, request_id, user_id, InstaceActions.INSTANCE_DISK_LV_EXTEND,
                                                   ActionStatus.SUCCSESS, _msg, finish_time=get_datetime_str())
                add_disk_extend_action_to_database(uuid, request_id, user_id, InstaceActions.INSTANCE_DISK_DEV_EXTEND,
                                                   ActionStatus.SUCCSESS,
                                                   "dev {} extend successfully".format(extend_dev),
                                                   finish_time=get_datetime_str())
                data_list.append(extend_mount + ' has extended')
            else:
                # 非lvm扩容
                add_disk_extend_action_to_database(uuid, request_id, user_id, InstaceActions.INSTANCE_DISK_DEV_EXTEND,
                                                   ActionStatus.SUCCSESS,
                                                   "dev {} extend successfully".format(extend_dev),
                                                   finish_time=get_datetime_str())
                data_list.append(extend_mount + ' has extended')
        # vg剩余较多，扩充完毕
        elif flag == 2:
            data_list.append(extend_mount + ' has extended')
        # 非lvm, 告知还需要手动扩展分区 ; lvm加一块disk
        elif flag == 3:
            if extend_type != 'lvm':
                data_list.append('flag 3, not lvm blockresize error.')
                continue
            # 加一块磁盘
            add_disk_extend_action_to_database(uuid, request_id, user_id,
                                        InstaceActions.INSTANCE_ATTACH_NEW_DISK, ActionStatus.START, 'start')
            flag, dev, disk_size = __attach_disk_resize(disk_devices,connect_instance,storage_instance,uuid,extend_size)
            # 添加失败
            if not flag:
                _msg = "not allow to add one disk"
                data_list.append(_msg)
                update_disk_action_to_database(request_id, InstaceActions.INSTANCE_ATTACH_NEW_DISK, ActionStatus.FAILD, _msg)
                continue
            # 添加成功
            _msg = " attach a new disk {}".format(dev)
            update_disk_action_to_database(request_id, InstaceActions.INSTANCE_ATTACH_NEW_DISK, ActionStatus.SUCCSESS, _msg)
            add_disk_extend_to_database(disk_size, dev, instance_id)
            connect_instance.exec_qemu_command('pvcreate ' + '/dev/' + dev)
            connect_instance.exec_qemu_command('vgextend ' + vg_name + ' /dev/' + dev)
            add_disk_extend_action_to_database(uuid, request_id, user_id, InstaceActions.INSTANCE_DISK_VG_EXTEND,
                                               ActionStatus.SUCCSESS, "vgextend {} successfully".format(vg_name),
                                               finish_time=get_datetime_str())
            if extend_size < 9.9:
                command = 'lvextend ' + lv_path + ' -L +' + str(extend_size) + 'G'
            else:
                command = 'lvextend ' + str(lv_path) + ' -l +100%free'
            add_disk_extend_action_to_database(uuid, request_id, user_id, InstaceActions.INSTANCE_DISK_LV_EXTEND,
                                               ActionStatus.SUCCSESS, "lvextend {} successfully".format(str(lv_path)),
                                               finish_time=get_datetime_str())

            connect_instance.exec_qemu_command(command)
            if c_version == CentOS_Version.CentOS_7:
                connect_instance.exec_qemu_command('xfs_growfs ' + lv_path)
            else:
                connect_instance.exec_qemu_command('resize2fs ' + lv_path + ' ')
            data_list.append('add one disk successfully' + ' /dev/' + dev)
        # 剩余空间较多，让用户手动扩展
        elif flag == 4:
            # data_list.append('设备中空闲分区大小大于50G,请线下操作')
            # params = {'code': ActionStatus.FAILD, 'msg': 'failed', 'data': data_list}
            return False, "设备中空闲分区大小大于50G,请线下操作"

    del connect_instance
    del storage_instance
    params = {'code':ActionStatus.SUCCSESS,'msg':'success','data':data_list}
    return True,json_helper.write(params)


def extend_dev_size(mount_extend_list,host_ip,vmname,uuid, instance_id):

    data_list= []
    # 分别是实例连接和存储连接
    connect_instance = vmManager.libvirt_get_connect(host_ip, conn_type='instance', vmname=vmname)
    storage_instance = vmManager.libvirt_get_connect(host_ip, conn_type='storage', vmname=vmname,poolname=uuid)

    user_id = get_user()['user_id']
    request_id = ins_s.generate_req_id()

    # 连接失败，返回错误信息，action添加错误记录
    if not connect_instance or not storage_instance:
        msg = "connect或者storage连接失败，无法使用libvirt管理虚拟机"
        add_disk_display_action_to_database(uuid, request_id, user_id,
                                    InstaceActions.INSTANCE_LIBVIRT_ERROR, ActionStatus.FAILD, msg)
        return False,json_helper.write({'code':ActionStatus.FAILD,'msg':msg,'data':data_list})

    # 为了统一参数: extend_mount对应设备名 vda,vdb等
    for _mount_extend in mount_extend_list:
        extend_size = int(_mount_extend['mount_extend_size'])
        extend_mount = _mount_extend['mount_point']
        # mount_point_size = float(_mount_extend['mount_point_size'])
        disk_devices = connect_instance.get_disk_device()

        if extend_mount and extend_size == 0:
            continue

        # 没有设备名，对应添加一块盘
        if not extend_mount:
            # 判断新增挂载点的大小必须大于0
            if extend_size <= 0:
                return False, "新增挂载点的大小必须大于0"
            if extend_size > 1024:
                return False, "挂载点的大小不能超过1T"
            # 加一块磁盘,添加action
            add_disk_extend_action_to_database(uuid, request_id, user_id,
                                        InstaceActions.INSTANCE_ATTACH_NEW_DISK, ActionStatus.START, 'start')
            flag, dev, disk_size = __attach_disk_resize(disk_devices,connect_instance,storage_instance,uuid,extend_size)
            if not flag:
                msg = "not allow to add one disk"
                update_disk_action_to_database(request_id, InstaceActions.INSTANCE_ATTACH_NEW_DISK, ActionStatus.FAILD,
                                               msg)
                data_list.append(msg)
            else:
                # 添加成功
                msg = " attach a new disk {}".format(dev)
                update_disk_action_to_database(request_id, InstaceActions.INSTANCE_ATTACH_NEW_DISK,
                                               ActionStatus.SUCCSESS, msg)
                add_disk_extend_to_database(disk_size, dev, instance_id, extend_mount)
                data_list.append('add disk successfully, but you need add partition.')
        else: # 扩容设备
            return False, "暂时不支持windows操作系统扩容"
            # match_disk = filter(lambda x:x['dev'] == extend_mount,disk_devices)
            #
            # mount_point_size = float(_mount_extend['mount_point_size'])
            #
            # output = connect_instance.resize_disk(match_disk[0]['path'].split('/')[-1], extend_size + mount_point_size)
            # if output == -1 or output ==1: # 扩容失败
            #     msg = "disk {} blockresize error".format(extend_mount)
            #     add_disk_extend_action_to_database(uuid, request_id, user_id,
            #                                        InstaceActions.INSTANCE_DISK_DEV_EXTEND, ActionStatus.FAILD,msg)
            #     data_list.append('msg')
            # else:
            #     msg = "dev {} extend successfully".format(extend_mount)
            #     add_disk_extend_action_to_database(uuid, request_id, user_id, InstaceActions.INSTANCE_DISK_DEV_EXTEND,
            #                                        ActionStatus.SUCCSESS, msg, finish_time=get_datetime_str())
            #     update_disk_extend_to_database(extend_size + mount_point_size, extend_mount, instance_id)
            #     data_list.append(msg)

    del connect_instance
    del storage_instance
    params = {'code': ActionStatus.SUCCSESS, 'msg': 'success', 'data': data_list}
    return True, json_helper.write(params)


def _del_instance_data_db(instance_id, dc_type, instance_status):
    # instance
    update_data = {
        'isdeleted': '1',
        'deleted_at': get_datetime_str()
    }
    where_data = {
        'id': instance_id
    }
    ret = ins_s.InstanceService().update_instance_info(update_data, where_data)
    if ret != 1:
        logging.error('delete instance %s error', instance_id)

    # instance_flavor
    ret_f = ins_f_s.InstanceFlavorService().delete_instance_flavor(instance_id)
    if ret_f != 1:
        logging.error('delete instance %s flavor error', instance_id)

    # instance_group
    ret_g = ins_g_s.InstanceGroupService().delete_instance_group_info(instance_id)
    if ret_g != 1:
        logging.error('delete instance %s group error', instance_id)

    # instance_host
    update_data_h = {
        'isdeleted': '1',
        'deleted_at': get_datetime_str()
    }
    where_data_h = {
        'instance_id': instance_id
    }
    ret_h = ins_h_s.InstanceHostService().update_instance_host_info(update_data_h, where_data_h)
    if ret_h != 1:
        logging.error('delete instance %s host error', instance_id)

    # instance_image
    update_data_i = {
        'isdeleted': '1',
        'deleted_at': get_datetime_str()
    }
    where_data_i = {
        'instance_id': instance_id
    }
    ret_i = ins_i_s.InstanceImageService().update_instance_image_info(update_data_i, where_data_i)
    if ret_i != 1:
        logging.error('delete instance %s image error', instance_id)

    # instance_disk
    update_data_d = {
        'isdeleted': '1',
        'deleted_at': get_datetime_str()
    }
    where_data_d = {
        'instance_id': instance_id
    }
    ret_d = ins_d_s.InstanceDiskService().update_instance_disk_info(update_data_d, where_data_d)
    if ret_d != 1:
        logging.error('delete instance %s disk error', instance_id)

    # instance_ip
    update_data_ip = {
        'isdeleted': '1',
        'deleted_at': get_datetime_str()
    }
    where_data_ip = {
        'instance_id': instance_id
    }
    ret_i_ip = ins_ip_s.InstanceIPService().update_instance_ip_info(update_data_ip, where_data_ip)
    if ret_i_ip != 1:
        logging.error('delete instance %s ip error', instance_id)

    ip_datas_list = ins_s.get_all_ip_of_instance(instance_id)
    if len(ip_datas_list) > 0:
        for ip_data in ip_datas_list:
            if ip_data['segment_type'] != NetCardType.TENCENT_CLOUD_NORMAL:
                ret_change_ip_status, ret_change_ip_detail = __instance_delete_change_drprd_status(dc_type, ip_data)
                if not ret_change_ip_status:
                    logging.error(ret_change_ip_detail)
                    if instance_status == VMStatus.ERROR:
                        change_current_ip_status = IPStatus.HOLD
                    else:
                        change_current_ip_status = IPStatus.UNUSED
                elif ret_change_ip_detail == 'not prd or dr':
                    if instance_status == VMStatus.ERROR:
                        change_current_ip_status = IPStatus.HOLD
                    else:
                        change_current_ip_status = IPStatus.UNUSED
                elif ret_change_ip_detail == IPStatus.USED:
                    change_current_ip_status = IPStatus.PRE_ALLOCATION
                else:
                    if instance_status == VMStatus.ERROR:
                        change_current_ip_status = IPStatus.HOLD
                    else:
                        change_current_ip_status = IPStatus.UNUSED
            else:
                change_current_ip_status = IPStatus.PRE_ALLOCATION

            # 改变当前IP状态
            update_ip = {
                'status': change_current_ip_status,
                'updated_at': get_datetime_str()
            }
            where_ip = {
                'id': ip_data['id']
            }
            ret_ip = ip_s.IPService().update_ip_info(update_ip, where_ip)
            if ret_ip != 1:
                logging.error('update ip status error, update_data:%s, where_data:%s', update_ip, where_ip)

    return True


def _update_config_msg_to_db(task_id, msg, job_status):
        update_data = {
            'message': msg,
            'status': job_status,
            'finish_time': get_datetime_str()
        }
        where_data = {
            'task_id': task_id
        }
        return instance_action.InstanceActionsServices().update_instance_action_status(update_data, where_data)


def _instance_net_down(instance_name, instance_mac, host_ip, dev):

    connect_instance = vmManager.libvirt_get_connect(host_ip, conn_type='instance', vmname=instance_name)
    if not connect_instance:
        return False, 'can not connect to libvirtd'
    return vmManager.libvirt_instance_net_down(connect_instance, instance_mac, dev)


def _instance_net_offline(instance_name, instance_mac, host_ip, dev):
    connect_instance = vmManager.libvirt_get_connect(host_ip, conn_type='instance', vmname=instance_name)
    if not connect_instance:
        return False, 'can not connect to libvirtd'
    return vmManager.libvirt_instance_net_state_change(connect_instance, instance_mac, dev, NetCardStatus.DOWN)


def _instance_net_online(instance_name, instance_mac, host_ip, dev):
    connect_instance = vmManager.libvirt_get_connect(host_ip, conn_type='instance', vmname=instance_name)
    if not connect_instance:
        return False, 'can not connect to libvirtd'
    return vmManager.libvirt_instance_net_state_change(connect_instance, instance_mac, dev, NetCardStatus.UP)


def _instance_net_on(instance_name, instance_mac, host_ip, dev):

    connect_instance = vmManager.libvirt_get_connect(host_ip, conn_type='instance', vmname=instance_name)
    if not connect_instance:
        return False, 'can not connect to libvirtd'
    return vmManager.libvirt_instance_net_on(connect_instance, instance_mac, dev)


def _instance_net_update(instance_name, instance_mac, host_ip, dev):

    connect_instance = vmManager.libvirt_get_connect(host_ip, conn_type='instance', vmname=instance_name)
    if not connect_instance:
        return False, 'can not connect to libvirtd'
    return vmManager.libvirt_instance_net_update(connect_instance, instance_mac, dev)


def _instance_xml_dump(instance_name, xml_backup_dir, host_ip):
    connect_instance = vmManager.libvirt_get_connect(host_ip, conn_type='instance', vmname=instance_name)
    if not connect_instance:
        return False, 'can not connect to libvirtd'
    get_status, instance_xml = vmManager.libvirt_instance_xml(connect_instance)
    if get_status:
        ansible_ret = ansible_remote_backup_instance_xml(host_ip, instance_name, instance_xml,
                                                         get_datetime_str_link(), xml_backup_dir)
        if not ansible_ret:
            return False, 'instance xml backup failed'
        elif ansible_ret is 1:
            return False, 'instance xml backup failed because ansible not available'
        else:
            return True, 'instance xml backup successful'
    else:
        return False, instance_xml


def _change_instance_network(host_ip, ins_name, net_info, vlan_new=False, net_card_new=False):
    '''
        修改虚拟机指定网卡ip、网关、网卡配置
    :param net_info:
    :param vlan_new:
    :return:
    '''
    if net_card_new:
        # 连接libvirt找到对应虚拟机
        connect_libivrt = vmManager.libvirt_get_connect(host_ip, conn_type='instance', vmname=ins_name)
        if not connect_libivrt:
            return False, '无法使用libvirt进行虚拟机新增网卡配置，请联系管理员'

        # 通过libvirt串口配置虚拟机ip
        inject_net_status, result_msg = vmManager.libvirt_change_instance_ip(connect_libivrt, net_info, net_card_new=True)
        if not inject_net_status:
            return False, '无法使用libvirt进行虚拟机ip配置，请联系管理员'
        # elif 'output' in result_msg:
        #     if eval(result_msg)['return']['cmd_ret'] != 0:
        #         return False, '无法找到mac地址对应的网卡配置文件'
        # elif result_msg != '{"return":0}':
        #     return False, '无法找到mac地址对应的网卡配置文件'
        return True, '网卡配置成功'
    if not vlan_new:
        # 连接libvirt找到对应虚拟机
        connect_libivrt = vmManager.libvirt_get_connect(host_ip, conn_type='instance', vmname=ins_name)
        if not connect_libivrt:
            return False, '无法使用libvirt进行虚拟机ip配置，请联系管理员'

        # 通过libvirt串口修改虚拟机ip
        inject_net_status, result_msg = vmManager.libvirt_change_instance_ip(connect_libivrt, net_info)
        if not inject_net_status:
            return False, '无法使用libvirt进行虚拟机ip配置，请联系管理员'
        # elif 'output' in result_msg:
        #     if eval(result_msg)['return']['cmd_ret'] != 0:
        #         return False, '无法找到mac地址对应的网卡配置文件'
        # elif result_msg != '{"return":0}':
        #     return False, '无法找到mac地址对应的网卡配置文件'
    else:
        # 由于vlan发生改变需要修改虚拟机xml文件
        net_dev = 'br_bond0.' + net_info['vlan_new']
        _xml_backup_dir = DIR_INSTANCE_XML_BACKUP
        # 备份xml文件
        instance_xml_backup_status, _msg = _instance_xml_dump(ins_name, _xml_backup_dir, host_ip)
        if not instance_xml_backup_status:
            return False, _msg

        # 更新xml配置文件中网卡vlan
        net_update_status, _msg = _instance_net_update(ins_name, net_info['mac_addr'], host_ip, net_dev)
        if not net_update_status:
            return False, _msg

        # 连接libvirt找到对应虚拟机
        connect_libivrt = vmManager.libvirt_get_connect(host_ip, conn_type='instance', vmname=ins_name)
        if not connect_libivrt:
            return False, '无法使用libvirt进行虚拟机ip配置，请联系管理员'

        # 修改网卡文件(包括ip、掩码、网关)，并重启网络
        inject_net_status, result_msg = vmManager.libvirt_change_instance_ip(connect_libivrt, net_info, vlan_new=True)
        if not inject_net_status:
            return False, '无法使用libvirt进行虚拟机ip配置，请联系管理员'
        # elif 'output' in result_msg:
        #     if eval(result_msg)['return']['cmd_ret'] != 0:
        #         return False, '无法找到mac地址对应的网卡配置文件'
        # elif result_msg != '{"return":0}':
        #     return False, '无法找到mac地址对应的网卡配置文件'

    return True, 'ip修改成功'


def _instance_ip_configure_change_db(ins_id, net_info, env):

    if net_info['ip_addr']:
        # 查询ip对应的id
        ip_id_cur = ip_s.IPService().get_ip_by_ip_address(net_info['ip_addr'])
        ip_id_new = ip_s.IPService().get_ip_by_ip_address(net_info['ip_addr_new'])

        if not ip_id_cur or not ip_id_new:
            msg = '无法在数据库中找到ip：%s 或 %s 记录' % (ip_id_cur, ip_id_new)
            return False, msg

        # 查找生产、容灾环境对应的容灾、生产环境IP
        ret_change_status, ret_change_detail = __change_drprd_status(env, ip_id_cur, ip_id_new)
        if not ret_change_status:
            return False, ret_change_detail

        # 修改instance_ip表格
        # 如果是v2v虚拟机则改成删除ip信息
        instance_info = ins_s.InstanceService().get_instance_info(ins_id)
        instance_source = instance_info['create_source']
        if instance_source == '1' or instance_source == '2':
            instance_ipaddr = ip_s.get_ipaddress_of_instance(ins_id)
            instance_ip_id = ip_s.IPService().get_ip_by_ip_address(instance_ipaddr)['id']
            res = ip_s.del_ip_info(instance_ip_id)
            if not res:
                msg = "删除v2v迁移到kvm平台的虚拟机ip：%s 失败" % ip_id_cur['ip_address']
                return False, msg
        else:
            # 释放原来的ip
            if int(env) == DataCenterType.PRD or int(env) == DataCenterType.DR:
                pass
            else:
                _ip_change_db_status, _change_db_ip_msg = _change_db_ip_unused(ip_id_cur)
                if not _ip_change_db_status:
                    msg = "标记原有ip：%s 为未使用失败" % ip_id_cur['ip_address']
                    return False, msg

        update_data_ip = {
            'ip_id': ip_id_new['id']
        }
        where_data_ip = {
            'instance_id': ins_id,
            'mac': net_info['mac_addr'],
            'ip_id': ip_id_cur['id']
        }
        ret_i_ip = ins_ip_s.InstanceIPService().update_instance_ip_info(update_data_ip,
                                                                        where_data_ip)
        if ret_i_ip != 1:
            msg = "更新虚拟机ip：%s 为 %s 失败" % (ip_id_cur['ip_address'], ip_id_new['ip_address'])
            return False, msg

    else:
        ip_id_new = ip_s.IPService().get_ip_by_ip_address(net_info['ip_addr_new'])
        if not ip_id_new:
            msg = '无法在数据库中找到ip：%s 记录' % ip_id_new
            return False, msg

        # 查找生产、容灾环境对应的容灾、生产环境IP
        ret_change_status, ret_change_detail = __change_drprd_status(env, False, ip_id_new)
        if not ret_change_status:
            return False, ret_change_detail

        update_data_ip = {
            'ip_id': ip_id_new['id'],
            'updated_at': get_datetime_str()
        }
        where_data_ip = {
            'instance_id': ins_id,
            'mac': net_info['mac_addr']
        }
        ret_i_ip = ins_ip_s.InstanceIPService().update_instance_ip_info(update_data_ip,
                                                                        where_data_ip)
        if ret_i_ip != 1:
            msg = "更新虚拟机网卡ip：%s信息到数据库失败" % ip_id_new['ip_address']
            return False, msg

    return True, '数据库记录修改成功'


# 子网掩码计算
def _exchange_maskint(mask_int):
    bin_arr = ['0' for i in range(32)]
    for i in range(mask_int):
        bin_arr[i] = '1'
    tmpmask = [''.join(bin_arr[i * 8:i * 8 + 8]) for i in range(4)]
    tmpmask = [str(int(tmpstr, 2)) for tmpstr in tmpmask]
    return '.'.join(tmpmask)


def _change_db_ip_used(ip_info):
    '''
        修改数据库ip表中ip状态为已使用
    :param ip_info:
    :return:
    '''
    update_data = {
        'status': IPStatus.USED
    }
    where_data = {
        'id': ip_info['id']
    }
    ret_mark_ip = ip_s.IPService().update_ip_info(update_data, where_data)
    if ret_mark_ip <= 0:
        msg = "标记ip：%s 为已使用失败" % ip_info['ip_address']
        return False, msg
    return True, "标记ip：%s 为已使用成功" % ip_info['ip_address']


def _change_db_ip_unused(ip_info):
    '''
        修改数据库ip表中ip状态为未使用
    :param ip_info:
    :return:
    '''
    update_data = {
        'status': IPStatus.UNUSED
    }
    where_data = {
        'id': ip_info['id']
    }
    ret_mark_ip = ip_s.IPService().update_ip_info(update_data, where_data)
    if ret_mark_ip <= 0:
        msg = "标记ip：%s 为未使用失败" % ip_info['ip_address']
        return False, msg
    return True, "标记ip：%s 为未使用成功" % ip_info['ip_address']


def __change_drprd_status(env, ip_cur, ip_new):

    if ip_cur:
        # 更新原有ip状态
        if int(env) == DataCenterType.PRD:
            segment_dr = segment_m.SegmentMatchService().get_segment_match_info_by_prd_segment_id(ip_cur['segment_id'])
            if not segment_dr:
                return False, "无法获取当前生产IP对应容灾网段信息"
            segment_dr_data = segment_s.SegmentService().get_segment_info(segment_dr['dr_segment_id'])
            if not segment_dr_data:
                return False, "无法获取当前生产IP对应容灾网段详细信息"
            # 拼凑虚拟机容灾IP
            dr_ip = segment_dr_data['segment'].split('.')[0] + '.' + segment_dr_data['segment'].split('.')[1] + \
                    '.' + ip_cur['ip_address'].split('.')[2] + '.' + ip_cur['ip_address'].split('.')[3]
            dr_ip_info = ip_s.IPService().get_ip_by_ip_address(dr_ip)
            # 如果容灾IP是未使用中状态，可以使用
            if dr_ip_info:
                if dr_ip_info['status'] == IPStatus.PRE_ALLOCATION:
                    # 重置对应ip为未使用
                    update_dr_ip_data = {
                        'status': IPStatus.UNUSED
                    }
                    where_dr_ip_data = {
                        'id': dr_ip_info['id']
                    }
                    ret_mark_ip = ip_s.IPService().update_ip_info(update_dr_ip_data, where_dr_ip_data)
                    if ret_mark_ip <= 0:
                        return False, "当前生产IP对应容灾IP从预分配重置为未使用状态失败"

                    # 重置当前ip为未使用
                    update_cur_ip_data = {
                        'status': IPStatus.UNUSED
                    }
                    where_cur_ip_data = {
                        'id': ip_cur['id']
                    }
                    ret_mark_ip = ip_s.IPService().update_ip_info(update_cur_ip_data, where_cur_ip_data)
                    if ret_mark_ip <= 0:
                        return False, "当前生产IP从使用中重置为预分配状态失败"

                elif dr_ip_info['status'] == IPStatus.USED:
                    # 重置当前ip为预分配
                    update_prd_ip_data = {
                        'status': IPStatus.PRE_ALLOCATION
                    }
                    where_prd_ip_data = {
                        'id': ip_cur['id']
                    }
                    ret_mark_ip = ip_s.IPService().update_ip_info(update_prd_ip_data, where_prd_ip_data)
                    if ret_mark_ip <= 0:
                        return False, "当前生产IP对应容灾IP从使用中重置为预分配状态失败"
        elif int(env) == DataCenterType.DR:
            segment_prd = segment_m.SegmentMatchService().get_segment_match_info_by_dr_segment_id(ip_cur['segment_id'])
            if not segment_prd:
                return False, "无法获取当前容灾IP对应生产网段信息"
            segment_prd_data = segment_s.SegmentService().get_segment_info(segment_prd['prd_segment_id'])
            if not segment_prd_data:
                return False, "无法获取当前容灾IP对应生产网段详细信息"
            # 拼凑虚拟机生产IP
            prd_ip = segment_prd_data['segment'].split('.')[0] + '.' + segment_prd_data['segment'].split('.')[1] + '.' + \
                     ip_cur['ip_address'].split('.')[2] + '.' + ip_cur['ip_address'].split('.')[3]
            prd_ip_info = ip_s.IPService().get_ip_by_ip_address(prd_ip)
            # 如果生产环境ip是未使用中状态，可以使用
            if prd_ip_info:
                if prd_ip_info['status'] == IPStatus.PRE_ALLOCATION:
                    # 重置对应ip为未使用
                    update_dr_ip_data = {
                        'status': IPStatus.UNUSED
                    }
                    where_dr_ip_data = {
                        'id': prd_ip_info['id']
                    }
                    ret_mark_ip = ip_s.IPService().update_ip_info(update_dr_ip_data, where_dr_ip_data)
                    if ret_mark_ip <= 0:
                        return False, "当前容灾IP对应生产IP从预分配重置为未使用状态失败"

                    # 重置当前ip为未使用
                    update_cur_ip_data = {
                        'status': IPStatus.UNUSED
                    }
                    where_cur_ip_data = {
                        'id': ip_cur['id']
                    }
                    ret_mark_ip = ip_s.IPService().update_ip_info(update_cur_ip_data, where_cur_ip_data)
                    if ret_mark_ip <= 0:
                        return False, "当前容灾IP从使用中重置为预分配状态失败"
                elif prd_ip_info['status'] == IPStatus.USED:
                    # 重置当前ip为预分配
                    update_dr_ip_data = {
                        'status': IPStatus.PRE_ALLOCATION
                    }
                    where_dr_ip_data = {
                        'id': ip_cur['id']
                    }
                    ret_mark_ip = ip_s.IPService().update_ip_info(update_dr_ip_data, where_dr_ip_data)
                    if ret_mark_ip <= 0:
                        return False, "当前容灾IP对应生产IP从使用中重置为预分配状态失败"

    # 更新新ip状态
    if int(env) == DataCenterType.PRD:
        segment_dr = segment_m.SegmentMatchService().get_segment_match_info_by_prd_segment_id(ip_new['segment_id'])
        if not segment_dr:
            return False, "无法获取当前生产IP对应容灾网段信息"
        segment_dr_data = segment_s.SegmentService().get_segment_info(segment_dr['dr_segment_id'])
        if not segment_dr_data:
            return False, "无法获取当前生产IP对应容灾网段详细信息"
        # 拼凑虚拟机容灾IP
        dr_ip = segment_dr_data['segment'].split('.')[0] + '.' + segment_dr_data['segment'].split('.')[1] + \
                '.' + ip_new['ip_address'].split('.')[2] + '.' + ip_new['ip_address'].split('.')[3]
        dr_ip_info = ip_s.IPService().get_ip_by_ip_address(dr_ip)
        # 如果容灾IP是未使用中状态，可以使用
        if dr_ip_info:
            if dr_ip_info['status'] == IPStatus.UNUSED:
                # 重置对应ip为未使用
                update_dr_ip_data = {
                    'status': IPStatus.PRE_ALLOCATION
                }
                where_dr_ip_data = {
                    'id': dr_ip_info['id']
                }
                ret_mark_ip = ip_s.IPService().update_ip_info(update_dr_ip_data, where_dr_ip_data)
                if ret_mark_ip <= 0:
                    return False, "当前生产IP对应容灾IP从预分配重置为未使用状态失败"

    elif int(env) == DataCenterType.DR:
        segment_prd = segment_m.SegmentMatchService().get_segment_match_info_by_dr_segment_id(ip_new['segment_id'])
        if not segment_prd:
            return False, "无法获取当前容灾IP对应生产网段信息"
        segment_prd_data = segment_s.SegmentService().get_segment_info(segment_prd['prd_segment_id'])
        if not segment_prd_data:
            return False, "无法获取当前容灾IP对应生产网段详细信息"
        # 拼凑虚拟机生产IP
        prd_ip = segment_prd_data['segment'].split('.')[0] + '.' + segment_prd_data['segment'].split('.')[
            1] + '.' + \
                 ip_new['ip_address'].split('.')[2] + '.' + ip_new['ip_address'].split('.')[3]
        prd_ip_info = ip_s.IPService().get_ip_by_ip_address(prd_ip)
        # 如果生产环境ip是未使用中状态，可以使用
        if prd_ip_info:
            if prd_ip_info['status'] == IPStatus.UNUSED:
                # 重置对应ip为未使用
                update_dr_ip_data = {
                    'status': IPStatus.PRE_ALLOCATION
                }
                where_dr_ip_data = {
                    'id': prd_ip_info['id']
                }
                ret_mark_ip = ip_s.IPService().update_ip_info(update_dr_ip_data, where_dr_ip_data)
                if ret_mark_ip <= 0:
                    return False, "当前容灾IP对应生产IP从预分配重置为未使用状态失败"

    return True, "生产、容灾IP状态重置成功"


def __instance_delete_change_drprd_status(env, ip_datas):
    # 更新原有ip状态
    if int(env) == DataCenterType.PRD:
        segment_dr = segment_m.SegmentMatchService().get_segment_match_info_by_prd_segment_id(ip_datas['segment_id'])
        if not segment_dr:
            return False, "无法获取当前生产IP对应容灾网段信息"
        segment_dr_data = segment_s.SegmentService().get_segment_info(segment_dr['dr_segment_id'])
        if not segment_dr_data:
            return False, "无法获取当前生产IP对应容灾网段详细信息"
        # 拼凑虚拟机容灾IP
        dr_ip = segment_dr_data['segment'].split('.')[0] + '.' + segment_dr_data['segment'].split('.')[1] + \
                '.' + ip_datas['ip_address'].split('.')[2] + '.' + ip_datas['ip_address'].split('.')[3]
        dr_ip_info = ip_s.IPService().get_ip_by_ip_address(dr_ip)
        # 如果容灾IP是预分配状态，修改ip为未使用
        if dr_ip_info:
            if dr_ip_info['status'] == IPStatus.PRE_ALLOCATION:
                # 重置对应ip为未使用
                update_dr_ip_data = {
                    'status': IPStatus.UNUSED
                }
                where_dr_ip_data = {
                    'id': dr_ip_info['id']
                }
                ret_mark_ip = ip_s.IPService().update_ip_info(update_dr_ip_data, where_dr_ip_data)
                if ret_mark_ip <= 0:
                    return False, "当前生产IP对应容灾IP从预分配重置为未使用状态失败"
                return True, 'change ip status succeed'
            else:
                return True, dr_ip_info['status']
        else:
            return False, '无法获取生产IP对应容灾IP详细信息'

    elif int(env) == DataCenterType.DR:
        segment_prd = segment_m.SegmentMatchService().get_segment_match_info_by_dr_segment_id(ip_datas['segment_id'])
        if not segment_prd:
            return False, "无法获取当前容灾IP对应生产网段信息"
        segment_prd_data = segment_s.SegmentService().get_segment_info(segment_prd['prd_segment_id'])
        if not segment_prd_data:
            return False, "无法获取当前容灾IP对应生产网段详细信息"
        # 拼凑虚拟机生产IP
        prd_ip = segment_prd_data['segment'].split('.')[0] + '.' + segment_prd_data['segment'].split('.')[1] + '.' + \
                 ip_datas['ip_address'].split('.')[2] + '.' + ip_datas['ip_address'].split('.')[3]
        prd_ip_info = ip_s.IPService().get_ip_by_ip_address(prd_ip)
        # 如果生产环境ip是未使用中状态，可以使用
        if prd_ip_info:
            if prd_ip_info['status'] == IPStatus.PRE_ALLOCATION:
                # 重置对应ip为未使用
                update_dr_ip_data = {
                    'status': IPStatus.UNUSED
                }
                where_dr_ip_data = {
                    'id': prd_ip_info['id']
                }
                ret_mark_ip = ip_s.IPService().update_ip_info(update_dr_ip_data, where_dr_ip_data)
                if ret_mark_ip <= 0:
                    return False, "当前容灾IP对应生产IP从预分配重置为未使用状态失败"
                return True, 'change ip status succeed'
            else:
                return True, prd_ip_info['status']
        else:
            return False, '无法获取容灾IP对应生产IP详细信息'
    else:
        return True, 'not prd or dr'


# 筛选磁盘信息
def __get_extend_info(_mount_extend,connect_instance):
    """
        根据选择的挂载点 筛选，获取可扩磁盘的信息
        入参：_mount_extend : [_mount_point,_mount_partition_name,_mount_partition_type]
    :return:result: (flag, msg)
                  [lv_name, lv_size
                  vg_name, vg_free
                  pvs_list, pvs_size, pvs_free]
    """
    _mount_point = _mount_extend['mount_point']
    _mount_partition_name = _mount_extend['mount_partition_name']
    _mount_partition_type = _mount_extend['mount_partition_type']

    if not _mount_point or not _mount_partition_name or not _mount_partition_type:
        return False,"cannot get the mount infomation"


    # 查询文件系统名称，挂载点对应大小
    command = "for mount_point in `cat /etc/mtab | grep -w " + _mount_point + " | awk '{print $1}'`; do df -BM -P | grep -w $mount_point | awk '{print $1" + '\\\" ' + '\\\"' + "$2}'; done"
    flag,msg = connect_instance.exec_qemu_command(command)

    # 出错返回
    if not flag or msg == 'no output':
        return False,'query the filesystem error, ' + msg

    name_size = msg.split(' ')
    fs_name = name_size[0]
    fs_size = int(float(name_size[1].strip()[0:-1]) / 1024) + 1

    # 非lvm的返回信息
    if _mount_partition_type != 'lvm':
        fs_data = fs_name.split('/')
        if fs_data[-1].isalpha():
            return True,[fs_name, '', '', 0, [fs_data[-1]], [fs_size], [0]]
        else:
            # 查询分区对应的设备剩余多少空间
            free = __get_partition_free([fs_data[-1]],connect_instance)[0][0]
            return True,[fs_name, '', '', 0, [fs_data[-1]], [fs_size], [free]]

    # 查询 lv_path 和 vg_name
    command = "lvdisplay " + fs_name + " | awk 'NR==2||NR==4{print;}'"
    flag,msg = connect_instance.exec_qemu_command(command)

    if not flag or msg == 'no output':
        return False,'query logical-volume error, ' + msg
    lv_path = msg.split('\n')[0].split('                ')[-1]
    vg_name = msg.split('\n')[1].split('                ')[-1]

    # 查询vg剩余多少空间
    command = "vgdisplay " + vg_name + " -s"
    flag,msg = connect_instance.exec_qemu_command(command)
    if not flag or msg == 'no output':
        return False,'query matching volume-group free error, ' + msg
    output = [i for i in msg.split(' ') if i != '']
    vg_free = output[output.index('/') + 1]
    vg_unit = output[output.index('/') + 2]

    # 对vg_free单位进行转换
    if float(vg_free) != 0:
        vg_free = float(vg_free) / 1024 if vg_unit != 'GiB' else float(vg_free)
    else:
        vg_free = float(vg_free)

    # 查询所有pv信息
    pvs_all_list = []
    pvs_size = []
    pvs_free = []

    # 通过vg_name查询pv信息
    command = 'pvdisplay | grep -B1 -w %s' % vg_name
    flag,msg = connect_instance.exec_qemu_command(command)
    if not flag or msg == 'no output':
        return False,'query pvs_name and pvs_size error, ' + msg
    for line in msg.split('\n'):
        data = line.split('               ')
        if 'PV Name' == data[0].strip():
            pvs_all_list.append(data[-1].split('/')[-1])

    # 查询pv中对应的所有设备
    pvs_list = filter(lambda x: x.isalpha() and len(x) == 3, pvs_all_list)
    if pvs_list:
        for dev in pvs_list:
            # 查询对应设备的大小
            command = "lsblk -rb | grep -w " + dev + " | awk '{print $4}'"
            flag, msg = connect_instance.exec_qemu_command(command)
            if not flag or msg == 'no output':
                return False, "query devs' size error, " + msg
            pv_size_raw_data = msg.split('\n')[0]
            pv_size = float(pv_size_raw_data) / 1024 /1024 /1024

            pvs_size.append(pv_size)
            pvs_free.append(0)
        return True,[fs_name, lv_path, vg_name, vg_free, pvs_list, pvs_size, pvs_free]

    # pvs中没有设备，全部是分区的情况
    pvs_free = __get_partition_free(pvs_all_list,connect_instance)[0]
    pvs_size = __get_partition_free(pvs_all_list,connect_instance)[1]

    return True,[fs_name, lv_path, vg_name, vg_free, pvs_all_list, pvs_size, pvs_free]


def __get_partition_free(partition_list,connect_instance):
    """
      根据分区获取该分区对应设备还剩多少空间
    :param partition_list:
    :return: 是否查询成功, 查询结果
    """
    if not partition_list:
        return False,"partition doesn't exist"

    free_list = []
    part_size_list = []
    temp_list = []
    for part in partition_list:
        if part[0:-1] not in temp_list:
            temp_list.append(part[0:-1])
    for part in partition_list:

        # 判断part是否重复
        if part[0:-1] not in temp_list:
            continue
        # 获取设备的信息
        command = "lsblk -rb | grep -w " + part[0:-1] + " | awk '{print $4}'"
        flag, msg = connect_instance.exec_qemu_command(command)
        if not flag or msg == 'no output':
            return False, "query devs' size error, " + msg
        dev_size_raw_data = msg.split('\n')[0]
        dev_size = float(dev_size_raw_data) / 1024 / 1024 / 1024

        # 获取分区信息
        command = "lsblk -r /dev/" + part[0:-1] + " | awk '{print $1" + '\\\" ' + '\\\"' + "$4}'"
        flag,msg = connect_instance.exec_qemu_command(command)
        msg = msg.split('\n')
        if not flag or msg == 'no output':
            return False, "query partition infomation error, " + msg
        msg.pop()

        sum_size = 0
        free = 0

        # 分别获取匹配分区的信息, 设备对应所有分区的信息
        part_data = filter(lambda x: x.split(' ')[0] == part, msg)
        parts_data = filter(lambda x: x.split(' ')[0] != part[0:-1] and part[0:-1] in x.split(' ')[0], msg)

        match_part_data = part_data[0].split(' ')[-1]
        if match_part_data.endswith('G'):
            match_part_size = float(match_part_data[0:-1])
        elif match_part_data.endswith('T'):
            match_part_size = float(match_part_data[0:-1]) * 1024
        else:
            match_part_size = float(match_part_data[0:-1]) / 1024

        # 对所有分区信息中的大小求和, 计算出这块设备(disk)剩余多少空间未使用
        for every_part in parts_data:
            raw_data = every_part.split(' ')[-1]
            part_size = float(raw_data[0:-1]) if raw_data.endswith('G') else float(raw_data[0:-1]) / 1024
            sum_size += part_size
            free = dev_size - sum_size

        free_list.append(free)
        part_size_list.append(match_part_size)

        temp_list.remove(part[0:-1])
    return [free_list, part_size_list]

def __get_extend_flag(raw_data,extend_size,version,connect_instance):
    """
               is pv disk ? flag
               flag = 0 : 传入的raw_data为空
               flag = 1 : pv中存在设备, 比如vdc  --- resize
               flag = 2 : pv不存在设备, vg存在大量剩余空间, vg_free >= extend_size, resize lv直接返回结果
               flag = 3 : pv不存在设备, vg剩余空间不过扩容, sum(pvs_free) <= 50g, 加一块磁盘
               flag = 4 : pv不存在设备, vg剩余空间不过扩容, sum(pvs_free) > 50g, 提示用户剩余空间较多, 手动扩展
           """
    pvs_list = raw_data[0]
    pvs_free = raw_data[1]
    vg_free = raw_data[2]
    lv_path = raw_data[3]

    # flag = 0, 传入的数据不合法
    if pvs_list == [] or pvs_free == []:
        return 0,extend_size

    # flag = 1, pvs_list存在设备(比如vdc)
    for pv in pvs_list:
        if pv.isalpha():
            return 1,extend_size

    # vg_free < 5g, 就不去使用vg
    if vg_free >= 5:
        try:
            # 如果剩余较多，直接扩容
            if vg_free > extend_size + 0.1:
                command = 'lvextend -L +' + str(extend_size) + 'G ' + lv_path
                connect_instance.exec_qemu_command(command)
                if version == CentOS_Version.CentOS_7:
                    connect_instance.exec_qemu_command('xfs_growfs ' + lv_path)
                elif version == CentOS_Version.CentOS_6:
                    connect_instance.exec_qemu_command('resize2fs ' + lv_path)
                return 2,extend_size
            else:
                sum_free = sum(pvs_free)
                if sum_free <= 50:
                    command = 'lvextend ' + lv_path + ' -l +100%free'
                    connect_instance.exec_qemu_command(command)
                    # 扩容大小重置
                    extend_size -= vg_free
                    if version == CentOS_Version.CentOS_7:
                        connect_instance.exec_qemu_command('xfs_growfs ' + lv_path)
                    elif version == CentOS_Version.CentOS_6:
                        connect_instance.exec_qemu_command('resize2fs ' + lv_path)
                    return 3, extend_size
                else:
                    return 4, extend_size

        except:
            pass
            return 0


    # 对所有分区对应的设备剩余大小求和
    sum_free = sum(pvs_free)
    if sum_free <= 50:
        return 3,extend_size
    else:
        return 4,extend_size

def __attach_disk_resize(disk_devices,connect_instance,storage_instance,uuid,extend_size):
    """
        加一块磁盘
    :param disk_devices:
    :param connect_instance:
    :param storage_instance:
    :param uuid:
    :param extend_size:
    :return:
    """

    if len(disk_devices) == 0:
        return False, "no disk"
    max = disk_devices[0]
    for i in disk_devices:
        if i['dev'] > max['dev']:
             max = i
    disk_name = max['path'].split('/')[-1]
    disk_dev = max['dev']

    # 计算下一块磁盘的名称
    if disk_name.endswith('img'):
        new_disk_name = disk_name[0:-3] + 'disk' + str(time_helper.get_datetime_str_link())
    else:
        new_disk_name = disk_name.split('.')[0] + '.disk' + str(time_helper.get_datetime_str_link())

    # 计算下一块设备的名称
    if ord(disk_dev[-1]) >= 122:
        return False, ""
    new_disk_dev = disk_dev[0:-1] + chr(ord(disk_dev[-1]) + 1)

    # 刷新pool-list
    storage_instance.refresh()

    # 扩展的磁盘比要扩展的大小大1G
    flag, disk_size = vmManager.add_disk(storage_instance, uuid, new_disk_name, extend_size)
    if flag:
        connect_instance.attach_disk(
            storage_instance.get_disk_xml(uuid, new_disk_name, new_disk_dev))
        return True, new_disk_dev, disk_size
    else:
        return False, '', ''

    # connect_instance.attach_disk(
    #     storage_instance.get_disk_xml(uuid, new_disk_name, new_disk_dev))
    # return True, new_disk_dev


# add 2017/10/17 by wangzitong
def create_mount_point(extend_mount, disk_devices, extend_size, uuid, c_version, connect_instance, storage_instance
                       , request_id, user_id, instance_id):
    # 判断新增挂载点的大小必须大于0
    if extend_size <= 0:
        return False, "新增挂载点的大小必须大于0"
    # 判断VGapp是否存在
    flag, msg = connect_instance.exec_qemu_command("vgs | grep VGapp")
    if flag:
        # VGapp不存在
        if msg == "no output":
            flag1, msg1 = connect_instance.exec_qemu_command("cat /etc/lvm/lvm.conf | grep volume_list | grep -v '#'")
            if flag1:
                # 对volume_list没有限制
                if msg1 == "no output":
                    flag3, msg3 = __init_mount_point(extend_mount, disk_devices, extend_size, connect_instance, storage_instance,
                                       uuid, c_version, request_id, user_id, instance_id, 1)
                    return flag3, msg3
                # 对volume_list有限制
                else:
                    flag2, msg2 = connect_instance.exec_qemu_command(
                        "cat /etc/lvm/lvm.conf | grep volume_list | grep -v '#' | grep VGapp")
                    if flag2:
                        if msg2 == "no output":
                            # volume_list中不存在VGapp
                            _message = "OS不满足新增挂载点操作，请线下操作"
                            return False, _message
                        else:
                            flag3, msg3 = __init_mount_point(extend_mount, disk_devices, extend_size, connect_instance,
                                               storage_instance, uuid, c_version, request_id, user_id, instance_id, 1)
                            return flag3, msg3
            else:
                _message = "volume_list 查看错误，请检查/etc/lvm/kvm.conf文件"
                return False, _message
        # VGapp存在
        else:
            flag1, msg1 = connect_instance.exec_qemu_command("cat /etc/lvm/lvm.conf | grep volume_list | grep -v '#'")
            if flag1:
                # 对volume_list没有限制
                if msg1 == "no output":
                    flag4, msg4 = connect_instance.exec_qemu_command("vgs --units g | grep VGapp | awk '{print $7}'")
                    if flag4:
                        if msg4.strip('g') > extend_size:
                            flag3, msg3 = __init_mount_point(extend_mount, disk_devices, extend_size, connect_instance,
                                                             storage_instance, uuid, c_version, request_id, user_id,
                                                             instance_id, 2, attach=False)
                            return flag3, msg3
                        else:
                            flag3, msg3 = __init_mount_point(extend_mount, disk_devices, extend_size, connect_instance,
                                                             storage_instance, uuid, c_version,request_id, user_id,
                                                             instance_id, 2)
                            return flag3, msg3
                    else:
                        return False, "vgs 查看失败"
                # 对volume_list有限制
                else:
                    flag2, msg2 = connect_instance.exec_qemu_command(
                        "cat /etc/lvm/lvm.conf | grep volume_list | grep -v '#' | grep VGapp")
                    if flag2:
                        if msg2 == "no output":
                            _message = "OS不满足新增挂载点操作，请线下操作"
                            return False, _message
                        else:
                            flag4, msg4 = connect_instance.exec_qemu_command("vgs --units g | grep VGapp | awk '{print $7}'")

                            if flag4:
                                if float(msg4.strip().strip('g')) > extend_size:
                                    flag3, msg3 = __init_mount_point(extend_mount, disk_devices, extend_size,
                                                                     connect_instance,storage_instance, uuid, c_version,
                                                                     request_id, user_id, instance_id, 2, attach=False)
                                    return flag3, msg3
                                else:
                                    flag3, msg3 = __init_mount_point(extend_mount, disk_devices, extend_size,
                                                                     connect_instance,storage_instance, uuid, c_version,
                                                                     request_id, user_id, instance_id, 2)
                                    return flag3, msg3
                            else:
                                return False, "vgs 查看失败"
            else:
                _message = "volume_list 查看错误，请检查/etc/lvm/kvm.conf文件"
                return False, _message
    else:
        _message = 'vg 查看错误'
        return False, _message

# add 2017/10/17 by wangzitong
def __init_mount_point(extend_mount, disk_devices, extend_size, connect_instance, storage_instance, uuid, c_version,
                       request_id, user_id, instance_id, pv_handle, attach=True):

    lv_path = '/dev/VGapp/LV' + extend_mount.strip('/')
    # vg剩余空间少，不足以给新的mount点使用,需要加盘
    if attach:
        # 允许新建的存盘数量小于等于20块
        if len(disk_devices) >= 20:
            return False, "the disk no more than 20."

        # 查询数据库中要添加的新挂载点是否已经存在
        flag, msg = get_instance_disk_by_mount_point(extend_mount, instance_id)
        if flag:
            return False, "要添加的挂载点已经存在，请线下操作"

        # 加一块磁盘
        add_disk_extend_action_to_database(uuid, request_id, user_id,
                                           InstaceActions.INSTANCE_ATTACH_NEW_DISK, ActionStatus.START, 'start')

        flag, dev, disk_size = __attach_disk_resize(disk_devices, connect_instance, storage_instance, uuid, extend_size)
        if not flag:
            _msg = "not allow to add one disk"
            update_disk_action_to_database(request_id, InstaceActions.INSTANCE_ATTACH_NEW_DISK, ActionStatus.FAILD,
                                           _msg)
            return False, _msg
        _msg = " attach a new disk {}".format(dev)
        update_disk_action_to_database(request_id, InstaceActions.INSTANCE_ATTACH_NEW_DISK, ActionStatus.SUCCSESS, _msg)
        add_disk_extend_to_database(disk_size, dev, instance_id, extend_mount)
        # pvcreate
        connect_instance.exec_qemu_command('pvcreate ' + '/dev/' + dev)
        if pv_handle == 1:
            connect_instance.exec_qemu_command('vgcreate  VGapp' + ' /dev/' + dev)
            add_disk_extend_action_to_database(uuid, request_id, user_id, InstaceActions.INSTANCE_DISK_VG_CREATE,
                                               ActionStatus.SUCCSESS, "vgcreate VGapp successfully",
                                               finish_time=get_datetime_str())
        if pv_handle == 2:
            connect_instance.exec_qemu_command('vgextend  VGapp' + ' /dev/' + dev)
            add_disk_extend_action_to_database(uuid, request_id, user_id, InstaceActions.INSTANCE_DISK_VG_EXTEND,
                                               ActionStatus.SUCCSESS, "vgextend VGapp successfully",
                                               finish_time=get_datetime_str())
    # 创建挂载点
    flag, msg = connect_instance.exec_qemu_command('mkdir ' + extend_mount)
    if flag:
        _message = "挂载点创建成功"
    else:
        _message = "挂载点创建失败"
        return False, _message

    flag, msg = connect_instance.exec_qemu_command('lvcreate ' + ' -L +' + str(extend_size) + 'G' + ' VGapp ' + '-n LV'
                                       + extend_mount.strip('/'))
    if flag:
        if msg.find('"LV{}" created'.format(extend_mount.strip('/'))) == -1:
            add_disk_extend_action_to_database(uuid, request_id, user_id, InstaceActions.INSTANCE_DISK_LV_CREATE,
                                               ActionStatus.FAILD, "lvcreate {} failed".format(lv_path),
                                               finish_time=get_datetime_str())
            return False, msg
        else:
            add_disk_extend_action_to_database(uuid, request_id, user_id, InstaceActions.INSTANCE_DISK_LV_CREATE,
                                               ActionStatus.SUCCSESS, "lvcreate {} successfully".format(lv_path),
                                               finish_time=get_datetime_str())


    # add mount
    add_disk_extend_action_to_database(uuid, request_id, user_id, InstaceActions.INSTANCE_MOUNT_DISK,
                                       ActionStatus.START, "start mount disk", finish_time=get_datetime_str())
    if c_version == CentOS_Version.CentOS_7:
        connect_instance.exec_qemu_command('mkfs.xfs ' + lv_path)
        type = "xfs"
    else:
        connect_instance.exec_qemu_command('mkfs.ext4 ' + lv_path)
        type = "ext4"
    connect_instance.exec_qemu_command('mount ' + lv_path + ' ' + extend_mount)
    flag, msg = connect_instance.exec_qemu_command("lsblk | grep {}".format(extend_mount))
    if flag:
        if msg == "no output":
            _msg = "mount {} failed".format(extend_mount)
            update_disk_action_to_database(request_id, InstaceActions.INSTANCE_MOUNT_DISK, ActionStatus.FAILD,
                                           _msg)
            return False, _msg
        else:
            _msg = "mount {} successfully".format(extend_mount)
            update_disk_action_to_database(request_id, InstaceActions.INSTANCE_MOUNT_DISK,
                                           ActionStatus.SUCCSESS, _msg)
    # write mount_info into /etc/fstab
    add_disk_extend_action_to_database(uuid, request_id, user_id, InstaceActions.INSTANCE_WRITE_DISK,
                                       ActionStatus.START, "start write disk_mount info to /etc/fstab",
                                       finish_time=get_datetime_str())
    mount_info = "/dev/mapper/VGapp-LV%s %s    %s    defaults        0 0" % (extend_mount.strip('/'), extend_mount, type)
    command3 = "sed -i '$a {}' /etc/fstab".format(mount_info)
    connect_instance.exec_qemu_command(command3)
    flag, msg = connect_instance.exec_qemu_command("cat /etc/fstab | grep {}".format(extend_mount))
    if flag:
        if msg == "no output":
            _msg = "write disk_mount info to /etc/fstab failed"
            update_disk_action_to_database(request_id, InstaceActions.INSTANCE_WRITE_DISK, ActionStatus.FAILD, _msg)
            return False, _msg
        else:
            _msg = "write disk_mount info to /etc/fstab successfully"
            update_disk_action_to_database(request_id, InstaceActions.INSTANCE_WRITE_DISK, ActionStatus.SUCCSESS,
                                           _msg)
            return True, "new_point mount successfully"
    else:
        return False, "write disk_mount info to /etc/fstab failed"


task_id_1 = ins_s.generate_task_id()
task_id_2 = ins_s.generate_task_id()

def add_disk_display_action_to_database(uuid, request_id, user_id, action,status, message, finish_time=None):
    data = {'action': action,
            'instance_uuid': uuid,
            'task_id': task_id_1,
            'request_id': request_id,
            'user_id': user_id,
            'status': status,
            'message': message,
            'finish_time': finish_time
            }
    return instance_action.add_instance_actions_test(data)
def add_disk_extend_action_to_database(uuid, request_id, user_id, action,status, message, finish_time=None):
    data = {'action': action,
            'instance_uuid': uuid,
            'task_id': task_id_2,
            'request_id': request_id,
            'user_id': user_id,
            'status': status,
            'message': message,
            'finish_time':finish_time
            }
    return instance_action.add_instance_actions_test(data)


def update_disk_action_to_database(request_id, action, status, message):
    return instance_action.update_instance_actions(request_id, action, status, message)

def add_disk_extend_to_database(size, dev_name, instance_id, mount_point=None):
    instance_disk_data = {
        'instance_id': instance_id,
        'size_gb': size,
        'dev_name': dev_name,
        'mount_point': mount_point,
        'isdeleted': '0',
        'created_at': get_datetime_str()
    }
    task_id = ins_s.generate_task_id()
    ret9 = ins_d_s.InstanceDiskService().add_instance_disk_info(instance_disk_data)
    if ret9.get('row_num') <= 0:
        logging.info('task %s : pre add instance_disk info that has only one system disk error when create '
                     'instance, insert_data: %s', task_id, instance_disk_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    logging.info('task %s : pre insert instance_disk table that has only one system disk successful when '
                 'create instance', task_id)

def update_disk_extend_to_database(size, dev_name,instance_id):
    update_data = {
        'size_gb': size,
        'updated_at': get_datetime_str()
    }
    where_data = {
        'instance_id': instance_id,
        'dev_name': dev_name
    }
    ret = ins_d_s.InstanceDiskService().update_instance_disk_info(update_data,
                                                                  where_data)
def get_instance_disk_by_mount_point(mount_point, instance_id):
    ret_status, ret_data = ins_d_s.get_instance_action_by_mount(mount_point, instance_id)
    return ret_status, ret_data

def get_info_by_mount_and_disk(mount_point, dev_name, instance_id):
    ret_status, ret_data = ins_d_s.get_info_by_mount_and_disk(mount_point, dev_name, instance_id)
    return ret_status, ret_data

def update_instance_status(status, id):
    update_data = {
        'status': status,
        'updated_at': get_datetime_str()
    }
    where_data = {
        'id': id,
    }
    ret = ins_s.InstanceService().update_instance_info(update_data, where_data)

