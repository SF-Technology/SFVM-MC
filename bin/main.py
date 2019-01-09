# coding=utf8
# __author__ =  ""

import os
import logging
# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


def init_env():
    '''
        导入sys path
    :return:
    '''
    file_basic_path = os.path.dirname(os.path.abspath(__file__))

    basic_path = file_basic_path[0:-4]
    os.environ["BASIC_PATH"] = basic_path  # basic path 放到全局的一个变量当中去
    sys.path.append(basic_path)
    sys.path.append(basic_path+'/config')
    sys.path.append(basic_path+'/helper')
    sys.path.append(basic_path+'/lib')
    sys.path.append(basic_path+'/model')
    sys.path.append(basic_path+'/controller')
    sys.path.append(basic_path+'/service')

init_env()

from core import flask_app
from config import GLOBAL_CONFIG, AUDIT_LOG_PATH
from other import pid_util
from common_data_struct import user_info
from helper.log_helper import CloudLogger
import default
import json


def init_log(service_name):
    # 初始化log组件
    import log_helper

    # 初始化安全审计日志
    CloudLogger.init(AUDIT_LOG_PATH)

    log_path = GLOBAL_CONFIG['flask'][service_name]['logPath']
    log_level = GLOBAL_CONFIG['flask'][service_name]['logLevel']
    handler = log_helper.add_timed_rotating_file_handler(log_path, logLevel=log_level)
    return handler


def init_js_config_file():
    # 启动时在目录/static/js/config下生成配置文件，config.json
    file_content = GLOBAL_CONFIG['host_console_url']
    prj_path = default.DIR_DEFAULT
    json_path = prj_path + '/static/js/config/config.json'
    file_content_to_json = json.dumps(file_content)
    f = file(json_path, "w+")
    f.write(file_content_to_json)
    f.close()
    return 'done'


def start(service_name):

    init_js_config_file()

    log_handler = init_log(service_name)

    flask_config = GLOBAL_CONFIG.get("flask").get(service_name)
    # 启动falsk
    options = {
        'threaded': True,
    }
    host = flask_config.get("host")
    port = flask_config.get('port')
    debug_mode = flask_config.get('debug_mode')
    reg_module_name = flask_config.get("reg_module_name")
    print reg_module_name

    # 注册interface
    import reg_route
    reg_route.reg(reg_module_name)
    print reg_route

    logging.info(" start app %s", service_name)

    # 生成pid
    pid_file = os.environ["BASIC_PATH"] + '/bin/' + service_name + '_flask_app.pid'
    pid_ins = pid_util.PidUtil(service_name, pid_file)
    pid_ins.start()

    app = flask_app.get_flask_app()
    # secret_key两种方式：1.固定字符串  2.随机random：每次app重启，浏览器session会失效，用户需重登
    app.config['SECRET_KEY'] = 'kvmmgr_666_lee#!&@!*@%'

    login_manager = LoginManager()

    # flask-login注册用户登录
    @login_manager.user_loader
    def load_user(userid):
        user = user_info.UserInfo().get_user(userid)
        return user

    login_manager.init_app(app)

    app.logger.addHandler(log_handler)
    app.run(host, port, debug_mode, **options)

    pid_ins.clear()
    logging.info('stop app %s', service_name)


def help():
    print '''
    usage:

        python main.py service_name start
        python main.py service_name stop
    '''
    sys.exit()


def stop(service_name):
    pid_file = os.environ["BASIC_PATH"] + '/bin/' + service_name + '_flask_app.pid'
    pid_ins = pid_util.PidUtil(service_name, pid_file)
    logging.info("stop app %s", service_name)
    if pid_ins.stop() == 0:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':

    if len(sys.argv) < 3:
        help()

    service_name = sys.argv[1]
    action = sys.argv[2]
    if action == 'start':
        start(service_name)
    elif action == 'stop':
        stop(service_name)
    else:
        help()
