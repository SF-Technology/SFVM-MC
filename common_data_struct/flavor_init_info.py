# coding=utf8
'''
    创建VM时所需的flavor信息
'''
# __author__ =  ""

import base_define


class FlavorInitInfo(base_define.Base):

    def __init__(self):
        self.flavor_id = None
        self.name = None
        self.memory_mb = None
        self.root_disk_gb = None
        self.vcpu = None

    def init_from_db(self, one_db_data):
        self.flavor_id = one_db_data['id']
        self.name = one_db_data['name']
        self.memory_mb = one_db_data['memory_mb']
        self.root_disk_gb = one_db_data['root_disk_gb']
        self.vcpu = one_db_data['vcpu']

        return self