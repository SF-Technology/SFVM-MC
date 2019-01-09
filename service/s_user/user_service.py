# coding=utf8
'''
    USER服务
'''
# __author__ =  ""

from model import user
from model.const_define import UserAuthType
from service.s_role import role_service
from helper.encrypt_helper import encrypt, decrypt
import base64
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
from service.s_user_group import user_group_service as user_g_s
from service.s_group import group_service as group_s
from service.s_access import access_service
from service.s_area import area_service as area_s
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired, BadSignature


class UserService:
    def __init__(self):
        self.user_db = user.User(db_flag='kvm', table_name='tb_user')

    def add_user(self, insert_data):
        return self.user_db.insert(insert_data)

    def update_user_info(self, update_data, where_data):
        return self.user_db.update(update_data, where_data)

    def get_user_info_by_user_id(self, user_id):
        return self.user_db.get_one('userid', user_id)

    def query_data(self, **params):
        return self.user_db.simple_query(**params)

    def query_user_info(self, where_field, where_field_value):
        return self.user_db.get_one(where_field, where_field_value)

    def get_all_users(self):
        params = {
            'ORDER': [
                ['id', 'desc'],
            ],
        }
        return self.user_db.simple_query(**params)

    def login_local_user(self, userid, password):
        '''
            本地用户登录
        :param userid:
        :param password:
        :return:
        '''
        params = {
            'WHERE_AND': {
                '=': {
                    'userid': str(userid),
                    'password': base64.b64encode(str(password))
                }
            }
        }
        user_num, user_data = self.user_db.simple_query(**params)
        if user_num > 0:
            return user_data[0]
        else:
            return None

    def login_external_user(self, userid, password):
        '''
            外部应用用户登录
        :param userid:
        :param password:
        :return:
        '''
        params = {
            'WHERE_AND': {
                '=': {
                    'userid': str(userid),
                    'password': base64.b64encode(str(password)),
                    'auth_type': UserAuthType.EXTERNAL
                }
            }
        }
        user_num, user_data = self.user_db.simple_query(**params)
        if user_num > 0:
            return user_data[0]
        else:
            return None

    def check_userid_exist(self, user_id, auth_type=None):
        '''
            检查该用户ID是否已存在
        :param user_id:
        :param auth_type: 为None时不区分ad还是外部用户
        :return:
        '''
        params = {
            'WHERE_AND': {
                '=': {
                    'userid': user_id,
                }
            }
        }
        if auth_type:
            params['WHERE_AND']['=']['auth_type'] = auth_type

        user_nums, user_datas = self.user_db.simple_query(**params)
        if user_nums > 0:
            return True
        return False


def get_user():
    '''
        获取用户登陆状态及信息
    :return:
    '''
    # 已登录
    if not current_user.is_anonymous:
        user_data = {
            "user_name":  current_user.user_name,
            "user_id": current_user.user_id
        }
        return user_data
    else:
        return {
            "user_name": '',
            "user_id": ''
        }


def get_username_by_id(user_id):
    '''
           根据用户id返回用户名
        :return:
        '''
    user_info = UserService().query_user_info('userid',user_id)
    username = user_info['username']
    return username


def user_permisson(user_id):
    '''
        获取用户的所有操作权限
    :param user_id:
    :return: {u'instance': [u'create', u'delete', u'shutdown'],u'host':[u'create', u'delete']}
    '''
    user_permisson_list = []
    user_group_nums, user_group_data = user_g_s.UserGroupService().get_allgroup_user(user_id)
    # 新用户没有组
    if user_group_nums <= 0:
        return None

    for _user_group in user_group_data:
        _group_id = _user_group['group_id']
        _group_name = _user_group['group_name']
        # 通过group_id找到access表中对应的role_id，这里是默认一个组只有一个角色的
        # _role_info = access_service.AccessService().get_one('group_id', _group_id)
        num, _role_info = user_g_s.UserGroupService().get_user_role(user_id, _group_id)
        if num <= 0:
            _role_id = None
        else:
            _role_id = _role_info[0]['role_id']
        # 查询role_permission表中role_id对应的全部permission_id
        _role_permission_list = role_service.RolePermissionService().role_permission_list(_role_id)
        if _role_permission_list < 0:
            return None
        _host_list = []
        _instance_list = []
        _permission_dict = {}
        for _i in _role_permission_list:
            if _i.keys()[0] == 'instance':
                _instance_list.append(_i.values()[0])
            if _i.keys()[0] == 'host':
                _host_list.append(_i.values()[0])
        _permission_dict['instance'] = _instance_list
        _permission_dict['host'] = _host_list
        _permission_dict['role_id'] = _role_id
        _permission_dict['group_id'] = _group_id
        _permission_dict['group_name'] = _group_name

        user_permisson_list.append(_permission_dict)
    return user_permisson_list


def user_area(user_id):
    '''
        获取用户对应的所有组所属的全部区域
    :param user_id:
    :return: {'01223805': [3L, 1L, 2L, 4L, 15L, 22L, 11L]}
        注意：这里的区域ID是父区域ID
    '''
    data_dict = user.user_area_info(user_id)
    user_area_dict = {}
    area_list = []
    for i in data_dict:
        area_list.append(i.values()[0])
    user_area_dict[user_id] = area_list
    return user_area_dict


