# coding=utf8
'''
    常量定义
'''
__author__ = ""


class ErrorCode(object):
    SUCCESS = 0
    SUCCESS_PART = 1  # 部分成功，用于批量操作
    SYS_ERR = -10000  # 系统错误
    DUPLICATED_ERR = -10001  # 重复
    PARAM_ERR = -10002  # 参数错误
    CAPTCHA_ERR = -10003  # 验证码错误
    EXIST_USER = -10004  # 用户已经存在
    AUTH_ERROR = -10005  # 权限认证错误 用户签名错误
    NOT_EXIST_USER = -10006  # 用户不存在
    PWD_ERR = -10007  # 密码错误
    RATE_LIMIT_ERR = -10008  # 请求过于频繁
    ALL_FAIL = -10009  # 全部失败，用于批量操作

    ########################################
    MOBILE_FORMAT_ERR = -20000
    EXISTED_BIND_MOBILE = -20001

    USER_OR_PWD_ERR = -20002  # 用户名或者密码错误
    THIRD_PARTY_ERR = -20003  # 第三方平台校验错误


class ErrorMsg(object):
    MSG_DICT = {
        ErrorCode.SUCCESS: 'success',
        ErrorCode.SYS_ERR: 'sys error',
        ErrorCode.DUPLICATED_ERR: 'duplicated error',
        ErrorCode.PARAM_ERR: 'param error',
        ErrorCode.CAPTCHA_ERR: 'captcha error',
        ErrorCode.EXIST_USER: 'existed user',
        ErrorCode.AUTH_ERROR: 'auth error',
        ErrorCode.NOT_EXIST_USER: 'not exist error',
        ErrorCode.PWD_ERR: 'pwd error',
        ErrorCode.RATE_LIMIT_ERR: 'rate limit error',

        ErrorCode.MOBILE_FORMAT_ERR: 'mobile error',
        ErrorCode.EXISTED_BIND_MOBILE: 'existed bind mobile',
        ErrorCode.USER_OR_PWD_ERR: 'user or pwd error',
        ErrorCode.THIRD_PARTY_ERR: 'third party auth error',
    }


class IPStatus(object):
    '''
        IP状态
    '''
    UNUSED = '0'
    USED = '1'
    HOLD = '2'
    PRE_ALLOCATION = '3'


class IPStatusMsg(object):
    MSG_DICT = {
        IPStatus.UNUSED: '未使用',
        IPStatus.USED: '已使用',
        IPStatus.HOLD: '已保留',
    }


class VMStatus(object):
    '''
        虚拟机状态
    '''
    CREATING = '0'  # 创建中
    SHUTDOWN = '1'  # 关机
    SHUTDOWN_ING = '2'  # 关机中
    STARTUP = '3'  # 运行中
    STARTUP_ING = '4'  # 开机中
    SUSPENDED = '5'  # 挂起
    PAUSED = '6'  # 暂停
    MIGRATE = '7'  # 热迁移中
    COLD_MIGRATE = '8'  # 冷迁移中
    CONVERTING = '9'  # 转化中
    CLONEING = '10'  # 克隆中
    OTHER = '98'  # 其他
    ERROR = '99'  # 错误
    CREATE_ERROR = '100'  # 虚拟机创建失败
    CLONE_ERROR = '101'  # 虚拟机克隆失败
    CLONE_CREATE_ERROR = '102'  # 虚拟机克隆创建失败
    UNDER_CLONE = '103'  # 虚拟机被克隆中
    CONFIGURE_ING = '104'  # 虚拟机被克隆中
    MINIARCH_MIGRATE = '105'  # 微应用虚拟机迁移中


class VMStatusMsg(object):
    MSG_DICT = {
        VMStatus.CREATING: '创建中',
        VMStatus.SHUTDOWN: '关机',
        VMStatus.SHUTDOWN_ING: '关机中',
        VMStatus.STARTUP: '运行中',
        VMStatus.STARTUP_ING: '开机中',
        VMStatus.SUSPENDED: '挂起',
        VMStatus.PAUSED: '暂停',
        VMStatus.MIGRATE: '热迁移中',
        VMStatus.COLD_MIGRATE: '冷迁移中',
        VMStatus.CONVERTING: '转化中',
        VMStatus.CLONEING: '克隆中',
        VMStatus.OTHER: '其他',
        VMStatus.ERROR: '错误',
        VMStatus.CREATE_ERROR: '虚拟机创建失败',
        VMStatus.CLONE_ERROR: '虚拟机克隆失败',
        VMStatus.CLONE_CREATE_ERROR: '虚拟机克隆创建失败'
    }


