# -*- coding:utf-8 -*-

'''
import os, sys, signal
import getpass
import logging
import subprocess
import time
from IPy import IP
import requests
import json

# Path to our application
APPLICATION_PATH = os.path.split(__file__)[0]


def took_too_long():
    """
    Called when :meth:`main` takes too long to run its course (idle timeout
    before any connection was made).
    """
    timeout_script = os.path.join(APPLICATION_PATH, 'timeout.sh')
    sys.stdout.flush()
    # Calling execv() so we can quit the main process to reduce memory usage
    os.execv('/bin/sh', ['-c', timeout_script])
    os._exit(0)


def ssh_login():
    warn_msg = "**************************************************************\nIf you are not manager, please close the windows.\nAll your operation will be record, S.F.Express Group Co., Ltd.\n**************************************************************\n\n"
    logger_migrate_md5get = logging.getLogger('log_ipmi')
    logger_migrate_md5get.setLevel(logging.DEBUG)
    fh_migrate_md5get = logging.FileHandler('log_ipmi.log')
    fh_migrate_md5get.setLevel(logging.DEBUG)
    valid_user = False
    if len(sys.argv) < 2:
        print(warn_msg)
        while not valid_user:
            user = raw_input('input login user: ')
            if not user:
                continue
            else:
                passwd = getpass.getpass('input passwd:')
                if not passwd:
                    continue
                else:
                    return 0
    user_input = sys.argv[1]
    user_cookie = sys.argv[2]
    if len(user_input) > 100 or not user_cookie:
        return 0
    # 验证cookie是否合法
    url = 'http://localhost:8080/login/user'
    cookie = {'session': user_cookie}
    # headers = {"Cookie": "session=" + cookie}
    r = requests.get(url, cookies=cookie)
    if r.status_code != 200:
        return 0

    ret = json.loads(r.text.decode('utf-8'), encoding='utf-8')
    if ret['code'] == -10005:
        return 0
    elif ret['code'] == 0:
        args = user_input.split('&')
        dst_ip_from_front = args[0].split('=')[1]
        dc_type = args[2].split('=')[1]
        if str(dc_type) == '4' or str(dc_type) == '5':
            host_sn = '2017'
        else:
            host_sn = args[1].split('=')[1][-4:]
        try:
            is_ip_right = IP(dst_ip_from_front)
            dst_ip = dst_ip_from_front
            dst_ip_write_to_file = "echo '" + dst_ip + "," + host_sn + "' > /home/sfblj/dstip"
            os.system(dst_ip_write_to_file)
            os.system('/usr/bin/ssh sfblj@localhost')
            return 0
        except:
            return 'error ip'
    else:
        return 0

if __name__ == "__main__":
    ssh_login()

'''