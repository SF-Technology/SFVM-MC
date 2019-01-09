# coding=utf8
'''
    USER服务
'''
# __author__ =  ""

from model import net_area
from helper.time_helper import get_datetime_str


class NetAreaService:

    def __init__(self):
        self.net_area_db = net_area.NetArea(db_flag='kvm', table_name='net_area')

    def query_data(self, **params):
        return self.net_area_db.simple_query(**params)

    def add_net_area(self, insert_data):
        return self.net_area_db.insert(insert_data)

    def update_net_area_info(self, update_data, where_data):
        return self.net_area_db.update(update_data, where_data)

    def get_net_area_info(self, net_area_id):
        return self.net_area_db.get_one('id', net_area_id)

    def delete_net_area(self, net_area_id):
        update_data = {
            'isdeleted': '1',
            'deleted_at': get_datetime_str()
        }
        where_data = {
            'id': net_area_id
        }
        return self.net_area_db.update(update_data, where_data)

    def get_net_area_nums_in_dc(self, datacenter_id):
        '''
            获取指定机房下网络区域数量
        :param datacenter_id:
        :return:
        '''
        params = {
            'WHERE_AND': {
                "=": {
                    'datacenter_id': datacenter_id,
                    'isdeleted': '0'
                }
            },
        }
        total_nums, data = self.net_area_db.simple_query(**params)
        return total_nums

    def get_net_area_datas_in_dc(self, datacenter_id):
        '''
            获取指定机房下网络区域信息
        :param datacenter_id:
        :return:
        '''
        params = {
            'WHERE_AND': {
                "=": {
                    'datacenter_id': datacenter_id,
                    'isdeleted': '0'
                }
            },
        }
        return self.net_area_db.simple_query(**params)


def get_level_info():
    return net_area.get_level_info()


def get_area_info(**kwargs):
    return net_area.get_area_hostpool_datacenter(**kwargs)


def get_datacenter_area_info():
    return net_area.get_datacenter_area_info()


def check_name_exist_in_same_dc_type(net_area_name, dc_type):
    '''
        判断同一环境下机房的网络区域是否重名
    :param net_area_name:
    :param dc_type:
    :return:
    '''
    data = net_area.check_name_in_same_dc_type(net_area_name, dc_type)
    if data:
        return True
    return False


def get_netarea_info_by_name(env, dc_name, net_area_name):
    '''
         获取指定环境、机房下的指定网络区域是否存在
    :param env:
    :param dc_name:
    :param net_area_name:
    :return:
    '''
    return net_area.get_netarea_info_by_name(env, dc_name, net_area_name)


