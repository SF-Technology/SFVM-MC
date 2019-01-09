#coding=utf8

'''
    计算字符串的sha1指和md5指

    sha1('123456')

    md5('123456')
'''

import hashlib

def sha1(string):
    sha1obj = hashlib.sha1()
    sha1obj.update(string)
    hash = sha1obj.hexdigest()
    return hash


def md5(string):
    '''
        生成字符串的md5
    :param string:
    :return string:
    '''
    md = hashlib.md5()
    md.update(string)
    return md.hexdigest().lower()
