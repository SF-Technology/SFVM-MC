# -*- coding:utf-8 -*-

'''
    ansible2.0底层类库
'''

from collections import namedtuple
from config.default import ANSIABLE_REMOTE_PWD, ANSIABLE_REMOTE_SU_PWD, ANSIABLE_REMOTE_USER, ANSIABLE_REMOTE_SU_USER
from helper.encrypt_helper import decrypt
from ansible.parsing.dataloader import DataLoader
# from ansible.vars import VariableManager
# from ansible.inventory import Inventory
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.plugins.callback import CallbackBase
from ansible.errors import AnsibleError
from ansible import constants as C
import os
import shutil
import json


# 记录调用结果类（包括记录日志）
class ResultsCollector(CallbackBase):

    def __init__(self, *args, **kwargs):
        super(ResultsCollector, self).__init__(*args, **kwargs)
        self.status_no_hosts = False
        self.host_ok = {}
        self.host_failed = {}
        self.host_unreachable = {}
        self.host_skipped = {}

    def v2_playbook_on_no_hosts_matched(self):
        self.playbook_on_no_hosts_matched()
        self.status_no_hosts = True

    def _get_return_data(self, result):
        try:
            if result.get('msg', None):
                return_data = result.get('msg')
            elif result.get('stderr', None):
                return_data = result.get('stderr')
            else:
                return_data = result
        except:
            pass
        return return_data.encode('utf-8')

    def v2_runner_on_ok(self, result):
        host = result._host.get_name()
        self.runner_on_ok(host, result._result)
        self.host_ok[host] = result

    def v2_runner_on_failed(self, result, ignore_errors=False):
        host = result._host.get_name()
        self.runner_on_failed(host, result._result, ignore_errors)
        return_data = self._get_return_data(result._result)
        self.host_failed[host] = result

    def v2_runner_on_unreachable(self, result):
        host = result._host.get_name()
        self.runner_on_unreachable(host, result._result)
        return_data = self._get_return_data(result._result)
        self.host_unreachable[host] = result

    def v2_runner_on_skipped(self, result):
        if C.DISPLAY_SKIPPED_HOSTS:
            host = result._host.get_name()
            self.runner_on_skipped(host, self._get_item(getattr(result._result,'results', {})))
            self.host_skipped[host] = result

    def v2_playbook_on_stats(self, stats):
        log_msg = '===========palybook executes completed========'


