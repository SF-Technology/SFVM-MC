# coding=utf8
'''
    host表
'''
# __author__ =  ""

from lib.dbs.mysql import Mysql
from model import base_model


class Host(base_model.BaseModel):

    pass


def get_level_info(host_id):
    '''
        获取host以上的所有层级信息
    :return:
    '''
    ins = Mysql.get_instance("kvm")
    sql = ('\n'
           '              SELECT \n'
           '	            a.id, \n'
           '	            a.displayname host_name, \n'
           '	            b.displayname hostpool_name,\n'
           '	            c.displayname net_area_name,\n'
           '                d.displayname datacenter_name\n'
           '              FROM \n'
           '	            host a, hostpool b, net_area c, datacenter d \n'
           '              WHERE\n'
           '	            a.hostpool_id = b.id\n'
           '	            AND a.isdeleted = \'0\'\n'
           '	            AND b.net_area_id = c.id\n'
           '	            AND b.isdeleted = \'0\'\n'
           '	            AND c.datacenter_id = d.id\n'
           '	            AND c.isdeleted = \'0\'\n'
           '	            AND d.isdeleted = \'0\'\n'
           '	            AND a.id = %s\n'
           '            ')
    args = [host_id]
    db_conn = ins.get_connection()
    return ins.query_one(db_conn, sql, args)


