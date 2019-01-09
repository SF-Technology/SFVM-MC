# coding=utf8
'''
    v2v_esx
'''
# __author__ =  ""


import env
from lib.shell import ansibleCmdV2

env.init_env()
import time
import os
from service.s_image import image_service as im_s
from service.s_image_sync import image_sync_schedule as im_sy_sch
from service.s_host import host_service as ho_s
from service.s_image_sync import image_sync_service as im_sy_s
from helper.time_helper import get_datetime_str
from service.s_imagecache import imagecache_service as imca_s
import logging
from helper.encrypt_helper import decrypt
import socket
import threading
from datetime import datetime
from config.default import ANSIABLE_REMOTE_USER,ANSIABLE_REMOTE_SU_USER, \
    ANSIABLE_REMOTE_PWD,ANSIABLE_REMOTE_SU_PWD,IMAGE_SERVER,IMAGE_SERVER_PORT,\
    NET_AREA_IMAGE_CACHE_SERVER_PORT,DIR_DEFAULT



def image_sync_do_task():
    # 获取当前在进行的任务清单
    list_working = im_sy_s.check_task_todo()

    if not list_working:
        time.sleep(60)
        return 0

    threads = []
    for i in list_working:
        # 获取当前任务信息
        image_sync_task_id = i['id']
        host_ip = i['host_ip']
        request_thread = threading.Thread(target=single_task_do,
                                          args=(host_ip,image_sync_task_id))
        threads.append(request_thread)
        request_thread.start()

    # 判断多线程是否结束
    for t in threads:
        t.join()





