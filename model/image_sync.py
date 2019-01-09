# coding=utf8
'''
    image_sync_task表
'''


from lib.dbs.mysql import Mysql
from model import base_model
import logging


class Image_sync(base_model.BaseModel):

    pass

def get_ondo_task(host_ip,image_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
            a.type,
            a.status,
            a.id,
            a.speed_limit
        FROM
            image_sync_task a
        WHERE
            a.host_ip = %s
            AND a.image_id = %s
            AND a.status != '2'
            AND  a.isdeleted = '0'
    '''
    args = [host_ip,image_id]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)

def get_host_working_list(host_ip):
    ins = Mysql.get_instance("kvm")
    sql = '''
         SELECT
            a.type,
            a.status,
            a.id,
            a.speed_limit,
            a.`image_id`
        FROM
            image_sync_task a
        WHERE
            a.host_ip = %s
            AND a.status IN ('0','1')
            AND  a.isdeleted = '0'
    '''
    args = [host_ip]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)
