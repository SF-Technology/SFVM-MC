# coding=utf8
'''
    物理机服务
'''
# __author__ =  ""
from lib.shell import ansibleCmdV2
from model import host, const_define
from config.default import HOST_STANDARD_DIR, HOST_LIBVIRT_USER, HOST_LIBVIRT_PWD, HOST_PERFORMANCE_COLLECT_URL, \
    HOST_AGENT_PACKAGE_COPY_DIR, HOST_AGENT_PACKAGE_INSTALL_SHELL_DIR
from lib.serveroperate import operate
import libvirt
from libvirt import libvirtError
import logging
from helper.encrypt_helper import decrypt
from config.default import ANSIABLE_REMOTE_USER,ANSIABLE_REMOTE_SU_USER,\
    ANSIABLE_REMOTE_PWD,ANSIABLE_REMOTE_SU_PWD,ROOT_PWD,CS_YUM_SERVER,PRD_YUM_SERVER,PRD_DC_TYPE, HOST_OS_VER
from lib.vrtManager import instanceManager as vmManager
from service.s_ip import segment_service as seg_s
from service.s_hostpool import hostpool_service as hp_s
from service.s_datacenter import datacenter_service as da_s
import time
from model.const_define import ActionStatus
import os
from helper.log_helper import add_timed_rotating_file_handler
from lib.shell.ansibleCmdV2 import check_host_bond_connection, host_std_checklist, send_file_to_host, \
    run_change_host_bridge_shell, host_run_shell, ansible_run_shell
from lib.shell.ansiblePlaybookV2 import run_standard_host


class HostService:

    def __init__(self):
        self.host_db = host.Host(db_flag='kvm', table_name='host')

    def query_data(self, **params):
        return self.host_db.simple_query(**params)

    def add_host_info(self, insert_data):
        return self.host_db.insert(insert_data)

    def get_host_info(self, host_id):
        return self.host_db.get_one("id", host_id)

    def get_host_info_by_sn(self, sn):
        params = {
            'WHERE_AND': {
                "=": {
                    'sn': sn,
                    'isdeleted': '0',
                }
            },
        }
        total_nums, data = self.host_db.simple_query(**params)
        if total_nums > 0:
            return data[0]
        else:
            return None

    def get_host_info_by_manage_ip(self, manage_ip):
        params = {
            'WHERE_AND': {
                "=": {
                    'manage_ip': manage_ip,
                    'isdeleted': '0',
                }
            },
        }
        total_nums, data = self.host_db.simple_query(**params)
        if total_nums <= 0:
            return None
        return data[0]

    def get_host_info_by_hostip(self, host_ip):
        params = {
            'WHERE_AND': {
                "=": {
                    'ipaddress': host_ip,
                    'isdeleted': '0',
                }
            },
        }
        total_nums, data = self.host_db.simple_query(**params)
        if total_nums <= 0:
            return None
        return data[0]

    def get_host_info_by_ipadd(self,ipaddress):
        return self.host_db.get_one("ipaddress", ipaddress)


    def update_host_info(self, update_data, where_data):
        return self.host_db.update(update_data, where_data)


    def get_hosts_nums_of_hostpool(self, hostpool_id):
        '''
            获取指定集群下的host数量
        :param hostpool_id:
        :return:
        '''
        params = {
            'WHERE_AND': {
                "=": {
                    'hostpool_id': hostpool_id,
                    'isdeleted': '0',
                }
            },
        }
        total_nums, data = self.host_db.simple_query(**params)
        return total_nums

    def get_hosts_of_hostpool(self, hostpool_id):
        '''
            获取指定集群下的所有host
        :param hostpool_id:
        :return:
        '''
        params = {
            'WHERE_AND': {
                "=": {
                    'hostpool_id': hostpool_id,
                    'isdeleted': '0',
                }
            },
        }
        return self.host_db.simple_query(**params)

    def get_hosts_clone_status(self, host_ip):
        '''
            获取指定集群下的所有host
        :param hostpool_id:
        :return:
        '''
        params = {
            'WHERE_AND': {
                "=": {
                    'ipaddress': host_ip,
                    'isdeleted': '0',
                }
            },
        }
        total_num,data =  self.host_db.simple_query(**params)
        if total_num < 0:
            return False
        else:
            if data[0]['host_clone_status'] == '0':
                return True
            else:
                return False

    def get_available_hosts_of_hostpool(self, hostpool_id):
        '''
            获取指定集群下业务状态正常的所有host
        :param hostpool_id:
        :return:
        '''
        params = {
            'WHERE_AND': {
                "=": {
                    'hostpool_id': hostpool_id,
                    'typestatus': '0',
                    'isdeleted': '0',
                }
            },
        }
        return self.host_db.simple_query(**params)

    def delete_host(self, where_data):
        return self.host_db.delete(where_data)


