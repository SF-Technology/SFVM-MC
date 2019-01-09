# coding=utf8
'''
    虚拟机管理
'''
# __author__ =  ""

import logging
import os
from collections import OrderedDict
import StringIO

from collect_data.base import Global_define
from helper import json_helper
from flask import make_response
from pyexcel_xls import save_data, get_data
from helper.time_helper import get_datetime_str, get_datetime_now
from model.const_define import ErrorCode, VMCreateSource, OperationObject, OperationAction, DataCenterType
from service.s_instance import instance_service
from service.s_instance import instance_service as ins_s, instance_action_service as ins_a_s
from service.v2v_task import v2v_instance_info as v2v_i_i_s
from service.s_user.user_service import current_user_role_ids, get_user
from config.default import INSTANCE_MAX_DELETE
from flask import request
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
from service.s_operation.operation_service import add_operation_vm, add_operation_del_excel_vm


@login_required
def instance_flavor(instance_id):
    '''
        获取虚机flavor
    :param instance_id:
    :return:
    '''
    if not instance_id:
        logging.info('no instance_id when get flavor')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    flavor_data = ins_s.get_flavor_of_instance(instance_id)

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=flavor_data)


@login_required
@add_operation_vm(OperationObject.VM, OperationAction.DELETE)
def instance_delete():
    '''
        虚机删除
        关机超过一天才能删除
    :return:
    '''
    request_from_vishnu = False
    if get_user()['user_id'] == 'vishnu':
        is_admin = True
        request_from_vishnu = True
    else:
        # 判断操作用户身份
        role_ids = current_user_role_ids()
        # 系统管理员
        if 1 in role_ids:
            is_admin = True
        else:
            is_admin = False

    permission_limited = False

    ins_ids = request.values.get('instance_ids')
    if not ins_ids:
        logging.info('no instance_ids when delete instance')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    ins_ids_list = ins_ids.split(',')
    # 操作的instance数
    all_num = len(ins_ids_list)
    if all_num > int(INSTANCE_MAX_DELETE):
        logging.info('delete nums %s is greater than max %s', all_num, INSTANCE_MAX_DELETE)
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    fail_num = 0
    for _ins_id in ins_ids_list:
        # 查询虚拟机对应环境信息，应用管理员不能删除非DEV环境虚拟机
        ins_group = ins_s.get_group_of_instance(_ins_id)
        if not ins_group:
            logging.error('instance %s group data is no exist in db when delete instance', str(_ins_id))
            fail_num += 1
            continue
        else:
            if not is_admin and int(ins_group['dc_type']) != DataCenterType.DEV:
                permission_limited = True
                fail_num += 1
                continue
        _ins_data = ins_s.InstanceService().get_instance_info(_ins_id)
        if _ins_data:
            # 维石只能删除克隆备份的虚拟机
            if request_from_vishnu and 'clone' not in _ins_data['name']:
                fail_num += 1
                continue
            _ret_del = ins_a_s.delete_instance(_ins_data, _ins_data['status'])
            if not _ret_del:
                fail_num += 1
                continue
        else:
            logging.error('the instance is not exist in db when delete instance')
            fail_num += 1
            continue

    # 全失败
    if fail_num == all_num:
        logging.error("delete instance all failed")
        if permission_limited:
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="非DEV环境虚拟机请联系系统组删除")
        elif request_from_vishnu:
            return json_helper.format_api_resp(code=ErrorCode.SUCCESS)
        else:
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    # 部分成功
    if 0 < fail_num < all_num:
        logging.error("delete instance part failed")
        if permission_limited:
            return json_helper.format_api_resp(code=ErrorCode.SUCCESS_PART, msg="部分虚拟机删除成功, 非DEV环境虚拟机请联系系统组删除")
        elif request_from_vishnu:
            return json_helper.format_api_resp(code=ErrorCode.SUCCESS)
        else:
            return json_helper.format_api_resp(code=ErrorCode.SUCCESS_PART, msg="部分虚拟机删除成功")
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


