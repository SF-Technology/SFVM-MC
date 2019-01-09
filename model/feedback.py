# coding=utf8
'''
    user_feedback表
'''


from lib.dbs.mysql import Mysql
from model import base_model
import json, MySQLdb

class Feedback(base_model.BaseModel):
    pass

def query_category_info():
    ins = Mysql.get_instance("kvm")
    db_conn = ins.get_connection()
    sql = "SELECT a.category,a.id ,b.category,b.id , c.category,c.id FROM " \
          "(problem_category_info a INNER JOIN problem_category_info b " \
          "ON a.id = b.parent_id ) INNER JOIN problem_category_info c " \
          "ON b.id = c.parent_id WHERE a.category ='概览'OR a.category ='区域' "

    sql2 = "select a.category,a.id ,b.category,b.id  from problem_category_info a " \
            "inner join problem_category_info b on a.id = b.parent_id where a.category ='机房'" \
            "or a.category ='网络区域'or a.category ='集群'or a.category ='HOST'or a.category ='VM'" \
            "or a.category ='IP'or a.category ='镜像管理'or a.category ='组管理'or a.category ='迁移' ;"
    arg = []
    data = ins.query(db_conn, sql, arg)
    data2 = ins.query(db_conn, sql2, arg)

    category = {}
    for i in range(len(data)):
        row = data[i]
        parts = [row['category'], row['b.category'], row['c.category']]
        parent = category
        key = parts.pop(0)
        while parts:
            parent = parent.setdefault(key, {})
            key = parts.pop(0)
        parent[key] = row['c.id']

    for i in range(len(data2)):
        row = data2[i]
        parts = [row['category'], row['b.category']]
        parent = category
        key = parts.pop(0)
        while parts:
            parent = parent.setdefault(key, {})
            key = parts.pop(0)
        parent[key] = row['b.id']

    return category
