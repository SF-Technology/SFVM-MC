# coding=utf8
'''
    机房服务
'''
# __author__ =  ""

from model import datacenter
from service.s_area import area_service as area_s
from helper.time_helper import get_datetime_str
from service.s_net_area import net_area as n_a_s



class DataCenterService:

    def __init__(self):
        self.datacenter_db = datacenter.DataCenter(db_flag='kvm', table_name='datacenter')

    def query_data(self, **params):
        return self.datacenter_db.simple_query(**params)

    def add_datacenter(self, insert_data):
        return self.datacenter_db.insert(insert_data)

    def get_datacenter_info(self, datacenter_id):
        return self.datacenter_db.get_one('id', datacenter_id)

    def update_datacenter_info(self, update_data, where_data):
        return self.datacenter_db.update(update_data, where_data)

    def delete_datacenter(self, datacenter_id):
        update_data = {
            'isdeleted': '1',
            'deleted_at': get_datetime_str()
        }
        where_data = {
            'id': datacenter_id
        }
        return self.datacenter_db.update(update_data, where_data)

    def get_datacenter_nums_in_area(self, area_id):
        '''
            获取指定区域下的机房数量
            这里包括区域和其子区域
        :param area_id:
        :return:
        '''
        child_nums, child_datas = area_s.AreaService().get_child_areas(area_id)
        area_ids_list = [child['id'] for child in child_datas]
        area_ids_list.append(area_id)
        area_ids_list = list(set(area_ids_list))

        params = {
            'WHERE_AND': {
                '=': {
                    'isdeleted': '0',
                },
                'in': {
                    'area_id': area_ids_list
                },
            },
        }
        total_nums, data = self.datacenter_db.simple_query(**params)

        return total_nums

    def get_datacenters_in_area(self, area_id):
        '''
            获取指定区域下的所有机房信息
        :param area_id:
        :return:
        '''
        params = {
            'WHERE_AND': {
                '=': {
                    'area_id': area_id,
                    'isdeleted': '0',
                },
            },
        }
        return self.datacenter_db.simple_query(**params)

    def get_all_datacenters_of_areas(self, area_ids_list):
        '''
            获取批量区域下所有的机房信息和总数量
        :param area_ids_list:
        :return:
        '''
        all_dc_nums = 0
        all_dc_data_list = []
        for _area_id in area_ids_list:
            _params = {
                'WHERE_AND': {
                    '=': {
                        'area_id': _area_id,
                        'isdeleted': '0',
                    },
                },
            }
            _dcs_num, _dcs_data = self.datacenter_db.simple_query(**_params)
            if _dcs_num > 0:
                for _dc in _dcs_data:
                    all_dc_data_list.append(_dc)
                all_dc_nums += _dcs_num
        return all_dc_nums, all_dc_data_list

    def check_dc_name_exist_in_same_type(self, dc_name, dc_type):
        '''
            检查同类机房下名字是否重复
        :param dc_name:
        :param dc_type:
        :return:
        '''
        params = {
            'WHERE_AND': {
                '=': {
                    'name': dc_name,
                    'dc_type': dc_type,
                    'isdeleted': '0',
                },
            },
        }
        dcs_nums, dcs_datas = self.datacenter_db.simple_query(**params)
        if dcs_nums > 0:
            return True
        return False

    def get_all_datacenters_by_name(self, dc_name):
        '''
            通过机房名称查找机房所有信息
        :param dc_name:
        :return:
        '''
        params = {
            'WHERE_AND': {
                '=': {
                    'name': dc_name,
                    'isdeleted': '0'
                }
            }
        }
        dcs_nums, dcs_datas = self.datacenter_db.simple_query(**params)
        if dcs_nums > 0:
            return True, dcs_datas
        return False, ''

    def get_all_datacenter_in_db(self):
        '''
            获取数据库中所有的机房信息
        :return:
        '''
        params = {
            'WHERE_AND': {
                '=': {
                    'isdeleted': '0'
                }
            }
        }
        return self.datacenter_db.simple_query(**params)

    def get_dctype_by_net_area_id(self,net_area_id):
        net_area_data = n_a_s.NetAreaService().get_net_area_info(net_area_id)
        datacenter_id = net_area_data['datacenter_id']
        datacenter_data = DataCenterService().get_datacenter_info(datacenter_id)
        dc_type = datacenter_data['dc_type']
        return dc_type

