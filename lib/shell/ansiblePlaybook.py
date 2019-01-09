# coding=utf8
'''
    ansible操作
'''
# __author__ =  ""


import ansible.runner
import ansible.playbook
from config.default import ANSIABLE_REMOTE_PWD, ANSIABLE_REMOTE_SU_PWD, ANSIABLE_REMOTE_USER, ANSIABLE_REMOTE_SU_USER
from helper.encrypt_helper import decrypt
import ansible.runner
import os
import logging
from ansible import utils
from ansible import callbacks
from helper.log_helper import add_timed_rotating_file_handler_for_hoststd


# 日志格式化
def _init_log(service_name):
    log_basic_path = os.path.dirname(os.path.abspath(__file__))[0:-9]
    log_name = log_basic_path + 'log/' + str(service_name) + '.log'
    add_timed_rotating_file_handler_for_hoststd(log_name, logLevel='WARNING')

class PlaybookRunnerCallbacks(callbacks.PlaybookRunnerCallbacks):

    def __init__(self, stats, verbose=None):
        super(PlaybookRunnerCallbacks, self).__init__(stats, verbose)

    def on_ok(self, host, host_result):
        super(PlaybookRunnerCallbacks, self).on_ok(host, host_result)
        logging.warning('===on_ok====host=%s===result=%s'%(host,host_result))

    def on_unreachable(self, host, results):
        super(PlaybookRunnerCallbacks, self).on_unreachable(host, results)
        logging.warning('===on_unreachable====host=%s===result=%s'%(host,results))

    def on_failed(self, host, results, ignore_errors=False):
        super(PlaybookRunnerCallbacks, self).on_failed(host, results, ignore_errors)
        logging.warning('===on_unreachable====host=%s===result=%s'%(host,results))

    def on_skipped(self, host, item=None):
        super(PlaybookRunnerCallbacks, self).on_skipped(host, item)
        logging.warning("this task does not execute,please check parameter or condition.")

class PlaybookCallbacks(callbacks.PlaybookCallbacks):

    def __init__(self,verbose=False):
        super(PlaybookCallbacks, self).__init__(verbose)

    def on_stats(self, stats):
        super(PlaybookCallbacks, self).on_stats( stats)
        logging.warning("palybook executes completed====")

stats = callbacks.AggregateStats()
runner_cb = PlaybookRunnerCallbacks(stats, verbose=utils.VERBOSITY)
playbook_cb = PlaybookCallbacks()

def ansible_run_playbook(play, host_list, params):
    # _init_log('host_std_playbook')
    logging.info('now start to playbook')
    pb = ansible.playbook.PlayBook(
                                    playbook=play,
                                    host_list=host_list,
                                    stats=stats,
                                    callbacks=playbook_cb,
                                    runner_callbacks=runner_cb,
                                    check=False,
                                    extra_vars=params,
                                    remote_user=ANSIABLE_REMOTE_USER,
                                    remote_pass=decrypt(ANSIABLE_REMOTE_PWD),
                                    become=True,
                                    become_method='su',
                                    become_user=ANSIABLE_REMOTE_SU_USER,
                                    become_pass=decrypt(ANSIABLE_REMOTE_SU_PWD)
                                    )
    result = pb.run()
    playbook_cb.on_stats(pb.stats)
    return result
