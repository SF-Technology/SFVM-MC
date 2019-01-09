#coding=utf8
'''
    pid工具  用户服务开启和停止时候创建和删除pid文件
'''

import os
import time
import signal

class PidUtil:

    def __init__(self, id, pidPath):
        self.id = id
        self.pidFile = pidPath

    def status(self):
        if not os.path.isfile(self.pidFile):
            return 0
        f = open(self.pidFile, 'r')
        pid = f.read()
        f.close()
        fname = '/proc/' + pid
        if not os.path.isdir(fname):
            return 0
        if os.stat(fname)[4] != os.getuid():
            return 0
        return int(pid)


    def start(self):
        pid = os.getpid()
        dname = os.path.dirname(self.pidFile)
        if not os.path.isdir(dname):
            os.makedirs(dname, 0755)
        f = open(self.pidFile, 'w')
        f.write(str(pid))
        f.close()
        return pid


    def clear(self):
        try:
            os.remove(self.pidFile)
        except:
            pass

    def stop(self):
        pid = self.status()
        if pid == 0:
            return -1
        for i in range(40):
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.1)
            if self.status() == 0:
                return 0
        return -2