#单个task的任务下发函数
def single_task_do(host_ip,task_id):
    im_sy_s.update_task_ondotag(task_id,'1')
    task_info = im_sy_s.ImageSyncService().get_image_sync_info(task_id)
    image_id = task_info['image_id']
    speed_limit = task_info['speed_limit']
    #获取当前任务的时间段
    task_num,task_time_list = get_task_worktime(task_id)
    #如果当前记录没有任务，return True
    if not task_num:
        return_data = 'no_job'
        message = '当前任务无可继续执行的计划'
        im_sy_s.update_task_ondotag(task_id, '0')
        return True,return_data,message
    else:
        #如果任务状态非已完成，且当前时间小于最后一条任务的时间
        while im_sy_s.ImageSyncService().get_image_sync_info(task_id)['status'] != '2'\
            and datetime.strptime(get_datetime_str(), "%Y-%m-%d %X") < get_task_endtime(task_id):
            #获取当前时间
            now_time_str = get_datetime_str()
            for task_time_info in task_time_list:
                task_starttime = task_time_info['task_starttime']
                task_endtime = task_time_info['task_endtime']
                sch_task_id = task_time_info['id']
                #判断该计划任务时间段是否可执行任务
                now_time = datetime.strptime(now_time_str, "%Y-%m-%d %X")
                res_checktime = Checktime(task_starttime,task_endtime,now_time)
                # 如果可执行则下发
                if res_checktime:
                    endtime = task_endtime
                    res_wget,res_msg,md5_tag = wget_func(host_ip,image_id,speed_limit,task_id,endtime,sch_task_id)
                    #wget下发成功则改变库中任务信息
                    if res_wget:
                        #如果发现镜像为最新
                        if md5_tag == '0':
                            where_data = {
                                'id':task_id
                            }
                            update_data = {
                                'on_task':'0',
                                'status':'2',
                                'message':res_msg
                            }
                            im_sy_s.ImageSyncService().update_image_sync_task(update_data, where_data)
                            print('now sleep 1min to check again')
                            time.sleep(60)
                        #如果发现镜像非最新
                        else:
                            #获取后台wget的进程号并存入DB
                            image_info = im_s.ImageService().get_image_info(image_id)
                            image_url = image_info['url']
                            wget_pid_res,wget_pid,wget_pid_msg = ansibleCmdV2.get_wget_pid(host_ip,image_url)
                            if not wget_pid_res:
                                wget_pid = '0'
                            where_data = {
                                'id':task_id,
                            }
                            update_data = {
                                'process_id':wget_pid
                            }
                            im_sy_s.ImageSyncService().update_image_sync_task(update_data, where_data)
                            message = res_msg + '尝试时间为 %s' %get_datetime_str()
                            where_data = {
                                'id':task_id
                            }
                            update_data = {
                                'on_task':'1',
                                'status':'1',
                                'message':message
                            }
                            #将image_sync_task表的on_task置为1
                            im_sy_s.ImageSyncService().update_image_sync_task(update_data,where_data)
                            #将image_sync_schedule表对应的sch_state置为1
                            where_data = {
                                'id':sch_task_id
                            }
                            update_data = {
                                'sch_state':'1'
                            }
                            im_sy_sch.ImageSyncScheduleService().update_image_sync_sch(update_data,where_data)
                            print('now sleep 1min to check again')
                            time.sleep(60)
                    #wget下发不成功处理
                    else:
                        message = "wget 下发不成功,尝试时间为 %s" %get_datetime_str()
                        im_sy_s.update_wget_message(task_id,message)
                        # 每过10min尝试wget一次
                        wget_retry_tag = False
                        while not wget_retry_tag and datetime.strptime(get_datetime_str(), "%Y-%m-%d %X") < task_endtime:
                            time.sleep(600)
                            print 'befor wget_func'
                            print task_id
                            res_wget, res_msg,md5_tag = wget_func(host_ip, image_id, speed_limit,task_id,endtime,sch_task_id)
                            if res_wget:
                                wget_retry_tag = True
                                message = res_msg +'尝试时间为 %s' % get_datetime_str()
                            else:
                                message = "wget 下发不成功,尝试时间为 %s" % get_datetime_str()
                            im_sy_s.update_wget_message(task_id, message)
                        #如果重试成功,库状态更新
                        if  res_wget:
                            #如果镜像为最新
                            if md5_tag == '0':
                                where_data = {
                                    'id': task_id
                                }
                                update_data = {
                                    'on_task': '0',
                                    'status': '2',
                                    'message': res_msg
                                }
                                im_sy_s.ImageSyncService().update_image_sync_task(update_data, where_data)
                                print('now sleep 1min to check again')
                                time.sleep(60)
                            #如果镜像非最新
                            else:
                                where_data = {
                                    'id': task_id
                                }
                                update_data = {
                                    'on_task': '1',
                                    'status': '1'
                                }
                                # 更新task_sync_task表
                                im_sy_s.ImageSyncService().update_image_sync_task(update_data, where_data)
                                # 将image_sync_schedule表对应的sch_state置为1
                                where_data = {
                                    'id': sch_task_id
                                }
                                update_data = {
                                    'sch_state': '1'
                                }
                                im_sy_sch.ImageSyncScheduleService().update_image_sync_sch(update_data, where_data)
                                print('now sleep 1min to check again')
                                time.sleep(60)
                        #如果重试失败,库状态更新
                        else:
                            time.sleep(5)
                            where_data = {
                                'id': task_id
                            }
                            update_data = {
                                'on_task': '0',
                                'status': '3'
                            }
                            # 更新task_sync_task表
                            im_sy_s.ImageSyncService().update_image_sync_task(update_data, where_data)
                            # 将image_sync_schedule表对应的sch_state置为1
                            where_data = {
                                'id': sch_task_id
                            }
                            update_data = {
                                'sch_state': '3'
                            }
                            im_sy_sch.ImageSyncScheduleService().update_image_sync_sch(update_data, where_data)
                            print('now sleep 1min to check again')
                            time.sleep(60)






#获取当前任务的可执行时间区间
def get_task_worktime(task_id):
    task_num,task_data = im_sy_sch.get_ondo_sch_list(task_id)
    if task_num == 0:
        return False
    else:
        task_time_list = []
        for task_info in task_data:
            insert_data = {
                'task_starttime':task_info['sch_starttime'],
                'task_endtime':task_info['sch_endtime'],
                'id':task_info['id']
            }
            task_time_list.append(insert_data)
        return task_num,task_time_list


#时间比较函数
def Checktime(starttime,endtime,checktime):
    if starttime <= checktime and endtime >= checktime:
        Flag = True
    else:
        Flag = False
    return Flag




#生成wget下载脚本
def create_wget_sh(task_id,image_url,image_server,speed_limit_parm,time_left):
    wgetfilename = 'sync_task_' + str(task_id) + '.sh'
    wgetfiledir = DIR_DEFAULT + '/deploy/wgetdir/' + wgetfilename
    f = open(wgetfiledir, 'w')
    command1 = '#/bin/bash'
    f.write(command1)
    f.write('\n')
    command2 = 'cd /app/image;wget -c ' + speed_limit_parm +' ' + image_server + image_url + ' >/dev/null 2>&1 &'
    f.write(command2)
    f.write('\n')
    print command2
    comm3 = "ps -ef|grep wget|grep '%s'|awk '{print $2}'" %image_url
    kill_comm = 'sleep '+ time_left + ' && kill -9 `%s` &' %comm3
    print kill_comm
    f.write(kill_comm)
    f.write('\n')
    f.close()

