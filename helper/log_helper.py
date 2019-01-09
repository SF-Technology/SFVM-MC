# coding=utf8
'''

    日志文件自动按照每天的日期切分

    filename log文件名 包含路径
    **kwargs  backupCount  最多保存多少天
              logLevel  可选指  DEBUG INFO ERROR WARNGING
    addTimedRotatingFileHandler(filename, **kwargs)
'''
# __author__ =  ""

import os
import logging
import logging.handlers
from flask_login import current_user
from flask import request, g
from model.const_define import AuditOperType
from config.default import CLOUD_VERSION


class WithAuditLogger(logging.Logger):
    AUDIT = logging.INFO + 1
    audit_field = {
        # login log
        1: ['Source_App', 'Destination_App', 'dst_ip', 'src_ip', 'Computer_name', 'src_mac', 'Oper_name', 'Oper_result',
            'fail_reason'],
        # user management log
        2: ['User_name', 'Source_App', 'Destination_App', 'dst_ip', 'Oper_type', 'Oper_result'],
        # role / permission management log
        3: ['User_name', 'Source_App', 'Destination_App', 'dst_ip', 'Oper_type', 'Oper_content_old', 'Oper_content_new',
            'Oper_result'],
        # sensitive info log
        6: ['Source_App', 'Destination_App', 'dst_ip', 'Request_type', 'Oper_type', 'QUERY_OBJ_INFO', 'Email' 'src_ip',
            'src_mac', 'Oper_content', 'Oper_affect_rows', 'Oper_result']
    }

    def __init__(self, name):
        logging.Logger.__init__(self, name)
        logging.addLevelName(self.AUDIT, 'AUDIT')

    def audit(self, log_type, field_data, *args, **kwargs):
        msg_list = []
        oper_code = 'NULL'
        # 获取登录用户ID，否则为Anonymous
        oper_user = current_user.user_id if current_user.is_authenticated else 'Anonymous'

        if field_data.get('oper_user'):
            oper_user = field_data['oper_user']

        if request.method in AuditOperType:
            oper_code = AuditOperType[request.method]

        basic_audit = {
            'Source_App': 'web',
            'Destination_App': 'SFVM-MC',
            'src_ip': request.remote_addr,
            'dst_ip': request.host,
            'config_name': request.path,
            'Oper_code': oper_code,
        }

        basic_audit.update(field_data)

        if kwargs.get('extra'):
            kwargs['extra'].update({'Audit_type': log_type,
                                    'Oper_user': oper_user,
                                    'version': CLOUD_VERSION})
        else:
            kwargs.update({'extra': {'Audit_type': log_type,
                                     'Oper_user': oper_user,
                                     'version': CLOUD_VERSION}})

        if self.isEnabledFor(self.AUDIT):
            extra_data = getattr(g, 'audit_field', None)
            for field in self.audit_field[log_type]:
                if extra_data and field in extra_data.keys():
                    msg_list.append(extra_data[field])
                elif basic_audit.get(field):
                    msg_list.append(basic_audit[field])
                else:
                    # 没有该项时设置为空
                    msg_list.append('')
            msg = u'\u0000'.join(msg_list)
            self._log(self.AUDIT, msg, args, **kwargs)


