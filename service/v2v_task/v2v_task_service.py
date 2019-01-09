# coding=utf8
'''
    v2v_任务查 看
'''
# __author__ =  ""
from lib.shell.ansibleCmdV2 import ansible_run_shell
from model import v2v_task
from lib.vrtManager.util import randomUUID
from time_helper import get_datetime_str
from lib.other import fileLock
import random
from config.default import OPENSTACK_DEV_PASS,OPENSTACK_SIT_PASS,KVMHOST_LOGIN_PASS,\
    KVMHOST_SU_PASS,ANSIABLE_REMOTE_USER,OPENSTACK_DEV_USER,OPENSTACK_SIT_USER
from helper.encrypt_helper import decrypt
import time
from lib.dbs.mysql import Mysql

class v2vTaskService:
    def __init__(self):
        self.v2v_task_db = v2v_task.v2vTask(db_flag='kvm', table_name='v2v_task')

    def add_v2v_task_info(self, insert_data):
        return self.v2v_task_db.insert(insert_data)

    def query_data(self, **params):
        return self.v2v_task_db.simple_query(**params)

    def update_v2v_status(self, update_data, where_data):
        return self.v2v_task_db.update(update_data, where_data)

    def get_v2v_retry(self,request_id):
        '''
            获取目标vm是否在v2v任务中
        :param :
        :return:
        '''
        params = {
            'WHERE_AND': {
                "=": {
                    'destory': '0',
                    'request_id':request_id,
                    'status':'2'
                }
            },
        }
        return self.v2v_task_db.simple_query(**params)

    def get_v2v_task_by_requestid(self,requestid):
        return self.v2v_task_db.get_one('request_id', requestid)



def get_v2v_todo():
    params = {
        'cancel':'0',
        'status':0
    }
    task_num,task_data = v2vTaskService().query_data(**params)
    if task_num > 0:
        return task_data


def generate_req_id():
        '''
                获取任务ID
            :return:
            '''
        return 'req-' + randomUUID()

def update_v2v_actions(request_id, status):
    '''
     更新v2v任务状态
    '''
    update_data = {
        'status': status,
        'finish_time': get_datetime_str()
    }
    where_data = {
        'request_id': request_id,
    }
    ret = v2vTaskService().update_v2v_status(update_data, where_data)
    if ret > 0:
        return True
    return False

def update_v2v_step(request_id,step):
    '''
    更新任务的步骤信息
    :param request_id:
    :param step:
    :return:
    '''
    update_data ={
        'step_done':step
    }

    where_data = {
        'request_id':request_id
    }
    ret = v2vTaskService().update_v2v_status(update_data, where_data)
    if ret > 0:
        return True
    return False

def up_esxv2v_vlist(request_id,vlist):
    '''
    更新任务的步骤信息
    :param request_id:
    :param step:
    :return:
    '''
    update_data ={
        'volumelist':vlist
    }

    where_data = {
        'request_id':request_id
    }
    ret = v2vTaskService().update_v2v_status(update_data, where_data)
    if ret > 0:
        return True
    return False

def update_v2v_destdir(request_id,dir):
    '''
        更新任务的vm路径
        :param request_id:
        :param dir:
        :return:
        '''
    update_data = {
        'dest_dir': dir
    }

    where_data = {
        'request_id': request_id
    }
    ret = v2vTaskService().update_v2v_status(update_data, where_data)
    if ret > 0:
        return True
    return False

def update_v2v_desthost(request_id,host):
    '''
        更新任务的目标kvmhost
        :param request_id:
        :param host:
        :return:
        '''
    update_data = {
        'dest_host': host
    }

    where_data = {
        'request_id': request_id
    }
    ret = v2vTaskService().update_v2v_status(update_data, where_data)
    if ret > 0:
        return True
    return False

