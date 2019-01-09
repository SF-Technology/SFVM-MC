#coding=utf8



from lib.dbs.mysql import Mysql
from model import base_model


class User(base_model.BaseModel):

    pass


def user_area_info(user_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
          SELECT DISTINCT t.area_id FROM user_group
            LEFT JOIN
            (SELECT area_id, group_id FROM access)t ON user_group.group_id = t.group_id
            WHERE user_group.user_id = %s
            ORDER BY t.area_id
        '''
    args = [user_id]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


