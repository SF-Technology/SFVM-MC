# coding=utf8
'''
    Balant接口调用
'''
# __author__ =  ""

from helper.http_helper import http_post_json
from config.default import BALANT_BASE, API_GET_TARGET_ID, API_GET_METRICS, API_GET_METRIC_DATA, BALANT_ATTR
from collections import defaultdict
import logging


def get_target_id(ip):
    '''
        获取target ID
    :param ip:
    :return:
    '''
    code, error, data = http_post_json(BALANT_BASE + API_GET_TARGET_ID,
                                                   req_data={"action": 103,
                                                             "keyword": ip,
                                                             "typeId": 1})

    if data['Return']:
        target_id = data['Return'][0]['id']
    else:
        target_id = ''

    return target_id


def get_metric_id(target_id):
    '''
        获取监控项IDS
    :param target_id:
    :return:
    '''
    metric_ids = []

    if not target_id:
        return [""] * len(BALANT_ATTR)

    code, error, data = http_post_json(BALANT_BASE + API_GET_METRICS,
                                       req_data={"action": 104,
                                                 "userId": "admin",
                                                 "targetId": target_id})

    for attr in BALANT_ATTR:
        metric_id = ""
        for i in data['Return']:
            if i['attrName'] == attr:
                if i['attrName'] in ['RxBytes', 'TxBytes']:
                    if i['objName'] == 'eth1':
                        metric_id = str(i['id'])
                elif i['attrName'] in ['recBytesPerSec', 'sendBytesPerSec']:
                    if i['objName'] == 'bond0' or i['objName'] == 'eth0':
                        metric_id = str(i['id'])
                else:
                    metric_id = str(i['id'])

        metric_ids.append(metric_id)

    return metric_ids


def get_metric_data(req_ips, metric_list, start_time, end_time):
    '''
        获取Balent数据
    :param req_ips:
    :param metric_list:
    :param start_time:
    :param end_time:
    :return:
    '''
    metric_data = defaultdict(lambda: list([[]]*len(BALANT_ATTR)))
    metric_id = []

    if not any([any(x) for x in metric_list]):
        return metric_data

    for i in range(0, len(req_ips)):
        metric_id.extend(filter(lambda z: z if z else None, metric_list[i]))
    metric_id = ','.join(metric_id)

    # 修改102为103
    code, error, data = http_post_json(BALANT_BASE + API_GET_METRIC_DATA,
                                       req_data={"action": 103,
                                                 "userId": "admin",
                                                 "metricId": metric_id,
                                                 "startTime": start_time,
                                                 "endTime": end_time
                                                 })
    req_data = {"action": 103,
                "userId": "admin",
                "metricId": metric_id,
                "startTime": start_time,
                "endTime": end_time}
    logging.info(str(start_time))
    logging.info(str(end_time))
    print 'XXXXXX', BALANT_BASE + API_GET_METRIC_DATA, req_data

    temp_metric = []
    for i in metric_list:
        temp_metric.extend(i)

    for m_data in data['Return']:
        res_metric = str(m_data['id'])
        # res_obj = str(m_data['objName'])
        for ip, m_metric in zip(req_ips, metric_list):
            temp_metric_data = []
            if res_metric in m_metric:
                for m in m_data['dataList']:
                    temp_metric_data.append([m['handCollectionTime'], m['valueExp']])
                metric_data[ip][m_metric.index(res_metric)] = temp_metric_data

    print metric_data
    # print res_obj
    return metric_data