@login_required
def instance_detail(instance_id):
    '''
        获取虚机详情
    :param instance_id:
    :return:
    '''
    if not instance_id:
        logging.info('no instance_id when get instance detail')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    ins_data = ins_s.InstanceService().get_instance_info(instance_id)
    if not ins_data:
        logging.error('instance %s info is no exist in db when get instance detail', instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    # VM创建来源
    create_source = ins_data['create_source']

    ins_flavor = ins_s.get_flavor_of_instance(instance_id)
    if not ins_flavor:
        logging.error('instance %s flavor info is no exist in db when get instance detail', instance_id)
        cpu = None
        memory_mb = None
        root_disk_gb = None
    else:
        cpu = ins_flavor['vcpu']
        memory_mb = ins_flavor['memory_mb']
        root_disk_gb = ins_flavor['root_disk_gb']

    system = None
    sys_version = None
    image_name = None
    # 本平台
    if create_source == VMCreateSource.CLOUD_SOURCE:
        ins_images = ins_s.get_images_of_instance(instance_id)
        if not ins_images:
            logging.error('instance %s image info is no exist in db when get instance detail', instance_id)
        else:
            system = ins_images[0]['system']
            sys_version = ins_images[0]['version']
            image_name = ins_images[0]['displayname']
    elif create_source == VMCreateSource.OPENSTACK or create_source == VMCreateSource.ESX:
        # v2v迁移的VM
        ins_v2v_data = v2v_i_i_s.v2vInstanceinfo().get_v2v_instance_info_by_instance_id(instance_id)
        if ins_v2v_data:
            system = ins_v2v_data['os_type']
            sys_version = ins_v2v_data['os_version']

    ins_group = ins_s.get_group_of_instance(instance_id)
    if not ins_group:
        logging.error('instance %s group info is no exist in db when get instance detail', instance_id)
        group_name = None
    else:
        group_name = ins_group['name']

    ins_ip = ins_s.get_ip_of_instance(instance_id)
    if not ins_ip:
        logging.error('instance %s ip info is no exist in db when get instance detail', instance_id)
        ip_address = None
    else:
        ip_address = ins_ip['ip_address']

    ins_netarea = ins_s.get_netarea_of_instance(instance_id)
    if not ins_netarea:
        logging.error('instance %s net area info is no exist in db when get instance detail', instance_id)
        net_area = None
    else:
        net_area = ins_netarea['name']

    ins_disks = ins_s.get_disks_of_instance(instance_id)
    if not ins_disks:
        logging.error('instance %s disks info is no exist in db when get instance detail', instance_id)
        disk_gb = None
    else:
        # disk_gb = ins_disks[0]['size_gb']
        disk_gb = sum([int(i['size_gb']) for i in ins_disks])

    ins_datacenter = ins_s.get_datacenter_of_instance(instance_id)
    if not ins_datacenter:
        logging.error('instance %s datacenter info is no exist in db when get instance detail', instance_id)
        dc_type = None
    else:
        dc_type = ins_datacenter['dc_type']

    data = {
        'instance_name': ins_data['name'],
        'uuid': ins_data['uuid'],
        'ip_address': ip_address,
        'dc_type': dc_type,
        'net_area': net_area,
        'system': system,
        'sys_version': sys_version,
        'image_name': image_name,
        'cpu': cpu,
        'memory_mb': memory_mb,
        'root_disk_gb': root_disk_gb,
        'disk_gb': disk_gb,
        'app_info': ins_data['app_info'],
        'owner': ins_data['owner'],
        'group_name': group_name,
        'create_source': create_source
    }
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=data)


