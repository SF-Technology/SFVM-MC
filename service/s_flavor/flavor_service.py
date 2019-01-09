# coding=utf8
'''
    flavor服务
'''
# __author__ =  ""

from model import flavor


class FlavorService:

    def __init__(self):
        self.flavor_db = flavor.Flavor(db_flag='kvm', table_name='flavor')

    def get_all_flavors(self):
        params = {
            'WHERE_AND': {
                "=": {
                    'isenable': '1',
                    'isdeleted': '0',
                }
            },
        }
        return self.flavor_db.simple_query(**params)

    def get_flavor_info(self, flavor_id):
        return self.flavor_db.get_one('id', flavor_id)


def get_flavor_by_vcpu_and_memory(vcpu, vmem):
    return flavor.get_flavor_by_vcpu_and_vmem(vcpu, vmem)
