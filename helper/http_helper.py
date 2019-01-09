
# coding=utf8
'''
    Balant接口调用
'''
# __author__ =  ""

import requests
import urllib2
from urllib2 import HTTPError, URLError
import json_helper


class HttpHelper:
    '''
        get put post delete 返回的是request的response对象
    '''

    def __init__(self, url, timeout=20):
        self.url = url
        self.timeout = timeout

    def http_get(self, params=None):
        '''
        :param dict params:  {'key1':'value1','key2':'value2'}
        :return:
        '''
        ret = requests.get(self.url, data=params, timeout = self.timeout)
        return ret

    def http_post(self, params=None):
        '''
        :param dict params:  {'key1':'value1','key2':'value2'}
        :return:
        '''
        ret = requests.post(self.url, params, timeout = self.timeout)
        return ret

    def http_put(self, params=None):
        '''
        :param dict params:  {'key1':'value1','key2':'value2'}
        :return:
        '''
        ret = requests.put(self.url, data = params, timeout = self.timeout)
        return ret

    def http_delete(self, params):
        '''
        :param dict params:  {'key1':'value1','key2':'value2'}
        :return:
        '''
        ret = requests.delete(self.url, data=params, timeout=self.timeout)
        return ret


def http_post_json(url, req_data=None, header=None):
    code = -1
    error = ''
    data={}
    req_data = {} if req_data is None else req_data
    header = {} if header is None else header

    request = urllib2.Request(url)
    request.add_header('Content-Type', 'application/json')

    for k, v in header.items():
        request.add_header(k, v)

    try:
        resp = urllib2.urlopen(request, json_helper.dumps(req_data)).read()
        data = json_helper.loads(resp)
    except HTTPError, e:
        code = e.code
        error = e.strerror
    except Exception, e:
        error = str(e)
    finally:
        return code, error, data
