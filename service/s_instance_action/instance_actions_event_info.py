# !/usr/bin/env python2.7
# -*- coding:utf-8 -*-
#

#   Date    :   2017/4/1
#   Desc    :
# Created by 062076 on 2017/4/1.
import  logging
import datetime

from service.s_instance_action import instance_action


#插入虚拟机的步骤信息
def add_instance_actions(data):
    action=data['action']
    instance_uuid=data['instance_uuid']
    request_id=data['request_id']
    user_id=data['user_id']
    message=data['message']
    insert_data ={
        'action':action,
        'instance_uuid':instance_uuid,
        'request_id':request_id,
        'user_id':user_id,
        'message':message,
        'start_time':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    ret = instance_action.InstanceActionsServices().add_instance_action_info(insert_data)
    if ret['last_id'] >0:
        return  True

    return  False




#插入虚拟机的步骤信息
def update_instance_actions(request_id,action,status,message):

    update_data ={
        'status':status,
        'finish_time':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'message':message
    }
    print message
    where_data={
        'request_id': request_id,
        'action': action
    }
    ret=instance_action.InstanceActionsServices().update_instance_action_status(update_data,where_data)
    if ret >0:
        return  True
    return  False




