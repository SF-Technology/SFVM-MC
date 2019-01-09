# coding=utf8
'''
    虚拟机-规格服务
'''


from model import instance_flavor


class InstanceFlavorService:

    def __init__(self):
        self.instance_flavor_db = instance_flavor.InstanceFlavor(db_flag='kvm', table_name='instance_flavor')

    def add_instance_flavor_info(self, insert_data):
        return self.instance_flavor_db.insert(insert_data)

    def update_instance_flavor(self, flavor_id, instance_id):
        update_data = {
            'flavor_id': flavor_id
        }
        where_data = {
            'instance_id': instance_id
        }
        return self.instance_flavor_db.update(update_data, where_data)

    def delete_instance_flavor(self, instance_id):
        where_data = {
            'instance_id': instance_id
        }
        return self.instance_flavor_db.delete(where_data)