class VMTypeStatus(object):
    '''
        虚拟机业务状态
    '''
    NORMAL = '0'
    OFF_LINE = '1'
    LOCKED = '2'


class VMTypeStatusMsg(object):
    MSG_DICT = {
        VMTypeStatus.NORMAL: '正常',
        VMTypeStatus.OFF_LINE: '下线',
        VMTypeStatus.LOCKED: '锁定',
    }


class VMCreateSource(object):
    '''
        虚拟机创建来源
    '''
    CLOUD_SOURCE = '0'
    OPENSTACK = '1'
    ESX = '2'

class ImageManage(object):
    '''
        镜像管理状态
    '''
    INIT = '-1'
    USABLE = '0'
    EDITING = '1'
    CHECKOUT = '2'
    RELEASING = '3'
    ERROR = '-10000'



class VMLibvirtStatus(object):
    '''
        虚拟机LIBVIRT状态
    '''
    SHUTDOWN = 5  # 关机
    STARTUP = 1   # 开机
    ERROR = -100  # 获取状态失败


class HostStatus(object):
    '''
        物理机稳定状态
    '''
    RUNNING = '0'  # 运行中
    STOP = '1'  # 关机
    ERROR = '99'  # 错误


class HostStatusMsg(object):
    MSG_DICT = {
        HostStatus.RUNNING: '运行中',
        HostStatus.STOP: '关机',
        HostStatus.ERROR: '错误',
    }


class HostLibvirtdStatus(object):
    '''
        物理机稳定状态
    '''
    NORMAL = '0'  # 正常
    UNUSUAL = '1'  # 异常


class HostTypeStatus(object):
    '''
        物理机业务状态
    '''
    NORMAL = '0'  # 正常
    LOCK = '1'  # 锁定
    MAINTAIN = '2'  # 维护


class HostTypeStatusMsg(object):
    MSG_DICT = {
        HostTypeStatus.NORMAL: '正常',
        HostTypeStatus.LOCK: '锁定',
        HostTypeStatus.MAINTAIN: '维护',
    }


class HostOperate(object):
    '''
        物理机远程操作
    '''
    START = 0  # 开机
    STOP = 1  # 硬关机
    SOFT_STOP = 2  # 软关机
    RESET = 3  # 硬重启
    SOFT_RESET = 4  # 软重启


class ImageType(object):
    '''
        镜像类型
    '''
    SYSTEMDISK = '0'  # 系统盘
    DATADISK = '1'  # 数据盘


class DataCenterType(object):
    '''
        机房类型
    '''
    OTHER = 0
    SIT = 1
    STG = 2
    DEV = 3
    PRD = 4
    DR = 5
    MINIARCHDR = 6
    TENCENTDR = 7
    PST = 8
    IST = 9


class DataCenterTypeForVishnu(object):
    TYPE_DICT = {
        'OTHER': DataCenterType.OTHER,
        'SIT': DataCenterType.SIT,
        'STG': DataCenterType.STG,
        'DEV': DataCenterType.DEV,
        'PRD': DataCenterType.PRD,
        'DR': DataCenterType.DR,
        'MINIARCHDR': DataCenterType.MINIARCHDR,
        'TENCENTDR': DataCenterType.TENCENTDR,
        'PST': DataCenterType.PST,
        'IST': DataCenterType.IST
    }


class DataCenterTypeMsg(object):
    MSG_DICT = {
        DataCenterType.SIT: '测试',
        DataCenterType.STG: '准生产',
        DataCenterType.DEV: '研发',
        DataCenterType.PRD: '生产',
        DataCenterType.DR: '容灾',
        DataCenterType.OTHER: '其他',
        DataCenterType.MINIARCHDR: '容灾微应用',
        DataCenterType.TENCENTDR: '腾讯双活容灾',
        DataCenterType.PST: '容灾压测',
        DataCenterType.IST: '测试压测'
    }


