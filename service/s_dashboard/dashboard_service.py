# coding=utf8
'''
    dashboard服务
'''


from service.s_host.host_service import get_hosts_of_datacenter
from service.s_host.host_schedule_service import get_host_used
from service.s_host import host_schedule_service as host_s_s
from service.s_hostpool import hostpool_service as hostpool_s
import threading

HOST_CAPACITY_CALCULATE_THREADINGLOCK = threading.Lock()


def get_cpu_mem_used_in_dc(dc_id):
    '''
        获取指定机房下所有host的CPU和MEM的使用情况
    :param dc_id:
    :return:
    '''
    all_hosts_data = get_hosts_of_datacenter(dc_id)
    all_cpu_used = 0
    all_cpu_unused = 0
    all_cpu = 0
    all_mem_used = 0
    all_mem_unused = 0
    all_mem = 0
    for _host in all_hosts_data:
        _host_used = get_host_used(_host, expire=False)
        if _host_used:
            _cpu_used_per = float(_host_used.get('current_cpu_used', 0)) if _host_used.get('current_cpu_used') else 0.0
            _cpu_core = float(_host_used.get('cpu_core', 0))
            _cpu_used = int(_cpu_used_per / 100 * _cpu_core)
            all_cpu_used += _cpu_used
            all_cpu_unused += (_cpu_core - _cpu_used)
            all_cpu += _cpu_core

            _mem_used_per = float(_host_used.get('current_mem_used', 0))
            _mem_size = float(_host_used.get('mem_size', 0))
            _mem_used = int(_mem_used_per / 100 * _mem_size)
            all_mem_used += _mem_used
            all_mem_unused += (_mem_size - _mem_used)
            all_mem += _mem_size

    if all_cpu == 0:
        all_cpu_used_per = 0
        all_cpu_unused_per = 0
    else:
        all_cpu_used_per = int(float(all_cpu_used) / all_cpu * 100)
        all_cpu_unused_per = 100 - all_cpu_used_per

    if all_mem == 0:
        all_mem_used_per = 0
        all_mem_unused_per = 0
    else:
        all_mem_used_per = int(float(all_mem_used) / all_mem * 100)
        all_mem_unused_per = 100 - all_mem_used_per

    return {
        'cpu_used': all_cpu_used,
        'cpu_used_per': all_cpu_used_per,
        'cpu_unused': all_cpu_unused,
        'cpu_unused_per': all_cpu_unused_per,
        'mem_used': all_mem_used,
        'mem_used_per': all_mem_used_per,
        'mem_unused': all_mem_unused,
        'mem_unused_per': all_mem_unused_per
    }


def get_cpu_mem_used(all_hosts_data, hostpool_id, req_mem_mb=4096, req_disk_gb=50, cpu_used=80, mem_used=95, disk_used=70):
    '''
        获取批量host的CPU和MEM的使用情况
    :param all_hosts_data:
    :param hostpool_id:
    :param req_mem_mb:
    :param req_disk_gb:
    :param cpu_used:
    :param mem_used:
    :param disk_used:
    :return:
    '''
    all_cpu_used = 0
    all_cpu_unused = 0
    all_cpu = 0
    all_mem_used = 0
    all_mem_unused = 0
    all_mem = 0
    all_mem_assign = 0
    all_hold_mem = 0
    all_available_create_vm_num = 0
    all_host_available = 0
    for _host in all_hosts_data:
        _host_used = get_host_used(_host, expire=False)
        if _host_used:
            _cpu_used_per = float(_host_used.get('current_cpu_used', 0)) if _host_used.get('current_cpu_used') else 0.0
            _cpu_core = float(_host_used.get('cpu_core', 0))
            _cpu_used = float(_cpu_used_per / 100 * _cpu_core)
            all_cpu_used += _cpu_used
            all_cpu_unused += (_cpu_core - _cpu_used)
            all_cpu += _cpu_core

            _mem_used_per = float(_host_used.get('current_mem_used', 0))
            _mem_size = float(_host_used.get('mem_size', 0))
            _mem_used = float(_mem_used_per / 100 * _mem_size)
            all_mem_used += _mem_used
            all_mem_unused += (_mem_size - _mem_used)
            all_mem += _mem_size
            all_mem_assign += int(_host_used.get('assign_mem', 0))
            all_hold_mem += int(_host_used.get('hold_mem_gb', 0)) * 1024

            # 以下为计算每台物理机可以创建的虚拟机数量
            _available_mem, _available_disk, _available_create_vm = get_host_available_mem_disk(_host_used,
                                                                                                int(req_mem_mb),
                                                                                                int(req_disk_gb) + 80,
                                                                                                max_disk=2000)
            # TODO 每台host最多创建50台vm
            _available_create_vm = _available_create_vm if _available_create_vm < 50 else 50

            if _host_used.get('type_status', '0') == '0':
                if float(_host_used.get('current_cpu_used', 0)) < cpu_used and \
                                float(_host_used.get('current_mem_used', 0)) < mem_used and \
                                float(_host_used.get('current_disk_used', 0)) < disk_used:
                    if _available_create_vm > 0:
                        all_host_available += 1
                    all_available_create_vm_num += _available_create_vm

    __least_host_num = hostpool_s.HostPoolService().get_least_host_num(hostpool_id)
    if __least_host_num:
        if all_host_available < int(__least_host_num):
            all_available_create_vm_num = 0

    if all_cpu == 0:
        all_cpu_used_per = 0
        all_cpu_unused_per = 0
    else:
        all_cpu_used_per = float('%.2f' % (float(all_cpu_used) / all_cpu * 100))
        all_cpu_unused_per = 100 - all_cpu_used_per

    if all_mem == 0:
        all_mem_used_per = 0
        all_mem_unused_per = 0
    else:
        all_mem_used_per = float('%.2f' % (float(all_mem_used) / all_mem * 100))
        all_mem_unused_per = 100 - all_mem_used_per

    if all_mem_assign == 0:
        all_mem_assign_per = 0
    else:
        all_mem_assign_per = float('%.2f' % (float(all_mem_assign) / (all_mem - all_hold_mem) * 100))

    return {
        'cpu_all': all_cpu,
        'cpu_used': all_cpu_used,
        'cpu_used_per': all_cpu_used_per,
        'cpu_unused': all_cpu_unused,
        'cpu_unused_per': all_cpu_unused_per,
        'mem_all': all_mem,
        'mem_used': all_mem_used,
        'mem_used_per': all_mem_used_per,
        'mem_unused': all_mem_unused,
        'mem_unused_per': all_mem_unused_per,
        'assign_mem': all_mem_assign,
        'assign_mem_per': all_mem_assign_per,
        'available_create_vm_num': all_available_create_vm_num
    }


