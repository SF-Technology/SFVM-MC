# coding=utf8
'''
    收集instance数据、状态
'''


from service.s_instance import instance_service as ins_s
from service.s_host import host_service as host_s
from lib.vrtManager.instanceManager import libvirt_get_connect, libvirt_get_all_instances_by_host
import logging
from model.const_define import VMStatus, VMLibvirtStatus
from helper.time_helper import get_datetime_str, get_timestamp, change_datetime_to_timestamp
from collect_data.base import check_collect_time_out_interval
from config.default import INSTANCE_STATUS_NOT_UPDATE


def get_collect_hosts(interval=60, nums=20):
    '''
        获取前20个上次收集时间最久远并且超过了时间间隔的host
    :param interval:
    :param nums:
    :return:
    '''
    params = {
        'WHERE_AND': {
            '=': {
                'isdeleted': '0',
            },
        },
        'ORDER': [
            ['instances_collect_time', 'asc']
        ],
    }
    hosts_list = []
    hosts_nums, hosts_data = host_s.HostService().query_data(**params)
    for _host in hosts_data:
        if check_collect_time_out_interval(_host['instances_collect_time'], interval) and len(hosts_list) <= nums:
            hosts_list.append(_host)

    return hosts_list


def collect_instances_data(host_ip):
    '''
        收集指定主机下所有instance的信息
    :param host_ip:
    :return:
    '''
    print '*' * 40
    print 'start colletc host ' + host_ip + ' instance data at ' + get_datetime_str()

    libvirt_connect_instance = libvirt_get_connect(host=host_ip, conn_type='instances')
    # libvirt连接不上时需要将host下面所有虚拟机状态改为错误
    if not libvirt_connect_instance:
        logging.error('unable to connect host %s when collect data', host_ip)
        instances = ins_s.get_instances_by_host_ip(host_ip)
        for _ins in instances:
            _ins_data = ins_s.InstanceService().get_instance_info_by_uuid(_ins['uuid'])
            if not _ins_data:
                logging.warn('libvirt instance uuid %s , but not exist in db when collect data', _ins['uuid'])
                continue

            # 创建中虚拟机做判断，如果处于创建中大于45分钟，更新虚拟机状态为创建失败
            if _ins_data['status'] == VMStatus.CREATING:
                check_vm_create_status = _check_vm_creating_time(_ins_data['created_at'])
                if check_vm_create_status:
                    # 如果是克隆创建的vm则更新状态为克隆创建失败
                    if _ins_data['clone_source_host']:
                        _update_data_i = {
                            'status': VMStatus.CLONE_CREATE_ERROR,
                            'updated_at': get_datetime_str()
                        }
                        _where_data_i = {
                            'uuid': _ins['uuid']
                        }
                        ret_i_create = ins_s.InstanceService().update_instance_info(_update_data_i, _where_data_i)
                        if ret_i_create != 1:
                            logging.error(
                                'update instance %s data error when collect instance data, update_data:%s, where_data:%s',
                                _ins['uuid'], _update_data_i, _where_data_i)
                    else:
                        _update_data_i = {
                            'status': VMStatus.CREATE_ERROR,
                            'updated_at': get_datetime_str()
                        }
                        _where_data_i = {
                            'uuid': _ins['uuid']
                        }
                        ret_i_create = ins_s.InstanceService().update_instance_info(_update_data_i, _where_data_i)
                        if ret_i_create != 1:
                            logging.error(
                                'update instance %s data error when collect instance data, update_data:%s, where_data:%s',
                                _ins['uuid'], _update_data_i, _where_data_i)
                        continue

            # 虚拟机处于创建中状态小于45分钟、并且虚拟机状态被放到不更新状态列表中
            if _ins_data['status'] in INSTANCE_STATUS_NOT_UPDATE:
                logging.info('not update instance %s status when in status %s', _ins['uuid'], _ins_data['status'])
                continue

            # 如果是v2v机器、状态为转化中则不更新状态
            if _ins_data['status'] == VMStatus.CONVERTING:
                logging.info('not update instance %s status when in status %s', _ins['uuid'], _ins_data['status'])
                continue

            _update_data_i = {
                'status': VMStatus.ERROR,
                'updated_at': get_datetime_str()
            }
            _where_data_i = {
                'uuid': _ins['uuid']
            }
            ret_i = ins_s.InstanceService().update_instance_info(_update_data_i, _where_data_i)
            if ret_i != 1:
                logging.error('update instance %s data error when collect instance data, update_data:%s, where_data:%s',
                              _ins['uuid'], _update_data_i, _where_data_i)
    else:
        instances = libvirt_get_all_instances_by_host(libvirt_connect_instance, host_ip)
        for _ins in instances:
            _ins_data = ins_s.InstanceService().get_instance_info_by_uuid(_ins['uuid'])
            if not _ins_data:
                logging.warn('libvirt instance uuid %s , but not exist in db when collect data', _ins['uuid'])
                continue

            # 创建中虚拟机做判断，如果处于创建中大于45分钟，更新虚拟机状态为创建失败
            if _ins_data['status'] == VMStatus.CREATING:
                check_vm_create_status = _check_vm_creating_time(_ins_data['created_at'])
                if check_vm_create_status:
                    #如果是克隆创建的vm则更新状态为克隆创建失败
                    if _ins_data['clone_source_host']:
                        _update_data_i = {
                            'status': VMStatus.CLONE_CREATE_ERROR,
                            'updated_at': get_datetime_str()
                        }
                        _where_data_i = {
                            'uuid': _ins['uuid']
                        }
                        ret_i_create = ins_s.InstanceService().update_instance_info(_update_data_i, _where_data_i)
                        if ret_i_create != 1:
                            logging.error(
                                'update instance %s data error when collect instance data, update_data:%s, where_data:%s',
                                _ins['uuid'], _update_data_i, _where_data_i)
                    else:
                        _update_data_i = {
                            'status': VMStatus.CREATE_ERROR,
                            'updated_at': get_datetime_str()
                        }
                        _where_data_i = {
                            'uuid': _ins['uuid']
                        }
                        ret_i_create = ins_s.InstanceService().update_instance_info(_update_data_i, _where_data_i)
                        if ret_i_create != 1:
                            logging.error(
                                'update instance %s data error when collect instance data, update_data:%s, where_data:%s',
                                _ins['uuid'], _update_data_i, _where_data_i)
                        continue
                    continue

            # 虚拟机处于创建中状态小于45分钟、并且虚拟机状态被放到不更新状态列表中
            if _ins_data['status'] in INSTANCE_STATUS_NOT_UPDATE:
                logging.info('not update instance %s status when in status %s', _ins['uuid'], _ins_data['status'])
                continue

            # 虚拟机处于关机中，并且虚拟机真实状态为运行中，此时不做状态更新
            if _ins_data['status'] == VMStatus.SHUTDOWN_ING and _ins['status'] != VMLibvirtStatus.SHUTDOWN:
                continue

            _update_data_i = {
                'status': _libvirt_status_2_ins_status(_ins['status']),
                'updated_at': get_datetime_str()
            }
            _where_data_i = {
                'uuid': _ins['uuid']
            }
            ret_i = ins_s.InstanceService().update_instance_info(_update_data_i, _where_data_i)
            if ret_i != 1:
                logging.error('update instance %s data error when collect instance data, update_data:%s, where_data:%s',
                              _ins['uuid'], _update_data_i, _where_data_i)

        instances = ins_s.get_instances_by_host_ip(host_ip)
        for _ins in instances:
            _ins_data = ins_s.InstanceService().get_instance_info_by_uuid(_ins['uuid'])
            if not _ins_data:
                logging.warn('libvirt instance uuid %s , but not exist in db when collect data', _ins['uuid'])
                continue

            # 创建中虚拟机做判断，如果处于创建中大于45分钟，更新虚拟机状态为创建失败
            if _ins_data['status'] == VMStatus.CREATING:
                check_vm_create_status = _check_vm_creating_time(_ins_data['created_at'])
                if check_vm_create_status:
                    # 如果是克隆创建的vm则更新状态为克隆创建失败
                    if _ins_data['clone_source_host']:
                        _update_data_i = {
                            'status': VMStatus.CLONE_CREATE_ERROR,
                            'updated_at': get_datetime_str()
                        }
                        _where_data_i = {
                            'uuid': _ins['uuid']
                        }
                        ret_i_create = ins_s.InstanceService().update_instance_info(_update_data_i, _where_data_i)
                        if ret_i_create != 1:
                            logging.error(
                                'update instance %s data error when collect instance data, update_data:%s, where_data:%s',
                                _ins['uuid'], _update_data_i, _where_data_i)
                    else:
                        _update_data_i = {
                            'status': VMStatus.CREATE_ERROR,
                            'updated_at': get_datetime_str()
                        }
                        _where_data_i = {
                            'uuid': _ins['uuid']
                        }
                        ret_i_create = ins_s.InstanceService().update_instance_info(_update_data_i, _where_data_i)
                        if ret_i_create != 1:
                            logging.error(
                                'update instance %s data error when collect instance data, update_data:%s, where_data:%s',
                                _ins['uuid'], _update_data_i, _where_data_i)

    # 更新收集时间
    _update_data_h = {
        'instances_collect_time': get_datetime_str()
    }
    _where_data_h = {
        'ipaddress': host_ip,
        'isdeleted': '0'
    }
    ret_h = host_s.HostService().update_host_info(_update_data_h, _where_data_h)
    if ret_h != 1:
        logging.error('update collect time error when collect instance data, update_data:%s, where_data:%s',
                      _update_data_h, _where_data_h)

    print 'end colletc host ' + host_ip + ' instance data at ' + get_datetime_str()
    print '*' * 40


def _libvirt_status_2_ins_status(libvirt_status):
    '''
        libvirt状态转换为instance状态
    :param libvirt_status:
    :return:
    '''
    if libvirt_status == VMLibvirtStatus.SHUTDOWN:
        return VMStatus.SHUTDOWN
    if libvirt_status == VMLibvirtStatus.STARTUP:
        return VMStatus.STARTUP
    if libvirt_status == VMLibvirtStatus.ERROR:
        return VMStatus.ERROR
    return VMStatus.OTHER


def _check_vm_creating_time(start_creating_time):
    '''
    :param start_creating_time:
    :return: True 虚拟机创建时间超过45分钟
    :return: False 虚拟机创建时间小于等于2小时
    '''
    current_timestamp = get_timestamp() * 1000
    vm_create_start_timestamp = change_datetime_to_timestamp(start_creating_time.strftime("%Y-%m-%d %H:%M:%S"))
    if (current_timestamp - vm_create_start_timestamp)/1000 > 0.75 * 3600:
        return True
    else:
        return False



