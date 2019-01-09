# coding=utf8
'''
    注册url路由
'''


import controller.web_api.e_user.user_init as user_init
from controller.web_api.e_area.area_list import area_list
from controller.web_api.e_area.area_manager import area_add, area_update, area_delete, get_parent_areas, get_child_areas, \
    add_child_area
from controller.web_api.e_area.area_level_info import get_area_level_info
from controller.web_api.e_datacenter import datacenter_list as e_datacenter_list
from controller.web_api.e_datacenter.datacenter_manager import datacenter_add, allocate_dc_2_area, datacenter_delete, \
    datacenter_update
from controller.web_api.e_datacenter.datacenter_monitor import datacenter_monitor
from controller.web_api.e_feedback import feedback_list as e_feedback_list
from controller.web_api.e_feedback import feedback_manager as e_feedback
from controller.web_api.e_group import group_list as e_group_list
from controller.web_api.e_group import group_manager as e_group
from controller.web_api.e_instance.instance_performance_data import instance_performance_data_to_other_platform
from controller.web_api.e_user_group.user_group_add_from_other_platform import group_create_from_other_platform
from controller.web_api.e_host import host_action as e_host_action
from controller.web_api.e_host import host_list as e_host_list
from controller.web_api.e_host import host_manager as e_host
from controller.web_api.e_host.host_export import export_host_excel
from controller.web_api.e_hostpool import hostpool_list as e_hostpool_list
from controller.web_api.e_hostpool.hostpool_manager import hostpool_add, hostpool_delete, hostpool_update
from controller.web_api.e_hostpool import hostpool_other as e_hostpool_other
from controller.web_api.e_hostpool.hostpool_monitor import hostpool_monitor
from controller.web_api.e_hostpool.hostpool_export import export_hostpool_excel
from controller.web_api.e_image import image_list as e_image_list
from controller.web_api.e_image import image_manage as e_image
from controller.web_api.e_instance.instance_action import instance_shutdown, instance_startup, instance_reboot
from controller.web_api.e_instance.instance_configure import instance_configure, configure_init,extend_disk, instance_add_netcard
from controller.web_api.e_instance.instance_create import instance_create
from controller.web_api.e_instance.instance_create_from_other_platform import instance_create_from_other_platform
from controller.web_api.e_instance.instance_init_info import instance_init_info
from controller.web_api.e_instance.instance_list import instance_list
from controller.web_api.e_instance.instance_manager import instance_flavor, instance_delete, instance_detail, \
    instance_os_version_modify,instance_excel_del_template,upload_del_instance_excel
from controller.web_api.e_instance.instance_migrate import migrate_init, instance_migrate
from controller.web_api.e_instance.instance_hot_migrate import hot_migrate_init, instance_hot_migrate
from controller.web_api.e_instance.instance_console import console
from controller.web_api.e_instance.instance_retry_create import instance_retry_create
from controller.web_api.e_instance.instance_export import export_instance_excel
from controller.web_api.e_instance.instance_retry import instance_retry
from controller.web_api.e_instance.instance_netcard_configure_from_other_platform import instance_add_netcard_from_other_platform
from controller.web_api.e_ip import ip_hold as e_ip_hold
from controller.web_api.e_ip import ip_init as e_ip_init
from controller.web_api.e_ip.ip_manager import ip_instance_info
from controller.web_api.e_ip import segment_manager as e_segment
from controller.web_api.e_ip.ip_apply_from_other_platform import ip_apply_from_other_platform, \
    ip_resource_display_to_other_platform, ip_resource_display_to_other_platform_new
