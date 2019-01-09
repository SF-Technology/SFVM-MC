# coding=utf8
'''
    网络区域管理
'''
# __author__ =  ""

from service.s_net_area import net_area
from common_data_struct import net_area_level_info, base_define
from service.s_area import area_service as area_s
import json_helper
from model.const_define import ErrorCode
from service.s_user.user_service import current_user_all_area_ids
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user


class NetArealevelInfoResp(base_define.Base):

    def __init__(self):
        self.level_info = []


@login_required
def net_area_level_info_get():
    resp = NetArealevelInfoResp()
    user_all_area_ids = current_user_all_area_ids()

    level_datas = net_area.get_level_info()
    for i in level_datas:
        # 只获取当前用户所在区域
        if user_all_area_ids and i['area_id'] not in user_all_area_ids:
            continue

        _level = net_area_level_info.NetArealevelInfo().init_from_db(i)
        # 如果有父区域
        if i['parent_id']:
            _parent_data = area_s.AreaService().get_area_info(i['parent_id'])
            if _parent_data:
                _level.area = _parent_data['displayname']
                _level.child_area = i['area_name']
            else:
                # 有父区域ID但没有相应信息，则当做没有父区域
                _level.area = i['area_name']
        else:
            # 如果没有父区域，则本身作为区域，子区域为空
            _level.area = i['area_name']

        resp.level_info.append(_level)
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=resp.to_json())