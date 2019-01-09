# coding=utf8
'''
    image_sync_intodb
'''
# __author__ =  ""



from helper import json_helper
from flask import request
from model.const_define import ErrorCode
from service.s_host import host_service as host_s
from service.s_image import image_service as im_s
from service.s_image_sync import image_sync_service as im_sy_s
from service.s_image_sync import image_sync_schedule as im_sy_sch
import json
from datetime import  datetime
import time



#主函数
def host_image_task_intodb():
    #获取单台host的入库信息
    front_data = request.get_data()
    front_data_dict = json.loads(front_data)
    host_id = front_data_dict['host_id']
    image_list = front_data_dict['image_list']
    if not host_id or not image_list:
        err_msg = '入参缺失'
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg =err_msg)
    #判断host_id是否异常
    host_data = host_s.HostService().get_host_info(host_id)
    host_ip = host_data['ipaddress']
    if not host_data:
        err_msg = '获取host信息失败'
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg =err_msg)
    #定义两个list来存成功的image_task和失败的image_task
    correct_image_task_list = []
    error_image_task_list = []

    # #判断前台发来的image_list总长度不能大于7
    # image_list_num = len(image_list)
    # if int(image_list_num) > 7 :
    #     err_msg = 'image任务数量不能大于7'
    #     return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=err_msg)

    #判断前台传输的image id信息是否有重复值
    image_id_rep_check = image_id_check_rep(image_list)
    if not image_id_rep_check:
        err_msg = '同步任务中出现重复的image id记录'
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=err_msg)

    # 判断镜像信息是否异常
    for image_task_info in image_list:
        image_id = image_task_info['image_id']
        image_info = im_s.ImageService().get_image_info(image_id)
        #如果判断image_id异常
        if not image_info:
            err_msg = '获取镜像id为' +image_id +'信息失败'
            err_data ={
                'image_task':image_task_info,
                'error_message':err_msg
            }
            error_image_task_list.append(err_data)
            image_list.remove(image_task_info)
        else:
            #判断新增任务时间是否异常
            res,msg = check_new_task_time(image_task_info,host_id,image_id)
            if not res:
                err_msg = msg
                err_data = {
                    'image_task': image_task_info,
                    'error_message': err_msg
                }
                error_image_task_list.append(err_data)
                image_list.remove(image_task_info)
                print 1

    #针对check后的任务清单做入库处理
    for image_task_info in image_list:
        # 判断任务是新增还是加入计划任务
        image_id = image_task_info['image_id']
        image_task_ondo = im_sy_s.get_ondo_task(host_ip, image_id)
        #如果为新增任务
        if not image_task_ondo:
            task_start_time_str = image_task_info['start_time']
            task_start_time = datetime.strptime(task_start_time_str, "%Y-%m-%d %X")
            task_info_list = image_task_info['task_list']
            task_num = len(task_info_list)
            #判断计划任务数是否大于7
            if task_num > 7:
                image_info = im_s.ImageService().get_image_info(image_id)
                image_name = image_info['name']
                image_descrp = image_info['description']
                err_msg = '该image ' + image_name +' ' +image_descrp + ' 所添加的计划任务数量大于7'
                err_data = {
                    'error_message': err_msg,
                    'image_task': image_task_info
                }
                error_image_task_list.append(err_data)
                image_list.remove(image_task_info)
            speed_limit = image_task_info['speed_limit']
            host_ip = host_s.HostService().get_host_info(host_id)['ipaddress']
            #将每个image_task入image_sync_task表
            insert_data = {
                'image_id':image_id,
                'host_ip':host_ip,
                'status':'0',
                'type':'1',
                'schedule_num':task_num,
                'start_time':task_start_time,
                'isdeleted':'0',
                'on_task':'0',
                'speed_limit':speed_limit,
                'process_id':'undefined'
            }
            res1 = im_sy_s.ImageSyncService().add_image_sync_task(insert_data)
            if not res1:
                message = '插入image_sync_task表失败'
                err_data = {
                    'image_task': image_task_info,
                    'error_message': message
                }
                error_image_task_list.append(err_data)
                image_list.remove(image_task_info)
            #如入image_sync_task表成功，则继续入image_sync_schedult表
            else:
                image_sync_task_id = res1.get('last_id')
                for sch_task in task_info_list:
                    sch_starttime_str = sch_task['sch_starttime']
                    sch_endtime_str = sch_task['sch_endtime']
                    sch_starttime = datetime.strptime(sch_starttime_str, "%Y-%m-%d %X")
                    sch_endtime = datetime.strptime(sch_endtime_str, "%Y-%m-%d %X")
                    insert_data = {
                        'image_task_id':image_sync_task_id,
                        'sch_state':'0',
                        'sch_starttime':sch_starttime,
                        'sch_endtime':sch_endtime,
                        'isdeleted':'0'
                    }
                    res = im_sy_sch.ImageSyncScheduleService().add_image_sync_sch(insert_data)
                    #如果入库失败则跳出循环并将上步入库的task_sync表的isdeleted置为1
                    if not res:
                        where_data ={
                            'id':image_sync_task_id
                        }
                        update_data = {
                            'isdeleted':'1'
                        }
                        im_sy_s.ImageSyncService().update_image_sync_task(update_data,where_data)
                        err_msg = '插入计划任务失败'
                        err_data ={
                            'error_message':err_msg,
                            'image_task':image_task_info
                        }
                        error_image_task_list.append(err_data)
                        image_list.remove(image_task_info)
                        error_image_task_list.append(err_data)
                        break


        #如果已存在image_id,只是新增计划任务
        else:
            #获取当前image_id下在running的计划任务数
            image_sync_task_id = image_task_ondo[0]['id']
            sch_ondo_num,sch_ondo_data = im_sy_sch.get_ondo_sch_list(image_sync_task_id)
            #判断前台输入的image任务数量是否大于当前可添加的数量
            sch_add_num = len(image_task_info['task_list'])
            if sch_add_num + sch_ondo_num > 7:
                image_info = im_s.ImageService().get_image_info(image_id)
                image_name = image_info['name']
                image_descrp = image_info['description']
                message = '镜像' + image_name + ' ' + image_descrp +'可添加任务数量大于最大值'
                err_data = {
                    'image_task': image_task_info,
                    'error_message': message
                }
                error_image_task_list.append(err_data)
                image_list.remove(image_task_info)
            #如果前台输入的计划任务数量不超过最大值则入库
            else:
                task_info_list = image_task_info['task_list']
                for sch_task in task_info_list:
                    sch_starttime_str = sch_task['sch_starttime']
                    sch_endtime_str = sch_task['sch_endtime']
                    sch_starttime = datetime.strptime(sch_starttime_str, "%Y-%m-%d %X")
                    sch_endtime = datetime.strptime(sch_endtime_str, "%Y-%m-%d %X")
                    insert_data = {
                        'image_task_id':image_sync_task_id,
                        'sch_state':'0',
                        'sch_starttime':sch_starttime,
                        'sch_endtime':sch_endtime,
                        'isdeleted':'0'
                    }
                    im_sy_sch.ImageSyncScheduleService().add_image_sync_sch(insert_data)


    #统计总的入库成功list和失败list并返回给前台
    for image_task in image_list:
        correct_image_task_list.append(image_task)
    #计算总的失败数
    total_image_task_num = len(image_list)
    total_fail_task_num = len(error_image_task_list)
    if total_image_task_num == 0:
        tag = ErrorCode.ALL_FAIL
    else:
        tag = ErrorCode.SUCCESS
    return_data = {
        'fail_task_num':str(total_fail_task_num),
        'fail_task_list':error_image_task_list,
        'succss_task_list':correct_image_task_list
    }
    return json_helper.format_api_resp(code=tag,data=return_data )


