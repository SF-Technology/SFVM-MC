# coding=utf8
'''
    物理机服务 - 调度策略
'''
# __author__ = ""

from service.s_instance import instance_filter, instance_service as ins_s
from service.s_host import host_metric_service as host_metric
from service.s_host import host_service as host_s
import logging
from collect_data.base import check_collect_time_out_interval
from config.default import INSTANCE_MAX_NUMS_IN_HOST


def migrate_filter_hosts(hosts_list, hostpool_host_nums):
    '''
        VM迁移筛选目标主机
    :param hosts_list:
    :param hostpool_host_nums:
    :return:
    '''
    # 获取指定host ip列表的当前使用率信息
    hosts = map(get_host_used, hosts_list)

    # 过滤器n：过滤掉没有使用情况的
    n_filter = instance_filter.none_data_filter()
    hosts = filter(n_filter, hosts)
    if not hosts:
        return {}

    # 过滤器lack：过滤掉缺失指定性能指标的
    lack_filter = instance_filter.lack_metric_key_filter()
    hosts = filter(lack_filter, hosts)
    if not hosts:
        return {}

    # 过滤器z：过滤掉mem和disk的值为0的
    z_filter = instance_filter.zero_data_filter()
    hosts = filter(z_filter, hosts)
    if not hosts:
        return {}

    # 过滤器：筛选业务状态不符合要求的
    t_filter = instance_filter.type_status_filter()
    hosts = filter(t_filter, hosts)
    if not hosts:
        return {}

    # 过滤器：筛选libvirtd状态异常的
    l_filter = instance_filter.libvirtd_status_filter()
    hosts = filter(l_filter, hosts)
    if not hosts:
        return {}

    # 过滤器c：根据当前使用率设定过滤阀值
    logging.info("步骤1 物理机使用率过滤 开始：虚拟机迁移过滤目标主机信息，总host数量%s, host信息如下%s", str(len(hosts)), hosts)
    __max_cpu = 80 - 80/hostpool_host_nums
    c_filter = instance_filter.current_used_filter(max_cpu=__max_cpu, max_mem=95, max_disk=70)
    hosts = filter(c_filter, hosts)
    logging.info("步骤1 物理机使用率过滤 结束：虚拟机迁移过滤目标主机信息，总host数量%s, host信息如下%s", str(len(hosts)), hosts)
    if not hosts:
        logging.error("虚拟机迁移过滤目标物理机使用率，每台物理机要求cpu使用率不能高于%s", str(__max_cpu))
        return {}

    # 过滤器w：内存和CPU过去一周p95值
    logging.info("步骤2 物理机p95过滤 开始：虚拟机迁移过滤目标主机信息，总host数量%s, host信息如下%s", str(len(hosts)), hosts)
    __max_cpu = 80 - 80/hostpool_host_nums
    w_filter = instance_filter.week_p95_used_filter(max_cpu=__max_cpu, max_mem=95)
    hosts = filter(w_filter, hosts)
    logging.info("步骤2 物理机p95过滤 结束：虚拟机迁移过滤目标主机信息，总host数量%s, host信息如下%s", str(len(hosts)), hosts)
    if not hosts:
        logging.error("虚拟机迁移过滤目标物理机p95，每台物理机要求cpu使用率不能高于%s", str(__max_cpu))
        return {}

    # 过滤器m：过滤存在有VM迁入的host
    m_filter = instance_filter.migrate_ing_filter()
    hosts = filter(m_filter, hosts)
    if not hosts:
        return {}

    i_filter = instance_filter.migrate_invalid_status_filter()
    hosts = filter(i_filter, hosts)
    if not hosts:
        return {}

    # 根据磁盘剩余空间排序
    hosts = sorted(hosts, key=free_disk_space)

    return hosts


