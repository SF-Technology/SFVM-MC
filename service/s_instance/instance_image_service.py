# coding=utf8
'''
    虚拟机-镜像服务
'''
# __author__ =  ""

from model import instance_image


class InstanceImageService:

    def __init__(self):
        self.instance_image_db = instance_image.InstanceImage(db_flag='kvm', table_name='instance_image')

    def add_instance_image_info(self, insert_data):
        return self.instance_image_db.insert(insert_data)

    def update_instance_image_info(self, update_data, where_data):
        return self.instance_image_db.update(update_data, where_data)

    def query_data(self, **params):
        return self.instance_image_db.simple_query(**params)

def get_ins_image_info_by_ins_id(instance_id):
    params = {
        'WHERE_AND': {
            "=": {
                'instance_id': instance_id,
                'isdeleted': '0'
            }
        },
    }
    total_num,data =  InstanceImageService().query_data(**params)
    if total_num >0:
        instance_image = data[0]
        return instance_image
    else:
        return False
