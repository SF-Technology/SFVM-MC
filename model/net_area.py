# coding=utf8
'''
    net_area表
'''
# __author__ =  ""

from lib.dbs.mysql import Mysql
from model import base_model
import logging


class NetArea(base_model.BaseModel):

    pass


def get_level_info():
    '''
        获取网络区域以上的层级信息
        网络区域 - 机房 - 区域 - 父区域ID
    :return:
    '''
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
          a.id,
          a.displayname net_area_name,
          b.displayname datacenter_name,
          b.dc_type,
          c.displayname area_name,
          c.parent_id,
          c.id area_id
        FROM
          net_area a, datacenter b, area c
        WHERE
          a.isdeleted = '0'
          AND a.datacenter_id = b.id
          AND b.isdeleted = '0'
          AND b.area_id = c.id
          AND c.isdeleted = '0'
    '''
    args = []
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_area_hostpool_datacenter(**kwargs):
    '''
        net_area表中标记isdeleted的net_area不算在返回结果中
        hostpool表中标记isdeleted的hostpool不算在net_area名下
    '''
    ins = Mysql.get_instance("kvm")
    sql = ('''
            SELECT net_area.name AS net_area_name,T.hostpool_nums,datacenter.name AS datacenter_name
            FROM net_area
            LEFT JOIN (SELECT COUNT(1) AS hostpool_nums,net_area_id
            FROM hostpool GROUP BY net_area_id) T ON net_area.id = T.net_area_id
            LEFT JOIN  datacenter
            ON net_area.datacenter_id = datacenter.id
            WHERE net_area.isdeleted = '0'
            GROUP BY net_area.id
            ORDER BY net_area.id DESC
            ''')
    args = []
    limit_sql = ' '
    if kwargs.get('PAGINATION'):
        page_size = kwargs.get('PAGINATION').get('page_size', 20)
        page_no = kwargs.get('PAGINATION').get('page_no', 1)
        if int(page_no) == 1:
            limit_sql = ' LIMIT 0,' + str(int(page_size))
        else:
            limit_sql = ' LIMIT ' + str((int(page_no) - 1) * int(page_size)) + ',' + str(int(page_size))
    db_conn = ins.get_connection()
    data = ins.query(db_conn, sql, args)
    total_nums = len(data)
    finally_sql = sql + limit_sql

    logging.debug('finally sql %s %s', finally_sql, args)
    data = ins.query(db_conn, finally_sql, args)
    return total_nums, data


def get_datacenter_area_info():
    '''
        获取机房以及它对应的区域 - 父区域信息
    :return:
    '''
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
          datacenter.id AS datacenter_id,
          datacenter.name AS datacenter_name,
          datacenter.dc_type,
          area.id,
          area.name AS area_name,
          t.parent_id,
          q.name AS parent_area_name
        FROM
          datacenter
        LEFT JOIN
          area ON datacenter.area_id = area.id
        LEFT JOIN
          (SELECT area.id, area.parent_id FROM area where isdeleted = '0') t ON area.id = t.id
        LEFT JOIN
          (SELECT area.id, area.name FROM area where isdeleted = '0') q ON area.parent_id = q.id
        WHERE datacenter.isdeleted = '0'
    '''
    args = []
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def user_net_area_list(user_id, **kwargs):
    '''
    sql语句里没有考虑area是否删除的情况，因为根据需求，area没有相关删除，需要的时候再添加上去
    '''
    ins = Mysql.get_instance("kvm")
    db_conn = ins.get_connection()
    sql = '''
        SELECT
          q.id AS net_area_id,
          q.displayname AS net_area_name,
          m.displayname AS datacenter_name,
          m.dc_type,
          COUNT(u.id) AS hostpool_nums
        FROM
          user_group
        LEFT JOIN
          access t ON t.group_id = user_group.group_id
        LEFT JOIN
          datacenter m ON m.area_id = t.area_id AND m.isdeleted = '0'
        LEFT JOIN
          net_area q ON m.id = q.datacenter_id AND q.isdeleted = '0'
        LEFT JOIN
          hostpool u ON u.net_area_id = q.id AND u.isdeleted = '0'
        WHERE user_group.user_id = %s AND q.id IS NOT NULL
        GROUP BY q.id
        ORDER BY q.id DESC
    '''
    # 计算总数  用于分页使用
    args = [user_id]
    total_data = ins.query(db_conn, sql, args)
    total_nums = len(total_data)
    page_no = int(kwargs['page_no'])
    page_size = kwargs['page_size']
    limit_sql = ' LIMIT %d, %d' % ((int(page_no) - 1) * int(page_size), int(page_size))
    sql += limit_sql
    data = ins.query(db_conn, sql, args)
    return total_nums, data


def check_name_in_same_dc_type(net_area_name, dc_type):
    '''
        判断同一环境下机房的网络区域是否重名
    :param net_area_name:
    :param dc_type:
    :return:
    '''
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT * FROM net_area WHERE name = %s AND id IN (
            SELECT
                a.id
            FROM net_area a
            LEFT JOIN
                datacenter b ON b.id = a.datacenter_id AND b.isdeleted = '0'
            WHERE
                a.isdeleted = '0' AND b.dc_type = %s
        )
    '''
    args = [net_area_name, dc_type]
    db_conn = ins.get_connection()
    return ins.query(db_conn, sql, args)


def get_netarea_info_by_name(env, dc_name, net_area_name):
    '''
        获取指定环境、机房下的指定网络区域是否存在
    :return:
    '''
    ins = Mysql.get_instance("kvm")
    sql = '''
        SELECT
          a.id,
          a.displayname net_area_name,
          b.displayname datacenter_name,
          b.dc_type,
          c.displayname area_name,
          c.parent_id,
          c.id area_id
        FROM
          net_area a, datacenter b, area c
        WHERE
          a.isdeleted = '0'
          AND a.datacenter_id = b.id
          AND b.isdeleted = '0'
          AND b.area_id = c.id
          AND c.isdeleted = '0'
          AND b.dc_type = %s
          AND b.name = %s
          AND a.name = %s
    '''
    args = [env, dc_name, net_area_name]
    db_conn = ins.get_connection()
    return ins.query_one(db_conn, sql, args)
