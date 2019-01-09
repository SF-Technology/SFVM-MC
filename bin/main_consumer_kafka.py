# coding=utf8
'''
    主程序
'''



import os
import sys
import time
import logging
import traceback
reload(sys)
sys.setdefaultencoding('utf-8')

import env
env.init_env()

from helper import log_helper
from config import GLOBAL_CONFIG, KAFKA_TOPIC_NAME
from consumer_handler import handler_register
from lib.mq import kafka_client
from service.s_instance import instance_service as ins_s
from service.s_instance_action import instance_action as ins_a_s
from helper import json_helper
#from lib.other import fileLock


def usage():
    print 'usage: python', ' your_appid start'
    sys.exit()


def start(consumer_id):
    try:
        config_info = GLOBAL_CONFIG.get('ASYNC_MESSAGE_BROKER')

        log_path = config_info.get('log_path')
        log_level = config_info.get('log_level')
        log_helper.add_timed_rotating_file_handler(log_path, logLevel=log_level)

        kafka_instance = kafka_client.MKafkaClient(**config_info.get('config'))
        kafka_instance.connect()

        # 初始化handler
        logging.info("config info %s", config_info)
        init_threads_num = config_info.get('init_threads_num', 32)
        max_threads_num = config_info.get('max_threads_num', 32)
        thread_idle_time = config_info.get('thread_idle_time', 60 * 5)
        handler_ins = handler_register.Handler(init_threads_num, max_threads_num, thread_idle_time)
        # handler_ins = handler_register.Handler_simple()

        # 开始接收消息
        topic_name = KAFKA_TOPIC_NAME
        # consumer = kafka_instance.get_consumer(topic_name)
        consumer = kafka_instance.get_balanced_consumer(topic_name)
        logging.info("start consumer")
        for msg_object in consumer:
            try:
                msg = msg_object.value
                print msg_object.offset
                if not msg:
                    time.sleep(1)
                else:
                    req_data = json_helper.read(msg)
                    data = json_helper.read(msg).get('data')
                    if req_data['routing_key'] == 'INSTANCE.CREATE':
                        # 检查虚拟机状态是否为创建中、创建失败，除此以外不重复创建
                        check_status, ins_status = ins_s.check_instance_status(data['uuid'])
                        if not check_status:
                            logging.info("can not find instance create from kafka")
                            logging.info(msg)
                        elif ins_status == '100':
                            logging.info(msg)
                            consumer.commit_offsets()
                            handler_ins.deal(msg)
                        elif ins_status == '0':
                            is_instance_exist = ins_a_s.whether_vm_repeat_create(data['request_id'])
                            if is_instance_exist:
                                logging.info("repeat job from kafka")
                                logging.info(msg)
                            else:
                                logging.info(msg)
                                consumer.commit_offsets()
                                handler_ins.deal(msg)
                        else:
                            logging.info("repeat instance create from kafka")
                            logging.info(msg)
                            consumer.commit_offsets()
                    elif req_data['routing_key'] == 'INSTANCE.CLONECREATE':
                        # 检查虚拟机状态是否为创建中、创建失败，除此以外不重复创建
                        check_status, ins_status = ins_s.check_instance_status(data['uuid'])
                        if not check_status:
                            logging.info("can not find instance create from kafka")
                            logging.info(msg)
                        elif ins_status == '102':
                            logging.info(msg)
                            consumer.commit_offsets()
                            handler_ins.deal(msg)
                        elif ins_status == '0':
                            is_instance_exist = ins_a_s.whether_vm_repeat_create(data['request_id'])
                            if is_instance_exist:
                                logging.info("repeat job from kafka")
                                logging.info(msg)
                            else:
                                logging.info(msg)
                                consumer.commit_offsets()
                                handler_ins.deal(msg)
                        else:
                            logging.info("repeat instance create from kafka")
                            logging.info(msg)
                            consumer.commit_offsets()
                    elif req_data['routing_key'] == 'INSTANCE.CLONE':
                        # 检查虚拟机状态是否为创建中、创建失败，除此以外不重复创建
                        check_status, ins_status = ins_s.check_instance_status(data['uuid'])
                        if not check_status:
                            logging.info("can not find instance create from kafka")
                            logging.info(msg)
                        elif ins_status == '102':
                            logging.info(msg)
                            consumer.commit_offsets()
                            handler_ins.deal(msg)
                        elif ins_status == '0':
                            is_instance_exist = ins_a_s.whether_vm_repeat_create(data['request_id'])
                            if is_instance_exist:
                                logging.info("repeat job from kafka")
                                logging.info(msg)
                            else:
                                logging.info(msg)
                                consumer.commit_offsets()
                                handler_ins.deal(msg)
                        else:
                            logging.info("repeat instance create from kafka")
                            logging.info(msg)
                            consumer.commit_offsets()
                    elif req_data['routing_key'] == 'INSTANCE.PERFORMANCE':
                        logging.info(msg)
                        consumer.commit_offsets()
                        handler_ins.deal(msg)

                    else:
                        is_instance_exist = ins_a_s.whether_vm_repeat_create(data['request_id'])
                        if is_instance_exist:
                            logging.info("repeat job from kafka")
                            logging.info(msg)
                        else:
                            logging.info(msg)
                            consumer.commit_offsets()
                            handler_ins.deal(msg)
            except:
                logging.error(traceback.format_exc())

        handler_ins.waitAndStopAll()

    except:
        print traceback.format_exc()
    logging.info(consumer_id + ' stop')
    sys.exit()


if __name__ == '__main__':
    #print len(sys.argv)
    #print sys.argv
    if len(sys.argv) != 3:
        usage()
    if sys.argv[1] == 'start':
        #os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
        start(sys.argv[2])
    else:
        usage()

