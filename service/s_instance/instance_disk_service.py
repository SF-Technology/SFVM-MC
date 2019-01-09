# coding=utf8
'''
    虚拟机-磁盘服务
'''


import time
# from libvirt import libvirtError
import logging
from model import disk
from model import instance_disk


class InstanceDiskService:

    def __init__(self):
        self.disk_db = disk.Disk(db_flag='kvm', table_name='instance_disk')

    def add_instance_disk_info(self, insert_data):
        return self.disk_db.insert(insert_data)

    def update_instance_disk_info(self, update_data, where_data):
        return self.disk_db.update(update_data, where_data)

    def query_data(self, **params):
        return self.disk_db.simple_query(**params)


def create_disk(hostname, conn, conn_storage, disk, uuid):
    retry_disk = 0
    retry_nums = 3
    disks = {}
    while retry_disk < retry_nums:
        time.sleep(5)
        try:
            # 创建磁盘
            disk_name = hostname + '.disk1'
            disk_xml = conn_storage.create_disk('vdb', disk_name, disk, uuid, 'qcow2', False)
            disk_path = conn.get_volume_path(disk_name)
            disks[disk_path] = conn.get_volume_type(disk_path)
            break
        # except libvirtError as err:
        #     logging.info(err)
        except:
            retry_disk += 1

    if retry_disk == retry_nums:
        logging.info('create disk retry %s times fail', retry_nums)
        # todo:要关闭连接
        # conn_storage.close()
        return -1

    return disk_xml

def get_ins_disk_info_by_ins_id(instance_id):
    params = {
        'WHERE_AND': {
            "=": {
                'instance_id': instance_id,
                'isdeleted': '0'
            }
        },
    }
    total_num,data =  InstanceDiskService().query_data(**params)
    if total_num >0:
        instance_disk = data[0]
        return instance_disk
    else:
        return False


def get_instance_action_by_mount(mount_point, instance_id):
    params = {
        'WHERE_AND': {
            '=': {
                'mount_point': mount_point,
                'instance_id': instance_id
            },
        },

    }
    total_nums, data = InstanceDiskService().query_data(**params)
    if total_nums > 0:
        return True, data
    else:
        return False, ''

def get_info_by_mount_and_disk(mount_point, dev_name, instance_id):
    params = {
        'WHERE_AND': {
            '=': {
                'mount_point': mount_point,
                'dev_name': dev_name,
                'instance_id': instance_id
            },
        },

    }
    total_nums, data = InstanceDiskService().query_data(**params)
    if total_nums > 0:
        return True, data
    else:
        return False, ''



