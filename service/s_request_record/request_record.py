# -*- coding:utf-8 -*-


from model import request_record


class RequestRecordService:

    def __init__(self):
        self.request_record_db = request_record.RequestRecord(db_flag='kvm', table_name='request_record')

    def add_request_record_info(self, insert_data):
        return self.request_record_db.insert(insert_data)

    def request_db_query_data(self, **params):
        return self.request_record_db.simple_query(**params)

    def update_request_status(self, update_data, where_data):
        return self.request_record_db.update(update_data, where_data)

    def get_request_record_info_by_taskid_kvm(self, taskid_kvm):
        return self.request_record_db.get_one("taskid_kvm", taskid_kvm)

