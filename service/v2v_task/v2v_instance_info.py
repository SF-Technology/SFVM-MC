# coding=utf8
'''
    v2v_任务查 看
'''


from model import v2v_instanceinfo
from lib.vrtManager.util import randomUUID
from time_helper import get_datetime_str


class v2vInstanceinfo:
    def __init__(self):
        self.v2v_instance_db = v2v_instanceinfo.v2v_instanceinfo(db_flag='kvm', table_name='v2v_instance_info')

    def add_v2v_instance_info(self, insert_data):
        return self.v2v_instance_db.insert(insert_data)

    def query_data(self, **params):
        return self.v2v_instance_db.simple_query(**params)

    def update_v2v_status(self, update_data, where_data):
        return self.v2v_instance_db.update(update_data, where_data)

    def get_v2v_instance_info_by_instance_id(self, instance_id):
        params = {
            'WHERE_AND': {
                 '=': {
                         'instance_id': instance_id,
                         'isdeleted': '0',
                 },
             }
        }
        ins_nums, ins_datas = self.v2v_instance_db.simple_query(**params)
        if ins_nums > 0:
            return ins_datas[0]
        return None






