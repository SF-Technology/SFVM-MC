# coding=utf8
'''
    虚拟机管理-导出文件
'''


from pyexcel_xls import save_data
from collections import OrderedDict
from flask import request, make_response
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
import StringIO
from model import instance
import json
from service.s_instance import instance_service as ins_s
from service.s_user.user_service import get_user, current_user_role_ids
from model.const_define import VMStatusMsg, DataCenterTypeMsg


@login_required
def export_instance_excel():
    params = {
        'WHERE_AND': {
            '=': {
                'status': None
            },
            'like': {
                'name': None,
                'uuid': None,
                'owner': None
            },
            'in': {
                'id': None
            }
        },
        'search_in_flag': 0,
        'page_size': request.values.get('page_size'),
        'page_no': request.values.get('page_no'),
    }
    ip_search_type = ''
    search = request.values.get('search')
    if search:
        json_search = json.loads(search)
        name = json_search.get('name')
        if name:
            params['WHERE_AND']['like']['name'] = '%' + name + '%'

        uuid = json_search.get('uuid')
        if uuid:
            params['WHERE_AND']['like']['uuid'] = '%' + uuid + '%'

        ip_address = json_search.get('ip_address')
        if ip_address:
            ip_search_type = json_search.get("ip_search_type")
            params['search_in_flag'] = 1
            # 先模糊查询IP地址对应的实例ID
            search_ip_data = ins_s.get_instances_by_fuzzy_ip(ip_address,ip_search_type)
            instance_id_list = [i['instance_id'] for i in search_ip_data]
            if instance_id_list:
                params['WHERE_AND']['in']['id'] = tuple(instance_id_list)


        host_ip = json_search.get('host_ip')
        if host_ip:
            params['search_in_flag'] = 1
            # 先模糊查询host IP对应的实例ID
            search_ip_data = ins_s.get_instances_by_fuzzy_host_ip(host_ip)
            instance_id_list = [i['instance_id'] for i in search_ip_data]
            if instance_id_list:
                params['WHERE_AND']['in']['id'] = tuple(instance_id_list)

        status = json_search.get('status')
        if status:
            params['WHERE_AND']['=']['status'] = status

        owner = json_search.get('owner')
        if owner:
            params['WHERE_AND']['like']['owner'] = '%' + owner + '%'

        group_name = json_search.get('group_name')
        if group_name:
            params['search_in_flag'] = 1
            # 先模糊查询应用组对应的实例ID
            search_group_data = ins_s.get_instances_by_fuzzy_group_name(group_name)
            instance_id_list = [i['instance_id'] for i in search_group_data]
            if instance_id_list:
                params['WHERE_AND']['in']['id'] = tuple(instance_id_list)

    # 系统管理员能看到其组所在区域的所有VM
    role_ids = current_user_role_ids()
    # 系统管理员
    if 1 in role_ids:
        is_admin = True
    else:
        is_admin = False

    total_nums, data = instance.user_instance_list(get_user()['user_id'], is_admin,ip_search_type, **params)

    # 生成excel
    excel_data = OrderedDict()
    sheet_1 = []
    # 标题行
    row_title_data = [u"主机名", u"IP地址", u"HOST IP", u"状态", u"应用管理员", u"所属应用组", u"应用系统信息",
                      u"所属集群", u"机房类型"]
    sheet_1.append(row_title_data)
    if ip_search_type:
        data = list(data)
        data.sort(lambda x, y: cmp(''.join([i.rjust(3, '0') for i in x['ip_address'].split('.')]),
                                           ''.join([i.rjust(3, '0') for i in y['ip_address'].split('.')])))
    for i in data:
        _instance_group = ins_s.get_group_of_instance(i['id'])
        if _instance_group:
            _instance_group_name = _instance_group['name']
        else:
            _instance_group_name = None

        _row_data = [
            i['instance_name'],
            i['ip_address'],
            i['host_ip'],
            unicode(VMStatusMsg.MSG_DICT.get(i['status'], '')),
            i['owner'],
            _instance_group_name,
            i['app_info'],
            i['hostpool_name'],
            unicode(DataCenterTypeMsg.MSG_DICT.get(int(i['dc_type']), '')),
        ]
        sheet_1.append(_row_data)

    excel_data.update({u"instances": sheet_1})

    io = StringIO.StringIO()
    save_data(io, excel_data)

    response = make_response(io.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=虚拟机信息.xls"
    return response