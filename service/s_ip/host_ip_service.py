# coding=utf8
'''
    主机IP服务
'''


import json


def get_host_used(ip):
    '''
    从"/app/info/ip地址"获取指定host的当前使用率信息
    mem_size:内存总大小，单位MB
    disk_size:存储镜像的卷大小，单位GB
    '''
    with open("/app/info/%s" % ip, 'r') as f:
        data = json.load(f)

    return {
        "ip": data["ip"],
        "hostname": data["hostname"],
        "cpu_core": int(data["cpu_core"]),
        "mem_size": int(data["mem_size"]),
        "disk_size": int(data["disk_size"]),
        "current_cpu_used": int(data["current_cpu_used"]),
        "current_mem_used": int(data["current_mem_used"]),
        "current_disk_used": int(data["current_disk_used"]),
        "week_cpu_p95_used": int(data["week_cpu_p95_used"]),
        "week_mem_p95_used": int(data["week_mem_p95_used"]),
        "assign_mem": get_host_assign_mem(ip)
    }


def get_host_assign_mem(ip):
    '''
    获取指定ip上已分配的内存空间，单位GB
    '''
    # todo
    pass