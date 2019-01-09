#coding=utf8

import functools
import logging
import time

#重试
def retry(times=3, sleep_time=3):
    def wrap(f):
        @functools.wraps(f)
        def inner(*args, **kwargs):
            for i in range(0, times):
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    logging.error(e)
                    time.sleep(sleep_time)
        return inner
    return wrap