class AnsibleShell(object):

    '''
    ansible shell模块功能类（适用于module='shell'或者module='copy'的命令）
    '''

    def __init__(self, host_list, timeout=10):
        '''
        :param host_list: hostlist = ['10.202.118.186']
        :param hostdict:
               hostdict = {"srcdir": HOST_STANDARD_DIR,
                 "libvirt_user_pwd": decrypt(HOST_LIBVIRT_PWD),
                 "root_pwd": decrypt(ROOT_PWD),
                 "host_perform_data_url": HOST_PERFORMANCE_COLLECT_URL,
                 "ansible_ssh_user": ANSIABLE_REMOTE_USER,
                 "ansible_ssh_pass": decrypt(ANSIABLE_REMOTE_PWD)}
        '''

        hostdict = {
                    "ansible_ssh_user": ANSIABLE_REMOTE_USER,
                    "ansible_ssh_pass": decrypt(ANSIABLE_REMOTE_PWD)
        }

        self.host_list = host_list + ','
        self.host_dict = hostdict

        Options = namedtuple('Options',
                             ['connection',
                              'remote_user',
                              'ask_sudo_pass',
                              'verbosity',
                              'ack_pass',
                              'module_path',
                              'forks',
                              'become',
                              'become_method',
                              'become_user',
                              'check',
                              'listhosts',
                              'listtasks',
                              'listtags',
                              'syntax',
                              'sudo_user',
                              'sudo',
                              'timeout',
                              'diff'])
        self.options = Options(
            connection='smart',
            remote_user=ANSIABLE_REMOTE_USER,
            ack_pass=None,
            sudo_user=ANSIABLE_REMOTE_SU_USER,
            forks=200,
            sudo='yes',
            ask_sudo_pass=False,
            verbosity=5,
            module_path=None,
            become=True,
            become_method='su',
            become_user=ANSIABLE_REMOTE_SU_USER,
            check=False,
            listhosts=None,
            listtasks=None,
            listtags=None,
            syntax=None,
            timeout=timeout,
            diff=False)

        self.loader = DataLoader()
        # self.inventory = Inventory(loader=self.loader, variable_manager=self.variable_manager, host_list=self.host_list)
        self.inventory = InventoryManager(loader=self.loader, sources=self.host_list)

        self.variable_manager = VariableManager(loader=self.loader, inventory=self.inventory)
        # self.variable_manager.set_inventory(self.inventory)
        self.variable_manager.extra_vars = self.host_dict
        self.passwords = {'become_pass': decrypt(ANSIABLE_REMOTE_SU_PWD),
                          'remote_pass': decrypt(ANSIABLE_REMOTE_PWD)}

    def run(self, command, remote_password=None):
        '''
            run() 用于普通shell命令
        :param command: command = 'ls /'
        :return:
            code: 0(正常) 3(unreachable) 其他
             data: {'fact_cache': <ansible.plugins.cache.FactCache object at 0x7f1f003808d0>,
                    'extra_vars': {
                                    'libvirt_user_pwd':
                                    'ansible_ssh_user':
                                    'root_pwd':
                                    'host_perform_data_url':
                                    'srcdir':
                                    'ansible_ssh_pass': },
                'host_vars_files': defaultdict(<type 'dict'>, {}),
                'np_fact_cache': defaultdict(<type 'dict'>, {
                    u'10.203.52.152':{u'shell_out':
                            {u'changed': True,
                             u'end': u'2018-01-24 15:32:23.267856',
                             u'stdout': ,
                            u'cmd': ,
                             u'rc': ,
                             u'start': u'2018-01-24 15:32:22.671536',
                             u'stderr': u'',
                             u'delta': u'0:00:00.596320',
                             'stdout_lines': ,
                             u'warnings': []}}}),
                'options_vars': defaultdict(<type 'dict'>, {}),
                 'group_vars_files': defaultdict(<type 'dict'>, {}),
                 'omit_token': ,
                  'vars_cache': }
        '''
        play_source = dict(
            name="Ansible Play",
            hosts='all',
            gather_facts='no',
            tasks=[
                dict(action=dict(module='shell', args=command), register='shell_out'),
                dict(action=dict(module='debug', args=dict(msg='{{shell_out.stdout}}')))
            ]
        )
        play = Play().load(play_source, variable_manager=self.variable_manager, loader=self.loader)

        # run it
        if not remote_password:
            remote_password = self.passwords
        tqm = None
        self.results_callback = ResultsCollector()
        try:
            tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.options,
                passwords=remote_password,
                stdout_callback=self.results_callback
                # run_additional_callbacks=C.DEFAULT_LOAD_CALLBACK_PLUGINS,
            )
            # self.results_callback = ResultsCollector()
            data = self.variable_manager.__getstate__()
            ret = tqm.run(play)
        finally:
            if tqm is not None:
                tqm.cleanup()
            shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)

        return ret, data

    def copy_file_run(self, src_file, dst_file, remote_password=None):
        play_source = dict(
            name="Ansible Copy File Play",
            hosts='all',
            gather_facts='no',
            tasks=[
                dict(action=dict(module='copy', args='src=%s dest=%s' % (src_file, dst_file)), register='shell_out')
                # dict(action=dict(module='debug', args=dict(msg='{{shell_out.stdout}}')))
            ]
        )
        play = Play().load(play_source, variable_manager=self.variable_manager, loader=self.loader)

        # run it
        if not remote_password:
            remote_password = self.passwords
        tqm = None
        self.results_callback = ResultsCollector()
        try:
            tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.options,
                passwords=remote_password,
                stdout_callback=self.results_callback,
                # run_additional_callbacks=C.DEFAULT_LOAD_CALLBACK_PLUGINS,
            )
            # self.results_callback = ResultsCollector()
            data = self.variable_manager.__getstate__()
            ret = tqm.run(play)
        finally:
            if tqm is not None:
                tqm.cleanup()
            shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)
        return ret, data


