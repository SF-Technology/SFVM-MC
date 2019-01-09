# coding=utf8
'''
    IP服务
'''
# __author__ =  ""

from model import ip
import model.instance_ip as instance_ip_db
from lib.dbs.mysql import Mysql
import logging
import traceback
from service.s_ip import segment_match as segment_m
from service.s_ip import segment_service as segment_s
from model.const_define import IPStatus, DataCenterType, PingStatus
import threading
import pyping
from config.default import PING_TIMEOUT


class IPService:

    def __init__(self):
        self.ip_db = ip.IP(db_flag='kvm', table_name='ip')

    def add_ip_info(self, insert_data):
        return self.ip_db.insert(insert_data)

    def update_ip_info(self, update_data, where_data):
        return self.ip_db.update(update_data, where_data)

    def get_ip_by_ip_address(self, ip_address):
        return self.ip_db.get_one('ip_address', ip_address)

    def get_ip_info(self, ip_id):
        return self.ip_db.get_one("id", ip_id)

    def get_ip_info_by_ipaddress(self, ip_address):
        return self.ip_db.get_one("ip_address", ip_address)


def del_ip_info(ip_id):
    return ip.delete_ip(ip_id)


def get_available_ips(segments_list, count, env):
    '''
        从网段list中循环获取可使用的多个IP
    :param segments_list:
    :param count:
    :param env:
    :return:
    '''
    for _segment in segments_list:
        ips_list = []
        ips_info = ip.get_available_ip(_segment['id'])
        if ips_info:
            # 多线程ping去掉通的ip
            global IP_AVAILABLE_LIST
            IP_AVAILABLE_LIST = []
            threads = []
            for _per_unused_ip in ips_info:
                ip_check_thread = threading.Thread(target=__ping_ip_available, args=(_per_unused_ip, ))
                threads.append(ip_check_thread)
                ip_check_thread.start()
            logging.info("ip available list: {}".format(IP_AVAILABLE_LIST))
            # 判断多线程是否结束
            for t in threads:
                t.join()

            if len(IP_AVAILABLE_LIST) < count:
                continue

            for _ip in IP_AVAILABLE_LIST:
                if int(env) == DataCenterType.PRD:
                    segment_dr = segment_m.SegmentMatchService().get_segment_match_info_by_prd_segment_id(_segment['id'])
                    if not segment_dr:
                        continue
                    segment_dr_data = segment_s.SegmentService().get_segment_info(segment_dr['dr_segment_id'])
                    if not segment_dr_data:
                        continue
                    # 拼凑虚拟机容灾IP
                    dr_ip = segment_dr_data['segment'].split('.')[0] + '.' + segment_dr_data['segment'].split('.')[1] + \
                            '.' + _ip['ip_address'].split('.')[2] + '.' + _ip['ip_address'].split('.')[3]
                    # ping ip，通的话不允许分配
                    ret_ping = __ping_ip_available_simple(dr_ip)
                    if not ret_ping:
                        continue
                    dr_ip_info = IPService().get_ip_by_ip_address(dr_ip)
                    # 如果容灾IP是未使用中状态，可以使用
                    if dr_ip_info:
                        if dr_ip_info['status'] == IPStatus.UNUSED:
                            ips_list.append(_ip)
                            if len(ips_list) == int(count):
                                return ips_list, _segment
                elif int(env) == DataCenterType.DR:
                    segment_prd = segment_m.SegmentMatchService().get_segment_match_info_by_dr_segment_id(_segment['id'])
                    if not segment_prd:
                        continue
                    segment_prd_data = segment_s.SegmentService().get_segment_info(segment_prd['prd_segment_id'])
                    if not segment_prd_data:
                        continue
                    # 拼凑虚拟机生产IP
                    prd_ip = segment_prd_data['segment'].split('.')[0] + '.' + segment_prd_data['segment'].split('.')[1] + '.' + _ip['ip_address'].split('.')[2] + '.' + _ip['ip_address'].split('.')[3]
                    ret_ping = __ping_ip_available_simple(prd_ip)
                    if not ret_ping:
                        continue
                    prd_ip_info = IPService().get_ip_by_ip_address(prd_ip)
                    # 如果生产环境ip是未使用中状态，可以使用
                    if prd_ip_info:
                        if prd_ip_info['status'] == IPStatus.UNUSED:
                            ips_list.append(_ip)
                            if len(ips_list) == int(count):
                                return ips_list, _segment
                else:
                    ips_list.append(_ip)
                    if len(ips_list) == int(count):
                        return ips_list, _segment

    # 如果没有获取到合适的IP，返回失败
    return False, ''


