# coding=utf8
'''
    镜像服务
'''
# __author__ =  ""

from model import image
from helper.time_helper import get_datetime_str



class ImageService:

    def __init__(self):
        self.image_db = image.Image(db_flag='kvm', table_name='image')

    def query_data(self, **params):
        return self.image_db.simple_query(**params)

    def add_image_info(self, insert_data):
        return self.image_db.insert(insert_data)

    def update_image_info(self, update_data, where_data):
        return self.image_db.update(update_data, where_data)

    def get_image_info_by_url(self, image_url):
        return self.image_db.get_one('url', image_url)

    def get_all_images(self, system=None):
        params = {
            'WHERE_AND': {
                "=": {
                    'isdeleted': '0',
                }
            },
        }
        if system:
            params['WHERE_AND']['=']['system'] = system
        return self.image_db.simple_query(**params)

    def get_images_by_name(self, image_name):
        params = {
            'WHERE_AND': {
                "=": {
                    'isdeleted': '0',
                    'name': image_name
                }
            },
        }
        return self.image_db.simple_query(**params)

    def get_image_by_url(self,url):
        params = {
            'WHERE_AND': {
                "=": {
                    'isdeleted': '0',
                    'url': url
                }
            },
        }
        return self.image_db.simple_query(**params)

    def image_sys_disk_confirm(self,image_name):
        params = {
            'WHERE_AND': {
                "=": {
                    'isdeleted': '0',
                    'name': image_name,
                    'type': '0'
                }
            },
        }
        return self.image_db.simple_query(**params)

    def get_images_by_name_t(self,image_name):
        #如果用于查找的为系统盘
        if '_disk' not in image_name:
            url = '/'+ image_name + '/' +image_name
            params = {
                'WHERE_AND': {
                    "=": {
                        'isdeleted': '0',
                        'url':url,
                        'type':'0'
                    }
                },
            }
            total_nums, data = ImageService().query_data(**params)
            if total_nums > 0:
                return True,data
            else:
                return False,None
        #如果用于查找的为数据盘
        else:
            url_var = '%'+ image_name
            params = {
                'WHERE_AND': {
                    "=": {
                        'isdeleted': '0',
                        'type':'1'
                    },
                    "like": {
                        'url':url_var
                    }
                },
            }
            total_nums, data = ImageService().query_data(**params)
            if total_nums > 0:
                return True, data
            else:
                return False,None


    def get_image_info(self, image_id):
        return self.image_db.get_one("id", image_id)



class ImageManageService:
    def __init__(self):
        self.image_manage_db = image.Image(db_flag='kvm', table_name='image_manage')

    def query_data(self, **params):
        return self.image_manage_db.simple_query(**params)

    def add_image_info(self, insert_data):
        return self.image_manage_db.insert(insert_data)

    def update_image_info(self, update_data, where_data):
        return self.image_manage_db.update(update_data, where_data)

    def get_image_manage_info_by_name(self, image_name):
        return self.image_manage_db.get_one('eimage_name', image_name)

    def get_img_manage_data_by_name(self, eimage_name):
        params = {
            'WHERE_AND': {
                "=": {
                    'eimage_name': eimage_name
                }
            },
        }
        total_nums, data = self.image_manage_db.simple_query(**params)
        if total_nums <= 0:
            return False, 'get image info error'
        return True, data[0]

    def update_image_manage_status(self, image_name, message, status):
        update_data = {
            'update_time':get_datetime_str(),
            'message':message,
            'status':status
        }
        where_data = {

            'eimage_name': image_name,
        }
        ret = self.update_image_info(update_data, where_data)

    def update_image_manage_msg(self, image_name, message):
        update_data = {
            'update_time':get_datetime_str(),
            'message':message,
        }
        where_data = {

            'eimage_name': image_name,
        }
        ret = self.update_image_info(update_data, where_data)


class ImageStatusService:
    def __init__(self):
        self.image_status_db = image.Image(db_flag='kvm', table_name='image_update_status')

    def query_data(self, **params):
        return self.image_status_db.simple_query(**params)

    def add_image_status_info(self, insert_data):
        return self.image_status_db.insert(insert_data)

    def update_image_info(self, update_data, where_data):
        return self.image_status_db.update(update_data, where_data)

    def add_image_status_action(self, image_name, update_action, state_tag, message):
        insert_data = {
            'status': state_tag,
            'update_action': update_action,
            'message': message,
            'update_time': get_datetime_str(),
            'eimage_name': image_name
        }
        ret = self.add_image_status_info(insert_data)
        if ret.get('row_num') <= 0:
            return False
        return True




