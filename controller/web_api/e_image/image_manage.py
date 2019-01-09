# coding=utf8
'''
    镜像管理
'''


from flask import request
import logging
from model.const_define import ErrorCode
import json_helper
from service.s_image import image_service
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
from helper.time_helper import get_datetime_str


@login_required
def add_image():
    name = request.values.get('name')
    displayname = request.values.get('displayname')
    system = request.values.get('system')
    description = request.values.get('description')
    version = request.values.get('version')
    url = request.values.get('url')
    md5 = request.values.get('md5')
    format = request.values.get('format')
    actual_size_mb = request.values.get('actual_size_mb')
    size_gb = request.values.get('size_gb')
    type = request.values.get('type')



    if not name or not system or not url or not md5 or not format or not actual_size_mb or not size_gb or not type:
        logging.info('入参缺失')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR,msg = '入参缺失')

    # url唯一
    image_db = image_service.ImageService().get_image_by_url(url)
    is_image = image_db[1]
    if is_image:
        logging.info('image url %s is duplicated when add image', url)
        return json_helper.format_api_resp(code=ErrorCode.DUPLICATED_ERR, msg="镜像路径不能重复")

    # 系统盘唯一判断
    if type == '0':
        image_res = image_service.ImageService().image_sys_disk_confirm(name)[1]
        if image_res:
            logging.info('image sys disk is unique can not add more')
            return json_helper.format_api_resp(code=ErrorCode.DUPLICATED_ERR, msg="镜像系统盘唯一无法再添加")

    insert_data = {
        'name': name,
        'displayname': displayname,
        'system': system,
        'version': version,
        'description': description,
        'md5': md5,
        'format': format,
        'actual_size_mb': actual_size_mb,
        'size_gb': size_gb,
        'isdeleted': '0',
        'created_at': get_datetime_str(),
        'url': url,
        'type': type,
    }
    ret = image_service.ImageService().add_image_info(insert_data)
    if ret.get('row_num') <= 0:
        logging.error("add image error, insert_data:%s", str(insert_data))
        error_msg = "添加新镜像 %s 失败",str(insert_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR,msg = error_msg)

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


@login_required
def edit_image():
    '''
    镜像信息修改
    :return:
    '''
    actual_size_mb = request.values.get('actual_size_mb')
    size_gb = request.values.get('size_gb')
    md5 = request.values.get('md5')
    image_id = request.values.get('image_id')

    if not actual_size_mb or not size_gb or not md5 or not image_id:
        logging.info('入参缺失')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR,msg = '入参缺失')

    # 入参合法性判断
    actual_size = float(actual_size_mb)
    size_total = float(size_gb)*1024
    if actual_size > size_total :
        error_msg = '镜像实际大小大于镜像总大小'
        logging.info(error_msg)
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg=error_msg)
    elif actual_size <= 0:
        error_msg = '镜像实际大小小于等于0'
        logging.info(error_msg)
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg=error_msg)
    #入参合法,更新DB
    else:
        update_res = _update_image_info(actual_size_mb,size_gb,md5,image_id)
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS, msg='镜像信息更新成功')


def _update_image_info(actual_size_mb,size_gb,md5,image_id):
    update_data = {
        'actual_size_mb': actual_size_mb,
        'size_gb': size_gb,
        'md5': md5
    }
    where_data = {
        'id': image_id
    }
    return image_service.ImageService().update_image_info(update_data,where_data)
