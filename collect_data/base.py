# coding=utf8
'''
    数据收集的共有方法
'''


from helper.time_helper import datetime_to_timestamp, get_timestamp, get_datetime_str


def check_collect_time_out_interval(last_collect_time, interval):
    '''
        检查上次收集时间是否超过了时间间隔
    :param last_collect_time:
    :param interval:
    :return:
    '''
    collect_timestamp = datetime_to_timestamp(last_collect_time)
    if get_timestamp() - collect_timestamp > interval:
        return True
    return False

class Global_define(object):
    '''全局变量'''
    @staticmethod
    def init():
        global _global_dict
        _global_dict = {}

    @staticmethod
    def set_value(key, value):
        """ 定义一个全局变量 """
        _global_dict[key] = value

    @staticmethod
    def get_value(key, defValue=[]):
        '''获得一个全局变量,不存在则返回默认值'''
        try:
            return _global_dict[key]
        except KeyError:
            return defValue