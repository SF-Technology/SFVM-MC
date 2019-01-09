# coding=utf8
'''
    镜像管理list信息
'''
# __author__ =  ""

import base_define
from model import const_define
from service.s_image import image_service


class ImageManagerInfo(base_define.Base):

    def __init__(self):
        self.image_id = None
        self.name = None
        self.displayname = None
        self.status = None
        self.related_image_tag = None
        self.template_vm_ip = None
        self.template_status = None
        self.create_time = None
        self.version = None
        self.system = None
        self.image_manage_message = None
        self.create_type = None


    def init_from_db(self, one_db_data):
        self.image_id = one_db_data['id']
        self.name = one_db_data['eimage_name']
        self.status = one_db_data['status']
        self.related_image_tag = one_db_data['related_image_tag']
        self.template_vm_ip = one_db_data['template_vm_ip']
        self.template_status = one_db_data['template_status']
        self.create_time = one_db_data['create_time']
        self.version = one_db_data['version']
        self.create_type = one_db_data['create_type']
        self.displayname = one_db_data['displayname']
        self.image_manage_message = one_db_data['message']
        self.system = one_db_data['os_type']
        return self