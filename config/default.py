# coding=utf8
# __author__ =  ""
# usage：sit environment use 'ENV = EnvType.SIT'

from pyDes import *
from base64 import *
from model.const_define import EnvType, VMStatus, DataCenterType
import os
def encrypt(str, key="ABCD-DBACFFF-KEY"):
    k = triple_des(key, CBC, "\0\1\2\3\4\5\6\7", pad=None, padmode=PAD_PKCS5)
    return encodestring(k.encrypt(str))[:-1]


ENV = EnvType.SIT

if ENV == EnvType.SIT:
    GLOBAL_CONFIG = {
        'db': {
            'kvm': {
                'db_type': 'mysql',
                'maxconnections': 300,  # 允许的最大连接数,
                'user': '用户名',
                'passwd': encrypt("用户名密码"),
                'host': '数据库地址',
                'port': 3306,
                'charset': 'utf8',  # 不指定的话,默认utf8
                'database_name': '数据库名',  # 数据库的名字,
                'setsession': ['set autocommit = 1'],
            },
        },
        'flask': {
            'api_web_sit': {
                'host': '0.0.0.0',
                'port': 8080,
                'debug_mode': True,
                'reg_module_name': 'web_api',  # 这里对应reg_route文件中的相关名字
                'logLevel': 'INFO',
                'logPath': './api_web_sit.log'
            },
        },

        'ASYNC_MESSAGE_BROKER': {
            'type': 'kafka',
            'config': {
                'hosts': '布置了kafka集群的ip：端口，例：10.10.10.10:80，',
                'zookeeper_hosts': '管理卡发卡集群的地址/kafka/itdc',
                'broker_version': '0.8.2',  # 这里需要跟服务端的kafka保持一致
            },
            'init_threads_num': 100,
            'max_threads_num': 1000,
            'thread_idle_time': 60 * 5,
            'log_path': './sit_kafka_consumer.log',
            'log_level': 'DEBUG',
        },
        'host_console_url': {
                "consoleAddress": "定义前端host console请求地址，例http://10.20.10.10:80",  # 定义前端host console请求地址，前端定义在static/js/config/config.json
                "awsKey": "12345678",
                "awsIv": "abcdef"
        }
    }

    # ************** kafka主题名称 ****************
    KAFKA_TOPIC_NAME = 'ESG_CLOUD_PORTAL'

    # vm默认root密码
    INSTANCE_ROOT_DEFAULT_PASS = encrypt("vm创建的默认密码")

    # **********ansiable参数  start***********************
    ANSIABLE_REMOTE_USER = "ansible用户账号"
    ANSIABLE_REMOTE_PWD = encrypt("ansible用户登录密码")
    ANSIABLE_REMOTE_SU_USER = "root"
    ANSIABLE_REMOTE_SU_PWD = encrypt("root用户密码")
    # **********ansiable参数  end*************************

    # ********* 获取物理机性能数据文件用户密码 **************
    GET_HOST_PERFORMANCE_USER = "获取物理机性能的用户名"
    GET_HOST_PERFORMANCE_PWD = encrypt("获取物理机性能的用户名密码")
    # ********* 获取物理机性能数据文件用户密码 **************

    # ********* 镜像服务器地址 ***************************
    IMAGE_SERVER = ['镜像的服务器地址']  # 例：['10.20.10.20']
    IMAGE_SERVER_PORT = 80

    # ********* tracker服务器地址 ***************************
    TRACKER_SERVER = ['tracker服务器地址']    # 例：['10.20.10.20']
    TRACKER_SERVER_PORT = 2710

    # ********* 镜像缓存服务器地址 ******************************************************
    # 数据48为网络区域DCN1 id，新增一个网络区域请录入网络区域id和对应的镜像缓存服务器信息
    NET_AREA_IMAGE_CACHE_SERVER = {
        '80': ['镜像的缓存服务器'], # 例：['10.20.10.20','10.20.10.30']
        '95': ['镜像的缓存服务器'],
        '99': ['镜像的缓存服务器']
    }
    NET_AREA_IMAGE_CACHE_SERVER_PORT = 3128

    # ********** 定义数据盘大小 ***************
    DATA_DISK_GB = 50

    # ************** 物理机性能数据收集url ****************
    HOST_PERFORMANCE_COLLECT_URL = '物理机性能的收集地址'  # ；https://10.20.20.10

    # 物理机远程操作
    SERVER_USER = "物理机远程登录账号"
    SERVER_PWD = encrypt("物理机登录密码")

    # ********** image_manage *********************
    IMAGE_EDIT_SERVER = '镜像编辑服务器'  #'10.20.10.10'  镜像编辑服务器

    INSTANCE_NETCARD_NUMS = 3

    # 允许虚拟机创建时一台物理机上最大的虚拟机数量
    INSTANCE_MAX_NUMS_IN_HOST = 50







LOG_PATH = './flask-d.log'

HOST_LIBVIRT_USER = "libvirt的用户账号"
HOST_LIBVIRT_PWD = encrypt("libvirt的用户密码")
HOST_LIBVIRT_LOGIN_TYPE = 1
ROOT_PWD = encrypt("root的密码")
HOST_NET_CARD = 'bond0'

CONN_SOCKET = 4
CONN_TLS = 3
CONN_SSH = 2
CONN_TCP = 1
TLS_PORT = 16514
SSH_PORT = 22
TCP_PORT = 16509

