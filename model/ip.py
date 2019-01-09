# coding=utf8
'''
    IP表
'''


from lib.dbs.mysql import Mysql
from model.const_define import IPStatus
from model import base_model


class IP(base_model.BaseModel):

    pass


def delete_ip(ip_id):
    '''
        删除IP
    :param ip_id:
    :return:
    '''
    ins = Mysql.get_instance("kvm")
    db_conn = ins.get_connection()
    sql = '''
                delete from ip where id = %s
            '''
    args = [ip_id]
    return ins.execute(db_conn, sql, args)


def get_available_ip(segment_id):
    ins = Mysql.get_instance("kvm")
    # select...for update 保留指定的行
    sql = '''
            SELECT * FROM ip WHERE status = %s AND segment_id = %s FOR UPDATE
        '''
    args = [IPStatus.UNUSED, segment_id]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_available_dr_ip(segment_id, group_id):
    ins = Mysql.get_instance("kvm")
    # select...for update 保留指定的行
    sql = '''
            SELECT * FROM ip WHERE status = %s AND segment_id = %s AND group_id = %s FOR UPDATE
        '''
    args = [IPStatus.UNUSED, segment_id, group_id]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_one_available_ip(segment_id):
    ins = Mysql.get_instance("kvm")
    # select...for update 保留指定的行
    sql = '''
            SELECT * FROM ip WHERE status = %s AND segment_id = %s FOR UPDATE
        '''
    args = [IPStatus.UNUSED, segment_id]
    db_conn = ins.get_connection()
    return ins.query_one(db_conn, sql, args)


def get_one_available_dr_ip(segment_id, group_id):
    ins = Mysql.get_instance("kvm")
    # select...for update 保留指定的行
    sql = '''
            SELECT * FROM ip WHERE status = %s AND segment_id = %s AND group_id = %s FOR UPDATE
        '''
    args = [IPStatus.UNUSED, segment_id, group_id]
    db_conn = ins.get_connection()
    return ins.query_one(db_conn, sql, args)


def ip_inited_in_segment(segment_id):
    '''
        获取指定网段ID下已经初始化的IP
    :param segment_id:
    :return:
    '''
    ins = Mysql.get_instance("kvm")
    sql = '''
                SELECT ip_address FROM ip WHERE segment_id = %s
            '''
    args = [segment_id]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def allocate_ip_to_instance(insert_data, db_conn=None):
    ins = Mysql.get_instance("kvm")
    return ins.simple_insert('instance_ip', insert_data, db_conn)


def get_ip_instance_info(instance_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
            SELECT a.* FROM ip a LEFT JOIN instance_ip b ON a.id = b.ip_id
              WHERE b.isdeleted = '0'
              AND b.instance_id = %s
        '''
    args = [instance_id]
    db_conn = ins.get_connection()
    return ins.query_one(db_conn, sql, args)


def get_instance_info_by_ip(ip_address):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
          a.name instance_name,
          a.uuid instance_uuid,
          a.id instance_id,
          e.ipaddress host_ip,
          g.name net_area_name,
          h.name datacenter_name,
          h.dc_type env
        FROM instance a
        LEFT JOIN
            instance_ip b ON a.id = b.instance_id AND b.isdeleted = '0'
        LEFT JOIN
            ip c ON c.id = b.ip_id
        LEFT JOIN
            instance_host d ON a.id = d.instance_id AND d.isdeleted = '0'
        LEFT JOIN
            host e ON e.id = d.host_id AND e.isdeleted = '0'
        LEFT JOIN
            hostpool f ON f.id = e.hostpool_id AND f.isdeleted = '0'
        LEFT JOIN
            net_area g ON g.id = f.net_area_id AND g.isdeleted = '0'
        LEFT JOIN
            datacenter h ON h.id = g.datacenter_id AND h.isdeleted = '0'
        WHERE a.isdeleted = '0' AND c.ip_address = %s
    '''
    args = [ip_address]
    db_conn = ins.get_connection()
    return ins.query_one(db_conn, sql, args)


def ip_all_in_segment(segment_id):
    '''
        获取指定网段ID下所有ip
    :param segment_id:
    :return:
    '''
    ins = Mysql.get_instance("kvm")
    sql = '''
                SELECT ip_address, status FROM ip WHERE segment_id = %s
            '''
    args = [segment_id]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)
