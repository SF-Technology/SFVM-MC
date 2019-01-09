# coding=utf8
'''
    USER_GROUP服务
'''


import model.user_group as user_group_db
from lib.dbs.mysql import Mysql
import logging
import traceback


class UserGroupService:

    def __init__(self):
        self.user_group_db = user_group_db.UserGroup(db_flag='kvm', table_name='user_group')

    def get_alluser_group(self, group_id):
        '''
        通过group_id查询所有属于这个group的user
        '''
        kwargs = {
            'WHERE_AND':
                {
                    '=': {
                        'group_id': group_id,
                    }
                }
        }
        return self.user_group_db.simple_query(**kwargs)

    def get_user_role(self, user_id, group_id):
        '''
        通过group_id查询所有属于这个group的user
        '''
        kwargs = {
            'WHERE_AND':
                {
                    '=': {
                        'user_id': user_id,
                        'group_id': group_id,
                    }
                }
        }
        return self.user_group_db.simple_query(**kwargs)

    def query_one(self, where_field, where_field_value):
        return self.user_group_db.get_one(where_field, where_field_value)

    def add_user_group(self, insert_data):
        return self.user_group_db.insert(insert_data)

    def update_user_group(self, update_data, where_data):
        return self.user_group_db.update(update_data, where_data)

    def get_allgroup_user(self, user_id):
        '''
        通过user_id查询所有这个user对应的全部group
        '''
        kwargs = {
            'WHERE_AND':
            {
                '=': {
                    'user_id': user_id,
                }
            }
        }
        return self.user_group_db.simple_query(**kwargs)

    def query_user_role_group(self, user_id, group_id):
        kwargs = {
            'WHERE_AND':
                {
                    '=': {
                        'user_id': user_id,
                        'group_id': group_id,
                    }
                }
        }
        return self.user_group_db.simple_query(**kwargs)


# def update_expire_at(user_id, group_id):
#     # TODO 改进这个函数
#     '''这个函数不能放到下面的类中去，因为localtime()没学会转义'''
#     return user_group_db.update_expire_at(user_id, group_id)


# def query_user_role_group(user_id, role_id, group_id):
#     return user_group_db.query_user_role_group(user_id, role_id, group_id)


def delete_user(user_id, group_id):
    return user_group_db.delete_user(user_id, group_id)


def delete_users_in_group(group_id):
    return user_group_db.delete_users_in_group(group_id)


def get_data_by_group_name(group_name):
    user_group_data = user_group_db.get_data_by_group_name(group_name)
    if not user_group_data:
        return None
    return user_group_data[0]



