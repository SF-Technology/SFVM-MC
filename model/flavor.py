# coding=utf8
'''
    flavor表
'''


from lib.dbs.mysql import Mysql
from model import base_model


class Flavor(base_model.BaseModel):

    pass


def get_flavor_by_vcpu_and_vmem(vcpu, vmem):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
            id
        FROM
            flavor
        WHERE
            vcpu = %s
            AND memory_mb = %s
            AND isenable = '1'
            AND isdeleted = '0'
    '''
    args = [vcpu, vmem]
    db_conn = ins.get_connection()
    return ins.query_one(db_conn, sql, args)
