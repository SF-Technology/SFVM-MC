# -*- coding:utf-8 -*-


from model import vip_info


class VIPService:

    def __init__(self):
        self.vip_db = vip_info.VipInfomation(db_flag='kvm', table_name='vip_info')

    def add_vip_info(self, insert_data):
        return self.vip_db.insert(insert_data)

    def get_vip_by_id(self, ip_id):
        return self.vip_db.get_one('ip_id', ip_id)