def get_host_mem_cpu_disk_used_multithreading(_host, req_mem_mb, req_disk_gb, all_hosts_data_after_filter):
    '''
        多线程获取每台物理机资源使用信息
    :param _host:
    :param req_mem_mb:
    :param req_disk_gb:
    :param all_hosts_data_after_filter:
    :return:
    '''
    global ALL_CPU_USED
    global ALL_CPU_UNUSED
    global ALL_CPU
    global ALL_MEM_USED
    global ALL_MEM_UNUSED
    global ALL_MEM
    global ALL_DISK_USED
    global ALL_DISK_UNUSED
    global ALL_DISK
    global ALL_CPU_ASSIGN
    global ALL_MEM_ASSIGN
    global ALL_DISK_ASSIGN
    global ALL_MEM_AVAILABLE
    global ALL_DISK_AVAILABLE
    global ALL_AVAILABLE_CREATE_VM
    global ALL_HOST_PERFORMANCE_DATAS
    global ALL_AVAILABLE_HOST_NUM

    global HOST_CAPACITY_CALCULATE_THREADINGLOCK

    _host_used = get_host_used(_host, expire=False)

    if _host_used:
        HOST_CAPACITY_CALCULATE_THREADINGLOCK.acquire()
        _cpu_used_per = float(_host_used.get('current_cpu_used', 0)) if _host_used.get('current_cpu_used') else 0.0
        _cpu_core = float(_host_used.get('cpu_core', 0))
        _cpu_used = float(_cpu_used_per / 100 * _cpu_core)
        ALL_CPU_USED += _cpu_used
        ALL_CPU_UNUSED += (_cpu_core - _cpu_used)
        ALL_CPU += _cpu_core

        _mem_used_per = float(_host_used.get('current_mem_used', 0))
        _mem_size = float(_host_used.get('mem_size', 0))
        _mem_used = float(_mem_used_per / 100 * _mem_size)
        ALL_MEM_USED += _mem_used
        ALL_MEM_UNUSED += (_mem_size - _mem_used)
        ALL_MEM += _mem_size

        _disk_used_per = float(_host_used.get('current_disk_used', 0))
        _disk_size = float(_host_used.get('disk_size', 0))
        _disk_used = float(_disk_used_per / 100 * _disk_size)
        ALL_DISK_USED += _disk_used
        ALL_DISK_UNUSED += (_disk_size - _disk_used)
        ALL_DISK += _disk_size

        # 已分配给虚拟机的内存、cpu和磁盘
        ALL_MEM_ASSIGN += _host_used.get('assign_mem', 0)
        ALL_CPU_ASSIGN += _host_used.get('assign_vcpu', 0)
        ALL_DISK_ASSIGN += _host_used.get('assign_disk', 0)

        # 获取物理机可用的内存、磁盘大小，保证最大内存使用率不大于max_mem和最大磁盘使用率不大于max_disk
        _available_mem, _available_disk, _available_create_vm = get_host_available_mem_disk(_host_used, int(req_mem_mb),
                                                                                            int(req_disk_gb) + 80,
                                                                                            max_disk=2000)
        # TODO 每台host最多创建50台vm
        _available_create_vm = _available_create_vm if _available_create_vm < 50 else 50

        ALL_MEM_AVAILABLE += _available_mem
        ALL_DISK_AVAILABLE += _available_disk

        # 物理机过滤，如果过滤后物理机数量为0或者小于集群最小物理机数量，则该集群可创建虚拟机数量为0
        # hosts_after_filter = host_s_s.filter_hosts(all_hosts_data)
        host_after_filter_available = False
        for host_after_filter in all_hosts_data_after_filter:
            if host_after_filter['ipaddress'] == _host_used['ipaddress']:
                host_after_filter_available = True
                break
        if host_after_filter_available:
            _host_list = []
            _host_list.append(_host_used)
            get_available_vm_number = host_s_s.count_host_available_vm_number(int(req_mem_mb),
                                                                              int(req_disk_gb) + 80,
                                                                              max_disk=2000)
            ret_hosts_1 = filter(get_available_vm_number, _host_list)

            hosts_vm_number_filter = host_s_s.host_available_create_vm_number_filter()
            ret_hosts_2 = filter(hosts_vm_number_filter, ret_hosts_1)
            if _host_used.get('type_status', '0') == '0' and len(ret_hosts_2) > 0:
                ALL_AVAILABLE_HOST_NUM += 1
                ALL_AVAILABLE_CREATE_VM += _available_create_vm

        # 拼装每一台物理机信息
        _host_data = {
            'hostname': _host_used.get('hostname', ''),
            'ip': _host_used.get('ipaddress', ''),
            'host_total_capacity': {
                'vcpu': int(_host_used.get('cpu_core', 0)),
                'mem_mb': int(_host_used.get('mem_size', 0)),
                'disk_gb': int(_host_used.get('disk_size', 0))
            },
            'host_assign_capacity': {
                'mem_mb': int(_host_used.get('assign_mem', 0)),
                'vcpu': int(_host_used.get('assign_vcpu', 0)),
                'disk_gb': int(_host_used.get('assign_disk', 0))
            },
            'host_available_capacity': {
                'mem_mb': _available_mem,
                'vcpu': int(_cpu_core - _cpu_used),
                'disk_gb': _available_disk,
                'vm_count': int(_available_create_vm)
            },
            'host_performance': {
                'vcpu_usage': int(_host_used.get('current_cpu_used', 0)),
                'mem_usage': int(_host_used.get('current_mem_used', 0)),
                'disk_usage': int(_host_used.get('current_disk_used', 0))
            },
            'net_speed': int(_host_used.get('net_size', 0)),
            'state': ''
        }
        ALL_HOST_PERFORMANCE_DATAS.append(_host_data)
        HOST_CAPACITY_CALCULATE_THREADINGLOCK.release()


