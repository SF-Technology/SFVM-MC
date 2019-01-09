# coding=utf8
'''
    v2v_openstack_retry
'''
# __author__ = 'anke'

from flask import request
from helper import json_helper
from service.v2v_task import v2v_task_service as v2v_op
from service.s_instance_action import instance_action as in_a_s
from model.const_define import ErrorCode,v2vActions,VMCreateSource

def v2v_openstack_retry():

    #获取入参信息
    retry = request.values.get('retry')
    request_his = request.values.get('request_id')
    source = v2v_op.v2vTaskService().get_v2v_task_by_requestid(request_his)['source']

    if not source:
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg='v2v来源缺失')

    if retry != '1':
        return json_helper.format_api_resp(code=ErrorCode.PARAM_ERR, msg='参数错误')

    #判断当前任务是否可重试
    res_task = v2v_op.get_v2v_retryable(request_his)
    if not res_task:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='任务状态无法重试')
    else:
        if source == VMCreateSource.OPENSTACK:
            res_t,res_msg = openstack_retry_action(request_his)
            if not res_t:
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=res_msg)
        else:
            res_e,res_emsg = esx_retry_action(request_his)
            if not res_e:
                return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=res_emsg)

        up_sta = v2v_op.updata_v2v_retry(request_his,0)
        if up_sta == True:
            return json_helper.format_api_resp(code=ErrorCode.SUCCESS, msg='重试下发成功')
        else:
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='重试下发失败')


def openstack_retry_action(request_id):
    v2v_task = v2v_op.v2vTaskService().get_v2v_task_by_requestid(request_id)
    step_done = v2v_task['step_done']
    dest_host = v2v_task['dest_host']
    dest_dir = v2v_task['dest_dir']
    vm_name = v2v_task['vm_name']
    vm_uuid = v2v_task['vm_uuid']
    if step_done == v2vActions.GET_VM_FILE :
        res,res_msg = v2v_op.op_retry_del_vm_folder(dest_host,dest_dir,vm_name,vm_uuid)
        if res == False:
            msg = "删除下载文件失败"
            return False,msg
        else:
            msg = "删除下载文件成功"
            return True,msg
    else:
        msg = "done"
        return  True,msg

def esx_retry_action(request_id):
    v2v_task = v2v_op.v2vTaskService().get_v2v_task_by_requestid(request_id)
    step_done = v2v_task['step_done']
    dest_host = v2v_task['dest_host']
    dest_dir = v2v_task['dest_dir']
    vm_name = v2v_task['vm_name']
    vmware_vm = v2v_task['vmware_vm']
    if int(step_done) >= 3 and int(step_done) < 5:
        tag,message = v2v_op.esx_retry_del_vm_folder(dest_host, dest_dir, vm_name, vmware_vm)
        if not tag:
            return False, message
        return True, message
    else:
        message = 'done'
        return True, message