def updata_v2v_cancel(request_id,cancel,status):
    '''
            更新任务的目标kvmhost
            :param request_id:
            :param host:
            :return:
            '''
    update_data = {
        'cancel':cancel,
        'status':status
    }

    where_data = {
        'request_id': request_id
    }
    ret = v2vTaskService().update_v2v_status(update_data, where_data)
    if ret > 0:
        return True
    return False

def updata_v2v_retry(request_id,status):
    '''
            retry则更新status的值为0
            :param request_id:
            :param retry:
            :return:
            '''
    update_data = {
        'status': status,
        'message':'正在重试',
        'start_time':get_datetime_str(),
        'finish_time':None
    }

    where_data = {
        'request_id': request_id
    }
    ret = v2vTaskService().update_v2v_status(update_data, where_data)
    if ret > 0:
        return True
    return False

def updata_v2v_status(request_id,status):
    '''
            更新任务的目标kvmhost
            :param request_id:
            :param host:
            :return:
            '''
    update_data = {
        'status': status
    }

    where_data = {
        'request_id': request_id
    }
    ret = v2vTaskService().update_v2v_status(update_data, where_data)
    if ret > 0:
        return True
    return False

def updata_v2v_ontask(request_id,ontask):
    '''
            更新任务的目标kvmhost
            :param request_id:
            :param host:
            :return:
            '''
    update_data = {
        'on_task': ontask
    }

    where_data = {
        'request_id': request_id
    }
    ret = v2vTaskService().update_v2v_status(update_data, where_data)
    if ret > 0:
        return True
    return False

def updata_v2v_ncport(request_id,ncport):
    '''

            '''
    update_data = {
        'port': ncport
    }

    where_data = {
        'request_id': request_id
    }
    ret = v2vTaskService().update_v2v_status(update_data, where_data)
    if ret > 0:
        return True
    return False

def updata_v2v_message(request_id,message):
    '''
            更新任务的目标kvmhost
            :param request_id:
            :param host:
            :return:
            '''
    update_data = {
        'message': message
    }

    where_data = {
        'request_id': request_id
    }
    ret = v2vTaskService().update_v2v_status(update_data, where_data)
    if ret > 0:
        return True
    return False

def get_v2v_desthost(request_id):
    params = {
        'WHERE_AND': {
            '=': {
                'request_id': request_id
            },
        },
    }

    total_nums, data = v2vTaskService().query_data(**params)
    if total_nums >0:
        desthost = data[0]['dest_host']
        return desthost
    else:
        return False

def get_v2v_destdir(request_id):
    params = {
        'WHERE_AND': {
            '=': {
                'request_id': request_id
            },
        },
    }
    total_nums, data = v2vTaskService().query_data(**params)
    if total_nums > 0:
        destdir = data[0]['dest_dir']
        return destdir
    else:
        return False

def get_v2v_ncport(request_id):
    params = {
        'WHERE_AND': {
            '=': {
                'request_id': request_id
            },
        },
    }
    total_nums, data = v2vTaskService().query_data(**params)
    if total_nums > 0:
        port = data[0]['port']
        return port
    else:
        return False


def get_v2v_running_by_reqid(request_id):
    params = {
        'WHERE_AND': {
            '=': {
                'request_id': request_id,
            },
        },
    }
    total_nums, data = v2vTaskService().query_data(**params)
    if data[0]['status'] == 0 and data[0]['on_task'] == '0':
        return True
    else:
        return False


def get_v2v_step(request_id):
    params = {
        'WHERE_AND': {
            '=': {
                'request_id': request_id
            },
        },
    }
    total_nums, data = v2vTaskService().query_data(**params)
    if total_nums > 0:
        step_done = data[0]['step_done']
        return step_done
    else:
        return False

def get_v2v_retryable(request_id):
    params = {
        'WHERE_AND': {
            '=': {
                'request_id': request_id
            },
        },
    }
    total_nums, data = v2vTaskService().query_data(**params)
    if total_nums > 0:
        status = data[0]['status']
        if status == 2 or status == 3:
            return True
        else:
            return False
    else:
        return False

