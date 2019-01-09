# coding=utf8

'''
    ansible playbook操作
'''
from lib.shell.ansible_v2_base import AnsiblePlaybook


# 调用执行ansible_playbook函数
def ansible_run_playbook(playbook_url, remote_ip_str, host_dict, timeout=60):
    '''

    :param playbook_url: playbook = '/home/01369659/test_ansible/deploy/host_std_info/host_std.yaml
    :param remote_ip_str: '10.202.118.186'或者'10.202.118.186,10.202.118.187'
    :param host_dict:
    :param timeout:
    hostdict = {"srcdir": HOST_STANDARD_DIR,
                        "libvirt_user_pwd": decrypt(HOST_LIBVIRT_PWD),
                        "root_pwd": decrypt(ROOT_PWD),
                        "host_perform_data_url": HOST_PERFORMANCE_COLLECT_URL,
                        }
    :return:
        False, fail_msg、False, unreachable_msg或True, success_msg
    '''

    remote_ip_list = []
    if ',' in remote_ip_str:
        remote_ip_list = remote_ip_str.split(',')
    else:
        remote_ip_list.append(remote_ip_str)

    ansible_playbook = AnsiblePlaybook(playbook_url, remote_ip_str, host_dict, timeout)
    ansible_code, ansible_message = ansible_playbook.run()
    if ansible_code == 1000 or ansible_code == 1001 or ansible_code == 1002:
        return False, ansible_message
    else:
        ansible_playbook_result = ansible_playbook.get_result()
        success_msg, fail_msg, unreachable_msg = ansible_playbook_result.get('success', '')\
            , ansible_playbook_result.get('fail', ''), ansible_playbook_result.get('unreachable', '')
        if fail_msg:
            return False, "执行playbook标准化主机配置失败, 原因：%s" % fail_msg
        elif unreachable_msg:
            return False, "无法连接目标物理机"
        return True, success_msg


def run_standard_host(playbook_url, remote_ip_str, host_dict):
    '''
        物理机加入物理机集群跑playbook做标准化
    :param playbook_url:
    :param remote_ip_str:
    :param host_dict:
    :return:
    '''
    return ansible_run_playbook(playbook_url, remote_ip_str, host_dict, 1800)
