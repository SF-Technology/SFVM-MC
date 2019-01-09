# coding=utf8
'''
    发布新的镜像接口
'''

import sys
import time
from flask import request

from lib.shell import ansibleCmdV2
from model.const_define import ErrorCode, ImageManage, \
    image_mange_action_state as im_m_act_sta, image_manage_action as im_m_act, image_ceate_type
import logging
import json_helper
from lib.vrtManager.util import randomUUID
from service.s_image import image_service as im_s
from helper.time_helper import get_datetime_str
from config.default import IMAGE_EDIT_SERVER
import re
import Queue
import threading
from service.s_imagecache import imagecache_service as imca_s
from config.default import IMAGE_SERVER

reload(sys)
sys.setdefaultencoding('utf-8')

img_server_queue = Queue.Queue()
imgcache_server_queue = Queue.Queue()

def get_image_actual_size(image_name,disk_name):
    res = ansibleCmdV2.image_actual_size(IMAGE_EDIT_SERVER,image_name,disk_name)
    if res[0] == False:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR,msg=res[1])
    # res[1]中就是image实际大小的值
    if re.search('G',res[1]) != None:
        # 将磁盘的大小转化成mb
        return  float(res[1].rstrip('G'))*1024
    elif re.search('M',res[1]) != None:
        return float(res[1].rstrip('M'))
    return res[1]


def get_image_md5(image_name,disk_name):
    res = ansibleCmdV2.get_image_md5(IMAGE_EDIT_SERVER, image_name, disk_name)
    if res[0] == False:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR,msg=res[1])
    # res[1]中就是image的md5值
    return res[1]


def get_image_size_gb(image_name,disk_name):
    '''获取image的size_gb值'''
    res = ansibleCmdV2.get_image_size_gb(IMAGE_EDIT_SERVER, image_name, disk_name)
    if res[0] == False:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR,msg=res[1])
    return int(res[1].rstrip('G'))


def get_image_file_num(image_name):
    # 获取镜像文件的数量，发布新镜像时磁盘数量就是文件数量
    res = ansibleCmdV2.get_image_file_num(IMAGE_EDIT_SERVER, image_name)
    if res[0] == False:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR,msg=res[1])
    return int(res[1])


def image_disk_md5_together(name):
    '''
    通过image的name获取image所有磁盘的size和md5值
    :param name:
    :return: image_info_list [{'actual_size_mb':988.0, 'md5':'6798980765'},{'actual_size_mb':1010.1, 'md5':'38677689898798'}]
    '''
    image_info_list = []
    # image的磁盘数目
    disk_num = get_image_file_num(name)
    disk_0_dict = {}
    actual_size = get_image_actual_size(name, name)
    disk_0_dict['actual_size_mb'] = actual_size
    image_md5 = get_image_md5(name, name)
    disk_0_dict['md5'] = image_md5
    if disk_num == 1:
        image_info_list.append(disk_0_dict)
    else:
        image_info_list.append(disk_0_dict)
        for i_n in range(1, int(disk_num)):
            dict_image = {}
            name_i = name + '_disk' + str(i_n + 1)
            actual_size = get_image_actual_size(name, name_i)
            dict_image['actual_size_mb'] = actual_size
            image_md5 = get_image_md5(name, name_i)
            dict_image['md5'] = image_md5
            image_info_list.append(dict_image)
    return image_info_list


