# coding=utf8
'''
    image_sync host清单
'''
# __author__ =  ""
from lib.shell.ansibleCmdV2 import image_md5_get
from service.s_host import host_service as host_s, host_schedule_service as host_s_s
from service.s_image_sync import image_sync_service as im_sy_s
from service.s_image_sync import image_sync_schedule as im_sy_sch
from service.s_image import image_service as im_s
from model.const_define import ErrorCode
from config.default import ANSIABLE_REMOTE_USER,OPENSTACK_DEV_USER
import json_helper
from common_data_struct import host_info,image_info
from config.default import KVMHOST_LOGIN_PASS,KVMHOST_SU_PASS
from helper.encrypt_helper import decrypt


#单个host的镜像信息返回汇总
def single_host_image_return(host_id):
    #获取当前host已有的镜像信息汇总
    res1,local_image_data = local_image_return(host_id)
    if not res1:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=local_image_data)
    else:
        #获取当前host上没有的镜像信息汇总
        res2,remote_image_data = image_remote_list(host_id)
        if not res2:
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=local_image_data)
        else:
            #获取当前库中任务存在的镜像任务
            host_info = host_s.HostService().get_host_info(host_id)
            host_ip = host_info['ipaddress']
            image_task_list = im_sy_s.get_host_working_list(host_ip)
            #分别对local_image_list和remote_image_list做处理
            local_image_data_ch = local_image_list_ch(host_id,local_image_data,image_task_list)
            remote_image_data_ch = remote_image_list_ch(remote_image_data,image_task_list)
            return_data ={
                'local_image_data':local_image_data_ch,
                'remote_image_data':remote_image_data_ch
            }
            return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=return_data)


#获取host上的存在的image情况
def get_host_local_image(host_id):
    host_db = host_s.HostService().get_host_info(host_id)
    if not host_db:
        message = '该物理机不存在'
        return False,message
    host = host_info.HostInfo()
    host_perform_info = host_s_s.get_host_used(host_db, expire=False)
    if not host_perform_info:
        message = '获取镜像信息失败'
        return False,message
    host.collect_time = host_perform_info['collect_time']
    host.start_time = host_perform_info['start_time']
    host_images = host_perform_info['images']
    if host_images == '':
        local_image_list = []
    else:
        local_image_list = host_images.split(' ')
    return True,local_image_list


#判断每个image是否为最新状态
def image_status_check(image_name,host_id):
    host_data = host_s.HostService().get_host_info(host_id)
    if not host_data:
        message = "获取host信息失败"
        return False, message
    res, image_data = im_s.ImageService().get_images_by_name_t(image_name)
    if not res:
        message = "获取镜像信息失败"
        return False, message
    image_local_md5, message = image_md5_get(host_data['ipaddress'], image_name)
    if not image_local_md5:
        return False,False,message
    else:
        res, image_data = im_s.ImageService().get_images_by_name_t(image_name)
        if not res:
            message = '镜像:%s不在远端镜像列表中' %image_name
            return False,'1',message
        else:
            image_remote_md5 = image_data[0]['md5']
            if image_local_md5 == image_remote_md5:
                message = "镜像为最新"
                return True,'0',message
            else:
                message = "镜像需更新"
                return True,'1',message


#获取当前所有镜像信息
def image_list():
    params = {
        'WHERE_AND': {
            '=': {
                'isdeleted': '0',
            },
        },
    }

    total_nums, data = im_s.ImageService().query_data(**params)
    image_total_list = []
    for i in data:
        image_total_list.append(i)

    return total_nums,image_total_list


#获取当前host上没有的镜像信息
def image_remote_list(host_id):
    #获取当前所有image的list
    image_num,image_total_list = image_list()
    remote_image_list = []
    #获取当前本地image的list
    res,image_local_list = get_host_local_image(host_id)
    if not res:
        return False,image_local_list
    else:
        if image_local_list == []:
            remote_image_list = image_total_list
            return True,remote_image_list
        else:
            _local_imageid_list = []
            #获取当前所有local_Image的id list
            for local_image in image_local_list:
                res,_local_image_info = im_s.ImageService().get_images_by_name_t(local_image)
                if res:
                    _local_image_id = _local_image_info[0]['id']
                    _local_imageid_list.append(_local_image_id)
            #如果发现总的image中有id不在本地image list中，则加入remote_List
            for image in image_total_list:
                if image['id'] not in _local_imageid_list:
                    remote_image_list.append(image)
            return True,remote_image_list


