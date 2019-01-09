# coding=utf8
'''
    物理机性能信息管理
'''
# __author__ =  ""

# import sys
from service.s_host import host_metric_service as hms
from flask import request
import json_helper
import host_metric_list
import requests
import json


# 处理post请求过来的数据，并写入数据库
def flush_host_perform_data_to_db():
    """
        提交数据并写入数据库，返回插入数据状态
        :return
        {
          "code": 0,
          "data": {
            "operate_return": "success",
            "record_num": 11,
            "record_success_insert_num": 11
          },
          "msg": "success"
        }
    """


    datadict = request.data
    datadict = json_helper.loads(datadict)   #数据可能有多条
    datadict = datadict['params']

    datadict = datadict['params']
    print datadict
    ndatalist = []      # 存放多条数据的列表
    ndatadict = {}      # 临时存储每一条数据【字典】
    for metric_key, info in datadict.items():
        ndatadict['metric_key'] = metric_key
        for key, value in info.items():
            ndatadict[key] = value
        ndatalist.append(ndatadict)
        ndatadict = {}
    result = hms.HostMetricService().push_data_to_db(metricinfo_list=ndatalist)

    print "result=", result
    r = host_metric_list.host_metric_apiresp(result)
    return r

#处理网络get请求的入口【api方式】
def get_host_perform_data():
    needinfo =  hms.HostMetricService().get_data_from_db()
    print 'needinfo=',needinfo
    r = host_metric_list.host_metric_getapiresp(needinfo)
    print r
    return r

#处理网络get请求的入口【通过host_ip】
def get_host_perform_data_by_hostip(host_ip=None):
    if request.method == 'POST':
        print 'post=',request
        print request.data
    datadict = json_helper.loads(request.data)
    gethostip = datadict['params']['host_ip']
    needinfo =  hms.HostMetricService().get_data_from_db_with_post(gethostip)
    print 'needinfo_byhostip=',needinfo
    r = host_metric_list.host_metric_getapiresp(needinfo)
    return r

if __name__ == '__main__':
    pass


    #data = json_helper.write(msg)
    #data = json_helper.dumps(msg)
    #result = flush_host_perform_data_to_db(data=data)
    #print result
    #data = {'params':json.dumps(msg)}
    #data = {"params":json.dumps(uuid)}
    #print data
    #print r.content
    #print r.content