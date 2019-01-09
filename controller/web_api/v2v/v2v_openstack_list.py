from flask import request
import json_helper
from service.v2v_task import v2v_task_service as v2v_op
from model.const_define import ErrorCode
from common_data_struct import base_define
from service.s_user import user_service as us_s
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user


class V2v_0p_listInfoResp(base_define.Base):

    def __init__(self):
        self.total = None
        self.rows = []


@login_required
def V2v_Op_Info():
    userid = request.values.get('user_id')
    superadmin = request.values.get('superadmin')
    page_size = int(request.values.get('page_size'))
    page_no = int(request.values.get('page_no'))
    resp = V2v_0p_listInfoResp()
    params = {
        'page_size': page_size,
        'page_no': page_no
    }
    if userid:
        if superadmin == '1':
            is_admin = True
        else:
            is_admin = False
        total_nums, data = v2v_op.v2v_task_list(**params)
        resp.total = total_nums
        for i in data:
            resp.rows.append(i)

        return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp.to_json())

    else:
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg='missing input param')

















