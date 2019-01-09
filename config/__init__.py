#coding=utf8
__author__ =  ""


import socket


try:
    hostname = socket.gethostname().lower()
    hostname = hostname.split('.')[0]
    exec('from %s import *' % hostname.replace('-', '_'))
except:
    from  develop import *
