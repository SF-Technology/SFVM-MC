# coding=utf8
'''
    user_group表
'''


from lib.dbs.mysql import Mysql
from model import base_model


class UserGroup(base_model.BaseModel):
    pass


def add_user_group(insert_data, db_conn=None):
    ins = Mysql.get_instance("kvm")
    return ins.simple_insert('user_group', insert_data, db_conn)


# def query_user_role_group(user_id, group_id):
#     ins = Mysql.get_instance("kvm")
#     sql = '''
#             SELECT * FROM user_group WHERE user_id = %s AND role_id = %s and user_id = %s
#         '''
#     args = [user_id, group_id]
#     db_conn = ins.get_connection()
#     return ins.query(db_conn, sql, args)


def query_data(group_id, **kwargs):
    '''
    输入group_id，查询属于这个group的所有的用户
    '''
    ins = Mysql.get_instance("kvm")
    db_conn = ins.get_connection()
    sql = '''
            SELECT * FROM user_group where group_id = %s
        '''
    # 计算总数的sql  用于分页使用
    count_sql = ' SELECT COUNT(*) total_nums FROM user_group WHERE group_id = %s '
    where_sql = ''
    args = [group_id]

    # order_by_sql = ' ORDER BY group_id DESC'
    sql += where_sql
    count_sql += where_sql
    count_result = ins.query_one(db_conn, count_sql, args)
    # sql += order_by_sql
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


def delete_user(user_id, group_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
            delete from user_group where user_id = %s and group_id = %s
        '''
    args = [user_id, group_id]
    db_conn = ins.get_connection()
    return ins.execute(db_conn, sql, args)


def delete_users_in_group(group_id):
    ins = Mysql.get_instance("kvm")
    sql = '''
            delete from user_group where group_id = %s
        '''
    args = [group_id]
    db_conn = ins.get_connection()
    return ins.execute(db_conn, sql, args)


# def update_expire_at(user_id, group_id):
#     '''这个函数用来修改用户在应用组里的权限过期时间'''
#     ins = Mysql.get_instance("kvm")
#     sql = '''
#             UPDATE user_group SET expire_at = LOCALTIME() WHERE user_id = %s and  group_id = %s
#         '''
#     args = [user_id, group_id]
#     db_conn = ins.get_connection()
#     return ins.execute(db_conn, sql, args)


def get_data_by_group_name(group_name):
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT a.* FROM user_group a, tb_group b
        WHERE
            a.group_id = b.id
            AND a.user_id = b.owner
            AND b.name = %s
    '''
    args = [group_name]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)



