# coding=utf8
'''
    收集host数据、状态
'''


import env
env.init_env()

import threading
from time import sleep

from config.default import HOST_COLLECT_INTERVAL, HOST_COLLECT_WORK_INTERVAL, HOST_COLLECT_NUMS
from collect import collect_host_data, get_collect_hosts

if __name__ == '__main__':
    while True:
        hosts_data = get_collect_hosts(interval=HOST_COLLECT_INTERVAL, nums=HOST_COLLECT_NUMS)
        if not hosts_data:
            print 'no collect host now, please wait'
            # 任务休息
            sleep(HOST_COLLECT_WORK_INTERVAL)

        all_threads = []
        for _host in hosts_data:
            _host_ip = _host['ipaddress']
            if _host_ip:
                # 收集host数据
                collect_host_t = threading.Thread(target=collect_host_data, args=(_host_ip,), name='thread-host-' + _host_ip)
                all_threads.append(collect_host_t)
                collect_host_t.start()

        # for thread in all_threads:
        #    thread.start()

        for thread in all_threads:
            thread.join()
