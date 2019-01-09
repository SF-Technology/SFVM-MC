# coding=utf8
'''
    虚拟机服务
'''
# __author__ =  ""

from model import instance
from lib.vrtManager.util import randomUUID
from service.s_host.host_service import get_hosts_of_datacenter


class InstanceService:

    def __init__(self):
        self.instance_db = instance.Instance(db_flag='kvm', table_name='instance')

    def query_data(self, **params):
        return self.instance_db.simple_query(**params)

    def get_instance_info(self, instance_id):
        return self.instance_db.get_one('id', instance_id)

    def add_instance_info(self, insert_data):
        return self.instance_db.insert(insert_data)

    def update_instance_info(self, update_data, where_data):
        return self.instance_db.update(update_data, where_data)

    def get_instance_info_by_uuid(self, instance_uuid):
        return self.instance_db.get_one('uuid', instance_uuid)

    def get_instance_info_by_requestid(self, request_id):
        return self.instance_db.get_one('request_id', request_id)

    def get_instance_info_by_name(self,instance_name):
        params = {
            'WHERE_AND': {
                "=": {
                    'name': instance_name,
                    'isdeleted': '0',
                }
            },
        }
        total_nums, data = self.instance_db.simple_query(**params)
        if total_nums <= 0:
            return None
        return data[0]


def get_instances_in_group(group_id):
    '''
        获取指定应用组下所有的虚机
    :param group_id:
    :return:
    '''
    _instances = instance.get_instances_info_in_group(group_id)
    return _instances


def get_instances_in_dc(dc_id):
    '''
        获取指定机房下所有的虚机
    :param dc_id:
    :return:
    '''
    all_instances_list = []
    hosts_data = get_hosts_of_datacenter(dc_id)
    for _host in hosts_data:
        _instances = instance.get_instances_info_in_host(_host['id'])
        for _ins in _instances:
            all_instances_list.append(_ins)
    return all_instances_list


def get_instances_nums_in_host(host_id):
    '''
        获取指定host下的虚机数量
    :param host_id:
    :return:
    '''
    return len(instance.get_instances_info_in_host(host_id))


def get_instances_in_host(host_id):
    '''
        获取指定host下的所有虚机
    :param host_id:
    :return:
    '''
    return instance.get_instances_info_in_host(host_id)


def get_instances_by_host_ip(host_ip):
    '''
        获取指定host ip对应host下的所有虚机
    :param host_ip:
    :return:
    '''
    return instance.get_instances_info_by_host_ip(host_ip)


def get_instances_by_fuzzy_ip(ip_address,ip_search_type):
    '''
        根据IP模糊查询对应的虚拟机
    :param ip_address:
    :return:
    '''
    return instance.get_instances_by_fuzzy_ip(ip_address,ip_search_type)


def get_instances_by_fuzzy_host_ip(host_ip):
    '''
        根据hostIP模糊查询对应的虚拟机
    :param host_ip:
    :return:
    '''
    return instance.get_instances_by_fuzzy_host_ip(host_ip)


def get_instances_by_fuzzy_group_name(group_name):
    '''
        根据group_name模糊查询对应的虚拟机
    :param group_name:
    :return:
    '''
    return instance.get_instances_by_fuzzy_group_name(group_name)


def get_datacenter_of_instance(instance_id):
    '''
        获取虚机对应的机房信息
    :param instance_id:
    :return:
    '''
    return instance.get_instance_datacenter_info(instance_id)


def get_netarea_of_instance(instance_id):
    '''
        获取虚机对应的网络区域信息
    :param instance_id:
    :return:
    '''
    return instance.get_instance_netarea_info(instance_id)


def get_hostpool_of_instance(instance_id):
    '''
        获取虚机对应的集群信息
    :param instance_id:
    :return:
    '''
    return instance.get_instance_hostpool_info(instance_id)


def get_hostip_of_instance(instance_id):
    '''
        获取虚机对应的host的IP地址
    :param instance_id:
    :return:
    '''
    host_info = instance.get_instance_host_info(instance_id)
    if host_info:
        return host_info['ipaddress']
    else:
        return None