def image_release_by_new():
    name = request.values.get('name')
    displayname = request.values.get('displayname'),
    system = request.values.get('system'),
    version = request.values.get('version')
    image_manage_data = im_s.ImageManageService().get_img_manage_data_by_name(name)
    create_type = image_manage_data[1]['create_type']
    if not name or not displayname or not system or not version:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='入参缺失')

    # 判断当前image状态是否正常
    image_manage_stat = image_manage_data[1]["status"]
    if image_manage_stat != ImageManage.CHECKOUT:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='当前模板机状态不允许此操作')

    # 更新image_manage状态为发布中
    message = ''
    eimage_name = name
    im_s.ImageManageService().update_image_manage_status(eimage_name, message, ImageManage.RELEASING)
    image_info_list = image_disk_md5_together(name)

    # 获取镜像文件的list
    res, image_list_info = ansibleCmdV2.get_image_disk_list(IMAGE_EDIT_SERVER, eimage_name)
    update_action = im_m_act.RELEASE_IMGSERVER
    if not res:
        # 更新image_manage表和image_update_status
        error_msg = image_list_info
        state_tag = im_m_act_sta.FAILED
        im_s.ImageManageService().update_image_manage_status(eimage_name, error_msg, ImageManage.CHECKOUT)
        im_s.ImageStatusService().add_image_status_action(eimage_name, update_action, state_tag, message)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=error_msg)
    image_disk_list = list(image_list_info)

    # 更新镜像服务器
    ret, message = img_server_update_img(eimage_name, image_disk_list, create_type)
    if not ret:
        error_msg = message
        state_tag = im_m_act_sta.FAILED
        im_s.ImageManageService().update_image_manage_status(eimage_name, error_msg, ImageManage.CHECKOUT)
        im_s.ImageStatusService().add_image_status_action(eimage_name, update_action, state_tag, error_msg)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=error_msg)
    # 如果为全新创建则跳过更新缓存服务器
    if create_type == image_ceate_type.ALL_NEW or create_type == image_ceate_type.FROM_EXIST:
        pass
    else:
        # 更新镜像缓存服务器
        ret, message = img_cache_server_update_img(eimage_name, image_disk_list)
        update_action = im_m_act.RELEASE_CACHESERVER
        if not ret:
            error_msg = message
            state_tag = im_m_act_sta.FAILED
            im_s.ImageManageService().update_image_manage_status(eimage_name, error_msg, ImageManage.CHECKOUT)
            im_s.ImageStatusService().add_image_status_action(eimage_name, update_action, state_tag, error_msg)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=error_msg)
    # 更新db
    tag = randomUUID()
    # 如果类型为现有补录，则update image表
    if create_type == image_ceate_type.UPDATE_EXIST:
        for index, i in enumerate(image_info_list):
            if index == 0:
                url_i = ('/' + name) * 2
            else:
                url_i = ('/' + name) * 2 + '_disk' + str(index + 1)
            update_data = {
                'md5': i['md5'],
                'actual_size_mb': i['actual_size_mb'],
                'tag': tag,
                'updated_at': get_datetime_str(),
            }
            where_data = {
                'url': url_i,
            }
            ret = im_s.ImageService().update_image_info(update_data, where_data)
            if ret < 0:
                logging.error("release image error, update_data:%s", str(update_data))
                error_msg = "发布镜像 %s 失败,更新image表信息失败", str(update_data)
                state_tag = im_m_act_sta.FAILED
                im_s.ImageManageService().update_image_manage_status(eimage_name, error_msg, ImageManage.CHECKOUT)
                im_s.ImageStatusService().add_image_status_action(eimage_name, update_action, state_tag, error_msg)
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=error_msg)
    # 新建镜像则add image表记录
    else:
        for index, i in enumerate(image_info_list):
            if index == 0:
                url_i = ('/' + name) * 2
                # image_info_list中第一个数据是系统盘
                type = '0'
                description = u'系统盘'
                size_gb = get_image_size_gb(name, name)
            else:
                url_i = ('/'+name)*2 + '_disk' + str(index+1)
                name_i = name + '_disk' + str(index + 1)
                type = '1'
                description = u'数据盘'
                size_gb = get_image_size_gb(name, name_i)

            insert_data = {
                'name': name,
                'displayname': displayname,
                'system': system,
                'version': version,
                'description': description,
                'md5': i['md5'],
                'format': 'qcow2',
                'actual_size_mb': i['actual_size_mb'],
                'size_gb': size_gb,
                'isdeleted': '0',
                'created_at': get_datetime_str(),
                'url': url_i,
                'type': type,
                # todo；uuid
                'tag': tag,
            }
            ret = im_s.ImageService().add_image_info(insert_data)
            if ret.get('row_num') <= 0:
                logging.error("add image error, insert_data:%s", str(insert_data))
                error_msg = "发布新镜像 %s 失败,更新image表失败" % eimage_name
                state_tag = im_m_act_sta.FAILED
                im_s.ImageManageService().update_image_manage_status(eimage_name, error_msg, ImageManage.CHECKOUT)
                im_s.ImageStatusService().add_image_status_action(eimage_name, update_action, state_tag, error_msg)
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR,msg = error_msg)
    update_data = {
        'status':'0',
        'create_type': image_ceate_type.USING
    }
    where_data = {
        'eimage_name':name
    }

    chan_status = im_s.ImageManageService().update_image_info(update_data,where_data)
    if chan_status < 0:
        logging.error("release image error, update_data:%s", str(update_data))
        error_msg = "发布镜像 %s 失败,更新image_manage表信息失败", eimage_name
        state_tag = im_m_act_sta.FAILED
        im_s.ImageManageService().update_image_manage_status(eimage_name, error_msg, ImageManage.CHECKOUT)
        im_s.ImageStatusService().add_image_status_action(eimage_name, update_action, state_tag, error_msg)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR,msg = error_msg)
    state_tag = im_m_act_sta.SUCCESSED
    message = '发布成功'
    im_s.ImageStatusService().add_image_status_action(eimage_name, update_action, state_tag, message)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)

