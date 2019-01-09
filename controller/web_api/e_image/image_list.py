# coding=utf8
'''
    镜像管理
'''


from flask import request
from model.const_define import ErrorCode
import json_helper
from service.s_image import image_service
from common_data_struct import base_define, image_info
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user


class ImageListResp(base_define.Base):

    def __init__(self):
        self.total = None
        self.rows = []


@login_required
def image_list():
    params = {
        'WHERE_AND': {
            '=': {
                'isdeleted': '0',
            },
        },
        'ORDER': [
            ['id', 'desc'],
        ],
        'PAGINATION': {
            'page_size': request.values.get('page_size', 20),
            'page_no': request.values.get('page_no', 1),
        }
    }

    total_nums, data = image_service.ImageService().query_data(**params)
    resp = ImageListResp()
    resp.total = total_nums
    for i in data:
        _image_info = image_info.ImageInfo().init_from_db(i)
        resp.rows.append(_image_info)

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp.to_json())