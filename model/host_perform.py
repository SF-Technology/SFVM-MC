# coding=utf8
'''
    host_perform表
'''


from model import base_model
from lib.dbs.mysql import Mysql


class HostPerform(base_model.BaseModel):

    pass


def get_metric_data(host_ips, start_time, end_time):
    ins = Mysql.get_instance("kvm")

    sql = '''
        SELECT
          T.ip,
          T.collect_time,
          SUM(current_cpu_used) current_cpu_used,
          SUM(cpu_core) cpu_core,
          SUM(current_mem_used) current_mem_used,
          SUM(mem_size) mem_size
        FROM (
            SELECT DISTINCT
              ip,
              collect_time,
              CASE metric_key WHEN 'current_cpu_used' THEN data_value ELSE 0 END 'current_cpu_used',
              CASE metric_key WHEN 'cpu_core' THEN data_value ELSE 0 END 'cpu_core',
              CASE metric_key WHEN 'current_mem_used' THEN data_value ELSE 0 END 'current_mem_used',
              CASE metric_key WHEN 'mem_size' THEN data_value ELSE 0 END 'mem_size'
            FROM
              tb_host_perform
    '''

    where_sql = ' WHERE 1 = 1 '
    args = []

    if host_ips:
        where_sql += ' AND ip IN %s'
        args.append(tuple(host_ips))

    if start_time and end_time:
        where_sql += 'AND (collect_time BETWEEN %s AND %s)'
        args.append(start_time)
        args.append(end_time)

    sql += where_sql
    sql += ' ORDER BY collect_time ) T GROUP BY T.ip, T.collect_time'
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)