def get_v2v_deleteable(request_id):
    params = {
        'WHERE_AND': {
            '=': {
                'request_id': request_id
            },
        },
    }
    total_nums, data = v2vTaskService().query_data(**params)
    if total_nums > 0:
        status = data[0]['status']
        if status == 0:
            message = "任务正在进行,请先取消"
            data = '0'
            return data,message
        elif status == 1:
            message = "任务已完成,无法操作"
            data = '1'
            return data,message
        elif status == 2 or status == 3:
            message = "任务可删除"
            data = '2'
            return data,message



    else:
        message = "找不到请求的任务"
        data = '-10000'
        return data,message

@fileLock.file_lock('v2v_port_lock')
def v2v_ncport(request_id):
     i=1
     while i< 1000:
         randport = random.randint(10001,10999)
         randport = str(randport)
         rand_res = get_v2v_nc_onuse(randport)
         if rand_res == True:
             updata_v2v_ncport(request_id,randport)
             return randport
         else:
             i += 1


def get_v2v_nc_onuse(port):
    params = {
        'WHERE_AND': {
            '=': {
                'port': port,
                'status':'0'
            },
        },
    }

    total_nums, data = v2vTaskService().query_data(**params)
    if total_nums > 0:
        return False
    else:
        return True


#删除vm
def del_vm(dest_host,vmname):
    command1 = 'virsh destroy ' + vmname
    command = 'virsh  undefine '+ vmname
    r_user = ANSIABLE_REMOTE_USER
    r_pass = decrypt(KVMHOST_LOGIN_PASS)
    b_user = OPENSTACK_DEV_USER
    b_pass = decrypt(KVMHOST_SU_PASS)
    res1 = ansible_run_shell(dest_host,command1)
    if res1['contacted'] == {}:
        msg = "连接目标kvmhost失败"
        return False,msg
    else:
        time.sleep(3)
        delvm_res = ansible_run_shell(dest_host,command)
        if 'contacted' not in delvm_res:
            msg = "连接目标kvmhost失败"
            return False, msg
        elif delvm_res['contacted'] == {}:
            msg = "连接目标kvmhost失败"
            return False,msg
        elif 'failed' in delvm_res['contacted'][dest_host]:
            msg = "删除目标vm失败"
            return False,msg
        else:
            msg = "目标VM已删除"
            return True,msg

#清空目标vm目录
def del_vm_folder(dest_host,dest_dir,vm_ip,vmuuid):
    if dest_dir == '/app/image/' or dest_dir == '/app/image':
        msg = "目标VM路径无效"
        return  False,msg
    else:
        command_check = 'ls ' + dest_dir
        r_user = ANSIABLE_REMOTE_USER
        r_pass = decrypt(KVMHOST_LOGIN_PASS)
        b_user = OPENSTACK_DEV_USER
        b_pass = decrypt(KVMHOST_SU_PASS)
        folder_check = ansible_run_shell(dest_host,command_check)
        if 'contacted' not in folder_check:
            msg = "连接目标kvmhost失败"
            return False, msg
        elif folder_check['contacted'] == {}:
            msg = "连接目标kvmhost失败"
            return False, msg
        elif 'failed' in folder_check['contacted'][dest_host]:
            msg = "vm存储路径获取失败"
            return False, msg
        else:
            comand_rm = 'cd '+ dest_dir + ';rm -f '+ vm_ip + '*;rm -f *.xml'
            folder_rm  = ansible_run_shell(dest_host,comand_rm)
            if folder_rm['contacted'] == {}:
                msg = "连接目标kvmhost失败"
                return False, msg
            elif 'failed' in folder_rm['contacted'][dest_host]:
                msg = "删除vm文件失败"
                return False, msg
            else:
                command_rmdir = 'rmdir '+ dest_dir
                dir_rm = ansible_run_shell(dest_host,command_rmdir)
                if dir_rm['contacted'] == {}:
                    msg = "连接目标kvmhost失败"
                    return False, msg
                elif 'failed' in dir_rm['contacted'][dest_host]:
                    msg = "删除vm路径失败"
                    return False, msg
                else:
                    rm_pool = 'virsh pool-destroy '+ vmuuid + ";virsh pool-undefine " + vmuuid
                    ansible_run_shell(dest_host, rm_pool)
                    msg = "目标路径已删除"
                    return True,msg