# def image_release_by_exist():
#     # 发布已有模板的镜像
#     '''
#     image_info_list = [{'actual_size_mb':1200.8, 'md5':'32234234234342'}]
#     :return:
#     '''
#     name = request.values.get('name')
#     image_info_list = []
#     params = {
#         'WHERE_AND': {
#             '=': {
#                 'name': name,}
#             }
#     }
#     ret_image = image_service.ImageService().query_data(**params)
#     if ret_image[0] <= 0:
#         return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg="image name is not exist")
#     # image的磁盘数目
#     disk_num = ret_image[0]
#     disk_0_dict = {}
#     actual_size = get_image_actual_size(name, name)
#     disk_0_dict['actual_size_mb'] = actual_size
#     image_md5 = get_image_md5(name, name)
#     disk_0_dict['md5'] = image_md5
#
#     if disk_num == 1:
#         image_info_list.append(disk_0_dict)
#     else:
#         image_info_list.append(disk_0_dict)
#         for i_n in range(1, int(disk_num)):
#             dict_image = {}
#             name_i =name + '_disk' + str(i_n + 1)
#             actual_size = get_image_actual_size(name,name_i)
#             dict_image['actual_size_mb'] = actual_size
#             image_md5 = get_image_md5(name,name_i)
#             dict_image['md5'] = image_md5
#             image_info_list.append(dict_image)
#
#     for index,i in enumerate(image_info_list):
#         if index == 0:
#             url_i = ('/' + name) * 2
#         else:
#             url_i = ('/'+name)*2 + '_disk' + str(index+1)
#         update_data = {
#             'md5': i['md5'],
#             'actual_size_mb': i['actual_size_mb'],
#             'updated_at': get_datetime_str(),
#         }
#         where_data = {
#             'url':url_i,
#         }
#         ret = image_service.ImageService().update_image_info(update_data,where_data)
#         if ret< 0:
#             logging.error("release image error, update_data:%s", str(update_data))
#             error_msg = "发布镜像 %s 失败", str(update_data)
#             return json_helper.format_api_resp(code=ErrorCode.SYS_ERR,msg = error_msg)
#     update_data = {
#         'status':'0',
#     }
#     where_data = {
#         'eimage_name':name
#     }
#
#     change_status = image_service.ImageManageService().update_image_info(update_data,where_data)
#     if change_status < 0:
#         return json_helper.format_api_resp(code=ErrorCode.SYS_ERR,msg = 'set image status error')
#     return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