class CloudLogger(object):
    warning, info, error, audit = None, None, None, None

    @staticmethod
    def init(filename):

        dname = os.path.dirname(filename)
        if dname and not os.path.isdir(dname):
            os.makedirs(dname, 0755)

        # log_levels = ['WARNING', 'INFO', 'ERROR', 'DEBUG', 'AUDIT']
        # logging.setLoggerClass(WithAuditLogger)
        # for level in log_levels:
        #     if level != 'AUDIT':
        #         log_file_h = logging.handlers.TimedRotatingFileHandler(
        #             filename=filename,
        #             when="midnight",
        #             interval=1,
        #             backupCount=30)
        #         fmt = logging.Formatter('%(asctime)12s %(filename)s[line:%(lineno)4d] [%(levelname)s]: %(message)s')
        #     else:
        #         log_file_h = logging.handlers.TimedRotatingFileHandler(
        #             filename=filename,
        #             when="midnight",
        #             interval=4,
        #             backupCount=30)
        #         fmt = logging.Formatter(u'%(audittype)s\u0000%(version)s\u0000%(asctime)s\u0000%(oper_user)s'
        #                                 u'\u0000%(message)s',
        #                                 datefmt='%Y-%m-%d %H:%M:%S')
        #     log_file_h.setFormatter(fmt)
        #     _logger = logging.getLogger(level)
        #     _logger.addHandler(log_file_h)
        #     _logger.setLevel(logging.INFO)
        #
        #     if level == 'WARNING':
        #         CloudLogger.warning = _logger.warning
        #     if level == 'INFO':
        #         CloudLogger.info = _logger.info
        #     if level == 'ERROR':
        #         CloudLogger.error = _logger.error
        #     if level == 'DEBUG':
        #         CloudLogger.error = _logger.debug
        #     if level == 'AUDIT':
        #         CloudLogger.audit = _logger.audit

        logging.setLoggerClass(WithAuditLogger)
        log_file_h = logging.handlers.TimedRotatingFileHandler(
            filename=filename,
            when="midnight",
            interval=4,
            backupCount=30)
        fmt = logging.Formatter(u'%(Audit_type)s\u0000%(version)s\u0000%(asctime)s\u0000%(Oper_user)s'
                                u'\u0000%(message)s',
                                datefmt='%Y-%m-%d %H:%M:%S')
        log_file_h.setFormatter(fmt)
        _logger = logging.getLogger('AUDIT')
        _logger.addHandler(log_file_h)
        _logger.setLevel(logging.INFO)
        CloudLogger.audit = _logger.audit


def add_timed_rotating_file_handler(filename, **kwargs):
    '''
        给logger添加一个时间切换文件的handler。
        默认时间是0点开始备份。
        如果不指定logger，则使用logging.getLogger()，也就是RootLogger。
    '''
    dname = os.path.dirname(filename)
    if dname and not os.path.isdir(dname):
        os.makedirs(dname, 0755)
    conf = {
        'when': 'midnight',
        'backupCount': kwargs.get('backupCount', 30),
        'format': '[%(asctime)s][%(filename)s-L%(lineno)d][%(levelname)s]: %(message)s',
        'logger': logging.getLogger(),
    }
    conf.update(kwargs)
    if conf.get('logLevel'):
        if isinstance(conf['logLevel'], str):
            conf['logLevel'] = getattr(logging, conf['logLevel'])
        conf['logger'].setLevel(conf['logLevel'])

    handler = logging.handlers.TimedRotatingFileHandler(
        filename=filename,
        when=conf['when'],
        backupCount=conf['backupCount'],
    )
    handler.setFormatter(
        logging.Formatter(conf['format'])
    )
    conf['logger'].addHandler(handler)
    return handler

def add_timed_rotating_file_handler_for_hoststd(filename, **kwargs):
    '''
        给logger添加一个时间切换文件的handler。
        默认时间是0点开始备份。
        如果不指定logger，则使用logging.getLogger()，也就是RootLogger。
    '''
    dname = os.path.dirname(filename)
    if dname and not os.path.isdir(dname):
        os.makedirs(dname, 0755)
    conf = {
        'when': 'midnight',
        'backupCount': kwargs.get('backupCount', 30),
        'format': '[%(asctime)s][%(filename)s-L%(lineno)d][%(levelname)s]: %(message)s',
        'logger': logging.getLogger(),
    }
    conf.update(kwargs)
    if conf.get('logLevel'):
        if isinstance(conf['logLevel'], str):
            conf['logLevel'] = getattr(logging, conf['logLevel'])
        conf['logger'].setLevel(conf['logLevel'])

    handler = logging.handlers.TimedRotatingFileHandler(
        filename=filename,
        when=conf['when'],
        backupCount=conf['backupCount'],
    )
    handler.setFormatter(
        logging.Formatter(conf['format'])
    )
    conf['logger'].addHandler(handler)
    return handler


def log_error(trackback_err_info, is_alert=False):
    '''
    :param trackback_err_info :  这个参数请使用traceback.format_exc()  来生成错误信息
           bool is_alert    :    是否需要发送短信或者邮件告警信息
    :return:
    '''
    logging.error(trackback_err_info)
    # TODO 是否需要发送告警信息
