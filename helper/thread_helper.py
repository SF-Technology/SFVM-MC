#coding=utf8



def lockingCall(lock):
    '''用于添加锁保护的Decorator'''
    def decoFunc(f):
        def callFunc(*args, **kwargs):
            lock.acquire()
            try:
                return f(*args, **kwargs)
            finally:
                lock.release()
        return callFunc
    return decoFunc