from controller.web_api.e_ip.ip_apply import ip_apply
from controller.web_api.e_ip.segment_capacity_to_other_platform import segment_capacity_to_other_platform
from controller.web_api.e_monitor import balent_monitor
from controller.web_api.e_monitor.health_monitor import health_monitor
from controller.web_api.e_net_area.net_area_level_info import net_area_level_info_get
from controller.web_api.e_net_area.net_area_list import net_area_list
from controller.web_api.e_net_area.net_area_manager import net_area_add, net_area_delete, net_area_update, net_area_info_init
from controller.web_api.e_net_area.net_area_monitor import net_area_monitor
from controller.web_api.e_user import user_list as e_user_list
from controller.web_api.e_user import user_manager as e_user_manager
from controller.web_api.e_user_group import user_group_list as e_user_group_list
from controller.web_api.e_user_group import user_group_manager as e_user_group
from controller.web_api.v2v.v2v_openstack_del import v2v_openstack_del
from controller.web_api.v2v.v2v_openstack_init import v2v_op_init_info
from controller.web_api.v2v.v2v_openstack_list import V2v_Op_Info
from controller.web_api.v2v.v2v_openstack_cancel import v2v_openstack_cancel
from controller.web_api.v2v.v2v_openstack_intodb import v2v_openstack_intodb
from controller.web_api.v2v.v2v_openstack_retry import v2v_openstack_retry
from controller.web_api.v2v.v2v_esx_init import v2v_esx_init_info
from controller.web_api.v2v.v2v_esx_define import  esx_vm_define
from controller.web_api.v2v.v2v_esx_intodb import v2v_esx_intodb
from controller.web_api.v2v.v2v_esx_batch import esx_intodb_batch
from controller.web_api.v2v.v2v_esx_batch_import import import_excel_esx, download_excel_esx
from controller.web_api.v2v.v2v_openstack_batch_t1 import task_check
from controller.web_api.v2v.v2v_openstack_batch_t2 import intodb_batch
from controller.web_api.v2v.v2v_openstack_batch_import import import_excel_openstack, download_excel_openstack
from controller.web_api.v2v.v2v_task_export import export_v2v_task_excel
from controller.web_api.e_dashboard.dashboard_info_v1 import dashboard_v1, dashboard_v1_map
from controller.web_api.e_dashboard.dashboard_info_v2 import dashboard_v2
from controller.web_api.e_instance.instance_clone import instance_clone
from controller.web_api.e_other.verify_code import verify_code_create
from controller.web_api.image_sync.host_list_info import get_host_image_batch as get_image_host
from controller.web_api.image_sync.host_list_info2 import single_host_image_return as single_host_image_return
from controller.web_api.image_sync.host_image_task import host_image_task_intodb as host_task_intodb
from controller.web_api.image_sync.host_list import image_sync_host as image_sy_host
from controller.web_api.e_hostpool.hostpool_capacity_to_other_platform import hostpool_capacity_to_other_platform
# from web_api.clone_create.intodb import clone_create_intodb
from controller.web_api.e_instance.instance_clone_create import clone_create_intodb
from controller.web_api.e_operation import operation_list as e_operation_list
from controller.web_api.e_instance.instance_create_from_other_platform_prd_dr import instance_create_from_other_platform_prd_dr
from controller.web_api.e_instance.instance_create_from_other_platform_with_ip import instance_create_from_other_platform_with_ip, \
    hostpool_info_init
from controller.web_api.e_host.host_perform_data_to_db import host_perform_data_to_db
from controller.web_api.e_kvm_platform_common_info import kvm_common_information_for_api
from controller.web_api.e_ip.ip_apply_from_other_platform import ips_apply_from_other_platform
from controller.web_api.e_image_manage import image_manage_list
from controller.web_api.e_image_manage import image_create
from controller.web_api.e_image_manage import image_release_by_exist, image_release_by_new
from controller.web_api.e_image_manage import image_edit
from controller.web_api.e_image_manage import image_checkout
from controller.web_api.e_image_manage import image_tmp_console
from controller.web_api.e_ip.segment_manager import add_segment
from controller.web_api.e_instance.instance_detail_for_miniarch import instance_detail_for_miniarch
from controller.web_api.e_instance.instance_status_change_for_miniarch import instance_status_change_for_miniarch


