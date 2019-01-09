# coding=utf8
'''
    image_sync_schedule服务
'''


from model import image_sync_schedule
from helper.time_helper import get_datetime_str

class ImageSyncScheduleService():

    def __init__(self):
        self.imagesyncschedule_db = image_sync_schedule.Image_sync_schedule(db_flag='kvm', table_name='image_sync_schedule')

    def get_image_sync_info(self, imagesync_id):
        return self.imagesyncschedule_db.get_one("id", imagesync_id)

    def query_data(self, **params):
        return self.imagesyncschedule_db.simple_query(**params)

    def add_image_sync_sch(self, insert_data):
        return self.imagesyncschedule_db.insert(insert_data)

    def update_image_sync_sch(self, update_data, where_data):
        return self.imagesyncschedule_db.update(update_data, where_data)

def get_image_sync_sch_by_image_task_id(image_task_id):
    params = {
        'WHERE_AND': {
            '=': {
                'image_task_id': image_task_id
            },
        },
    }
    total_nums, data = ImageSyncScheduleService().query_data(**params)
    if total_nums > 0:
        sch_task_data = data[0]
        return sch_task_data
    else:
        return False

def get_ondo_task(image_task_id):
    return image_sync_schedule.get_ondo_list(image_task_id)


def get_singe_sch_info(sch_num,image_task_id):
    sch_state_name = 'sch' + str(sch_num) + '_state'
    sch_task_data = get_image_sync_sch_by_image_task_id(image_task_id)
    single_sch_state = sch_task_data[sch_state_name]
    if single_sch_state:
        sch_start_name = 'sch' + str(sch_num) +'_starttime'
        sch_end_name = 'sch' + str(sch_num) + '_endtime'
        sch_start_time = sch_task_data[sch_start_name]
        sch_end_time = sch_task_data[sch_end_name]
        return single_sch_state,sch_start_time,sch_end_time
    else:
        return False

def get_ondo_sch_list(image_task_id):
    params = {
        'WHERE_AND': {
            '=': {
                'image_task_id': image_task_id,
                'isdeleted':'0'
            },
            'in': {
                'sch_state':['0','1']
            }
        },
    }
    total_nums, data = ImageSyncScheduleService().query_data(**params)
    return total_nums,data


def get_todo_sch_list(image_task_id):
    params = {
        'WHERE_AND': {
            '=': {
                'image_task_id': image_task_id,
                'isdeleted': '0'
                ''
            },
            '!=': {
                'sch_state': '2'
            }
        },
    }
    total_nums, data = ImageSyncScheduleService().query_data(**params)
    return total_nums, data


