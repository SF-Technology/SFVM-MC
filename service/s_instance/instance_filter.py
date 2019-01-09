# coding=utf8
'''
    虚拟机调度过滤器
'''
# __author__ =  ""

from model.const_define import HostTypeStatus
from service.s_instance import instance_migrate_service as ins_m_s
from service.s_host import host_service as host_s


def current_used_filter(max_cpu=100, max_mem=100, max_disk=100):
    '''
        过滤器：创建host当前使用率
    :param max_cpu: cpu使用率阀值
    :param max_mem: 内存使用率阀值
    :param max_disk: 硬盘使用率阀值
    :return:
    '''

    def x(host):
        if int(host["current_cpu_used"]) <= max_cpu and \
                        int(host["current_mem_used"]) <= max_mem and \
                        int(host["current_disk_used"]) <= max_disk:
            return True
        return False

    return x


def week_p95_used_filter(max_cpu=100, max_mem=100):
    '''
        过滤器：host的一周P95值
    :param max_cpu: cpu使用率阀值
    :param max_mem: 内存使用率阀值
    :return:
    '''

    def x(host):
        if int(host["week_cpu_p95_used"]) <= max_cpu and \
                        int(host["week_mem_p95_used"]) <= max_mem:
            return True
        return False

    return x


def type_status_filter():
    '''
        过滤器：过滤锁定状态
    :return:
    '''

    def x(host):
        if host['type_status'] != HostTypeStatus.LOCK and host['type_status'] != HostTypeStatus.MAINTAIN:
            return True
        return False

    return x


def libvirtd_status_filter():
    '''
        过滤器：过滤libvirtd异常的host
    :return:
    '''

    def x(host):
        if host['libvirtd_status'] == '0':
            return True
        return False

    return x


def none_data_filter():
    '''
        过滤器：过滤没有使用情况数据
    :return:
    '''

    def x(host):
        if host:
            return True
        return False

    return x


def lack_metric_key_filter():
    '''
        过滤器：过滤缺失指定性能指标的host
    :return:
    '''

    def x(host):
        if host.get('current_cpu_used') and host.get('current_mem_used') and host.get('current_disk_used') \
                and host.get('week_cpu_p95_used') and host.get('week_mem_p95_used') and host.get('libvirtd_status') \
                and host.get('mem_size') and host.get('disk_size'):
            return True
        return False

    return x


def zero_data_filter():
    '''
        过滤器：过滤mem和disk值为0的host
    :return:
    '''

    def x(host):
        if int(host['mem_size']) == 0 or int(host['disk_size']) == 0:
            return False
        return True

    return x


def fit_filter(vm, num=1, max_disk=100, max_mem=100):
    '''
        过滤器：过滤无法创建VM的host
    :param vm: 虚拟机配置信息的字典，包含mem_MB,disk_GB,app_cluster,count
    :param num: 虚拟机配置的倍数(即创建几台虚拟机)
    :param max_disk: 硬盘使用率阀值:
                    (host当前使用 + 申请存储 * 申请VM数)/host存储容量 > 70%
    :param max_mem: 内存使用率阀值：
                    (host当前使用 + 申请内存 * 申请VM数)/(host内存容量 - host保留内存GB) > 95%
    :return:
    '''

    def x(host):
        # 申请内存
        apply_mem = int(vm["mem_MB"]) * num
        # 总内存（去除了保留内存）
        all_mem = int(host.get('mem_size', 0)) - int(host["hold_mem_gb"]) * 1024
        if all_mem <= 0:
            return False

        # 当前已使用磁盘
        used_disk = float(host.get('current_disk_used', 0)) / 100 * int(host["disk_size"])
        # 申请磁盘
        apply_disk = int(vm["disk_GB"]) * num
        if ((int(host["assign_mem"]) + apply_mem) * 100 / all_mem) < max_mem and \
                        ((used_disk + apply_disk) * 100 / int(host["disk_size"])) < max_disk:
            return True
        return False

    return x


def v2v_batch_host_filter(apply_mem, apply_disk, max_disk=100, max_mem=100):
    '''
        过滤器：过滤无法创建VM的host
    :param apply_mem: 虚拟机申请内存
    :param apply_disk: 虚拟机申请磁盘
    :param max_disk: 硬盘使用率阀值:
                    (host当前使用 + 申请存储 * 申请VM数)/host存储容量 > 70%
    :param max_mem: 内存使用率阀值：
                    (host当前使用 + 申请内存 * 申请VM数)/(host内存容量 - host保留内存GB) > 95%
    :return:
    '''

    def x(host):
        # 总内存（去除了保留内存）
        all_mem = int(host.get('mem_size', 0)) - int(host["hold_mem_gb"]) * 1024
        if all_mem <= 0:
            return False

        # 当前已使用磁盘
        used_disk = int(host.get('current_disk_used', 0)) / 100 * int(host["disk_size"])
        if ((int(host["assign_mem"]) + apply_mem) * 100 / all_mem) < max_mem and \
                        ((used_disk + apply_disk) * 100 / int(host["disk_size"])) < max_disk:
            return True
        return False

    return x


def migrate_ing_filter():
    '''
        过滤器：过滤存在有VM迁入的host
    :return:
    '''

    def x(host):
        params = {
            'WHERE_AND': {
                '=': {
                    'dst_host_id': host['host_id'],
                    'migrate_status': '0'
                }
            },
        }
        migrate_num, migrate_host = ins_m_s.InstanceMigrateService().query_data(**params)
        if migrate_num > 0:
            return False
        return True

    return x


def migrate_invalid_status_filter():
    '''
        过滤器：过滤处于锁定和维护状态的host
    :return:
    '''
    def x(host):
        if host['type_status'] == HostTypeStatus.LOCK \
                or host['type_status'] == HostTypeStatus.MAINTAIN:
            return False
        return True

    return x


def instance_nums_filter(max_instance_nums):
    '''
        过滤器：过滤掉虚拟机数量大于max_instance_nums的物理机
    :return:
    '''

    def x(host):
        instance_datas = host_s.get_instances_of_host_without_clone(host['id'])
        if not instance_datas:
            instance_nums = 0
        else:
            instance_nums = len(instance_datas)
        if instance_nums < max_instance_nums:
            return True
        return False

    return x
