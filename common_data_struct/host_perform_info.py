# coding:utf-8
'''
    物理机性能信息
'''


import base_define


class HostPerformanceInfo(base_define.Base):

    def __init__(self):
        self.host_ip = None       # physical server host ipaddress
        self.host_name = None     # physical server  hostname
        # self.host_uuid = None     # physical server uuid
        self.collect_time = None  # performance collect time
        self.metric_key = None    # specifiy key(cpu.sys; cpu.user; cpu.free; mem....)
        self.data_value = None    # spcifiy  key value

    def set_data(self, datadict):
        self.host_ip = datadict.get('host_ip', None)
        self.host_name = datadict.get('host_name', None)
        # self.host_uuid = datadict.get('host_uuid',None)
        self.collect_time = datadict.get('collect_time', None)
        self.metric_key = datadict.get('metric_key', None)
        self.data_value = datadict.get('data_value', None)

    def __str__(self):
        return "<" + str(self.host_ip) + "," + str(self.host_name) + ","\
               + str(self.collect_time) + ","\
                + str(self.metric_key) + "," + str(self.data_value) + ">"
