# coding=utf8
'''
    虚拟机迁移的实际函数
'''
from lib.shell.ansibleCmdV2 import host_run_shell
from service.s_host import host_schedule_service as host_s_s
from service.s_instance import instance_host_service as ins_h_s, instance_service as ins_s, \
    instance_migrate_service as ins_m_s
from service.s_instance_action.instance_action import add_instance_actions, update_instance_actions
from service.s_instance.instance_service import InstanceService
from helper.time_helper import get_datetime_str
from lib.shell.modules.migrateAnsibleCmd import ansible_migrate_qos_speed, ansible_migrate_vol_get, ansible_change_migrate_dir, \
    ansible_migrate_cancel_qos_speed, ansible_migrate_md5_get
from lib.vrtManager.instanceManager import libvirt_instance_undefined
import threading
import time
import logging
import json_helper
from model.const_define import InstaceActions, ActionStatus, MigrateStatus, VMStatus
from lib.vrtManager import instanceManager
from lib.other import fileLock


def cold_migrate(msg_data):
    '''
        虚机冷迁移
    :param msg_data:
    :return:
    '''
    msg = json_helper.read(msg_data)
    data = msg.get('data')

    request_id = data.get('request_id')
    # migarte表ID
    migrate_tab_id = data.get('migrate_tab_id')
    speed_limit = data.get('speed_limit')
    ins_data_s = data.get('ins_data_s')
    host_data_d = data.get('host_data_d')
    host_data_s = data.get('host_data_s')

    host_ip_d = host_data_d['ipaddress']
    host_id_d = host_data_d['id']
    host_name_d = host_data_d['name']

    host_ip_s = host_data_s['ipaddress']
    host_id_s = host_data_s['id']
    host_name_s = host_data_s['name']

    ins_id_s = ins_data_s['id']
    ins_uuid_s = ins_data_s['uuid']
    ins_name_s = ins_data_s['name']

    user_id = data.get('user_id')

    # todo:先判断该VM是否存在
    data = {'action': InstaceActions.INSTANCE_COLD_MIGRATE_CONFIRM_SPEED,
            'instance_uuid': ins_uuid_s,
            'request_id': request_id,
            'user_id': user_id,
            'message': 'start'
            }
    add_instance_actions(data)

    m_flag, m_speed = _confirm_migrate_speed(speed_limit, host_data_s)
    if not m_flag:
        message = 'source host %s confirm migrate speed %s error' % (host_id_s, speed_limit)
        logging.error(message)
        _change_migrate_host(host_id_s, host_name_s, ins_id_s)
        update_instance_actions(request_id, InstaceActions.INSTANCE_COLD_MIGRATE_CONFIRM_SPEED,
                                ActionStatus.FAILD, message)
        ins_m_s.InstanceMigrateService().change_migrate_status(migrate_tab_id, MigrateStatus.FAILED)
        return
    else:
        message = 'source host %s confirm migrate speed %s successful' % (host_id_s, speed_limit)
        update_instance_actions(request_id, InstaceActions.INSTANCE_COLD_MIGRATE_CONFIRM_SPEED,
                                ActionStatus.SUCCSESS, message)

    ret_s = ansible_migrate_qos_speed(host_ip_s, host_ip_d, m_speed)
    if not ret_s:
        message = 'host %s ansible migrate qos speed %s Mbit/s error' % (host_ip_d, m_speed)
        logging.error(message)
        _change_migrate_host(host_id_s, host_name_s, ins_id_s)
        update_instance_actions(request_id, InstaceActions.INSTANCE_COLD_MIGRATE_CONFIRM_SPEED,
                                ActionStatus.FAILD, message)
        ins_m_s.InstanceMigrateService().change_migrate_status(migrate_tab_id, MigrateStatus.FAILED)
        return
    else:
        message = 'host %s ansible migrate qos speed %s Mbit/s successful' % (host_ip_d, m_speed)
        update_instance_actions(request_id, InstaceActions.INSTANCE_COLD_MIGRATE_CONFIRM_SPEED,
                                ActionStatus.SUCCSESS, message)

    # 开始迁移前获取源端vol、xml文件md5
    data = {'action': InstaceActions.INSTANCE_COLD_MIGRATE_VOL_XML_MD5_S,
            'instance_uuid': ins_uuid_s,
            'request_id': request_id,
            'user_id': user_id,
            'message': 'start'
            }
    add_instance_actions(data)

    ins_vol_md5_cmd = 'cd /app/image/' + ins_uuid_s + ';/bin/md5sum *'
    ins_xml_md5_cmd = 'cd /etc/libvirt/qemu;/bin/md5sum ' + ins_data_s['name'] + '.xml'
    ret_v_m, ins_vol_md5_s = ansible_migrate_md5_get(host_ip_s, ins_vol_md5_cmd)
    if not ret_v_m:
        message = 'host %s get migrate vol md5 error' % host_id_s
        logging.error(message)
        _change_migrate_host(host_id_s, host_name_s, ins_id_s)
        update_instance_actions(request_id, InstaceActions.INSTANCE_COLD_MIGRATE_VOL_XML_MD5_S,
                                ActionStatus.FAILD, message)
        ins_m_s.InstanceMigrateService().change_migrate_status(migrate_tab_id, MigrateStatus.FAILED)
        return
    else:
        message = 'host %s get migrate vol md5 successful' % host_id_s
        update_instance_actions(request_id, InstaceActions.INSTANCE_COLD_MIGRATE_VOL_XML_MD5_S,
                                ActionStatus.SUCCSESS, message)

    ret_x_m, ins_xml_md5_s = ansible_migrate_md5_get(host_ip_s, ins_xml_md5_cmd)
    if not ret_x_m:
        message = 'host %s get migrate xml md5 error' % host_id_s
        logging.error(message)
        _change_migrate_host(host_id_s, host_name_s, ins_id_s)
        update_instance_actions(request_id, InstaceActions.INSTANCE_COLD_MIGRATE_VOL_XML_MD5_S,
                                ActionStatus.FAILD, message)
        ins_m_s.InstanceMigrateService().change_migrate_status(migrate_tab_id, MigrateStatus.FAILED)
        return
    else:
        message = 'host %s get migrate xml md5 successful' % host_id_s
        update_instance_actions(request_id, InstaceActions.INSTANCE_COLD_MIGRATE_VOL_XML_MD5_S,
                                ActionStatus.SUCCSESS, message)

    # 在目标主机上新建虚拟机镜像存储目录
    data = {'action': InstaceActions.INSTANCE_COLD_MIGRATE_MKDIR_DIR,
            'instance_uuid': ins_uuid_s,
            'request_id': request_id,
            'user_id': user_id,
            'message': 'start'
            }
    add_instance_actions(data)

    ret_status, ret_middle_status, ret_msg = __ansible_remote_mkdir_instance_dir(host_ip_d, ins_uuid_s)
    if not ret_status:
        message = 'host %s remote mkdir instance %s dir error' % (host_ip_d, ins_uuid_s)
        logging.error(message)
        _change_migrate_host(host_id_s, host_name_s, ins_id_s)
        update_instance_actions(request_id, InstaceActions.INSTANCE_COLD_MIGRATE_MKDIR_DIR,
                                ActionStatus.FAILD, message)
        ins_m_s.InstanceMigrateService().change_migrate_status(migrate_tab_id, MigrateStatus.FAILED)
        return
    else:
        message = 'host %s remote mkdir instance %s dir successful' % (host_ip_d, ins_uuid_s)
        update_instance_actions(request_id, InstaceActions.INSTANCE_COLD_MIGRATE_MKDIR_DIR,
                                ActionStatus.SUCCSESS, message)

    # 新建虚拟机池
    data = {'action': InstaceActions.INSTANCE_COLD_MIGRATE_STORAGE_POOL,
            'instance_uuid': ins_uuid_s,
            'request_id': request_id,
            'user_id': user_id,
            'message': 'start'
            }
    add_instance_actions(data)

    logging.info('start create storage pool %s', ins_uuid_s)
    ret_p = _create_storage_pool(host_ip_d, ins_uuid_s)
    if not ret_p:
        message = 'host %s create storage pool error' % host_ip_d
        logging.error(message)
        _change_migrate_host(host_id_s, host_name_s, ins_id_s)
        update_instance_actions(request_id, InstaceActions.INSTANCE_COLD_MIGRATE_STORAGE_POOL,
                                ActionStatus.FAILD, message)
        ins_m_s.InstanceMigrateService().change_migrate_status(migrate_tab_id, MigrateStatus.FAILED)
        return
    else:
        message = 'host %s create storage pool successful' % host_ip_d
        update_instance_actions(request_id, InstaceActions.INSTANCE_COLD_MIGRATE_STORAGE_POOL,
                                ActionStatus.SUCCSESS, message)

    # 拷贝vol和xml文件
    data = {'action': InstaceActions.INSTANCE_COLD_MIGRATE_VOL_XML_COPY,
            'instance_uuid': ins_uuid_s,
            'request_id': request_id,
            'user_id': user_id,
            'message': 'start'
            }
    add_instance_actions(data)

    ret_c = _copy_vol_and_xml(host_id_s, host_ip_s, host_id_d, host_ip_d, ins_uuid_s, ins_data_s['name'])
    if not ret_c:
        message = 'copy vol and xml from %s to %s error' % (host_ip_s, host_ip_d)
        logging.error(message)
        _change_migrate_host(host_id_s, host_name_s, ins_id_s)
        update_instance_actions(request_id, InstaceActions.INSTANCE_COLD_MIGRATE_VOL_XML_COPY,
                                ActionStatus.FAILD, message)
        ins_m_s.InstanceMigrateService().change_migrate_status(migrate_tab_id, MigrateStatus.FAILED)
        return
    else:
        message = 'copy vol and xml from %s to %s successful' % (host_ip_s, host_ip_d)
        update_instance_actions(request_id, InstaceActions.INSTANCE_COLD_MIGRATE_VOL_XML_COPY,
                                ActionStatus.SUCCSESS, message)

    # todo:先判断该VM是否存在
    # 查看拷贝后目的端主机文件md5是否与源端一致
    data = {'action': InstaceActions.INSTANCE_COLD_MIGRATE_VOL_XML_MD5_D,
            'instance_uuid': ins_uuid_s,
            'request_id': request_id,
            'user_id': user_id,
            'message': 'start'
            }
    add_instance_actions(data)

    ret_v_m, ins_vol_md5_d = ansible_migrate_md5_get(host_ip_d, ins_vol_md5_cmd)
    if not ret_v_m:
        message = 'get migrate destination %s vol md5 error' % host_ip_d
        logging.error(message)
        _change_migrate_host(host_id_s, host_name_s, ins_id_s)
        update_instance_actions(request_id, InstaceActions.INSTANCE_COLD_MIGRATE_VOL_XML_MD5_D,
                                ActionStatus.FAILD, message)
        ins_m_s.InstanceMigrateService().change_migrate_status(migrate_tab_id, MigrateStatus.FAILED)
        return
    else:
        message = 'get migrate destination %s vol md5 successful' % host_ip_d
        update_instance_actions(request_id, InstaceActions.INSTANCE_COLD_MIGRATE_VOL_XML_MD5_D,
                                ActionStatus.SUCCSESS, message)

    ret_x_m, ins_xml_md5_d = ansible_migrate_md5_get(host_ip_d, ins_xml_md5_cmd)
    if not ret_x_m:
        message = 'get migrate destination %s xml md5 error' % host_ip_d
        logging.error(message)
        _change_migrate_host(host_id_s, host_name_s, ins_id_s)
        update_instance_actions(request_id, InstaceActions.INSTANCE_COLD_MIGRATE_VOL_XML_MD5_D,
                                ActionStatus.FAILD, message)
        ins_m_s.InstanceMigrateService().change_migrate_status(migrate_tab_id, MigrateStatus.FAILED)
        return
    else:
        message = 'get migrate destination %s xml md5 successful' % host_ip_d
        update_instance_actions(request_id, InstaceActions.INSTANCE_COLD_MIGRATE_VOL_XML_MD5_D,
                                ActionStatus.SUCCSESS, message)

    # 比对
    data = {'action': InstaceActions.INSTANCE_COLD_MIGRATE_MD5_MATCH,
            'instance_uuid': ins_uuid_s,
            'request_id': request_id,
            'user_id': user_id,
            'message': 'start'
            }
    add_instance_actions(data)

    if ins_vol_md5_d != ins_vol_md5_s or ins_xml_md5_d != ins_xml_md5_s:
        message = 'vol or xml md5 not match, vol_s:%s, vol_d:%s, xml_s:%s, xml_d:%s' % \
                  (ins_vol_md5_s, ins_vol_md5_d, ins_xml_md5_s, ins_xml_md5_d)
        logging.error(message)
        _change_migrate_host(host_id_s, host_name_s, ins_id_s)
        update_instance_actions(request_id, InstaceActions.INSTANCE_COLD_MIGRATE_MD5_MATCH,
                                ActionStatus.FAILD, message)
        ins_m_s.InstanceMigrateService().change_migrate_status(migrate_tab_id, MigrateStatus.FAILED)
        return
    else:
        message = 'vol or xml md5 match successful, vol_s:%s, vol_d:%s, xml_s:%s, xml_d:%s' % \
                  (ins_vol_md5_s, ins_vol_md5_d, ins_xml_md5_s, ins_xml_md5_d)
        update_instance_actions(request_id, InstaceActions.INSTANCE_COLD_MIGRATE_MD5_MATCH,
                                ActionStatus.SUCCSESS, message)

    # 在目标主机上定义迁移后虚拟机
    data = {'action': InstaceActions.INSTANCE_COLD_MIGRATE_DEFINE_D,
            'instance_uuid': ins_uuid_s,
            'request_id': request_id,
            'user_id': user_id,
            'message': 'start'
            }
    add_instance_actions(data)

    ret_status, ret_middle_status, ret_msg = __ansible_migrate_instance_define(host_ip_d, ins_name_s)
    if not ret_status:
        message = 'dest host %s define migrate instance error' % host_ip_d
        logging.error(message)
        _change_migrate_host(host_id_s, host_name_s, ins_id_s)
        update_instance_actions(request_id, InstaceActions.INSTANCE_COLD_MIGRATE_DEFINE_D,
                                ActionStatus.FAILD, message)
        ins_m_s.InstanceMigrateService().change_migrate_status(migrate_tab_id, MigrateStatus.FAILED)
        return
    else:
        message = 'dest host %s define migrate instance successful' % host_ip_d
        update_instance_actions(request_id, InstaceActions.INSTANCE_COLD_MIGRATE_DEFINE_D,
                                ActionStatus.SUCCSESS, message)

    # 这里之后的步骤都是在成功将VM迁移到目标host上后对源host的操作，所以接下来每一步如果出错都不将VM的host ip改回源host
    # 将虚拟机和存储池在源宿主机上undefined
    data = {'action': InstaceActions.INSTANCE_COLD_MIGRATE_UNDEFINE_S,
            'instance_uuid': ins_uuid_s,
            'request_id': request_id,
            'user_id': user_id,
            'message': 'start'
            }
    add_instance_actions(data)

    ret_u = libvirt_instance_undefined(host_ip_s, ins_data_s)
    if not ret_u:
        message = 'source host %s undefined instance error' % host_id_s
        logging.error(message)
        update_instance_actions(request_id, InstaceActions.INSTANCE_COLD_MIGRATE_UNDEFINE_S,
                                ActionStatus.FAILD, message)
        ins_m_s.InstanceMigrateService().change_migrate_status(migrate_tab_id, MigrateStatus.FAILED)
        return
    else:
        message = 'source host %s undefined instance successful' % host_id_s
        update_instance_actions(request_id, InstaceActions.INSTANCE_COLD_MIGRATE_UNDEFINE_S,
                                ActionStatus.SUCCSESS, message)

    # 修改原虚拟机存储目录名字
    data = {'action': InstaceActions.INSTANCE_COLD_MIGRATE_BACKUP_NAME,
            'instance_uuid': ins_uuid_s,
            'request_id': request_id,
            'user_id': user_id,
            'message': 'start'
            }
    add_instance_actions(data)

    ret_d = ansible_change_migrate_dir(host_ip_s, host_ip_d, ins_uuid_s)
    if not ret_d:
        message = 'source host %s backup dir after migrate error' % host_id_s
        logging.error(message)
        update_instance_actions(request_id, InstaceActions.INSTANCE_COLD_MIGRATE_BACKUP_NAME,
                                ActionStatus.FAILD, message)
        ins_m_s.InstanceMigrateService().change_migrate_status(migrate_tab_id, MigrateStatus.FAILED)
        return
    else:
        message = 'source host %s backup dir after migrate successful' % host_id_s
        update_instance_actions(request_id, InstaceActions.INSTANCE_COLD_MIGRATE_BACKUP_NAME,
                                ActionStatus.SUCCSESS, message)

    # 迁移后取消限速
    data = {'action': InstaceActions.INSTANCE_COLD_MIGRATE_CANCEL_SPEED,
            'instance_uuid': ins_uuid_s,
            'request_id': request_id,
            'user_id': user_id,
            'message': 'start'
            }
    add_instance_actions(data)

    ret_c = ansible_migrate_cancel_qos_speed(host_ip_s)
    if not ret_c:
        message = 'source host %s cancel set migrate speed error' % host_id_s
        logging.error(message)
        update_instance_actions(request_id, InstaceActions.INSTANCE_COLD_MIGRATE_CANCEL_SPEED,
                                ActionStatus.FAILD, message)
        ins_m_s.InstanceMigrateService().change_migrate_status(migrate_tab_id, MigrateStatus.FAILED)
        return
    else:
        message = 'source host %s cancel set migrate speed successful' % host_id_s
        update_instance_actions(request_id, InstaceActions.INSTANCE_COLD_MIGRATE_CANCEL_SPEED,
                                ActionStatus.SUCCSESS, message)

    ret_u = ins_m_s.InstanceMigrateService().change_migrate_status(migrate_tab_id, MigrateStatus.SUCCESS)
    if ret_u != 1:
        logging.error('update instance migrate info error when after cold migrate instance')

    # 迁移后修改虚拟机状态为关机中
    vm_cold_migrate_status = VMStatus.SHUTDOWN
    _update_instance_status(ins_uuid_s, vm_cold_migrate_status)


