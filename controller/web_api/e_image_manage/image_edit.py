# coding=utf8
'''
    镜像开机编辑服务
'''

from flask import request
from helper import json_helper
from helper.time_helper import get_datetime_str
import image_manage_action as im_man_act
from model.const_define import ErrorCode, ImageManage
from service.s_image import image_service as im_s
from service.s_ip import segment_service as segment_s
from model.const_define import image_manage_action as im_m_act, image_mange_action_state as im_m_act_sta, img_tmp_status
import sys
#from lib.websocket.my_socket import socketio
#from flask_socketio import emit
sys.setdefaultencoding('utf-8')


def image_edit():
    eimage_name = request.values.get('image_name')
    if not eimage_name:
        # message =  {
        #     'code': ErrorCode.SYS_ERR,
        #     'msg': "入参缺失"
        # }
        # socketio.emit('image_edit_resp', message, namespace='/image_edit_return')
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='入参缺失')

    # 判断当前image状态是否正常
    image_manage_data = im_s.ImageManageService().get_img_manage_data_by_name(eimage_name)
    image_manage_stat = image_manage_data[1]["status"]
    image_manage_type = image_manage_data[1]["os_type"]
    image_manage_osver = image_manage_data[1]["version"]
    enable_stat = [ImageManage.INIT, ImageManage.CHECKOUT, ImageManage.USABLE]
    if image_manage_stat not in enable_stat:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='当前模板机状态不允许此操作')

    # template vm start
    ret, message = im_man_act._img_tem_start(eimage_name)
    update_action = im_m_act.START_VEM
    if not ret:
        state_tag = im_m_act_sta.FAILED
        im_s.ImageStatusService().add_image_status_action(eimage_name, update_action, state_tag, message)
        im_s.ImageManageService().update_image_manage_msg(eimage_name, message)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=message)
    else:
        state_tag = im_m_act_sta.SUCCESSED
        im_s.ImageStatusService().add_image_status_action(eimage_name, update_action, state_tag, message)

    # update template vm stat
    update_data = {
        'template_status':img_tmp_status.RUNNING
    }
    where_data = {
        'eimage_name':eimage_name
    }
    im_s.ImageManageService().update_image_info(update_data, where_data)

    # template vm inject ip
    ret, res_data = im_s.ImageManageService().get_img_manage_data_by_name(eimage_name)
    update_action = im_m_act.IP_INJECT
    if not ret:
        state_tag = im_m_act_sta.FAILED
        error_msg = res_data
        im_s.ImageStatusService().add_image_status_action(eimage_name, update_action, state_tag, error_msg)
        im_s.ImageManageService().update_image_manage_msg(eimage_name, message)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='获取镜像信息失败')
    ip_address = res_data['template_vm_ip']
    segment_data = segment_s.SegmentService().get_segment_for_img_tmp()
    if not segment_data:
        error_msg = '获取镜像模板专用网段失败'
        state_tag = im_m_act_sta.FAILED
        im_s.ImageStatusService().add_image_status_action(eimage_name, update_action, state_tag, error_msg)
        im_s.ImageManageService().update_image_manage_msg(eimage_name, message)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='获取镜像模板专用网段失败')
    netmask_int = int(segment_data['netmask'])
    netmask = exchange_maskint(netmask_int)
    gateway = segment_data['gateway_ip']
    dns1 = segment_data['dns1']
    dns2 = segment_data['dns2']
    res, message = im_man_act._img_tem_inject(eimage_name, ip_address, netmask, gateway, image_manage_type,
                                              image_manage_osver, dns1, dns2)
    update_action = im_m_act.IP_INJECT
    if not res:
        error_msg = message
        state_tag = im_m_act_sta.FAILED
        im_s.ImageStatusService().add_image_status_action(eimage_name, update_action, state_tag, error_msg)
        im_s.ImageManageService().update_image_manage_msg(eimage_name, message)
        msg = '模板机%s 初始化注入失败' % eimage_name
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=msg)
    else:
        state_tag = im_m_act_sta.SUCCESSED
        im_s.ImageStatusService().add_image_status_action(eimage_name, update_action, state_tag, message)
    # 更新template_status
    message = ''
    im_s.ImageManageService().update_image_manage_status(eimage_name, message, ImageManage.EDITING)
    message = '模板机%s 开机编辑成功' % eimage_name
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, msg=message)


# 根据子网掩码位数计算子网掩码值
def exchange_maskint(mask_int):
  bin_arr = ['0' for i in range(32)]
  for i in range(mask_int):
    bin_arr[i] = '1'
  tmpmask = [''.join(bin_arr[i * 8:i * 8 + 8]) for i in range(4)]
  tmpmask = [str(int(tmpstr, 2)) for tmpstr in tmpmask]
  return '.'.join(tmpmask)