class DataCenterTypeTransform(object):
    MSG_DICT = {
        DataCenterType.SIT: 'sit',
        DataCenterType.STG: 'stg',
        DataCenterType.DEV: 'dev',
        DataCenterType.PRD: 'prd',
        DataCenterType.DR: 'dr',
        DataCenterType.MINIARCHDR: 'miniarchdr',
        DataCenterType.TENCENTDR: 'tencentdr',
        DataCenterType.PST: 'pst',
        DataCenterType.IST: 'ist'
    }


class DataCenterTypeTransformCapital(object):
    MSG_DICT = {
        DataCenterType.SIT: 'SIT',
        DataCenterType.STG: 'STG',
        DataCenterType.DEV: 'DEV',
        DataCenterType.PRD: 'PRD',
        DataCenterType.DR: 'DR',
        DataCenterType.OTHER: 'OTHER',
        DataCenterType.MINIARCHDR: 'MINIARCHDR',
        DataCenterType.TENCENTDR: 'TENCENTDR',
        DataCenterType.PST: 'PST',
        DataCenterType.IST: 'IST'
    }


class UserStatus(object):
    '''
        用户状态
    '''
    NORMAL = '0'  # 正常
    LOCK = '1'  # 锁定
    OTHER = '2'  # 其他


class UserAuthType(object):
    '''
        用户认证类型
    '''
    AD = '0'  # AD认证
    LOCAL = '1'  # 本地认证
    EXTERNAL = '2'  # 外部应用调用


class KafkaTopic(object):
    '''
        kafka消息主题
    '''
    INSTANCE = 'ESG_CLOUD_PORTAL'
    IMAGE = 'image'
    DEFAULT = 'default'
    V2V = 'v2v'


class v2vActions(object):
    '''
        v2v操作的几个步骤
    '''
    CREATE_DEST_DIR = "create_destination_dir"
    VM_DISK_STANDARDLIZE = "standardlize_target_vm_diskname"
    GET_VM_FILE = "get_vm_file"
    COPY_VM_DISK = "copy_vm_disk_to_desthost"
    COPY_VM_XML = "copy_vm_xml_to_desthost"
    VM_STANDARDLIZE = "standardlize_target_vm"
    VM_DEFINE = "define_target_vm"
    IP_INJECT = "inject_vm_ip_configuration"
    VM_START = "start_target_vm"
    BEGIN = "begin"
    CREATE_STOR_POOL = "create_storage_pool"

class vmRetryActions(object):
    '''
        vm页面重试操作的类型
    '''
    INSTANCE_CREATE_RETRY = "createFailed"
    INSTANCE_CLONE_CREATE_RETRY = "cloneFailed"


class esx_v2vActions(object):
    '''
        v2v操作的几个步骤
    '''
    BEGIN = "0"
    CREATE_DEST_DIR = "1"
    CREATE_STOR_POOL = "2"
    COPY_FILE_TO_LOCAL = "3"
    VIRT_V2V_FILES = "4"
    DELETE_TMP_FILE = "5"
    VM_SYS_DISK_STD = "6"
    VM_DATA_DISK_STD = "7"
    VM_DEFINE1 = "8"
    VM_START1 = "9"
    ATTACH_DISK = "10"
    WINDOWS_DISK_CH = "11"
    VM_START2 = "12"
    WINDOWS_STD = "13"


