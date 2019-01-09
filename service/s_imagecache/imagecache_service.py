# coding=utf8
'''
    镜像缓存服务
'''


from model import imagecache


class ImageCacheService:

    def __init__(self):
        self.imagecache_db = imagecache.ImageCache(db_flag='kvm', table_name='imagecache')

    def query_data(self, **params):
        return self.imagecache_db.simple_query(**params)

    def add_imagecache_info(self, insert_data):
        return self.imagecache_db.insert(insert_data)

    def update_imagecache_info(self, update_data, where_data):
        return self.imagecache_db.update(update_data, where_data)

    def get_imagecache_info_by_net_area_id(self,net_area_id):
        params = {
            'WHERE_AND': {
                "=": {
                    'net_area_id': net_area_id
                }
            },
        }
        total_nums, data = self.imagecache_db.simple_query(**params)
        if total_nums <= 0:
            return None
        return data

    def get_all_imagecache_addr(self):
        params = {

        }
        total_nums, data = self.imagecache_db.simple_query(**params)
        if total_nums <= 0:
            return None
        return data

def get_imagecache_list_by_net_area_id(net_area_id):
    imagecache_data = ImageCacheService().get_imagecache_info_by_net_area_id(net_area_id)
    if not imagecache_data:
        return False,"获取镜像缓存服务器失败"
    else:
        imagecache_list = []
        imagecache01 = imagecache_data[0]['imagecache_ip']
        imagecache02 = imagecache_data[1]['imagecache_ip']
        imagecache_list = [imagecache01,imagecache02]
        return True,imagecache_list

