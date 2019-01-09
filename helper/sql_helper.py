#coding=utf8
__author__ =  ""
'''
    生成sql语句的一些工具函数'''


def generate_insert_sql(tablename, dict_data):
    '''
        生成insert的sql语句
    :param tablename:
    :param dict_data:
    :return  tuple:
             (string sql,  list args)  tuple的前面一个元素表示格式化好的字符串的sql 后面一个表示参数是list类型
    '''
    sql = ' INSERT INTO ' + tablename + " "
    keys = dict_data.keys()
    sql += '('
    for i in keys:
        sql += i + ','
    sql = sql.rstrip(',')
    sql += ') '
    sql += " VALUES "
    args = []
    sql += '('
    for i in keys:
        args.append(dict_data[i])
        sql += "%s,"
    sql = sql.rstrip(',')
    sql += ')'
    return sql, args



def generate_update_sql(tablename, update_data, where_data):
    '''
        生成update语句
    :param tablename:
    :param update_data:
    :param where_data:
    :return:
    '''
    sql = ' UPDATE ' + tablename
    sql += ' SET '
    args = []
    for i in update_data.items():
        sql += ' `'+i[0]+'`' +' =  %s,'
        args.append(i[1])
    sql = sql.rstrip(',')
    sql += ' WHERE 1 = 1'
    for i in where_data.items():
        sql += ' AND ' + i[0] + ' = %s'
        args.append(i[1])
    return sql, args


def generate_delete_sql(tablename, where_data):
    '''
        生成简单的delete语句
    :param tablename:
    :param where_data:
    :return:
    '''
    sql = ' DELETE FROM ' + tablename
    sql += ' WHERE 1 = 1 '
    if not where_data:
        #不许不带where条件
        return ' 1 = 2 '
    args = []
    for i in where_data.items():
        # sql += ' AND %s = %s'
        sql += ' AND ' + i[0] + ' = %s'
        # args.append(i[0])
        args.append(i[1])
    return sql,args