def _update_instance_status(uuid, vm_status):
    update_data = {
        'status': vm_status,
        'updated_at': get_datetime_str()
    }
    where_data = {
        'uuid': uuid
    }
    return InstanceService().update_instance_info(update_data, where_data)


def _confirm_migrate_speed(speed_limit, host_s):
    '''
        确定源主机的迁移速度
    :param speed_limit:
    :param host_s:
    :return:
    '''
    # 目标主机的性能数据
    host_used_d = host_s_s.get_host_used(host_s)
    # 迁移前限速，根据网络使用率调整迁移速率为（网络带宽-当前使用上传带宽）* 0.8
    # 总带宽 - 已使用带宽 = 剩余带宽，然后只使用80%，这相当最大理论值
    net_speed = (int(host_used_d["net_size"]) -
                 int(host_used_d["current_net_tx_used"]) * int(host_used_d["net_size"])) * 0.8
    # 取两者最小值
    migrate_speed = int(net_speed) if int(speed_limit) > int(net_speed) else int(speed_limit)
    # 迁移速度最小确保20MByte = 160 Mbit
    migrate_speed = migrate_speed if migrate_speed > 160 else 160

    return True, migrate_speed


def _copy_vol_and_xml(host_id_s, host_ip_s, host_id_d, host_ip_d, ins_uuid_s, ins_name_s):
    '''
        vol和xml文件拷贝
    :param host_id_s:
    :param host_ip_s:
    :param host_id_d:
    :param host_ip_d:
    :param ins_uuid_s:
    :param ins_name_s:
    :return:
    '''

    @fileLock.file_lock('cold_migrate_nc_port')
    def _get_nc_port(src_host_id, dst_host_id):
        '''
            获取指定源主机上可用的端口
        :param src_host_id:
        :param dst_host_id:
        :return:
        '''
        port_list = ins_m_s.InstanceMigrateService().get_host_using_nc_port(src_host_id)
        # 迁移的端口范围为9000 - 10000
        for i in range(9000, 10000):
            if i not in port_list:
                nc_port = i

                # 更新端口
                update_data = {
                    'nc_port': i
                }
                where_data = {
                    'src_host_id': src_host_id,
                    'dst_host_id': dst_host_id,
                    'migrate_status': '0'
                }
                ret = ins_m_s.InstanceMigrateService().update_instance_migrate_info(update_data, where_data)
                break
        return nc_port

    # 迁移端口
    nc_transfer_port = _get_nc_port(host_id_s, host_id_d)
    if _copy_vol(nc_transfer_port, host_ip_s, host_ip_d, ins_uuid_s) \
            and _copy_xml(nc_transfer_port, host_ip_s, host_ip_d, ins_name_s):
        return True
    return False


