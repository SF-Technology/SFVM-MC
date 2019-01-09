# coding=utf8
'''
    虚拟机信息
'''
# __author__ =  ""

import base_define
from service.v2v_task import v2v_instance_info as v2v_ins
from model import const_define


class InstanceInfo(base_define.Base):

    def __init__(self):
        self.instance_id = None
        self.name = None
        self.displayname = None
        self.uuid = None
        self.status = None
        self.ip_address = None
        self.hostpool = None
        self.owner = None
        self.app_info = None
        self.app_group = None
        self.app_group_id = None
        self.group_id = None
        self.host_ip = None
        self.dc_type = None
        self.request_id = None

    def user_instance(self, one_db_data):
        self.hostpool = one_db_data['hostpool_name']
        self.instance_id = one_db_data['id']
        self.name = one_db_data['instance_name']
        self.displayname = one_db_data['displayname']
        self.uuid = one_db_data['uuid']
        self.status = one_db_data['status']
        self.owner = one_db_data['owner']
        self.ip_address = one_db_data['ip_address']
        self.group_id = one_db_data['group_id']
        self.host_ip = one_db_data['host_ip']
        self.dc_type = one_db_data['dc_type']
        self.request_id = one_db_data['request_id']
        self.app_info = one_db_data['app_info']
        self.hostpool_id = one_db_data['hostpool_id']
        self.flavor_id = one_db_data['flavor_id']
        self.create_source = one_db_data['create_source']
        # v2v机器则在v2v_instance_info表获取system信息
        if one_db_data['create_source'] != '0':
            self.system = v2v_ins.v2vInstanceinfo().get_v2v_instance_info_by_instance_id(one_db_data['id'])['os_type']
        else:
            self.system = one_db_data['system']

        return self
