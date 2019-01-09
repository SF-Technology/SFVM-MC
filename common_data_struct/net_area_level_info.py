# coding=utf8
'''
    创建HOST时所需的网络区域以上的层级信息
'''


import base_define


class NetArealevelInfo(base_define.Base):

    def __init__(self):
        self.area = None
        self.child_area = None
        self.datacenter = None
        self.net_area_name = None
        self.net_area_id = None
        self.dc_type = None

    def init_from_db(self, one_db_data):
        self.dc_type = one_db_data['dc_type']
        self.datacenter = one_db_data['datacenter_name']
        self.net_area_name = one_db_data['net_area_name']
        self.net_area_id = one_db_data['id']

        return self