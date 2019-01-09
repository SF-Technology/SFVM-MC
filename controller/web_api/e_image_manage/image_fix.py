# coding=utf8
'''
    镜像管理状态修复
'''
# __author__ =  ""
from flask import request
from helper import json_helper
from helper.time_helper import get_datetime_str
import image_manage_action as im_man_act
from model.const_define import ErrorCode, ImageManage
from service.s_image import image_service as im_s
from service.s_ip import segment_service as segment_s
from model.const_define import image_manage_action as im_m_act, image_mange_action_state as im_m_act_sta
import sys
sys.setdefaultencoding('utf-8')

def image_fix():
    return