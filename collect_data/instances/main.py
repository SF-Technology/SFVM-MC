# coding=utf8
'''
    收集instance数据、状态
'''


import env
env.init_env()

import threading
from time import sleep
from config.default import INSTANCES_COLLECT_INTERVAL, INSTANCES_COLLECT_WORK_INTERVAL, INSTANCES_COLLECT_NUMS
from collect import collect_instances_data, get_collect_hosts

if __name__ == '__main__':
    while True:
        hosts_data = get_collect_hosts(interval=INSTANCES_COLLECT_INTERVAL, nums=INSTANCES_COLLECT_NUMS)
        if not hosts_data:
            print 'no collect host now, please wait'
            # 任务休息
            sleep(INSTANCES_COLLECT_WORK_INTERVAL)

        all_threads = []
        for _host in hosts_data:
            _host_ip = _host['ipaddress']
            if _host_ip:
                # 收集instance数据
                collect_ins_t = threading.Thread(target=collect_instances_data, args=(_host_ip,),
                                                 name='thread-instance-' + _host_ip)
                all_threads.append(collect_ins_t)

        for thread in all_threads:
            thread.start()

        for thread in all_threads:
            thread.join()