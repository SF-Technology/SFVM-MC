# coding=utf8
'''
    注册url路由
'''
# __author__ =  ""

from core import flask_app


def reg(module_name):
    '''
        这里的module_name来自于config中的reg_module_name
    :param module_name:
    :return:
    '''

    app = flask_app.get_flask_app()

    if module_name == 'web_api':
        from web_api import reg_route
    elif module_name == 'other_api':
        from other_api import reg_route
    reg_route.reg(app)
