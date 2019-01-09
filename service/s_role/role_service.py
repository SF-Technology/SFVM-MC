# coding=utf8
'''
    ROLE, ROLE_PERMISSON, PERMISSION服务
'''
# __author__ =  ""

from model import role,role_permission,permission


class RoleService:

    def __init__(self):
        self.role_db = role.Role(db_flag='kvm', table_name='role')

    def query_role(self, where_field, where_field_value):
        return self.role_db.get_one(where_field, where_field_value)


class PermissionService:
    def __init__(self):
        self.permission_db = permission.Permission(db_flag='kvm', table_name='permission')

    def one_permission_info(self, permission_id):
        '''
        返回的dict是permission的name和module
        :return: {'name': 'create', 'module': 'instance}
        '''
        permission_info = self.permission_db.get_one('id', permission_id)
        new_dict = {permission_info.get('module'): permission_info.get('name')}
        return new_dict

    def query_permission(self):
        kwargs = {
            'WHERE_AND': {
                'id': 'asc'
            }
        }
        return self.permission_db.simple_query(**kwargs)


class RolePermissionService():

    def __init__(self):
        self.role_permission_db = role.Role(db_flag='kvm', table_name='role_permission')

    def role_permission_list(self, role_id):
        '''
        返回list，list的元素为多个dict，每个dict的元素为role_id对应的其中一个permission表中的permission的name和module信息
        :return [{u'instance': u'create'}, {u'instance': u'delete'},...]
        '''
        kwargs = {
            'WHERE_AND': {
                '=': {
                    'role_id': role_id
                }
            }
        }
        permission_list = []
        tuple_role = self.role_permission_db.simple_query(**kwargs)
        for i in tuple_role[1]:
            permission_id = i.get('permission_id')
            permission_info = PermissionService().one_permission_info(permission_id)
            permission_list.append(permission_info)
        return permission_list

