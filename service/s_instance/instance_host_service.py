# coding=utf8
'''
    虚拟机-主机服务
'''
# __author__ =  ""

from model import instance_host


class InstanceHostService:

    def __init__(self):
        self.instance_host_db = instance_host.InstanceHost(db_flag='kvm', table_name='instance_host')

    def add_instance_host_info(self, insert_data):
        return self.instance_host_db.insert(insert_data)

    def update_instance_host_info(self, update_data, where_data):
        return self.instance_host_db.update(update_data, where_data)

    def query_data(self, **params):
        return self.instance_host_db.simple_query(**params)

    def delete_instance_host(self, where_data):
        return self.instance_host_db.delete(where_data)

def get_ins_host_info_by_ins_id(instance_id):
    params = {
        'WHERE_AND': {
            "=": {
                'instance_id': instance_id,
                'isdeleted': '0'
            }
        },
    }
    total_num,data =  InstanceHostService().query_data(**params)
    if total_num >0:
        instance_image = data[0]
        return instance_image
    else:
        return False
