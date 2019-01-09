# coding=utf8
'''
    网络区域管理
'''
# __author__ =  ""


from flask import request
from model.const_define import ErrorCode, OperationObject, OperationAction
from service.s_net_area import net_area as net_area_s
from service.s_hostpool import hostpool_service as hostpool_s
from service.s_ip import segment_service as segment_s
from service.s_datacenter import datacenter_service as dc_s
from service.s_imagecache import imagecache_service as imca_s
import logging
import json_helper
from common_data_struct import base_define
from time_helper import get_datetime_str
from service.s_user.user_service import current_user_all_area_ids
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
from service.s_operation.operation_service import add_operation_netarea


class NetAreaListResp(base_define.Base):

    def __init__(self):
        self.total = None
        self.rows = []


@login_required
def net_area_info_init():
    '''
    为前端提供一个创建网络区域的区域--子区域--机房初始列表
    '''
    user_all_area_ids = current_user_all_area_ids()

    ret_init = net_area_s.get_datacenter_area_info()
    if not ret_init:
        return []
    for i in ret_init:
        if user_all_area_ids and i['id'] not in user_all_area_ids:
            del i
            continue

        if i['parent_id'] == -1:
            i['parent_id'] = i['id']
            i['parent_area_name'] = i['area_name']
            del(i['id'], i['area_name'])

    resp = NetAreaListResp()
    for i in ret_init:
        # 只获取当前用户所在区域
        if user_all_area_ids and i['parent_id'] not in user_all_area_ids:
            continue

        resp.rows.append(i)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp.to_json())


@login_required
@add_operation_netarea(OperationObject.NET_AREA, OperationAction.ADD)
def net_area_add():
    datacenter_id = request.values.get('datacenter_id')
    name = request.values.get('name')
    imagecache01 = request.values.get('imagecache01')
    imagecache02 = request.values.get('imagecache02')

    if not name or not datacenter_id or not imagecache01 or not imagecache02:
        logging.info('no area_name or datacenter_id when add net_area')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    dc_data = dc_s.DataCenterService().get_datacenter_info(datacenter_id)
    if not dc_data:
        logging.error('datacenter %s no exist in db when add net_area', datacenter_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    # 同一环境下机房下的网络区域不能重名
    name_exist = net_area_s.check_name_exist_in_same_dc_type(name, dc_data['dc_type'])
    if name_exist:
        logging.error('name %s in dc_type %s is duplicated when add net_area', name, dc_data['dc_type'])
        return json_helper.format_api_resp(code=ErrorCode.DUPLICATED_ERR,
                                           msg='同环境机房下的网络区域名不能重复，请修改网络区域名')

    # 两台imagecache不能重复
    if imagecache01 == imagecache02:
        logging.info('imagecache address duplicated')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="镜像缓存服务器地址重复")

    insert_data = {
        'datacenter_id': datacenter_id,
        'name': name,
        'displayname': name,
        'created_at': get_datetime_str(),
    }
    ret = net_area_s.NetAreaService().add_net_area(insert_data)
    if ret == -1:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)



    net_area_id = ret.get('last_id')
    insert_imagecache01 = {
        "net_area_id": net_area_id,
        "imagecache_ip": imagecache01,
        "create_at": get_datetime_str()
    }
    ret = imca_s.ImageCacheService().add_imagecache_info(insert_imagecache01)
    if ret.get('row_num') <= 0:
        logging.error("add imagecache01 error, insert_data:%s", str(insert_data))
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="新增cache01地址失败")

    insert_imagecache02 = {
        "net_area_id": net_area_id,
        "imagecache_ip": imagecache02,
        "create_at": get_datetime_str()
    }
    ret = imca_s.ImageCacheService().add_imagecache_info(insert_imagecache02)
    if ret.get('row_num') <= 0:
        logging.error("add imagecache02 error, insert_data:%s", str(insert_data))
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="新增cache02地址失败")

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS,msg="新增网络区域成功")


