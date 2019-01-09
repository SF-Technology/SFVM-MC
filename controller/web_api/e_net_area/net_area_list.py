# coding=utf8
'''
    net_area相关
'''
# __author__ =  ""

from flask import request
import traceback
from model.const_define import ErrorCode
from service.s_net_area import net_area
from service.s_net_area import net_area
from service.s_imagecache import imagecache_service as imca_s
import logging
import json_helper
from common_data_struct import base_define, net_area_info
from model import net_area
from service.s_user.user_service import get_user
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user


class NetAreaListResp(base_define.Base):

    def __init__(self):
        self.total = None
        self.rows = []


@login_required
def net_area_list():
    '''
    :return: 这个接口返回3个字段，网络区域的名称，网络区域所属的机房名称，网络区域下所有的集群数量
    '''
    kwargs = {
        'page_size': request.values.get('page_size', 20),
        'page_no': request.values.get('page_no', 1),
    }
    total_nums, data = net_area.user_net_area_list(get_user()['user_id'], **kwargs)
    resp = NetAreaListResp()
    resp.total = total_nums
    for i in data:
        _net_area_info = net_area_info.NetAreaInfo().net_area_info(i)
        dict = classToDict(_net_area_info)
        net_area_id = i['net_area_id']
        res,imagecache_list = imca_s.get_imagecache_list_by_net_area_id(net_area_id)
        if res:
            dict["imagecache_list"] = imagecache_list
        else:
            dict["imagecache_list"] = "获取失败"
        resp.rows.append(dict)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp.to_json())

def classToDict(obj):
    is_list = obj.__class__ == [].__class__
    is_set = obj.__class__ == set().__class__

    if is_list or is_set:
        obj_arr = []
        for o in obj:
            dict = {}
            dict.update(o.__dict__)
            obj_arr.append(dict)
        return obj_arr
    else:
        dict = {}
        dict.update(obj.__dict__)
        return dict




