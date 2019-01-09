# -*- coding:utf-8 -*-
# __author__ =  ""
# Created by 062076 on 2017/3/6.

import model.auth as auth
from flask import request, render_template, redirect, session
import jinja2
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user,logout_user
# from flask.ext.httpauth import HTTPBasicAuth
from flask_httpauth import HTTPBasicAuth
from werkzeug.contrib.cache import SimpleCache
from flask import session
from helper import json_helper
from model.const_define import ErrorCode, UserAuthType, OperationObject, OperationAction
from common_data_struct import user_info
import logging
from service.s_user import user_service as user_s
from service.s_user_group import user_group_service as user_g_s
from service.s_operation import operation_service as oper_s
from helper.time_helper import get_datetime_str, get_timestamp, change_datetime_to_timestamp


cache = SimpleCache()
# 用户登录锁定时间
lock_minute = 15

auth_api_user = HTTPBasicAuth()
api_login_user = ''


@oper_s.add_operation_login(OperationObject.LOGIN_LOGOUT, OperationAction.LOGIN)
def login():
    userid = request.values.get('userid')
    password = request.values.get('password')
    # base64解密
    # password = base64.b64decode(password)

    # 限制同一浏览器只能登录一个账号
    if current_user and not current_user.is_anonymous and userid != current_user.user_id:
        logging.warn('login another user %s when now has user %s', userid, current_user.user_id)
        # 当当前有用户登录时，再次登录则直接跳到前一个用户
        user_permisson = user_s.user_permisson(current_user.user_id)
        user_data = {
            "user_name": current_user.user_name,
            "user_id": current_user.user_id,
            "user_permisson": user_permisson
        }
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=user_data)

    # 默认本地认证
    auth_type = request.values.get('auth_type', UserAuthType.LOCAL)
    if not userid or not password or not auth_type:
        return json_helper.format_api_resp(code=ErrorCode.USER_OR_PWD_ERR, msg='您输入的账号非法，请重新输入!')

    fail_attempts = cache.get(userid)  # 查找userid的缓存，存在则说明上次错误登录留下的缓存还没过期
    if fail_attempts >= 5:  # 如果输错是超过5次，直接返回提示
        cache.set(userid, fail_attempts + 1, lock_minute * 60)
        message = '您的账号密码输错次数过多，请%d分钟后再尝试' % lock_minute
        return json_helper.format_api_resp(code=ErrorCode.USER_OR_PWD_ERR, msg=message)

    if auth_type == UserAuthType.EXTERNAL:
        # 外部API认证
        # ----------------------------------- local begin -------------------------------------------
        api_user = user_s.UserService().login_external_user(userid, password)
        if not api_user:
            if not fail_attempts:
                fail_attempts = 1
            else:
                fail_attempts += 1

            if fail_attempts >= 5:
                cache.set(userid, fail_attempts, lock_minute * 60)
                message = '您的账号密码输错次数过多，请%d分钟后再尝试!' % lock_minute
                return json_helper.format_api_resp(code=ErrorCode.USER_OR_PWD_ERR, msg=message)

            cache.set(userid, fail_attempts, lock_minute * 60)

            message = '账号密码错误，您还可以重试%d次!' % (5 - fail_attempts)
            logging.info('login ladp fail, ' + message)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=message)
        else:
            user = user_info.UserInfo().get_user(userid)
            # 不允许登录
            if not user.is_active:
                logging.info('userid: %s is not allow login', userid)
                return json_helper.format_api_resp(code=ErrorCode.USER_OR_PWD_ERR, msg='您的账号已锁定，请联系管理员!')

            login_user(user)
            cache.set(userid, 0, 0.1)  # 输对密码就清掉cache
        # ----------------------------------- api end ---------------------------------------------

    elif auth_type == UserAuthType.LOCAL:
        # 本地认证
        # ----------------------------------- local begin -------------------------------------------
        local_user = user_s.UserService().login_local_user(userid, password)
        if not local_user:
            if not fail_attempts:
                fail_attempts = 1
            else:
                fail_attempts += 1

            if fail_attempts >= 5:
                cache.set(userid, fail_attempts, lock_minute * 60)
                message = '您的账号密码输错次数过多，请%d分钟后再尝试!' % lock_minute
                return json_helper.format_api_resp(code=ErrorCode.USER_OR_PWD_ERR, msg=message)

            cache.set(userid, fail_attempts, lock_minute * 60)

            message = '账号密码错误，您还可以重试%d次!' % (5 - fail_attempts)
            logging.info('login ladp fail, ' + message)
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, msg=message)
        else:
            user = user_info.UserInfo().get_user(userid)
            # 不允许登录
            if not user.is_active:
                logging.info('userid: %s is not allow login', userid)
                return json_helper.format_api_resp(code=ErrorCode.USER_OR_PWD_ERR, msg='您的账号已锁定，请联系管理员!')

            login_user(user)
            cache.set(userid, 0, 0.1)  # 输对密码就清掉cache
        # ----------------------------------- local end ---------------------------------------------

    # 返回用户信息
    user_permisson = user_s.user_permisson(current_user.user_id)
    user_data = {
        "user_name": current_user.user_name,
        "user_id": current_user.user_id,
        "user_permisson": user_permisson
    }
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=user_data)


def index():
    return redirect('/kvm/login.html')


def logout():
    user_id = current_user.user_id
    logout_user()
    session.clear()
    logging.info('userid: %s is logged out', user_id)
    oper_s.add_operation_other(user_id, OperationObject.LOGIN_LOGOUT, OperationAction.LOGOUT, "SUCCESS")
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)


def get_user():
    '''
        获取用户登陆状态及信息
    :return:
    '''
    # 已登录
    if not current_user.is_anonymous:
        user_permisson = user_s.user_permisson(current_user.user_id)
        user_data = {
            "user_name": current_user.user_name,
            "user_id": current_user.user_id,
            "user_permisson": user_permisson
        }
        return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data=user_data)
    else:
        return json_helper.format_api_resp(code=ErrorCode.AUTH_ERROR, msg='用户未登录')


@auth_api_user.login_required
def other_api_get_auth_token():
    global api_login_user
    token = user_s.generate_api_auth_token(api_login_user, expiration=1296000)
    return json_helper.format_api_resp_token_to_vishnu(token=token)


@auth_api_user.verify_password
def verify_api_user_pwd(username_or_token, password):
    global api_login_user
    if not username_or_token:
        return False
    api_user = user_s.verify_api_auth_token(username_or_token)
    if not api_user:
        api_user = user_s.UserService().get_user_info_by_user_id(username_or_token)
        if not api_user or not user_s.verify_password(password, api_user['password']):
            return False
        if api_user['auth_type'] != 2:
            return False
    elif api_user['auth_type'] != 2:
        return False
    api_login_user = api_user['userid']
    return True