def current_user_areas():
    '''
        获取当前用户的所属区域ID列表
    :return:
    '''
    c_user = get_user()
    c_user_id = c_user['user_id']
    if not c_user_id:
        return None

    return user_area(c_user_id)[c_user_id]


def current_user_all_area_ids():
    '''
        获取当前用户的所属区域（父区域、子区域）ID列表
    :return:
    '''
    # 由于这里获取的父区域ID，所以先将父区域下面的子区域ID也取出来
    user_area_ids = current_user_areas()
    all_area_ids = []
    for _area_id in user_area_ids:
        _area_info = area_s.AreaService().get_area_info(_area_id)
        if _area_info:
            # 父区域
            if _area_info['parent_id'] == -1:
                _child_nums, _child_data = area_s.AreaService().get_child_areas(_area_id)
                # 有子区域，把子区域的ID都加上
                if _child_nums > 0:
                    for _child in _child_data:
                        all_area_ids.append(_child['id'])
            else:
                # 子区域，把其父区域ID加上
                all_area_ids.append(_area_info['parent_id'])

            # 同时把本区域加上
            all_area_ids.append(_area_id)

    # 去除重复的
    return list(set(all_area_ids))


def user_all_area_ids_by_userid(user_id):
    '''
        获取指定用户的所属区域（父区域、子区域）ID列表
    :return:
    '''
    # 由于这里获取的父区域ID，所以先将父区域下面的子区域ID也取出来
    user_area_ids = user_area(user_id)[user_id]
    all_area_ids = []
    for _area_id in user_area_ids:
        _area_info = area_s.AreaService().get_area_info(_area_id)
        if _area_info:
            # 父区域
            if _area_info['parent_id'] == -1:
                _child_nums, _child_data = area_s.AreaService().get_child_areas(_area_id)
                # 有子区域，把子区域的ID都加上
                if _child_nums > 0:
                    for _child in _child_data:
                        all_area_ids.append(_child['id'])
            else:
                # 子区域，把其父区域ID加上
                all_area_ids.append(_area_info['parent_id'])

            # 同时把本区域加上
            all_area_ids.append(_area_id)

    # 去除重复的
    return list(set(all_area_ids))


def current_user_groups():
    '''
        获取当前用户的所属应用组
    :return:
    '''
    c_user = get_user()
    c_user_id = c_user['user_id']
    if not c_user_id:
        return None

    groups_list = []
    user_groups_num, user_groups_data = user_g_s.UserGroupService().get_allgroup_user(c_user_id)
    for _user_group in user_groups_data:
        _group_num, _group_data = group_s.GroupService().get_group_info(_user_group['group_id'])
        if _group_num > 0:
            groups_list.append(_group_data[0])

    return groups_list


def current_user_groups_by_userid(user_id):
    '''
        获取指定用户的所属应用组
    :return:
    '''
    groups_list = []
    user_groups_num, user_groups_data = user_g_s.UserGroupService().get_allgroup_user(user_id)
    for _user_group in user_groups_data:
        _group_num, _group_data = group_s.GroupService().get_group_info(_user_group['group_id'])
        if _group_num > 0:
            groups_list.append(_group_data[0])

    return groups_list


def current_user_group_ids():
    '''
        获取当前用户的所属应用组ID
    :return:
    '''
    c_user = get_user()
    c_user_id = c_user['user_id']
    if not c_user_id:
        return None

    group_ids_list = []
    user_groups_num, user_groups_data = user_g_s.UserGroupService().get_allgroup_user(c_user_id)
    for _user_group in user_groups_data:
        group_ids_list.append(_user_group['group_id'])

    return list(set(group_ids_list))


def current_user_role_ids():
    '''
        获取当前用户的角色ID
    :return:
    '''
    c_user = get_user()
    c_user_id = c_user['user_id']
    if not c_user_id:
        return None

    user_group_nums, user_group_data = user_g_s.UserGroupService().get_allgroup_user(c_user_id)
    # 新用户没有组
    if user_group_nums <= 0:
        return None

    role_ids_list = [user_group['role_id'] for user_group in user_group_data]
    return list(set(role_ids_list))


def generate_api_auth_token(api_userid, expiration=1296000):
    '''
        给外部应用调用生成token，默认token失效时间为15天
    :param api_userid:
    :param expiration:
    :return:
    '''
    s = Serializer('KvmDashboard/888888', expires_in=expiration)
    return s.dumps({'userid': api_userid})


def verify_api_auth_token(token):
    '''
        校验用户token是否合法，合法则返回用户userid
    :param token:
    :return:
    '''
    s = Serializer('KvmDashboard/888888')
    try:
        data = s.loads(token)
    except SignatureExpired:
        return None  # valid token, but expired
    except BadSignature:
        return None  # invalid token
    api_user = UserService().get_user_info_by_user_id(data['userid'])
    return api_user


def verify_password(password, password_db):
    '''
        外部应用调用校验密码是否正确
    :param password:
    :param password_db:
    :return:
    '''
    real_pwd = base64.b64decode(password_db)
    if password == real_pwd:
        return True
    else:
        return False

