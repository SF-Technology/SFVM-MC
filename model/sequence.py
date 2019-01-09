# coding=utf8
'''
    生成sequence
'''


from dbs.mysql import Mysql


def get_next(seq_name):
    '''
        获取sequnce的下一个值
    :param seq_name: 需要先在sequence表中插入是初始化的值
    :return int:
    '''
    db_pool = Mysql.get_instance('user')
    db_connection = db_pool.get_connection()
    sql = '''UPDATE sequence SET seq_value = LAST_INSERT_ID(seq_value + 1) WHERE seq_name = %s'''
    args = [seq_name]
    db_pool.execute(db_connection,sql, args)
    sql2 = '''
        SELECT LAST_INSERT_ID() id;
    '''
    rs2 = db_pool.query_one(db_connection,sql2)
    db_pool.commit(db_connection)
    return rs2 and rs2['id'] or None
