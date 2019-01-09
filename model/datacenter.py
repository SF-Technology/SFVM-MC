# coding=utf8
'''
    datacenter表
'''
# __author__ =  ""

from lib.dbs.mysql import Mysql
from model import base_model


class DataCenter(base_model.BaseModel):

    pass


def user_datacenter_list(user_id, all_areas_list, **kwargs):
    '''
    sql语句里没有考虑area是否删除的情况，因为根据需求，area没有相关删除，需要的时候再添加上去
    '''
    ins = Mysql.get_instance("kvm")
    db_conn = ins.get_connection()
    sql = '''
          SELECT
            m.id AS datacenter_id,
            m.displayname,
            m.dc_type,
            m.province,
            m.address,
            m.description,
            u.id AS hostpool_id,
            q.id AS net_area_id,
            COUNT(u.id) AS hostpool_nums
        FROM
            user_group
        LEFT JOIN
            access t ON t.group_id = user_group.group_id
        LEFT JOIN
            datacenter m ON m.area_id = t.area_id AND m.isdeleted = '0'
        LEFT JOIN
            net_area q ON m.id = q.datacenter_id AND q.isdeleted = '0'
        LEFT JOIN hostpool u ON u.net_area_id = q.id AND u.isdeleted = '0'
        WHERE user_group.user_id = %s AND m.id IS NOT NULL
        GROUP BY m.id
        ORDER BY m.id DESC
    '''
    # 计算总数  用于分页使用
    where_sql = ''
    args = [user_id]
    total_data = ins.query(db_conn, sql, args)
    total_nums = len(total_data)
    limit_sql = ''
    page_no = int(kwargs['page_no'])
    page_size = kwargs['page_size']
    limit_sql = ' LIMIT %d, %d' % ((int(page_no) - 1) * int(page_size), int(page_size))
    sql += limit_sql
    data = ins.query(db_conn, sql, args)
    return total_nums, data
