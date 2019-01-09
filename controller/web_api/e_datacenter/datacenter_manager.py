# coding=utf8
'''
    机房管理
'''


from flask import request
from model.const_define import ErrorCode, OperationObject, OperationAction
from service.s_datacenter import datacenter_service as dc_s
from service.s_net_area import net_area as net_area_s
from service.s_increment import increment_service as incre_s
import logging
import json_helper
from helper.time_helper import get_datetime_str
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
from service.s_operation.operation_service import add_operation_datacenter


@login_required
@add_operation_datacenter(OperationObject.DATACENTER, OperationAction.ADD)
def datacenter_add(area_id):
    name = request.values.get('name')
    address = request.values.get('address')
    description = request.values.get('description')
    dc_type = request.values.get('dc_type')
    province = request.values.get('province')

    if not area_id or not name or not dc_type or not province:
        logging.info('the params is invalid when add datacenter')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    # 同类型的机房不能同名
    name_exist = dc_s.DataCenterService().check_dc_name_exist_in_same_type(name, dc_type)
    if name_exist:
        logging.error('name %s in type %s is duplicated when add datacenter', name, dc_type)
        return json_helper.format_api_resp(code=ErrorCode.DUPLICATED_ERR,
                                           msg="同环境类型下机房名不能重复，请修改机房名")

    insert_data = {
        'area_id': area_id,
        'name': name,
        'displayname': name,
        'dc_type': dc_type,
        'province': province,
        'address': address,
        'description': description,
        'isdeleted': '0',
        'created_at': get_datetime_str()
    }
    ret = dc_s.DataCenterService().add_datacenter(insert_data)
    if ret.get('row_num') <= 0:
        logging.error("add datacenter error, insert_data:%s", str(insert_data))
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


@login_required
def allocate_dc_2_area(datacenter_id, area_id):
    '''
        分配机房给区域
    :param datacenter_id:
    :param area_id:
    :return:
    '''
    if not datacenter_id or not area_id:
        logging.info('no datacenter_id or area_id when allocate datacenter to area')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    update_data = {
        'area_id': area_id,
    }
    where_data = {
        'datacenter_id': datacenter_id,
    }
    ret = dc_s.DataCenterService().update_datacenter_info(update_data, where_data)
    if ret.get('row_num') <= 0:
        logging.error("allocate datacenter to area error, update_data:%s, where_data:%s",
                      str(update_data), str(where_data))
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


@login_required
@add_operation_datacenter(OperationObject.DATACENTER, OperationAction.DELETE)
def datacenter_delete():
    datacenter_ids = request.values.get('datacenter_ids')
    if not datacenter_ids:
        logging.error('no datacenter_ids when delete datacenter')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    datacenter_ids_list = datacenter_ids.split(',')
    # 操作的datacenter数
    all_num = len(datacenter_ids_list)
    msg = None
    fail_num = 0
    for _id in datacenter_ids_list:
        _net_area_nums = net_area_s.NetAreaService().get_net_area_nums_in_dc(_id)
        if _net_area_nums > 0:
            logging.error('no allow to delete datacenter %s that has net area', _id)
            fail_num += 1
            # 单台操作且已失败则直接跳出循环
            if all_num == 1:
                msg = '该机房下已分配有网络区域，不允许删除'
                break
            continue

        _ret = dc_s.DataCenterService().delete_datacenter(_id)
        if _ret <= 0:
            logging.error('db delete datacenter %s fail when delete datacenter', _id)
            fail_num += 1
            continue

        _dc_info = dc_s.DataCenterService().get_datacenter_info(_id)
        if not _dc_info:
            logging.error('datacenter info %s is not exist in db when delete datacenter', _id)
            fail_num += 1
            continue

        # 把该机房的主机名增量值清空
        incre_s.clean_dc_increment_value(_dc_info['name'])

    # 全失败
    if fail_num == all_num:
        logging.error("delete datacenter all failed")
        if msg:
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=msg)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    # 部分成功
    if 0 < fail_num < all_num:
        logging.error("delete all %s datacenter part %s failed", all_num, fail_num)
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS_PART, msg="部分机房删除成功")
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


@login_required
@add_operation_datacenter(OperationObject.DATACENTER, OperationAction.ALTER)
def datacenter_update(datacenter_id):
    name = request.values.get('name')
    province = request.values.get('province')
    address = request.values.get('address')
    description = request.values.get('description')

    if not datacenter_id or not name or not province:
        logging.error('the params is invalid when update datacenter')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    dc_data = dc_s.DataCenterService().get_datacenter_info(datacenter_id)
    if not dc_data:
        logging.error('the datacenter %s is no exist in db when update datacenter', datacenter_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    if dc_data['name'] != name:
        # 同类型的机房不能同名
        name_exist = dc_s.DataCenterService().check_dc_name_exist_in_same_type(name, dc_data['dc_type'])
        if name_exist:
            logging.error('name %s in type %s is duplicated when update datacenter', name, dc_data['dc_type'])
            return json_helper.format_api_resp(code=ErrorCode.DUPLICATED_ERR,
                                               msg="同环境类型下机房名不能重复，请修改机房名")

    update_data = {
        'name': name,
        'displayname': name,
        'province': province,
        'address': address,
        'description': description,
        'updated_at': get_datetime_str()
    }
    where_data = {
        'id': datacenter_id,
    }
    ret = dc_s.DataCenterService().update_datacenter_info(update_data, where_data)
    if ret < 0:
        logging.error("update datacenter error, update_data:%s, where_data:%s", str(update_data), str(where_data))
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)
