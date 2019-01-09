# coding=utf8
'''
    组_角色_区域列表信息
'''
# __author__ =  ""

import base_define


class AcessInfo(base_define.Base):

    def __init__(self):
        self.area_name = 0
        self.group_name = 0
        self.role_name = 0


    def init_from_db(self, one_db_data):
        self.area_id = one_db_data['id']
        self.displayname = one_db_data['displayname']
        self.manager = one_db_data['manager']
        return self
