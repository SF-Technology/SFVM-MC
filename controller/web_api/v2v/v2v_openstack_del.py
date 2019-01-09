# coding=utf8
'''
    v2v_openstack_cancel
'''
# __author__ = 'anke'

from flask import request
from helper import json_helper
from service.v2v_task import v2v_task_service as v2v_op
from model.const_define import ErrorCode,IPStatus,v2vActions,VMCreateSource
from service.s_instance import instance_service as ins_s, instance_flavor_service as ins_f_s, \
    instance_group_service as ins_g_s, instance_host_service as ins_h_s,  \
    instance_ip_service as ins_ip_s, instance_disk_service as ins_d_s
from helper.time_helper import get_datetime_str
from service.s_ip import ip_service as ip_s
from service.v2v_task import v2v_instance_info as v2v_in_i
import logging




def v2v_openstack_del():

    #获取入参信息
    delete = request.values.get('delete')
    request_his = request.values.get('request_id')
    source = v2v_op.v2vTaskService().get_v2v_task_by_requestid(request_his)['source']

    if not source:
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg='v2v来源缺失')

    if delete != '1' :
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg='参数错误')

    #判断当前任务是否完成
    data,message  = v2v_op.get_v2v_deleteable(request_his)
    if data != '2':
        return_msg = message
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg=return_msg)
    else:
        if source == VMCreateSource.OPENSTACK:
            del_res,del_msg = del_action(request_his)
            if del_res == False:
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=del_msg)
        else:
            tag,errmsg = esx_del_action(request_his)
            if not tag:
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=errmsg)

        v2v_task = v2v_op.v2vTaskService().get_v2v_task_by_requestid(request_his)
        v2v_vm_uuid = v2v_task['vm_uuid']
        #更新instance表
        instance_info = ins_s.InstanceService().get_instance_info_by_uuid(v2v_vm_uuid)
        instance_id = instance_info['id']
        update_data = {
            'isdeleted': '1',
            'deleted_at': get_datetime_str()
        }
        where_data = {
            'id': instance_id
        }
        ret = ins_s.InstanceService().update_instance_info(update_data, where_data)
        if ret != 1:
            logging.error('删除instance %s 错误', instance_id)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='删除instance错误')

        # instance_flavor
        ret_f = ins_f_s.InstanceFlavorService().delete_instance_flavor(instance_id)
        if ret_f != 1:
            logging.error('delete instance %s flavor error', instance_id)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='删除instance flavor错误')

        # instance_group
        ret_g = ins_g_s.InstanceGroupService().delete_instance_group_info(instance_id)
        if ret_g != 1:
            logging.error('delete instance %s group error', instance_id)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='删除instance group错误')

        # instance_host
        update_data_h = {
            'isdeleted': '1',
            'deleted_at': get_datetime_str()
        }
        where_data_h = {
            'instance_id': instance_id
        }
        ret_h = ins_h_s.InstanceHostService().update_instance_host_info(update_data_h, where_data_h)
        if ret_h != 1:
            logging.error('delete instance %s host error', instance_id)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='删除instance host错误')

        # instance_disk
        update_data_d = {
            'isdeleted': '1',
            'deleted_at': get_datetime_str()
        }
        where_data_d = {
            'instance_id': instance_id
        }
        ret_d = ins_d_s.InstanceDiskService().update_instance_disk_info(update_data_d, where_data_d)
        if ret_d != 1:
            logging.error('delete instance %s disk error', instance_id)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='删除instance disk错误')

        # instance_ip
        update_data_ip = {
            'isdeleted': '1',
            'deleted_at': get_datetime_str()
        }
        where_data_ip = {
            'instance_id': instance_id
        }
        ret_i_ip = ins_ip_s.InstanceIPService().update_instance_ip_info(update_data_ip, where_data_ip)
        if ret_i_ip != 1:
            logging.error('delete instance %s ip error', instance_id)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='删除instance ip错误')

        #更新v2v_instance_info
        update_data = {
            'isdeleted':'1',
            'deleted_at':get_datetime_str()
        }
        where_data ={
            'instance_id':instance_id
        }
        ret_v2v_in_i = v2v_in_i.v2vInstanceinfo().update_v2v_status(update_data,where_data)
        if ret_v2v_in_i != 1:
            logging.error('delete v2v instance info error')
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='删除v2v instance info错误')

        # 删除vm的ip
        ip_data = ins_s.get_ip_of_instance(instance_id)
        ip_id = ip_data['id']
        if ip_data:
            ip_s.del_ip_info(ip_id)


        #更新v2v_task表
        where_v2v = {
            'request_id':request_his
        }
        update_v2v = {
            'destory':'1'
        }
        v2v_op.v2vTaskService().update_v2v_status(update_v2v,where_v2v)

        return json_helper.format_api_resp(code=ErrorCode.SUCCESS, msg='删除v2v任务完成')



