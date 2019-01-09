# coding=utf8
'''
    增量生成器服务
'''


from model import increment
from config.default import ENV
from model.const_define import EnvType


class IncrementService:

    def __init__(self):
        self.increment_db = increment.Increment(db_flag='kvm', table_name='increment')

    def get_increment_by_prex(self, prex):
        return self.increment_db.get_one("prex_str", prex)

    def add_increment_of_prex(self, prex):
        insert_data = {
            "prex_str": prex,
            "increment_value": 1  # 主机名从1开始
        }
        return self.increment_db.insert(insert_data)


def get_increment_of_prex(prex):
    '''
        获取指定前缀的当前增量值
    :param prex:
    :return:
    '''
    service = IncrementService()
    increment_data = service.get_increment_by_prex(prex)
    # 没有该前缀的值则新增
    if not increment_data:
        ret_add = service.add_increment_of_prex(prex)
        increment_value = 1
    else:
        increment_value = increment_data['increment_value']

    return increment_value


def increase_increment_value(prex, num=1):
    '''
        增加指定前缀的增量值
    :param prex:
    :param num:
    :return:
    '''
    ret_increase = increment.increase_num_increment_value(prex, num)


def clean_dc_increment_value(dc_name):
    '''
        清空指定机房下的主机名增量值
    :param dc_name:
    :return:
    '''
    # sit环境的主机名区分一下
    if ENV == EnvType.SIT:
        prex_str_l = 'SIT' + dc_name + 'VLK'
        prex_str_w = 'SIT' + dc_name + 'VWK'
    else:
        prex_str_l = dc_name + 'VLK'
        prex_str_w = dc_name + 'VWK'

    increment.delete_increment_value_by_prex(prex_str_l)
    increment.delete_increment_value_by_prex(prex_str_w)