def clone_filter_hosts(hosts_list, hostpool_host_nums):
    '''
        VM迁移筛选目标主机
    :param hosts_list:
    :param hostpool_host_nums:
    :return:
    '''
    # 获取指定host ip列表的当前使用率信息
    hosts = map(get_host_used, hosts_list)

    # 过滤器n：过滤掉没有使用情况的
    n_filter = instance_filter.none_data_filter()
    hosts = filter(n_filter, hosts)
    if not hosts:
        return {}

    # 过滤器lack：过滤掉缺失指定性能指标的
    lack_filter = instance_filter.lack_metric_key_filter()
    hosts = filter(lack_filter, hosts)
    if not hosts:
        return {}

    # 过滤器z：过滤掉mem和disk的值为0的
    z_filter = instance_filter.zero_data_filter()
    hosts = filter(z_filter, hosts)
    if not hosts:
        return {}

    # 过滤器：筛选业务状态不符合要求的
    t_filter = instance_filter.type_status_filter()
    hosts = filter(t_filter, hosts)
    if not hosts:
        return {}

    # 过滤器：筛选libvirtd状态异常的
    l_filter = instance_filter.libvirtd_status_filter()
    hosts = filter(l_filter, hosts)
    if not hosts:
        return {}

    # 过滤器c：根据当前使用率设定过滤阀值
    logging.info("步骤1 物理机使用率过滤 开始：虚拟机迁移过滤目标主机信息，总host数量%s, host信息如下%s", str(len(hosts)), hosts)
    __max_cpu = 80 - 80/hostpool_host_nums
    c_filter = instance_filter.current_used_filter(max_cpu=__max_cpu, max_mem=95, max_disk=70)
    hosts = filter(c_filter, hosts)
    logging.info("步骤1 物理机使用率过滤 结束：虚拟机迁移过滤目标主机信息，总host数量%s, host信息如下%s", str(len(hosts)), hosts)
    if not hosts:
        logging.error("虚拟机迁移过滤目标物理机使用率，每台物理机要求cpu使用率不能高于%s", str(__max_cpu))
        return {}

    # 过滤器w：内存和CPU过去一周p95值
    logging.info("步骤2 物理机p95过滤 开始：虚拟机迁移过滤目标主机信息，总host数量%s, host信息如下%s", str(len(hosts)), hosts)
    __max_cpu = 80 - 80/hostpool_host_nums
    w_filter = instance_filter.week_p95_used_filter(max_cpu=__max_cpu, max_mem=95)
    hosts = filter(w_filter, hosts)
    logging.info("步骤2 物理机p95过滤 结束：虚拟机迁移过滤目标主机信息，总host数量%s, host信息如下%s", str(len(hosts)), hosts)
    if not hosts:
        logging.error("虚拟机迁移过滤目标物理机p95，每台物理机要求cpu使用率不能高于%s", str(__max_cpu))
        return {}

    # 过滤器m：过滤存在有VM迁入的host
    m_filter = instance_filter.migrate_ing_filter()
    hosts = filter(m_filter, hosts)
    if not hosts:
        return {}

    i_filter = instance_filter.migrate_invalid_status_filter()
    hosts = filter(i_filter, hosts)
    if not hosts:
        return {}

    # 根据磁盘剩余空间排序
    hosts = sorted(hosts, key=free_mem_unassign)

    return hosts


def migrate_match_hosts(hosts_list, vm, group_id, least_host_num=1, max_mem=95, max_disk=70):
    '''
        检验host是否有为虚拟机提供热迁、冷迁的条件，只迁移一台
    '''

    # 过滤掉因VM申请资源而超过限定阀值的host
    hosts = map(get_host_used, hosts_list)

    logging.info('迁移VM分配host 步骤1：分配HOST，开始过滤器1：性能指标缺失过滤器 总host数：%s, '
                 'start match hosts and start lack_metric_key_filter hosts : %s', len(hosts), hosts)

    # 过滤器n：过滤掉没有使用情况的
    n_filter = instance_filter.none_data_filter()
    hosts = filter(n_filter, hosts)
    if not hosts:
        logging.error('迁移VM分配host 步骤2：性能数据空值过滤器后没有合适主机 no available host after none_data_filter')
        return {}

    # 过滤器lack：过滤掉缺失指定性能指标的
    lack_filter = instance_filter.lack_metric_key_filter()
    hosts = filter(lack_filter, hosts)
    if not hosts:
        logging.error('迁移VM分配host 步骤3：性能指标缺失过滤器后没有合适主机 no available host after lack_metric_key_filter')
        return {}

    # 过滤器z：过滤掉mem和disk的值为0的
    z_filter = instance_filter.zero_data_filter()
    hosts = filter(z_filter, hosts)
    if not hosts:
        logging.error('迁移VM分配host 步骤4：内存、磁盘空值过滤器后没有合适主机 no available host after zero_data_filter')
        return {}

    vm_fit_filter = instance_filter.fit_filter(vm, num=1, max_mem=max_mem, max_disk=max_disk)
    hosts = filter(vm_fit_filter, hosts)
    if len(hosts) == 0:
        logging.info("迁移VM分配host 步骤5：分配虚拟机到物理机后没有合适主机 no available host after fit_filter")
        return {}

    # 过滤运行有与当前虚拟机相同应用组的虚拟机所在物理机
    vm_group_filter = filter_host_with_same_group_id(group_id)
    hosts = filter(vm_group_filter, hosts)
    if len(hosts) == 0:
        logging.info("迁移VM分配host 步骤6：相同应用组物理机过滤后没有合适主机 no available host after vm_group_filter")
        return {}

    logging.info('迁移VM分配host 步骤7：结束分配资源过滤器，开始分配HOST 总host数：%s, '
                 'end fit_filter and start match hosts : %s', len(hosts), hosts)

    return hosts