def Checktime(starttime,endtime,checktime):
    #start_tag = time.strftime(starttime,'%Y-%m-%d %H:%M:%S')
    #end_tag = time.strftime(endtime,'%Y-%m-%d %H:%M:%S')
    #check_tag = time.strftime(checktime,'%Y-%m-%d %H:%M:%S')
    if starttime <= checktime  and endtime >= checktime:
        Flag = True
    else:
        Flag = False
    return Flag


#获取指定image任务的开始时间和结束时间的list
def image_task_get(host_id,image_id):
    host_ip = host_s.HostService().get_host_info(host_id)['ipaddress']
    #查询db，获取当前host上的任务信息
    res_data = im_sy_s.get_ondo_task(host_ip, image_id)
    task_time_list = []
    if res_data:
        image_sy_type = res_data[0]['type']
        image_sy_id = res_data[0]['id']
        # 如果是计划任务，则记录任务的时间到list中
        if image_sy_type != "0":
            sch_ondo_num,sch_ondo_data_list = im_sy_sch.get_ondo_sch_list(image_sy_id)
            if sch_ondo_num > 0:
                for sch_data in sch_ondo_data_list:
                    insert_data = {
                        'sch_starttime':sch_data['sch_starttime'],
                        'sch_endtime':sch_data['sch_endtime']
                    }
                    task_time_list.append(insert_data)
    return task_time_list