@login_required
@add_operation_netarea(OperationObject.NET_AREA, OperationAction.DELETE)
def net_area_delete():
    net_area_ids = request.values.get('net_area_ids')
    if not net_area_ids:
        logging.error('no net_area_ids when delete net area')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    net_area_ids_list = net_area_ids.split(',')
    # 操作的net area数
    all_num = len(net_area_ids_list)
    msg = None
    fail_num = 0
    for _id in net_area_ids_list:
        # 有集群和网段的都不能删除
        _hostpool_num = hostpool_s.HostPoolService().get_hostpool_nums_in_net_area(_id)
        if _hostpool_num > 0:
            logging.error('no allow to delete net area %s that has hostpool', _id)
            fail_num += 1
            # 单台操作且已失败则直接跳出循环
            if all_num == 1:
                msg = '该网络区域下已分配有集群，不允许删除'
                break
            continue

        _segment_num = segment_s.SegmentService().get_segment_nums_in_net_area(_id)
        if _segment_num > 0:
            logging.error('no allow to delete net area %s that has network segment', _id)
            fail_num += 1
            # 单台操作且已失败则直接跳出循环
            if all_num == 1:
                msg = '该网络区域下已分配有网段，不允许删除'
                break
            continue

        _ret = net_area_s.NetAreaService().delete_net_area(_id)
        if _ret <= 0:
            logging.error('db delete net area %s fail when delete net area', _id)
            fail_num += 1
            continue

    # 全失败
    if fail_num == all_num:
        logging.error("delete net area all failed")
        if msg:
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=msg)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)
    # 部分成功
    if 0 < fail_num < all_num:
        logging.error("delete all %s net area part %s failed", all_num, fail_num)
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS_PART, msg="部分网络区域删除成功")
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


#@login_required
@add_operation_netarea(OperationObject.NET_AREA, OperationAction.ALTER)
def net_area_update(net_area_id):
    name = request.values.get('name')
    imagecache01 = request.values.get('imagecache01')
    imagecache02 = request.values.get('imagecache02')
    if not net_area_id or not name or not imagecache01 or not imagecache02:
        logging.error('the params is invalid when update net area')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR)

    net_area_data = net_area_s.NetAreaService().get_net_area_info(net_area_id)
    if not net_area_data:
        logging.error('net area %s is no exist in db when update net area', net_area_id)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    if net_area_data['name'] != name:
        dc_data = dc_s.DataCenterService().get_datacenter_info(net_area_data['datacenter_id'])
        if not dc_data:
            logging.error('datacenter %s is no exist in db when update net area', net_area_data['datacenter_id'])
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

        # 同一环境下机房下的网络区域不能重名
        name_exist = net_area_s.check_name_exist_in_same_dc_type(name, dc_data['dc_type'])
        if name_exist:
            logging.error('name %s in dc_type %s is duplicated when update net area', name, dc_data['dc_type'])
            return json_helper.format_api_resp(code=ErrorCode.DUPLICATED_ERR,
                                               msg='同环境机房下的网络区域名不能重复，请修改网络区域名')

    # 两台imagecache不能重复
    if imagecache01 == imagecache02:
        logging.info('imagecache address duplicated')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg="镜像缓存服务器地址重复")


    update_data = {
        'name': name,
        'displayname': name,
        'updated_at': get_datetime_str()
    }
    where_data = {
        'id': net_area_id,
    }
    ret = net_area_s.NetAreaService().update_net_area_info(update_data, where_data)
    if ret < 0:
        logging.error("update net area error, update_data:%s, where_data:%s", str(update_data), str(where_data))
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR)

    imagecache_data = imca_s.ImageCacheService().get_imagecache_info_by_net_area_id(net_area_id)
    imagecache01_data = imagecache_data[0]
    imagecache02_data = imagecache_data[1]
    exist_cache_ids = [imagecache01_data['id'],imagecache02_data['id']]
    # update imagecache01
    where_data = {
        "id":exist_cache_ids[0]
    }
    update_data = {
        "imagecache_ip":imagecache01
    }
    ret = imca_s.ImageCacheService().update_imagecache_info(update_data,where_data)
    # update imagecache02
    where_data = {
        "id": exist_cache_ids[1]
    }
    update_data = {
        "imagecache_ip": imagecache02
    }
    ret = imca_s.ImageCacheService().update_imagecache_info(update_data, where_data)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)

