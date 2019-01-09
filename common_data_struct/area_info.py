# coding=utf8
'''
    区域信息
'''
# __author__ =  ""

import base_define


class AreaInfo(base_define.Base):

    def __init__(self):
        self.area_id = None
        self.displayname = None
        self.child_areas_nums = 0
        self.datacenter_nums = 0
        self.hostpool_nums = 0
        self.host_run_nums = 0
        self.host_nums = 0
        self.instance_run_nums = 0
        self.instance_nums = 0
        self.manager = None


    def init_from_db(self, one_db_data):
        self.area_id = one_db_data['id']
        self.displayname = one_db_data['displayname']
        self.manager = one_db_data['manager']
        return self