def op_retry_del_vm_folder(dest_host, dest_dir, vm_ip, vmuuid):
    if dest_dir == '/app/image/' or dest_dir == '/app/image':
        msg = "目标VM路径无效"
        return False, msg
    else:
        command_check = 'ls ' + dest_dir
        r_user = ANSIABLE_REMOTE_USER
        r_pass = decrypt(KVMHOST_LOGIN_PASS)
        b_user = OPENSTACK_DEV_USER
        b_pass = decrypt(KVMHOST_SU_PASS)
        folder_check = ansible_run_shell(dest_host, command_check)
        if 'contacted' not in folder_check:
            msg = "连接目标kvmhost失败"
            return False, msg
        elif folder_check['contacted'] == {}:
            msg = "连接目标kvmhost失败"
            return False, msg
        elif 'failed' in folder_check['contacted'][dest_host]:
            msg = "vm存储路径获取失败"
            return False, msg
        else:
            comand_rm = 'cd ' + dest_dir + ';rm -f ' + vm_ip + '*;rm -f *.xml'
            folder_rm = ansible_run_shell(dest_host, comand_rm)
            if folder_rm['contacted'] == {}:
                msg = "连接目标kvmhost失败"
                return False, msg
            elif 'failed' in folder_rm['contacted'][dest_host]:
                msg = "删除vm文件失败"
                return False, msg
            else:
                msg = "残余文件已清除"
                return True, msg

# esx_v2v清空目标vm目录
def esx_del_vm_folder(dest_host, dest_dir, vm_ip, vmuuid,vmware_vm):
    if dest_dir == '/app/image/' or dest_dir == '/app/image':
        msg = "目标VM路径无效"
        return False, msg
    else:
        command_check = 'ls ' + dest_dir
        r_user = ANSIABLE_REMOTE_USER
        r_pass = decrypt(KVMHOST_LOGIN_PASS)
        b_user = OPENSTACK_DEV_USER
        b_pass = decrypt(KVMHOST_SU_PASS)
        folder_check = ansible_run_shell(dest_host, command_check)
        if 'contacted' not in folder_check:
            msg = "连接目标kvmhost失败"
            return False, msg
        elif folder_check['contacted'] == {}:
            msg = "连接目标kvmhost失败"
            return False, msg
        elif 'failed' in folder_check['contacted'][dest_host]:
            msg = "vm存储路径获取失败"
            return False, msg
        else:
            comand_rm = 'cd ' + dest_dir + ';rm -f ' + vm_ip + '*;rm -f *.xml;rm -f ' +vmware_vm +'*'
            folder_rm = ansible_run_shell(dest_host, comand_rm)
            if folder_rm['contacted'] == {}:
                msg = "连接目标kvmhost失败"
                return False, msg
            elif 'failed' in folder_rm['contacted'][dest_host]:
                msg = "删除vm文件失败"
                return False, msg
            else:
                command_rmdir = 'rmdir ' + dest_dir
                dir_rm = ansible_run_shell(dest_host, command_rmdir)
                if dir_rm['contacted'] == {}:
                    msg = "连接目标kvmhost失败"
                    return False, msg
                elif 'failed' in dir_rm['contacted'][dest_host]:
                    msg = "删除vm路径失败"
                    return False, msg
                else:
                    rm_pool = 'virsh pool-destroy ' + vmuuid + ";virsh pool-undefine " + vmuuid
                    ansible_run_shell(dest_host, rm_pool)
                    msg = "目标路径已删除"
                    return True, msg

