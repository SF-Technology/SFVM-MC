# !/usr/bin/env python2.7
# -*- coding:utf-8 -*-


import base_model
import instance_actions
from time_helper import get_datetime_str


class InstanceActionsServices(base_model.BaseModel):

    def __init__(self):
        self.instance_actions_db = instance_actions.InstanceActions(db_flag='kvm', table_name='instance_actions')

    def query_data(self, **params):
        return self.instance_actions_db.simple_query(**params)

    def get_instance_action(self, instance_id):
        return self.instance_actions_db.get_one('id', instance_id)

    def update_instance_specaction_status(self,update_data,request_id,action):
        update_da = {
            "status":update_data
        }
        where_data = {
            "request_id":request_id,
            "action":action
        }
        return self.instance_actions_db.update(update_da, where_data)

    def add_instance_action_info(self, insert_data):
        return self.instance_actions_db.insert(insert_data)

    def update_instance_action_status(self, update_data, where_data):
        return self.instance_actions_db.update(update_data, where_data)

    def get_request_id_in_instance_action(self, request_id):
        return self.instance_actions_db.get_one('request_id', request_id)

    def delete_instance_action(self, request_id, action, instance_uuid):
        where_data = {
            'instance_uuid': instance_uuid,
            'request_id': request_id,
            'action': action
        }
        return self.instance_actions_db.delete(where_data)


def add_instance_actions(data):
    '''
        插入虚拟机的步骤信息
    :param data:
    :return:
    '''
    action = data['action']
    instance_uuid = data['instance_uuid']
    request_id = data['request_id']
    user_id = data['user_id']
    message = data['message']
    insert_data = {
        'action': action,
        'instance_uuid': instance_uuid,
        'request_id': request_id,
        'user_id': user_id,
        'message': message,
        'start_time': get_datetime_str()
    }
    ret = InstanceActionsServices().add_instance_action_info(insert_data)
    if ret['last_id'] > 0:
        return True
    return False

def add_instance_actions_test(data):
    '''
        插入虚拟机的步骤信息
    :param data:
    :return:
    '''
    action = data['action']
    instance_uuid = data['instance_uuid']
    task_id = data['task_id']
    request_id = data['request_id']
    user_id = data['user_id']
    message = data['message']
    status = data['status']
    finish_time = data['finish_time']    #add
    insert_data = {
        'action': action,
        'instance_uuid': instance_uuid,
        'task_id': task_id,
        'request_id': request_id,
        'user_id': user_id,
        'status': status,
        'message': message,
        'start_time': get_datetime_str(),
        'finish_time': finish_time          #add
    }
    ret = InstanceActionsServices().add_instance_action_info(insert_data)
    if ret['last_id'] > 0:
        return True
    return False

def update_instance_actions(request_id, action, status, message):
    '''
        更新虚拟机的步骤信息
    :param request_id:
    :param action:
    :param status:
    :param message:
    :return:
    '''
    update_data = {
        'status': status,
        'finish_time': get_datetime_str(),
        'message': message
    }
    where_data = {
        'request_id': request_id,
        'action': action
    }
    ret = InstanceActionsServices().update_instance_action_status(update_data, where_data)
    if ret > 0:
        return True
    return False


def add_instance_actions_when_vm_image_check(data):
    '''
        插入虚拟机的步骤信息
    :param data:
    :return:
    '''
    action = data['action']
    instance_uuid = data['instance_uuid']
    request_id = data['request_id']
    user_id = data['user_id']
    message = data['message']
    task_id = data['task_id']
    insert_data = {
        'action': action,
        'instance_uuid': instance_uuid,
        'request_id': request_id,
        'task_id': task_id,
        'user_id': user_id,
        'message': message,
        'start_time': get_datetime_str()
    }
    ret = InstanceActionsServices().add_instance_action_info(insert_data)
    if ret['last_id'] > 0:
        action_id = ret.get('last_id')
        return True, action_id
    return False, 0


def update_instance_actions_when_vm_create(request_id, action, status, message, task_id):
    '''
        更新虚拟机的步骤信息
    :param request_id:
    :param action:
    :param status:
    :param message:
    :return:
    '''
    update_data = {
        'status': status,
        'finish_time': get_datetime_str(),
        'message': message,
        'task_id': task_id
    }
    where_data = {
        'request_id': request_id,
        'action': action
    }
    ret = InstanceActionsServices().update_instance_action_status(update_data, where_data)
    if ret > 0:
        return True
    return False


def update_instance_actions_when_image_check(request_id, action, status, message, task_id, action_id):
    '''
        更新虚拟机的镜像确认步骤信息
    :param request_id:
    :param action:
    :param status:
    :param message:
    :return:
    '''
    update_data = {
        'status': status,
        'finish_time': get_datetime_str(),
        'message': message,
        'task_id': task_id
    }
    where_data = {
        'request_id': request_id,
        'action': action,
        'id': action_id
    }
    ret = InstanceActionsServices().update_instance_action_status(update_data, where_data)
    if ret > 0:
        return True
    return False


def whether_vm_repeat_create(request_id):
    '''
        检查是否有虚拟机创建
    :param instance_uuid:
    :return:
    '''
    ret = InstanceActionsServices().get_request_id_in_instance_action(request_id)
    if ret:
        return True
    else:
        return False


def whether_vm_create_step_error(request_id):
    '''
        检查虚拟机创建过程中是否有失败步骤
    :param request_id:
    :return:
    '''
    params = {
        'WHERE_AND': {
            '=': {
                'request_id': request_id,
            },
        },
    }
    total_nums, data = InstanceActionsServices().query_data(**params)
    for create_step in data:
        if create_step['status'] == 2:
            return True
    return False


def get_instance_action_service_status(request_id, action):
    '''
         获取服务状态
     :param :
     :return:
     '''
    params = {
        'WHERE_AND': {
            "=": {
                'request_id': request_id,
                'action': action
            }
        },
    }
    act_num, act_data = InstanceActionsServices().query_data(**params)
    if act_num <= 0:
        return False, ''
    else:
        for per_action_data in act_data:
            act_status = per_action_data['status']
            if not per_action_data['status']:
                return True, act_status
            else:
                return True, int(act_status)


def get_instance_action_by_task_id(task_id):
    params = {
        'WHERE_AND': {
            '=': {
                'task_id': task_id,
            },
        },
    }
    total_nums, data = InstanceActionsServices().query_data(**params)
    if total_nums > 0:
        return True, data
    else:
        return False, ''


def get_instance_action_by_message(message):
    params = {
        'WHERE_AND': {
            '=': {
                'message': message,
            },
        },
        'ORDER': [
            ['start_time', 'desc']
        ],
    }
    total_nums, data = InstanceActionsServices().query_data(**params)
    if total_nums > 0:
        return True, data
    else:
        return False, ''


def get_instance_action_by_action_start():
    params = {
        'WHERE_AND': {
            '=': {
                'message': 'start',
                'action': 'instance_directory_create'
            },
        },
    }
    total_nums, data = InstanceActionsServices().query_data(**params)
    if total_nums > 0:
        return True, data
    else:
        return False, ''
