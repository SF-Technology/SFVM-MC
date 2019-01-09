#coding=utf8
import os
import logging
import traceback
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
    sys.path.append(basic_path+'/interface')

init_env()

import config
from core import flask_app


def init_log():
    import log_helper
    handler = log_helper.add_timed_rotating_file_handler(config.LOG_PATH, logLevel=logging.DEBUG)
    return handler
try:
    app = flask_app.get_flask_app()
    app.logger.addHandler(init_log())

    import reg_route
    reg_route.reg('web_api')

    logging.info('start')

    application = app.wsgi_app
except:
    logging.error(traceback.format_exc())

