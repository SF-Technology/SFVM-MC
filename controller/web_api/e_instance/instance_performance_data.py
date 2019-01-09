# -*- coding:utf-8 -*-



import os
import time
# from flask.ext.httpauth import HTTPBasicAuth
from flask_httpauth import HTTPBasicAuth
from config import KAFKA_TOPIC_NAME
from helper import json_helper
from helper.time_helper import get_datetime_str
from lib.mq.kafka_client import send_async_msg
from model.const_define import VsJobStatus
from service.s_ip import ip_lock_service

auth_api_user = HTTPBasicAuth()


def instance_performance_data_to_other_platform():
    '''获取web服务器的性能数据'''
    msg = ''
    command = "supervisorctl status | awk -F ' ' '{print $2}'"
    supervisorctl_data = os.popen(command).read()
    supervisorctl_list = supervisorctl_data.split('\n')[:-1]
    for i in supervisorctl_list:
        if i.strip() != "RUNNING":
            msg += 'web服务器性能数据存在非running状态； '
    table_vishi = ip_lock_service.IpLockService().get_ip_lock_info("performance_data")
    if table_vishi:
        update_data = {
            "istraceing":"0"
        }
        where_data = {
            "table_name":"performance_data"
        }
        ip_lock_service.IpLockService().update_ip_lock_info(update_data,where_data)

    else:
        insert_data = {
            "table_name":"performance_data",
            "istraceing":"0"
        }
        ip_lock_service.IpLockService().add_ip_lock_db(insert_data)
    ret_ip_lock = ip_lock_service.IpLockService().get_ip_lock_info("performance_data")
    if ret_ip_lock["istraceing"] != "0":
        msg += 'web服务器性能数据设置检测初始化数据失败； '
    data = {
        "routing_key": "INSTANCE.PERFORMANCE",
        "send_time": get_datetime_str(),
        "data":{
            "table_name":"performance_data"
        }
    }
    send_async_msg(KAFKA_TOPIC_NAME,data)
    nums = 0
    status = False
    while nums <10:
        table_vishi = ip_lock_service.IpLockService().get_ip_lock_info("performance_data")
        if str(table_vishi["istraceing"]) == '1':
            status = True
            break
        else:
            nums += 1
            time.sleep(1)
    if not status:
        msg += 'kafka消费任务异常，超时10秒； '
    if msg:
        return json_helper.format_api_resp_msg_to_vishnu_resource(job_status=VsJobStatus.FAILED,detail=msg)
    return json_helper.format_api_resp_msg_to_vishnu_resource(job_status=VsJobStatus.SUCCEED,detail='web服务器正常，kafka消费正常')