def esx_retry_del_vm_folder(dest_host, dest_dir, vm_name, vmware_vm):
    if dest_dir == '/app/image/' or dest_dir == '/app/image':
        msg = "目标VM路径无效"
        return False, msg
    else:
        command_check = 'ls ' + dest_dir
        r_user = ANSIABLE_REMOTE_USER
        r_pass = decrypt(KVMHOST_LOGIN_PASS)
        b_user = OPENSTACK_DEV_USER
        b_pass = decrypt(KVMHOST_SU_PASS)
        folder_check = ansible_run_shell(dest_host, command_check)
        if 'contacted' not in folder_check:
            msg = "连接目标kvmhost失败"
            return False, msg
        elif folder_check['contacted'] == {}:
            msg = "连接目标kvmhost失败"
            return False, msg
        elif 'failed' in folder_check['contacted'][dest_host]:
            msg = "vm存储路径获取失败"
            return False, msg
        else:
            comand_rm = 'cd ' + dest_dir + ';rm -f ' + vm_name + '*;rm -f *.xml;rm -f ' + vmware_vm + '*'
            folder_rm = ansible_run_shell(dest_host, comand_rm)
            if folder_rm['contacted'] == {}:
                msg = "连接目标kvmhost失败"
                return False, msg
            elif 'failed' in folder_rm['contacted'][dest_host]:
                msg = "删除vm文件失败"
                return False, msg
            else:
                msg = "目标路径已删除"
                return True, msg


#esx v2v清空临时目录
def esx_del_tmp_folder(dest_host,vmware_vm):
        r_user = ANSIABLE_REMOTE_USER
        r_pass = decrypt(KVMHOST_LOGIN_PASS)
        b_user = OPENSTACK_DEV_USER
        b_pass = decrypt(KVMHOST_SU_PASS)
        dest_dir = '/app/tmp/'+ vmware_vm
        comand_rm = 'cd '+ dest_dir + ';rm -f '+ vmware_vm + '*;rm -f *.xml'
        folder_rm  = ansible_run_shell(dest_host,comand_rm)
        if 'contacted' not in folder_rm:
            msg = "连接目标kvmhost失败"
            return False, msg
        elif folder_rm['contacted'] == {}:
            msg = "连接目标kvmhost失败"
            return False, msg
        elif 'failed' in folder_rm['contacted'][dest_host]:
            msg = "删除vm文件失败"
            return False, msg
        else:
            command_rmdir = 'rmdir '+ dest_dir
            dir_rm = ansible_run_shell(dest_host,command_rmdir)
            if dir_rm['contacted'] == '{}':
                msg = "连接目标kvmhost失败"
                return False, msg
            else:
                msg = "目标路径已删除"
                return True, msg


def v2v_task_list(**kwargs):
    ins = Mysql.get_instance("kvm")
    db_conn = ins.get_connection()
    args = []
    sql = '''
            SELECT
                v2v_task.vm_ip,
                v2v_task.request_id,
                v2v_task.start_time,
                v2v_task.finish_time,
                v2v_task.status,
                u.username,
                v2v_task.step_done,
                v2v_task.message,
                v2v_task.source,
                v2v_task.vm_ostype
            FROM
                v2v_task
            LEFT JOIN
                tb_user u ON u.userid = v2v_task.user_id
            where v2v_task.destory = '0'
            '''
    sql += '''
            GROUP BY v2v_task.id
            ORDER BY v2v_task.id DESC
        '''

    # 计算总数  用于分页使用
    total_data = ins.query(db_conn, sql, args)
    total_nums = len(total_data)

    if kwargs.get('page_no') and kwargs.get('page_size'):
        page_no = int(kwargs['page_no'])
        page_size = kwargs['page_size']
        limit_sql = ' LIMIT %d, %d' % ((int(page_no) - 1) * int(page_size), int(page_size))
        sql += limit_sql

    data = ins.query(db_conn, sql, args)
    return total_nums, data

