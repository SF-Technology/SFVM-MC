# coding=utf8
'''
    INSTANCE_GROUP服务
'''
# __author__ =  ""

import model.instance_group as instance_group_db
import model.group as group_db
from model import instance_group
from lib.dbs.mysql import Mysql
import logging
import traceback


def query_group_info(instance_id):
    '''
    从instance_group表中查询instance对应的group，再从tb_group表中提取group的所有信息
    :return 返回如下
    {'description': u'something, 'displayname': u'something, 'id': 3L, 'isdeleted': u'0', 'name': u'user'}
    '''
    data = instance_group_db.query_data(instance_id)
    if data:
        group_id = data[0].get('group_id')
        resp = group_db.query_group_info(group_id)
        return resp
    return None


class InstanceGroupService:

    def __init__(self):
        self.instance_group_db = instance_group.InstanceGroup(db_flag='kvm', table_name='instance_group')

    def add_instance_group_info(self, insert_data):
        return self.instance_group_db.insert(insert_data)

    def query_data(self, where_field, where_field_value):
        return self.instance_group_db.get_one(where_field, where_field_value)

    def update_instance_group_info(self, update_data, where_data):
        return self.instance_group_db.update(update_data, where_data)

    def delete_instance_group_info(self, instance_id):
        where_data = {
            'instance_id': instance_id
        }
        return self.instance_group_db.delete(where_data)

    def get_instance_group_info(self, instance_id):
        return self.instance_group_db.get_one('instance_id', instance_id)
