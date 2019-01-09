# coding=utf8
'''
    虚拟机-迁移服务
'''
# __author__ =  ""

from model import instance_migrate
from model.const_define import MigrateStatus
from helper.time_helper import get_datetime_str


class InstanceMigrateService:

    def __init__(self):
        self.instance_migrate_db = instance_migrate.InstanceMigrate(db_flag='kvm', table_name='instance_migrate')

    def add_instance_migrate_info(self, insert_data):
        return self.instance_migrate_db.insert(insert_data)

    def query_data(self, **params):
        return self.instance_migrate_db.simple_query(**params)

    def update_instance_migrate_info(self, update_data, where_data):
        return self.instance_migrate_db.update(update_data, where_data)

    def get_host_on_task(self):
        '''
            获取任务在运行的host记录
        :param :
        :return:
        '''
        params = {
            'WHERE_AND': {
                "=": {
                    'migrate_status': MigrateStatus.DOING,
                }
            },
        }
        return self.instance_migrate_db.simple_query(**params)

    def get_host_using_nc_port(self, src_host_id):
        params = {
            'WHERE_AND': {
                "=": {
                    'src_host_id': src_host_id,
                    'migrate_status': MigrateStatus.DOING,
                }
            },
        }
        nums, datas = self.instance_migrate_db.simple_query(**params)
        if nums > 0:
            return [d['nc_port'] for d in datas]
        return None

    def change_migrate_status(self, migrate_tab_id, status):
        '''
            修改迁移任务状态
        :param migrate_tab_id:
        :param status:
        :return:
        '''
        update_data = {
            'migrate_status': status,
            'deleted_at': get_datetime_str()
        }
        where_data = {
            'id': migrate_tab_id
        }
        return self.instance_migrate_db.update(update_data, where_data)