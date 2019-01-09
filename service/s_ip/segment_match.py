# -*- coding:utf-8 -*-
# __author__ =  ""
# __author__ = ""
'''
    生产容灾网段对应表查询逻辑函数
'''

from model import segment_match


class SegmentMatchService:

    def __init__(self):
        self.segment_match_db = segment_match.SegmentMatch(db_flag='kvm', table_name='segment_match')

    def get_segment_match_info_by_prd_segment_id(self, prd_segment_id):
        return self.segment_match_db.get_one('prd_segment_id', prd_segment_id)

    def get_segment_match_info_by_dr_segment_id(self, dr_segment_id):
        return self.segment_match_db.get_one('dr_segment_id', dr_segment_id)

    def add_segment_match_info(self, insert_data):
        return self.segment_match_db.insert(insert_data)

