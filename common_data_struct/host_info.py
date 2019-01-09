# coding=utf8
'''
    物理机信息
'''
# __author__ =  ""

import base_define


class HostInfo(base_define.Base):

    def __init__(self):
        self.host_id = None
        self.sn = None  # 序列号
        self.name = None
        self.displayname = None
        self.ipaddress = None
        self.status = None
        self.typestatus = None
        self.hold_mem_gb = None
        self.manage_ip = None
        self.hostpool = None
        self.net_area = None
        self.datacenter = None
        self.dc_type = None
        self.instance_nums = None
        self.mem_assign_per = None
        self.cpu_core = None   # CPU核数  单位：核
        self.current_cpu_used = None  # CPU使用率
        self.mem_size = None  # 内存   单位：M
        self.current_mem_used = None    # 内存使用率
        self.disk_size = None  # 磁盘容量  单位：G
        self.current_disk_used = None  # 磁盘使用率
        self.collect_time = None
        self.hostpool_name = None
        self.area_name = None
        self.group_id = None
        self.num = None

    def init_from_db(self, one_db_data):
        self.area_name = one_db_data['area_name']
        self.datacenter = one_db_data['datacenter_name']
        self.dc_type = one_db_data['dc_type']
        self.net_area = one_db_data['net_area_name']
        self.hostpool = one_db_data['hostpool_name']
        self.displayname = one_db_data['host_name']  # 目前displayname跟name一样
        self.host_id = one_db_data['host_id']
        self.name = one_db_data['host_name']
        self.sn = one_db_data['sn']
        self.ipaddress = one_db_data['ipaddress']
        self.status = one_db_data['status']
        self.typestatus = one_db_data['typestatus']
        self.hold_mem_gb = one_db_data['hold_mem_gb']
        self.manage_ip = one_db_data['manage_ip']
        self.group_id = one_db_data['group_id']
        return self