def get_host_nums_in_dcs(dc_datas):
    '''
        获取批量机房下总host数量
    :param dc_datas:
    :return:
    '''
    all_host_nums = 0
    for _dc in dc_datas:
        _hosts = host.get_hosts_by_datacenter_id(_dc['id'])
        all_host_nums += len(_hosts)
    return all_host_nums

def get_hosts_of_datacenter(datacenter_id):
    '''
        获取指定机房下的所有host
    :param datacenter_id:
    :return:
    '''
    return host.get_hosts_by_datacenter_id(datacenter_id)


def get_hosts_of_net_area(net_area_id):
    '''
        获取指定网络区域下的所有host
    :param net_area_id:
    :return:
    '''
    return host.get_hosts_by_net_area_id(net_area_id)


def _get_hosts_of_net_area(net_area_id):
    '''
        获取指定网络区域下的所有host
    :param net_area_id:
    :return:
    '''
    return host._get_hosts_by_net_area_id(net_area_id)


def get_level_info(host_id):
    '''
        获取host以上的所有层级信息
    :param host_id:
    :return:
    '''
    return host.get_level_info(host_id)


def get_vm_assign_mem_of_host(host_id):
    '''
        获取host下所有vm分配的总内存量
    :param host_id:
    :return:
    '''
    assign_info = host.get_vm_assign_mem_of_host(host_id)
    if assign_info['assign_mem']:
        return assign_info['assign_mem']
    else:
        return 0


def get_vm_assign_vcpu_of_host(host_id):
    '''
        获取host下所有vm分配的总cpu个数
    :param host_id:
    :return:
    '''
    assign_info = host.get_vm_assign_vcpu_of_host(host_id)
    if assign_info['assign_vcpu']:
        return assign_info['assign_vcpu']
    else:
        return 0


def get_vm_assign_disk_of_host(host_id):
    '''
        获取host下所有vm分配的总磁盘大小
    :param host_id:
    :return:
    '''
    assign_info = host.get_vm_assign_disk_of_host(host_id)
    if assign_info['assign_disk']:
        return assign_info['assign_disk']
    else:
        return 0


def get_instances_of_host(host_id):
    '''
        获取host下所有instances
    :param host_id:
    :return:
    '''
    return host.get_instances_of_host(host_id)


def get_instances_of_host_without_clone(host_id):
    '''
        获取host下非克隆备份instances
    :param host_id:
    :return:
    '''
    instance_data_list = []
    instance_data = host.get_instances_of_host(host_id)
    if instance_data:
        for _instance in instance_data:
            if '-clone' not in _instance['name']:
                instance_data_list.append(_instance)
    return instance_data_list


def get_host_net_area_id(host_id):
    hostid =  host.get_host_net_area_id(host_id)
    return hostid


def get_hosts_by_fuzzy_hostpool_name(hostpool_name):
    '''
        根据hostpool_name模糊查询对应的hosts
    :param hostpool_name:
    :return:
    '''
    return host.get_hosts_by_fuzzy_hostpool_name(hostpool_name)


def pre_allocate_host_resource(host_id, cpu, memory, disk):
    '''
        创建VM时预分配host资源
    :param host_id:
    :param cpu:
    :param memory:
    :param disk:
    :return:
    '''
    return host.pre_allocate_host_resource(host_id, int(cpu), int(memory), int(disk))


