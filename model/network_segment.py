# coding=utf8
'''
    network_segment表
'''
# __author__ =  ""
# __author__ = ""

from lib.dbs.mysql import Mysql
from model import base_model


class NetworkSegment(base_model.BaseModel):

    pass


def ip_info_in_segment(segment_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
            SELECT id,vlan,netmask,gateway_ip,dns1,dns2 FROM network_segment WHERE id = %s
        '''
    args = [segment_id]
    db_conn = ins.get_connection()
    return ins.query_one(db_conn, sql, args)


def get_level_info(segment_type=False):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
          a.id,
          a.segment,
          b.displayname net_area,
          b.id net_area_id,
          c.displayname datacenter,
          c.dc_type,
          d.id area_id
        FROM
          network_segment a, net_area b, datacenter c, area d
        WHERE
          a.net_area_id = b.id
          AND b.datacenter_id = c.id
          AND c.area_id = d.id
          AND b.isdeleted = '0'
          AND c.isdeleted = '0'
          AND d.isdeleted = '0'
    '''
    args = []
    if segment_type:
        sql += "AND a.segment_type = %s"
        args.append(segment_type)
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def _get_level_info(segment_type=False):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
          a.id,
          a.segment,
          b.displayname net_area,
          b.id net_area_id,
          c.displayname datacenter,
          c.dc_type,
          d.id area_id
        FROM network_segment AS a
        RIGHT JOIN net_area AS b ON  a.net_area_id = b.id
	    RIGHT JOIN datacenter AS c ON b.datacenter_id = c.id
        RIGHT JOIN  AREA AS d ON c.area_id = d.id
        WHERE
	b.isdeleted = '0'
        AND c.isdeleted = '0'
        AND d.isdeleted = '0'
    '''
    args = []
    if segment_type:
        sql += "AND a.segment_type = %s"
        args.append(segment_type)
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_segments_info_by_name(net_area_name, datacenter_name, env):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
          a.id,
          a.segment,
          a.segment_type,
          a.netmask,
          a.vlan,
          a.gateway_ip,
          a.dns1,
          a.dns2,
          b.displayname net_area,
          c.displayname datacenter,
          c.dc_type,
          d.id area_id
        FROM
          network_segment a, net_area b, datacenter c, area d
        WHERE
          a.net_area_id = b.id
          AND b.datacenter_id = c.id
          AND c.area_id = d.id
          AND b.isdeleted = '0'
          AND c.isdeleted = '0'
          AND d.isdeleted = '0'
          AND b.name = %s
          AND c.name = %s
          AND c.dc_type = %s
    '''
    args = [net_area_name, datacenter_name, env]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_segments_info_by_type(net_area_name, datacenter_name, env, segment_type):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
          a.id,
          a.segment,
          a.segment_type,
          a.netmask,
          a.vlan,
          a.gateway_ip,
          a.dns1,
          a.dns2,
          b.displayname net_area,
          c.displayname datacenter,
          c.dc_type,
          d.id area_id
        FROM
          network_segment a, net_area b, datacenter c, area d
        WHERE
          a.net_area_id = b.id
          AND b.datacenter_id = c.id
          AND c.area_id = d.id
          AND b.isdeleted = '0'
          AND c.isdeleted = '0'
          AND d.isdeleted = '0'
          AND b.name = %s
          AND c.name = %s
          AND c.dc_type = %s
          AND a.segment_type = %s
    '''
    args = [net_area_name, datacenter_name, env, segment_type]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_ips_by_segment(segment_id, segment, page=1):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
          a.id,
          a.ip_address,
          a.status,
          b.segment,
          b.id segment_id,
          b.netmask,
          c.displayname net_area
        FROM
          ip a,
          network_segment b,
          net_area c
        WHERE
          a.segment_id = b.id
          AND b.net_area_id = c.id
          AND b.id = %s
    '''
    args = [segment_id]

    if page:
        # 根据网段取前三位匹配的IP
        ip_mask = segment.split(".")[0] + "." + segment.split(".")[1] + "." + str(int(segment.split(".")[2]) + page - 1)
        sql += " AND a.ip_address LIKE %s"
        args.append("%" + ip_mask + "%")
    sql += " ORDER BY INET_ATON(a.ip_address) ASC"
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_network_segments_info_by_name_paging(datacenter_name, env, net_area_name, page_num, page_size):
    ins = Mysql.get_instance("kvm")
    db_conn = ins.get_connection()
    sql = '''
        SELECT
          a.id,
          a.segment,
          a.netmask,
          a.vlan,
          a.gateway_ip,
          a.dns1,
          a.dns2,
          b.displayname net_area,
          c.displayname datacenter,
          c.dc_type,
          d.id area_id
        FROM
          network_segment a, net_area b, datacenter c, area d
        WHERE
          a.net_area_id = b.id
          AND b.datacenter_id = c.id
          AND c.area_id = d.id
          AND b.isdeleted = '0'
          AND c.isdeleted = '0'
          AND d.isdeleted = '0'
          AND b.name = %s
          AND c.name = %s
          AND c.dc_type = %s
    '''
    # 计算总数  用于分页使用
    args = [net_area_name, datacenter_name, env]

    total_data = ins.query(db_conn, sql, args)
    total_nums = len(total_data)
    limit_sql = ' LIMIT %d, %d' % ((int(page_num) - 1) * int(page_size), int(page_size))
    sql += limit_sql
    data = ins.query(db_conn, sql, args)
    return total_nums, data


def get_network_segments_info_in_dc_by_name_paging(datacenter_name, env, page_num, page_size):
    ins = Mysql.get_instance("kvm")
    db_conn = ins.get_connection()
    sql = '''
        SELECT
          a.id,
          a.segment,
          a.netmask,
          a.vlan,
          a.gateway_ip,
          a.dns1,
          a.dns2,
          b.name net_area,
          c.displayname datacenter,
          c.dc_type,
          d.id area_id
        FROM
          network_segment a, net_area b, datacenter c, area d
        WHERE
          a.net_area_id = b.id
          AND b.datacenter_id = c.id
          AND c.area_id = d.id
          AND b.isdeleted = '0'
          AND c.isdeleted = '0'
          AND d.isdeleted = '0'
          AND c.name = %s
          AND c.dc_type = %s
    '''
    # 计算总数  用于分页使用
    args = [datacenter_name, env]

    total_data = ins.query(db_conn, sql, args)
    total_nums = len(total_data)
    limit_sql = ' LIMIT %d, %d' % ((int(page_num) - 1) * int(page_size), int(page_size))
    sql += limit_sql
    data = ins.query(db_conn, sql, args)
    return total_nums, data


def get_network_segments_info_by_segment_name(datacenter_name, env, net_area_name, network_segment):
    ins = Mysql.get_instance("kvm")
    db_conn = ins.get_connection()
    sql = '''
        SELECT
          a.id,
          a.segment,
          a.netmask,
          a.vlan,
          a.gateway_ip,
          a.dns1,
          a.dns2,
          b.displayname net_area,
          c.displayname datacenter,
          c.dc_type,
          d.id area_id
        FROM
          network_segment a, net_area b, datacenter c, area d
        WHERE
          a.net_area_id = b.id
          AND b.datacenter_id = c.id
          AND c.area_id = d.id
          AND b.isdeleted = '0'
          AND c.isdeleted = '0'
          AND d.isdeleted = '0'
          AND b.name = %s
          AND c.name = %s
          AND c.dc_type = %s
          AND a.segment = %s
    '''

    args = [net_area_name, datacenter_name, env, network_segment]
    data = ins.query_one(db_conn, sql, args)
    return data


def get_network_segment_id_info_by_network_segment(net_area_id, segment, vlan, gateway_ip, host_bridge_name):
    ins = Mysql.get_instance("kvm")
    db_conn = ins.get_connection()
    sql = '''
    SELECT
         id
    FROM
         network_segment a 
    WHERE 
         a.net_area_id = %s
    AND  a.segment = %s
    AND  a.vlan = %s
    AND  a.gateway_ip = %s
    AND  a.host_bridge_name = %s
       
      
    '''
    args = [net_area_id, segment, vlan, gateway_ip, host_bridge_name]
    data = ins.query_one(db_conn, sql, args)
    return data

