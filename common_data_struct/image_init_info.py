# coding=utf8
'''
    创建VM时所需的image信息
'''
# __author__ =  ""

import base_define


class ImageInitInfo(base_define.Base):

    def __init__(self):
        self.image_id = None
        self.name = None
        self.displayname = None

    def init_from_db(self, one_db_data):
        self.image_id = one_db_data['id']
        self.name = one_db_data['name']
        self.displayname = one_db_data['displayname']

        return self