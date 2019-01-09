# coding=utf8
'''
    物理机性能信息插入db服务
'''
# __author__ =  ""

import logging
from model import host_perform
from lib.dbs.mysql import Mysql
from common_data_struct import host_perform_info
import datetime
from config.default import HOST_PERFORMANCE_NUMS


class HostMetricService:

    def __init__(self):
        self.host_perform_db = host_perform.HostPerform(db_flag='kvm', table_name='tb_host_perform')

    # 根据传过来的列表，进行入库操作
    def push_data_to_db(self, metricinfo_list=None):

        hostmetrice = host_perform_info.HostPerformanceInfo()  # 初始化一条数据：也就是一个类实例
        insert_count = 0    #成功插入的数量
        message = []        #数据插入失败的提示
        ret_result = ()
        try:
            db_pool = Mysql.get_instance("kvm")
            db_connection = db_pool.get_connection()
            for metricinfo in metricinfo_list:
                hostmetrice.set_data(metricinfo)
                cdata = self.modify_data(hostmetrice)
                if cdata[1]:
                    sql = """
                        insert into tb_host_perform (ip, hostname, collect_time, metric_key, data_value) values (%s,%s,%s,%s,%s);
                    """
                    args = [hostmetrice.host_ip, hostmetrice.host_name, hostmetrice.collect_time,
                            hostmetrice.metric_key, hostmetrice.data_value]

                    # 请传入刚才获取的db连接db_connection变量
                    lastrowid = db_pool.insert(db_connection, sql, args)  # 插入成功则返回主键id
                    if type(lastrowid.get('last_id',None)) == long:
                        insert_count += 1
                else:   # 验证数据有效失败
                    print cdata[0]
                    logging.error(cdata[0])
                    message.append(cdata[0])

            # 请显式的提交事务  不要开启auto_commit
            db_pool.commit(db_connection)
        except Exception,e:
            logging.info("%s" % e.message)
            print(e)
            ret_result = ','.join(message), len(metricinfo_list), insert_count, False
        else:
            if len(message)==0:
                ret_result = 'success', len(metricinfo_list), insert_count, True
            else:
                ret_result = ','.join(message), len(metricinfo_list), insert_count, True
        finally:
            return ret_result

    def modify_data(self, metricinfo=None):
        message = 'success'
        try:
            metricinfo.collect_time = datetime.datetime.strptime(metricinfo.collect_time ,"%Y-%m-%d %H:%M:%S")
            if len(metricinfo.host_ip)>25:
                message = 'host_ip %s length is not accept, pleace check!' % metricinfo.host_ip
            if len(metricinfo.host_name)>30:
                message = 'host_name %s length > 30, pleace check!' % metricinfo.host_name
            if len(metricinfo.metric_key)>50:
                message = 'host metric_key %s length > 50 ,pleace check!' % metricinfo.metric_key
            # if type(float(metricinfo.data_value)) != float:
            #    message = ' %s data value type could not transfter to float, please check' % metricinfo.data_value
        except Exception,e:
            message = e.message
            print e
            logging.info("%s" % e.message)
            return message, False
        else:
            if message == 'success':
                return message, True
            else:
                return message, False

    def get_data_from_db(self):
        hostmetrice = host_perform_info.HostPerformanceInfo()  # 初始化一条数据：也就是一个类实例
        get_count = 0  # 成功获取的数据行
        message = []  # 数据插入失败的提示
        ret_result = ()
        try:
            db_pool = Mysql.get_instance("kvm")
            db_connection = db_pool.get_connection()
            # select语句
            sql = "select * from tb_host_perform order by collect_time desc limit " \
                  + str(HOST_PERFORMANCE_NUMS)
            # args = [222]
            # res = db_pool.query(db_connection, sql, args)  # 还有query_one方法
            res = db_pool.query(db_connection, sql)

            if _check_date(res):
                needdict = self.new_key_value(res)
                print needdict

                needinfo = tuple([':'.join([key, str(needdict[key])]) for key in needdict])
                print needinfo
                return needinfo
        except Exception, e:
            logging.error(e.message)
            return tuple('error:', e.message,)

    def get_data_from_db_with_post(self, host_ip):
        try:
            db_pool = Mysql.get_instance("kvm")
            db_connection = db_pool.get_connection()
            # select语句
            sql = "select * from tb_host_perform where host_ip='%s' order by collect_time desc limit " % \
                  host_ip + str(HOST_PERFORMANCE_NUMS)
            res = db_pool.query(db_connection, sql)

            if _check_date(res):
                needdict = self.new_key_value(res)
                print needdict

                needinfo = tuple([':'.join([key, str(needdict[key])]) for key in needdict])
                print needinfo
                return needinfo
        except Exception, e:
            logging.error(e.message)
            print e

    def new_key_value(self, res):
        newdict = {}
        for data in res:
             for sdata in data:
                if sdata == 'metric_key':
                    self.set_v(akey=data[sdata], avalue=data['data_value'], dd=newdict)
        b = [self.set_v(akey=sdata, avalue=data[sdata], dd=newdict)
             for sdata in data for data in res if sdata != 'metric_key' and sdata != 'data_value']
        return newdict

    @staticmethod
    def set_v(akey=None, avalue=None, dd=None):
        dd[akey] = avalue

    def get_host_performance_data_by_hostip(self, host_ip=None):
        '''
            获取host性能数据
        :param host_ip:
        :return:
        '''
        try:
            db_pool = Mysql.get_instance("kvm")
            db_connection = db_pool.get_connection()
            # select语句
            # sql = "select * from tb_host_perform where ip='%s' order by collect_time desc limit " % \
            #       host_ip + str(HOST_PERFORMANCE_NUMS)

            sql = '''select * from tb_host_perform where ip = '%s' and collect_time = (
                        select collect_time from tb_host_perform where ip = '%s' ORDER BY collect_time desc limit 1
                        )''' % (host_ip, host_ip)

            res = db_pool.query(db_connection, sql)

            logging.info('host_perform_data_from_db')
            logging.info(res)

            if _check_date(res):
                needdict = self.new_key_value(res)
                logging.info('host_perform_data_after_nulldata')
                logging.info(needdict)
                return needdict

        except Exception, e:
            logging.error(e.message)
            return {'error': e.message}


def _check_date(res):
    times = [data['collect_time'] for data in res if data['collect_time']]
    if len(set(times)) != 1:
        return False
    return True