def get_hostpool_mem_cpu_disk_used(all_hosts_data, req_mem_mb, req_disk_gb, hostpool_id):
    '''
        获取集群下所有物理机资源使用信息
    :param all_hosts_data:
    :param req_mem_mb:
    :param req_disk_gb:
    :return:
    '''
    global ALL_CPU_USED
    global ALL_CPU_UNUSED
    global ALL_CPU
    global ALL_MEM_USED
    global ALL_MEM_UNUSED
    global ALL_MEM
    global ALL_DISK_USED
    global ALL_DISK_UNUSED
    global ALL_DISK
    global ALL_CPU_ASSIGN
    global ALL_MEM_ASSIGN
    global ALL_DISK_ASSIGN
    global ALL_MEM_AVAILABLE
    global ALL_DISK_AVAILABLE
    global ALL_AVAILABLE_CREATE_VM
    global ALL_HOST_PERFORMANCE_DATAS
    global ALL_AVAILABLE_HOST_NUM

    ALL_CPU_USED = 0
    ALL_CPU_UNUSED = 0
    ALL_CPU = 0
    ALL_MEM_USED = 0
    ALL_MEM_UNUSED = 0
    ALL_MEM = 0
    ALL_DISK_USED = 0
    ALL_DISK_UNUSED = 0
    ALL_DISK = 0
    ALL_CPU_ASSIGN = 0
    ALL_MEM_ASSIGN = 0
    ALL_DISK_ASSIGN = 0
    ALL_MEM_AVAILABLE = 0
    ALL_DISK_AVAILABLE = 0
    ALL_AVAILABLE_CREATE_VM = 0
    ALL_HOST_PERFORMANCE_DATAS = []
    ALL_AVAILABLE_HOST_NUM = 0

    threads = []

    hosts_after_filter = host_s_s.filter_hosts(all_hosts_data)

    # 集群所有物理机cpu、mem性能数据统计
    for _host in all_hosts_data:
        # 多线程查询每台物理机使用情况
        _host_thread = threading.Thread(target=get_host_mem_cpu_disk_used_multithreading,
                                        args=(_host, req_mem_mb, req_disk_gb, hosts_after_filter, ))
        threads.append(_host_thread)
        _host_thread.start()

        # 判断多线程是否结束
    for t in threads:
        t.join()

    if ALL_CPU == 0:
        all_cpu_used_per = 0
        all_cpu_unused_per = 0
    else:
        all_cpu_used_per = float('%.2f' % (float(ALL_CPU_USED) / ALL_CPU * 100))
        all_cpu_unused_per = 100 - all_cpu_used_per

    if ALL_MEM == 0:
        all_mem_used_per = 0
        all_mem_unused_per = 0
    else:
        all_mem_used_per = float('%.2f' % (float(ALL_MEM_USED) / ALL_MEM * 100))
        all_mem_unused_per = 100 - all_mem_used_per

    if ALL_DISK == 0:
        all_disk_used_per = 0
        all_disk_unused_per = 0
    else:
        all_disk_used_per = float('%.2f' % (float(ALL_DISK_USED) / ALL_DISK * 100))
        all_disk_unused_per = 100 - all_disk_used_per

    __least_host_num = hostpool_s.HostPoolService().get_least_host_num(hostpool_id)
    if __least_host_num:
        if ALL_AVAILABLE_HOST_NUM < int(__least_host_num):
            ALL_AVAILABLE_CREATE_VM = 0

    return {
        'cpu_all': int(ALL_CPU),
        'cpu_used': int(ALL_CPU_USED),
        'cpu_used_per': int(all_cpu_used_per),
        'cpu_unused': int(ALL_CPU_UNUSED),
        'cpu_unused_per': int(all_cpu_unused_per),
        'mem_all': int(ALL_MEM),
        'mem_used': int(ALL_MEM_USED),
        'mem_used_per': int(all_mem_used_per),
        'mem_unused': int(ALL_MEM_UNUSED),
        'mem_unused_per': int(all_mem_unused_per),
        'disk_all': int(ALL_DISK),
        'disk_used': int(ALL_DISK_USED),
        'disk_used_per': int(all_disk_used_per),
        'disk_unused': int(ALL_DISK_UNUSED),
        'disk_unused_per': int(all_disk_unused_per),
        'mem_assign': int(ALL_MEM_ASSIGN),
        'cpu_assign': int(ALL_CPU_ASSIGN),
        'disk_assign': int(ALL_DISK_ASSIGN),
        'mem_available': int(ALL_MEM_AVAILABLE),
        'disk_available': int(ALL_DISK_AVAILABLE),
        'available_create_vm': int(ALL_AVAILABLE_CREATE_VM),
        'all_host_performance_datas': ALL_HOST_PERFORMANCE_DATAS,
        'all_available_host_num': ALL_AVAILABLE_HOST_NUM
    }


