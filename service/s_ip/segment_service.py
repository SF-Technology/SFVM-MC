# coding=utf8
'''
    网段服务
'''
# __author__ =  ""

from model import network_segment, ip


class SegmentService:

    def __init__(self):
        self.segment_db = network_segment.NetworkSegment(db_flag='kvm', table_name='network_segment')

    def add_segment_info(self, insert_data):
        return self.segment_db.insert(insert_data)

    def query_data(self, **params):
        return self.segment_db.simple_query(**params)

    def get_segment_info(self, segment_id):
        return self.segment_db.get_one('id', segment_id)

    def get_segment_info_bysegment(self, segment):
        return self.segment_db.get_one('segment', segment)

    def get_segment_nums_in_net_area(self, net_area_id):
        '''
            获取指定网络区域下网段数量
        :param net_area_id:
        :return:
        '''
        params = {
            'WHERE_AND': {
                "=": {
                    'net_area_id': net_area_id
                }
            },
        }
        total_nums, data = self.segment_db.simple_query(**params)
        return total_nums

    def get_segment_datas_in_net_area(self, net_area_id):
        '''
            获取指定网络区域下网段信息
        :param net_area_id:
        :return:
        '''
        params = {
            'WHERE_AND': {
                "=": {
                    'net_area_id': net_area_id
                }
            },
        }
        return self.segment_db.simple_query(**params)

    def get_area_segment_list(self, net_area_id):
        '''
            获取物理机加入资源池新建网桥需要的网段信息
        :param net_area_id:
        :return:
        '''
        segment_data_list = self.get_segment_datas_in_net_area(net_area_id)
        if segment_data_list == {}:
            return False, '该网络区域下无可用IP网段'
        else:
            segment_list = []
            for segment_data in segment_data_list[1]:
                segment_data_params = {
                    'vlan': segment_data['vlan'],
                    'host_bridge_name': segment_data['host_bridge_name'],
                    'gateway': segment_data['gateway_ip']
                }
                segment_list.append(segment_data_params)
            return True, segment_list

    def get_segment_for_img_tmp(self):
        '''
                    获取虚拟机模板用网段
                :param :segment_type
                :return:
                '''
        params = {
            'WHERE_AND': {
                "=": {
                    'segment_type': '3'
                }
            },
        }
        num, total =  self.segment_db.simple_query(**params)
        return total[0]



def ip_info_in_segment(segment_id):
    return network_segment.ip_info_in_segment(segment_id)


def get_level_info(segment_type=False):
    return network_segment.get_level_info(segment_type)

def _get_level_info(segment_type=False):
    return network_segment._get_level_info(segment_type)

def get_ips_page(segment_id, page):
    segment_info = SegmentService().get_segment_info(segment_id)
    if not segment_info:
        return -1, -1

    ips_data = network_segment.get_ips_by_segment(segment_id, segment_info['segment'], page)
    if ips_data:
        return 1, ips_data
    else:
        # 如果该网段下暂无IP信息在db中，则直接返回网段信息
        return 2, segment_info


def get_segments_data(net_area_name, datacenter_name, env):
    '''
        通过网络区域名称、机房名称、环境查询网段信息
    :param net_area_name:
    :param datacenter_name:
    :param env:
    :return:
    '''
    return network_segment.get_segments_info_by_name(net_area_name, datacenter_name, env)


def get_segments_data_by_type(net_area_name, datacenter_name, env, segment_type):
    '''
        通过网络区域名称、机房名称、环境查询网段信息
    :param net_area_name:
    :param datacenter_name:
    :param env:
    :param segment_type:
    :return:
    '''
    return network_segment.get_segments_info_by_type(net_area_name, datacenter_name, env, segment_type)


def get_network_segments_data_paging(datacenter_name, env, net_area_name, page_num, page_size):
    return network_segment.get_network_segments_info_by_name_paging(datacenter_name, env, net_area_name, page_num,
                                                                    page_size)


def get_network_segments_data_in_dc_paging(datacenter_name, env, page_num, page_size):
    return network_segment.get_network_segments_info_in_dc_by_name_paging(datacenter_name, env, page_num, page_size)


def get_network_segments_data_by_segment_name(datacenter_name, env, net_area_name, net_segment):
    return network_segment.get_network_segments_info_by_segment_name(datacenter_name, env, net_area_name,
                                                                     net_segment)


def get_ip_datas_by_segmentid(segment_id):
    return ip.ip_all_in_segment(segment_id)



