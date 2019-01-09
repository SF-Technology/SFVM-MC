# coding=utf8
'''
    access表
'''
# __author__ =  ""

from lib.dbs.mysql import Mysql
from model import base_model


class Access(base_model.BaseModel):

    pass


def add_access_info(values):
    '''
    :param 格式 values = [(1, 2, 3), (1, 4, 5)]
    批量插入group_role_area信息到access表中
    :return:
    '''
    ins = Mysql.get_instance("kvm")
    sql = '''
            INSERT INTO `access` (group_id, role_id, area_id)
            VALUES
        '''
    i = 0
    while i < len(values) - 1:
        sql += str(values[i]) + ','
        i += 1
    sql += str(values[-1])
    db_conn = ins.get_connection()
    return ins.insert(db_conn, sql)


def delete_access_info(group_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
            DELETE FROM access WHERE group_id = %s
        '''
    args = [group_id]
    db_conn = ins.get_connection()
    return ins.execute(db_conn, sql, args)


def delete_access_info_by_area_id(area_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
        DELETE FROM access WHERE area_id = %s
    '''
    args = [area_id]
    db_conn = ins.get_connection()
    return ins.execute(db_conn, sql, args)