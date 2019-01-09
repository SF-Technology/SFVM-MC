# -*- coding:utf-8 -*-
# __author__ = '郭思远'
'''
    导出v2v页面所有记录到excel表格
'''
from pyexcel_xls import save_data
from collections import OrderedDict
from flask import request, make_response
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
import StringIO
from model.const_define import V2vTaskStatusTransform, V2vCreateSourceTransform
from service.v2v_task import v2v_task_service as v2v_t_s


@login_required
def export_v2v_task_excel():
    params = {
        'page_size': request.values.get('page_size'),
        'page_no': request.values.get('page_no')
    }

    total_nums, data = v2v_t_s.v2v_task_list(**params)

    # 生成excel
    excel_data = OrderedDict()
    sheet_1 = []
    # 标题行
    row_title_data = [u"IP地址", u"任务ID", u"开始时间", u"结束时间", u"任务状态", u"任务来源",
                      u"任务详情", u"操作者"]
    sheet_1.append(row_title_data)

    for i in data:
        _row_data = [
            i['vm_ip'],
            i['request_id'],
            i['start_time'],
            i['finish_time'],
            unicode(V2vTaskStatusTransform.MSG_DICT.get(str(i['status']), '')),
            unicode(V2vCreateSourceTransform.MSG_DICT.get(i['source'], '')),
            i['message'],
            i['username']
        ]
        sheet_1.append(_row_data)

    excel_data.update({u"tasks": sheet_1})

    io = StringIO.StringIO()
    save_data(io, excel_data)

    response = make_response(io.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=v2v迁移任务信息.xls"
    return response
