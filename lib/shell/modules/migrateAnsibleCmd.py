# coding=utf8
'''
    虚拟机迁移ansible操作
'''
# __author__ =  ""


import logging
import traceback
from lib.shell.ansibleCmdV2 import ansible_run_shell
from helper.time_helper import get_timestamp


def ansible_migrate_qos_speed(host_ip_s, host_ip_d, migrate_speed):
    '''
        设置目标主机的迁移速度
    :param host_ip_s:
    :param host_ip_d:
    :param migrate_speed:
    :return:
    '''
    try:
        speed_cmd = 'cd /root;/bin/bash migratespeedQos ' + host_ip_d + ' ' + str(migrate_speed)
        hostlist = [host_ip_s]
        ansible_code, ansible_msg = ansible_run_shell(host_ip_s, speed_cmd)
        logging.info(ansible_msg)

        if ansible_code == 3:
            message = '连接目标KVM HOST %s 失败' % (host_ip_s)
            logging.error(message)
            return False, message

        elif ansible_code != 0:
            logging.info("set host migrate speed return: %s" %ansible_msg['np_fact_cache'][host_ip_s])
            logging.info('exec %s   failed ' % speed_cmd)
            return False
        else:
            logging.info('exec %s   success ' % speed_cmd)
            return True
    except:
        logging.error(traceback.format_exc())
        return False


def ansible_migrate_cancel_qos_speed(host_ip):
    '''
        取消host迁移速度限制
    :param host_ip:
    :param migrate_speed:
    :return:
    '''
    try:
        cancel_cmd = 'cd /root;/bin/bash deletemigratespeedQos'
        hostlist = [host_ip]
        ansible_code, ansible_msg = ansible_run_shell(host_ip, cancel_cmd)
        logging.info(ansible_msg)

        if ansible_code == 3:
            message = '连接目标KVM HOST %s 失败' % (host_ip)
            logging.error(message)
            return False, message

        elif ansible_code != 0:
            logging.info("set host migrate speed return: %s" %ansible_msg['np_fact_cache'][host_ip])
            return False
        else:
            logging.info('exec %s   success ' % cancel_cmd)
            return True
    except:
        logging.error(traceback.format_exc())
        return False


def ansible_migrate_md5_get(host_ip, cmd):
    '''
        获取迁移文件MD5
    :param host_ip:
    :param cmd:
    :return:
    '''
    try:
        hostlist = [host_ip]
        ansible_code, ansible_msg = ansible_run_shell(host_ip, cmd)
        logging.info(ansible_msg)

        if ansible_code == 3:
            message = '连接目标KVM HOST %s 失败' % (host_ip)
            logging.error(message)
            return False, message

        elif ansible_code != 0:
            logging.info("get migrate md5 return: %s" % ansible_msg['np_fact_cache'][host_ip])
            logging.info('exec %s   failed ' % cmd)
            return False, None
        else:
            logging.info('exec %s   success ' % cmd)
            return True, ansible_msg['np_fact_cache'][host_ip]['shell_out']['stdout'].split('\n')
    except:
        logging.error(traceback.format_exc())
        return False, None


def ansible_migrate_vol_get(host_ip, ins_uuid):
    '''
        获取迁移目标主机卷名称
    :param host_ip:
    :param ins_uuid:
    :return:
    '''
    try:
        vol_cmd = 'cd /app/image/' + ins_uuid + ';ls'
        hostlist = [host_ip]
        ansible_code, ansible_msg = ansible_run_shell(host_ip, vol_cmd)
        logging.info(ansible_msg)

        if ansible_code == 3:
            message = '连接目标KVM HOST %s 失败' % (host_ip)
            logging.error(message)
            return False, message

        elif ansible_code != 0:
            logging.info("get migrate host vol return: %s" % ansible_msg['np_fact_cache'][host_ip])
            logging.info('exec %s   failed ' % vol_cmd)
            return False, None
        else:
            logging.info('exec %s   success ' % vol_cmd)
            return True, ansible_msg['np_fact_cache'][host_ip]['shell_out']['stdout'].split('\n')
    except:
        logging.error(traceback.format_exc())
        return False, None



def ansible_change_migrate_dir(host_ip_s, host_ip_d, ins_uuid):
    '''
        迁移后修改目录名称
    :param host_ip_s:
    :param host_ip_d:
    :param ins_uuid:
    :return:
    '''
    try:
        bak_name = ins_uuid + '-migrate-to-' + host_ip_d + '-' + str(get_timestamp())
        dir_cmd = 'cd /app/image;/bin/mv ' + ins_uuid + ' ' + bak_name
        hostlist = [host_ip_s]
        ansible_code, ansible_msg = ansible_run_shell(host_ip_s, dir_cmd)
        logging.info(ansible_msg)

        if ansible_code == 3:
            message = '连接目标KVM HOST %s 失败' % (host_ip_s)
            logging.error(message)
            return False, message

        elif ansible_code != 0:
            logging.info("change migrate dir return: %s" % ansible_msg['np_fact_cache'][host_ip_s])
            logging.info('exec %s   failed ' % dir_cmd)
            return False
        else:
            logging.info('exec %s   success ' % dir_cmd)
            return True
    except:
        logging.error(traceback.format_exc())
        return False