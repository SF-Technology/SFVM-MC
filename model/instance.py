# coding=utf8
'''
    instance表
'''


from lib.dbs.mysql import Mysql
from model import base_model


class Instance(base_model.BaseModel):
    pass


def get_instances_by_fuzzy_ip(ip_address,ip_search_type):
    ins = Mysql.get_instance("kvm")
    if  ip_search_type:
        sql = '''
            SELECT
                a.id instance_id
            FROM
                instance a
            LEFT JOIN
                instance_ip b ON a.id = b.instance_id AND b.isdeleted = '0'
            LEFT JOIN
                ip c ON c.id = b.ip_id
            WHERE
                a.isdeleted = '0'
                AND b.instance_id IS NOT NULL
                AND c.id IS NOT NULL
                AND c.ip_address LIKE %s
            '''
        args = ['%' + ip_address + '%']
        db_conn = ins.get_connection()
        return ins.query(db_conn, sql, args)
    else:
        sql = '''
                    SELECT
                        a.id instance_id
                    FROM
                        instance a
                    LEFT JOIN
                        instance_ip b ON a.id = b.instance_id AND b.isdeleted = '0'
                    LEFT JOIN
                        ip c ON c.id = b.ip_id
                    WHERE
                        a.isdeleted = '0'
                        AND b.instance_id IS NOT NULL
                        AND c.id IS NOT NULL
                        AND c.ip_address = %s
                    '''
        args = [ip_address]
        db_conn = ins.get_connection()
        return ins.query(db_conn, sql, args)