INSTANCE_DISK_PATH = '/app/image/%s/%s'
IMAGE_PATH = '/app/image/%s'

# 虚拟机批量操作的最大数目
INSTANCE_MAX_CREATE = '100'  # 创建
INSTANCE_MAX_STARTUP = '100'   # 开机
INSTANCE_MAX_SHUTDOWN = '100'   # 关机
INSTANCE_MAX_DELETE = '100'   # 删除

# **********Balent监控调用  start************
# BALANT_ATTR = ['CpuUsagePercent', 'usage_percent', 'RXDiff', 'TXDiff', 'Write', 'Read']  # 监控项
# 监控项
BALANT_ATTR = ['used', 'Memused', 'recBytesPerSec', 'sendBytesPerSec', 'totalWriteBytesPerSec', 'totalReadBytesPerSec']
# BALANT_ATTR = ['recBytesPerSec', 'sendBytesPerSec']

API_GET_TARGET_ID = "/balantflow/restservices/montarget"
API_GET_METRICS = "/balantflow/restservices/monmetric"
API_GET_METRIC_DATA = "/balantflow/restservices/monmetricdata"
# **********Balent监控调用  end************

ST_ENVIRONMENT = [DataCenterType.PST, DataCenterType.IST]

# **********instance和host状态数据收集  start************
# instance数据收集
INSTANCES_COLLECT_INTERVAL = 3  # 收集时间间隔（秒）
INSTANCES_COLLECT_NUMS = 1000  # 一次任务的线程数
INSTANCES_COLLECT_WORK_INTERVAL = 5  # 任务时间间隔（秒）
INSTANCE_STATUS_NOT_UPDATE = [VMStatus.CREATING, VMStatus.MIGRATE, VMStatus.COLD_MIGRATE, VMStatus.CLONEING,
                              VMStatus.CREATE_ERROR, VMStatus.CLONE_CREATE_ERROR, VMStatus.UNDER_CLONE,
                              VMStatus.CONFIGURE_ING, VMStatus.CLONE_ERROR]
# host状态数据收集
HOST_COLLECT_INTERVAL = 3  # 收集时间间隔（秒）
HOST_COLLECT_NUMS = 500  # 一次任务的线程数
HOST_COLLECT_WORK_INTERVAL = 5  # 任务时间间隔（秒）
# host性能数据收集
HOST_PERFORMANCE_COLLECT_INTERVAL = 120  # 收集时间间隔（秒）
HOST_PERFORMANCE_COLLECT_NUMS = 20  # 一次任务的线程数
HOST_PERFORMANCE_COLLECT_WORK_INTERVAL = 15  # 任务时间间隔（秒）
# **********instance和host状态数据收集  end************

# **********工单状态数据收集与更新  start*************
REQUEST_STATUS_COLLECT_INTERVAL = 10  # 收集时间间隔（秒）
REQUEST_STATUS_COLLECT_NUMS = 100  # 一次任务的线程数
REQUEST_STATUS_COLLECT_WORK_INTERVAL = 15  # 任务时间间隔（秒）
# **********工单状态数据收集与更新  end*************


# **********host性能数据  start************
# host性能指标数
HOST_PERFORMANCE_NUMS = 15
# host监控项
HOST_MONITOR_ATTR = ['current_cpu_used', 'current_mem_used']
# **********host性能数据  end************

# **********VNC CONSOLE配置项************
WS_PORT = 6080
WS_HOST = '0.0.0.0'
WS_CERT = None
WS_KEY = None
# **********VNC CONSOLE配置项************

# **********物理机初始化程序路径********************************************
DIR_DEFAULT = os.path.dirname(os.path.abspath(__file__))[0:-7]
HOST_STANDARD_DIR = DIR_DEFAULT + '/deploy/host_std_info'
HOST_AGENT_PACKAGE_COPY_DIR = DIR_DEFAULT + '/deploy/pip_hostagent_package'
HOST_AGENT_PACKAGE_INSTALL_SHELL_DIR = DIR_DEFAULT + '/deploy'
# **********物理机初始化程序路径********************************************


# **********虚拟机xml文件在物理机上备份目录*******************
DIR_INSTANCE_XML_BACKUP = '/app/instance_xml_bak'

CLOUD_VERSION = '1.0'
AUDIT_LOG_PATH = './api_web_audit.log'

# ********* tracker存放种子文件目录 ***************************
TORRENT_DIR = '/app/clone_torrent'

# ********* clone传输端口 ***************************
CLONE_TORR_PORT= 8090

# ********* yum源地址 ***************************
CS_YUM_SERVER = 'yum 源的地址'  # 10.20.10.20
PRD_YUM_SERVER = 'yum  源地址'  # 10.20.10.20
PRD_DC_TYPE = ['4', '5', '6', '8']

# ********* 镜像管理 ***************************
IMAGE_OS_TYPE = ['linux', 'windows']
#IMAGE_OS_VER = ['6.6', '6.8', '7.2']
IMAGE_OS_VER = [
{
    "OS_TYPE": "linux",
    "OS_VER": ['6.6', '6.8', '7.2']
},
{
    "OS_TYPE": "windows",
    "OS_VER": ['2008', '2012']
}
]

# ********* HOST OS版本 ************************
HOST_OS_VER = '7.3'

# ********* ping超时时间 **********************
PING_TIMEOUT = 2
