# coding=utf8
'''
    GROUP服务
'''
# __author__ =  ""

import model.group as group_db


class GroupService:

    def __init__(self):
        self.group_db = group_db.Group(db_flag='kvm', table_name='tb_group')

    def query_data(self, **params):
        return self.group_db.simple_query(**params)

    def get_group_info(self, group_id):
        kwargs = {
            'WHERE_AND': {
                '=': {
                    'id': group_id,
                    'isdeleted': '0',
                }
            }
        }
        return self.group_db.simple_query(**kwargs)

    def add_group_info(self, insert_data):
        return self.group_db.insert(insert_data)

    def query_one(self, where_field, where_field_value):
        return self.group_db.get_one(where_field, where_field_value)


def update_group_info(update_data, where_data):
    return group_db.update_group(update_data, where_data)


def get_group_info_by_name(group_name):
    return group_db.query_group_info_by_group_name(group_name)


def get_group_info_by_name_and_env(group_name, env):
    return group_db.query_group_info_by_group_name_and_env(group_name, env)


def get_group_quota_used(group_id):
    '''
        获取指定组已用配额
    :param group_id:
    :return: {'SUM(m.vcpu)': Decimal('4'), 'SUM(m.root_disk_gb)': Decimal('160'), 'SUM(m.memory_mb)': Decimal('16384'), instance_num}
    '''
    group_flavor_quota = group_db.group_quota_flavor_used(group_id)
    # 如果返回的配额值为空，将它设置成0
    for x, y in group_flavor_quota[0].items():
        if not y:
            group_flavor_quota[0][x] = 0

    group_data_disk_used = group_db.group_quota_data_disk_used(group_id)
    if group_data_disk_used['all_data_disk_gb']:
        all_data_disk_gb = group_data_disk_used['all_data_disk_gb']
    else:
        all_data_disk_gb = 0

    return {
        'all_vcpu': group_flavor_quota[0]['all_vcpu'],
        'all_mem_mb': group_flavor_quota[0]['all_mem_mb'],
        'all_disk_gb': group_flavor_quota[0]['all_root_disk_gb'] + all_data_disk_gb,   # 磁盘使用=系统盘+数据盘
        'instance_num': group_flavor_quota[0]['instance_num']
    }
