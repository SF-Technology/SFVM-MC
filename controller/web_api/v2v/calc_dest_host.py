# coding=utf8
'''
    v2v-筛选目标host
'''
# __author__ = 'anke'

import logging
from model.const_define import ErrorCode
from helper import  json_helper
from service.s_host import host_service as host_s, host_schedule_service as host_s_s
from service.s_hostpool import hostpool_service
from service.s_instance import instance_migrate_service


def calc_dest_host(hostpool_id,vm_cpu,vm_mem,vm_disk,group_id):
    '''
            筛选host
        :param hostpool_id:
        :return:
        '''
    #入参完全性判断
    vmcpu = vm_cpu
    vmmem = vm_mem
    vmdisk = int(vm_disk) + 80

    if not hostpool_id  or not vmcpu or not vmmem or not vmdisk :
        logging.info('params are invalid or missing')
        code = ErrorCode.PARAM_ERR
        data = None
        msg = '参数错误'
        return code,data,msg


    # 获取主机列表
    all_hosts_nums, all_hosts_data = host_s.HostService().get_hosts_of_hostpool(hostpool_id)

    # 可用物理机数量不足
    least_host_num = hostpool_service.HostPoolService().get_least_host_num(hostpool_id)
    if all_hosts_nums < least_host_num or all_hosts_nums < 1:
        logging.info('not enough host in cluster')
        code = ErrorCode.SYS_ERR
        data = ''
        msg = '集群不够资源，无法进行v2v操作'
        return code, data, msg

    # 取得host_list
    hosts_after_filter = host_s_s.filter_hosts(all_hosts_data)
    if len(hosts_after_filter) == 0:
        logging.info('no host have free resource in cluster ')
        code = ErrorCode.SYS_ERR
        data = ''
        msg = '没有适合的主机，无法进行v2v操作'
        return code, data, msg
    vm = {
        "vcpu": vmcpu,
        "mem_MB": vmmem,
        "disk_GB": vmdisk,
        "count":'1',
        "group_id":group_id
    }
    host_list = host_s_s.match_hosts(hosts_after_filter, vm, least_host_num=least_host_num, max_disk=2000)
    host_len = len(host_list)
    if host_len == 0:
        logging.info('no host have enough resouce for the target vm')
        code = ErrorCode.SYS_ERR
        data = ''
        msg = '主机资源不满足v2v虚拟机，无法进行v2v操作'
        return code, data, msg
    else:
        logging.info('the host resource has been worked out')
        hosts_on_task_num,hosts_on_task = instance_migrate_service.InstanceMigrateService().get_host_on_task()
        host_on_task_list = []
        for h in hosts_on_task:
            host_on_task_list.append(h['dst_host_id'])
        for host in host_list:
            if host['id'] in host_on_task_list:
                host_list.pop(host)
        if host_list[0] == '':
            logging.info('the filted hosts are all having task for migrate or v2v,no free one')
            code = ErrorCode.SYS_ERR
            data = ''
            msg = '匹配主机均在迁移或v2v任务中，无法进行v2v操作'
            return code, data, msg
        else:
            dest_host_ip =host_list[0]['ipaddress']
            logging.info('the suitable host for v2v has been workd out '+ dest_host_ip)
            msg = "已找到匹配主机"
            data = dest_host_ip
            code = ErrorCode.SUCCESS
            return code, data, msg



