def get_host_available_mem_disk(host_data, mem_mb, disk_gb, max_disk=70, max_mem=95):
    '''
        获取指定物理机可用的内存、磁盘大小，保证最大内存使用率不大于max_mem和最大磁盘使用率不大于max_disk
    :param host_data:
    :param max_disk:
    :param max_mem:
    :return:
    '''
    # 总内存（去除了保留内存）
    all_mem = int(host_data.get('mem_size', 0)) - int(host_data["hold_mem_gb"]) * 1024
    if all_mem <= 0:
        return 0, 0, 0
    # 当前可用内存
    available_mem = (float(max_mem) / 100) * all_mem - int(host_data["assign_mem"])
    # 当前可用磁盘
    available_disk_gb = (float(max_disk) / 100) * int(host_data.get('disk_size', 0)) - float(host_data.get('current_disk_used', 0)) / 100 * int(host_data.get('disk_size', 0))

    if available_mem <= 0 or available_disk_gb <= 0:
        return 0, 0, 0

    # 指定内存可以创建虚拟机数量
    vm_num, y = divmod(available_mem, int(mem_mb))
    if vm_num > 0:
        while vm_num > 0:
            if int(disk_gb) * vm_num <= available_disk_gb:
                return int(available_mem), int(available_disk_gb), vm_num
            else:
                vm_num -= 1
    return int(available_mem), int(available_disk_gb), 0
