# coding=utf8
'''
    组件健康状态监控
'''


import json_helper
from model.const_define import ErrorCode
from lib.shell import cmd
import logging


def health_monitor():
    # 首先根据supervisor判断启动的组件是否都是RUNNING正常状态
    status_cmd = "sudo supervisorctl status | awk '{print $2}'"
    status_cmd_out = cmd.ShellCmd(status_cmd).stdout
    status_list = str(status_cmd_out).split('\n')

    print status_cmd_out
    print status_list

    status_flag = True
    for _status in status_list:
        if _status and _status != 'RUNNING':
            status_flag = False
            break

    if not status_flag:
        logging.error('there exist no health process when health monitor')
        return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, data='sick')

    # 然后从启动的组件中，检测指定组件的进程状态
    name_cmd = "sudo supervisorctl status | awk '{print $1}'"
    name_cmd_out = cmd.ShellCmd(name_cmd).stdout
    name_list = str(name_cmd_out).split('\n')

    print name_cmd_out
    print name_list

    # 判断主程序 8080端口
    if "kvmmgr_dashboard" in name_list:
        dashboard_cmd = "netstat -anp | grep 8080 | grep LISTEN"
        dashboard_cmd_out = cmd.ShellCmd(dashboard_cmd).stdout
        if not dashboard_cmd_out:
            logging.error('kvmmgr_dashboard port:8080 is no run when health monitor')
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, data='sick')

    # 判断虚拟机console 6080端口
    if "kvmmgr_dashboard_instance_console" in name_list:
        vm_console_cmd = "netstat -anp | grep 6080 | grep LISTEN"
        vm_console_cmd_out = cmd.ShellCmd(vm_console_cmd).stdout
        if not vm_console_cmd_out:
            logging.error('kvmmgr_dashboard_instance_console port:6080 is no run when health monitor')
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, data='sick')

    # 判断物理机console 4200端口
    if "kvmmgr_dashboard_host_console" in name_list:
        host_console_cmd = "netstat -anp | grep 4200 | grep LISTEN"
        host_console_cmd_out = cmd.ShellCmd(host_console_cmd).stdout
        if not host_console_cmd_out:
            logging.error('kvmmgr_dashboard_host_console port:4200 is no run when health monitor')
            return json_helper.format_api_resp(code=ErrorCode.SYS_ERR, data='sick')

    # 只要从返回数据中匹配上“health”，就表明各组件健康
    return json_helper.format_api_resp(code=ErrorCode.SUCCESS, data='health')