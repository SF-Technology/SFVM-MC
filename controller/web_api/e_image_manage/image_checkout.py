# coding=utf8
'''
    关机生成镜像
'''
# __author__ =  ""
from flask import request
from helper import json_helper
import image_manage_action as im_man_act
from model.const_define import ErrorCode, ImageManage
from service.s_image import image_service as im_s
from model.const_define import image_manage_action as im_m_act, image_mange_action_state as im_m_act_sta, img_tmp_status
import sys
sys.setdefaultencoding('utf-8')


def image_checkout():
    eimage_name = request.values.get('image_name')
    if not eimage_name:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='入参缺失')

    # 判断当前image状态是否正常
    image_manage_data = im_s.ImageManageService().get_img_manage_data_by_name(eimage_name)
    os_type = image_manage_data[1]["os_type"]
    image_manage_stat = image_manage_data[1]["status"]
    if image_manage_stat != ImageManage.EDITING:
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg='当前模板机状态不允许此操作')

    # template vm remove ip
    update_action = im_m_act.IP_REMOVE
    ret, message = im_man_act.img_tem_rm_ip(eimage_name, os_type)
    if not ret:
        state_tag = im_m_act_sta.FAILED
        im_s.ImageStatusService().add_image_status_action(eimage_name, update_action, state_tag, message)
        im_s.ImageManageService().update_image_manage_msg(eimage_name, message)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=message)
    else:
        state_tag = im_m_act_sta.SUCCESSED
        im_s.ImageStatusService().add_image_status_action(eimage_name, update_action, state_tag, message)

    # template vm shutdown
    update_action = im_m_act.VEM_SHUTDOWN
    ret, message = im_man_act._img_tem_shutdown(eimage_name)
    if not ret:
        state_tag = im_m_act_sta.FAILED
        im_s.ImageStatusService().add_image_status_action(eimage_name, update_action, state_tag, message)
        im_s.ImageManageService().update_image_manage_msg(eimage_name, message)
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=message)
    else:
        state_tag = im_m_act_sta.SUCCESSED
        im_s.ImageStatusService().add_image_status_action(eimage_name, update_action, state_tag, message)

    # 更新template vm状态为关机
    update_data = {
        'template_status': img_tmp_status.SHUTDOWN
    }
    where_data = {
        'eimage_name': eimage_name
    }
    im_s.ImageManageService().update_image_info(update_data, where_data)

    # 更新template_status
    message = ''
    im_s.ImageManageService().update_image_manage_status(eimage_name, message, ImageManage.CHECKOUT)
    message = '模板机%s 生成模板成功' % eimage_name
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, msg=message)