#判断新增的任务时间是否有误
def check_new_task_time(image_task_info,host_id,image_id):
    task_info_list = image_task_info['task_list']
    task_num = len(task_info_list)
    new_task_time_list = []
    image_info =  im_s.ImageService().get_image_info(image_id)
    image_name = image_info['name']
    image_descrp = image_info['description']
    image_return_to_user = image_name + '(' +image_descrp + ')'
    # 如果存在结束时间大于开始时间则报错
    for i in range(int(task_num)):
        task_starttime_str = task_info_list[i]['sch_starttime']
        task_endtime_str = task_info_list[i]['sch_endtime']
        task_starttime = datetime.strptime(task_starttime_str, "%Y-%m-%d %X")
        task_endtime = datetime.strptime(task_endtime_str, "%Y-%m-%d %X")
        if task_starttime > task_endtime:
            err_msg = '计划任务的结束时间大于开始时间,相关镜像为 %s 错误的开始时间为 %s ' \
                      '错误的结束时间为 %s' %(image_return_to_user,task_starttime_str,task_endtime_str)
            err_data = {
                'image_task': image_task_info,
                'error_message': err_msg
            }
            return False,err_data
        else:
            new_task_time_list.append(task_starttime)
            new_task_time_list.append(task_endtime)
    #判断当前库中是否有running的任务时间点与新增有冲突
    image_ondo_task_list = image_task_get(host_id,image_id)
    if image_ondo_task_list == []:
        return True,'success'
    else:
        #针对新增任务的每个时间点，对表中的每个running task做时间冲突的判断
        for image_ondo_task in image_ondo_task_list:
            imagetask_starttime = image_ondo_task['sch_starttime']
            imagetask_endtime = image_ondo_task['sch_endtime']
            for new_task_time in new_task_time_list:
                res = Checktime(imagetask_starttime,imagetask_endtime,new_task_time)
                if res:
                    task_starttime_to_user = imagetask_starttime.strftime("%Y-%m-%d %X")
                    task_endtime_to_user = imagetask_endtime.strftime("%Y-%m-%d %X")
                    msg = '新增计划的时间与当前在运行的任务时间有冲突,' \
                          '相关镜像为 %s,与库中存在的时间段为%s %s 的任务有冲突' %(image_return_to_user,task_starttime_to_user,task_endtime_to_user)
                    return False,msg
        return True,'success'


#判断前台传输的image list中是否存在重复的image id
def image_id_check_rep(image_list):
    Flag = True
    image_id_check_list = []
    for image_task_info in image_list:
        image_id = image_task_info['image_id']
        image_id_check_list.append(image_id)
    for i in image_id_check_list:
        if image_id_check_list.count(i) > 1:
            Flag = False
    return Flag


















