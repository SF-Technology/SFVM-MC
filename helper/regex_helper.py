#coding=utf8
__author__ =  ""
import re

mobile_pattern = re.compile(r'^1[34578]\d{9}$')
captcha_pattern = re.compile(r'^\d{6}$')
birthday_pattern = re.compile(r'^(19|20)\d\d[- /.](0[1-9]|1[012])[- /.](0[1-9]|[12][0-9]|3[01])$')




def is_valid_mobile(mobile):
    '''
        是否是有效的手机号码
    :param mobile:
    :return True / False:
    '''
    if not mobile:
        return False
    global mobile_pattern
    result = mobile_pattern.match(mobile)
    if result:
        return True
    else:
        return False


def is_valid_captcha(captcha):
    '''
        是否是有效的验证码 6位数字型的字符串
    :param captcha:
    :return True / False:
    '''
    if not captcha:
        return False
    if len(captcha) < 6:
        return False
    match_result = captcha.match(captcha)
    if not match_result:
        return False
    return True


def is_valid_birthday(birthday):
    if not birthday:
        return False
    match_result = birthday_pattern.match(birthday)
    if not match_result:
        return False
    return True


def is_valid_password(password):
    if not password:
        return False
    if len(password) != 32:
        return False
    return True