def clone_match_hosts(hosts_list, vm, group_id, least_host_num=1, max_mem=95, max_disk=70):
    '''
        检验host是否有为虚拟机提供热迁、冷迁的条件，只迁移一台
    '''

    # 过滤掉因VM申请资源而超过限定阀值的host
    hosts = map(get_host_used, hosts_list)

    logging.info('迁移VM分配host 步骤1：分配HOST，开始过滤器1：性能指标缺失过滤器 总host数：%s, '
                 'start match hosts and start lack_metric_key_filter hosts : %s', len(hosts), hosts)

    # 过滤器n：过滤掉没有使用情况的
    n_filter = instance_filter.none_data_filter()
    hosts = filter(n_filter, hosts)
    if not hosts:
        logging.error('迁移VM分配host 步骤2：性能数据空值过滤器后没有合适主机 no available host after none_data_filter')
        return {}

    # 过滤器lack：过滤掉缺失指定性能指标的
    lack_filter = instance_filter.lack_metric_key_filter()
    hosts = filter(lack_filter, hosts)
    if not hosts:
        logging.error('迁移VM分配host 步骤3：性能指标缺失过滤器后没有合适主机 no available host after lack_metric_key_filter')
        return {}

    # 过滤器z：过滤掉mem和disk的值为0的
    z_filter = instance_filter.zero_data_filter()
    hosts = filter(z_filter, hosts)
    if not hosts:
        logging.error('迁移VM分配host 步骤4：内存、磁盘空值过滤器后没有合适主机 no available host after zero_data_filter')
        return {}

    vm_fit_filter = instance_filter.fit_filter(vm, num=1, max_mem=max_mem, max_disk=max_disk)
    hosts = filter(vm_fit_filter, hosts)
    if len(hosts) == 0:
        logging.info("迁移VM分配host 步骤5：分配虚拟机到物理机后没有合适主机 no available host after fit_filter")
        return {}

    # host数大于vm申请数，按同一应用组下的vm数量从小到大排序
    if int(vm["count"]) < len(hosts):
        # 同一应用的vm打散到不同host上
        group_vm_num = get_group_vm_num_in_host(vm["group_id"])
        hosts = map(group_vm_num, hosts)
        hosts = sorted(hosts, key=lambda h: h["group_vm_num"])
        return hosts
    else:
        # 获取每台物理机上最多可创建的虚拟机数量
        get_available_vm_number = count_host_available_vm_number(mem_mb=int(vm['mem_MB']), disk_gb=int(vm['disk_GB']), max_mem=max_mem, max_disk=max_disk)
        hosts = filter(get_available_vm_number, hosts)

        available_vm_nember = 0
        for per_host in hosts:
            available_vm_nember += per_host.get('available_create_vm_num', 0)

        if available_vm_nember < int(vm["count"]):
            logging.info('迁移VM分配host 步骤6：所有host可以分配的vm总数：%s, 无法满足%s台vm的创建任务', available_vm_nember, vm["count"])
            return {}

        # 按照每台物理机可以创建的虚拟机数量从大到小排序
        hosts = sorted(hosts, key=lambda h: h["available_create_vm_num"], reverse=True)
        return hosts


