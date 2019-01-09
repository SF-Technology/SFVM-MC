# coding=utf8
'''
    集群信息
'''
# __author__ = ""

import base_define


class HostPoolInfo(base_define.Base):

    def __init__(self):
        self.hostpool_id = None
        self.displayname = None
        self.datacenter = None
        self.net_area = None
        self.area_name = None
        self.hosts_nums = 0
        self.instances_nums = 0
        self.cpu_nums = 0
        self.mem_nums = 0
        self.cpu_used_per = 0
        self.mem_used_per = 0
        self.mem_assign = 0
        self.mem_assign_per = 0
        self.least_host_num = None
        self.dc_type = None
        self.available_create_vm_nums = 0
        self.available_ip_nums = 0
        self.hostpool_type = "0"
        self.app_code = ""

    def init_from_db(self, one_db_data):
        self.hostpool_id = one_db_data['hostpool_id']
        self.displayname = one_db_data['hostpool_name']
        self.least_host_num = one_db_data['least_host_num']
        self.datacenter = one_db_data['datacenter_name']
        self.net_area = one_db_data['net_area_name']
        self.area_name = one_db_data['area_name']
        self.instances_nums = one_db_data['instances_nums']
        self.dc_type = one_db_data['dc_type']
        self.hostpool_type = "1" if one_db_data['hostpool_type'] == "1" else "0"
        self.app_code = one_db_data['app_code'] if one_db_data['app_code'] else ""
        return self