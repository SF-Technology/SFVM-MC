# coding=utf8
'''
    net_area显示信息
'''


import base_define


class NetAreaInfo(base_define.Base):

    def __init__(self):
        self.net_area_id = None
        self.net_area_name = None
        self.datacenter_name = None
        self.dc_type = None
        self.hostpool_nums = None
        self.imagecache01 = None
        self.imagecache02 = None

    def net_area_info(self, one_db_data):
        self.net_area_id = one_db_data['net_area_id']
        self.net_area_name = one_db_data['net_area_name']
        self.datacenter_name = one_db_data['datacenter_name']
        self.dc_type = one_db_data['dc_type']
        self.hostpool_nums = one_db_data['hostpool_nums']

        return self