# 单台img_server镜像的更新操作
def update_image(host_ip, image_disk_list, image_name, create_type):
    if create_type == '0' or create_type == '1':
        pass
    else:
        for image_disk in image_disk_list:
            # 先将当前镜像文件进行备份
            ret, message = ansibleCmdV2.img_backup(host_ip, image_disk, image_name)
            if not ret:
                result = False, message
                img_server_queue.put(result)
                return
    # 将新的镜像文件下载到imgserver上
    if create_type == '0' or create_type == '1':
        dest_dir = '/app/image/' + image_name
        ret, message = ansibleCmdV2.create_destdir(host_ip, dest_dir)
        if not ret:
            result = False, message
            img_server_queue.put(result)
            return
    for image_disk in image_disk_list:
        ret, message = ansibleCmdV2.download_img(host_ip, image_name, image_disk)
        if not ret:
            result = False, message
            img_server_queue.put(result)
            return
    message = 'image %s update successed' % image_name
    result = True, message
    img_server_queue.put(result)
    return


# 镜像服务器更新镜像函数
def img_server_update_img(image_name, image_disk_list,create_type):
    threads = []
    hostlist = IMAGE_SERVER
    for host in hostlist:
        update_img_thread = threading.Thread(target=update_image, args=(host, image_disk_list, image_name, create_type))
        threads.append(update_img_thread)
        update_img_thread.start()

    for t in threads:
        t.join()

    return_msg_list = []
    while not img_server_queue.empty():
        return_msg_list.append(img_server_queue.get())
    error_list = []
    for msg_list in return_msg_list:
        if msg_list[0] is False:
            error_list.append(msg_list[1])
    if error_list == []:
        return True, '镜像服务器更新镜像 %s 成功' %image_name
    else:
        return False, error_list[0]

# # 镜像缓存服务器更新
# def img_cache_server_update_img(image_name, image_disk_list):
#     cache_list = get_avail_cacheserver()
#     threads = []
#     hostlist = cache_list
#     for host in hostlist:
#         update_imgcache_thread = threading.Thread(target=single_cacheserver_update, args=(image_name, image_disk_list, host))
#         threads.append(update_imgcache_thread)
#         update_imgcache_thread.start()
#
#     for t in threads:
#         t.join()
#
#     return_msg_list = []
#     while not imgcache_server_queue.empty():
#         return_msg_list.append(imgcache_server_queue.get())
#     error_list = []
#     for msg_list in return_msg_list:
#         if msg_list[0] is False:
#             error_list.append(msg_list[1])
#     if error_list == []:
#         return True, True, '镜像缓存服务器更新镜像 %s 成功' % image_name
#     else:
#         total_cache_num = len(cache_list)
#         error_cache_num = len(error_list)
#         if error_cache_num > total_cache_num*0.3:
#             error_str = ','.join(error_list)
#             err_msg = '更新失败的缓存服务器超过总数的30%，以下缓存服务器更新失败:' + error_str
#             return False, False, err_msg
#         else:
#             error_str = ','.join(error_list)
#             err_msg = '以下镜像缓存服务器更新失败，请手动更新:' + error_str
#             return False, True, err_msg


# 镜像缓存服务器更新
def img_cache_server_update_img(image_name, image_disk_list):
    cache_list = get_avail_cacheserver()
    fail_list = []
    hostlist = cache_list
    for host in hostlist:
        res, msg = single_cacheserver_update(image_name, image_disk_list, host)
        if not res:
            fail_list.append(msg)
    if fail_list:
        return False, fail_list
    else:
        return True, "镜像缓存服务器更新成功"


# 单台镜像缓存服务器更新
def single_cacheserver_update(image_name, image_disk_list, host_ip):
    image_server_list = IMAGE_SERVER
    Flag = False
    res_msg = ''
    i = 0
    # 失败后等3秒重试，重试2次
    while i < 3 and not Flag:
        time.sleep(3)
        ret, message = ansibleCmdV2.imgcache_update(image_name, image_disk_list, host_ip, image_server_list)
        res_msg = message
        if not ret:
            i += 1
        else:
            Flag = True
    if Flag:
        return True, res_msg
    else:
        return False, res_msg


# 获取所有可用镜像缓存服务器
def get_avail_cacheserver():
    total_data = imca_s.ImageCacheService().get_all_imagecache_addr()
    imagecache_list = []
    for data in total_data:
        imagecache_list.append(data['imagecache_ip'])
    return imagecache_list
