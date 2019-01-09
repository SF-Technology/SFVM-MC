# coding=utf8
'''
    镜像信息
'''


import base_define
from model import const_define


class ImageInfo(base_define.Base):

    def __init__(self):
        self.image_id = None
        self.displayname = None
        self.system = None
        self.create_time = None
        self.description = None
        self.version = None
        self.md5 = None
        self.url = None
        self.actual_size_mb = None
        self.size_gb = None

    def init_from_db(self, one_db_data):
        self.image_id = one_db_data['id']
        self.displayname = one_db_data['displayname']
        self.system = one_db_data['system']
        self.create_time = one_db_data['created_at']
        self.description = one_db_data['description']
        self.version = one_db_data['version']
        self.md5 = one_db_data['md5']
        self.url = one_db_data['url']
        self.actual_size_mb = one_db_data['actual_size_mb']
        self.size_gb = one_db_data['size_gb']

        return self