def configuare_filter_host(hosts_list, vm, cluster_hosts_count, max_mem=95, max_disk=70):

    '''
        查询物理机资源是否满足虚拟机修改配置
    :param hosts_list:
    :param vm:
    :param cluster_hosts_count :
    :param max_mem:
    :param max_disk:
    :return:
    '''

    # 获取指定host ip列表的当前使用率信息
    hosts = map(get_host_used, hosts_list)
    if not hosts:
        msg = '无法获取物理机性能数据，无法修改虚拟机配置'
        logging.error(msg)
        return {}, msg

    logging.info(hosts)
    # 过滤器n：过滤掉没有使用情况的
    n_filter = instance_filter.none_data_filter()
    hosts = filter(n_filter, hosts)
    if not hosts:
        msg = '物理机性能数据为空，无法修改虚拟机配置'
        return {}, msg

    # 过滤器lack：过滤掉缺失指定性能指标的
    lack_filter = instance_filter.lack_metric_key_filter()
    hosts = filter(lack_filter, hosts)
    if not hosts:
        msg = '物理机部分关键性能数据缺失，无法修改虚拟机配置'
        logging.error(msg)
        return {}, msg

    # 过滤器z：过滤掉mem和disk的值为0的
    z_filter = instance_filter.zero_data_filter()
    hosts = filter(z_filter, hosts)
    if not hosts:
        msg = '物理机性能数据中mem_size或者disk_size为空，无法修改虚拟机配置'
        logging.error(msg)
        return {}, msg

    # 过滤器a：根据当前使用率设定过滤阀值
    logging.info("步骤1 物理机使用率过滤 开始：虚拟机配置所在主机信息，总host数量%s, host信息如下%s", str(len(hosts)), hosts)
    __max_cpu = 80 - 80 / cluster_hosts_count
    a_filter = instance_filter.current_used_filter(max_cpu=__max_cpu, max_mem=95, max_disk=70)
    hosts = filter(a_filter, hosts)

    if not hosts:
        logging.error("虚拟机配置所在宿主机cpu使用率要求不大于%s", str(__max_cpu))
        msg = '物理机负载高，请把虚拟机迁移到其他物理机上再扩容'
        logging.error(msg)
        return {}, msg

    # 过滤器b：过滤不满足修改配置物理机
    lack_filter = instance_filter.lack_metric_key_filter()
    hosts = filter(lack_filter, hosts)
    if not hosts:
        msg = '物理机性能数据不完整不满足虚拟机配置更改'
        logging.error(msg)
        return {}, msg

    vm_fit_filter = instance_filter.fit_filter(vm, num=1, max_mem=max_mem, max_disk=max_disk)
    hosts = filter(vm_fit_filter, hosts)
    if len(hosts) == 0:
        msg = '物理机资源不足,请把虚拟机迁移到其他物理机上再扩容'
        logging.info(msg)
        return {}, msg

    msg = '物理机资源满足虚拟机配置修改'
    logging.info(msg)

    return hosts, msg


