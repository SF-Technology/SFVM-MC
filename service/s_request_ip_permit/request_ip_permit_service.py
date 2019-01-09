# -*- coding:utf-8 -*-
# __author__ =  ""
from model import request_ip_permit


class RequestIpPermitService(object):

    def __init__(self):
        self.request_ip_premit_db = request_ip_permit.RequestIpPermit(db_flag='kvm', table_name='request_ip_permit')

    def query_data(self, **params):
        return self.request_ip_premit_db.simple_query(**params)

    def add_request_ip(self, insert_data):
        return self.request_ip_premit_db.insert(insert_data)

