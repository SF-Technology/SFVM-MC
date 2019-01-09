
import traceback
import logging
import log_helper

def is_valid_app_uuid(app_uuid):
    try:
        if not app_uuid:
            return False
        tmp_list = app_uuid.split("-")
        if len(tmp_list) != 5:
            logging.error(" len [%s] %s",len(tmp_list),tmp_list)
            return False
        if len(tmp_list[0]) != 8 and len(tmp_list[1]) != 4 and len(tmp_list[2]) != 4 and len(tmp_list[3]) != 4 and len(tmp_list[4]) != 12:
            logging.error("len is error %s",tmp_list)
            return False
        return True
    except:
        log_helper.log_error(traceback.format_exc(), True)
        return False