def get_host_of_instance(instance_id):
    '''
        获取虚机对应的host
    :param instance_id:
    :return:
    '''
    return instance.get_instance_host_info(instance_id)


def get_flavor_of_instance(instance_id):
    '''
        获取虚机的flavor信息
    :param instance_id:
    :return:
    '''
    return instance.get_instance_flavor_info(instance_id)


def get_images_of_instance(instance_id):
    '''
        获取虚机的image信息
    :param instance_id:
    :return:
    '''
    return instance.get_instance_images_info(instance_id)


def get_images_of_clone_instance(instance_id):
    '''
        获取虚机的image信息
    :param instance_id:
    :return:
    '''
    return instance.get_clone_instance_images_info(instance_id)


def get_disks_of_instance(instance_id):
    '''
        获取虚机的disk信息
    :param instance_id:
    :return:
    '''
    return instance.get_instance_disks_info(instance_id)


def get_a_disk_of_instance(instance_id, dev_name):
    '''
        获取虚机的指定磁盘信息
    :param instance_id:
    :param dev_name:
    :return:
    '''
    return instance.get_instance_a_disk_info(instance_id, dev_name)


def get_full_disks_info_of_instance(instance_id):
    return instance.get_instance_full_disks_info(instance_id)


def get_data_disk_size_of_instance(instance_id):
    '''
        获取虚拟机数据盘总大小
    :param instance_id:
    :return:
    '''
    ret = instance.get_instance_disks_size(instance_id)
    if not ret:
        return False, ''
    else:
        for disk in ret:
            if not disk['data_disk_size']:
                return True, 0
            else:
                return True, disk['data_disk_size']


def get_group_of_instance(instance_id):
    '''
        获取虚机的group信息
    :param instance_id:
    :return:
    '''
    return instance.get_instance_group_info(instance_id)


def get_ip_of_instance(instance_id):
    '''
        获取虚机的主网IP信息
    :param instance_id:
    :return:
    '''
    return instance.get_instance_ip_info(instance_id)


def get_all_ip_of_instance(instance_id):
    '''
        获取虚机的所有IP信息
    :param instance_id:
    :return:
    '''
    return instance.get_instance_all_ip_info(instance_id)


def get_net_info_of_instance(instance_id):
    '''
        获取虚机所有网卡信息，mac、ip信息
    :param instance_id:
    :return:
    '''
    return instance.get_instance_net_info(instance_id)


def get_net_segment_info_of_instance(instance_id):
    '''
        获取虚拟机ip所在网段对应网络信息
    :param instance_id:
    :return:
    '''
    return instance.get_instance_net_segment_info(instance_id)


def get_net_info_of_instance_by_mac_addr(mac_addr):
    '''
        获取虚机mac对应网络信息
    :param instance_id:
    :return:
    '''
    return instance.get_instance_net_info_by_mac_addr(mac_addr)


def generate_req_id():
    '''
        获取请求ID
    :return:
    '''
    return 'req-' + randomUUID()


def generate_task_id():
    '''
        获取任务ID
    :return:
    '''
    return 'task-' + randomUUID()


def check_instance_status(instance_uuid):
    '''
        获取虚拟机状态
    :param instance_uuid:
    :return:
    '''
    instance_info = InstanceService().get_instance_info_by_uuid(instance_uuid)
    if not instance_info:
        return False, ''
    elif instance_info['isdeleted'] == '1':
        return False, ''
    else:
        return True, instance_info['status']

def get_clonecreate_bt_status(task_id,host_ip,action,request_id):
    '''
        获取指定task_id下是否有host上在做bt操作
    :param task_id,host_ip,action:
    :return:
    '''
    return instance.get_clone_task_bttrans_status(task_id,host_ip,action,request_id)


def get_clonecreate_bt_done(task_id,host_ip,action,request_id):
    '''
        获取指定task_id下是否有host上在做bt操作
    :param task_id,host_ip,action:
    :return:
    '''
    return instance.get_clone_task_bttrans_done(task_id,host_ip,action,request_id)


def get_instance_info_by_ip(ip_address):
    '''根据ip获取虚拟机信息'''
    return instance.get_instance_info_by_ip_address(ip_address)