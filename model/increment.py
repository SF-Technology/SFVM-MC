# coding=utf8
'''
    increment表
'''


from model import base_model
from lib.dbs.mysql import Mysql


class Increment(base_model.BaseModel):

    pass


def increase_num_increment_value(prex, num):
    ins = Mysql.get_instance("kvm")
    sql = '''
        UPDATE increment
        SET increment_value =  increment_value + %s
        WHERE prex_str = %s
    '''
    args = [num, prex]
    db_conn = ins.get_connection()
    return ins.execute(db_conn, sql, args)


def delete_increment_value_by_prex(prex):
    ins = Mysql.get_instance("kvm")
    sql = '''
        DELETE FROM increment where prex_str = %s
    '''
    args = [prex]
    db_conn = ins.get_connection()
    return ins.execute(db_conn, sql, args)