# -*- coding:utf-8 -*-

# from model import ip
from model import ip_lock as ip_lock_db


class IpLockService:

    def __init__(self):
        self.ip_lock_db = ip_lock_db.IpLock(db_flag='kvm', table_name='ip_lock')

    def update_ip_lock_info(self, update_data, where_data):
        return self.ip_lock_db.update(update_data, where_data)

    def get_ip_lock_info(self, table_name='ip'):
        return self.ip_lock_db.get_one("table_name", table_name)

    def add_ip_lock_db(self, insert_data):
        return self.ip_lock_db.insert(insert_data)
