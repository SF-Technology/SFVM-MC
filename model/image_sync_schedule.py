# coding=utf8
'''
    image_sync_schedule表
'''


from lib.dbs.mysql import Mysql
from model import base_model
import logging

class Image_sync_schedule(base_model.BaseModel):

    pass


def get_ondo_list(image_task_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
            SELECT
                a.sch1_state,
                a.sch1_starttime,
                a.sch1_endtime,
                a,sch2_state,
                a,sch2_starttime,
                a,sch2_endtime,
                a,sch3_state,
                a,sch3_starttime,
                a,sch3_endtime,
                a,sch4_state,
                a,sch4_starttime,
                a,sch4_endtime,
                a,sch5_state,
                a,sch5_starttime,
                a,sch5_endtime,
                a,sch6_state,
                a,sch6_starttime,
                a,sch6_endtime,
                a,sch7_state,
                a,sch7_starttime,
                a,sch7_endtime
            FROM
                image_sync_schedule a
            WHERE
                a.image_task_id = %s
        '''
    args = [image_task_id]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)