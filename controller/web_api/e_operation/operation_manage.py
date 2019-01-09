#coding=utf8
'''
    操作记录
'''


from flask import request
from model.const_define import ErrorCode
from service.s_operation import operation_service
import logging
import json_helper
import datetime


def add_operation(operator, operator_ip, operation_object, operation_action, operation_result, extra_data=None):

    insert_data = {
        "operator": operator,
        "operator_ip": operator_ip,
        "operation_object": operation_object,
        "operation_action": operation_action,
        "operation_date": datetime.datetime.now(),
        "operation_result": operation_result,
        "extra_data": extra_data
    }
    # from service.s_operation.operation_service import add_operation
    # add_operation(user_id, '', '用户反馈', 'CREATE', 'FAILED', '')
    # add_operation(user_id, '', '用户反馈', 'CREATE', 'SECCESS', '')
    ret = operation_service.OperationService().insert_operation(insert_data)
    if ret.get('row_num') <= 0:
        logging.error("add operation error, insert_data:%s", str(insert_data))
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)