@login_required
def instance_recreate():
    '''
        重新创建虚拟机
    :return:
    '''
    instance_id = request.values.get('instance_id')
    if not instance_id:
        logging.info('no instance_id when recreate instance')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    ins_data = ins_s.InstanceService().get_instance_info(instance_id)
    if not ins_data:
        logging.error('no instance %s info when recreate instance', instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


@login_required
def instance_os_version_modify(instance_id):
    '''
        修改os版本为unknown的虚拟机
    :param instance_id:
    :json param :
    :return:
    '''
    req_json = request.data
    req_data = json_helper.loads(req_json)
    n_os_version = req_data["os_version"]

    if not instance_id or not str(n_os_version):
        logging.info('no instance_id or os_version when modify instance os version')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    ins_data = ins_s.InstanceService().get_instance_info(instance_id)
    if not ins_data:
        logging.error('instance %s info is no exist in db when modify instance os version', instance_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    # VM创建来源
    create_source = ins_data['create_source']

    # 本平台
    if create_source == VMCreateSource.OPENSTACK or create_source == VMCreateSource.ESX:
        # v2v迁移的VM
        ins_v2v_data = v2v_i_i_s.v2vInstanceinfo().get_v2v_instance_info_by_instance_id(instance_id)
        if ins_v2v_data:
            if ins_v2v_data['os_version'] and ins_v2v_data['os_version'] == "unknown":
                # 更新v2v虚拟机os版本
                update_data = {
                    'os_version': n_os_version
                }
                where_data = {
                    'instance_id': instance_id
                }
                v2v_i_i_s.v2vInstanceinfo().update_v2v_status(update_data, where_data)
    else:
        # todo: kvm2.0需要增加对平台自身创建虚拟机操作系统版本校验，unknown的可以修改
        pass

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, msg="操作系统版本更新成功")


@login_required
def instance_excel_del_template():
    '''虚拟机批量删除模板'''
    # 系统管理员能看到其组所在区域的所有VM
    role_ids = current_user_role_ids()
    # 系统管理员
    if 1 not in  role_ids:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="当前用户权限不足，请联系系统组管理员")
    sheet = []
    excel_data = OrderedDict()
    name = " del_instance_template "
    title_data = [u"待删除虚拟机ip地址"]
    sheet.append(title_data)
    for i in [u'10.10.10.10',u'12.12.12.12']:
        sheet.append([i])
    excel_data.update({name: sheet})
    io = StringIO.StringIO()
    save_data(io, excel_data)
    response = make_response(io.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename={}.xls".format(name)
    response.headers["page-type"] = "download"
    return response


@login_required
@add_operation_del_excel_vm(OperationObject.VM, OperationAction.DELETE)
def upload_del_instance_excel():
    '''导入批量删除的虚拟机ip，虚拟机需关机一个月无任何操作'''
    g = Global_define()
    g.init()
    g.set_value('vm_list',[])
    # 系统管理员能看到其组所在区域的所有VM
    role_ids = current_user_role_ids()
    # 系统管理员
    if 1 not in role_ids:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="当前用户权限不足，请联系系统组管理员")
    if not request.files:
        return json_helper.format_api_resp(ErrorCode.PARAM_ERR, msg="请求入参缺失")
    f = request.files['file']

    file_name, file_suffix = os.path.splitext(f.filename)
    if file_suffix != '.xls' and file_suffix != '.xlsx':
        return json_helper.format_api_resp(code=ErrorCode.ALL_FAIL, msg="导入规则的文件格式必须为excel格式")

    xls_data = get_data(f)
    xls_noempty_data = 0
    all_data_list = []
    for sheet_n in xls_data.keys():
        # 只处理一个sheet数据
        if xls_data[sheet_n]:
            all_data_list = xls_data[sheet_n]
            xls_noempty_data += 1
            break
    if xls_noempty_data == 0:
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="不能上传空excel文件")

    if len(all_data_list) < 2:
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="请填写需删除虚拟机IP后再提交该excel文件")
    err_data = []
    ins_data_list = []
    ip_data_list = []
    now_time = get_datetime_now()
    for i,rows in enumerate(all_data_list):
        # 默认第一行为标题，跳过
        if i != 0:
            ret_ins = instance_service.get_instance_info_by_ip(rows[0])
            if ret_ins:
                shut_down_time = ret_ins['shut_down_time']
                if (now_time-shut_down_time).days >=30:
                    ins_data_list.append(ret_ins)
                    ip_data_list.append(rows[0])
                    continue
                else:
                    err_data.append(rows[0])
            else:
                err_data.append(rows[0])
    if err_data:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="以下的虚拟机ip不符合条件，请检测ip是否存在或关机无操作30天：{}".format(err_data))

    g.set_value("vm_list",ip_data_list)
    fail_num = 0
    all_num = len(ins_data_list)
    for _ins_data in ins_data_list:
        _ret_del = ins_a_s.delete_instance(_ins_data, _ins_data['status'])
        if not _ret_del:
            fail_num += 1
            continue
    # 全失败
    if fail_num == all_num:
        logging.error("delete instance all failed")
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="导入excel删除虚拟机全部失败")
    # 部分成功
    if 0 < fail_num < all_num:
        logging.error("delete instance part failed")
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS_PART, msg="导入excel删除虚拟机部分失败")
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, msg="全部删除成功")