def reg(app):
    '''
        这里放外部访问的api接口
    :return:
    '''

    # 首页模块
    app.add_url_rule(rule='/dashboard/v1', view_func=dashboard_v1, methods=['GET'])
    app.add_url_rule(rule='/dashboard/v1/map', view_func=dashboard_v1_map, methods=['GET'])
    app.add_url_rule(rule='/dashboard/v2', view_func=dashboard_v2, methods=['GET'])

    # 虚拟机管理模块
    app.add_url_rule(rule='/instance/init', view_func=instance_init_info, methods=['GET'])
    app.add_url_rule(rule='/instance/hostpool/<int:hostpool_id>', view_func=instance_create, methods=['POST'])
    app.add_url_rule(rule='/instance/list', view_func=instance_list, methods=['GET'])
    app.add_url_rule(rule='/instance/<int:instance_id>/flavor', view_func=instance_flavor, methods=['GET'])
    app.add_url_rule(rule='/instance/startup', view_func=instance_startup, methods=['PUT'])
    app.add_url_rule(rule='/instance/shutdown', view_func=instance_shutdown, methods=['PUT'])
    app.add_url_rule(rule='/instance/reboot', view_func=instance_reboot, methods=['PUT'])
    app.add_url_rule(rule='/instance/configure/init/<int:instance_id>', view_func=configure_init, methods=['GET'])
    app.add_url_rule(rule='/instance/extend/<int:instance_id>', view_func=extend_disk, methods=['GET'])
    app.add_url_rule(rule='/instance/configure/netcard/<int:instance_id>', view_func=instance_add_netcard, methods=['POST'])
    app.add_url_rule(rule='/instance/configure/<int:instance_id>', view_func=instance_configure, methods=['PUT'])
    app.add_url_rule(rule='/instance', view_func=instance_delete, methods=['DELETE'])
    app.add_url_rule(rule='/instance/migrate/init/<int:instance_id>', view_func=migrate_init, methods=['GET'])
    app.add_url_rule(rule='/instance/migrate/<int:instance_id>/to/<int:host_id>', view_func=instance_migrate, methods=['PUT'])
    app.add_url_rule(rule='/instance/hotmigrate/init/<int:instance_id>', view_func=hot_migrate_init, methods=['GET'])
    app.add_url_rule(rule='/instance/hotmigrate/<int:instance_id>/to/<int:host_id>', view_func=instance_hot_migrate,methods=['PUT'])
    app.add_url_rule(rule='/instance/info/<int:instance_id>', view_func=instance_detail, methods=['GET'])
    app.add_url_rule(rule='/instance/os_version_modify/<int:instance_id>', view_func=instance_os_version_modify,
                     methods=['POST'])
    app.add_url_rule(rule='/instance/console', view_func=console, methods=['GET'])
    app.add_url_rule(rule='/instance/clone/<int:instance_id>', view_func=instance_clone, methods=['POST'])
    app.add_url_rule(rule='/instance/recreate', view_func=instance_retry_create, methods=['PUT'])
    app.add_url_rule(rule='/instance/excel', view_func=export_instance_excel, methods=['GET'])
    app.add_url_rule(rule='/instance/clone/create', view_func=clone_create_intodb, methods=['POST'])
    app.add_url_rule(rule='/instance/retry', view_func=instance_retry, methods=['PUT'])
    app.add_url_rule(rule='/instance/del_template', view_func=instance_excel_del_template, methods=['GET'])
    app.add_url_rule(rule='/instance/del_upload_ins', view_func=upload_del_instance_excel, methods=['DELETE'])


    # 物理机管理模块
    app.add_url_rule(rule='/host/list', view_func=e_host_list.host_list, methods=['GET'])
    app.add_url_rule(rule='/host/<int:hostpool_id>', view_func=e_host.add_host, methods=['POST'])
    app.add_url_rule(rule='/host/lock/<int:host_id>', view_func=e_host_action.lock, methods=['PUT'])
    app.add_url_rule(rule='/host/maintain/<int:host_id>', view_func=e_host_action.maintain, methods=['PUT'])
    app.add_url_rule(rule='/host/info/<int:host_id>', view_func=e_host.get_host_detail, methods=['GET'])
    app.add_url_rule(rule='/host/delete', view_func=e_host.delete_host, methods=['PUT'])
    app.add_url_rule(rule='/host/operate', view_func=e_host_action.operate_host, methods=['PUT'])
    app.add_url_rule(rule='/host/<int:host_id>', view_func=e_host.host_update, methods=['PUT'])
    app.add_url_rule(rule='/host/excel', view_func=export_host_excel, methods=['GET'])

    # IP管理模块
    app.add_url_rule(rule='/ip/apply', view_func=ip_apply, methods=['POST'])
    app.add_url_rule(rule='/ip/hold', view_func=e_ip_hold.hold_ip, methods=['PUT'])
    app.add_url_rule(rule='/ip/batch/hold', view_func=e_ip_hold.hold_ips, methods=['PUT'])
    app.add_url_rule(rule='/ip/hold/cancel', view_func=e_ip_hold.cancel_hold_ip, methods=['PUT'])
    app.add_url_rule(rule='/ip/batch/hold/cancel', view_func=e_ip_hold.cancel_hold_ips, methods=['PUT'])
    app.add_url_rule(rule='/ip/init/<int:segment_id>', view_func=e_ip_init.init_ip, methods=['POST'])
    app.add_url_rule(rule='/ip/batch/init/<int:segment_id>', view_func=e_ip_init.init_ips, methods=['POST'])
    app.add_url_rule(rule='/ip/init/cancel', view_func=e_ip_init.cancel_init_ip, methods=['DELETE'])
    app.add_url_rule(rule='/ip/batch/init/cancel', view_func=e_ip_init.cancel_init_ips, methods=['DELETE'])
    app.add_url_rule(rule='/ip/info', view_func=ip_instance_info, methods=['GET'])
    app.add_url_rule(rule='/segment/init', view_func=e_segment.init_segment, methods=['GET'])
    app.add_url_rule(rule='/segment/<int:segment_id>/<int:page>', view_func=e_segment.get_ips_segment, methods=['GET'])
    app.add_url_rule(rule='/segment/add', view_func=add_segment, methods=['POST'])

    # 镜像管理模块
    app.add_url_rule(rule='/image/list', view_func=e_image_list.image_list, methods=['GET'])
    app.add_url_rule(rule='/image', view_func=e_image.add_image, methods=['POST'])
    app.add_url_rule(rule='/image', view_func=e_image.edit_image, methods=['PUT'])

    # 集群管理模块
    app.add_url_rule(rule='/hostpool/list', view_func=e_hostpool_list.hostpool_list, methods=['GET'])
    app.add_url_rule(rule='/hostpool/<int:net_area_id>', view_func=hostpool_add, methods=['POST'])
    app.add_url_rule(rule='/hostpool', view_func=hostpool_delete, methods=['DELETE'])
    app.add_url_rule(rule='/hostpool/<int:hostpool_id>', view_func=hostpool_update, methods=['PUT'])
    app.add_url_rule(rule='/hostpool/levelinfo', view_func=e_hostpool_other.get_hostpool_level_info, methods=['GET'])
    app.add_url_rule(rule='/hostpool/<int:hostpool_id>/monitor', view_func=hostpool_monitor, methods=['GET'])
    app.add_url_rule(rule='/hostpool/excel', view_func=export_hostpool_excel, methods=['GET'])

    # 机房管理模块
    app.add_url_rule(rule='/datacenter/list', view_func=e_datacenter_list.datacenter_list, methods=['GET'])
    app.add_url_rule(rule='/datacenter/<int:area_id>', view_func=datacenter_add, methods=['POST'])
    app.add_url_rule(rule='/datacenter', view_func=datacenter_delete, methods=['DELETE'])
    app.add_url_rule(rule='/datacenter/<int:datacenter_id>', view_func=datacenter_update, methods=['PUT'])
    app.add_url_rule(rule='/datacenter/<int:datacenter_id>/area/<int:area_id>', view_func=allocate_dc_2_area, methods=['PUT'])
    app.add_url_rule(rule='/datacenter/<int:datacenter_id>/monitor', view_func=datacenter_monitor, methods=['GET'])

    # 区域管理模块
    app.add_url_rule(rule='/area/list', view_func=area_list, methods=['GET'])
    app.add_url_rule(rule='/area', view_func=area_add, methods=['POST'])
    app.add_url_rule(rule='/area', view_func=area_delete, methods=['DELETE'])
    app.add_url_rule(rule='/area/<int:area_id>', view_func=area_update, methods=['PUT'])
    app.add_url_rule(rule='/area/<int:parent_area_id>/<int:child_area_id>', view_func=add_child_area, methods=['PUT'])
    app.add_url_rule(rule='/area/child/<int:area_id>', view_func=get_child_areas, methods=['GET'])
    app.add_url_rule(rule='/area/parent', view_func=get_parent_areas, methods=['GET'])
    app.add_url_rule(rule='/area/levelinfo', view_func=get_area_level_info, methods=['GET'])

    # 用户管理模块
    app.add_url_rule(rule='/user', view_func=e_user_manager.add_user, methods=['POST'])
    app.add_url_rule(rule='/user/info', view_func=e_user_manager.query_user_info, methods=['GET'])
    app.add_url_rule(rule='/user/list', view_func=e_user_list.user_list, methods=['GET'])
    app.add_url_rule(rule='/user', view_func=e_user_manager.update_user, methods=['PUT','DELETE'])

    # 登录
    app.add_url_rule(rule='/', view_func=user_init.index, methods=['GET', 'POST'])
    app.add_url_rule(rule='/login', view_func=user_init.login, methods=['POST'])
    app.add_url_rule(rule='/logout', view_func=user_init.logout, methods=['GET'])
    app.add_url_rule(rule='/index', view_func=user_init.index, methods=['GET'])
    app.add_url_rule(rule='/login/user', view_func=user_init.get_user, methods=['GET'])

    # 组管理模块
    app.add_url_rule(rule='/group/list', view_func=e_group_list.group_list, methods=['GET'])
    app.add_url_rule(rule='/group', view_func=e_group.add_group, methods=['POST'])
    app.add_url_rule(rule='/group/<int:group_id>', view_func=e_group.update_group, methods=['PUT'])
    app.add_url_rule(rule='/group/<int:group_id>', view_func=e_group.delete_group, methods=['DELETE'])
    app.add_url_rule(rule='/group/init_info/<int:group_id>', view_func=e_group.init_group_info, methods=['GET'])

    # 用户-组管理模块
    app.add_url_rule(rule='/user_group/<int:group_id>', view_func=e_user_group_list.users_in_group, methods=['GET'])
    app.add_url_rule(rule='/user_group/init_area', view_func=e_user_group.group_init_area_info, methods=['GET'])
    app.add_url_rule(rule='/user_group', view_func=e_user_group.delete_user_group, methods=['DELETE'])
    app.add_url_rule(rule='/user_group/insideuser/<int:group_id>', view_func=e_user_group.add_insideuser_to_group, methods=['POST'])
    app.add_url_rule(rule='/user_group/otheruser/<int:group_id>', view_func=e_user_group.add_outuser_to_group, methods=['POST'])

    # 网络区域模块
    app.add_url_rule(rule='/net_area/levelinfo', view_func=net_area_level_info_get, methods=['GET'])
    app.add_url_rule(rule='/net_area/list', view_func=net_area_list, methods=['GET'])
    app.add_url_rule(rule='/net_area/init_info', view_func=net_area_info_init, methods=['GET'])
    app.add_url_rule(rule='/net_area', view_func=net_area_add, methods=['POST'])
    app.add_url_rule(rule='/net_area', view_func=net_area_delete, methods=['DELETE'])
    app.add_url_rule(rule='/net_area/<int:net_area_id>', view_func=net_area_update, methods=['PUT'])
    app.add_url_rule(rule='/net_area/<int:net_area_id>/monitor', view_func=net_area_monitor, methods=['GET'])

    # 用户反馈模块
    app.add_url_rule(rule='/feedback/list', view_func=e_feedback_list.feedback_list, methods=['GET'])
    app.add_url_rule(rule='/feedback', view_func=e_feedback.get_problem_category, methods=['GET'])
    app.add_url_rule(rule='/feedback/add', view_func=e_feedback.add_feedback, methods=['POST'])

    # Balent监控
    app.add_url_rule(rule='/monitor', view_func=balent_monitor.monitor, methods=['POST'])
    app.add_url_rule(rule='/health', view_func=health_monitor, methods=['GET'])

    # v2v_openstack
    app.add_url_rule(rule='/v2v/openstack/init', view_func=v2v_op_init_info, methods=['GET'])
    app.add_url_rule(rule='/v2v/list', view_func=V2v_Op_Info, methods=['GET'])
    app.add_url_rule(rule='/v2v/openstack/cancel', view_func=v2v_openstack_cancel, methods=['PUT'])
    app.add_url_rule(rule='/v2v/openstack/retry', view_func=v2v_openstack_retry, methods=['PUT'])
    app.add_url_rule(rule='/v2v/openstack/<int:hostpool_id>', view_func=v2v_openstack_intodb, methods=['POST'])
    app.add_url_rule(rule='/v2v/openstack', view_func=v2v_openstack_del, methods=['DELETE'])
    app.add_url_rule(rule='/v2v/openstack/task_check', view_func=task_check, methods=['POST'])
    app.add_url_rule(rule='/v2v/openstack/batch_2', view_func=intodb_batch, methods=['POST'])
    app.add_url_rule(rule='/v2v/openstack/batch/import', view_func=import_excel_openstack, methods=['POST'])
    app.add_url_rule(rule='/v2v/openstack/excel', view_func=download_excel_openstack, methods=['GET'])

    # v2v_esx
    app.add_url_rule(rule='/v2v/esx/define', view_func=esx_vm_define, methods=['POST'])
    app.add_url_rule(rule='/v2v/esx/init', view_func=v2v_esx_init_info, methods=['GET'])
    app.add_url_rule(rule='/v2v/esx/<int:hostpool_id>', view_func=v2v_esx_intodb, methods=['POST'])
    app.add_url_rule(rule='/v2v/esx/batch', view_func=esx_intodb_batch, methods=['POST'])
    app.add_url_rule(rule='/v2v/esx/batch/import', view_func=import_excel_esx, methods=['POST'])
    app.add_url_rule(rule='/v2v/esx/excel', view_func=download_excel_esx, methods=['GET'])

    app.add_url_rule(rule='/v2v/task/excel', view_func=export_v2v_task_excel, methods=['GET'])

    # 验证码
    app.add_url_rule(rule='/VerifyCode', view_func=verify_code_create, methods=['GET'])

    # 维石接口获取token
    app.add_url_rule(rule='/api/token', view_func=user_init.other_api_get_auth_token, methods=['POST'])
    app.add_url_rule(rule='/api/instance_create', view_func=instance_create_from_other_platform_with_ip, methods=['POST'])
    app.add_url_rule(rule='/api/instance_create_prd_dr', view_func=instance_create_from_other_platform_prd_dr, methods=['POST'])
    app.add_url_rule(rule='/api/vip_apply', view_func=ip_apply_from_other_platform, methods=['POST'])
    app.add_url_rule(rule='/api/hostpool_capacity', view_func=hostpool_capacity_to_other_platform, methods=['POST'])
    app.add_url_rule(rule='/api/ip_segment', view_func=ip_resource_display_to_other_platform, methods=['GET'])
    app.add_url_rule(rule='/api/ip_segment_match', view_func=ip_resource_display_to_other_platform_new, methods=['POST'])
    app.add_url_rule(rule='/api/segment_capacity', view_func=segment_capacity_to_other_platform, methods=['POST'])
    app.add_url_rule(rule='/api/instance_configure/netcard', view_func=instance_add_netcard_from_other_platform,
                     methods=['POST'])
    app.add_url_rule(rule='/api/instance_create_with_ip', view_func=instance_create_from_other_platform_with_ip, methods=['POST'])
    app.add_url_rule(rule='/api/hostpool_info', view_func=hostpool_info_init, methods=['GET'])
    app.add_url_rule(rule='/api/instance_performance_data', view_func=instance_performance_data_to_other_platform, methods=['GET'])

    # 容灾微应用虚拟机信息
    app.add_url_rule(rule='/api/instance/miniarch/info', view_func=instance_detail_for_miniarch,
                     methods=['GET'])
    app.add_url_rule(rule='/api/instance/miniarch/status', view_func=instance_status_change_for_miniarch,
                     methods=['PUT'])

    # image_sync
    app.add_url_rule(rule='/image_sync/host_list/get_hosts', view_func=image_sy_host, methods=['GET'])
    app.add_url_rule(rule='/image_sync/host_list2/<int:host_id>', view_func=single_host_image_return, methods=['GET'])
    app.add_url_rule(rule='/image_sync/host_task_intodb', view_func=host_task_intodb, methods=['POST'])
    app.add_url_rule(rule='/image_sync/host_list/host_image_batch', view_func=get_image_host, methods=['POST'])

    # 物理机性能采集接口
    app.add_url_rule(rule='/host/host_perform_data', view_func=host_perform_data_to_db, methods=['POST'])

    # 应用组创建外部接口
    app.add_url_rule(rule='/api/group_add', view_func=group_create_from_other_platform, methods=['POST'])
    app.add_url_rule(rule='/api/ip/pre_allocation', view_func=ips_apply_from_other_platform, methods=['POST'])

    # kvm平台提供公共信息获取给软负载平台外部接口
    app.add_url_rule(rule='/api/sfslb_common_info', view_func=kvm_common_information_for_api.kvm_common_info, methods=['GET'])

    # 操作记录
    app.add_url_rule(rule='/operation/list', view_func=e_operation_list.operation_list, methods=['GET'])

    # 新的镜像管理相关信息
    app.add_url_rule(rule='/image_manage/list', view_func=image_manage_list.image_manage_list, methods=['GET'])
    app.add_url_rule(rule='/image_manage/create_new_init', view_func=image_create.image_create_init, methods=['GET'])
    app.add_url_rule(rule='/image_manage/create_new', view_func=image_create.image_create_new, methods=['POST'])
    app.add_url_rule(rule='/image_manage/create_exist_init', view_func=image_create.image_create_exist_init, methods=['GET'])
    app.add_url_rule(rule='/image_manage/create_by_exist', view_func=image_create.image_create_exist, methods=['POST'])
    app.add_url_rule(rule='/image_manage/update_by_exist', view_func=image_create.image_update_by_exist, methods=['POST'])
    app.add_url_rule(rule='/image_manage/image_release_by_new', view_func=image_release_by_new.image_release_by_new, methods=['POST'])
    app.add_url_rule(rule='/image_manage/image_release_by_exist', view_func=image_release_by_exist.image_release_by_exist, methods=['POST'])
    app.add_url_rule(rule='/image_manage/image_edit', view_func=image_edit.image_edit, methods=['POST'])
    app.add_url_rule(rule='/image_manage/image_checkout', view_func=image_checkout.image_checkout, methods=['POST'])
    app.add_url_rule(rule='/image_manage/console', view_func=image_tmp_console.image_console, methods=['GET'])


