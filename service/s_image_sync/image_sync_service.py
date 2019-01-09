# coding=utf8
'''
    image_sync服务
'''


from model import image_sync
from helper.time_helper import get_datetime_str
from model import image_sync_schedule


class ImageSyncService():

    def __init__(self):
        self.imagesync_db = image_sync.Image_sync(db_flag='kvm', table_name='image_sync_task')

    def get_image_sync_info(self, imagesync_id):
        return self.imagesync_db.get_one("id", imagesync_id)

    def query_data(self, **params):
        return self.imagesync_db.simple_query(**params)

    def add_image_sync_task(self, insert_data):
        return self.imagesync_db.insert(insert_data)

    def update_image_sync_task(self, update_data, where_data):
        return self.imagesync_db.update(update_data, where_data)

def update_wget_message(task_id,message):
    where_data = {
        'id': task_id
    }
    update_data = {
        'message': message
    }
    ImageSyncService().update_image_sync_task(update_data, where_data)

def update_task_ondotag(task_id,ondotag):
    where_data = {
        'id': task_id
    }
    update_data = {
        'on_task': ondotag
    }
    ImageSyncService().update_image_sync_task(update_data, where_data)


def get_ondo_task(host_ip,image_id):
    return image_sync.get_ondo_task(host_ip,image_id)

def get_task_startttime(task_id):
    params = {
        'WHERE_AND': {
            '=': {
                'id': task_id
            },
        },
    }
    total_nums, data = ImageSyncService().query_data(**params)
    if total_nums > 0:
        starttime = data[0]['start_time']
        return starttime
    else:
        return False



def check_task_todo():
    params = {
        'WHERE_AND': {
            '=': {
                'isdeleted': '0',
                'on_task':'0'
            },
            'in': {
                'status': ['0','1']
            }
        },
    }
    task_num, task_data = ImageSyncService().query_data(**params)
    if task_num > 0:
        return task_data


def get_host_working_list(host_ip):
    return image_sync.get_host_working_list(host_ip)