#任务删除相关操作
def del_action(request_id):
    request_his =request_id
    v2v_task = v2v_op.v2vTaskService().get_v2v_task_by_requestid(request_his)
    dest_host = v2v_task['dest_host']
    dest_dir = v2v_task['dest_dir']
    vm_name =v2v_task['vm_name']
    vm_ip = v2v_task['vm_ip']
    vmuuid = v2v_task['vm_uuid']
    step_done = v2v_op.get_v2v_step(request_his)
    if step_done == v2vActions.COPY_VM_DISK or step_done == v2vActions.CREATE_DEST_DIR or step_done == v2vActions.CREATE_STOR_POOL \
        or step_done == v2vActions.GET_VM_FILE or step_done == v2vActions.COPY_VM_XML or step_done == v2vActions.VM_STANDARDLIZE:
        res,res_data = v2v_op.del_vm_folder(dest_host,dest_dir,vm_name,vmuuid)
        if res == False:
            msg = '删除vm路径失败'
            return False,msg
        else:
            msg = "删除vm路径成功"
            return True,msg
    elif step_done == v2vActions.VM_DEFINE or step_done == v2vActions.VM_START:
        res1, res1_data = v2v_op.del_vm(dest_host, vm_name)
        if res1 == False:
            msg = '删除vm失败'
            return False, msg
        else:
            res2,res2_data = v2v_op.del_vm_folder(dest_host,dest_dir,vm_name,vmuuid)
            if res2 == False:
                msg = '删除vm路径失败'
                return False, msg
            else:
                msg = "删除vm路径成功"
                return True, msg
    else:
        msg = '删除操作完成'
        return True,msg


def esx_del_action(request_id):
    step_done = v2v_op.v2vTaskService().get_v2v_task_by_requestid(request_id)["step_done"]
    dest_host = v2v_op.v2vTaskService().get_v2v_task_by_requestid(request_id)["dest_host"]
    dest_dir = v2v_op.v2vTaskService().get_v2v_task_by_requestid(request_id)["dest_dir"]
    vm_name = v2v_op.v2vTaskService().get_v2v_task_by_requestid(request_id)["vm_name"]
    vmuuid = v2v_op.v2vTaskService().get_v2v_task_by_requestid(request_id)["vm_uuid"]
    vmware_vm = v2v_op.v2vTaskService().get_v2v_task_by_requestid(request_id)["vmware_vm"]
    step_done_int = int(step_done)
    if step_done_int == 0:
        msg = "已完成"
        return True,msg
    elif step_done_int == 1 :
        tag,msg = v2v_op.del_vm_folder(dest_host, dest_dir, vmware_vm,vmuuid)
        if tag:
            return True,msg
        else:
            return False,msg
    elif step_done_int >= 2 and step_done_int <= 7:
        tag, msg = v2v_op.esx_del_vm_folder(dest_host, dest_dir, vm_name, vmuuid,vmware_vm)
        if not tag:
            return False,msg
        else:
            tag,msg = v2v_op.esx_del_tmp_folder(dest_host,vmware_vm)
            if tag:
                return True,msg
            else:
                return False,msg
    elif step_done_int >=8:
        tag,msg = v2v_op.del_vm(dest_host,vm_name)
        if not tag:
            return  False,msg
        else:
            tag,msg = v2v_op.esx_del_vm_folder(dest_host, dest_dir, vm_name, vmuuid,vmware_vm)
            if tag:
                return True,msg
            else:
                return False,msg








































