# coding=utf8
'''
    新开发的镜像创建
'''
# __author__ =  ""


import logging
import sys
from config.default import IMAGE_OS_TYPE, IMAGE_OS_VER, IMAGE_EDIT_SERVER
from flask import request
from helper import json_helper
import image_manage_action as im_man_act
from lib.shell import ansibleCmdV2
from lib.vrtManager.util import randomUUID
from helper.time_helper import get_datetime_str
from model.const_define import ErrorCode, IPStatus, IpLockStatus, ImageManage, img_tmp_status, image_ceate_type
from service.s_image import image_service
from service.s_ip import ip_service
from service.s_ip import ip_lock_service as ip_l_s
sys.setdefaultencoding('utf-8')
import time

def image_create_init():
    # 新生成镜像的初始值
    kwargs = {
        'os_type': IMAGE_OS_TYPE,
        'os_ver_list': IMAGE_OS_VER
    }
    if not IMAGE_OS_TYPE or not IMAGE_OS_VER:
        logging.info('os_type或者os_ver值缺失')
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg='入参缺失')
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=kwargs)

# 创建全新镜像
def image_create_new():
    eimage_name = request.values.get('image_name')
    displayname = request.values.get('displayname')
    template_ostype = request.values.get('os_type')
    version = request.values.get('version')
    if not eimage_name or not displayname or not version or not template_ostype:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='入参缺失')

    # 判断当前image表是否有同名镜像
    image_nums, image_data = image_service.ImageService().get_images_by_name(eimage_name)
    if image_data:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='image表已存在同名镜像')

    # 判断当前image_manage表是否有同名镜像
    eimage_data = image_service.ImageManageService().get_image_manage_info_by_name(eimage_name)
    if eimage_data:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='image_manage表已存在同名镜像')

    # 获取IP资源，先判断是否有人也在分配IP资源，有则等待1s，时间之后再优化
    ip_lock_unused = False
    while not ip_lock_unused:
        ret_ip_lock_status = ip_l_s.IpLockService().get_ip_lock_info('ip')
        if not ret_ip_lock_status:
            logging.error('创建新镜像 %s 失败：检查IP时无法获取资源锁状态') %eimage_name
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='检查IP时无法获取资源锁状态')
        if ret_ip_lock_status['istraceing'] == IpLockStatus.USED:
            time.sleep(1)
        else:
            ip_lock_unused = True
    # 更新ip_lock表istraceing字段为1
    ret_ip_lock_used_status, ret_ip_lock_used_datas = __update_ip_lock_used()
    if not ret_ip_lock_used_status:
        logging.error(ret_ip_lock_used_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_used_datas)
    try:
        ret_ips_status, ret_ips_data = __check_ip_resource()
    except Exception as e:
        _msg = '创建全新镜像：判断IP资源是否足够出现异常 : check ip resource exception when create new image ，err：%s' %e
        logging.error(_msg)
        ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
        if not ret_ip_lock_unused_status:
            logging.error(ret_ip_lock_unused_datas)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=_msg)

    if not ret_ips_status:
        ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
        if not ret_ip_lock_unused_status:
            logging.error(ret_ip_lock_unused_datas)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ips_data)

    # 更新ip_lock表istraceing字段为0
    ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
    if not ret_ip_lock_unused_status:
        logging.error(ret_ip_lock_unused_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)

    #segment_data = segment_s.SegmentService().get_segment_for_img_tmp()
    ip_data = ret_ips_data
    message = '模板机 %s 创建预分配IP成功' % eimage_name
    logging.info(message)

    # 模板机define
    ret, message = im_man_act._img_tem_define(eimage_name)
    if not ret:
        logging.error(message)
        # 将预分频的ip释放
        _set_ip_init(ip_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=message)

    tag = randomUUID()
    # 添加信息到image_manage表
    insert_data = {
        'eimage_name': eimage_name,
        'displayname': displayname,
        # status=-1:初始化;0:使用中;1:编辑中;2:待发布
        'status': ImageManage.INIT,
        'related_image_tag': tag,
        'os_type': template_ostype,
        'version': version,
        #创建全新镜像，template_status值默认1
        'template_status': img_tmp_status.SHUTDOWN,
        'template_vm_ip': ip_data['ip_address'],
        'message': '创建完成',
        'create_type':image_ceate_type.ALL_NEW,
        'create_time': get_datetime_str()
    }
    # 创建全新的镜像
    ret = image_service.ImageManageService().add_image_info(insert_data)
    if ret.get('row_num') <= 0:
        logging.error("add image error, insert_data:%s", str(insert_data))
        error_msg = "添加新镜像 %s 失败",str(insert_data)
        _set_ip_init(ip_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR,msg = error_msg)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