def standard_host(manage_ip,hostpool_id):
    '''
        物理机标准化操作
    :param manage_ip:
    :return:
    '''
    url = HOST_STANDARD_DIR + '/host_std.yaml'

    host_list = [manage_ip]

    # 获取新增host所在网络区域的vlanlist
    hostpool_info = hp_s.HostPoolService().get_hostpool_info(hostpool_id)
    net_area_id = hostpool_info['net_area_id']
    vlan_res, vlan_data = seg_s.SegmentService().get_area_segment_list(net_area_id)
    if not vlan_res:
        return False, vlan_data
    else:
        host_vlan_filter_dict = {}
        host_vlan_list = vlan_data
        # host_vlan_list_dupl = sorted(set(host_vlan_list), key=host_vlan_list.index)
        # 根据br_bond对网段进行分类
        for _host_vlan in host_vlan_list:
            if _host_vlan['host_bridge_name'] in host_vlan_filter_dict.keys():
                host_vlan_filter_dict[_host_vlan['host_bridge_name']].append(_host_vlan['vlan'])
            else:
                host_vlan_filter_dict[_host_vlan['host_bridge_name']] = [_host_vlan['vlan']]
        # host_vlan_list_dupl = sorted(set(host_vlan_list), key=lambda i: i["host_bridge_name"])

    # 循环调用playbook为不同bond新建网桥，每次调用完成后需要time.sleep(5)
    br_bond_create_shell_url = HOST_STANDARD_DIR + '/host_std_br_bond_create.yaml'
    for _bond_name, _vlan_list in host_vlan_filter_dict.items():
        host_dict = {
                     "srcdir": HOST_STANDARD_DIR,
                     "host_vlan_list": _vlan_list,
                     "br_bond": _bond_name.split('_')[1]
                     }

        run_result, run_message = run_standard_host(br_bond_create_shell_url, manage_ip, host_dict)
        if not run_result:
            logging.info('物理机%s初始化新增内网vlan执行playbook失败，原因:%s' % (manage_ip, run_message))

            return False, run_message

        time.sleep(2)

        time.sleep(2)

    # 构造host网桥检测入参内容
    host_test_bridge_list = []
    for vlan_info in vlan_data :
        bridge_name = vlan_info['host_bridge_name'] + '.' + vlan_info['vlan']
        gateway_ip = vlan_info['gateway']
        vlan = vlan_info['vlan']
        host_test_bridge = {
            "bridge": bridge_name,
            "gateway": gateway_ip,
            "vlan": vlan
        }
        host_test_bridge_list.append(host_test_bridge)

    # # 循环调用playbook测试HOST上对指定网桥的访问是否正常
    # bridge_test_shell_url = HOST_STANDARD_DIR + '/host_std_test_vlan.yaml'
    # host_dict = {
    #     "test_bridge_info": host_test_bridge_list
    # }
    res, message = check_vlan_connection(manage_ip, host_test_bridge_list)
    if not res:
        return False, message

    logging.info('start to do host std playbook')
    # 获取host所在网络区域的yum源地址
    datacenter_id = da_s.DataCenterService().get_dctype_by_net_area_id(net_area_id)
    if str(datacenter_id) in PRD_DC_TYPE:
        yum_server_addr = PRD_YUM_SERVER
    else:
        yum_server_addr = CS_YUM_SERVER

    # #构造vlan_list字符串传递给playbook作为入参
    # vlan_list_str = " ".join(host_vlan_list)
    # vlan_str = "\'" + vlan_list_str + "\'"
    # print vlan_str
    playbook_url = HOST_STANDARD_DIR + '/host_std.yaml'
    host_dict = {
        "srcdir": HOST_STANDARD_DIR,
        "agentdir": HOST_AGENT_PACKAGE_COPY_DIR,
        "agentshelldir": HOST_AGENT_PACKAGE_INSTALL_SHELL_DIR,
        "libvirt_user_pwd": decrypt(HOST_LIBVIRT_PWD),
        "root_pwd": decrypt(ROOT_PWD),
        "yum_server_ip": yum_server_addr
    }

    run_result, run_message = run_standard_host(playbook_url, manage_ip, host_dict)

    if not run_result:
        return False, run_message

    logging.info('物理机%s初始化playbook执行成功' % manage_ip)

    # 创建池
    pool_ret = _create_storage_pool(manage_ip)
    if not pool_ret:
        logging.info('host manage ip %s create pool fail when standard host', manage_ip)
        msg = "创建存储池失败"
        return False,msg

    # 创建clone池
    pool_ret = _create_clone_pool(manage_ip)
    if not pool_ret:
        logging.info('host manage ip %s create clone pool fail when standard host', manage_ip)
        msg = "创建clone存储池失败"
        return False, msg

    # host 运行checklist
    ret_checklist, msg_checklist = host_std_checklist(manage_ip)
    if not ret_checklist:
        msg = msg_checklist
        logging.info(msg)
        return False, msg


    msg = "标准化主机成功"
    return True,msg




