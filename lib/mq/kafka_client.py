# coding=utf8


from pykafka import KafkaClient
from config import GLOBAL_CONFIG
import json_helper
from config import KAFKA_TOPIC_NAME
import logging
import datetime


class MKafkaClient:

    def __init__(self, hosts, zookeeper_hosts, broker_version, **kwargs):
        self.hosts = hosts
        self.zookeeper_hosts = zookeeper_hosts
        self.broker_version = broker_version
        self.client = None
        self.consumer_group = 'ESG_CLOUD_PORTAL_CONSUMER'

    def connect(self):
        self.client = KafkaClient(hosts=self.hosts,
                                  zookeeper_hosts=self.zookeeper_hosts,
                                  broker_version=self.broker_version)

    def choose_topic(self, topic_name):
        '''
        :param topic_name:
        :return: topic object
        '''
        return self.client.topics[topic_name]

    def send_msg(self, topic_name, msg):
        topic = self.choose_topic(topic_name)
        return topic.get_sync_producer().produce(msg)

    def get_consumer(self, topic_name):
        return self.choose_topic(topic_name).get_simple_consumer()

    def get_balanced_consumer(self, topic_name):
        return self.choose_topic(topic_name).get_balanced_consumer(consumer_group=self.consumer_group,
                                                                   auto_commit_enable=False,
                                                                   zookeeper_connect=self.zookeeper_hosts,
                                                                   rebalance_max_retries=10,
                                                                   rebalance_backoff_ms=10 * 1000
                                                                   )


def send_async_msg(topic=KAFKA_TOPIC_NAME, msg=None):
    '''
        发送KAFKA消息
    :param topic:
    :param msg:
    :return:
    '''
    logging.info('kafka send async msg, date: {}'.format(datetime.datetime.now()))
    config_info = GLOBAL_CONFIG.get('ASYNC_MESSAGE_BROKER')
    client = KafkaClient(
        hosts=config_info.get('config').get('hosts'),
        zookeeper_hosts=config_info.get('config').get('zookeeper_hosts'),
        broker_version=config_info.get('config').get('broker_version')
    )
    """
    topic = client.topics[topic]
    with topic.get_sync_producer() as producer:
        producer.produce(json_helper.dumps(msg))
    return 'success'
    """
    topic = client.topics[topic]
    producer = topic.get_sync_producer()
    return producer.produce(json_helper.dumps(msg))







