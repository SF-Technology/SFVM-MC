# # coding=utf8
# '''
#     image_sync_intodb
# '''
#
#
# import logging
# from helper import json_helper
# from model.const_define import ErrorCode,VMStatus,VMTypeStatus,VMCreateSource,esx_v2vActions
# from flask import request
# from service.s_image_sync import image_sync_service as im_sy_s
# from service.v2v_task import v2v_task_service as v2v_op
# from service.s_instance_action import instance_action as in_a_s
# from service.s_instance import instance_host_service as ins_h_s, instance_ip_service as ins_ip_s, \
#     instance_disk_service as ins_d_s, instance_service as ins_s, \
#     instance_flavor_service as ins_f_s, instance_group_service as ins_g_s
# from service.s_ip import ip_service as ip_s ,segment_service as seg_s
# from service.s_flavor import flavor_service
# from service.s_host import host_service as ho_s
# from service.v2v_task import v2v_instance_info as v2v_in_i
# from lib.vrtManager.util import randomUUID, randomMAC
# from helper.time_helper import get_datetime_str
# from pyVim.connect import SmartConnectNoSSL, Disconnect
# import base64
# import json
#
# #主函数
# def image_sync_indoto():
#     #定义image_sync_list用来接收前台传入的多条记录
#     image_sync_str = request.values.get("image_sync_batch")
#     image_sync_list = json.loads(image_sync_str)
#     task_list = []
#     error_list = []
#     total_num = len(image_sync_list)
#     #针对list中的每个对象检查当前任务数
#     for image_sync_task in image_sync_list:
#         host_ip = image_sync_task['host_ip']
#         task_num_exist = im_sy_s.get_task_ondo_num(host_ip)
#         if task_num_exist:
#             if task_num_exist >= 3:
#                 message = "当前活跃状态任务超过或等于3条"
#                 image_sync_task['error_message'] = message
#                 error_list.append(image_sync_task)
#             else:
#                 return True
#         else:
#             return True
#     #针对每个image任务做入库
#     for image in
#
