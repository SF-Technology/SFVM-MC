# -*- coding:utf-8 -*-
# __author__ =  ""

import sys
import os
import time


def get_file_mtime(vm_name):
    try:
        ftime = os.path.getmtime("/var/log/libvirt/qemu/%s.log" % vm_name)
        current_time = time.time()
        if (current_time - ftime) >= 86400:
            return '0'
        else:
            return '1'
    except:
        return '1'



if __name__ == '__main__':
  time = get_file_mtime(sys.argv[1])
  print time
