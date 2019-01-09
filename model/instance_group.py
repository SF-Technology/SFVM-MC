# coding=utf8
'''
    instance_group表
'''


from lib.dbs.mysql import Mysql
from model import base_model


class InstanceGroup(base_model.BaseModel):

    pass


def query_data(instance_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
            SELECT * FROM instance_group WHERE instance_id = %s
        '''
    args = [instance_id]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


