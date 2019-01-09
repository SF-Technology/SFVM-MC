# coding=utf8
# __author__ = ""
'''
    使用DBUtils为MySQLDB客户端的连接池二次封装 (线程安全的)

    依赖config default.py当中的配置文件
        'db':{
            'user' : {
                        'db_type' : 'mysql',
                        'maxconnections' : 30,  #允许的最大连接数,
                        'user' : 'test_user',
                        'passwd' : 's5IQABSd8G4=',
                        'host' : '127.0.0.1',
                        'port' : 3306,
                        'charset' : 'utf8',   #不指定的话,默认utf8
                        'database_name' : 'test_db_nmae' #数据库的名字
                    },
            'goods' : {
                        'db_type' : 'mysql',
                        'maxconnections' : 30,  #允许的最大连接数,
                        'user' : 'test_user_2',
                        'passwd' : 's5IQABSd8G4=',
                        'host' : '127.0.0.1',
                        'port' : 3306,
                        'charset' : 'utf8',   #不指定的话,默认utf8
                        'database_name' : 'test_db_name2', #数据库的名字
                    },
        },

    用法:
        from dbs.mysql import Mysql
        db_pool = Mysql.get_instance('goods')    #这里的goods字符串来自于上面的配置前面可key
        #从连接池中获取一个可用的连接
        db_connection = db_pool.get_connection()

        #select语句
        sql = "select * from test_table where id = %s"
        args = [222]
        res = db_pool.query(db_connection, sql, args)  #还有query_one方法

        #insert语句
        sql = "insert into test_table (name) values (%s)"
        args = ["name2"]
        #请传入刚才获取的db连接db_connection变量
        lastrowid = db_pool.insert(db_connection, sql, ['g3'])   #插入成功则返回主键id
        #请显式的提交事务  不要开启auto_commit
        db_pool.commit(db_connection)

        #update语句
        sql = "update test_table set name = %s where id = %s"
        args = ['name_333', 66]
        #请传入刚才获取的db连接db_connection变量
        db_pool.execute(db_connection, sql, args)
        #请显式的提交事务  不要开启auto_commit
        db_pool.commit(db_connection)
'''

import MySQLdb
from MySQLdb.cursors import DictCursor
from DBUtils.PooledDB import PooledDB
from helper import encrypt_helper
from helper import sql_helper


INSTANCE_POOL = {

}


class Mysql(object):

    def __init__(self, db_flag_name, **kwargs):
        '''
                构造函数
        :param db_flag_name:

        :param kwargs:
        '''
        params_init_db_pool = {
            'creator': MySQLdb,
            # 'mincached' : kwargs.get("mincached", 5),
            # 'maxcached' : kwargs.get("maxcached", 10),
            'maxconnections': kwargs.get("maxconnections", 50),
            'user': kwargs.get("user"),
            'passwd': encrypt_helper.decrypt(kwargs.get("passwd")),
            'host': kwargs.get("host", '127.0.0.1'),
            'port': kwargs.get("port", 3306),
            'charset': kwargs.get("charset", 'utf8'),
            'cursorclass': DictCursor,
            'db': kwargs.get("database_name"),
            'setsession': kwargs.get("setsession"),
            'reset': False,
            'connect_timeout': 60 * 2,
        }
        self.db_pool = PooledDB(**params_init_db_pool)
        self.fetch_many_size = 20000


    @staticmethod
    def get_instance(db_flag_name):
        global INSTANCE_POOL
        from config import GLOBAL_CONFIG
        init_config = GLOBAL_CONFIG.get('db').get(db_flag_name)
        pool_db_instance = INSTANCE_POOL.get(db_flag_name)
        if not pool_db_instance:
            pool_db_instance = Mysql(db_flag_name, **init_config)
            INSTANCE_POOL[db_flag_name] = pool_db_instance
        return pool_db_instance

    def get_connection(self):
        return self.db_pool.connection()

    def get_cursor(self, connection):
        return connection.cursor()

    def query(self, connection, *args, **kwargs):
        cursor = self.get_cursor(connection)
        cursor.execute(*args, **kwargs)
        # 这里限制查询出的最多条数  如果需要查询更多的条数  请手工设置fetch_many_size属性
        rs = cursor.fetchmany(size=self.fetch_many_size)
        return rs

    def query_one(self, connection, *args, **kwargs):
        cursor = self.get_cursor(connection)
        cursor.execute(*args, **kwargs)
        rs = cursor.fetchone()
        return rs

    def insert(self, connection, *args, **kwargs):
        cursor = self.get_cursor(connection)
        ret = cursor.execute(*args, **kwargs)
        return {
            'row_num' : cursor.rowcount,  # 影响的行数
            'last_id' : cursor.lastrowid,  # 最后插入的自增id
        }

    def begin(self, connection):
        connection.begin()

    def commit(self, connection):
        connection.commit()

    def rollback(self, connection):
        connection.rollback()

    def execute(self, connection, *args, **kwargs):
        cursor = self.get_cursor(connection)
        return cursor.execute(*args, **kwargs)

    def execute_many(self, connection, *args, **kwargs):
        cursor = self.get_cursor(connection)
        return cursor.executemany(*args, **kwargs)

    def simple_insert(self, table_name, insert_data, db_conn=None):
        if not db_conn:
            db_conn = self.get_connection()
        insert_sql, args = sql_helper.generate_insert_sql(table_name, insert_data)
        return self.insert(db_conn, insert_sql, args)

    def simple_update(self, table_name, update_data, where_data,db_conn=None):
        if not db_conn:
            db_conn = self.get_connection()
        update_sql, args = sql_helper.generate_update_sql(table_name, update_data, where_data)
        return self.execute(db_conn, update_sql, args)

    def simple_delete(self, table_name, where_data, db_conn=None):
        if not db_conn:
            db_conn = self.get_connection()
        delete_sql, args = sql_helper.generate_delete_sql(table_name, where_data)
        return self.execute(db_conn, delete_sql, args)


if __name__ == '__main__':
    pass
