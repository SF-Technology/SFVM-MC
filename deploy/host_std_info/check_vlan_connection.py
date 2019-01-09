#!/usr/bin/python2.7
import sys
import ast
import locale
import subprocess

vlan_test_info_list = str(sys.argv[1])
vlan_test_info_list = ast.literal_eval(vlan_test_info_list)


def execute_command(cmd):
        s = subprocess.Popen(str(cmd), stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
        stdout = s.stdout.read().decode(locale.getpreferredencoding())
        stderr = s.stderr.read().decode(locale.getpreferredencoding())
        return_code = s.poll()
        return return_code

error_result=[]
for test_info in vlan_test_info_list:
        cmd = '/sbin/arping -q -c 2 -w 3 -D  -I %s %s >/dev/null 2>&1' %(test_info['bridge'], test_info['gateway'])
        result = execute_command(cmd)
        if result != 1:
                error_result.append(test_info['vlan'])

if error_result:
        print error_result
        sys.exit(1)
else:
        sys.exit(0)