def __ping_ip_available(per_ip):
    '''
        将ping不通（未使用）ip加入全局ip列表IP_AVAILABLE_LIST中
    :param per_ip:
    :return:
    '''
    global IP_AVAILABLE_LIST
    try:
        ret_ping = pyping.ping(per_ip['ip_address'], timeout=PING_TIMEOUT)
        if ret_ping.ret_code == PingStatus.FAILED:
            IP_AVAILABLE_LIST.append(per_ip)
    except:
        pass


def __ping_ip_available_simple(ip_addresss):
    '''
        ping不通（未使用）ip返回True，ping的通返回False
    :param ip_addresss:
    :return:
    '''
    try:
        ret_ping = pyping.ping(ip_addresss, timeout=PING_TIMEOUT)
        if ret_ping.ret_code == PingStatus.FAILED:
            return True
        return False
    except:
        return False


def get_avail_tmp_ip():
    '''
        从专用网段中获取一个ip分配给模板机
    :param segments_list:
    :param count:
    :param env:
    :return:
    '''
    segment_data = segment_s.SegmentService().get_segment_for_img_tmp()
    ips_info = ip.get_available_ip(segment_data['id'])
    if not ips_info:
        return False, '该网段id：%s没有可用ip' % str(segment_data['id'])
    ip_data = ips_info[0]
    return ip_data, segment_data


def get_available_ips_in_group(segments_list, group_id, count):
    '''
        从网段list中循环获取可使用的多个IP
    :param segments_list:
    :param group_id:
    :param count:
    :return:
    '''
    for _segment in segments_list:
        ips_list = []
        ips_info = ip.get_available_dr_ip(_segment['id'], group_id)
        if ips_info:
            for _ip in ips_info:
                ips_list.append(_ip)
                if len(ips_list) == int(count):
                    return ips_list, _segment

    # 如果没有获取到合适的IP，返回失败
    return False, ''


def get_available_vips(segments_list, count):
    '''
        从网段list找出一个拥有3个可用ip的网段并返回
    :param segments_list:
    :param count:
    :return:
    '''
    for _segment in segments_list:
        ips_list = []
        ips_info = ip.get_available_ip(_segment['id'])
        if ips_info:
            for _ip in ips_info:
                ips_list.append(_ip)
                if len(ips_list) == int(count):
                    return ips_list, _segment

    # 如果没有获取到合适的IP，返回失败
    return False, ''


def get_available_ip_by_segment_id(segment_id):
    '''
        从指定网段中找出可用ip数量
    :param segment_id:
    :return:
    '''
    ip_list = []
    ip_info = ip.get_available_ip(segment_id)
    if ip_info:
        for _ip in ip_info:
            ip_list.append(_ip)
        if len(ip_list) > 0:
            return True, len(ip_list)

    # 如果没有获取到合适的IP，返回失败
    return False, 0


def get_available_segment_ip(segment_id, env, count=1):
    '''
        返回指定网段可用ip
    :param segment_id:
    :param env:
    :param count:
    :return:
    '''
    ips_info = ip.get_available_ip(segment_id)
    if ips_info:
        # 多线程ping去掉通的ip
        global IP_AVAILABLE_LIST
        IP_AVAILABLE_LIST = []
        threads = []
        for _per_unused_ip in ips_info:
            ip_check_thread = threading.Thread(target=__ping_ip_available, args=(_per_unused_ip,))
            threads.append(ip_check_thread)
            ip_check_thread.start()
        # 判断多线程是否结束
        for t in threads:
            t.join()

        if len(IP_AVAILABLE_LIST) > 0:
            for _ip in IP_AVAILABLE_LIST:
                if int(env) == DataCenterType.PRD:
                    segment_dr = segment_m.SegmentMatchService().get_segment_match_info_by_prd_segment_id(segment_id)
                    if not segment_dr:
                        continue
                    segment_dr_data = segment_s.SegmentService().get_segment_info(segment_dr['dr_segment_id'])
                    if not segment_dr_data:
                        continue
                    # 拼凑虚拟机容灾IP
                    dr_ip = segment_dr_data['segment'].split('.')[0] + '.' + segment_dr_data['segment'].split('.')[1] + \
                            '.' + _ip['ip_address'].split('.')[2] + '.' + _ip['ip_address'].split('.')[3]
                    # ping ip，通的话不允许分配
                    ret_ping = __ping_ip_available_simple(dr_ip)
                    if not ret_ping:
                        continue
                    dr_ip_info = IPService().get_ip_by_ip_address(dr_ip)
                    # 如果容灾IP是未使用中状态，可以使用
                    if dr_ip_info:
                        if dr_ip_info['status'] == IPStatus.UNUSED:
                            # 保留对应ip
                            update_dr_ip_data = {
                                'status': IPStatus.PRE_ALLOCATION
                            }
                            where_dr_ip_data = {
                                'id': dr_ip_info['id']
                            }
                            ret_mark_ip = IPService().update_ip_info(update_dr_ip_data, where_dr_ip_data)
                            if ret_mark_ip <= 0:
                                continue
                            return True, _ip
                elif int(env) == DataCenterType.DR:
                    segment_prd = segment_m.SegmentMatchService().get_segment_match_info_by_dr_segment_id(segment_id)
                    if not segment_prd:
                        continue
                    segment_prd_data = segment_s.SegmentService().get_segment_info(segment_prd['prd_segment_id'])
                    if not segment_prd_data:
                        continue
                    # 拼凑虚拟机生产IP
                    prd_ip = segment_prd_data['segment'].split('.')[0] + '.' + segment_prd_data['segment'].split('.')[1] + '.' + _ip['ip_address'].split('.')[2] + '.' + _ip['ip_address'].split('.')[3]
                    # ping ip，通的话不允许分配
                    ret_ping = __ping_ip_available_simple(prd_ip)
                    if not ret_ping:
                        continue
                    prd_ip_info = IPService().get_ip_by_ip_address(prd_ip)
                    # 如果生产环境ip是未使用中状态，可以使用
                    if prd_ip_info:
                        if prd_ip_info['status'] == IPStatus.UNUSED:
                            # 保留对应ip
                            update_prd_ip_data = {
                                'status': IPStatus.PRE_ALLOCATION
                            }
                            where_prd_ip_data = {
                                'id': prd_ip_info['id']
                            }
                            ret_mark_ip = IPService().update_ip_info(update_prd_ip_data, where_prd_ip_data)
                            if ret_mark_ip <= 0:
                                continue
                            return True, _ip
                else:
                    return True, _ip

    # 如果没有获取到合适的IP，返回失败
    return False, ''


