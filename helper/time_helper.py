# coding=utf8
'''
    时间封装函数
'''
# __author__ =  ""

import time
import datetime


def get_datetime_str():
    '''
    :return:  2015-10-20 14:21:01
    '''
    return time.strftime("%Y-%m-%d %X")

def get_datatime_one_str():
    '''
        :return:  2015-10-20 14:21:01
        '''
    return time.strftime("%Y-%m-%d-%X")


def get_datetime_str_link():
    '''
    :return:  20151020142101
    '''
    return time.strftime("%Y%m%d%H%M%S")


def get_date_ymd_str():
    '''
    :return:  2015-10-20
    '''
    return time.strftime("%Y-%m-%d")


def get_timestamp(is_int=1):
    '''

    :param is_int: 是否需要返回整型的
    :return  int  or float:
    '''
    ts = time.time()
    if is_int:
        ts = int(ts)
    return ts


def change_datetime_to_timestamp(date_time):
    '''
        将日期转换时间戳
    :param date_time:
    :return:
    '''
    timearray = time.strptime(date_time, "%Y-%m-%d %H:%M:%S")
    ts = int(time.mktime(timearray)) * 1000
    return ts


def get_future_datetime(seconds):
    '''
        获取未来的日期
        params  int seconds  秒数
    :return: 2015-10-11 21:11:03
    '''
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() + seconds))


def get_before_datetime(seconds):
    '''
        获取过去的日期
    :param int seconds: 秒数
    :return 2015-09-11 20:12:33:
    '''
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() - seconds))


def datetime_to_str(the_datetime):
    '''
        datetime类型转换成标准格式时间字符串
    :param the_datetime:
    :return:
    '''
    return the_datetime.strftime("%Y-%m-%d %H:%M:%S")


def datetime_to_timestamp(the_datetime, is_float=False):
    '''
        datetime类型转成时间戳
    :param is_float:
    :param the_datetime:
    :return int / float:
    '''
    ms = time.mktime(the_datetime.timetuple())
    if not is_float:
        ms = int(ms)
    return ms


def timestamp_to_datetime(timestamp):
    '''
        时间戳转成datetime类型
    :param timestamp:
    :return:
    '''
    # 转换成localtime
    time_local = time.localtime(timestamp)
    dt = time.strftime("%Y-%m-%d %H:%M:%S",time_local)
    return dt


def get_range_timestamp_str(str_range, style='ts'):
    '''
        获取范围内的开始时间和结束时间
    :param str_range:
    :param style: ts:时间戳 dt:datetime类型
    :return: timestamp or datetime
    '''
    str_start, str_end = '', ''

    try:
        # 距离现在多少分钟，根据此距离算出开始时间和结束时间
        minutes_range = int(str_range)
        str_start = str((datetime.datetime.now() - datetime.timedelta(minutes=minutes_range)).strftime('%Y-%m-%d %H:%M:%S'))
        str_end = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    except ValueError, err:

        if str_range == 'today':
            str_start = str(datetime.date.today()) + " 00:00:01"
            str_end = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        elif str_range == 'yester':
            str_start = str(datetime.date.today() - datetime.timedelta(days=1)) + " 00:00:01"
            str_end = str(datetime.date.today()) + " 00:00:01"
        elif str_range == 'week':
            str_start = str(datetime.date.today() - datetime.timedelta(days=7)) + " 00:00:01"
            str_end = str(datetime.date.today()) + " 00:00:01"
        elif str_range == 'month':
            str_start = str(datetime.date.today() - datetime.timedelta(days=30)) + " 00:00:01"
            str_end = str(datetime.date.today()) + " 00:00:01"
        else:
            raise err

    except Exception, e:
        raise e
    print 'range is', str_start, str_end

    # 返回时间戳
    if style == 'ts':
        timestamp_start = change_datetime_to_timestamp(str_start)
        timestamp_end = change_datetime_to_timestamp(str_end)

        return timestamp_start, timestamp_end
    else:
        # 返回datetime
        return str_start, str_end


def get_datetime_now():
    '''获取datetime的当前时间
    :return:  2015-10-14 10:21:01
    '''
    return datetime.datetime.now()