#下发wget命令
def send_wget(host_ip,image_url,image_server,speed_limit_parm,check_dir,endtime,sch_task_id):
    #判断远端wget脚本文件是否存在，如不存在，则生成并拷贝过去
    print 'before wget_file_check'
    print sch_task_id
    check_wget_tag, check_wget_msg = ansibleCmdV2.wget_file_check(host_ip, sch_task_id)
    if not check_wget_tag:
        file_name = check_dir +'/deploy/wgetdir/sync_task_' + str(sch_task_id) + '.sh'
        check_local = os.path.exists(file_name)
        if not check_local:
            time_left = endtime - datetime.strptime(get_datetime_str(), "%Y-%m-%d %X")
            time_left_sec = time_left.seconds
            if int(time_left_sec) <0:
                time_left_sec = 0
            time_left_str = str(time_left_sec)
            create_wget_sh(sch_task_id, image_url, image_server, speed_limit_parm,time_left_str)
        send_wget_tag, send_wget_msg = ansibleCmdV2.send_wget_sh(host_ip, sch_task_id, check_dir)
        if not send_wget_tag:
            return False,send_wget_msg
    check_wget_tag, check_wget_msg = ansibleCmdV2.wget_file_check(host_ip, sch_task_id)
    if not check_wget_tag:
        return False,check_wget_msg
    #执行wget命令
    exec_wget_tag,exec_wget_msg = ansibleCmdV2.exec_wget_com(host_ip,sch_task_id)
    if not exec_wget_tag:
        return False,exec_wget_msg
    else:
        return True,exec_wget_msg


# 查看服务器是否可用
def _check_server_is_up(host_ip, host_port):
    """
    returns True if the given host is up and we are able to establish
    a connection using the given credentials.
    """
    try:
        socket_host = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_host.settimeout(0.5)
        socket_host.connect((host_ip, host_port))
        socket_host.close()
        return True
    except Exception as err:
        logging.info(err)
        return False

#返回镜像拷贝的server地址
def _confirm_image_copy_url(net_area_id):
    '''
        返回镜像拷贝地址
    :param speed_limit:
    :param host_s:
    :return:
    '''
    available_image_server = []
    available_cache_image_server = []
    # 通过net_area_id获取镜像服务器、镜像缓存服务器信息
    if not IMAGE_SERVER:
        _msg = 'can not find image server'
        logging.error(_msg)
        return False, _msg, ''
    elif len(IMAGE_SERVER) <= 0:
        _msg = 'can not find image server'
        logging.error(_msg)
        return False, _msg, ''

    for image_server in IMAGE_SERVER:
        if _check_server_is_up(image_server, IMAGE_SERVER_PORT):
            available_image_server.append(image_server)

    if len(available_image_server) == 0:
        _msg = 'can not find available image server'
        logging.error(_msg)
        return False, _msg, ''

    imagecache_data = imca_s.ImageCacheService().get_imagecache_info_by_net_area_id(net_area_id)
    if not imagecache_data:
        _msg = 'can not find image cache server'
        logging.error(_msg)
        return False, _msg, ''
    elif len(imagecache_data) <= 0:
        _msg = 'can not find image cache server'
        logging.error(_msg)
        return False, _msg, ''

    for image_cache_server in imagecache_data:
        if _check_server_is_up(image_cache_server['imagecache_ip'], NET_AREA_IMAGE_CACHE_SERVER_PORT):
            available_cache_image_server.append(image_cache_server['imagecache_ip'])

    if len(available_cache_image_server) == 0:
        _msg = 'can not find available image cache server'
        logging.error(_msg)
        return False, _msg, ''

    _image_server = 'http://' + available_image_server[0] + ':' + str(IMAGE_SERVER_PORT)
    _image_cache_server = 'http://' + available_cache_image_server[0] + ':' \
                          + str(NET_AREA_IMAGE_CACHE_SERVER_PORT)
    return True, _image_server, _image_cache_server


