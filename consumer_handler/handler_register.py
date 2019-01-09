# coding=utf8


import time
import logging

from consumer_handler import instanceCreatePerformance
from lib.thread import thread_pool
from helper import json_helper
from consumer_handler import KAFKA_TOPIC_KEYS
import instanceHandler
import migrateHandler
import instanceCloneHandler
import cloneCreate
import instancediskconfig
import hotmigrateHandler

EVENT2FUNC = {
    KAFKA_TOPIC_KEYS['INSTANCE_CREATE']: [
        instanceHandler.create_instance
    ],
    KAFKA_TOPIC_KEYS['INSTANCE_COLD_MIGRATE']: [
        migrateHandler.cold_migrate
    ],
    KAFKA_TOPIC_KEYS['INSTANCE_DISKCONFIG']: [
        instancediskconfig.instance_disk_config
    ],
    KAFKA_TOPIC_KEYS['INSTANCE_CLONE_CREATE']: [
        cloneCreate.clone_create
    ],
    KAFKA_TOPIC_KEYS['INSTANCE_HOT_MIGRATE']: [
        hotmigrateHandler.hot_migrate
    ],
    KAFKA_TOPIC_KEYS['INSTANCE_CLONE']: [
        instanceCloneHandler.instance_clone
    ],
    KAFKA_TOPIC_KEYS['INSTANCE_CREATE_PERFORMANCE']: [
        instanceCreatePerformance.instance_performance
    ],
}


class Handler_simple():
    '''
        封装“从事件到处理函数”的映射关系
    '''
    def deal(self, msg):
        ''' 处理具体业务 '''
        if not msg:
            return

        decoded_data = self.decode_msg(msg)
        if not decoded_data:
            return

        topic_type = decoded_data.get('routing_key')
        handler_list = EVENT2FUNC.get(topic_type)
        if not handler_list:
            logging.info('need not handle')
            return

        for one_handler in handler_list:
            print "---start handler---"
            one_handler(msg)

    def decode_msg(self, msg):
        try:
            return json_helper.read(msg)
        except:
            return None


class Handler(thread_pool.ThreadPool):
    '''
        封装“从事件到处理函数”的映射关系
    '''
    def __init__( self, init_threads_num, max_threads_num, thread_idle_time):
        '''取事件对应的函数'''
        thread_pool.ThreadPool.__init__(self, init_threads_num, max_threads_num, thread_idle_time)

    def deal(self, msg):
        ''' 处理具体业务 '''
        if not msg:
            return

        decoded_data = self.decode_msg(msg)
        if not decoded_data:
            return

        self.set_clear_time()

        topic_type = decoded_data.get('routing_key')
        handler_list = EVENT2FUNC.get(topic_type)
        if not handler_list:
            logging.info('need not handle')
            return

        if not self.hasFreeThread():
            self.addThreads(1)

        for one_handler in handler_list:
            self.addTask(one_handler, msg)

        self.clear_idle_thread()

    def decode_msg(self, msg):
        try:
            return json_helper.read(msg)
        except:
            return None

    def set_clear_time(self):
        self.clear_time = time.time()

    def clear_idle_thread(self):
        # 每隔n分钟清理一下空闲已久的线程
        if time.time() - self.clear_time > 300 :
            self.removeFreeThread()
            self.clear_time = time.time()