def get_vm_assign_mem_of_host(host_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
          SUM(a.memory_mb) assign_mem
        FROM
          flavor a, instance_flavor b, instance_host c, instance d
        WHERE
          c.instance_id = b.instance_id
          AND b.flavor_id = a.id
          AND a.isdeleted = '0'
          AND c.host_id = %s
          AND c.isdeleted = '0'
          AND b.instance_id = d.id
          AND d.name NOT LIKE '%%clone%%'
    '''
    args = [host_id]
    db_conn = ins.get_connection()
    return ins.query_one(db_conn, sql, args)


def get_vm_assign_vcpu_of_host(host_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
          SUM(a.vcpu) assign_vcpu
        FROM
          flavor a, instance_flavor b, instance_host c
        WHERE
          c.instance_id = b.instance_id
          AND b.flavor_id = a.id
          AND a.isdeleted = '0'
          AND c.host_id = %s
    '''
    args = [host_id]
    db_conn = ins.get_connection()
    return ins.query_one(db_conn, sql, args)


def get_vm_assign_disk_of_host(host_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
          SUM(a.root_disk_gb + d.size_gb) assign_disk
        FROM
          flavor a, instance_flavor b, instance_host c, instance_disk d
        WHERE
          c.instance_id = b.instance_id
          AND d.instance_id = c.instance_id
          AND b.flavor_id = a.id
          AND a.isdeleted = '0'
          AND c.host_id = %s
    '''
    args = [host_id]
    db_conn = ins.get_connection()
    return ins.query_one(db_conn, sql, args)


def get_instances_of_host(host_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
            SELECT
              a.id instance_id,
              a.name,
              a.status
            FROM
              instance a, host b, instance_host c
            WHERE
              a.id = c.instance_id
              and b.id = c.host_id
              and a.isdeleted = '0'
              and b.isdeleted = '0'
              and c.isdeleted = '0'
              and b.id = %s
        '''
    args = [host_id]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_hosts_by_fuzzy_hostpool_name(hostpool_name):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
            a.id host_id
        FROM
            host a
        LEFT JOIN
            hostpool b ON a.hostpool_id = b.id AND b.isdeleted = '0'
        WHERE
            a.isdeleted = '0'
            AND b.name LIKE %s
    '''
    args = ['%' + hostpool_name + '%']
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def pre_allocate_host_resource(host_id, cpu, memory, disk):
    ins = Mysql.get_instance("kvm")
    sql = '''
        UPDATE host
        SET
            cpu = cpu - %s,
            memory_mb = memory_mb - %s,
            app_disk_mb = app_disk_mb - %s
        WHERE id = %s
    '''
    args = [cpu, memory, disk, host_id]
    db_conn = ins.get_connection()
    return ins.execute(db_conn, sql, args)


def get_host_info_in_area():
    '''
    获取所有的Host-Hostpool-Net_area-Datacenter-Area的列表
    :return:
    '''
    ins = Mysql.get_instance("kvm")
    sql = ('''
            SELECT host.id AS host_id,host.`name` AS host_name,host.hostpool_id, m.hostpool_name,m.net_area_id,n.net_area_name,
              n.datacenter_id, q.datacenter_name,q.area_id,v.parent_id,w.parent_name,area.name AS area_name
              FROM `host`
              LEFT JOIN
              (SELECT id,`name` AS hostpool_name,net_area_id FROM hostpool) m ON host.hostpool_id = m.id
              LEFT JOIN
              (SELECT id,`name` AS net_area_name,datacenter_id FROM net_area) n ON m.net_area_id = n.id
              LEFT JOIN
              (SELECT id,`name` AS datacenter_name,area_id FROM datacenter) q ON n.datacenter_id = q.id
              LEFT JOIN `area` ON q.area_id = area.id
              LEFT JOIN
              (SELECT area.parent_id FROM `area` WHERE area.isdeleted = '0' AND parent_id = -1) u ON u.parent_id=area.id
              LEFT JOIN
              (SELECT parent_id FROM `area`) v ON area.parent_id=v.parent_id
              LEFT JOIN
              (SELECT id AS parent_id, `name` AS parent_name FROM `area` WHERE parent_id = -1) w ON area.parent_id = w.parent_id
    ''')
    args = []
    db_conn = ins.get_connection()
    total_nums = ins.execute(db_conn, sql, args)
    data = ins.query(db_conn, sql, args)
    return total_nums, data


def get_hosts_by_datacenter_id(datacenter_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
            a.id,
            a.ipaddress,
            a.sn,
            a.status
        FROM
            host a, hostpool b, net_area c, datacenter d
        WHERE
            a.hostpool_id = b.id
            AND b.net_area_id = c.id
            AND c.datacenter_id = d.id
            AND a.isdeleted = '0'
            AND b.isdeleted = '0'
            AND c.isdeleted = '0'
            AND d.isdeleted = '0'
            AND d.id = %s
    '''
    args = [datacenter_id]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_hosts_by_net_area_id(net_area_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT ipaddress FROM host WHERE isdeleted = '0' AND hostpool_id IN (
            SELECT id FROM hostpool WHERE net_area_id = %s AND isdeleted = '0'
        )
    '''
    args = [net_area_id]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def _get_hosts_by_net_area_id(net_area_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT ipaddress FROM host WHERE isdeleted = '0' AND hostpool_id IN (
            SELECT id FROM hostpool WHERE net_area_id = %s AND isdeleted = '0'
        ) AND `status` ='0'
    '''
    args = [net_area_id]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def user_host_list(user_id, **kwargs):
    '''
    用户对应的所有host集合，返回了从area到host的所有层级等相关信息，前端需要的字段从函数返回值中选取就可以了
    '''
    ins = Mysql.get_instance("kvm")
    db_conn = ins.get_connection()
    sql = '''
        SELECT
            n.name AS area_name,
            m.displayname AS datacenter_name,
            m.dc_type,
            q.displayname AS net_area_name,
            u.displayname AS hostpool_name,
            j.id AS group_id,
            j.name AS group_name,
            j.owner,
            w.name AS host_name,
            w.ipaddress,
            w.id AS host_id,
            w.sn,
            w.hold_mem_gb,
            w.manage_ip,
            w.status,
            w.typestatus
        FROM
          user_group
        LEFT JOIN
          access t ON t.group_id = user_group.group_id
        LEFT JOIN
          tb_group j ON t.group_id = j.id AND isdeleted = '0'
        LEFT JOIN
          datacenter m ON m.area_id = t.area_id AND m.isdeleted = '0'
        LEFT JOIN
          area n ON m.area_id = n.id and n.isdeleted = '0'
        LEFT JOIN
          net_area q ON m.id = q.datacenter_id AND q.isdeleted = '0'
        LEFT JOIN
          hostpool u ON u.net_area_id = q.id AND u.isdeleted = '0'
        LEFT JOIN
          host w ON w.hostpool_id = u.id AND w.isdeleted = '0'
        '''

    where_sql = ' WHERE user_group.user_id = %s AND w.id IS NOT NULL'
    args = [user_id]

    if kwargs['WHERE_AND']['like']['name']:
        where_sql += ' AND w.name LIKE %s'
        args.append(kwargs['WHERE_AND']['like']['name'])

    if kwargs['WHERE_AND']['like']['sn']:
        where_sql += ' AND w.sn LIKE %s'
        args.append(kwargs['WHERE_AND']['like']['sn'])

    if kwargs['WHERE_AND']['like']['ip_address']:
        where_sql += ' AND w.ipaddress LIKE %s'
        args.append(kwargs['WHERE_AND']['like']['ip_address'])

    if kwargs['WHERE_AND']['like']['manage_ip']:
        where_sql += ' AND w.manage_ip LIKE %s'
        args.append(kwargs['WHERE_AND']['like']['manage_ip'])

    if kwargs['WHERE_AND']['=']['status']:
        where_sql += ' AND w.status = %s'
        args.append(kwargs['WHERE_AND']['=']['status'])

    # 等于1表示有搜索
    if kwargs['search_in_flag'] == 1:
        if kwargs['WHERE_AND']['in']['id']:
            where_sql += ' AND w.id IN %s'
            args.append(kwargs['WHERE_AND']['in']['id'])
        else:
            where_sql += ' AND w.id IN (NULL)'

    sql += where_sql
    sql += '''
        GROUP BY w.id
        ORDER BY w.id DESC
    '''

    # 计算总数  用于分页使用
    total_data = ins.query(db_conn, sql, args)
    total_nums = len(total_data)

    if kwargs.get('page_no') and kwargs.get('page_size'):
        page_no = int(kwargs['page_no'])
        page_size = kwargs['page_size']
        limit_sql = ' LIMIT %d, %d' % ((int(page_no) - 1) * int(page_size), int(page_size))
        sql += limit_sql

    data = ins.query(db_conn, sql, args)
    return total_nums, data


def get_host_net_area_id(host_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT a.net_area_id FROM hostpool a, host b
        WHERE b.id = %s AND b.hostpool_id = a.id
    '''
    args = [host_id]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)