def filter_hosts(hosts_list):
    '''
    第一部分 使用过滤器过滤掉不符合条件的host
    '''
    # 获取指定host ip列表的当前使用率信息
    hosts = map(get_host_used, hosts_list)

    logging.info('创建VM 步骤8-1：过滤HOST，开始过滤器1：空值过滤器 总host数：%s', len(hosts))

    # 过滤器n：过滤掉没有使用情况的
    n_filter = instance_filter.none_data_filter()
    hosts = filter(n_filter, hosts)
    if not hosts:
        logging.error('创建VM 步骤8-1：空值过滤器后没有合适主机 no available host after none_data_filter')
        return {}

    logging.info('创建VM 步骤8-2：结束空值过滤器，开始过滤器2：虚拟机数量过滤器 总host数：%s', len(hosts))

    # 过滤器v：过滤掉已经有50台虚拟机的物理机，这个数值通过变量定义
    v_filter = instance_filter.instance_nums_filter(INSTANCE_MAX_NUMS_IN_HOST)
    hosts = filter(v_filter, hosts)
    if not hosts:
        logging.error('创建VM 步骤8-2：虚拟机数量过滤器后没有合适主机 no available host after instance_nums_filter')
        return {}

    logging.info('创建VM 步骤8-3：结束虚拟机数量过滤器，开始过滤器3：性能指标缺失过滤器 总host数：%s', len(hosts))

    # 过滤器lack：过滤掉缺失指定性能指标的
    lack_filter = instance_filter.lack_metric_key_filter()
    hosts = filter(lack_filter, hosts)
    if not hosts:
        logging.error('创建VM 步骤8-3：性能指标缺失过滤器后没有合适主机 no available host after lack_metric_key_filter')
        return {}

    logging.info('创建VM 步骤8-4：结束性能指标缺失过滤器，开始过滤器4：零值过滤器 总host数：%s', len(hosts))

    # 过滤器z：过滤掉mem和disk的值为0的
    z_filter = instance_filter.zero_data_filter()
    hosts = filter(z_filter, hosts)
    if not hosts:
        logging.error('创建VM 步骤8-4：零值过滤器后没有合适主机 no available host after zero_data_filter')
        return {}

    logging.info('创建VM 步骤8-5：结束零值过滤器，开始过滤器5：业务状态过滤器 总host数：%s', len(hosts))

    # 过滤器t：筛选业务状态不符合要求的
    t_filter = instance_filter.type_status_filter()
    hosts = filter(t_filter, hosts)
    if not hosts:
        logging.error('创建VM 步骤8-5：业务状态过滤器后没有合适主机 no available host after type_status_filter')
        return {}

    logging.info('创建VM 步骤8-6：结束业务状态过滤器，开始过滤器6：libvirtd状态过滤器 总host数：%s', len(hosts))

    # 过滤器l：筛选libvirtd状态异常的
    l_filter = instance_filter.libvirtd_status_filter()
    hosts = filter(l_filter, hosts)
    if not hosts:
        logging.error('创建VM 步骤8-6：libvirtd状态过滤器后没有合适主机 no available host after libvirtd_status_filter')
        return {}

    logging.info('创建VM 步骤8-7：结束libvirtd状态过滤器，开始过滤器7：当前使用率过滤器 总host数：%s', len(hosts))

    # 过滤器c：根据当前使用率设定过滤阀值
    __max_cpu = 80 - 80/len(hosts_list)
    c_filter = instance_filter.current_used_filter(max_cpu=__max_cpu, max_mem=95, max_disk=70)
    hosts = filter(c_filter, hosts)
    if not hosts:
        logging.error('创建VM 步骤8-7：当前使用率过滤器后没有合适主机 no available host after '
                      'current_used_filter，每台物理机要求cpu使用率不能超过%s', str(__max_cpu))
        return {}

    logging.info('创建VM 步骤8-8：结束当前使用率过滤器，开始过滤器8：一周P95过滤器 总host数：%s', len(hosts))

    # 过滤器w：内存和CPU过去一周p95值
    __max_cpu = 80 - 80/len(hosts_list)
    w_filter = instance_filter.week_p95_used_filter(max_cpu=__max_cpu, max_mem=95)
    hosts = filter(w_filter, hosts)
    if not hosts:
        logging.error('创建VM 步骤8-8：一周P95过滤器后没有合适主机 no available host after '
                      'week_p95_used_filter，每台物理机要求cpu使用率不能超过%s', str(__max_cpu))
        return {}

    logging.info('创建VM 步骤8-9：结束一周P95过滤器，开始根据磁盘剩余空间来排序 总host数：%s', len(hosts))

    # 根据磁盘剩余空间排序
    hosts = sorted(hosts, key=free_disk_space)
    logging.info('创建VM 步骤8-10：结束根据磁盘剩余空间排序 总host数：%s', len(hosts))
    return hosts


