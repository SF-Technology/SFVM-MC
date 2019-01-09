# coding=utf8
'''
    tb_user表中用户信息字段
'''


import base_define
from service.s_user import user_service
from service.s_access import access_service
from model.const_define import UserStatus, AuditType
from helper.time_helper import get_datetime_str
from helper.log_helper import CloudLogger


class UserInfo(base_define.Base):

    def __init__(self, user_id=None, user_name=None, areas=[]):
        self.user_id = user_id
        self.user_name = user_name
        self.status = None
        self.email = None
        self.areas = areas

    @classmethod
    def get_user(cls, user_id):
        user_res = user_service.UserService().query_user_info('userid', user_id)
        area_nums, areas_data = access_service.AccessService().get_groups_info(user_id)
        if not user_res:
            _user = UserInfo()
        else:
            if area_nums > 0:
                _user = UserInfo(user_id=user_id, user_name=user_res['username'], areas=list(areas_data))
            else:
                _user = UserInfo(user_id=user_id, user_name=user_res['username'])
        return _user

    @staticmethod
    def create_new_user(user_ldap):
        new_user_data = {
            'userid': user_ldap['userid'],
            'username': user_ldap['name'],
            'email': user_ldap['mail'],
            'telephone': user_ldap['mobile'],
            'fengsheng': None,
            'status': UserStatus.NORMAL,
            'isdeleted': '0',
            'created_at': get_datetime_str()
        }
        res = user_service.UserService().add_user(new_user_data)
        new_user = None

        # 记录安全日志
        field_data = {
            'User_name': user_ldap['name'] or None,
            'Oper_type': 'add'
        }
        if res.get('row_num') > 0:
            field_data.update({'Oper_result': '1 Success'})
            new_user = UserInfo.get_user(user_ldap['userid'])
        else:
            field_data.update({'Oper_result': '0 Fail', 'fail_reason': 'insert new user info to db fail'})

        CloudLogger.audit(AuditType.USERMGR, field_data)
        return new_user

    @property
    def is_active(self):
        '''
            返回用户是否可以登录
        :return:
        '''
        user = user_service.UserService().query_user_info('userid', self.user_id)
        # 锁定状态的用户不能登录
        if user and user['status'] == UserStatus.LOCK:
            return False
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        '''
            返回是否是匿名用户, 也就是未登陆的用户等
        :return:
        '''
        return False

    def get_id(self):
        try:
            return unicode(self.user_id)
        except AttributeError:
            raise NotImplementedError('No `userid` attribute - override `get_id`')

    def init_from_db(self, one_db_data):
        self.user_id = one_db_data['userid']
        self.user_name = one_db_data['username']
        self.status = one_db_data['status']
        self.email = one_db_data['email']
        return self