def image_create_exist_init():
    # 根据已有镜像生成镜像的初始值接口
    params = {
        'WHERE_AND': {
            'in': {
                'system': ['linux', 'windows']
            },
        },
        'ORDER': [
            ['id', 'desc'],
        ],
    }
    ret = image_service.ImageService().query_data(**params)
    ret_new = ret[1]

    for i in ret_new:
        for y in i.keys():
            if y != 'system' and y != 'version' and y != 'name' and y != 'tag' and y!= 'displayname':
                del i[y]
    news_ids = []
    for id in ret_new:
        if id not in news_ids:
            news_ids.append(id)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=news_ids)

def __update_ip_lock_unused():
    '''
        更新ip_lock表istraceing字段为0
    :return:
    '''

    update_ip_lock_data = {
        'istraceing': IpLockStatus.UNUSED
    }
    where_ip_lock_data = {
        'table_name': 'ip'
    }
    ret_update_ip_lock = ip_l_s.IpLockService().update_ip_lock_info(update_ip_lock_data, where_ip_lock_data)
    if not ret_update_ip_lock:
        return False, '创建VM 步骤10：检查IP时无法更新资源锁状态为未使用中'
    return True, '创建VM 步骤10：检查IP时更新资源锁状态为未使用中成功'


# 从已有镜像创建新镜像
def image_create_exist():
    eimage_name = request.values.get('image_name')
    displayname = request.values.get('displayname')
    source_img_name = request.values.get('source_img_name')
    template_ostype = request.values.get('os_type')
    version = request.values.get('version')
    tag = randomUUID()
    if not eimage_name or not displayname or not version or not source_img_name or not template_ostype:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='入参缺失')

    # 判断当前image表是否有同名镜像
    image_nums, image_data = image_service.ImageService().get_images_by_name(eimage_name)
    if image_data:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='image表已存在同名镜像')

    # 判断当前image_manage表是否有同名镜像
    eimage_data = image_service.ImageManageService().get_image_manage_info_by_name(eimage_name)
    if eimage_data:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='image_manage表已存在同名镜像')

    # 获取IP资源，先判断是否有人也在分配IP资源，有则等待1s，时间之后再优化
    ip_lock_unused = False
    while not ip_lock_unused:
        ret_ip_lock_status = ip_l_s.IpLockService().get_ip_lock_info('ip')
        if not ret_ip_lock_status:
            logging.error('创建新镜像 %s 失败：检查IP时无法获取资源锁状态') % eimage_name
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='检查IP时无法获取资源锁状态')
        if ret_ip_lock_status['istraceing'] == IpLockStatus.USED:
            time.sleep(1)
        else:
            ip_lock_unused = True
    # 更新ip_lock表istraceing字段为1
    ret_ip_lock_used_status, ret_ip_lock_used_datas = __update_ip_lock_used()
    if not ret_ip_lock_used_status:
        logging.error(ret_ip_lock_used_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_used_datas)
    try:
        ret_ips_status, ret_ips_data = __check_ip_resource()
    except Exception as e:
        _msg = '从已有镜像创建全新镜像：判断IP资源是否足够出现异常 : check ip resource exception when create exist image ，err：%s' %e
        logging.error(_msg)
        ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
        if not ret_ip_lock_unused_status:
            logging.error(ret_ip_lock_unused_datas)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=_msg)

    if not ret_ips_status:
        ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
        if not ret_ip_lock_unused_status:
            logging.error(ret_ip_lock_unused_datas)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ips_data)

    # 更新ip_lock表istraceing字段为0
    ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
    if not ret_ip_lock_unused_status:
        logging.error(ret_ip_lock_unused_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)


    ip_data = ret_ips_data
    message = '模板机 %s 创建预分配IP成功' % eimage_name
    logging.info(message)

    # 在镜像编辑服务器上创建相应文件夹
    dest_dir = '/app/image/' + eimage_name
    ret, msg = ansibleCmdV2.create_destdir(IMAGE_EDIT_SERVER, dest_dir)
    if not ret:
        logging.error(msg)
        _set_ip_init(ip_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=msg)


    # 获取新镜像文件的list到镜像编辑服务器
    ret, message = im_man_act._img_create_from_exist(source_img_name, eimage_name)
    if not ret:
        logging.error(message)
        _set_ip_init(ip_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=message)

    # 模板机define
    ret, message = im_man_act._img_tem_define(eimage_name)
    if not ret:
        logging.error(message)
        _set_ip_init(ip_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=message)

    # 根据已有镜像生成镜像的接口
    # todo:template_vm_ip入参需要添加
    insert_data = {
        'eimage_name': eimage_name,
        'displayname': displayname,
        # status=-1:初始化;0:使用中;1:编辑中;2:待发布
        'status': ImageManage.INIT,
        'related_image_tag': tag,
        'version': version,
        # 根据已有的镜像创建，template_status只默认1
        'template_status': img_tmp_status.SHUTDOWN,
        'template_vm_ip': ip_data['ip_address'],
        'message': '创建完成',
        'create_type':image_ceate_type.FROM_EXIST,
        'create_time': get_datetime_str(),
        'os_type': template_ostype
    }
    ret = image_service.ImageManageService().add_image_info(insert_data)
    if ret.get('row_num') <= 0:
        logging.error("add image error, insert_data:%s", str(insert_data))
        error_msg = "添加新镜像 %s 失败", str(insert_data)
        _set_ip_init(ip_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=error_msg)

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


