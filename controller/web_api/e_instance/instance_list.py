# coding=utf8
'''
    虚拟机管理 - 列表
'''
# __author__ =  ""

from flask import request
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
import json_helper
from common_data_struct import instance_info, base_define
from model.const_define import ErrorCode
from service.s_instance import instance_service as ins_s
from model import instance
from service.s_user.user_service import get_user, current_user_role_ids
import json
import  logging

class InstanceListResp(base_define.Base):

    def __init__(self):
        self.total = None
        self.rows = []


@login_required
def instance_list():
    '''
        获取虚机列表
    :return:
    '''
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
    logging.info('-------------------------------1')
    ip_search_type = ""
    search = request.values.get('search')
    if search:
        json_search = json.loads(search)
        name = json_search.get('name')
        if name:
            params['WHERE_AND']['like']['name'] = '%' + name + '%'

        uuid = json_search.get('uuid')
        if uuid:
            params['WHERE_AND']['like']['uuid'] = '%' + uuid + '%'

        instance_id_list_all = []
        ip_address = json_search.get('ip_address')
        if ip_address:
            ip_search_type = json_search.get("ip_search_type")
            params['search_in_flag'] = 1
            # 先模糊查询IP地址对应的实例ID
            search_ip_data = ins_s.get_instances_by_fuzzy_ip(ip_address,ip_search_type)
            instance_id_list = [i['instance_id'] for i in search_ip_data]
            instance_id_list_all.append(instance_id_list)
            # if instance_id_list:
            #     params['WHERE_AND']['in']['id'] = tuple(instance_id_list)


        host_ip = json_search.get('host_ip')
        if host_ip:
            params['search_in_flag'] = 1
            # 先模糊查询host IP对应的实例ID
            search_ip_data = ins_s.get_instances_by_fuzzy_host_ip(host_ip)
            instance_id_list = [i['instance_id'] for i in search_ip_data]
            instance_id_list_all.append(instance_id_list)
            # if instance_id_list:
            #     params['WHERE_AND']['in']['id'] = tuple(instance_id_list)

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
            instance_id_list_all.append(instance_id_list)
            # if instance_id_list:
            #     params['WHERE_AND']['in']['id'] = tuple(instance_id_list)

        # 新增关联表查询是需要编写以下逻辑
        if instance_id_list_all:
            if len(instance_id_list_all) == 1:
                params['WHERE_AND']['in']['id'] = tuple(instance_id_list_all[0])
            if len(instance_id_list_all) == 2:
                params['WHERE_AND']['in']['id'] = tuple(list(set(instance_id_list_all[0]).
                                                             intersection(set(instance_id_list_all[1]))))
            if len(instance_id_list_all) == 3:
                r1 = list(set(instance_id_list_all[0]).intersection(set(instance_id_list_all[1])))
                r2 = list(set(r1).intersection(set(instance_id_list_all[2])))
                params['WHERE_AND']['in']['id'] = tuple(r2)

    logging.info('-------------------------------2')
    # 系统管理员能看到其组所在区域的所有VM
    role_ids = current_user_role_ids()
    # 系统管理员
    if 1 in role_ids:
        is_admin = True
    else:
        is_admin = False
    logging.info('-------------------------------3{}'.format(get_user()['user_id']))


    total_nums, data = instance.user_instance_list(get_user()['user_id'], is_admin,ip_search_type, **params)
    logging.info('-------------------------------77{}'.format(total_nums))
    resp = InstanceListResp()
    resp.total = total_nums
    logging.info('-------------------------------4')
    for i in data:
        _instance_info = instance_info.InstanceInfo().user_instance(i)
        _instance_group = ins_s.get_group_of_instance(i['id'])
        if _instance_group:
            _instance_info.app_group = _instance_group['name']
            _instance_info.app_group_id = _instance_group['group_id']

        resp.rows.append(_instance_info)
    resp = resp.to_json()
    logging.info('-------------------------------5{}'.format(resp))
    if ip_search_type:
        resp["rows"].sort(lambda x, y: cmp(''.join([i.rjust(3, '0') for i in x['ip_address'].split('.')]),
                                  ''.join([i.rjust(3, '0') for i in y['ip_address'].split('.')])))
        if params.get('page_no') and params.get('page_size'):
            page_no = int(params['page_no'])
            page_size = int(params['page_size'])
            resp["rows"] = resp["rows"][(page_no - 1) * page_size: page_no * page_size]
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp)