def match_hosts(hosts_list, vm, least_host_num=2, max_mem=95, max_disk=70):
    '''
    第二部分 检验host是否有分配资源给VM的能力
    '''
    # 用least_host_num集群最小host数来控制vm均衡分布
    if int(vm["count"]) > len(hosts_list) and len(hosts_list) < int(least_host_num):
        logging.info("vm number greater than host number, but host number less than least_host_num %s", least_host_num)
        return {}

    # 过滤掉因VM申请资源而超过限定阀值的host
    hosts = map(get_host_used, hosts_list)

    logging.info('创建VM 步骤9-1：分配HOST，开始过滤器1：性能指标缺失过滤器 总host数：%s', len(hosts))

    # 过滤器n：过滤掉没有使用情况的
    n_filter = instance_filter.none_data_filter()
    hosts = filter(n_filter, hosts)
    if not hosts:
        logging.error('创建VM 步骤9-1-1：性能数据空值过滤器后没有合适主机 no available host after none_data_filter')
        return {}

    # 过滤器lack：过滤掉缺失指定性能指标的
    lack_filter = instance_filter.lack_metric_key_filter()
    hosts = filter(lack_filter, hosts)
    if not hosts:
        logging.error('创建VM 步骤9-1-2：性能指标缺失过滤器后没有合适主机 no available host after lack_metric_key_filter')
        return {}

    logging.info('创建VM 步骤9-2：结束性能指标缺失过滤器，开始过滤器2：零值过滤器 总host数：%s', len(hosts))

    # 过滤器z：过滤掉mem和disk的值为0的
    z_filter = instance_filter.zero_data_filter()
    hosts = filter(z_filter, hosts)
    if not hosts:
        logging.error('创建VM 步骤9-2：内存、磁盘为零过滤器后没有合适主机 no available host after zero_data_filter')
        return {}

    logging.info('创建VM 步骤9-3：结束性能零值过滤器，开始过滤器3：分配资源过滤器 总host数：%s', len(hosts))

    vm_fit_filter = instance_filter.fit_filter(vm, num=1, max_mem=max_mem, max_disk=max_disk)
    hosts = filter(vm_fit_filter, hosts)
    if len(hosts) == 0 or len(hosts) < least_host_num:
        logging.info("创建VM 步骤9-3：分配资源过滤器后没有合适主机 no available host after fit_filter")
        return {}

    logging.info('创建VM 步骤9-4：结束分配资源过滤器，开始分配HOST 总host数：%s', len(hosts))

    if int(vm["count"]) == 1:
        host_without_group_list = []
        group_vm_num = get_group_vm_num_in_host(vm["group_id"])
        hosts_filter_first = map(group_vm_num, hosts)
        for _host in hosts_filter_first:
            if _host.get('group_vm_num', 0) == 0:
                host_without_group_list.append(_host)
        if len(host_without_group_list) > 0:
            # 获取每台物理机上最多可创建的虚拟机数量
            get_available_vm_number = count_host_available_vm_number(mem_mb=int(vm['mem_MB']),
                                                                     disk_gb=int(vm['disk_GB']), max_mem=max_mem,
                                                                     max_disk=max_disk)
            hosts_filter_second = filter(get_available_vm_number, host_without_group_list)
            if len(hosts_filter_second) >= int(vm["count"]):
                hosts_filter_third = sorted(hosts_filter_second, key=lambda h: h["available_create_vm_num"],
                                            reverse=True)
                hosts = hosts_filter_third[0: int(vm["count"])]
                return hosts

    # host数大于vm申请数，按同一应用组下的vm数量从小到大排序
    if int(vm["count"]) < len(hosts):
        # 同一应用的vm打散到不同host上
        group_vm_num = get_group_vm_num_in_host(vm["group_id"])
        hosts = map(group_vm_num, hosts)
        hosts = sorted(hosts, key=lambda h: h["group_vm_num"])
        hosts = hosts[0: int(vm["count"])]
        return hosts
    else:
        # 获取每台物理机上最多可创建的虚拟机数量
        get_available_vm_number = count_host_available_vm_number(mem_mb=int(vm['mem_MB']), disk_gb=int(vm['disk_GB']), max_mem=max_mem, max_disk=max_disk)
        hosts = filter(get_available_vm_number, hosts)

        available_vm_nember = 0
        for per_host in hosts:
            logging.info('创建VM 步骤9-5-1：物理机 %s 最多还可以创建虚拟机 %s 台', per_host['ipaddress'], str(int(per_host.get('available_create_vm_num', 0))))
            available_vm_nember += per_host.get('available_create_vm_num', 0)

        if available_vm_nember < int(vm["count"]):
            logging.info('创建VM 步骤9-5：所有host可以分配的vm总数：%s, 无法满足%s台vm的创建任务', available_vm_nember, vm["count"])
            return {}

        # 按照每台物理机可以创建的虚拟机数量从小到大排序
        # hosts = sorted(hosts, key=host_available_create_vm_number)

        all_vm_create = 0
        available_hosts = []
        while all_vm_create < int(vm["count"]):
            # 过滤可以创建虚拟机数量为0的物理机
            hosts_vm_number_filter = host_available_create_vm_number_filter()
            hosts = filter(hosts_vm_number_filter, hosts)
            for per_host in hosts:
                per_host['available_create_vm_num'] -= 1
                available_hosts.append(per_host)
                all_vm_create += 1

        logging.info('创建VM 步骤9-6：已完成所有host分配')
        """
        # 当host数量小于vm申请数，将不满足条件物理机踢出列表后继续判断
        while len(hosts) >= least_host_num:
            # host数小于vm申请数，按磁盘剩余空间从小到大排序
            hosts = sorted(hosts, key=free_disk_space)
            x, y = divmod(int(vm["count"]), len(hosts))
            hosts_before_filter_num = len(hosts)
            vm_fit_filter = instance_filter.fit_filter(vm, num=x, max_mem=max_mem, max_disk=max_disk)
            hosts = filter(vm_fit_filter, hosts)
            if hosts_before_filter_num != len(hosts):
                logging.info("Some host do not have enough resource1, continue to filter")
                continue

            if y != 0:
                hosts_y = hosts[0:y]
                hosts_before_filter_num = len(hosts_y)
                vm_fit_filter = instance_filter.fit_filter(vm, num=x + 1, max_mem=max_mem, max_disk=max_disk)
                hosts_y = filter(vm_fit_filter, hosts_y)
                if hosts_before_filter_num != len(hosts_y):
                    logging.info("Some host do not have enough resource2, continue to filter")
                    continue
                else:
                    return hosts
            else:
                return hosts
        """
        return available_hosts