#返回host上已有镜像的信息
def local_image_return(host_id):
    #获取host上当前的image清单
    res1, local_image_list = get_host_local_image(host_id)
    local_image_return_list = []
    #如果本地没有镜像
    if not res1:
        return False,local_image_list
    #如果本地有镜像
    else:
        #针对本地的每个镜像获取其是否为最新
        for image in local_image_list:
            image_status_tag = False
            tag = 0
            #重试3次获取是否最新
            while not image_status_tag and tag < 3:
                image_status_tag, checktag, checkmsg = image_status_check(image, host_id)
                tag  = tag +1
            #获取镜像是否最新失败
            if not image_status_tag:
                if checktag == '1':
                    ret_msg = '本地镜像%s不在远端镜像服务器列表中' %image
                    res_data = {
                        'image_info': image,
                        'msg': ret_msg,
                        'check_data': 'faile'
                    }
                    local_image_return_list.append(res_data)
                else:
                    res_data = {
                        'image_info':image,
                        'msg':'获取镜像失败',
                        'check_data':'faile'
                    }
                    local_image_return_list.append(res_data)
            #获取镜像是否最新成功
            else:
                #如果该image为最新，则只返回image的信息
                if checktag == '0':
                    res, image_data = im_s.ImageService().get_images_by_name_t(image)
                    check_data = {
                        'image_info': image_data[0],
                        'check_data': checktag,
                        'msg': checkmsg
                    }
                    local_image_return_list.append(check_data)
                #如果该image非最新，则获取其任务状态并一并返回
                else:
                    res,image_info = im_s.ImageService().get_images_by_name_t(image)
                    image_id = image_info[0]['id']
                    task_data = image_task_get(host_id,image_id)
                    res, image_data = im_s.ImageService().get_images_by_name_t(image)
                    check_data = {
                        'image_info': image_data[0],
                        'check_data': checktag,
                        'msg': checkmsg,
                        'task_info':task_data
                    }
                    local_image_return_list.append(check_data)
        return True,local_image_return_list


#获取指定image的任务信息
def image_task_get(host_id,image_id):
    host_ip = host_s.HostService().get_host_info(host_id)['ipaddress']
    #查询db，获取当前host上的任务信息
    res_data = im_sy_s.get_ondo_task(host_ip, image_id)
    if res_data:
        image_sy_type = res_data[0]['type']
        image_sy_stat = res_data[0]['status']
        image_sy_id = res_data[0]['id']
        image_sy_speed = res_data[0]['speed_limit']

        # 如果是立即执行的任务，则返回任务开始时间
        if image_sy_type == "0":
            task_startime = im_sy_s.get_task_startttime(image_sy_id)
            res1_data = {
                'host_ip': host_ip,
                'ondo_task':'0',
                'task_type': image_sy_type,
                'start_time': task_startime,
                'task_state': image_sy_stat
            }
            return res1_data
        # 如果是计划任务，则返回每个计划任务的情况
        else:
            task_startime = im_sy_s.get_task_startttime(image_sy_id)
            sch_ondo_num,sch_ondo_list = im_sy_sch.get_ondo_sch_list(image_sy_id)
            res2_data = {
                'host_ip': host_ip,
                'ondo_task': '0',
                'task_type': image_sy_type,
                'start_time': task_startime,
                'task_state': image_sy_stat,
                'task_sch_ondo_list': sch_ondo_list,
                'speed_limit':image_sy_speed,
                'task_sch_ondo_num':sch_ondo_num
            }
            return res2_data
    # 如果host无进行中状态的任务，则返回host_ip给前端
    else:
        res3_data = {
            'ondo_task': '1',
            'host_ip': host_ip,
        }
        return res3_data


#对local_image_list与库中image_list做筛选
def local_image_list_ch(host_id,local_image_list,task_image_list):
    local_imageid_list = []
    for local_image_data in local_image_list:
        if local_image_data['check_data'] != 'faile':
            local_image_info = local_image_data['image_info']
            local_imageid = local_image_info['id']
            local_imageid_list.append(str(local_imageid))
    for task_image_info in task_image_list:
        #如果发现库中有任务的image不在当前host上
        if task_image_info['image_id'] not in local_imageid_list:
            #获取其任务信息并装填入local_image_list中
            task_data = image_task_get(host_id, task_image_info['image_id'])
            image_info = im_s.ImageService().get_image_info(task_image_info['image_id'])
            checkmsg = '库中已有任务，本地尚无镜像'
            check_data = {
                'image_info': image_info,
                'check_data': '1',
                'msg': checkmsg,
                'task_info': task_data
            }
            local_image_list.append(check_data)
    return local_image_list



#对remote_image_list与库中image_list做筛选
def remote_image_list_ch(remote_image_list,task_image_list):
    remote_imageid_list = []
    for remote_image_data in remote_image_list:
        remote_imageid = remote_image_data['id']
        remote_imageid_list.append(str(remote_imageid))
    for task_image_info in task_image_list:
        # 如果发现库中有任务的image在remote_image_list中
        if task_image_info['image_id']  in remote_imageid_list:
            image_info = im_s.ImageService().get_image_info(task_image_info['image_id'])
            remote_image_list.remove(image_info)
    return remote_image_list














