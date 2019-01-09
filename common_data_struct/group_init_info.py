# coding=utf8
'''
    创建VM时所需的group信息
'''
# __author__ =  ""

import base_define


class GroupInitInfo(base_define.Base):

    def __init__(self):
        self.name = None
        self.owner = None
        self.cpu = None
        self.mem = None
        self.disk = None
        self.vm = None
        self.area_list = None
        self.role_id = None

    def init_from_db(self, one_db_data):
        self.group_id = one_db_data['id']
        self.displayname = one_db_data['displayname']
        return self

    def init_group_info(self, one_db_data):
        self.name = one_db_data['name']
        self.owner = one_db_data['owner']
        self.role_id = one_db_data['role_id']
        self.cpu = one_db_data['cpu']
        self.mem = one_db_data['mem']
        self.disk = one_db_data['disk']
        self.vm = one_db_data['vm']
        self.area_list = one_db_data['area_list']

        return self