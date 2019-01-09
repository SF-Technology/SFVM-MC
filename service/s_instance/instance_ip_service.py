# coding=utf8
'''
    虚拟机-IP服务
'''
# __author__ =  ""

from model import instance_ip


class InstanceIPService:

    def __init__(self):
        self.instance_ip_db = instance_ip.InstanceIP(db_flag='kvm', table_name='instance_ip')

    def add_instance_ip_info(self, insert_data):
        return self.instance_ip_db.insert(insert_data)

    def update_instance_ip_info(self, update_data, where_data):
        return self.instance_ip_db.update(update_data, where_data)

    def query_data(self, **params):
        return self.instance_ip_db.simple_query(**params)

def get_instance_mac_list(instance_id):
    params = {
        'WHERE_AND': {
            '=': {
                'instance_id': instance_id
            },
        },
    }

    total_nums, data = InstanceIPService().query_data(**params)
    mac_list = []
    for singledata in data:
        mac_list.append(singledata['mac'])
    return mac_list