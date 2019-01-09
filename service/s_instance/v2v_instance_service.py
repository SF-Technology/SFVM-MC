# -*- coding:utf-8 -*-
# __author__ =  ""

from model import v2v_instanceinfo


class V2VInstanceService:

    def __init__(self):
        self.v2v_instance_db = v2v_instanceinfo.v2v_instanceinfo(db_flag='kvm', table_name='v2v_instance_info')

    def query_data(self, **params):
        return self.v2v_instance_db.simple_query(**params)

    def get_v2v_instance_info(self, instance_id):
        return self.v2v_instance_db.get_one('instance_id', instance_id)