def _copy_vol(nc_transfer_port, host_ip_s, host_ip_d, ins_uuid_s):
    '''
        vol文件拷贝
    :param nc_transfer_port:
    :param host_ip_s:
    :param host_ip_d:
    :param ins_uuid_s:
    :return:
    '''
    threads = []
    # 获取源物理机上虚拟机卷名称，用于下面一步的数据拷贝
    ret_flag_g, ins_vol_s = ansible_migrate_vol_get(host_ip_s, ins_uuid_s)
    if not ret_flag_g:
        return False

    logging.info('start to copy img disk from source host to destination host')
    # 存储文件拷贝
    for _ins_vol in ins_vol_s:
        ins_vol_server_get_d = 'cd /app/image/' + ins_uuid_s + ';/bin/nc -l -4 ' \
                               + str(nc_transfer_port) + ' > ' + _ins_vol
        ins_vol_server_send_s = 'cd /app/image/' + ins_uuid_s + ';/bin/nc -4 ' \
                                + host_ip_d + ' ' + str(nc_transfer_port) + ' < ' + _ins_vol
        # 多线程启动nc拷贝镜像文件
        t_vol_host_d = threading.Thread(target=__ansible_migrate_volumes_get, args=(host_ip_d, ins_vol_server_get_d,7200))
        threads.append(t_vol_host_d)
        t_vol_host_d.start()

        time.sleep(5)

        t_vol_host_s = threading.Thread(target=__ansible_migrate_volumes_get, args=(host_ip_s, ins_vol_server_send_s,7200))
        threads.append(t_vol_host_s)
        t_vol_host_s.start()

        # 判断多线程是否结束
        for t in threads:
            t.join()
    logging.info('copy img disk from source host to destination host successful')

    return True


