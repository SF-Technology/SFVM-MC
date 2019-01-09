# coding=utf8
'''
    物理机IPMI操作
'''
# __author__ =  ""

from lib.shell import cmd
from config import default
from helper import encrypt_helper
import time
import sys
import subprocess


def server_status(manage_ip, sn):
    '''
        物理机状态查询
    :param manage_ip:
    :param sn:
    :return:
    '''
    command = "ipmitool -I lanplus -H %s -U %s -P %s power status" % \
              (manage_ip, default.SERVER_USER, encrypt_helper.decrypt(default.SERVER_PWD) + sn)
    result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # 设置超时规则，每250ms去获取返回结果，结果为空或者查询未超过1s，继续等待250ms
    timeout = 1
    poll_seconds = .250
    deadline = time.time() + timeout
    while time.time() < deadline and result.poll() == None:
        time.sleep(poll_seconds)
    if result.poll() == None:
        result.terminate()
        return 2
    ret = result.stdout.readline().split('\n')[0]
    if ret == 'Error: Unable to establish IPMI v2 / RMCP+ session':
        return 1
    elif ret == 'Chassis Power is on' or ret == 'Chassis Power is off':
        return ret
    else:
        return 2


def server_start(manage_ip, sn):
    '''
        远程开机
    :param manage_ip:
    :param sn:
    :return: 返回3，机器状态已经为操作预期状态；返回2，ipmi操作超时，请重新下发指令；
             返回1，ipmi无法使用，请联系管理员查看；返回0，操作成功
    '''
    # 远程开机前先确定物理机状态, 开机状态不允许操作
    host_status = server_status(manage_ip, sn)
    if host_status is 1 or host_status is 2:
        return 1
    if host_status is 'Chassis Power is on':
        return 3

    command = "ipmitool -I lanplus -H %s -U %s -P %s power on" % \
              (manage_ip, default.SERVER_USER, encrypt_helper.decrypt(default.SERVER_PWD) + sn)
    result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # 设置超时规则，每250ms去获取返回结果，结果为空或者查询未超过1s，继续等待250ms
    timeout = 1
    poll_seconds = .250
    deadline = time.time() + timeout
    while time.time() < deadline and result.poll() == None:
        time.sleep(poll_seconds)
    if result.poll() == None:
        result.terminate()
        return 2
    ret = result.stdout.readline().split('\n')[0]
    if ret == 'Error: Unable to establish IPMI v2 / RMCP+ session':
        return 1
    elif ret == 'Chassis Power Control: Up/On':
        return 0
    else:
        return 2


def server_stop(manage_ip, sn):
    '''
        远程硬关机
    :param manage_ip:
    :param sn:
    :return: 返回3，机器状态已经为操作预期状态；返回2，ipmi操作超时，请重新下发指令；
             返回1，ipmi无法使用，请联系管理员查看；返回0，操作成功
    '''
    # 远程硬关机前先确定物理机状态, 关机状态不允许操作
    host_status = server_status(manage_ip, sn)
    if host_status is 1 or host_status is 2:
        return 1
    if host_status is 'Chassis Power is off':
        return 3

    command = "ipmitool -I lanplus -H %s -U %s -P %s power off" % \
              (manage_ip, default.SERVER_USER, encrypt_helper.decrypt(default.SERVER_PWD) + sn)
    result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # 设置超时规则，每250ms去获取返回结果，结果为空或者查询未超过1s，继续等待250ms
    timeout = 1
    poll_seconds = .250
    deadline = time.time() + timeout
    while time.time() < deadline and result.poll() == None:
        time.sleep(poll_seconds)
    if result.poll() == None:
        result.terminate()
        return 2
    ret = result.stdout.readline().split('\n')[0]
    if ret == 'Error: Unable to establish IPMI v2 / RMCP+ session':
        return 1
    elif ret == 'Chassis Power Control: Down/Off':
        return 0
    else:
        return 2


