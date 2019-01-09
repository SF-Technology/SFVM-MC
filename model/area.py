# coding=utf8
'''
    area表
'''
# __author__ =  ""

from lib.dbs.mysql import Mysql
from model import base_model


class Area(base_model.BaseModel):

    pass


def get_area_info():
    '''
        获取区域 - 父区域信息
    :return:
    '''
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT re.* FROM (
            SELECT
                area.id, area.name, area.parent_id,q.name AS parent_name
            FROM area
            LEFT JOIN
              (SELECT id, name FROM area WHERE parent_id = -1 AND isdeleted = '0') q ON area.parent_id = q.id
            WHERE isdeleted = '0'
        ) re
        WHERE re.id NOT IN (SELECT parent_id FROM area)
    '''
    args = []
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)

