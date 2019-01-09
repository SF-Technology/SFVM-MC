# coding=utf8
'''
    HOSTPOOL表
'''


from lib.dbs.mysql import Mysql
from model import base_model


class HostPool(base_model.BaseModel):

    pass


def get_hostpools_by_dc_id(datacenter_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT * FROM hostpool WHERE isdeleted = '0' AND net_area_id IN (
            SELECT id FROM net_area WHERE datacenter_id = %s AND isdeleted = '0'
        )
    '''
    args = [datacenter_id]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_instances_nums(hostpool_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
            SELECT COUNT(*) nums FROM instance_host WHERE host_id IN (
              SELECT id FROM host WHERE hostpool_id = %s AND isdeleted = '0'
            )
        '''
    args = [hostpool_id]
    db_conn = ins.get_connection()
    return ins.query_one(db_conn, sql, args)


def get_level_info_hostpool_zb():
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
            a.id hostpool_id,
            a.least_host_num,
            a.displayname hostpool_name,
            b.displayname net_area_name,
            c.name dc_name,
            c.dc_type,
            d.id area_id,
            d.name area_name,
            b.id net_area_id
        FROM
            hostpool a, net_area b, datacenter c, area d
        WHERE
            a.isdeleted = '0'
            AND a.net_area_id = b.id
            AND b.isdeleted = '0'
            AND b.datacenter_id = c.id
            AND c.isdeleted = '0'
            AND c.area_id = d.id
            AND d.isdeleted = '0'
            AND d.area_type = '0'
    '''
    args = []
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def v2v_get_level_info_hostpool_zb():
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
            a.id hostpool_id,
            a.least_host_num,
            a.displayname hostpool_name,
            b.displayname net_area_name,
            c.dc_type,
            c.name as datacenter_name,
            d.id area_id
        FROM
            hostpool a, net_area b, datacenter c, area d
        WHERE
            a.isdeleted = '0'
            AND a.net_area_id = b.id
            AND b.isdeleted = '0'
            AND b.datacenter_id = c.id
            AND c.isdeleted = '0'
            AND c.area_id = d.id
            AND d.isdeleted = '0'
            AND d.area_type = '0'
    '''
    args = []
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_hostpool_info_zb_for_vishnu(dc_type, net_area_name):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
            a.id hostpool_id
        FROM
            hostpool a, net_area b, datacenter c, area d
        WHERE
            a.isdeleted = '0'
            AND a.net_area_id = b.id
            AND b.isdeleted = '0'
            AND b.datacenter_id = c.id
            AND c.isdeleted = '0'
            AND c.area_id = d.id
            AND d.isdeleted = '0'
            AND d.area_type = '0'
            AND c.`dc_type` = %s
            AND b.`name` = %s
    '''
    args = [dc_type, net_area_name]
    db_conn = ins.get_connection()
    return ins.query_one(db_conn, sql, args)


def get_level_info_hostpool_cs():
    ins = Mysql.get_instance("kvm")
    sql = '''
            SELECT
                a.id hostpool_id,
                a.least_host_num,
                a.displayname hostpool_name,
                b.displayname net_area_name,
                c.dc_type
            FROM
                hostpool a, net_area b, datacenter c, area d
            WHERE
                a.isdeleted = '0'
                AND a.net_area_id = b.id
                AND b.isdeleted = '0'
                AND b.datacenter_id = c.id
                AND c.isdeleted = '0'
                AND c.area_id = d.id
                AND (c.dc_type = '1' OR c.dc_type = '2' OR c.dc_type = '3')
                AND d.isdeleted = '0'
                AND d.area_type = '0'
        '''
    args = []
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_level_info_hostpool_v2v():
    ins = Mysql.get_instance("kvm")
    sql = '''
            SELECT
                a.id hostpool_id,
                a.least_host_num,
                a.displayname hostpool_name,
                b.displayname net_area_name,
                c.dc_type
            FROM
                hostpool a, net_area b, datacenter c, area d
            WHERE
                a.isdeleted = '0'
                AND a.net_area_id = b.id
                AND b.isdeleted = '0'
                AND b.datacenter_id = c.id
                AND c.isdeleted = '0'
                AND c.area_id = d.id
                AND d.isdeleted = '0'
                AND d.area_type = '0'
        '''
    args = []
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_level_info_hostpool_dq():
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
            a.id hostpool_id,
            a.least_host_num,
            a.displayname hostpool_name,
            b.displayname net_area_name,
            c.displayname datacenter_name,
            c.dc_type,
            c.name dc_name,
            d.displayname area_name,
            d.parent_id,
            d.id area_id,
            d.name area_name,
            b.id net_area_id
        FROM
            hostpool a, net_area b, datacenter c, area d
        WHERE
            a.isdeleted = '0'
            AND a.net_area_id = b.id
            AND b.isdeleted = '0'
            AND b.datacenter_id = c.id
            AND c.isdeleted = '0'
            AND c.area_id = d.id
            AND d.isdeleted = '0'
            AND d.area_type = '1'
    '''
    args = []
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_level_info_by_id(hostpool_id):
    '''
        获取指定hostpool的所有层级信息
        集群 - 网络区域 - 机房 - 区域
    :return:
    '''
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
          a.displayname hostpool_name,
          b.displayname net_area_name,
          c.dc_type,
          c.displayname datacenter_name,
          c.name dc_name,
          d.displayname area_name
        FROM
          hostpool a, net_area b, datacenter c, area d
        WHERE
          a.isdeleted = '0'
          AND a.net_area_id = b.id
          AND b.isdeleted = '0'
          AND b.datacenter_id = c.id
          AND c.isdeleted = '0'
          AND c.area_id = d.id
          AND d.isdeleted = '0'
          AND a.id = %s
    '''
    args = [hostpool_id]
    db_conn = ins.get_connection()
    return ins.query_one(db_conn, sql, args)


def get_level_info():
    '''
        获取hostpool以上的所有层级信息
        集群 - 网络区域 - 机房 - 区域
    :return:
    '''
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
          a.id hostpool_id,
          a.displayname hostpool_name,
          b.displayname net_area_name,
          c.displayname datacenter_name,
          c.dc_type,
          d.displayname area_name,
          d.id area_id
        FROM
          hostpool a, net_area b, datacenter c, area d
        WHERE
          a.isdeleted = '0'
          AND a.net_area_id = b.id
          AND b.isdeleted = '0'
          AND b.datacenter_id = c.id
          AND c.isdeleted = '0'
          AND c.area_id = d.id
          AND d.isdeleted = '0'
    '''
    args = []
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_segment_info(hostpool_id):
    '''
        获取hostpool对应的网络区域下所有网段
    :param hostpool_id:
    :return:
    '''
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT * FROM network_segment WHERE net_area_id IN (
          SELECT b.id FROM hostpool a, net_area b
            WHERE
              a.net_area_id = b.id
              AND a.isdeleted = '0'
              AND b.isdeleted = '0'
              AND a.id = %s
        )
    '''
    args = [hostpool_id]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_hostpool_nums():
    '''
    根据net_area_id在hostpool表中查询它下面有多少个hostpool，返回hostpool数量
    :return ({'net_area_id': 1L, 'COUNT(*)': 3L}, {'net_area_id': 2L, 'COUNT(*)': 2L})
    '''
    ins = Mysql.get_instance("kvm")
    sql = '''
            SELECT net_area_id, COUNT(*) FROM hostpool GROUP BY net_area_id
            '''
    args = []
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def user_hostpool_list(user_id, **kwargs):
    '''
    用户
    '''
    ins = Mysql.get_instance("kvm")
    db_conn = ins.get_connection()
    sql = '''
          SELECT
            m.id AS datacenter_id,
            q.id AS net_area_id,
            n.name AS area_name,
            u.id AS hostpool_id,
            m.displayname AS datacenter_name,
            m.dc_type,
            q.displayname AS net_area_name,
            u.displayname AS hostpool_name,
            u.least_host_num,
            u.hostpool_type AS hostpool_type,
            u.app_code AS app_code,
            COUNT(w.id) AS hosts_nums,
            COUNT(v.instance_id) AS instances_nums
        FROM
            user_group
        LEFT JOIN
           access t ON t.group_id = user_group.group_id
        LEFT JOIN
           datacenter m ON m.area_id = t.area_id AND m.isdeleted = '0'
        LEFT JOIN
           area n ON m.area_id = n.id AND n.isdeleted = '0'
        LEFT JOIN
           net_area q ON m.id = q.datacenter_id AND q.isdeleted = '0'
        LEFT JOIN
           hostpool u ON u.net_area_id = q.id AND u.isdeleted = '0'
        LEFT JOIN
           host w ON w.hostpool_id = u.id AND w.isdeleted = '0'
        LEFT JOIN
           instance_host v ON w.id = v.host_id AND v.isdeleted = '0'
        WHERE user_group.user_id = %s AND u.id IS NOT NULL
        GROUP BY u.id
        ORDER BY u.id DESC
    '''
    # 计算总数  用于分页使用
    args = [user_id]
    total_data = ins.query(db_conn, sql, args)
    total_nums = len(total_data)

    if kwargs.get('page_no') and kwargs.get('page_size'):
        page_no = int(kwargs['page_no'])
        page_size = kwargs['page_size']
        limit_sql = ' LIMIT %d, %d' % ((int(page_no) - 1) * int(page_size), int(page_size))
        sql += limit_sql

    data = ins.query(db_conn, sql, args)
    return total_nums, data


def get_datacenter_hostpool_list(datacenter_id, net_area_name, page_num, page_size, hostpool_id=None):
    '''
    获取指定机房下所有集群信息
    '''
    ins = Mysql.get_instance("kvm")
    db_conn = ins.get_connection()
    sql = '''
          SELECT
            b.id AS net_area_id,
            b.name AS net_area_name,
            c.id AS cluster_id,
            c.name AS cluster_name,
            c.hostpool_type AS cluster_type,
            c.app_code AS cluster_app_code
        FROM
            datacenter
        LEFT JOIN
           net_area b ON datacenter.id = b.datacenter_id AND b.isdeleted='0'
        LEFT JOIN
           hostpool c ON c.net_area_id = b.id AND c.isdeleted='0'
        WHERE datacenter.id=%s
    '''
    # 计算总数  用于分页使用
    args = [datacenter_id]

    if net_area_name:
        sql += ' AND b.name=%s'
        args.append(net_area_name)
    if hostpool_id:
        sql += ' AND c.id=%s'
        args.append(hostpool_id)

    sql += ' GROUP BY c.id '

    total_data = ins.query(db_conn, sql, args)
    total_nums = len(total_data)
    limit_sql = ' LIMIT %d, %d' % ((int(page_num) - 1) * int(page_size), int(page_size))
    sql += limit_sql
    data = ins.query(db_conn, sql, args)
    return total_nums, data


def get_hostpool_by_vmenv_netarea_hostpool(vm_env, netarea_name, hostpool_name):
    ins = Mysql.get_instance("kvm")
    sql = '''
            SELECT
                a.id hostpool_id,
                a.least_host_num,
                a.displayname hostpool_name,
                b.displayname net_area_name,
                c.dc_type
            FROM
                hostpool a, net_area b, datacenter c
            WHERE
                a.isdeleted = '0'
                AND a.net_area_id = b.id
                AND b.isdeleted = '0'
                AND b.datacenter_id = c.id
                AND c.isdeleted = '0'
                AND c.dc_type = %s
                AND b.name = %s
                AND a.name = %s
        '''
    args = [vm_env, netarea_name, hostpool_name]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_hostpool_by_area_dc_env_netarea_hostpool(area_name, dc_name, vm_env, netarea_name, hostpool_name):
    ins = Mysql.get_instance("kvm")
    sql = '''
            SELECT
                a.id hostpool_id,
                a.least_host_num,
                a.displayname hostpool_name,
                b.displayname net_area_name,
                c.dc_type
            FROM
                hostpool a, net_area b, datacenter c, area d
            WHERE
                a.isdeleted = '0'
                AND a.net_area_id = b.id
                AND b.isdeleted = '0'
                AND b.datacenter_id = c.id
                AND c.isdeleted = '0'
                AND c.area_id = d.id
                AND d.isdeleted = '0'
                AND d.name = %s
                AND c.name = %s
                AND c.dc_type = %s
                AND b.name = %s
                AND a.name = %s
        '''
    args = [area_name, dc_name, vm_env, netarea_name, hostpool_name]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_hostpool_info_by_name(env, dc_name, net_area):
    '''
        获取指定环境、机房、网络区域下的集群信息
    :return:
    '''
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
          a.id hostpool_id,
          a.displayname hostpool_name,
          b.displayname net_area_name,
          c.displayname datacenter_name,
          c.dc_type,
          d.displayname area_name,
          d.id area_id
        FROM
          hostpool a, net_area b, datacenter c, area d
        WHERE
          a.isdeleted = '0'
          AND a.net_area_id = b.id
          AND b.isdeleted = '0'
          AND b.datacenter_id = c.id
          AND c.isdeleted = '0'
          AND c.area_id = d.id
          AND d.isdeleted = '0'
          AND c.dc_type = %s
          AND c.name = %s
          AND b.name = %s
        GROUP BY a.id
    '''
    args = [env, dc_name, net_area]
    db_conn = ins.get_connection()
    return ins.query_one(db_conn, sql, args)


def get_all_hostpool_info():
    '''
        获取所有机房、网络区域、集群信息
    :return:
    '''
    ins = Mysql.get_instance("kvm")
    sql = '''
             SELECT datacenter.dc_type AS env, datacenter.`name` AS datacenter, 
                     net_area.id AS net_id, net_area.name AS net_area, 
                     hostpool.id AS hostpool_id, hostpool.hostpool_type AS hostpool_type, 
                     hostpool.name AS hostpool_name, hostpool.app_code AS hostpool_appcode
             FROM `area` LEFT JOIN datacenter ON area.id=datacenter.area_id 
             LEFT JOIN net_area ON datacenter.id=net_area.datacenter_id
             LEFT JOIN hostpool ON hostpool.net_area_id=net_area.id
             WHERE area.isdeleted='0' AND datacenter.isdeleted='0' AND net_area.isdeleted='0' AND hostpool.isdeleted='0';    
          '''
    args = []
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)
