# coding=utf8
'''
    用户反馈
'''


from flask import request
from model.const_define import ErrorCode, OperationObject, OperationAction
from service.s_feedback import feedback_service
import logging
import json_helper
import datetime
from service.s_operation.operation_service import add_operation
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user


@login_required
@add_operation(OperationObject.FEEDBACK, OperationAction.ADD)
def add_feedback():
    user_id = request.values.get('user_id')
    problem_id = request.values.get('problem_id')
    problem_description = request.values.get('problem_description')
    network_address = request.values.get('network_address')
    problem_category = request.values.get('problem_category')
    submit_time = datetime.datetime.now()

    if not user_id or not problem_id or not problem_description or not network_address:
        logging.info('the params is invalid when add feedback')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    insert_data = {
        'user_id': user_id,
        'problem_id': problem_id,
        'problem_description': problem_description,
        'network_address': network_address,
        'problem_category': problem_category,
        'submit_time': submit_time
    }

    ret = feedback_service.FeedbackService().add_feedback_info(insert_data)
    if ret.get('row_num') <= 0:
        logging.error("add feedback error, insert_data:%s", str(insert_data))
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


@login_required
def get_problem_category():
    res = feedback_service.FeedbackService().get_category_info()
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=res)