def v2v_batch_match_host(hosts_list, vm, least_host_num=2, max_mem=95, max_disk=70):
    '''
    第二部分 检验host是否有分配资源给VM的能力
    '''
    # 用least_host_num集群最小host数来控制vm均衡分布
    if int(vm["count"]) > len(hosts_list) and len(hosts_list) < int(least_host_num):
        logging.info("vm number greater than host number, but host number less than least_host_num %s", least_host_num)
        return {}
    apply_mem = vm["apply_mem"]
    apply_disk = vm["apply_disk"]
    # 过滤掉因VM申请资源而超过限定阀值的host
    hosts = map(get_host_used, hosts_list)
    vm_fit_filter = instance_filter.v2v_batch_host_filter(apply_mem,apply_disk, max_mem=max_mem, max_disk=max_disk)
    hosts = filter(vm_fit_filter, hosts)
    if len(hosts) == 0:
        logging.info("no available host after fit_filter")
        return {}

    # host数大于vm申请数，按同一应用组下的vm数量从小到大排序
    if int(vm["count"]) < len(hosts):
        # 同一应用的vm打散到不同host上
        group_vm_num = get_group_vm_num_in_host(vm["group_id"])
        hosts = map(group_vm_num, hosts)
        hosts = sorted(hosts, key=lambda h: h["group_vm_num"])
        hosts = hosts[0: int(vm["count"])]
        return hosts
    else:
        # host数小于vm申请数，按磁盘剩余空间从小到大排序
        hosts = sorted(hosts, key=free_disk_space)
        return hosts


def free_disk_space(host):
    '''
        获取host剩余磁盘空间
    :param host:
    :return:
    '''
    free_space = int(host["disk_size"]) * (100 - int(host.get('current_disk_used', 0))) / 100
    return free_space

def free_mem_unassign(host):
    '''
        获取host剩余磁盘空间
    :param host:
    :return:
    '''
    free_percent = float(host["assign_mem"]) / float(host["mem_size"])*100
    return free_percent


def host_available_create_vm_number_filter():
    '''
        将可创建的虚拟机数量为0的物理机过滤掉
    :return:
    '''
    def x(host):
        vm_count = host.get('available_create_vm_num', 0)
        if vm_count <= 0:
            return False
        return host
    return x


def get_group_vm_num_in_host(group_id):
    '''
        获取指定host主机上指定应用组的vm数量
    '''
    def x(host):
        count = 0
        host_instances = host_s.get_instances_of_host(host['host_id'])
        for _ins in host_instances:
            _group = ins_s.get_group_of_instance(_ins['instance_id'])
            if _group and _group['group_id'] == int(group_id):
                count += 1

        host["group_vm_num"] = count
        return host

    return x