#下发wget
def wget_func(host_ip,image_id,speed_limit,task_id,endtime,sch_task_id):
    #比对镜像是否最新
    check_md5_tag,check_md5_msg = check_image_status(host_ip,task_id)
    if not check_md5_tag:
        print 'md5 check return######################################'
        print check_md5_msg
        return False,check_md5_msg,'1'
    else:
        #镜像为最新返回
        if check_md5_msg == '0':
            msg = '镜像为最新无需更新'
            return True,msg,'0'
        else:
            check_dir = DIR_DEFAULT
            image_info = im_s.ImageService().get_image_info(image_id)
            image_url = image_info['url']
            image_type = image_info['type']
            image_name = image_info['name']
            print 'in wget_func'
            print task_id
            wget_conf_tag,wget_conf_data = ansibleCmdV2.wget_confirm(host_ip,image_url)
            print 'wget_confirm_msg###########################################'
            print wget_conf_tag
            print wget_conf_data
            print 'done#################################'
            if not wget_conf_tag:
                message = wget_conf_data
                return False,message,'1'
            else:
                image_info = im_s.ImageService().get_image_info(image_id)
                image_url = image_info['url']
                speed_limit_parm = '--limit-rate ' + speed_limit + 'm'
                host_info = ho_s.HostService().get_host_info_by_hostip(host_ip)
                host_id =host_info['id']
                net_area_id_get = ho_s.get_host_net_area_id(host_id)
                net_area_id = net_area_id_get[0]['net_area_id']
                print type(net_area_id)
                print 'net area id is '
                print net_area_id
                res, image_server, image_cache_server = _confirm_image_copy_url(str(net_area_id))
                print 'get image server##########################'
                print res
                print image_server
                print image_cache_server
                print 'done##############################################'
                #获取镜像服务器和缓存服务器
                if not res:
                    return False,image_server,'1'
                # 如果后台没有wget命令在下载image，则下发ansible下载
                if wget_conf_data == '2':
                    print 'print wget parm#########################'
                    print host_ip
                    print speed_limit_parm
                    print image_url
                    print 'done###############################'
                    print 'before send_wget'
                    print task_id
                    send_wget_tag,send_message = send_wget(host_ip,image_url,image_server,speed_limit_parm,check_dir,endtime,sch_task_id)
                    return send_wget_tag,send_message,'1'
                #如果后台有wget命令在运行，判断是否为当前镜像
                else:
                    if wget_conf_data == str(image_type):
                        message = '后台已在下载任务镜像'
                        logging.info(message)
                        return True,message,'1'
                    else:
                        logging.info('后台未下载任务所需镜像，可下发')
                        send_wget_tag, send_message = send_wget(host_ip,image_url,image_server,speed_limit_parm,check_dir,endtime,sch_task_id)
                        return send_wget_tag,send_message,'1'



#检查镜像是否最新
def check_image_status(host_ip,task_id):
    task_info = im_sy_s.ImageSyncService().get_image_sync_info(task_id)
    image_id = task_info['image_id']
    image_info = im_s.ImageService().get_image_info(image_id)
    image_name = image_info['url'].split('/')[2]
    image_status_tag, checktag, checkmsg = image_status_check(image_name, host_ip)
    if not image_status_tag:
        return False,False
    else:
        #镜像最新返回'0'
        if checktag == '0':
            return True,'0'
        else:
            #镜像非最新返回'1'
            return True,'1'


#判断每个image是否为最新状态
def image_status_check(image_name,host_ip):
    image_dir = '/app/image/'+image_name
    check_file_exists,msg = ansibleCmdV2.check_file_exists(host_ip,image_dir)
    print 'remote image check result########################################'
    print check_file_exists,msg
    if check_file_exists:
        image_local_md5,message  = ansibleCmdV2.image_md5_get(host_ip,image_name)
        print 'local image md5 get result############################'
        print image_local_md5
        print message
        if not image_local_md5:
            return False,False,message
        else:
            res, image_data = im_s.ImageService().get_images_by_name_t(image_name)
            image_remote_md5 = image_data[0]['md5']
            print 'remote image md5########################'
            print image_remote_md5
            if image_local_md5 == image_remote_md5:
                message = "镜像为最新"
                return True,'0',message
            else:
                message = "镜像需更新"
                return True,'1',message
    else:
        message = "镜像需更新"
        return True, '1', message

#获取任务的结束时间
def get_task_endtime(task_id):
    task_num, task_data = im_sy_sch.get_ondo_sch_list(task_id)
    if task_num == 0:
        return False
    else:
        task_end_list = []
        for task_info in task_data:
            task_end_list.append(task_info['sch_endtime'])
        task_dead_time = max(task_end_list)
        return task_dead_time


if __name__ == '__main__':
   while True:
       image_sync_do_task()


