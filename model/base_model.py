#coding=utf8
'''
    把对于表的简单的curd操作封装起来 不用重复去copy paster代码
'''
__author__ =  ""

from lib.dbs.mysql import Mysql
import logging


class BaseModel(object):

    def __init__(self, db_flag, table_name):
        '''
        :param db_flag:  config中的数据库连接标识
        :param table_name: 表名
        :return:
        '''
        self.db_flag = db_flag
        self.table_name = table_name
        self.db_instance = Mysql.get_instance(self.db_flag)

    def get_db_instance(self):
        return self.db_instance

    def insert(self, insert_data, db_conn=None):
        '''
        :param dict insert_data:  {'字段名':'字段值'}
        :return:
        '''
        if not db_conn:
            db_conn = self.db_instance.get_connection()
        return self.db_instance.simple_insert(self.table_name, insert_data, db_conn)

    def batch_insert(self,  insert_data_list):
        '''
            通过一条sql语句批量插入
      :param insert_data_list:
        :return:
        '''
        #TODO
        pass

    def update(self, update_data, where_data):
        '''
        :param dict update_data:
        :param dict where_data:
        :return:
        '''
        return self.db_instance.simple_update(self.table_name, update_data, where_data)

    def delete(self, where_data):
        '''
        :return:
        '''
        return self.db_instance.simple_delete(self.table_name, where_data)

    def get_one(self, where_field, where_field_value):
        '''
            根据单个字段值 返回一条记录
        :param field:
        :param field_value:
        :return:
        '''
        sql = '''SELECT * FROM ''' + self.table_name
        sql += " WHERE `" + where_field + "`" + " = %s"
        args = [where_field_value]
        db_conn = self.db_instance.get_connection()
        return self.db_instance.query_one(db_conn, sql, args)

    def simple_query(self, **kwargs):
        '''

                生成常规的sql语句
                如果复杂sql，请自行拼装
        :param kwargs:
               {
                    'WHERE_AND' :
                        {
                            '=' : {
                                'field-1' : 'field-1-value',
                                'field-2' : 'field-2-value',
                            },
                            '!=' : {
                                'field-1' : 'field-1-value',
                                'field-2' : 'field-2-value',
                            },
                            '>=' : {
                                'field-1' : 'field-1-value',
                                'field-2' : 'field-2-value',
                            },
                            '<=' : {
                                'field-1' : 'field-1-value',
                                'field-2' : 'field-2-value',
                            },
                            '>' : {
                                'field-1' : 'field-1-value',
                                'field-2' : 'field-2-value',
                            },
                            '<' : {
                                'field-1' : 'field-1-value',
                                'field-2' : 'field-2-value',
                            },
                            'in' : {
                                'field-1' : ['value-1','value-2']
                                'field-2' : ['value-1','value-2']
                            },
                            'not in' : {
                                'field-1' : ['value-1','value-2']
                                'field-2' : ['value-1','value-2']
                            },
                            'like' : {
                                'field-1' : 'field1-value 这里对应sql中like后面的，自行定义',
                                'field-2' : 'field1-value 这里对应sql中like后面的，自行定义',
                             }
                            'not like' : {
                                'field-1' : 'field1-value 这里对应sql中like后面的，自行定义',
                                'field-2' : 'field1-value 这里对应sql中like后面的，自行定义',
                             }
                            'between_and' : {
                                'field-1' : ['start_value','end_value'],
                                'field-2' : ['start_value','end_value'],
                             }
                        },
                   'ORDER': [
                        ['field1', 'asc'],
                        ['field2', 'desc']
                    ],
                    'PAGINATION': {   #如果要分页 两个必须传递
                        'page_size' : 10,  #每页多少条数据
                        'page_no': 2,      #页码
                    },
               }
        :return:
        '''
        sql = "SELECT * FROM " + self.table_name + " WHERE 1 = 1 "
        count_sql = " SELECT COUNT(*) total_nums FROM " + self.table_name + " WHERE 1 = 1 "
        where_sql = ''
        args = []
        if kwargs.get('WHERE_AND'):
            where_and = kwargs.get('WHERE_AND')
            if where_and.get('='):
                for key, value in where_and.get('=').items():
                    where_sql += ' AND '+key + ' = %s'
                    args.append(value)
            if where_and.get('!='):
                for key, value in where_and.get('!=').items():
                    where_sql += ' AND '+key + ' != %s'
                    args.append(value)
            if where_and.get('>='):
                for key, value in where_and.get('>=').items():
                    where_sql += ' AND '+key + ' >= %s'
                    args.append(value)
            if where_and.get('<='):
                for key, value in where_and.get('<=').items():
                    where_sql += ' AND '+key + ' <= %s'
                    args.append(value)
            if where_and.get('<'):
                for key, value in where_and.get('<').items():
                    where_sql += ' AND '+key + ' <  %s'
                    args.append(value)
            if where_and.get('>'):
                for key, value in where_and.get('>').items():
                    where_sql += ' AND '+key + ' >  %s'
                    args.append(value)
            if where_and.get('in'):
                for key, value in where_and.get('in').items():
                    where_sql += ' AND '+key + ' IN  %s'
                    args.append(tuple(value))
            if where_and.get('not in'):
                for key, value in where_and.get('not in').items():
                    where_sql += ' AND '+key + ' NOT IN  %s'
                    args.append(tuple(value))
            if where_and.get('like'):
                for key, value in where_and.get('like').items():
                    where_sql += ' AND '+key + ' LIKE  %s'
                    args.append(value)
            if where_and.get('not like'):
                for key, value in where_and.get('not like').items():
                    where_sql += ' AND '+key + ' NOT LIKE  %s'
                    args.append(value)
            if where_and.get('between_and'):
                for key, value in where_and.get('between_and').items():
                    where_sql += ' AND '+key + ' between %s and %s'
                    args.append(value[0])
                    args.append(value[1])

        count_sql += where_sql
        db_conn = self.db_instance.get_connection()
        count_result = self.db_instance.query_one(db_conn, count_sql, args)
        total_nums = count_result.get('total_nums', 0)
        order_sql = ' '
        if kwargs.get('ORDER'):
            order_sql += ' ORDER BY '
            ORDER = kwargs['ORDER']
            for i in ORDER:
                order_sql += i[0] + ' ' + i[1] + ','
            # 切除最后多余的逗号
            order_sql = order_sql[0:-1]
        limit_sql = ' '
        if kwargs.get('PAGINATION'):
            page_size = kwargs.get('PAGINATION').get('page_size', 100)
            page_no = kwargs.get('PAGINATION').get('page_no', 1)
            if int(page_no) == 1:
                limit_sql = ' LIMIT 0,' + str(int(page_size))
            else:
                limit_sql = ' LIMIT ' + str((int(page_no) - 1)*int(page_size)) + ',' + str(int(page_size))

        finally_sql = sql + where_sql + order_sql + limit_sql

        logging.debug('finally sql %s %s', finally_sql, args)

        data = self.db_instance.query(db_conn, finally_sql, args)

        return total_nums, data