def _copy_xml(nc_transfer_port, host_ip_s, host_ip_d, ins_name_s):
    '''
        xml文件拷贝
    :param nc_transfer_port:
    :param host_ip_s:
    :param host_ip_d:
    :param ins_name_s:
    :return:
    '''
    threads = []
    logging.info('start to copy xml file from source host %s to destination host %s', host_ip_s, host_ip_d)
    ins_xml_server_get_d = 'cd /etc/libvirt/qemu;/bin/nc -l -4 ' + str(nc_transfer_port) + ' > ' + ins_name_s + '.xml'
    ins_xml_server_send_s = 'cd /etc/libvirt/qemu;/bin/nc -4 ' + host_ip_d + ' ' + str(
        nc_transfer_port) + ' < ' + ins_name_s + '.xml'
    # 多线程启动nc拷贝xml文件
    t_xml_host_d = threading.Thread(target=__ansible_migrate_file_get, args=(host_ip_d, ins_xml_server_get_d))
    threads.append(t_xml_host_d)
    t_xml_host_d.start()

    time.sleep(5)

    t_xml_host_s = threading.Thread(target=__ansible_migrate_file_get, args=(host_ip_s, ins_xml_server_send_s))
    threads.append(t_xml_host_s)
    t_xml_host_s.start()

    # 判断多线程是否结束
    for t in threads:
        t.join()
    logging.info('copy xml file from source host %s to destination host %s successful', host_ip_s, host_ip_d)
    return True


