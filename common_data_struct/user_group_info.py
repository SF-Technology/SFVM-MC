# coding=utf8
'''
    tb_user表中用户信息字段
'''


import base_define
from service.s_user import user_service
import datetime



class UserGroupInfo(base_define.Base):

    def __init__(self):
        self.user_id = None


    def user_group_info(self, one_db_data):
        self.user_id = one_db_data['user_id']
        self.user_name = one_db_data['user_name']
        return self