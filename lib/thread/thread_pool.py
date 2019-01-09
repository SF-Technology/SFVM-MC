# coding=utf8
# __author__ =  ""
'''
线程池的基础类

示例:
###############################################################
   #开启10个线程
   pools = ThreadPool(10)
   def say_hello(name):
       print 'hello!'
   #把任务放入线程池中，开始执行任务 addTask 
   #第一个参数是函数名
   #第二个参数是函数需要的参数
   pools.addTask( say_hello, [ 'wade' ] )
###############################################################

   该类库源代码主要来自于：https://github.com/tuxlinuxien/ThreadPool

   然后根据实际需要进行相应的修改
   原始类库不支持线程动态增减

'''
import threading
import Queue
import time
import logging
import traceback


class ThreadPoolTask(threading.Thread):

    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.kill = False
        self.queue = queue
        self._waitToKill = False
        self.last_active_time = time.time()
        self.isRunning = False

    def run(self):
        while not self.kill:
            self.isRunning = False
            try:
                callback, args = self.queue.get(timeout=1)
                self.isRunning = True
                try:
                    stime = time.time()
                    callback(args)
                    endtime = time.time()
                    logging.debug('func:[%s] cost:[%0.3fs]',callback.func_name,endtime-stime)
                    self.last_active_time = time.time()
                except:
                    logging.error( traceback.format_exc() )
            except Queue.Empty:
                pass
            except:
                logging.error(traceback.format_exc())
            if self._waitToKill and not self.isRunning:
                self.kill = True

    def stop(self):
        self.kill = True

    def waitAndStop(self):
        self._waitToKill = True

    def isKilled(self):
        return self.kill


class ThreadPool:

    def __init__(self, pool_size, max_pool_size,max_idle_time=300):
        self.pool_size = pool_size
        # 某个线程最多空闲多少秒 就会被结束掉
        self.thread_list = []
        if max_pool_size < pool_size:
            self.max_pool_size = pool_size 
        else:
            self.max_pool_size = max_pool_size
        if pool_size > 1000 or max_pool_size > 1000:
            self.pool_size = 100
            self.max_pool_size = 100
        if max_idle_time > 3600 or max_idle_time < 300:
            max_idle_time = 600
        self.max_idle_time = max_idle_time
        self.queue = Queue.Queue(max_pool_size)
        self.action_lock = threading.Lock()
        self._initThreads()

    def _initThreads(self):
        self.action_lock.acquire()
        for i in range(0, self.pool_size):
            thr = ThreadPoolTask(self.queue)
            thr.setDaemon(True)
            self.thread_list.append(thr)
        for thr in self.thread_list:
            thr.start()
        self.action_lock.release()

    def _removeDeadThreads(self):
        for thr in self.thread_list:
            if thr.isKilled():
                self.thread_list.remove(thr)
                del thr

    def hasFreeThread(self):
        free_flag = 0
        for i in self.thread_list:
            if not i.isRunning:
                free_flag = 1
        return free_flag

    def removeFreeThread(self):
        '''
           结束已经一段时间没有工作的工作线程
        '''
        try:
            self.action_lock.acquire()
            count_stop = 0
            for i in self.thread_list:
                if count_stop + self.pool_size >= self.max_pool_size:
                    break
                if (not i.isRunning) and time.time() - i.last_active_time > self.max_idle_time:
                    i.waitAndStop()
                    count_stop += 1
                    logging.info('已经结束1个空闲线程')
        except:
            logging.error( traceback.format_exc() )
        finally:
            self.action_lock.release()
        
    def delThreads(self, num):
        try:
            self.action_lock.acquire()
            if self.thread_list == []:
                return
            for thr in self.thread_list:
                if num > 0:
                    thr.stop()
                    num -= 1
            self._removeDeadThreads()
        finally:
            self.action_lock.release()

    def addThreads(self, num):
        try:
            self.action_lock.acquire()
            self._removeDeadThreads()
            thread_nums = len(self.thread_list)
            logging.info(' thread num %s max %s',thread_nums,self.max_pool_size)
            if thread_nums >= self.max_pool_size:
                return
            for cpt in range(num):
                thr = ThreadPoolTask(self.queue)
                thr.setDaemon(True)
                thr.start()
                self.thread_list.append(thr)
            logging.info('添加[%s]个工作线程成功',num)
        except:
            logging.error( traceback.format_exc() )
            pass
        finally:
            self.action_lock.release()

    def stopAll(self):
        for thr in self.thread_list:
            thr.stop()

    def waitAndStopAll(self):
        for thr in self.thread_list:
            thr.waitAndStop()

    def joinAll(self):
        for thr in self.thread_list:
            thr.join()

    def countThreads(self):
        try:
            self.action_lock.acquire()
            return len(self.thread_list)
        finally:
            self.action_lock.release()
 
    def addTask(self, callback, args):
        try:
            self.action_lock.acquire()
            self._removeDeadThreads()
            if self.thread_list == []:
                return
            self.queue.put((callback, args))
        finally:
            self.action_lock.release()
