# coding=utf8
'''
    区域服务
'''
# __author__ =  ""

from model import area
from helper.time_helper import get_datetime_str


class AreaService:

    def __init__(self):
        self.area_db = area.Area(db_flag='kvm', table_name='area')

    def add_area(self, insert_data):
        return self.area_db.insert(insert_data)

    def update_area_info(self, update_data, where_data):
        return self.area_db.update(update_data, where_data)

    def delete_area(self, area_id):
        update_data = {
            'isdeleted': '1',
            'deleted_at': get_datetime_str()
        }
        where_data = {
            'id': area_id
        }
        return self.area_db.update(update_data, where_data)

    def query_data(self, **params):
        return self.area_db.simple_query(**params)

    def get_all_areas(self):
        params = {
            'WHERE_AND': {
                '=': {
                    'isdeleted': '0',
                },
            },
            'ORDER': [
                ['id', 'desc'],
            ],
        }
        return self.area_db.simple_query(**params)

    def get_area_zb_info(self):
        return self.area_db.get_one("area_type", '0')

    def get_area_info(self, area_id):
        return self.area_db.get_one("id", area_id)

    def get_child_areas_nums(self, area_id):
        params = {
            'WHERE_AND': {
                '=': {
                    'parent_id': area_id,
                    'isdeleted': '0',
                },
            },
        }
        total_nums, data = self.area_db.simple_query(**params)
        return total_nums

    def get_child_areas(self, area_id):
        '''
            获取区域的子区域
        :param area_id:
        :return:
        '''
        params = {
            'WHERE_AND': {
                '=': {
                    'parent_id': area_id,
                    'isdeleted': '0',
                },
            },
        }
        return self.area_db.simple_query(**params)

    def get_available_parents(self, all_area_ids):
        '''
            获取适合做父区域的区域
            由于这里只会有（区域 - 子区域）两级，所有父区域ID为-1（即不是任何区域的子区域）的区域都可以
        :return:
        '''
        params = {
            'WHERE_AND': {
                'in': {
                    'id': all_area_ids
                },
                '=': {
                    'parent_id': -1,
                    'isdeleted': '0',
                },
            },
        }
        return self.area_db.simple_query(**params)

    def check_area_name_exist(self, area_name):
        '''
            检查指定区域名是否存在
        :param area_name:
        :return:
        '''
        params = {
            'WHERE_AND': {
                '=': {
                    'name': area_name,
                    'isdeleted': '0',
                },
            },
        }
        area_nums, area_datas = self.area_db.simple_query(**params)
        if area_nums > 0:
            return True
        return False

