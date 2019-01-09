# coding=utf8
'''
    user_feedback服务
'''


import model.feedback as feedback_db
from lib.dbs.mysql import Mysql
import logging
import traceback


class FeedbackService:
    def __init__(self):
        self.feedback_db = feedback_db.Feedback(db_flag='kvm', table_name='feedback_info')

    def query_data(self, **params):
        return self.feedback_db.simple_query(**params)

    def add_feedback_info(self, insert_data):
        return self.feedback_db.insert(insert_data)

    def get_category_info(self):
        return feedback_db.query_category_info()




