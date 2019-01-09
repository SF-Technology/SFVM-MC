# coding=utf8
'''
    用户反馈
'''


from flask import request
import traceback
from model.const_define import ErrorCode
from service.s_feedback import feedback_service
import logging
import json_helper
from common_data_struct import base_define, feedback_info
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user


class FeedbackResp(base_define.Base):

    def __init__(self):
        self.total = None
        self.rows = []


@login_required
def feedback_list():
    user_id = request.values.get('user_id')

    params = {
        'ORDER': [
            ['id', 'desc'],
        ],
        'PAGINATION': {
            'page_size': request.values.get('page_size', 20),
            'page_no': request.values.get('page_no', 1),
        },
        'WHERE_AND': {
            '=': {
            }
        }
    }

    if user_id:
        params['WHERE_AND']['=']['user_id'] = user_id
    else:
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    total_nums, data = feedback_service.FeedbackService().query_data(**params)
    resp = FeedbackResp()
    resp.total = total_nums
    for i in data:
        _feedback_info = feedback_info.FeedbackInfo().init_from_db(i)
        resp.rows.append(_feedback_info)

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp.to_json())
