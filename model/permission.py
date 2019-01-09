# coding=utf8
'''
    role_perssion表
'''


from lib.dbs.mysql import Mysql
from model import base_model

class Permission(base_model.BaseModel):

    pass


def query_module():
    '''
    返回list, 在permission表中搜出全部的module
    :return [u'host', u'instance']
    '''
    ins = Mysql.get_instance("kvm")
    db_conn = ins.get_connection()
    sql = '''
            SELECT `module` FROM permission GROUP BY `module`
        '''
    args = []
    list_module = []
    data = ins.query(db_conn, sql, args)
    for i in data:
        list_module.append(i.get('module'))
    return list_module