def get_all_available_segment_ip(segment_id, env):
    '''
        返回指定网段所有可用ip
    :param segment_id:
    :param env:
    :return:
    '''
    ips_list = []
    ips_info = ip.get_available_ip(segment_id)
    if ips_info:
        # 多线程ping去掉通的ip
        global IP_AVAILABLE_LIST
        IP_AVAILABLE_LIST = []
        threads = []
        for _per_unused_ip in ips_info:
            ip_check_thread = threading.Thread(target=__ping_ip_available, args=(_per_unused_ip,))
            threads.append(ip_check_thread)
            ip_check_thread.start()
        # 判断多线程是否结束
        for t in threads:
            t.join()

        if len(IP_AVAILABLE_LIST) > 0:
            for _ip in IP_AVAILABLE_LIST:
                if int(env) == DataCenterType.PRD:
                    segment_dr = segment_m.SegmentMatchService().get_segment_match_info_by_prd_segment_id(segment_id)
                    if not segment_dr:
                        continue
                    segment_dr_data = segment_s.SegmentService().get_segment_info(segment_dr['dr_segment_id'])
                    if not segment_dr_data:
                        continue
                    # 拼凑虚拟机容灾IP
                    dr_ip = segment_dr_data['segment'].split('.')[0] + '.' + segment_dr_data['segment'].split('.')[1] + \
                            '.' + _ip['ip_address'].split('.')[2] + '.' + _ip['ip_address'].split('.')[3]
                    # ping ip，通的话不允许分配
                    # ret_ping = __ping_ip_available_simple(dr_ip)
                    # if not ret_ping:
                    #     continue
                    dr_ip_info = IPService().get_ip_by_ip_address(dr_ip)
                    # 如果容灾IP是未使用中状态，可以使用
                    if dr_ip_info:
                        if dr_ip_info['status'] == IPStatus.UNUSED:
                            ips_list.append(_ip)
                elif int(env) == DataCenterType.DR:
                    segment_prd = segment_m.SegmentMatchService().get_segment_match_info_by_dr_segment_id(segment_id)
                    if not segment_prd:
                        continue
                    segment_prd_data = segment_s.SegmentService().get_segment_info(segment_prd['prd_segment_id'])
                    if not segment_prd_data:
                        continue
                    # 拼凑虚拟机生产IP
                    prd_ip = segment_prd_data['segment'].split('.')[0] + '.' + segment_prd_data['segment'].split('.')[1] + '.' + _ip['ip_address'].split('.')[2] + '.' + _ip['ip_address'].split('.')[3]
                    # ping ip，通的话不允许分配
                    # ret_ping = __ping_ip_available_simple(prd_ip)
                    # if not ret_ping:
                    #     continue
                    prd_ip_info = IPService().get_ip_by_ip_address(prd_ip)
                    # 如果生产环境ip是未使用中状态，可以使用
                    if prd_ip_info:
                        if prd_ip_info['status'] == IPStatus.UNUSED:
                            ips_list.append(_ip)
                else:
                    ips_list.append(_ip)

    # 如果没有获取到合适的IP，返回失败
    return True, ips_list