class InstaceActions(object):
    '''
        虚拟机创建的几个步骤
    '''
    INSTANCE_DIRECTORY_CREATE = "instance_directory_create"
    IMAGE_SYNC_STATUS = "image_sync_status"
    IMAGE_STATUS = "image_status"
    STORAGE_POOL_CREATE = "storage_pool_create"
    IMAGE_CLONE = "image_clone"
    DISK_XML_CREATE = "disk_create"
    INSTANCE_CREATE = "instance_create"
    INSTANCE_INJECT_DATA = "instance_inject_data"

    INSTANCE_STARTUP = 'instance_startup'
    INSTANCE_SHUTDOWN = 'instance_shutdown'
    INSTANCE_REBOOT = 'instance_reboot'
    INSTANCE_CHANGE_CONFIGURE = 'instance_change_configure'
    INSTANCE_ADD_NETCARD = 'instance_add_netcard'

    INSTANCE_DISK_MOUNTPOINT_CHECK = 'instance_disk_mountpoint_check'
    INSTANCE_DISK_CHECK = 'instance_disk_check'
    INSTANCE_DISK_LV_CHECK = 'instance_disk_lv_check'
    INSTANCE_DISK_SIZE_CHECK = 'instance_disk_size_check'
    INSTANCE_DISK_RESIZE = 'instance_disk_resize'
    INSTANCE_DISK_DEVICE = 'instance_disk_device'
    INSTANCE_STATUS_CHECK = 'instance_status_check'
    INSTANCE_DISK_INJECT_TO_OS = 'instance_disk_INJECT_TO_OS'

    INSTANCE_COLD_MIGRATE_CONFIRM_SPEED = 'instance_cold_migrate_confirm_speed'
    INSTANCE_COLD_MIGRATE_VOL_XML_MD5_S = 'instance_cold_migrate_vol_xml_md5_source'
    INSTANCE_COLD_MIGRATE_VOL_XML_MD5_D = 'instance_cold_migrate_vol_xml_md5_dest'
    INSTANCE_COLD_MIGRATE_MKDIR_DIR = 'instance_cold_migrate_mkdir_dir'
    INSTANCE_COLD_MIGRATE_STORAGE_POOL = 'instance_cold_migrate_storage_pool'
    INSTANCE_COLD_MIGRATE_VOL_XML_COPY = 'instance_cold_migrate_vol_xml_copy'
    INSTANCE_COLD_MIGRATE_MD5_MATCH = 'instance_cold_migrate_md5_match'
    INSTANCE_COLD_MIGRATE_DEFINE_D = 'instance_cold_migrate_define_dest'
    INSTANCE_COLD_MIGRATE_UNDEFINE_S = 'instance_cold_migrate_undefine_source'
    INSTANCE_COLD_MIGRATE_BACKUP_NAME = 'instance_cold_migrate_backup_name'
    INSTANCE_COLD_MIGRATE_CANCEL_SPEED = 'instance_cold_migrate_cancel_speed'

    INSTANCE_HOT_MIGRATE_DISK_INFO = 'instance_hot_migrate_disk_info_get'
    INSTANCE_HOT_MIGRATE_HOSTS_ADD = 'instance_hot_migrate_add_hosts'
    INSTANCE_HOT_MIGRATE_MKDIR_DIR = 'instance_hot_migrate_mkdir_dir'
    INSTANCE_HOT_MIGRATE_STORAGE_POOL  = 'instance_hot_migrate_storage_pool'
    INSTANCE_HOT_MIGRATE_CREATE_DISK = 'instance_hot_migrate_creat_disk'
    INSTANCE_HOT_MIGRATE_CHECK_DISK = 'check has all disk created success'
    INSTANCE_HOT_MIGRATE_START_MOVE  = 'instance_hot_migrate_start_move'
    INSTANCE_HOT_MIGRATE_UNDEFINE_S = 'instance_hot_migrate_undefine_source'
    INSTANCE_HOT_MIGRATE_BACKUP_NAME = 'instance_hot_migrate_backup_name'

    INSTANCE_CLONE_CHECK_HOST_STATUS = 'instance_clone_check_host_status'
    INSTANCE_CLONE_CREATE_DIR = 'instance_clone_create_dir'
    INSTANCE_CLONE_CREATE_STORAGE_POOL = 'instance_clone_create_storage_pool'
    INSTANCE_CLONE_TRANS_IMAGE= 'instance_clone_trans_image'
    INSTANCE_CLONE_DISK_SNAPSHOT = 'instance_disk_snapshot_create'
    INSTANCE_CLONE_DISK_SNAPSHOT_COMMIT = 'instance_clone_disk_snapshot_commit'
    INSTANCE_CLONE_RENAME_IMAGES = 'instance_clone_rename_images'
    INSTANCE_CLONE_CREATE_XML_AND_STORAGE = 'instance_clone_create_xml_and_storage'
    INSTANCE_CLONE_DEFINE_VM = 'instance_clone_define_vm'
    INSTANCE_CLONE_START_VM= 'instace_clone_start_vm'
    INSTANCE_CLONE_CREATE_GET_IMAGE = 'instance_clone_create_get_image_file'
    INSTANCE_CLONE_BT_TRANS_IMAGE = 'instance_clone_create_bt_trans_imagefiles'
    INSTANCE_CLONE_CREATE_PRE_CONF = 'instance_clone_create_pre_configuration'
    INSTANCE_CLONE_CREATE_NET_UP = 'instance_clone_create_up_network'
    INSTANCE_CLONE_CREATE_CP_IMAGE = 'instance_clone_create_cp_images'
    INSTANCE_CLONE_CREATE_CHMOD = 'instance_clone_create_change_image_mod'