def _pool_create(remote_ip):
    '''
        创建池
    :param remote_ip:
    :return:
    '''
    xml = """
        <pool type='dir'>
           <name>image</name>
           <capacity unit='bytes'>0</capacity>
           <allocation unit='bytes'>0</allocation>
           <available unit='bytes'>0</available>
           <source>
           </source>
           <target>
             <path>/app/image</path>
           </target>
        </pool>
    """
    try:
        conn = libvirt.open('qemu+tcp://'+ HOST_LIBVIRT_USER +'@'+remote_ip+'/system')
        conn.storagePoolDefineXML(xml, 0)
        stg = conn.storagePoolLookupByName('image')
        stg.create(0)
        stg.setAutostart(1)
    except libvirtError, e:
        text1 = e.args[0]
        if "already" in text1:
            return True
        else:
            return False
    return True


def operate_host_flag(manage_ip, flag, sn):
    '''
        物理机远程操作
    :param manage_ip:
    :param flag:
    :param sn:
    :return:
    '''
    if flag == const_define.HostOperate.START:
        return operate.server_start(manage_ip, sn)
    elif flag == const_define.HostOperate.STOP:
        return operate.server_stop(manage_ip, sn)
    elif flag == const_define.HostOperate.SOFT_STOP:
        return operate.server_soft_stop(manage_ip, sn)
    elif flag == const_define.HostOperate.RESET:
        return operate.server_reset(manage_ip, sn)
    elif flag == const_define.HostOperate.SOFT_RESET:
        return operate.server_soft_reset(manage_ip, sn)


def _pool_delete(remote_ip):
    command1 = 'virsh pool-destroy image'
    command2 = 'virsh pool-undefine image'
    r_user = ANSIABLE_REMOTE_USER
    r_pass = decrypt(ANSIABLE_REMOTE_PWD)
    b_user = ANSIABLE_REMOTE_SU_USER
    b_pass = decrypt(ANSIABLE_REMOTE_SU_PWD)
    host = remote_ip
    c1 = ansible_run_shell(host,command1)
    if c1['contacted'] == {}:
       return False
    else :
        c2 = ansible_run_shell(host,command2)
        if c2['contacted'] == {}:
           return False
        else :
            return True


# 创建存储池
def _create_storage_pool(host_ip):
    connect_storages = vmManager.libvirt_get_connect(host_ip, conn_type='storages')
    if not connect_storages:
        msg = "libvirt connect error"
        return False,msg
    else:
        pool_status, pool_name = vmManager.libvirt_create_image_pool(connect_storages,'image')
        if not pool_status:
            if "already" in pool_name:
                msg = "pool image already exist"
                return True,msg
            else:
                msg = "pool image create failed"
                return False,msg
        else:
            msg = "pool image create success"
            return True,msg

# 创建clone存储池
def _create_clone_pool(host_ip):
    connect_storages = vmManager.libvirt_get_connect(host_ip, conn_type='storages')
    if not connect_storages:
        msg = "libvirt connect error"
        return False,msg
    else:
        pool_status, pool_name = vmManager.libvirt_create_clone_pool(connect_storages,'clone')
        if not pool_status:
            if "already" in pool_name:
                msg = "pool clone already exist"
                return True,msg
            else:
                msg = "pool clone create failed"
                return False,msg
        else:
            msg = "pool clone create success"
            return True,msg


# 检查bond0连通性
def check_bond_connection(host_ip, vlan_id):
    command1 = '/usr/sbin/ip a|grep br_bond0.' + vlan_id
    r_user = ANSIABLE_REMOTE_USER
    r_pass = decrypt(ANSIABLE_REMOTE_PWD)
    b_user = ANSIABLE_REMOTE_SU_USER
    b_pass = decrypt(ANSIABLE_REMOTE_SU_PWD)
    host = host_ip
    c1 = ansible_run_shell(host, command1)
    if 'contacted' not in c1:
        message = '连接目标HOST %s 失败' % (host_ip)
        logging.error(message)
        return False, False, message
    elif c1['contacted'] == {}:
        message = '连接目标kvm host失败'
        logging.error(message)
        return False, False, message
    elif 'failed' in c1['contacted'][host_ip]:
        message = '获取HOST %s 网桥信息出错' % (host_ip)
        logging.error(message)
        return False, False, message
    elif c1['contacted'][host_ip]['stderr']:
        message = '获取HOST %s 网桥信息出错' % (host_ip)
        logging.error(message)
        return False, False, message
    elif c1['contacted'][host_ip]['stdout'] == '':
        message = 'HOST %s 上主网所在网桥未创建' % (host_ip)
        logging.info(message)
        return False, True, message
    else:
        message = '获取HOST上主网网桥成功'
        logging.info(message)
        return True, True, message


