# coding=utf8
'''
    物理机管理-导出文件
'''
# __author__ =  ""

# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
from flask import request, make_response
import json
from service.s_host import host_service as host_s
from service.s_instance import instance_service as ins_s
from service.s_host import host_schedule_service as host_s_s
from service.s_user.user_service import get_user
from model import host
from model.const_define import DataCenterTypeMsg, HostStatusMsg, HostTypeStatusMsg
from pyexcel_xls import save_data
from collections import OrderedDict
import StringIO


@login_required
def export_host_excel():
    params = {
        'WHERE_AND': {
            '=': {
                'status': None
            },
            'like': {
                'name': None,
                'sn': None,
                'ip_address': None,
                'manage_ip': None
            },
            'in': {
                'id': None
            }
        },
        'search_in_flag': 0,
        'page_size': request.values.get('page_size'),
        'page_no': request.values.get('page_no'),
    }

    search = request.values.get('search')
    if search:
        json_search = json.loads(search)
        name = json_search.get('name')
        if name:
            params['WHERE_AND']['like']['name'] = '%' + name + '%'

        sn = json_search.get('sn')
        if sn:
            params['WHERE_AND']['like']['sn'] = '%' + sn + '%'

        ip_address = json_search.get('ip_address')
        if ip_address:
            params['WHERE_AND']['like']['ip_address'] = '%' + ip_address + '%'

        manage_ip = json_search.get('manage_ip')
        if manage_ip:
            params['WHERE_AND']['like']['manage_ip'] = '%' + manage_ip + '%'

        status = json_search.get('status')
        if status:
            params['WHERE_AND']['=']['status'] = status

        hostpool_name = json_search.get('hostpool_name')
        if hostpool_name:
            params['search_in_flag'] = 1
            # 先模糊查询hostpool name对应的HOST ID
            search_hostpool_data = host_s.get_hosts_by_fuzzy_hostpool_name(hostpool_name)
            host_id_list = [i['host_id'] for i in search_hostpool_data]
            if host_id_list:
                params['WHERE_AND']['in']['id'] = tuple(host_id_list)

    total_nums, data = host.user_host_list(get_user()['user_id'], **params)

    # 生成excel
    excel_data = OrderedDict()
    sheet_1 = []
    # 标题行
    row_title_data = [u"序列号(主键)", u"主机名", u"IP地址", u"状态", u"业务状态", u"集群", u"网络区域", u"所在机房",
                      u"机房类型", u"管理IP", u"VM数量", u"保留内存", u"内存分配率(%)"]
    sheet_1.append(row_title_data)

    for i in data:
        _row_data = [
            i['sn'],
            i['host_name'],
            i['ipaddress'],
            unicode(HostStatusMsg.MSG_DICT.get(i['status'], '')),
            unicode(HostTypeStatusMsg.MSG_DICT.get(i['typestatus'], '')),
            i['hostpool_name'],
            i['net_area_name'],
            i['datacenter_name'],
            unicode(DataCenterTypeMsg.MSG_DICT.get(int(i['dc_type']), '')),
            i['manage_ip'],
            ins_s.get_instances_nums_in_host(i['host_id']),
            i['hold_mem_gb'],
            host_s_s.get_host_mem_assign_percent(i),
        ]
        sheet_1.append(_row_data)

    excel_data.update({u"hosts": sheet_1})

    io = StringIO.StringIO()
    save_data(io, excel_data)

    response = make_response(io.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=物理机信息.xls"
    return response