###############################3add 2017/09/29
    INSTANCE_UPDATE_QEMU_AGENT = 'instance_update_qemu_agent'
    INSTANCE_DISK_INFO_DISPLAY = 'instance_disk_info_display'
    INSTANCE_DISK_EXTEND = 'instance_disk_extend'
    INSTANCE_LIBVIRT_ERROR = 'instance_libvirt_error'
    INSTANCE_ATTACH_NEW_DISK = 'instance_attach_new_disk'
    INSTANCE_DISK_DEV_EXTEND = 'instance_disk_dev_extend'
    INSTANCE_DISK_LV_EXTEND = 'instance_disk_lv_extend'
    INSTANCE_DISK_LV_CREATE = 'instance_disk_lv_create'
    INSTANCE_DISK_VG_EXTEND = 'instance_disk_vg_extend'
    INSTANCE_DISK_VG_CREATE = 'instance_disk_vg_create'
    INSTANCE_CREATE_MOUNT_POINT = 'instance_create_mount_point'
    INSTANCE_MOUNT_DISK = 'instance_mount_disk'
    INSTANCE_WRITE_DISK = 'instance_write_disk'


class CentOS_Version(object):
    CentOS_7 = 'CentOS_7'
    CentOS_6 = 'CentOS_6'



class ActionStatus(object):
    '''
        虚拟机操作类：成功，失败，开始
    '''
    START = 0
    SUCCSESS = 1
    FAILD = 2
    OTHER = 3


class MigrateStatus(object):
    '''
        迁移任务状态
    '''
    DOING = '0'
    SUCCESS = '1'
    FAILED = '2'


class EnvType(object):
    '''
        项目运行环境
    '''
    DEV = 'dev'  # 开发
    VISHNUDEV = 'vishdev'  # 维石接口开发环境
    VISHNUSTG = 'vishstg'  # 维石接口用户验收环境
    SIT = 'sit'  # SIT
    PRO_1 = 'pro_1'  # 生产1
    PRO_2 = 'pro_2'  # 生产2
    PRA = 'pra' # 灰度
    EXHIBITION = 'exhibition'  # 展示环境
    PST = 'pst'  # 容灾压测环境


class VsJobStatus(object):
    '''
        维石平台任务步骤执行结果
    '''
    SUCCEED = 'succeed'
    FAILED = 'failed'


class AuditType(object):
    '''
        安全审计日志类型
    '''
    LOGIN = 1  # 登录日志
    USERMGR = 2  # 用户管理日志
    PERMMGR = 3  # 角色/权限管理日志
    SENSITIVEINFO = 6  # 敏感信息操作日志


class esx_env(object):
    '''
        esx_env
    '''
    SIT = '1'
    STG = '2'
    DEV = '3'
    PRD = '4'
    DR = '5'

# 安全规定的操作编码
AuditOperType = {
    'POST': '001',
    'PUT': '002',
    'DELETE': '003',
    'GET': '011',
    'LOGIN': '013',
    'LOGOUT': '014'
}


class OperationObject(object):
    LOGIN_LOGOUT = "登录/登出"
    AREA = "区域"
    DATACENTER = "机房"
    NET_AREA = "网络区域"
    HOSTPOOL = "集群"
    HOST = "HOST"
    VM = "VM"
    IP = "IP"
    IMAGE = "镜像"
    USER_GROUP = "应用组"
    MIGRATE = "迁移"
    OPERATION = "操作记录"
    FEEDBACK = "用户反馈"