def get_instances_by_fuzzy_host_ip(host_ip):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
            a.id instance_id
        FROM
            instance a
        LEFT JOIN
            instance_host b ON a.id = b.instance_id AND b.isdeleted = '0'
        LEFT JOIN
            host c ON c.id = b.host_id AND c.isdeleted = '0'
        WHERE
            a.isdeleted = '0'
            AND b.instance_id IS NOT NULL
            AND c.id IS NOT NULL
            AND c.ipaddress LIKE %s
        '''
    args = ['%' + host_ip + '%']
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_instances_by_fuzzy_group_name(group_name):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
            a.id instance_id
        FROM
            instance a
        LEFT JOIN
            instance_group b ON a.id = b.instance_id
        LEFT JOIN
            tb_group c ON c.id = b.group_id AND c.isdeleted = '0'
        WHERE
            a.isdeleted = '0'
            AND b.instance_id IS NOT NULL
            AND c.id IS NOT NULL
            AND c.name LIKE %s
        '''
    args = ['%' + group_name + '%']
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_instance_datacenter_info(instance_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
            a.displayname,
            a.dc_type
        FROM
            datacenter a, net_area b, hostpool c, host d, instance e, instance_host f
        WHERE
            e.id = f.instance_id
            AND f.host_id = d.id
            AND d.hostpool_id = c.id
            AND c.net_area_id = b.id
            AND b.datacenter_id = a.id
            AND a.isdeleted = '0'
            AND b.isdeleted = '0'
            AND c.isdeleted = '0'
            AND d.isdeleted = '0'
            AND e.isdeleted = '0'
            AND f.isdeleted = '0'
            AND e.id = %s
    '''
    args = [instance_id]
    db_conn = ins.get_connection()
    return ins.query_one(db_conn, sql, args)


def get_instance_netarea_info(instance_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
            a.name,
            a.id
        FROM
            net_area a, hostpool b, host c, instance d, instance_host e
        WHERE
            d.id = e.instance_id
            AND e.host_id = c.id
            AND c.hostpool_id = b.id
            AND b.net_area_id = a.id
            AND a.isdeleted = '0'
            AND b.isdeleted = '0'
            AND c.isdeleted = '0'
            AND d.isdeleted = '0'
            AND e.isdeleted = '0'
            AND d.id = %s
    '''
    args = [instance_id]
    db_conn = ins.get_connection()
    return ins.query_one(db_conn, sql, args)


def get_instance_hostpool_info(instance_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT * FROM hostpool WHERE id = (
              SELECT
                b.hostpool_id
              FROM
                instance a, host b, instance_host c
              WHERE
                a.id = c.instance_id AND b.id = c.host_id AND c.instance_id = %s
        )
    '''
    args = [instance_id]
    db_conn = ins.get_connection()
    return ins.query_one(db_conn, sql, args)


def get_instance_host_info(instance_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
            SELECT a.* FROM host a LEFT JOIN instance_host b
              ON a.id = b.host_id WHERE b.instance_id = %s AND a.isdeleted='0' AND b.isdeleted='0'
        '''
    args = [instance_id]
    db_conn = ins.get_connection()
    return ins.query_one(db_conn, sql, args)


def get_instance_flavor_info(instance_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
            SELECT
              a.name,
              a.displayname,
              b.id flavor_id,
              b.memory_mb,
              b.name flavor_name,
              b.root_disk_gb,
              b.vcpu
            FROM
              instance a, flavor b, instance_flavor c
            WHERE
              a.id = c.instance_id AND b.id = c.flavor_id AND c.instance_id = %s
        '''
    args = [instance_id]
    db_conn = ins.get_connection()
    return ins.query_one(db_conn, sql, args)


def get_instance_images_info(instance_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
          b.displayname,
          b.name,
          b.system,
          b.version
        FROM
          instance a, image b, instance_image c
        WHERE
          a.id = c.instance_id AND b.id = c.image_id AND a.id = %s
    '''
    args = [instance_id]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_clone_instance_images_info(instance_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
          c.image_id AS id,
          b.displayname,
          b.name,
          b.system,
          b.version
        FROM
          instance a, image b, instance_image c
        WHERE
          a.id = c.instance_id AND b.id = c.image_id AND a.id = %s
    '''
    args = [instance_id]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_instance_disks_info(instance_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
          b.size_gb,
          b.mount_point
        FROM
          instance a, instance_disk b
        WHERE
          a.id = b.instance_id
          AND a.isdeleted = '0'
          AND b.isdeleted = '0'
          AND a.id = %s
    '''
    args = [instance_id]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_instance_a_disk_info(instance_id, dev_name):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
          b.size_gb,
          b.mount_point
        FROM
          instance a, instance_disk b
        WHERE
          a.id = b.instance_id
          AND a.isdeleted = '0'
          AND b.isdeleted = '0'
          AND a.id = %s
          AND b.dev_name = %s
    '''
    args = [instance_id, dev_name]
    db_conn = ins.get_connection()
    return ins.query_one(db_conn, sql, args)


def get_instance_full_disks_info(instance_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
          *
        FROM
          instance a, instance_disk b
        WHERE
          a.id = b.instance_id
          AND a.isdeleted = '0'
          AND b.isdeleted = '0'
          AND a.id = %s
    '''
    args = [instance_id]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_instance_disks_size(instance_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
          SUM(b.size_gb) AS data_disk_size
        FROM
          instance a, instance_disk b
        WHERE
          a.id = b.instance_id
          AND a.isdeleted = '0'
          AND b.isdeleted = '0'
          AND a.id = %s
    '''
    args = [instance_id]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_instance_group_info(instance_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
          b.id group_id,
          b.name,
          b.dc_type
        FROM
          instance a, tb_group b, instance_group c
        WHERE
          a.id = c.instance_id AND b.id = c.group_id AND a.id = %s
    '''
    args = [instance_id]
    db_conn = ins.get_connection()
    return ins.query_one(db_conn, sql, args)


def get_instance_ip_info(instance_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
          b.id,
          b.ip_address,
          b.segment_id
        FROM
          instance a, ip b, instance_ip c
        WHERE
          a.id = c.instance_id AND b.id = c.ip_id AND c.isdeleted = '0' AND a.id = %s AND c.type = '0'
    '''
    args = [instance_id]
    db_conn = ins.get_connection()
    return ins.query_one(db_conn, sql, args)


def get_instance_all_ip_info(instance_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
          b.id,
          b.ip_address,
          b.segment_id,
          n.segment_type
        FROM
          instance a, ip b, instance_ip c, network_segment n
        WHERE
          a.id = c.instance_id AND b.id = c.ip_id AND a.id = %s AND b.segment_id = n.id
    '''
    args = [instance_id]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_instance_net_info(instance_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
          a.id AS instance_id,
          c.id AS ip_id,
          c.ip_address,
          c.vlan,
          b.mac,
          b.type AS nic_type,
          n.segment_type
        FROM
          instance a
        LEFT JOIN
          instance_ip b ON a.id = b.instance_id AND b.isdeleted = '0'
        LEFT JOIN
          ip c ON c.id = b.ip_id
        LEFT JOIN
          network_segment n ON n.id = c.segment_id
        WHERE
          a.id = %s AND a.isdeleted = '0'
    '''
    args = [instance_id]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_instance_net_segment_info(instance_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
          b.id,
          b.ip_address,
          d.netmask,
          d.vlan,
          d.segment,
          d.gateway_ip,
          d.net_area_id,
          d.segment_type,
          d.dns1,
          d.dns2,
          c.mac
        FROM
          instance a, ip b, instance_ip c, network_segment d
        WHERE
          a.id = c.instance_id AND b.id = c.ip_id AND a.id = %s AND a.isdeleted = '0' AND b.segment_id = d.id AND c.isdeleted = '0'
    '''
    args = [instance_id]
    db_conn = ins.get_connection()
    return ins.query_one(db_conn, sql, args)


def get_instance_net_info_by_mac_addr(mac_addr):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
          b.id AS ip_id,
          b.ip_address,
          b.vlan,
          instance_ip.mac,
          n.host_bridge_name
        FROM
          instance_ip
        LEFT JOIN
          ip b ON b.id =  instance_ip.ip_id
        LEFT JOIN
          network_segment n ON b.segment_id = n.id
        WHERE
          instance_ip.mac = %s AND instance_ip.isdeleted = '0'
    '''
    args = [mac_addr]
    db_conn = ins.get_connection()
    return ins.query_one(db_conn, sql, args)


def get_instances_info_in_group(group_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
          a.name,
          a.status
        FROM instance a
        LEFT JOIN instance_group b ON a.id = b.instance_id
        WHERE a.isdeleted = '0' AND b.group_id = %s
    '''
    args = [group_id]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_instances_info_in_host(host_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
            SELECT a.* FROM instance a LEFT JOIN instance_host b ON a.id = b.instance_id
              WHERE a.isdeleted = '0' AND b.host_id = %s AND b.isdeleted = '0'
        '''
    args = [host_id]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_instances_info_by_host_ip(host_ip):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
            a.uuid,
            a.name,
            a.created_at
        FROM
            instance a, instance_host b, host c
        WHERE
            a.id = b.instance_id
            AND b.host_id = c.id
            AND a.isdeleted = '0'
            AND b.isdeleted = '0'
            AND c.isdeleted = '0'
            AND c.ipaddress = %s
    '''
    args = [host_ip]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def user_instance_list(user_id, is_admin=False,ip_search_type=False,**kwargs):
    '''
    用户对应的所有instance集合，返回了从area到instance的所有相关信息，需要的话从函数中读取就可以了
    '''
    ins = Mysql.get_instance("kvm")
    db_conn = ins.get_connection()
    sql = '''
        SELECT
            j.name AS group_name,
            u.displayname AS hostpool_name,
            i.name AS instance_name,
            i.displayname AS displayname,
            i.uuid,
            u.id AS hostpool_id,
            i.status,
            i.id,
            i.owner,
            im.system,
            i.create_source,
            i.app_info,
            i.request_id,
            j.id AS group_id,
            m.dc_type,
            w.ipaddress AS host_ip,
            g.ip_address,
            f.flavor_id AS flavor_id
        FROM
            user_group
        LEFT JOIN
            access t ON t.group_id = user_group.group_id
        LEFT JOIN
            tb_group j ON t.group_id = j.id
        LEFT JOIN
            datacenter m ON m.area_id = t.area_id AND m.isdeleted = '0'
        LEFT JOIN
            net_area q ON m.id = q.datacenter_id AND q.isdeleted = '0'
        LEFT JOIN
            hostpool u ON u.net_area_id = q.id AND u.isdeleted = '0'
        LEFT JOIN
            host w ON w.hostpool_id = u.id AND w.isdeleted = '0'
        LEFT JOIN
            instance_host v ON w.id = v.host_id AND v.isdeleted = '0'
        LEFT JOIN
            instance i ON v.instance_id = i.id AND i.isdeleted = '0'
        LEFT JOIN
            instance_flavor f ON i.id = f.instance_id
        LEFT JOIN
            instance_image a ON a.instance_id = i.id
        LEFT JOIN
            image im ON im.id = a.image_id
        '''

    if not is_admin:
        sql += '''
            LEFT JOIN
                instance_group b ON b.group_id = j.id AND b.instance_id = i.id AND b.group_id = user_group.group_id
        '''

    sql += '''
        LEFT JOIN
            instance_ip p ON i.id = p.instance_id AND p.isdeleted = '0' AND p.`ip_id` IS NOT NULL AND p.type = '0'
        LEFT JOIN
            ip g ON p.ip_id = g.id
        LEFT JOIN
            network_segment ns ON ns.id = g.segment_id AND ns.segment_type = '0'
    '''

    where_sql = 'WHERE user_group.user_id = %s AND i.name IS NOT NULL'
    if not is_admin:
        where_sql += '''
            AND b.group_id IS NOT NULL
        '''
    args = [user_id]

    if kwargs['WHERE_AND']['like']['name']:
        where_sql += ' AND i.name LIKE %s'
        args.append(kwargs['WHERE_AND']['like']['name'])

    if kwargs['WHERE_AND']['like']['uuid']:
        where_sql += ' AND i.uuid LIKE %s'
        args.append(kwargs['WHERE_AND']['like']['uuid'])

    # 等于1表示有搜索
    if kwargs['search_in_flag'] == 1:
        if kwargs['WHERE_AND']['in']['id']:
            where_sql += ' AND i.id IN %s'
            args.append(kwargs['WHERE_AND']['in']['id'])
        else:
            where_sql += ' AND i.id IN (NULL)'

    if kwargs['WHERE_AND']['=']['status']:
        where_sql += ' AND i.status = %s'
        args.append(kwargs['WHERE_AND']['=']['status'])

    if kwargs['WHERE_AND']['like']['owner']:
        where_sql += ' AND i.owner LIKE %s'
        args.append(kwargs['WHERE_AND']['like']['owner'])

    sql += where_sql
    sql += '''
        GROUP BY i.id
        ORDER BY i.id DESC
    '''

    # 计算总数  用于分页使用
    total_data = ins.query(db_conn, sql, args)
    total_nums = len(total_data)
    if not ip_search_type:
        if kwargs.get('page_no') and kwargs.get('page_size'):
            page_no = int(kwargs['page_no'])
            page_size = kwargs['page_size']
            limit_sql = ' LIMIT %d, %d' % ((int(page_no) - 1) * int(page_size), int(page_size))
            sql += limit_sql

    data = ins.query(db_conn, sql, args)
    return total_nums, data


# 获取instance克隆创建的任务状态
def get_clone_task_bttrans_status(task_id,host_ip,action,request_id):
    param = '%'+ host_ip + '%'
    ins = Mysql.get_instance("kvm")
    sql = '''
            SELECT
                i.id
            FROM
                instance_actions i
            WHERE
                i.task_id = %s
                AND i.message LIKE %s
                AND i.action = %s
                AND i.request_id != %s
        '''
    args = [task_id,param,action,request_id]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


# 获取instance克隆创建的任务是否有完成的
def get_clone_task_bttrans_done(task_id,host_ip,action,request_id):
    param = '%'+ host_ip + '%'
    ins = Mysql.get_instance("kvm")
    sql = '''
            SELECT
                a.id
            FROM
                instance_actions a
            WHERE
                a.task_id = %s
                AND a.message LIKE %s
                AND a.action = %s
                AND a.status = '1'
                AND a.request_id != %s
        '''
    args = [task_id,param,action,request_id]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_instance_info_by_ip_address(ip_address):
    '''获取虚拟机信息'''
    ins = Mysql.get_instance("kvm")
    sql = '''
            SELECT a.* ,c.ip_address FROM instance AS a
                INNER JOIN instance_ip AS b ON a.`id`=b.`instance_id`
                INNER JOIN ip AS c ON b.`ip_id` = c.`id`
                WHERE  c.`ip_address` = %s
                AND  b.`isdeleted` = '0'
                AND  a.`isdeleted` = '0'
                AND  a.`status` ='1'
            '''
    args = [ip_address]
    db_conn = ins.get_connection()
    return ins.query_one(db_conn, sql, args)