# 检查HOST OS版本
def check_host_os_ver(host_ip):
    os_ver = HOST_OS_VER
    command1 = 'cat /etc/redhat-release |grep %s' % os_ver
    r_user = ANSIABLE_REMOTE_USER
    r_pass = decrypt(ANSIABLE_REMOTE_PWD)
    b_user = ANSIABLE_REMOTE_SU_USER
    b_pass = decrypt(ANSIABLE_REMOTE_SU_PWD)
    host = host_ip
    c1 = ansible_run_shell(host, command1)
    if 'contacted' not in c1:
        message = '连接目标HOST %s 失败' % host_ip
        logging.error(message)
        return False, message
    elif c1['contacted'] == {}:
        message = '连接目标kvm host失败'
        logging.error(message)
        return False, message
    elif 'failed' in c1['contacted'][host_ip]:
        message = '获取HOST %s OS版本失败' % host_ip
        logging.error(message)
        return False, message
    elif c1['contacted'][host_ip]['stderr']:
        message = '获取HOST %s OS版本失败' % host_ip
        logging.error(message)
        return False, message
    elif c1['contacted'][host_ip]['stdout'] == '':
        message = 'HOST %s OS版本异常,非指定的 %s 版本,请检查' % (host_ip, os_ver)
        logging.info(message)
        return False, message
    else:
        message = 'HOST %s OS版本检查通过' % host_ip
        logging.info(message)
        return True, message




# 下发host网桥改名脚本
def send_check_vlan(host_ip):

    # send_wget_sh_comm = 'scr=' + check_dir +'/deploy/wgetdir/sync_task_' +str(task_id) + ' dest=/root'
    chg_bridge_command = {
        'src': HOST_STANDARD_DIR + '/check_vlan_connection.py',
        'dest': '/root'
    }
    test_vlan = ansibleCmdV2.ansible_run_copy(host_ip, chg_bridge_command['src'],chg_bridge_command['dest'])
    print test_vlan
    if test_vlan['contacted'] == {}:
        message = '连接目标host失败'
        return False, message
    elif 'failed' in test_vlan['contacted'][host_ip]:
        message = '下发vlan检测脚本到HOST %s失败'
        return False, message
    else:
        message = '下发vlan检测脚本到HOST %s成功'
        return True, message




# HOST检查vlan连通性
def check_vlan_connection(host_ip, test_vlan_info_list):
    test_vlan_info = '"'+ str(test_vlan_info_list) + '"'
    command = '/usr/bin/python /root/check_vlan_connection.py %s' % test_vlan_info
    ret = ansibleCmdV2.ansible_run_shell(host_ip,command)
    if 'contacted' not in ret:
        message = '连接目标HOST %s 失败' % host_ip
        logging.error(message)
        return False, message
    elif ret['contacted'] == {}:
        message = '连接目标kvm host %s失败' % host_ip
        logging.error(message)
        return False, message
    elif 'failed' in ret['contacted'][host_ip]:
        message = '连接目标kvm host %s失败' % host_ip
        logging.error(message)
        return False, message
    elif ret['contacted'][host_ip]['stderr']:
        message = 'ansible执行命令失败，物理机ip：%s' % host_ip
        logging.error(message)
        return False, message
    # elif ret['contacted'][host_ip]['rc'] != 0:
    #     vlan_check_error = ret['contacted'][host_ip]['stdout'].encode('raw_unicode_escape').decode('utf8')
    #     message = '目标kvm host %s到以下vlan %s 不通，请检查' % (host_ip, vlan_check_error)
    #     logging.info(message)
    #     return False, message
    else:
        message = '目标KVM HOST %s vlan检查通过' % host_ip
        return True, message


# # 日志格式化
# def _init_log(service_name):
#     log_basic_path = os.path.dirname(os.path.abspath(__file__))[0:-14]
#     log_name = log_basic_path + 'log/' + str(service_name) + '.log'
#     add_timed_rotating_file_handler(log_name, logLevel='INFO')