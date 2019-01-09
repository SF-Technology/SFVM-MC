# coding=utf8
'''
    区域与子区域的层级信息
'''
# __author__ =  ""

import base_define


class ArealevelInfo(base_define.Base):

    def __init__(self):
        self.id = None
        self.area = None
        self.child_area = None

    def init_from_db(self, one_db_data):
        self.id = one_db_data['id']

        return self