# 已有镜像补录
def image_update_by_exist():
    eimage_name = request.values.get('eimage_name')
    displayname = request.values.get('displayname')
    version = request.values.get('version')
    template_ostype = request.values.get('os_type')
    tag = randomUUID()
    if not eimage_name or not displayname or not version or not template_ostype:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='入参缺失')

    # 判断当前image表是否有该镜像信息
    image_nums, image_data = image_service.ImageService().get_images_by_name(eimage_name)
    if not image_data:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='image表不存在此镜像')

    # 判断当前image_manage表是否有同名镜像
    eimage_data = image_service.ImageManageService().get_image_manage_info_by_name(eimage_name)
    if eimage_data:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='image_manage表已存在同名镜像')

    # 获取IP资源，先判断是否有人也在分配IP资源，有则等待1s，时间之后再优化
    ip_lock_unused = False
    while not ip_lock_unused:
        ret_ip_lock_status = ip_l_s.IpLockService().get_ip_lock_info('ip')
        if not ret_ip_lock_status:
            logging.error('创建新镜像 %s 失败：检查IP时无法获取资源锁状态') % eimage_name
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='检查IP时无法获取资源锁状态')
        if ret_ip_lock_status['istraceing'] == IpLockStatus.USED:
            time.sleep(1)
        else:
            ip_lock_unused = True
    # 更新ip_lock表istraceing字段为1
    ret_ip_lock_used_status, ret_ip_lock_used_datas = __update_ip_lock_used()
    if not ret_ip_lock_used_status:
        logging.error(ret_ip_lock_used_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_used_datas)
    try:
        ret_ips_status, ret_ips_data = __check_ip_resource()
    except Exception as e:
        _msg = '已有镜像补录：判断IP资源是否足够出现异常 : check ip resource exception when image update by exist ，err：%s' % e
        logging.error(_msg)
        ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
        if not ret_ip_lock_unused_status:
            logging.error(ret_ip_lock_unused_datas)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=_msg)

    if not ret_ips_status:
        ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
        if not ret_ip_lock_unused_status:
            logging.error(ret_ip_lock_unused_datas)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ips_data)

    # 更新ip_lock表istraceing字段为0
    ret_ip_lock_unused_status, ret_ip_lock_unused_datas = __update_ip_lock_unused()
    if not ret_ip_lock_unused_status:
        logging.error(ret_ip_lock_unused_datas)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=ret_ip_lock_unused_datas)


    ip_data = ret_ips_data
    message = '模板机 %s 创建预分配IP成功' % eimage_name
    logging.info(message)

    # 在镜像编辑服务器上创建相应文件夹
    dest_dir = '/app/image/' + eimage_name
    ret, msg = ansibleCmdV2.create_destdir(IMAGE_EDIT_SERVER, dest_dir)
    if not ret:
        logging.error(msg)
        _set_ip_init(ip_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=msg)


    # 获取新镜像文件的list到镜像编辑服务器
    ret, message = im_man_act._img_create_from_exist(eimage_name, eimage_name)
    if not ret:
        logging.error(message)
        _set_ip_init(ip_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=message)

    # 模板机define
    ret, message = im_man_act._img_tem_define(eimage_name)
    if not ret:
        logging.error(message)
        _set_ip_init(ip_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=message)

    # 根据已有镜像生成镜像的接口
    insert_data = {
        'eimage_name': eimage_name,
        'displayname': displayname,
        # status=-1:初始化;0:使用中;1:编辑中;2:待发布
        'status': ImageManage.INIT,
        'related_image_tag': tag,
        'version': version,
        # 根据已有的镜像创建，template_status只默认1
        'template_status': img_tmp_status.SHUTDOWN,
        'template_vm_ip':  ip_data['ip_address'],
        'message': '创建完成',
        'create_type':image_ceate_type.UPDATE_EXIST,
        'create_time': get_datetime_str(),
        'os_type': template_ostype,
    }
    ret = image_service.ImageManageService().add_image_info(insert_data)
    if ret.get('row_num') <= 0:
        logging.error("add image error, insert_data:%s", str(insert_data))
        error_msg = "添加新镜像 %s 失败", str(insert_data)
        _set_ip_init(ip_data)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=error_msg)

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)

