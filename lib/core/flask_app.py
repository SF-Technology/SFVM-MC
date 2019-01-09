# coding=utf8


import time
import logging
import traceback
from flask import Flask, request
from flask.app import _request_ctx_stack
import json_helper
import log_helper
import json
from helper.log_helper import CloudLogger
from model.const_define import ErrorCode, ErrorMsg, AuditType
import ip_helper
from service.s_user import user_service as user_s

FLASK_GLOBAL_APP = None


class My_Flask(Flask):

    def dispatch_request(self):
        start_time = time.time()
        resp = super(My_Flask, self).dispatch_request()
        """
        cost = time.time() - start_time
        req = _request_ctx_stack.top.request
        ret_data = {}
        try:
            if resp:
                resp_data = resp.data
                if resp.data.startswith("jQuery") or resp.data.startswith('jsonp'):
                    first = resp_data.find('(')
                    resp_data = resp_data[first+1:-2]
                ret_data = json_helper.loads(resp_data)
        except:
            errinfo = traceback.format_exc()
            errinfo = 'resp:%s exc:%s' % (resp, errinfo)
            log_helper.log_error(errinfo)
        ret_code = ret_data.get('code')
        if ret_code is not None:
            ret_code = int(ret_code)

        # log 不要打印password
        get_args = dict(req.args.items())
        get_args.pop('password', None)
        post_args = dict(req.form.items())
        post_args.pop('password', None)

        # 记录access.log
        logging.info("ip:%s base_url:%s path:%s method: %s platform:%s browser:%s browser_version:%s cost:%.3fs "
                     "get args:%s post args:%s ret:%s ret_msg:%s",
                     ip_helper.get_real_ip(req), req.base_url, req.full_path, req.method, req.user_agent.platform,
                     req.user_agent.browser, req.user_agent.version, cost, get_args.items(), post_args.items(),
                     ret_code, ErrorMsg.MSG_DICT.get(ret_code))
                     """
        return resp


def get_flask_app():

    def my_before_request():
        pass

    def my_after_request(response):
        response.direct_passthrough = False

        log_type = None
        field_data = {}
        # 登录日志
        if request.path.startswith('/login') \
                or request.path.startswith('/logout'):
            log_type = AuditType.LOGIN
            field_data.update({
                'Oper_name': 'login' if request.path.startswith('/login') else 'logout'
            })

        # 角色/权限管理日志
        elif request.path.startswith('/user_group') and request.method == 'DELETE':
            log_type = AuditType.PERMMGR
            # 被操作的账号
            oper_user_id = request.values.get('user_id')
            oper_user_info = user_s.UserService().get_user_info_by_user_id(oper_user_id)
            if oper_user_info:
                oper_user_name = oper_user_info['username']
            else:
                oper_user_name = None

            group_id = request.values.get('group_id')
            field_data.update({
                'User_name': oper_user_name,
                'Oper_type': 'delete',
                'Oper_content_old': 'user in group id ' + group_id,
                'Oper_content_new': 'delete user from group id ' + group_id
            })
        elif request.path.startswith('/user_group/insideuser/'):
            log_type = AuditType.PERMMGR

            # 被操作的账号
            oper_user_id = request.values.get('user_id')
            oper_user_info = user_s.UserService().get_user_info_by_user_id(oper_user_id)
            if oper_user_info:
                oper_user_name = oper_user_info['username']
            else:
                oper_user_name = None

            group_name = request.values.get('group_name')
            field_data.update({
                'User_name': oper_user_name,
                'Oper_type': 'authorize',
                'Oper_content_old': 'user not in group ' + group_name,
                'Oper_content_new': 'add user to group ' + group_name
            })
        elif request.path.startswith('/user_group/otheruser/'):
            log_type = AuditType.PERMMGR
            group_name = request.values.get('group_name')
            field_data.update({
                'User_name': request.values.get('user_name'),
                'Oper_type': 'authorize',
                'Oper_content_old': 'user not in group ' + group_name,
                'Oper_content_new': 'add user to group ' + group_name
            })

        try:
            resp_result = json_helper.loads(response.data)
            # 判断请求是否成功
            if resp_result.get('code') == ErrorCode.SUCCESS:
                field_data.update({'Oper_result': '1 Success'})
            else:
                field_data.update({'Oper_result': '0 Fail', 'fail_reason': resp_result.get('msg')})
        except Exception, e:
            pass

        if log_type:
            CloudLogger.audit(log_type, field_data)

        return response

    global FLASK_GLOBAL_APP
    if not FLASK_GLOBAL_APP:
        FLASK_GLOBAL_APP = My_Flask(__name__, template_folder='../../static', static_folder='../../static',
                                    static_url_path='/kvm')
    FLASK_GLOBAL_APP.before_request(my_before_request)
    FLASK_GLOBAL_APP.after_request(my_after_request)
    FLASK_GLOBAL_APP.register_error_handler(BaseException, global_error_handler)
    return FLASK_GLOBAL_APP


def global_error_handler(exception):
    from flask import request
    errinfo = traceback.format_exc()
    errinfo = 'path:%s args:%s %s' % (request.full_path, request.values, errinfo)
    log_helper.log_error(errinfo, True)
    resp = {
        'code': ErrorCode.SYS_ERR,
    }
    return json_helper.write(resp)
