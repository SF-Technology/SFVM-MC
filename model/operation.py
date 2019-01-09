#coding=utf8
'''
    operation_records表
'''


from lib.dbs.mysql import Mysql
from model import base_model
import json, MySQLdb


class Operation(base_model.BaseModel):
    pass


def query_operation_record(**params):
    ins = Mysql.get_instance("kvm")
    db_conn = ins.get_connection()
    sql = "SELECT operator, operator_ip, operation_object, operation_action, operation_date,operation_result,extra_data FROM operation_records WHERE 1=1"

    arg = []
    data = ins.query(db_conn, sql, arg)

    return data


def query_operation_list(**kwargs):
    ins = Mysql.get_instance("kvm")
    db_conn = ins.get_connection()
    sql = '''
             SELECT
                  operator, operator_ip, operation_object, operation_action, operation_date, operation_result, extra_data
             FROM
                  operation_records
             WHERE
                  1=1
                  '''

    args = []
    where_sql = ''
    if kwargs['WHERE_AND']['like']['operator']:
        where_sql += ' AND operator LIKE %s'
        args.append(kwargs['WHERE_AND']['like']['operator'])

    if kwargs['WHERE_AND']['like']['operator_ip']:
        where_sql += ' AND operator_ip LIKE %s'
        args.append(kwargs['WHERE_AND']['like']['operator_ip'])

    if kwargs['WHERE_AND']['=']['operation_object']:
        where_sql += ' AND operation_object = %s'
        args.append(kwargs['WHERE_AND']['=']['operation_object'])

    if kwargs['WHERE_AND']['=']['operation_action']:
        where_sql += ' AND operation_action = %s'
        args.append(kwargs['WHERE_AND']['=']['operation_action'])

    if kwargs['WHERE_AND']['like']['operation_result']:
        where_sql += ' AND operation_result LIKE %s'
        args.append(kwargs['WHERE_AND']['like']['operation_result'])

    if kwargs['WHERE_AND']['like']['extra_data']:
        where_sql += ' AND extra_data LIKE %s'
        args.append(kwargs['WHERE_AND']['like']['extra_data'])

    if kwargs['WHERE_AND']['>=']['operation_date']:
        where_sql += ' AND operation_date >= %s'
        args.append(kwargs['WHERE_AND']['>=']['operation_date'])

    if kwargs['WHERE_AND']['<=']['operation_date']:
        where_sql += ' AND operation_date <= %s'
        args.append(kwargs['WHERE_AND']['<=']['operation_date'])

    sql += where_sql
    sql += ' ORDER BY operation_date DESC '

    total_data = ins.query(db_conn, sql, args)
    total_nums = len(total_data)
    if kwargs.get('page_no') and kwargs.get('page_size'):
        page_no = int(kwargs['page_no'])
        page_size = kwargs['page_size']
        limit_sql = 'LIMIT %d, %d' % ((int(page_no) - 1)*int(page_size), int(page_size))
        sql += limit_sql
    data = ins.query(db_conn, sql, args)
    return total_nums, data
