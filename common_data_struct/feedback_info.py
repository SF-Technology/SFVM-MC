# coding=utf8
'''
    用户反馈信息
'''
# __author__ =  ""

import base_define

class FeedbackInfo(base_define.Base):

    def __init__(self):
        self.problem_description = None
        self.network_address = None
        self.submit_time = None

    def init_from_db(self, one_db_data):
        self.problem_description = one_db_data['problem_description']
        self.network_address = one_db_data['network_address']
        self.submit_time = one_db_data['submit_time']
        self.problem_category = one_db_data['problem_category']

        return self