def __update_ip_lock_used():
    '''
        更新ip_lock表istraceing字段为1
    :return:
    '''

    update_ip_lock_data = {
        'istraceing': IpLockStatus.USED
    }
    where_ip_lock_data = {
        'table_name': 'ip'
    }
    ret_update_ip_lock = ip_l_s.IpLockService().update_ip_lock_info(update_ip_lock_data, where_ip_lock_data)
    if not ret_update_ip_lock:
        return False, '创建VM 步骤10：检查IP时无法更新资源锁状态为使用中'
    return True, '创建VM 步骤10：检查IP时更新资源锁状态为使用中成功'

def __check_ip_resource():
    '''
        判断IP资源是否足够
    :param hostpool_id:
    :param count:
    :return:
    '''
    # 获取可用ip
    ret_ip_data, ret_ip_segment_datas = ip_service.get_avail_tmp_ip()
    if not ret_ip_data:
        return False, '未找到可用的IP用于分配给模板机'

    # 标记ip为预分配
    update_data = {
        'status': IPStatus.PRE_ALLOCATION
    }
    where_data = {
        'id': ret_ip_data['id']
    }
    ret_mark_ip = ip_service.IPService().update_ip_info(update_data, where_data)
    if ret_mark_ip <= 0:
        return False, '模板机预分频IP %s 失败' % ret_ip_data['ip_address']
    else:
        return True, ret_ip_data

def _set_ip_init(ret_ip_data):
    # 标记ip为初始化状态
    update_data = {
        'status': IPStatus.UNUSED
    }
    where_data = {
        'id': ret_ip_data['id']
    }
    ret_mark_ip = ip_service.IPService().update_ip_info(update_data, where_data)
    if ret_mark_ip <= 0:
        return False, 'IP %s 状态重置为初始化失败' % ret_ip_data['ip_address']
    else:
        return True, 'IP %s 状态重置为初始化成功' % ret_ip_data['ip_address']



def __init_ip(segment_datas, ip_address):
    '''
        IP初始化
    :param segment_datas:
    :param ip_address:
    :return:
    '''
    ip_vlan = segment_datas['vlan']
    ip_netmask = segment_datas['netmask']
    ip_segment_id = segment_datas['id']
    ip_gateway_ip = segment_datas['gateway_ip']
    ip_dns1 = segment_datas['dns1']
    ip_dns2 = segment_datas['dns2']

    insert_data = {
        'ip_address': ip_address,
        'segment_id': ip_segment_id,
        'netmask': ip_netmask,
        'vlan': ip_vlan,
        'gateway_ip': ip_gateway_ip,
        'dns1': ip_dns1,
        'dns2': ip_dns2,
        'status': IPStatus.UNUSED,
        'created_at': get_datetime_str()
    }
    ret = ip_service.IPService().add_ip_info(insert_data)
    if ret == -1:
        return False
    return True

