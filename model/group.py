# coding=utf8
'''
   tb_group表
'''


from lib.dbs.mysql import Mysql
from model import base_model

class Group(base_model.BaseModel):
    pass


def add_group_info(insert_data, db_conn=None):
    ins = Mysql.get_instance("kvm")
    return ins.simple_insert('tb_group', insert_data, db_conn)


def query_data(**kwargs):
    ins = Mysql.get_instance("kvm")
    db_conn = ins.get_connection()
    sql = '''
            SELECT * FROM tb_group where 1 = 1
        '''
    # 计算总数的sql  用于分页使用
    count_sql = ' SELECT COUNT(*) total_nums FROM tb_group WHERE 1 = 1 '
    where_sql = ''
    args = []

    order_by_sql = ' ORDER BY id DESC'
    sql += where_sql
    count_sql += where_sql
    count_result = ins.query_one(db_conn, count_sql, args)
    sql += order_by_sql
    limit_sql = ''
    if kwargs.get('page_no') and kwargs.get('page_size'):
        page_no = int(kwargs['page_no'])
        if page_no <= 1:
            page_no = 1
        page_size = kwargs['page_size']
        limit_sql = ' LIMIT %d, %d' % ((int(page_no) - 1) * int(page_size), int(page_size))
    sql += limit_sql
    data = ins.query(db_conn, sql, args)
    total_nums = count_result.get('total_nums') and count_result.get('total_nums') or 0
    return total_nums, data


def update_group(update_data, where_data):
    ins = Mysql.get_instance("kvm")
    table_name = 'tb_group'
    return ins.simple_update(table_name, update_data, where_data)


def query_group_info(group_id):
    ins = Mysql.get_instance("kvm")
    db_conn = ins.get_connection()
    sql = '''
            SELECT * FROM tb_group where  id = %s AND isdeleted = '0'
        '''
    args = [group_id]
    return ins.query_one(db_conn, sql, args)


def query_group_info_by_group_name(group_name):
    ins = Mysql.get_instance("kvm")
    db_conn = ins.get_connection()
    sql = '''
            SELECT * FROM tb_group where  name = %s AND isdeleted = '0'
        '''
    args = [group_name]
    return ins.query_one(db_conn, sql, args)


def query_group_info_by_group_name_and_env(group_name, env):
    ins = Mysql.get_instance("kvm")
    db_conn = ins.get_connection()
    sql = '''
            SELECT * FROM tb_group where  name = %s AND dc_type = %s AND isdeleted = '0'
        '''
    args = [group_name, env]
    return ins.query_one(db_conn, sql, args)


def delete_group(group_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
            delete from tb_group where id = %s
                    '''
    args = [group_id]
    db_conn = ins.get_connection()
    return ins.execute(db_conn, sql, args)


def group_area_info(group_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
          t.id AS area_id, t.name, t.parent_id, m.name AS parent_name
        FROM access
        LEFT JOIN
          (SELECT id, name, parent_id FROM area WHERE isdeleted = '0') t ON access.area_id = t.id
        LEFT JOIN
          (SELECT id, name FROM area WHERE isdeleted = '0') m ON t.parent_id = m.id
        WHERE access.group_id = %s AND t.id IS NOT NULL
    '''
    args = [group_id]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def group_quota_flavor_used(group_id):
    '''
    查询group下所有instance的实际已使用的配额总数：vcpu,memory_mb,root_disk_gb
    '''
    ins = Mysql.get_instance("kvm")
    sql = '''
          SELECT
            SUM(m.vcpu) all_vcpu,
            SUM(m.memory_mb) all_mem_mb,
            SUM(m.root_disk_gb) all_root_disk_gb,
            COUNT(t.instance_id) instance_num
          FROM instance_group
          LEFT JOIN
          (SELECT instance_id, flavor_id FROM instance_flavor) t ON instance_group.instance_id = t.instance_id
          LEFT JOIN
          (SELECT vcpu,memory_mb, root_disk_gb, id FROM flavor) m ON t.flavor_id = m.id
          WHERE instance_group.group_id = %s
         '''
    args = [group_id]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def group_quota_data_disk_used(group_id):
    '''
        查询group下所有instance的实际已分配的数据盘容量
    :param group_id:
    :return:
    '''
    ins = Mysql.get_instance("kvm")
    sql = '''
          SELECT SUM(c.size_gb) all_data_disk_gb
          FROM instance a, instance_group b, instance_disk c
          WHERE
            a.id = b.instance_id
            AND a.id = c.instance_id
            AND a.isdeleted = '0'
            AND c.isdeleted = '0'
            AND b.group_id = %s
    '''
    args = [group_id]
    db_conn = ins.get_connection()
    return ins.query_one(db_conn, sql, args)


def user_group_list(user_id, is_super_group=False, **kwargs):
    '''
    查询用户所在的全部应用组的相关信息
    目前没有考虑一个用户在加入多个不同角色的应用组中所以拥有不同的角色导致的权限冲突问题
    :return:
    '''
    ins = Mysql.get_instance("kvm")
    db_conn = ins.get_connection()
    sql = '''
        SELECT t.id, t.name, t.owner, t.cpu, t.mem, t.disk, t.vm, t.dc_type, m.role_id
        FROM user_group
          LEFT JOIN
          (SELECT id, name, owner, cpu, mem, disk, vm, dc_type FROM tb_group WHERE isdeleted = '0') t ON t.id = user_group.group_id
          LEFT JOIN
          (SELECT role_id, group_id FROM access) m ON m.group_id = user_group.group_id
    '''
    args = []
    where_sql = ' WHERE 1 = 1 '

    if not is_super_group:
        where_sql += ' AND user_group.user_id = %s'
        args.append(user_id)

    if kwargs['WHERE_AND']['like']['name']:
        where_sql += ' AND t.name LIKE %s'
        args.append(kwargs['WHERE_AND']['like']['name'])

    if kwargs['WHERE_AND']['like']['owner']:
        where_sql += ' AND t.owner LIKE %s'
        args.append(kwargs['WHERE_AND']['like']['owner'])

    if kwargs['WHERE_AND']['like']['user_id']:
        where_sql += ' AND user_group.user_id LIKE %s'
        args.append(kwargs['WHERE_AND']['like']['user_id'])

    sql += where_sql
    sql += ' GROUP BY t.id ORDER BY t.id DESC'

    # 计算总数  用于分页使用
    total_data = ins.query(db_conn, sql, args)
    total_nums = len(total_data)
    page_no = int(kwargs['page_no'])
    page_size = kwargs['page_size']
    limit_sql = ' LIMIT %d, %d' % ((int(page_no) - 1) * int(page_size), int(page_size))
    sql += limit_sql
    data = ins.query(db_conn, sql, args)
    return total_nums, data
