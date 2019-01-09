# coding=utf8
'''
    新开发的镜像管理
'''
# __author__ =  ""

from flask import request
from model.const_define import ErrorCode
import json_helper
from service.s_image import image_service
from common_data_struct import base_define, image_manage_info



class ImageListResp(base_define.Base):

    def __init__(self):
        self.total = None
        self.rows = []



def image_manage_list():
    params = {
        'ORDER': [
            ['id', 'desc'],
        ],
        'PAGINATION': {
            'page_size': request.values.get('page_size', 20),
            'page_no': request.values.get('page_no', 1),
        }
    }

    total_nums, data = image_service.ImageManageService().query_data(**params)
    resp = ImageListResp()
    resp.total = total_nums
    for i in data:
        _image_info = image_manage_info.ImageManagerInfo().init_from_db(i)
        resp.rows.append(_image_info)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp.to_json())