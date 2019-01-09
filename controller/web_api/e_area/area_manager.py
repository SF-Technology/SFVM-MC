# coding=utf8
'''
    区域管理
'''
# __author__ =  ""

from flask import request
from model.const_define import ErrorCode, OperationObject, OperationAction
from service.s_area import area_service as area_s
from service.s_datacenter import datacenter_service as dc_s
from service.s_access import access_service as access_s
from service.s_user.user_service import current_user_all_area_ids
import logging
import json_helper
from service.s_user import user_service
from helper.time_helper import get_datetime_str
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
from service.s_operation.operation_service import add_operation_area


@login_required
@add_operation_area(OperationObject.AREA, OperationAction.ADD)
def area_add():
    name = request.values.get('name')
    manager = request.values.get('manager')
    parent_id = request.values.get('parent_id')

    if not name or not parent_id:
        logging.info('no name or parent_id when add area')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    is_exist = user_service.UserService().query_user_info('userid', manager)
    if not is_exist:
        logging.error("no such manager %s exist when add area", manager)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="对不起，你输入的管理员ID不存在")

    # 区域名不能重复
    name_exist = area_s.AreaService().check_area_name_exist(name)
    if name_exist:
        logging.error('name %s is duplicated when add area', name)
        return json_helper.format_api_resp(code=ErrorCode.DUPLICATED_ERR, msg="区域名不能重复，请修改区域名")

    insert_data = {
        'name': name,
        'displayname': name,
        'parent_id': parent_id,
        'manager': manager,
        'area_type': '1',
        'isdeleted': '0',
        'created_at': get_datetime_str()
    }
    ret = area_s.AreaService().add_area(insert_data)
    if ret.get('row_num') <= 0:
        logging.error("add area error, insert_data:%s", str(insert_data))
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


@login_required
@add_operation_area(OperationObject.AREA, OperationAction.ALTER)
def area_update(area_id):
    name = request.values.get('name')
    manager = request.values.get('manager')
    if not area_id or not name or not manager:
        logging.info('no area_id or name or manager when update area')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    is_exist = user_service.UserService().query_user_info('userid', manager)
    if not is_exist:
        logging.error("no such manager %s exist when update area", manager)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="对不起，你输入的管理员ID不存在")

    # 区域名不能重复
    old_area = area_s.AreaService().get_area_info(area_id)
    if not old_area:
        logging.error('area %s is not exist in db when update area', area_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    if old_area['name'] != name:
        name_exist = area_s.AreaService().check_area_name_exist(name)
        if name_exist:
            logging.error('name %s is duplicated when update area', name)
            return json_helper.format_api_resp(code=ErrorCode.DUPLICATED_ERR, msg="区域名不能重复，请修改区域名")

    update_data = {
        'name': name,
        'displayname': name,
        'manager': manager,
        'updated_at': get_datetime_str()
    }
    where_data = {
        'id': area_id,
    }
    ret = area_s.AreaService().update_area_info(update_data, where_data)
    if ret < 0:
        logging.error("update area error, update_data:%s, where_data:%s", str(update_data), str(where_data))
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


@login_required
def add_child_area(parent_area_id, child_area_id):
    if not parent_area_id or not child_area_id:
        logging.info('no parent_area_id or child_area_id when add child area')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    update_data = {
        'parent_id': parent_area_id,
    }
    where_data = {
        'id': child_area_id,
    }
    ret = area_s.AreaService().update_area_info(update_data, where_data)
    if ret.get('row_num') <= 0:
        logging.error("add child area error, update_data:%s, where_data:%s", str(update_data), str(where_data))
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


@login_required
def get_child_areas(area_id):
    if not area_id:
        logging.info('no area_id when get child areas')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    child_nums, child_data = area_s.AreaService().get_child_areas(area_id)
    child_list = []
    for i in child_data:
        if i["id"] not in current_user_all_area_ids():
            continue

        _child = {
            "child_id": i["id"],
            "child_name": i["displayname"],
            "datacenter_nums": dc_s.DataCenterService().get_datacenter_nums_in_area(i['id']),
            "manager": i['manager']
        }
        child_list.append(_child)

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=child_list)


@login_required
def get_parent_areas():
    '''
        获取所有适合做父区域的数据
    :return:
    '''

    parent_list = []
    user_areas_list = current_user_all_area_ids()
    if not user_areas_list:
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=parent_list)

    parent_nums, parent_datas = area_s.AreaService().get_available_parents(user_areas_list)
    for i in parent_datas:
        # 没有子区域但有机房的区域不能作为父区域
        _dc_nums = dc_s.DataCenterService().get_datacenter_nums_in_area(i['id'])
        _child_nums = area_s.AreaService().get_child_areas_nums(i['id'])
        if _child_nums < 1 and _dc_nums > 0:
            continue

        _parent = {
            "parent_id": i["id"],
            "parent_name": i["displayname"],
        }
        parent_list.append(_parent)

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=parent_list)


@login_required
@add_operation_area(OperationObject.AREA, OperationAction.DELETE)
def area_delete():
    area_ids = request.values.get('area_ids')
    if not area_ids:
        logging.error('no area_ids when delete area')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    area_ids_list = area_ids.split(',')
    # 操作的area数
    all_num = len(area_ids_list)
    msg = None
    fail_num = 0
    for _id in area_ids_list:
        # 有子区域、机房、组关联的都不能删除
        _child_nums = area_s.AreaService().get_child_areas_nums(_id)
        if _child_nums > 0:
            logging.error('no allow to delete area %s that has child area', _id)
            fail_num += 1
            # 单台操作且已失败则直接跳出循环
            if all_num == 1:
                msg = '该区域下有子区域，不允许删除'
                break
            continue
        else:
            _dc_nums = dc_s.DataCenterService().get_datacenter_nums_in_area(_id)
            if _dc_nums > 0:
                logging.error('no allow to delete area %s that has datacenter', _id)
                fail_num += 1
                # 单台操作且已失败则直接跳出循环
                if all_num == 1:
                    msg = '该区域下已分配有机房，不允许删除'
                    break
                continue

        _ret = area_s.AreaService().delete_area(_id)
        if _ret <= 0:
            logging.error('db delete area %s fail when delete area', _id)
            fail_num += 1
            continue

        _ret_a = access_s.delete_access_info_by_area_id(_id)
        if _ret_a <= 0:
            logging.error('db delete area %s access info when delete area', _id)
            fail_num += 1
            continue

    # 全失败
    if fail_num == all_num:
        logging.error("delete area all failed")
        if msg:
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=msg)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    # 部分成功
    if 0 < fail_num < all_num:
        logging.error("delete all area %s part %s failed", all_num, fail_num)
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS_PART, msg="部分区域删除成功")
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)