def server_soft_stop(manage_ip, sn):
    '''
        远程软关机
    :param manage_ip:
    :param sn:
    :return: 返回3，机器状态已经为操作预期状态；返回2，ipmi操作超时，请重新下发指令；
             返回1，ipmi无法使用，请联系管理员查看；返回0，操作成功
    '''
    # 远程软关机前先确定物理机状态, 关机状态不允许操作
    host_status = server_status(manage_ip, sn)
    if host_status is 1 or host_status is 2:
        return 1
    if host_status is 'Chassis Power is off':
        return 3

    command = "ipmitool -I lanplus -H %s -U %s -P %s power soft" % \
              (manage_ip, default.SERVER_USER, encrypt_helper.decrypt(default.SERVER_PWD) + sn)
    result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # 设置超时规则，每250ms去获取返回结果，结果为空或者查询未超过1s，继续等待250ms
    timeout = 1
    poll_seconds = .250
    deadline = time.time() + timeout
    while time.time() < deadline and result.poll() == None:
        time.sleep(poll_seconds)
    if result.poll() == None:
        result.terminate()
        return 2
    ret = result.stdout.readline().split('\n')[0]
    if ret == 'Error: Unable to establish IPMI v2 / RMCP+ session':
        return 1
    elif ret == 'Chassis Power Control: Soft':
        return 0
    else:
        return 2


def server_reset(manage_ip, sn):
    '''
        远程硬重启
    :param manage_ip:
    :param sn:
    :return: 返回3，机器状态已经为操作预期状态；返回2，ipmi操作超时，请重新下发指令；
             返回1，ipmi无法使用，请联系管理员查看；返回0，操作成功
    '''
    # 远程硬重启前先确定物理机状态, 关机状态不允许操作
    host_status = server_status(manage_ip, sn)
    if host_status is 1 or host_status is 2:
        return 1
    if host_status is 'Chassis Power is off':
        return 3

    command = "ipmitool -I lanplus -H %s -U %s -P %s power reset" % \
              (manage_ip, default.SERVER_USER, encrypt_helper.decrypt(default.SERVER_PWD) + sn)
    result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # 设置超时规则，每250ms去获取返回结果，结果为空或者查询未超过1s，继续等待250ms
    timeout = 1
    poll_seconds = .250
    deadline = time.time() + timeout
    while time.time() < deadline and result.poll() == None:
        time.sleep(poll_seconds)
    if result.poll() == None:
        result.terminate()
        return 2
    ret = result.stdout.readline().split('\n')[0]
    if ret == 'Error: Unable to establish IPMI v2 / RMCP+ session':
        return 1
    elif ret == 'Chassis Power Control: Reset':
        return 0
    else:
        return 2


def server_soft_reset(manage_ip, sn):
    '''
        远程软重启
    :param manage_ip:
    :param sn:
    :return: 返回3，机器状态已经为操作预期状态；返回2，ipmi操作超时，请重新下发指令；
             返回1，ipmi无法使用，请联系管理员查看；返回0，操作成功
    '''
    # 远程软重启前先确定物理机状态, 关机状态不允许操作
    host_status = server_status(manage_ip, sn)
    if host_status is 1 or host_status is 2:
        return 1
    if host_status is 'Chassis Power is off':
        return 3

    command = "ipmitool -I lanplus -H %s -U %s -P %s power cycle" % \
              (manage_ip, default.SERVER_USER, encrypt_helper.decrypt(default.SERVER_PWD) + sn)
    result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # 设置超时规则，每250ms去获取返回结果，结果为空或者查询未超过1s，继续等待250ms
    timeout = 1
    poll_seconds = .250
    deadline = time.time() + timeout
    while time.time() < deadline and result.poll() == None:
        time.sleep(poll_seconds)
    if result.poll() == None:
        result.terminate()
        return 2
    ret = result.stdout.readline().split('\n')[0]
    if ret == 'Error: Unable to establish IPMI v2 / RMCP+ session':
        return 1
    elif ret == 'Chassis Power Control: Cycle':
        return 0
    else:
        return 2
