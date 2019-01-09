# coding=utf8
'''
    集群管理-导出文件
'''


# from flask.ext.login import login_required
from flask_login import LoginManager,login_user,login_required,current_user
from flask import request, make_response
from model import hostpool
from service.s_user.user_service import get_user
from pyexcel_xls import save_data
from collections import OrderedDict
import StringIO
from model.const_define import DataCenterTypeMsg
from service.s_host import host_service as host_s
from service.s_dashboard.dashboard_service import get_cpu_mem_used
from service.s_net_area.net_area import NetAreaService as net_area_s
from service.s_ip.segment_service import SegmentService as ip_segment_s
from service.s_ip import ip_service


@login_required
def export_hostpool_excel():
    params = {
        'page_size': request.values.get('page_size'),
        'page_no': request.values.get('page_no'),
    }

    total_nums, data = hostpool.user_hostpool_list(get_user()['user_id'], **params)

    # 生成excel
    excel_data = OrderedDict()
    sheet_1 = []
    # 标题行
    row_title_data = [u"集群名", u"网络区域", u"所在机房", u"机房类型", u"Host数量", u"Host数量下限", u"vm数量",
                      u"CPU数(核)", u"CPU使用率(%)", u"MEM总量(MB)", u"MEM分配率(%)", u"MEM使用率(%)",
                      u"可创建虚拟机数量(个)", u"可用ip数量(个)"]
    sheet_1.append(row_title_data)

    for i in data:
        # 获取该集群下所有host的cpu、mem使用情况
        _all_host_num, _all_host_data = host_s.HostService().get_hosts_of_hostpool(i['hostpool_id'])
        if _all_host_num > 0:
            _cpu_mem_used = get_cpu_mem_used(_all_host_data, i['hostpool_id'])
            _cpu_nums = _cpu_mem_used['cpu_all']
            _cpu_used_per = _cpu_mem_used['cpu_used_per']
            _mem_nums = _cpu_mem_used['mem_all']
            _mem_assign_per = _cpu_mem_used['assign_mem_per']
            _mem_used_per = _cpu_mem_used['mem_used_per']
            _available_create_vm_nums = _cpu_mem_used['available_create_vm_num']
        else:
            _cpu_nums = 0
            _cpu_used_per = 0
            _mem_nums = 0
            _mem_assign_per = 0
            _mem_used_per = 0
            _available_create_vm_nums = 0

        # 获取集群可用ip数量
        _available_ip_nums = __all_ip_available_num(i['datacenter_id'], i['net_area_id'])

        _row_data = [
            i['hostpool_name'],
            i['net_area_name'],
            i['datacenter_name'],
            unicode(DataCenterTypeMsg.MSG_DICT.get(int(i['dc_type']), '')),
            host_s.HostService().get_hosts_nums_of_hostpool(i['hostpool_id']),
            i['least_host_num'],
            i['instances_nums'],
            _cpu_nums,
            _cpu_used_per,
            _mem_nums,
            _mem_assign_per,
            _mem_used_per,
            _available_create_vm_nums,
            _available_ip_nums,
        ]
        sheet_1.append(_row_data)

    excel_data.update({u"hostpools": sheet_1})

    io = StringIO.StringIO()
    save_data(io, excel_data)

    response = make_response(io.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=集群信息.xls"
    return response


def __all_ip_available_num(dc_id, net_area_id=None):
    '''
        对于一个网络区域最大可使用ip个数以所有网段中ip个数最多的那个为准
    :param dc_id:
    :param net_area_id:
    :return:
    '''
    dc_ip_num = 0
    if not net_area_id:
        net_area_num, net_area_datas = net_area_s().get_net_area_datas_in_dc(dc_id)
        if net_area_num <= 0:
            return 0
        for one_net_area_data in net_area_datas:
            ip_num_list = []
            ip_segment_num, ip_segment_datas = ip_segment_s().get_segment_datas_in_net_area(one_net_area_data['id'])
            if ip_segment_num <= 0:
                continue
            for one_ip_segment in ip_segment_datas:
                ip_ret, ip_num = ip_service.get_available_ip_by_segment_id(one_ip_segment['id'])
                if ip_ret:
                    ip_num_list.append(ip_num)
            if len(ip_num_list) > 0:
                net_area_ip_num = max(ip_num_list)
                dc_ip_num += net_area_ip_num
    else:
        ip_num_list = []
        ip_segment_num, ip_segment_datas = ip_segment_s().get_segment_datas_in_net_area(net_area_id)
        if ip_segment_num <= 0:
            return 0
        for one_ip_segment in ip_segment_datas:
            ip_ret, ip_num = ip_service.get_available_ip_by_segment_id(one_ip_segment['id'])
            if ip_ret:
                ip_num_list.append(ip_num)
        if len(ip_num_list) > 0:
            net_area_ip_num = max(ip_num_list)
            dc_ip_num += net_area_ip_num
    return dc_ip_num
