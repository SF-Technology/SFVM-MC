# coding=utf8
'''
    机房信息
'''
# __author__ =  ""

import base_define


class DataCenterInfo(base_define.Base):

    def __init__(self):
        self.datacenter_id = None
        self.displayname = None
        self.dc_type = None
        self.hostpool_nums = None
        self.province = None
        self.address = None
        self.description = None

    def init_from_db(self, one_db_data):
        self.datacenter_id = one_db_data['datacenter_id']
        self.displayname = one_db_data['displayname']
        self.dc_type = one_db_data['dc_type']
        self.hostpool_nums = one_db_data['hostpool_nums']
        self.province = one_db_data['province']
        self.address = one_db_data['address']
        self.description = one_db_data['description']
        return self