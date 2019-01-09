# coding=utf8
'''
    v2v_openstack_cancel
'''
# __author__ = 'anke'

from flask import request
from helper import json_helper
from service.v2v_task import v2v_task_service as v2v_op
from model.const_define import ErrorCode,VMCreateSource

def v2v_openstack_cancel():

    #获取入参信息
    cancel = request.values.get('cancel')
    request_his = request.values.get('request_id')
    source = v2v_op.v2vTaskService().get_v2v_task_by_requestid(request_his)['source']

    if cancel != '1':
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg='参数错误')

    #判断当前任务是否完成
    res_task = v2v_op.get_v2v_running_by_reqid(request_his)
    if res_task == False:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='任务状态无法操作')
    else:
        up_cal = v2v_op.updata_v2v_cancel(request_his,1,3)
        if up_cal == True:
            return json_helper.format_api_resp(code=ErrorCode.SUCCESS, msg='取消下发成功')
        else:
            return json_helper.format_api_resp(code=ErrorCode.SUCCESS, msg='取消下发失败')






