# coding=utf8
'''
    创建VM时所需的group信息
'''


import base_define


class GroupInitInfo(base_define.Base):

    def __init__(self):
        self.group_id = None
        self.name = None
        self.owner = None
        self.cpu = None
        self.mem = None
        self.disk = None
        self.vm = None
        self.role_id = None
        self.dc_type = None

    def init_from_db(self, one_db_data):
        self.group_id = one_db_data['id']
        self.name = one_db_data['name']
        self.owner = one_db_data['owner']
        self.cpu = one_db_data['cpu']
        self.mem = one_db_data['mem']
        self.disk = one_db_data['disk']
        self.vm = one_db_data['vm']
        self.role_id = one_db_data['role_id']
        self.dc_type = one_db_data['dc_type']
        return self

    def init_from_db_1(self, one_db_data):
        self.group_id = one_db_data['id']
        self.name = one_db_data['name']
        self.owner = one_db_data['owner']
        self.cpu = one_db_data['cpu']
        self.mem = one_db_data['mem']
        self.disk = one_db_data['disk']
        self.vm = one_db_data['vm']
        self.dc_type = one_db_data['dc_type']
        return self

