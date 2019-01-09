# coding=utf8
'''
    HOSTPOOL管理
'''


from model.const_define import ErrorCode
import json_helper
from service.s_hostpool import hostpool_service
from service.s_user.user_service import current_user_all_area_ids
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user


@login_required
def get_hostpool_level_info():
    '''
        获取层级信息
        机房 - 网络区域 - 集群
    :return:
    '''
    user_all_area_ids = current_user_all_area_ids()
    ret_data = hostpool_service.get_level_info()
    level_list = []
    for i in ret_data:
        # 只显示当前用户所属的区域
        if user_all_area_ids and i['area_id'] not in user_all_area_ids:
            continue

        _data = {
            "hostpool_id": i['hostpool_id'],
            "hostpool": i['hostpool_name'],
            "net_area": i['net_area_name'],
            "datacenter": i['datacenter_name'],
            "dc_type": i['dc_type']
        }
        level_list.append(_data)

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=level_list)




