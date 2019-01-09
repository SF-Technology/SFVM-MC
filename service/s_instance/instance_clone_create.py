# coding=utf8
'''
    虚拟机-规格服务
'''
# __author__ =  ""

from model import instance_clone_create


class InstanceCloneCreateService:

    def __init__(self):
        self.instance_clone_create_db = instance_clone_create.instance_clone_create(db_flag='kvm', table_name='instance_clone_create')

    def add_instance_clone_create_info(self, insert_data):
        return self.instance_clone_create_db.insert(insert_data)

    def query_data(self, **params):
        return self.instance_clone_create_db.simple_query(**params)

def get_ins_clone_create_info_by_task_id(task_id):
    params = {
        'WHERE_AND': {
            "=": {
                'task_id': task_id
            }
        },
    }
    total_num,data =  InstanceCloneCreateService().query_data(**params)
    if total_num >0:
        instance_clone_create_data = data[0]
        return instance_clone_create_data
    else:
        return False
