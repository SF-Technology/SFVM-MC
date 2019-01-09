# -*- coding:utf-8 -*-

import random
import string


def get_strings(length):
    '''
        随机生成指定长度的字符串
    :param length:
    :return:
    '''
    return ''.join(random.sample(string.ascii_letters + string.digits, int(length)))


def get_password_strings(length):
    '''
        随机生成指定长度的密码
    :param length:
    :return:
    '''
    punctuation_string = """!#$%&()*@"""
    return ''.join(random.sample(string.ascii_letters + string.digits + punctuation_string, int(length)))
