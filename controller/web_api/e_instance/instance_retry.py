# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
from flask import request
import json
import json_helper
from model.const_define import vmRetryActions,ErrorCode
from instance_retry_create import instance_retry_create
from instace_clone_create_retry import instance_clone_retry_create




@login_required
def instance_retry():
    instance_create_retry_info = request.values.get(vmRetryActions.INSTANCE_CREATE_RETRY)
    instance_clonecreate_retry_info = request.values.get(vmRetryActions.INSTANCE_CLONE_CREATE_RETRY)
    if instance_create_retry_info != '':
        instance_retry_create(instance_create_retry_info)
    if instance_clonecreate_retry_info != '':
        instance_clone_retry_create(instance_clonecreate_retry_info)

    return json_helper.format_api_resp(code=ErrorCode.SUCCESS)





