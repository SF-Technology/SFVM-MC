# coding=utf8
'''
    创建VM时所需的area层级信息 - 地区
'''


import base_define


class AreaDQInitInfo(base_define.Base):

    def __init__(self):
        self.hostpool_id = None
        self.hostpool_name = None
        self.net_area_name = None
        self.datacenter_name = None
        self.dc_type = None
        self.child_area_name = None
        self.area_name = None

    def init_from_db(self, one_db_data):
        self.hostpool_id = one_db_data['hostpool_id']
        self.hostpool_name = one_db_data['hostpool_name']
        self.net_area_name = one_db_data['net_area_name']
        self.datacenter_name = one_db_data['datacenter_name']
        self.dc_type = one_db_data['dc_type']

        return self