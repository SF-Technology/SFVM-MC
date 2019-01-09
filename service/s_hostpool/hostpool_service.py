# coding=utf8
'''
    HOSTPOOL服务
'''


from model import hostpool
from helper.time_helper import get_datetime_str


class HostPoolService:

    def __init__(self):
        self.hostpool_db = hostpool.HostPool(db_flag='kvm', table_name='hostpool')

    def get_hostpool_info(self, hostpool_id):
        return self.hostpool_db.get_one("id", hostpool_id)

    def query_data(self, **params):
        return self.hostpool_db.simple_query(**params)

    def add_hostpool(self, insert_data):
        return self.hostpool_db.insert(insert_data)

    def update_hostpool_info(self, update_data, where_data):
        return self.hostpool_db.update(update_data, where_data)

    def delete_hostpool(self, hostpool_id):
        update_data = {
            'isdeleted': '1',
            'deleted_at': get_datetime_str()
        }
        where_data = {
            'id': hostpool_id
        }
        return self.hostpool_db.update(update_data, where_data)

    def check_name_exist(self, net_area_id, name):
        params = {
            'WHERE_AND': {
                '=': {
                    'net_area_id': net_area_id,
                    'name': name,
                    'isdeleted': '0',
                },
            },
        }
        total_nums, data = self.hostpool_db.simple_query(**params)
        return total_nums

    def get_least_host_num(self, hostpool_id):
        _hostpool_info = self.hostpool_db.get_one('id', hostpool_id)
        if _hostpool_info:
            return _hostpool_info['least_host_num']
        else:
            return 0

    def get_hostpool_nums_in_net_area(self, net_area_id):
        '''
            获取指定网络区域下的集群数
        :param net_area_id:
        :return:
        '''
        params = {
            'WHERE_AND': {
                "=": {
                    'net_area_id': net_area_id,
                    'isdeleted': '0',
                }
            },
        }
        total_nums, data = self.hostpool_db.simple_query(**params)
        return total_nums

    def get_hostpool_datas_in_net_area(self, net_area_id):
        '''
            获取指定网络区域下的集群信息
        :param net_area_id:
        :return:
        '''
        params = {
            'WHERE_AND': {
                "=": {
                    'net_area_id': net_area_id,
                    'isdeleted': '0',
                }
            },
        }
        return self.hostpool_db.simple_query(**params)


def get_hostpool_nums_in_dc(datacenter_id):
    '''
        获取指定机房下的集群数
    :param datacenter_id:
    :return:
    '''
    hostpool_datas = hostpool.get_hostpools_by_dc_id(datacenter_id)
    return len(hostpool_datas)


def get_hostpool_datas_in_dc(datacenter_id):
    '''
        获取指定机房下的集群信息
    :param datacenter_id:
    :return:
    '''
    hostpool_datas = hostpool.get_hostpools_by_dc_id(datacenter_id)
    return hostpool_datas


def get_hostpool_nums_in_dcs(dc_datas):
    '''
        获取批量机房下的总集群数
    :param dc_datas:
    :return:
    '''
    all_hostpool_nums = 0
    for _dc in dc_datas:
        _hostpool_datas = hostpool.get_hostpools_by_dc_id(_dc['id'])
        _hostpool_nums = len(_hostpool_datas)
        if _hostpool_nums > 0:
            all_hostpool_nums += _hostpool_nums

    return all_hostpool_nums


def get_instances_nums(hostpool_id):
    return hostpool.get_instances_nums(hostpool_id)['nums']


def get_level_info_hostpool_zb():
    '''
    获取集群所有层级信息 - 总部
    :return:
    '''
    return hostpool.get_level_info_hostpool_zb()


def v2v_get_level_info_hostpool_zb():
    '''
        v2v_esx:获取集群所有层级信息 - 总部
        :return:
        '''
    return hostpool.v2v_get_level_info_hostpool_zb()


def get_hostpool_info_zb(env, net_area):
    '''
        获取总部制定网络区域、机房的物理集群id
    :return:
    '''
    try:
        zb_host_pool_ret = hostpool.get_hostpool_info_zb_for_vishnu(env, net_area)
        return zb_host_pool_ret
    except:
        return None


def get_level_info_hostpool_cs():
    '''
    获取集群所有层级信息 - 总部
    :return:
    '''
    return hostpool.get_level_info_hostpool_cs()


def get_level_info_hostpool_dq():
    '''
    获取集群所有层级信息 - 地区
    :return:
    '''
    return hostpool.get_level_info_hostpool_dq()


def get_env_of_hostpool(hostpool_id):
    '''
        获取集群所在的机房类型
    :param hostpool_id:
    :return:
    '''
    level_info = get_level_info_by_id(hostpool_id)
    if not level_info:
        return None

    return level_info['dc_type']


def get_level_info_by_id(hostpool_id):
    return hostpool.get_level_info_by_id(hostpool_id)


def get_dc_name_of_hostpool(hostpool_id):
    '''
        获取集群对应的机房名
    :param hostpool_id:
    :return:
    '''
    level_info = hostpool.get_level_info_by_id(hostpool_id)
    if level_info:
        return level_info['dc_name']
    else:
        return None


def get_level_info():
    return hostpool.get_level_info()


def get_hostpool_info_by_name(env, dc_name, net_area):
    return hostpool.get_hostpool_info_by_name(env, dc_name, net_area)


def get_segment_info(hostpool_id):
    return hostpool.get_segment_info(hostpool_id)


def get_hostpool_by_vmenv_netarea_hostpool(vm_env, netarea_name, hostpool_name):
    hostpool_list = hostpool.get_hostpool_by_vmenv_netarea_hostpool(vm_env, netarea_name, hostpool_name)
    if not hostpool_list:
        return None
    return hostpool_list[0]


def get_hostpool_by_area_dc_env_netarea_hostpool(area_name, dc_name, vm_env, netarea_name, hostpool_name):
    hostpool_list = hostpool.get_hostpool_by_area_dc_env_netarea_hostpool(area_name, dc_name, vm_env, netarea_name,
                                                                          hostpool_name)
    if not hostpool_list:
        return None
    return hostpool_list[0]


def get_hostpool_info():
    ''' 获取所有集群信息'''
    hostpool_info = hostpool.get_all_hostpool_info()
    return hostpool_info