def _create_storage_pool(host_ip, uuid):
    '''
        创建存储池
    :param host_ip:
    :param uuid:
    :return:
    '''
    connect_storages = instanceManager.libvirt_get_connect(host_ip, conn_type='storages')
    pool_status, pool_name = instanceManager.libvirt_create_storage_pool(connect_storages, uuid)
    if pool_status:
        return True
    return False


def _change_migrate_host(host_id_s, host_name_s, ins_id_s):
    '''
        当迁移失败后将host修改回源host
    :param host_id_s:
    :param host_name_s:
    :param ins_id_s:
    :return:
    '''
    update_data = {
        'host_id': host_id_s,
        'host_name': host_name_s,
        'updated_at': get_datetime_str()
    }
    where_data = {
        'isdeleted': '0',
        'instance_id': ins_id_s
    }
    ret = ins_h_s.InstanceHostService().update_instance_host_info(update_data, where_data)
    if ret != 1:
        logging.error('update instance host info error when cold migrate, update_data:%s, where_data:%s',
                      update_data, where_data)

def __ansible_migrate_volumes_get(host_ip, cmd, timeout):
    '''
        获取迁移文件
    :param host_ip:
    :param cmd:
    :param task_id:
    :param timeout:
    :return:
    '''
    ret_status, ret_middle_status, ret_msg = host_run_shell(host_ip, cmd, timeout=timeout)
    if not ret_status:
        return False
    return True

def __ansible_migrate_file_get(host_ip, cmd):
    '''
        获取迁移文件
    :param host_ip:
    :param cmd:
    :param task_id:
    :param timeout:
    :return:
    '''
    ret_status, ret_middle_status, ret_msg = host_run_shell(host_ip, cmd)
    if not ret_status:
        return False
    return True


def __ansible_remote_mkdir_instance_dir(dest_host_ip, dir_name):
    '''
        目标物理机上创建虚拟机存储目录
    :param dest_host_ip:
    :param dir_name:
    :return:
    '''
    command = "/bin/mkdir -p /app/image/%s" % dir_name
    return host_run_shell(dest_host_ip, command)

def __ansible_migrate_instance_define(host_ip_d, ins_name):
    '''
        目标物理机上通过xml文件创建虚拟机
    :param host_ip_d:
    :param ins_name:
    :return:
    '''
    command = 'cd /etc/libvirt/qemu;/bin/virsh define ' + ins_name + '.xml'
    return host_run_shell(host_ip_d, command)