def get_host_used(host, expire=True, expire_time=600):
    '''
        获取host资源使用情况
    :param host:
    :param expire:设置True，表示获取性能数据时要考虑收集时间
    :param expire_time:超过过期时间，则认为性能数据不准确，不予采用
    :return:
    '''
    host_ip = host['ipaddress']
    # 获取性能数据
    used_data = host_s.HostService().get_host_info_by_hostip(host_ip)
    if not used_data:
        logging.error('the host %s perform data not in a time', host_ip)
        return None

    if expire and check_collect_time_out_interval(used_data['host_performance_collect_time'], expire_time):
        logging.error('the host %s perform data is expire', host_ip)
        return None

    # 获取db中数据
    # host_info = host_s.HostService().get_host_info_by_sn(host['sn'])
    # if host_info and used_data:
    used_data['host_id'] = used_data['id']
    # used_data['sn'] = used_data['sn']
    used_data['type_status'] = used_data['typestatus']
    # used_data['hold_mem_gb'] = host_info['hold_mem_gb']
    # used_data['name'] = host_info['name']
    # used_data['ipaddress'] = host_info['ipaddress']
    # used_data['libvirtd_status'] = host_info['libvirtd_status']
    used_data['collect_time'] = used_data['host_performance_collect_time']
    used_data['ip'] = used_data['ipaddress']
    used_data['hostname'] = used_data['name']
    # 获取host下所有vm分配的mem、vcpu、qdisk
    used_data['assign_mem'] = host_s.get_vm_assign_mem_of_host(used_data['id'])
    used_data['assign_vcpu'] = host_s.get_vm_assign_vcpu_of_host(used_data['id'])
    used_data['assign_disk'] = host_s.get_vm_assign_disk_of_host(used_data['id'])

    return used_data


def get_host_used_by_hostip(host_ip, expire=True, expire_time=600):
    '''
        获取host资源使用情况
    :param host_ip:
    :param expire:设置True，表示获取性能数据时要考虑收集时间
    :param expire_time:超过过期时间，则认为性能数据不准确，不予采用
    :return:
    '''
    # 获取性能数据
    used_data = host_s.HostService().get_host_info_by_hostip(host_ip)
    if not used_data:
        logging.error('the host %s perform data can not get in db', host_ip)
        return None

    if expire and check_collect_time_out_interval(used_data['host_performance_collect_time'], expire_time):
        logging.error('the host %s perform data is expire', host_ip)
        return None

    return used_data


def count_host_available_vm_number(mem_mb=4096, disk_gb=130, max_disk=70, max_mem=95):
    '''
        获取指定物理机可以创建的指定配置虚拟机个数
    :param mem_mb:
    :param disk_gb:
    :param max_disk:
    :param max_mem:
    :return:
    '''
    def x(host):
        # 总内存（去除了保留内存）
        all_mem = int(host.get('mem_size', 0)) - int(host["hold_mem_gb"]) * 1024
        if all_mem <= 0:
            host['available_create_vm_num'] = 0
            return False
        # 当前可用内存
        available_mem = (float(max_mem) / 100) * all_mem - int(host["assign_mem"])
        # 当前可用磁盘
        available_disk_gb = (float(max_disk) / 100) * int(host.get('disk_size', 0)) - float(
            host.get('current_disk_used', 0)) / 100 * int(host.get('disk_size', 0))

        if available_mem <= int(mem_mb) or available_disk_gb <= int(disk_gb):
            host['available_create_vm_num'] = 0
            return False

        # 指定内存可以创建虚拟机数量
        vm_num, y = divmod(available_mem, int(mem_mb))
        if vm_num > 0:
            while vm_num > 0:
                if int(disk_gb)*vm_num <= available_disk_gb:
                    host['available_create_vm_num'] = vm_num
                    return True
                else:
                    vm_num -= 1
        host['available_create_vm_num'] = 0
        return False

    return x


def get_host_mem_assign_percent(host_data):
    '''
        返回物理机内存分配率
    :param host_data:
    :return:
    '''
    _host_used = get_host_used(host_data, expire=False)
    if not _host_used:
        return 0
    host_mem_size = float(_host_used.get('mem_size', 0))
    host_mem_assign = int(_host_used.get('assign_mem', 0))
    host_hold_mem = int(_host_used.get('hold_mem_gb', 0)) * 1024

    if host_mem_assign == 0:
        host_mem_assign_per = 0
    elif int(host_mem_size) == 0:
        host_mem_assign_per = 0
    else:
        host_mem_assign_per = float('%.2f' % (float(host_mem_assign) / (host_mem_size - host_hold_mem) * 100))

    return host_mem_assign_per


def filter_host_with_same_group_id(group_id):
    '''
        过滤运行有指定应用组下虚拟机的物理机
    '''
    def x(host):
        host_instances = host_s.get_instances_of_host(host['host_id'])
        for _ins in host_instances:
            _group = ins_s.get_group_of_instance(_ins['instance_id'])
            if _group and _group['group_id'] == int(group_id):
                return False
        return host
    return x