class OperationAction(object):
    LOGIN = "登录"
    LOGOUT = "登出"
    ADD = "新增"
    ALTER = "修改"  # 修改、配置
    DELETE = "删除"
    CREATE = "创建"  # 暂未使用
    STARTUP = "开机"
    SHUTDOWN = "关机"
    REBOOT = "重启"  # 暂未使用
    MIGRATE = "冷迁移"
    HOT_MIGRATE = "热迁移"
    CLONE_BACKUP = "克隆备份"
    CLONE_CREATE = "克隆创建"
    LOCK = "锁定"
    CONSOLE = "打开控制台"
    OPERATE = "其他操作"
    MAINTAIN = "维护"
    REMOVE_USER = "移除用户"
    ADD_INSIDE_USER = "新增域用户"
    ADD_OUTER_USER = "新增外部用户"
    IP_APPLY = "申请IP"
    HOLD_IP = "保留IP"
    CANCEL_HOLD_IP = "取消保留IP"
    INIT_IP = "初始化IP"
    CANCEL_INIT_IP = "取消初始化IP"


class ApiOrigin(object):
    VISHNU = '0'
    SFSLB = '1'
    FWAF = '2'


class ApiOriginString(object):
    VISHNU = 'vishnu'
    SFSLB = 'sfslb'
    FWAF = 'fwaf'


class IpLockStatus(object):
    UNUSED = '0'
    USED = '1'


class InstanceCloneCreateTransType(object):
        BT = '0'
        WGET = '1'


class IpType(object):
    '''
        机房类型
    '''
    UNALLOCATED = '0'
    ALLOCATED = '1'
    HOLD = '2'
    PREALLOCATED = '3'
    UNINIT = '4'


class IpTypeTransform(object):
    MSG_DICT = {
        IpType.UNALLOCATED: 'unallocated',
        IpType.ALLOCATED: 'allocated',
        IpType.HOLD: 'hold',
        IpType.PREALLOCATED: 'preallocated',
        IpType.UNINIT: 'uninit'
    }


class V2vTaskStatus(object):
    '''
        v2v任务状态
    '''
    RUNNING = '0'  # 运行中
    FINISH = '1'  # 已完成
    ERROR = '2'  # 错误
    CANCEL = '3'  # 已取消


class V2vTaskStatusTransform(object):
    MSG_DICT = {
        V2vTaskStatus.RUNNING: '运行中',
        V2vTaskStatus.FINISH: '已完成',
        V2vTaskStatus.ERROR: '错误',
        V2vTaskStatus.CANCEL: '已取消'
    }


class V2vCreateSource(object):
    '''
        v2v任务状态
    '''
    OPENSTACK = '1'  # OPENSTACK迁移
    ESX = '2'  # ESX迁移


class V2vCreateSourceTransform(object):
    MSG_DICT = {
        V2vCreateSource.OPENSTACK: 'OPENSTACK迁移',
        V2vCreateSource.ESX: 'ESX迁移'
    }

class image_manage_action(object):
    INITED = 'inited'
    START_VEM = 'start_template_vm'
    IP_INJECT = 'inject_ip_to_vemplate'
    IP_REMOVE = 'remove_ip_from_vemplate'
    VEM_SHUTDOWN = 'shutdown_template_vm'
    RELEASE_IMGSERVER = 'release_to_img_server'
    RELEASE_CACHESERVER = 'release_to_cache_server'

class image_mange_action_state(object):
    SUCCESSED = '0'
    FAILED = '1'

class img_tmp_status(object):
    SHUTDOWN = '1'
    RUNNING = '0'

class image_ceate_type(object):
    ALL_NEW = '0'
    FROM_EXIST = '1'
    USING = '2'
    UPDATE_EXIST = '-1'


class NetCardType(object):
    INTERNAL = '0'
    INTERNEL_TELECOM = '1'
    INTERNEL_UNICOM = '2'
    INTERNAL_IMAGE = '3'
    INTERNAL_NAS = '4'
    TENCENT_CLOUD_NORMAL = '5'


class NetCardTypeToDevice(object):
    MSG_DICT = {
        NetCardType.INTERNAL: 'bond0',
        NetCardType.INTERNAL_NAS: 'bond1'
    }


class NetCardStatus(object):
    UP = 'up'
    DOWN = 'down'


class PingStatus(object):
    SUCCEED = 0
    FAILED = 1


class InstanceNicType(object):
    MAIN_NETWORK_NIC = '0'
    NORMAL_NETWORK_NIC = '1'


class NetworkSegmentStatus(object):
    ENABLE = '0'
    DISABLE = '1'
