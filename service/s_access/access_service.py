# coding=utf8
'''
    access list
'''
# __author__ =  ""

from model import access
from s_user_group import user_group_service
import logging
import json_helper
from model.const_define import ErrorCode
from s_role import role_service


class AccessService:

    def __init__(self):
        self.access_db = access.Access(db_flag='kvm', table_name='access')

    def get_groups_info(self, user_id):
        '''
        通过user_id查询user_group表中它所属的所有group_id，再通过group_id查询所有access表中它们对应的area_id
        :return: (2L, ({'area_id': 1L, 'group_id': 1L, 'role_id': 1L}, {'area_id': 2L, 'group_id': 2L, 'role_id': 2L})
        '''
        groups_nums, groups_data = user_group_service.UserGroupService().get_allgroup_user(user_id)
        if groups_nums <= 0:
            logging.info('no group exist with this user in table user_group')
            return 0, []
        group_list = []
        for i in groups_data:
            group_list.append(i.get('group_id'))
        kwargs = {
            'WHERE_AND':
                {
                    'in': {
                        'group_id': group_list
                    }
                }
        }
        return self.access_db.simple_query(**kwargs)

    def add_info(self, insert_data):
        return self.access_db.insert(insert_data)

    def query_info(self, kwargs):
        return self.access_db.simple_query(**kwargs)

    def update_info(self, update_data, where_data):
        return self.access_db.update(update_data, where_data)

    def get_one(self, where_field, where_field_value):
        return self.access_db.get_one(where_field, where_field_value)

    def check_area_access(self, area_id):
        '''
            检测指定区域是否有权限和组的关系
        :param area_id:
        :return:
        '''
        kwargs = {
            'WHERE_AND': {
                '=': {
                    'area_id': area_id
                }
            }
        }
        nums, datas = self.access_db.simple_query(**kwargs)
        if nums > 0:
            return True
        return False


def add_access_list(group_id, role_id, area_str):
    '''批量增加access表中的信息'''
    values = []
    area_list = area_str.split(",")
    for area_id in area_list:
        values.append((group_id, role_id, int(area_id)))
    print values
    return access.add_access_info(values)


def delete_access_info_by_area_id(area_id):
    '''
        删除指定区域的access信息
    :param area_id:
    :return:
    '''
    return access.delete_access_info_by_area_id(area_id)