class AnsiblePlaybook(object):
    '''
        ansible_playbook功能类
    '''
    def __init__(self, playbook, host_list, hostdict, timeout=60):
        '''

        :param playbook: playbook= '/home/01369659/test_ansible/deploy/host_std_info/host_std.yaml'
        :param host_list: hostlist = ['10.202.118.186']
        :param hostdict:
        hostdict = {"srcdir": HOST_STANDARD_DIR,
                 "libvirt_user_pwd": decrypt(HOST_LIBVIRT_PWD),
                 "root_pwd": decrypt(ROOT_PWD),
                 "host_perform_data_url": HOST_PERFORMANCE_COLLECT_URL,
                 }

        '''
        hostdict["ansible_ssh_user"] = ANSIABLE_REMOTE_USER
        hostdict["ansible_ssh_pass"] = decrypt(ANSIABLE_REMOTE_PWD)

        self.playbook_path = playbook
        self.host_list = host_list + ','
        self.host_dict = hostdict

        Options = namedtuple('Options',
                             ['connection',
                              'remote_user',
                              'ask_sudo_pass',
                              'verbosity',
                              'ack_pass',
                              'module_path',
                              'forks',
                              'become',
                              'become_method',
                              'become_user',
                              'check',
                              'listhosts',
                              'listtasks',
                              'listtags',
                              'syntax',
                              'sudo_user',
                              'sudo',
                              'timeout',
                              'diff'])
        self.options = Options(
            connection='smart',
            remote_user=ANSIABLE_REMOTE_USER,
            ack_pass=None,
            sudo_user=ANSIABLE_REMOTE_SU_USER,
            forks=200,
            sudo='yes',
            ask_sudo_pass=False,
            verbosity=5,
            module_path=None,
            become=True,
            become_method='su',
            become_user=ANSIABLE_REMOTE_SU_USER,
            check=False,
            listhosts=None,
            listtasks=None,
            listtags=None,
            syntax=None,
            timeout=timeout,
            diff=False)

        # self.variable_manager = VariableManager()
        # self.loader = DataLoader()
        # # self.inventory = Inventory(loader=self.loader, variable_manager=self.variable_manager, host_list=self.host_list)
        # self.inventory = InventoryManager(loader=self.loader, sources=self.host_list)
        # self.variable_manager.set_inventory(self.inventory)
        # self.variable_manager.extra_vars = self.host_dict
        self.loader = DataLoader()
        # self.inventory = Inventory(loader=self.loader, variable_manager=self.variable_manager, host_list=self.host_list)
        self.inventory = InventoryManager(loader=self.loader, sources=self.host_list)

        self.variable_manager = VariableManager(loader=self.loader, inventory=self.inventory)
        # self.variable_manager.set_inventory(self.inventory)
        self.variable_manager.extra_vars = self.host_dict
        self.passwords = {
                            'become_pass': decrypt(ANSIABLE_REMOTE_SU_PWD),
                            'remote_pass': decrypt(ANSIABLE_REMOTE_PWD)
        }

    # 定义运行的方法和返回值
    def run(self):
        if not os.path.exists(self.playbook_path):
            code = 1000
            results = {'playbook': self.playbook_path, 'msg': self.playbook_path + ' playbook is not exist',
                       'flag': False}
            return code, results
            # results=self.playbook_path+'playbook is not existed'
            # return code,complex_msg,results
        playbook = PlaybookExecutor(playbooks=[self.playbook_path],
                                inventory=self.inventory,
                                variable_manager=self.variable_manager,
                                loader=self.loader,
                                options=self.options,
                                passwords=self.passwords)
        self.results_callback = ResultsCollector()
        playbook._tqm._stdout_callback = self.results_callback
        try:
            code = playbook.run()
        except AnsibleError:
            code = 1001
            results = {'playbook': self.playbook_path, 'msg': self.playbook_path + ' playbook have syntax error',
                       'flag': False}
            # results='syntax error in '+self.playbook_path #语法错误
            return code, results
        if self.results_callback.status_no_hosts:
            code = 1002
            results = {'playbook': self.playbook_path, 'msg': self.results_callback.status_no_hosts, 'flag': False,
                       'executed': False}
            # results='no host match in '+self.playbook_path
            return code, results
        return code, ''

    def get_result(self):
        '''
            返回playbook结果
        :return: {'success': {}, 'fail': {}, 'unreachable': {}}
        '''
        self.result_all = {'success': {}, 'fail': {}, 'unreachable': {}}
        # print result_all
        # print dir(self.results_callback)

        # unreachable message
        for host, result in self.results_callback.host_unreachable.items():
            self.result_all['unreachable'][host] = result._result.get('msg', '')
            return self.result_all

        # fail message
        for host, result in self.results_callback.host_failed.items():
            self.result_all['fail'][host] = result._result.get('stderr', '')
            return self.result_all

        # success message
        for host, result in self.results_callback.host_ok.items():
            self.result_all['success'][host] = result._result.get('msg', '')
            return self.result_all

        return self.result_all