def get_available_segment_dr_ip(segment_id, group_id):
    '''
        返回指定网段可用容灾ip
    :param segment_id:
    :return:
    '''
    return ip.get_one_available_dr_ip(segment_id, group_id)


def get_all_available_ips(segments_list, env):
    '''
        从网段list中循环获取可使用的多个IP
    :param segments_list:
    :param env:
    :return:
    '''
    ips_list = []
    for _segment in segments_list:
        ips_info = ip.get_available_ip(_segment['id'])
        if ips_info:
            # 多线程ping去掉通的ip
            global IP_AVAILABLE_LIST
            IP_AVAILABLE_LIST = []
            threads = []
            for _per_unused_ip in ips_info:
                ip_check_thread = threading.Thread(target=__ping_ip_available, args=(_per_unused_ip,))
                threads.append(ip_check_thread)
                ip_check_thread.start()
            # 判断多线程是否结束
            for t in threads:
                t.join()

            if len(IP_AVAILABLE_LIST) <= 0:
                continue

            for _ip in IP_AVAILABLE_LIST:
                if int(env) == DataCenterType.PRD:
                    segment_dr = segment_m.SegmentMatchService().get_segment_match_info_by_prd_segment_id(
                        _segment['id'])
                    if not segment_dr:
                        continue
                    segment_dr_data = segment_s.SegmentService().get_segment_info(segment_dr['dr_segment_id'])
                    if not segment_dr_data:
                        continue
                    # 拼凑虚拟机容灾IP
                    dr_ip = segment_dr_data['segment'].split('.')[0] + '.' + segment_dr_data['segment'].split('.')[1] + \
                            '.' + _ip['ip_address'].split('.')[2] + '.' + _ip['ip_address'].split('.')[3]
                    # ping ip，通的话不允许分配
                    # ret_ping = __ping_ip_available_simple(dr_ip)
                    # if not ret_ping:
                    #     continue
                    dr_ip_info = IPService().get_ip_by_ip_address(dr_ip)
                    # 如果容灾IP是未使用中状态，可以使用
                    if dr_ip_info:
                        if dr_ip_info['status'] == IPStatus.UNUSED:
                            _ip['ip_type'] = _segment['segment_type']
                            ips_list.append(_ip)
                elif int(env) == DataCenterType.DR:
                    segment_prd = segment_m.SegmentMatchService().get_segment_match_info_by_dr_segment_id(
                        _segment['id'])
                    if not segment_prd:
                        continue
                    segment_prd_data = segment_s.SegmentService().get_segment_info(segment_prd['prd_segment_id'])
                    if not segment_prd_data:
                        continue
                    # 拼凑虚拟机生产IP
                    prd_ip = segment_prd_data['segment'].split('.')[0] + '.' + segment_prd_data['segment'].split('.')[
                        1] + '.' + _ip['ip_address'].split('.')[2] + '.' + _ip['ip_address'].split('.')[3]
                    # ping ip，通的话不允许分配
                    # ret_ping = __ping_ip_available_simple(prd_ip)
                    # if not ret_ping:
                    #     continue
                    prd_ip_info = IPService().get_ip_by_ip_address(prd_ip)
                    # 如果生产环境ip是未使用中状态，可以使用
                    if prd_ip_info:
                        if prd_ip_info['status'] == IPStatus.UNUSED:
                            _ip['ip_type'] = _segment['segment_type']
                            ips_list.append(_ip)
                else:
                    _ip['ip_type'] = _segment['segment_type']
                    ips_list.append(_ip)

    return ips_list


def get_all_available_dr_ips(segments_list, group_id):
    '''
        从网段list中循环获取可使用的多个IP
    :param segments_list:
    :param group_id:
    :return:
    '''
    ips_list = []
    for _segment in segments_list:
        ips_info = ip.get_available_dr_ip(_segment['id'], group_id)
        if ips_info:
            for _ip in ips_info:
                ips_list.append(_ip)

    return ips_list


def ip_inited_in_segment(segment_id):
    '''
        获取指定网段ID下已经初始化的IP
    :param segment_id:
    :return:
    '''
    return ip.ip_inited_in_segment(segment_id)


def get_ipaddress_of_instance(instance_id):
    '''
        返回指定instance_id的ip地址
    :param instance_id:
    :return:
    '''
    ip_info = ip.get_ip_instance_info(instance_id)
    if ip_info:
        return ip_info['ip_address']
    else:
        return None


def get_instance_info_by_ip(ip_address):
    '''
        获取指定IP所分配的VM
    :param ip_address:
    :return:
    '''
    return ip.get_instance_info_by_ip(ip_address)
