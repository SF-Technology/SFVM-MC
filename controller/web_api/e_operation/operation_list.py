# coding=utf8
'''
    操作记录
'''


from flask import request
import traceback
from model.const_define import ErrorCode
from service.s_operation import operation_service
import logging
import json
from model import operation
import json_helper
from common_data_struct import base_define


class OperationResp(base_define.Base):
    def __init__(self):
        self.total = None
        self.rows = []


def operation_list():

    params = {
        'WHERE_AND': {
            '>=': {
                "operation_date": None,
            },
            '<=': {
                "operation_date": None,
            },
            '=': {
                "operation_object": None,
                "operation_action": None,
            },
            'like': {
                'operator': None,
                "operator_ip": None,
                "operation_result": None,
                "extra_data": None,
            },
        },
        'page_size': request.values.get('page_size'),
        'page_no': request.values.get('page_no'),
    }

    search = request.values.get('search')
    if search:
        json_search = json.loads(search)
        for i in json_search:
            if i == "start_time":
                params['WHERE_AND']['>=']['operation_date'] = ' ' + json_search[i] + ' '
            elif i == "end_time":
                params['WHERE_AND']['<=']['operation_date'] = ' ' + json_search[i] + ' '
            elif i == "operation_object":
                params['WHERE_AND']['=']['operation_object'] = json_search[i]
            elif i == "operation_action":
                params['WHERE_AND']['=']['operation_action'] = json_search[i]
            else:
                params['WHERE_AND']['like'][i] = '%' + json_search[i] + '%'

    # total_nums, data = operation_service.OperationService().get_operation_record(**params)
    # total_nums, data = operation_service.OperationService().query_data(**params)
    total_nums, data = operation.query_operation_list(**params)
    resp = OperationResp()
    resp.total = total_nums
    for one_data in data:
        _info = OperationInfo().init_data(one_data)
        resp.rows.append(_info)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp.to_json())


def operation_log():
    search = request.values.get('search')
    res = operation_service.OperationService().get_operation_record()
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=res)


class OperationInfo(base_define.Base):
    def __init__(self):
        self.operator = None
        self.operator_ip = None
        self.operation_object = None
        self.operation_action = None
        self.operation_date = None
        self.operation_result = None
        self.extra_data = None

    def init_data(self, one_data):
        self.operator = one_data['operator']
        self.operator_ip = one_data['operator_ip']
        self.operation_object = one_data['operation_object']
        self.operation_action = one_data['operation_action']
        self.operation_date = one_data['operation_date']
        self.operation_result = one_data['operation_result']
        self.extra_data = one_data['extra_data']

        return self

