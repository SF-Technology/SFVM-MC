# coding=utf8
# Copyright (C) 2013 Webvirtmgr.
#
import time
import os.path
try:
    from libvirt import libvirtError, VIR_DOMAIN_XML_SECURE, VIR_MIGRATE_LIVE, \
        VIR_MIGRATE_UNSAFE, VIR_DOMAIN_UNDEFINE_SNAPSHOTS_METADATA, VIR_DOMAIN_AFFECT_LIVE, VIR_DOMAIN_AFFECT_CONFIG, \
        VIR_MIGRATE_NON_SHARED_DISK, VIR_MIGRATE_NON_SHARED_INC, VIR_MIGRATE_TUNNELLED, VIR_MIGRATE_PEER2PEER, VIR_MIGRATE_PERSIST_DEST, VIR_MIGRATE_OFFLINE, VIR_DOMAIN_AFFECT_LIVE, VIR_DOMAIN_AFFECT_CONFIG, \
        VIR_DOMAIN_SNAPSHOT_CREATE_NO_METADATA, VIR_DOMAIN_SNAPSHOT_CREATE_DISK_ONLY, VIR_DOMAIN_SNAPSHOT_CREATE_ATOMIC, \
        VIR_DOMAIN_BLOCK_COMMIT_ACTIVE, VIR_DOMAIN_BLOCK_COMMIT_RELATIVE, VIR_DOMAIN_BLOCK_COMMIT_DELETE
except:
    from libvirt import libvirtError, VIR_DOMAIN_XML_SECURE, VIR_MIGRATE_LIVE
from . import util
from util import randomMAC
from xml.etree import ElementTree
from datetime import datetime
from connection import wvmConnect
from model.const_define import CentOS_Version
# from service.s_instance import instance_service as ins_s
from model.const_define import InstaceActions, ActionStatus
# InstaceActions, ActionStatus

########################################add 2019/09/29
# from service.s_instance import instance_action_service
# from service.s_instance import instance_service
# from service.s_instance import instance_action_service, instance_service




import libvirt_qemu
import time
import base64
import logging

QEMU_CONSOLE_TYPES =['vnc', 'spice']

class wvmInstances(wvmConnect):
    def get_instance_status(self, name):
        inst = self.get_instance(name)
        return inst.info()[0]

    def get_instance_memory(self, name):
        inst = self.get_instance(name)
        mem = util.get_xml_path(inst.XMLDesc(0), "/domain/currentMemory")
        return int(mem) / 1024

    def get_instance_vcpu(self, name):
        inst = self.get_instance(name)
        cur_vcpu = util.get_xml_path(inst.XMLDesc(0), "/domain/vcpu/@current")
        if cur_vcpu:
            vcpu = cur_vcpu
        else:
            vcpu = util.get_xml_path(inst.XMLDesc(0), "/domain/vcpu")
        return vcpu

    def get_instance_managed_save_image(self, name):
        inst = self.get_instance(name)
        return inst.hasManagedSaveImage(0)

    def get_uuid(self, name):
        inst = self.get_instance(name)
        return inst.UUIDString()

    def start(self, name):
        dom = self.get_instance(name)
        dom.create()

    def reboot(self, name):
        dom = self.get_instance(name)
        dom.reboot()

    def shutdown(self, name):
        dom = self.get_instance(name)
        dom.shutdown()

    def force_shutdown(self, name):
        dom = self.get_instance(name)
        dom.destroy()

    def managedsave(self, name):
        dom = self.get_instance(name)
        dom.managedSave(0)

    def managed_save_remove(self, name):
        dom = self.get_instance(name)
        dom.managedSaveRemove(0)

    def suspend(self, name):
        dom = self.get_instance(name)
        dom.suspend()

    def resume(self, name):
        dom = self.get_instance(name)
        dom.resume()

    def moveto(self, conn, name, live, unsafe, undefine):
        flags = 0
        if live and conn.get_status() == 1:
            flags |= VIR_MIGRATE_LIVE
        if unsafe and conn.get_status() == 1:
            flags |= VIR_MIGRATE_UNSAFE
        flags |= VIR_MIGRATE_NON_SHARED_INC
        flags |= VIR_MIGRATE_PEER2PEER
        flags |= VIR_MIGRATE_PERSIST_DEST
        flags |= VIR_MIGRATE_LIVE
        # flags |= VIR_MIGRATE_OFFLINE
        dom = conn.get_instance(name)
        """
        migrateSetMaxSpeed(self, bandwidth, flags=0) method of libvirt.virDomain instance
            The maximum bandwidth (in MiB/s) that will be used to do migration
            can be specified with the bandwidth parameter. Not all hypervisors
            will support a bandwidth cap
        """

        # 迁移速度设置
        # dom.migrateSetMaxSpeed(500, 0)
        try:
            dom.migrate(self.wvm, flags, name, None, 500)
        except libvirtError as err:
            return False, err
        if undefine:
            dom.undefine()
        return True, 'SUCCESS'

    def define_move(self, name):
        dom = self.get_instance(name)
        xml = dom.XMLDesc(VIR_DOMAIN_XML_SECURE)
        self.wvm.defineXML(xml)


class wvmInstance(wvmConnect):
    def __init__(self, host, login, passwd, conn, vname):
        wvmConnect.__init__(self, host, login, passwd, conn)
        self.instance = self.get_instance(vname)
        self.vmname = vname

    def get_status(self):
        inst = self.get_instance(self.vmname)
        return inst.info()[0]

    def cancel_move_to(self):
        return self.instance.abortJob()

    def get_info(self):
        inst = self.get_instance(self.vmname)
        return  inst.info

    def start(self):
        self.instance.create()

    def ip_inject(self,vmname, vmip, gateway, mask, dns1, dns2, ostype, cloudarea):
        if ostype == 'Linux':
            time.sleep(20)
            command = 'sh /root/kvmprep/ipconfigure.sh ' + vmip + ' ' + mask + ' ' + gateway + ' ' + vmname + ' ' + cloudarea
        elif ostype == 'Windows':
            time.sleep(100)
            command = 'c:\\\kvmprep\\\ipconfigure.bat '+ vmip + ' ' + mask + ' ' + gateway + ' ' + dns1 + ' ' + dns2
        else:
            time.sleep(20)
            command = 'sh /root/kvmprep/ipconfigure.sh ' + vmip + ' ' + mask + ' ' + gateway + ' ' + vmname + ' ' + cloudarea
        libvirt_qemu.qemuAgentCommand(self.instance, '{"execute":"exe-cmd","arguments":{"cmd":"%s"}}' % command, 200, 0)

    def esx_ip_inject(self,vmname, vmip, gateway, mask, dns1, dns2, ostype, cloudarea):

        if ostype == 'Linux':
            time.sleep(20)
            command = 'sh /root/kvmprep/ipconfigure.sh ' + vmip + ' ' + mask + ' ' + gateway + ' ' + vmname + ' ' + cloudarea
        elif ostype == 'Windows':
            time.sleep(100)
            command = 'c:\\\kvmprep\\\ipconfigure.bat ' + vmip + ' ' + mask + ' ' + gateway + ' ' + dns1 + ' ' + dns2
        else:
            time.sleep(20)
            command = 'sh /root/kvmprep/ipconfigure.sh ' + vmip + ' ' + mask + ' ' + gateway + ' ' + vmname + ' ' + cloudarea
        libvirt_qemu.qemuAgentCommand(self.instance, '{"execute":"exe-cmd","arguments":{"cmd":"%s"}}' % command, 200, 0)

    def win_disk_online(self):

        time.sleep(10)
        command = "diskpart \\/s c:\\\kvmprep\\\diskonline.txt"
        libvirt_qemu.qemuAgentCommand(self.instance, '{"execute":"exe-cmd","arguments":{"cmd":"%s"}}' % command, 200, 0)

    def startwcreate(self, hostname, env, ip, gateway, mask, dns1, dns2, user_passwd, image_name, access, stimeout, ostype):

        if ostype == 'linux':
            command = '/bin/bash /root/init.sh ' + env + ' ' + gateway + ' ' + hostname + ' ' + ip + ' ' + mask + ' ' + dns1 + ' ' + dns2 + ' ' + access + ' '
            time.sleep(10)
        elif ostype == 'windows':
            if image_name == 'win2008r2_en':
                time.sleep(300)
            else:
                time.sleep(200)
            command = 'c:\\\kvmprep\\\windowsprep\\\windowsprep.bat ' + env + ' ' + gateway + ' ' + hostname + ' ' + ip + ' ' + mask + ' ' + dns1 + ' ' + dns2 + ' ' + access + ' ' + '2' + ' '
        else:
            command = '/bin/bash /root/init.sh ' + env + ' ' + gateway + ' ' + hostname + ' ' + ip + ' ' + mask + ' ' + dns1 + ' ' + dns2 + ' ' + access + ' ' + '2' + ' '

        libvirt_qemu.qemuAgentCommand(self.instance, '{"execute":"exe-cmd","arguments":{"cmd":"%s"}}' % command, 600, 0)
        if user_passwd:
            if ostype == 'linux':
                reset_passwd_command = "echo '%s' | passwd --stdin root" % user_passwd
                libvirt_qemu.qemuAgentCommand(self.instance, '{"execute":"exe-cmd","arguments":{"cmd":"%s"}}' % reset_passwd_command, 600, 0)
            elif ostype == 'windows':
                reset_passwd_command = "net user winsvruser %s" % user_passwd
                libvirt_qemu.qemuAgentCommand(self.instance,
                                              '{"execute":"exe-cmd","arguments":{"cmd":"%s"}}' % reset_passwd_command,
                                              600, 0)

    def spec_inject(self, injectdata, ostype):
        if ostype == 'linux':
            command = injectdata
            time.sleep(10)
        elif ostype == 'windows':
            return 0
        else:
            command = injectdata
        libvirt_qemu.qemuAgentCommand(self.instance, '{"execute":"exe-cmd","arguments":{"cmd":"%s"}}' % command,
                                      600, 0)

    def image_inject(self, injectdata):
        command = injectdata
        libvirt_qemu.qemuAgentCommand(self.instance, '{"execute":"exe-cmd","arguments":{"cmd":"%s"}}' % command,
                                      600, 0)

    # retry inject data
    def retry_inject_data(self, hostname, env, ip, gateway, mask, dns1, dns2, user_passwd, image_name, access, stimeout, ostype):
        self.start()
        if ostype == 'linux':
            command = '/usr/bin/sh /root/init.sh ' + env + ' ' + gateway + ' ' + hostname + ' ' + ip + ' ' + mask + ' ' + dns1 + ' ' + dns2 + ' ' + access + ' '
        elif ostype == 'windows':
            if image_name == 'win2008r2_en':
                time.sleep(60)
            else:
                time.sleep(30)
            command = 'c:\\\kvmprep\\\windowsprep\\\windowsprep.bat ' + env + ' ' + gateway + ' ' + hostname + ' ' + ip + ' ' + mask + ' ' + dns1 + ' ' + dns2 + ' ' + access + ' ' + '2' + ' '
        else:
            command = '/usr/bin/sh /root/init.sh ' + env + ' ' + gateway + ' ' + hostname + ' ' + ip + ' ' + mask + ' ' + dns1 + ' ' + dns2 + ' ' + access + ' ' + '2' + ' '
        libvirt_qemu.qemuAgentCommand(self.instance, '{"execute":"exe-cmd","arguments":{"cmd":"%s"}}' % command, 600, 0)

        if user_passwd:
            if ostype == 'linux':
                reset_passwd_command = "echo '%s' | passwd --stdin root" % user_passwd
                libvirt_qemu.qemuAgentCommand(self.instance, '{"execute":"exe-cmd","arguments":{"cmd":"%s"}}' % reset_passwd_command, 600, 0)
            elif ostype == 'windows':
                reset_passwd_command = "net user winsvruser %s" % user_passwd
                libvirt_qemu.qemuAgentCommand(self.instance,
                                              '{"execute":"exe-cmd","arguments":{"cmd":"%s"}}' % reset_passwd_command,
                                              600, 0)

    def getqemuagentstuats(self):
        try:
            libvirt_qemu.qemuAgentCommand(self.instance, '{"execute":"exe-cmd","arguments":{"cmd":"hostname"}}', 600, 0)
            # libvirt_qemu.qemuMonitorCommand()
            return True
        except libvirtError as err:
            return False

    def add_instance_ip(self, net_data):
        try:
            ret = libvirt_qemu.qemuAgentCommand(self.instance,
                                                '{"execute":"exe-cmd","arguments":{"cmd":"ret=`grep -il \'%s\' /sys/class/net/eth*/address | awk -F \'/\' \'{print $5}\'`;if [ ! -n \'$ret\' ]; then  echo \'not ok\';  else  cp /etc/sysconfig/network-scripts/ifcfg-eth0 /etc/sysconfig/network-scripts/ifcfg-$ret;sed -i \'s/DEVICE.*/DEVICE=\'$ret\'/g\' /etc/sysconfig/network-scripts/ifcfg-$ret;sed -i \'s/IPADDR.*/IPADDR=%s/g\' /etc/sysconfig/network-scripts/ifcfg-$ret;sed -i \'s/NETMASK.*/NETMASK=%s/g\' /etc/sysconfig/network-scripts/ifcfg-$ret;ifup $ret;  fi"}}' % (
                                                    net_data['mac_addr'], net_data['ip_addr_new'],
                                                    net_data['netmask_new']), 60, 0)
            return True, ret
        except libvirtError as err:
            return False, err

    def change_instance_ip(self, ins_mac, ins_ip_cur, ins_ip_new):
        try:
            ret = libvirt_qemu.qemuAgentCommand(self.instance,
                                                '{"execute":"exe-cmd","arguments":{"cmd":"ret=`grep -il \'%s\' /sys/class/net/eth*/address | awk -F \'/\' \'{print $5}\'`;if [ ! -n \'$ret\' ]; then  echo \'not ok\';  else  sed -i \'s/%s/%s/g\' /etc/sysconfig/network-scripts/ifcfg-$ret;ifdown $ret;ifup $ret;sed -i \'s/%s/%s/g\' /etc/hosts;  fi"}}' % (
                                                    ins_mac, ins_ip_cur, ins_ip_new, ins_ip_cur, ins_ip_new), 60, 0)
            return True, ret
        except libvirtError as err:
            return False, err

    def change_instance_ip_netmask_gateway(self, net_data):
        try:
            ret = libvirt_qemu.qemuAgentCommand(self.instance,
                                                '{"execute":"exe-cmd","arguments":{"cmd":"ret=`grep -il \'%s\' /sys/class/net/eth*/address | awk -F \'/\' \'{print $5}\'`;if [ ! -n \'$ret\' ]; then  echo \'not ok\';  else  sed -i \'s/IPADDR.*/IPADDR=%s/g\' /etc/sysconfig/network-scripts/ifcfg-$ret;sed -i \'s/NETMASK.*/NETMASK=%s/g\' /etc/sysconfig/network-scripts/ifcfg-$ret;sed -i \'s/GATEWAY.*/GATEWAY=%s/g\' /etc/sysconfig/network;ifdown $ret;ifup $ret;sed -i \'s/%s/%s/g\' /etc/hosts;  fi"}}' % (
                                                    net_data['mac_addr'], net_data['ip_addr_new'],
                                                    net_data['netmask_new'], net_data['gateway_new'],
                                                    net_data['ip_addr'], net_data['ip_addr_new']), 60, 0)
            return True, ret
        except libvirtError as err:
            return False, err

    def resize_disk_by_qemu_agent(self, disk_dev, disk_vg_lv, disk_size):
        try:
            command = '/bin/bash /root/resize_volume.sh ' + disk_dev + ' ' + disk_vg_lv + ' ' + disk_size
            libvirt_qemu.qemuAgentCommand(self.instance, '{"execute":"exe-cmd","arguments":{"cmd":"%s"}}'
                                          % command, 600, 0)
            return True
        except libvirtError as err:
            return False

    def shutdown(self):
        self.instance.shutdown()

    def force_shutdown(self):
        self.instance.destroy()

    def managedsave(self):
        self.instance.managedSave(0)

    def managed_save_remove(self):
        self.instance.managedSaveRemove(0)

    def suspend(self):
        self.instance.suspend()

    def resume(self):
        self.instance.resume()

    def delete(self):
        try:
            self.instance.undefineFlags(VIR_DOMAIN_UNDEFINE_SNAPSHOTS_METADATA)
        except:
            self.instance.undefine()

    def _XMLDesc(self, flag):
        return self.instance.XMLDesc(flag)

    def _blockcommit(self, disk_tag, flags, snap_url):
        return self.instance.blockCommit(disk_tag, None, snap_url, 0, flags)

    def _defineXML(self, xml):
        return self.wvm.defineXML(xml)

    def get_status(self):
        return self.instance.info()[0]

    def get_autostart(self):
        return self.instance.autostart()


    def attach_disk(self, xml):
        flags = 0
        flags |= VIR_DOMAIN_AFFECT_LIVE
        flags |= VIR_DOMAIN_AFFECT_CONFIG
        return self.instance.attachDeviceFlags(xml, flags)

    def attach_disk_for_v2v(self, xml):
        flags = 0
        flags |= VIR_DOMAIN_AFFECT_LIVE
        return self.instance.attachDeviceFlags(xml, flags)


    def detach_disk(self, diskname):
        flags = 0
        flags |= VIR_DOMAIN_AFFECT_LIVE
        flags |= VIR_DOMAIN_AFFECT_CONFIG
        xml = self.get_attach_disk_device(diskname)
        if xml:
            return self.instance.detachDeviceFlags(xml, flags)
        else:
            return 1


    def resize_disk(self, diskname, disksize):
        flags = 0
        disk = self.get_resize_disk_device(diskname)
        size = int(disksize) * 1048576
        if disk:
            return self.instance.blockResize(disk, size, flags)
        else:
            return 1

    def block_info(self, path_name):
        info = self.instance.blockInfo(path_name)
        return info


    def detach_net(self, net_xml):
        flags = 0
        flags |= VIR_DOMAIN_AFFECT_LIVE
        flags |= VIR_DOMAIN_AFFECT_CONFIG
        return self.instance.detachDeviceFlags(net_xml, flags)


    def attach_net(self, net_xml):
        flags = 0
        flags |= VIR_DOMAIN_AFFECT_LIVE
        flags |= VIR_DOMAIN_AFFECT_CONFIG
        return self.instance.attachDeviceFlags(net_xml, flags)


    def update_net(self, net_xml):
        flags = 0
        flags |= VIR_DOMAIN_AFFECT_LIVE
        flags |= VIR_DOMAIN_AFFECT_CONFIG
        return self.instance.updateDeviceFlags(net_xml, flags)


    def instance_xml(self):
        return self._XMLDesc(0)

    # net up by qemu agent
    def instance_net_up(self, ins_mac):
        try:
            ret = libvirt_qemu.qemuAgentCommand(self.instance, '{"execute":"exe-cmd","arguments":{"cmd":"ret=`grep -il \'%s\' /sys/class/net/eth*/address | awk -F \'/\' \'{print $5}\'`;if [ ! -n \'$ret\' ]; then  echo \'not ok\';  else  ifup $ret;  fi"}}'
                                                % ins_mac, 600, 0)
            return True, ret
        except libvirtError as err:
            return False, err

    def set_autostart(self, flag):
        return self.instance.setAutostart(flag)

    def get_uuid(self):
        return self.instance.UUIDString()

    def get_vcpu(self):
        vcpu = util.get_xml_path(self._XMLDesc(0), "/domain/vcpu")
        return int(vcpu)

    def get_cur_vcpu(self):
        cur_vcpu = util.get_xml_path(self._XMLDesc(0), "/domain/vcpu/@current")
        if cur_vcpu:
            return int(cur_vcpu)

    def get_memory(self):
        mem = util.get_xml_path(self._XMLDesc(0), "/domain/memory")
        return int(mem) / 1024

    def get_cur_memory(self):
        mem = util.get_xml_path(self._XMLDesc(0), "/domain/currentMemory")
        return int(mem) / 1024

    def get_description(self):
        return util.get_xml_path(self._XMLDesc(0), "/domain/description")

    def get_max_memory(self):
        return self.wvm.getInfo()[1] * 1048576

    def get_max_cpus(self):
        """Get number of physical CPUs."""
        hostinfo = self.wvm.getInfo()
        pcpus = hostinfo[4] * hostinfo[5] * hostinfo[6] * hostinfo[7]
        range_pcpus = xrange(1, int(pcpus + 1))
        return range_pcpus

    def get_net_device(self):
        def get_mac_ipaddr(net, mac_host):
            def fixed(ctx):
                for net in ctx.xpathEval('/network/ip/dhcp/host'):
                    mac = net.xpathEval('@mac')[0].content
                    host = net.xpathEval('@ip')[0].content
                    if mac == mac_host:
                        return host
                return None

            return util.get_xml_path(net.XMLDesc(0), func=fixed)

        def networks(ctx):
            result = []
            for net in ctx.xpathEval('/domain/devices/interface'):
                mac_host = net.xpathEval('mac/@address')[0].content
                nic_host = net.xpathEval('source/@network|source/@bridge|source/@dev')[0].content
                try:
                    net = self.get_network(nic_host)
                    ip = get_mac_ipaddr(net, mac_host)
                except:
                    ip = None
                result.append({'mac': mac_host, 'nic': nic_host, 'ip': ip})
            return result

        return util.get_xml_path(self._XMLDesc(0), func=networks)

    def get_config_net_device(self):
        def config_networks(ctx):
            result = []
            for net in ctx.xpathEval('/domain/devices/interface'):
                mac_host = net.xpathEval('mac/@address')[0].content
                nic_host = net.xpathEval('source/@network|source/@bridge|source/@dev')[0].content
                result.append({'mac': mac_host, 'nic': nic_host})
            return result

        return util.get_xml_path(self._XMLDesc(0), func=config_networks)

    def get_delete_disk_device(self, uuid):
        def disks(ctx):
            result = []
            dev = None
            volume = None
            storage = None
            src_fl = None
            disk_format = None
            for disk in ctx.xpathEval('/domain/devices/disk'):
                device = disk.xpathEval('@device')[0].content
                if device == 'disk':
                    try:
                        dev = disk.xpathEval('target/@dev')[0].content
                        src_fl = disk.xpathEval('source/@file|source/@dev|source/@name|source/@volume')[0].content
                        disk_format = disk.xpathEval('driver/@type')[0].content
                        try:
                            stg_refresh = self.get_storage(uuid)
                            if stg_refresh.info()[0] != 0:
                                try:
                                    stg_refresh.refresh(0)
                                except:
                                    pass
                            vol = self.get_volume_by_path(src_fl)
                            volume = vol.name()
                            stg = vol.storagePoolLookupByVolume()
                            storage = stg.name()
                        except libvirtError:
                            volume = src_fl
                    except:
                        pass
                    finally:
                        result.append(
                            {'dev': dev, 'image': volume, 'storage': storage, 'path': src_fl, 'format': disk_format})
            return result

        return util.get_xml_path(self._XMLDesc(0), func=disks)

    def get_disk_device(self):
        def disks(ctx):
            result = []
            dev = None
            volume = None
            storage = None
            src_fl = None
            disk_format = None
            for disk in ctx.xpathEval('/domain/devices/disk'):
                device = disk.xpathEval('@device')[0].content
                if device == 'disk':
                    try:
                        dev = disk.xpathEval('target/@dev')[0].content
                        src_fl = disk.xpathEval('source/@file|source/@dev|source/@name|source/@volume')[0].content
                        disk_format = disk.xpathEval('driver/@type')[0].content
                        try:
                            vol = self.get_volume_by_path(src_fl)
                            volume = vol.name()
                            stg = vol.storagePoolLookupByVolume()
                            storage = stg.name()
                        except libvirtError:
                            volume = src_fl
                    except:
                        pass
                    finally:
                        result.append(
                            {'dev': dev, 'image': volume, 'storage': storage, 'path': src_fl, 'format': disk_format})
            return result

        return util.get_xml_path(self._XMLDesc(0), func=disks)

    def get_configure_disk_device(self, uuid):
        def disks(ctx):
            result = []
            dev = None
            volume = None
            storage = None
            src_fl = None
            disk_format = None
            for disk in ctx.xpathEval('/domain/devices/disk'):
                device = disk.xpathEval('@device')[0].content
                if device == 'disk':
                    try:
                        dev = disk.xpathEval('target/@dev')[0].content
                        src_fl = disk.xpathEval('source/@file|source/@dev|source/@name|source/@volume')[0].content
                        disk_format = disk.xpathEval('driver/@type')[0].content
                        try:
                            stg_refresh = self.get_storage(uuid)
                            if stg_refresh.info()[0] != 0:
                                try:
                                    stg_refresh.refresh(0)
                                except:
                                    pass
                            vol = self.get_volume_by_path(src_fl)
                            volume = vol.name()
                            stg = vol.storagePoolLookupByVolume()
                            storage = stg.name()
                        except libvirtError:
                            volume = src_fl
                    except:
                        pass
                    finally:
                        result.append(
                            {'dev': dev, 'image': volume, 'storage': storage, 'path': src_fl, 'format': disk_format})
            return result

        return util.get_xml_path(self._XMLDesc(0), func=disks)

    def get_delete_disk_device(self, uuid):
        def disks(ctx):
            result = []
            dev = None
            volume = None
            storage = None
            src_fl = None
            disk_format = None
            for disk in ctx.xpathEval('/domain/devices/disk'):
                device = disk.xpathEval('@device')[0].content
                if device == 'disk':
                    try:
                        dev = disk.xpathEval('target/@dev')[0].content
                        src_fl = disk.xpathEval('source/@file|source/@dev|source/@name|source/@volume')[0].content
                        disk_format = disk.xpathEval('driver/@type')[0].content
                        try:
                            stg_refresh = self.get_storage(uuid)
                            if stg_refresh.info()[0] != 0:
                                try:
                                    stg_refresh.refresh(0)
                                except:
                                    pass
                            vol = self.get_volume_by_path(src_fl)
                            volume = vol.name()
                            stg = vol.storagePoolLookupByVolume()
                            storage = stg.name()
                        except libvirtError:
                            volume = src_fl
                    except:
                        pass
                    finally:
                        result.append(
                            {'dev': dev, 'image': volume, 'storage': storage, 'path': src_fl, 'format': disk_format})
            return result

        return util.get_xml_path(self._XMLDesc(0), func=disks)


    def get_attach_disk_device(self, diskurl):
        def disks(ctx, diskurl1):
            for disk in ctx.xpathEval('/domain/devices/disk'):
                device = disk.xpathEval('@device')[0].content
                if device == 'disk':
                    dev = disk.xpathEval('target/@dev')[0].content
                    src_fl = disk.xpathEval('source/@file|source/@dev|source/@name|source/@volume')[0].content
                    if src_fl.split('/')[4] == diskurl1:
                        xml = """
                                    <disk type='file' device='disk'>
                                        <driver name='qemu' type='qcow2'/>
                                        <source file='/home/libvirt/image/%s'/>
                                        <target dev='%s' bus='virtio'/>
                                    </disk>""" % (diskurl1, dev)
                        return xml
        # print diskurl
        return util.get_disk_xml_path(self._XMLDesc(0), diskurl, func=disks)


    def get_resize_disk_device(self, diskurl):
        def disks(ctx, diskurl1):
            for disk in ctx.xpathEval('/domain/devices/disk'):
                device = disk.xpathEval('@device')[0].content
                if device == 'disk':
                    dev = disk.xpathEval('target/@dev')[0].content
                    src_fl = disk.xpathEval('source/@file|source/@dev|source/@name|source/@volume')[0].content
                    if src_fl.split('/')[4] == diskurl1:
                        return dev
        return util.get_disk_xml_path(self._XMLDesc(0), diskurl, func=disks)

    def get_media_device(self):
        def disks(ctx):
            result = []
            dev = None
            volume = None
            storage = None
            src_fl = None
            for media in ctx.xpathEval('/domain/devices/disk'):
                device = media.xpathEval('@device')[0].content
                if device == 'cdrom':
                    try:
                        dev = media.xpathEval('target/@dev')[0].content
                        try:
                            src_fl = media.xpathEval('source/@file')[0].content
                            vol = self.get_volume_by_path(src_fl)
                            volume = vol.name()
                            stg = vol.storagePoolLookupByVolume()
                            storage = stg.name()
                        except:
                            src_fl = None
                            volume = src_fl
                    except:
                        pass
                    finally:
                        result.append({'dev': dev, 'image': volume, 'storage': storage, 'path': src_fl})
            return result

        return util.get_xml_path(self._XMLDesc(0), func=disks)

    def mount_iso(self, dev, image):
        def attach_iso(dev, disk, vol):
            if disk.get('device') == 'cdrom':
                for elm in disk:
                    if elm.tag == 'target':
                        if elm.get('dev') == dev:
                            src_media = ElementTree.Element('source')
                            src_media.set('file', vol.path())
                            disk.insert(2, src_media)
                            return True

        storages = self.get_storages()
        for storage in storages:
            stg = self.get_storage(storage)
            if stg.info()[0] != 0:
                for img in stg.listVolumes():
                    if image == img:
                        vol = stg.storageVolLookupByName(image)
        tree = ElementTree.fromstring(self._XMLDesc(0))
        for disk in tree.findall('devices/disk'):
            if attach_iso(dev, disk, vol):
                break
        if self.get_status() == 1:
            xml = ElementTree.tostring(disk)
            self.instance.attachDevice(xml)
            xmldom = self._XMLDesc(VIR_DOMAIN_XML_SECURE)
        if self.get_status() == 5:
            xmldom = ElementTree.tostring(tree)
        self._defineXML(xmldom)

    def umount_iso(self, dev, image):
        tree = ElementTree.fromstring(self._XMLDesc(0))
        for disk in tree.findall('devices/disk'):
            if disk.get('device') == 'cdrom':
                for elm in disk:
                    if elm.tag == 'source':
                        if elm.get('file') == image:
                            src_media = elm
                    if elm.tag == 'target':
                        if elm.get('dev') == dev:
                            disk.remove(src_media)
        if self.get_status() == 1:
            xml_disk = ElementTree.tostring(disk)
            self.instance.attachDevice(xml_disk)
            xmldom = self._XMLDesc(VIR_DOMAIN_XML_SECURE)
        if self.get_status() == 5:
            xmldom = ElementTree.tostring(tree)
        self._defineXML(xmldom)

    def cpu_usage(self):
        cpu_usage = {}
        if self.get_status() == 1:
            nbcore = self.wvm.getInfo()[2]
            cpu_use_ago = self.instance.info()[4]
            time.sleep(1)
            cpu_use_now = self.instance.info()[4]
            diff_usage = cpu_use_now - cpu_use_ago
            cpu_usage['cpu'] = 100 * diff_usage / (1 * nbcore * 10 ** 9L)
        else:
            cpu_usage['cpu'] = 0
        return cpu_usage

    def disk_usage(self):
        devices = []
        dev_usage = []
        tree = ElementTree.fromstring(self._XMLDesc(0))
        for disk in tree.findall('devices/disk'):
            if disk.get('device') == 'disk':
                dev_file = None
                dev_bus = None
                network_disk = True
                for elm in disk:
                    if elm.tag == 'source':
                        if elm.get('protocol'):
                            dev_file = elm.get('protocol')
                            network_disk = True
                        if elm.get('file'):
                            dev_file = elm.get('file')
                        if elm.get('dev'):
                            dev_file = elm.get('dev')
                    if elm.tag == 'target':
                        dev_bus = elm.get('dev')
                if (dev_file and dev_bus) is not None:
                    if network_disk:
                        dev_file = dev_bus
                    devices.append([dev_file, dev_bus])
        for dev in devices:
            if self.get_status() == 1:
                rd_use_ago = self.instance.blockStats(dev[0])[1]
                wr_use_ago = self.instance.blockStats(dev[0])[3]
                time.sleep(1)
                rd_use_now = self.instance.blockStats(dev[0])[1]
                wr_use_now = self.instance.blockStats(dev[0])[3]
                rd_diff_usage = rd_use_now - rd_use_ago
                wr_diff_usage = wr_use_now - wr_use_ago
            else:
                rd_diff_usage = 0
                wr_diff_usage = 0
            dev_usage.append({'dev': dev[1], 'rd': rd_diff_usage, 'wr': wr_diff_usage})
        return dev_usage

    def net_usage(self):
        devices = []
        dev_usage = []
        tree = ElementTree.fromstring(self._XMLDesc(0))
        if self.get_status() == 1:
            tree = ElementTree.fromstring(self._XMLDesc(0))
            for target in tree.findall("devices/interface/target"):
                devices.append(target.get("dev"))
            for i, dev in enumerate(devices):
                rx_use_ago = self.instance.interfaceStats(dev)[0]
                tx_use_ago = self.instance.interfaceStats(dev)[4]
                time.sleep(1)
                rx_use_now = self.instance.interfaceStats(dev)[0]
                tx_use_now = self.instance.interfaceStats(dev)[4]
                rx_diff_usage = (rx_use_now - rx_use_ago) * 8
                tx_diff_usage = (tx_use_now - tx_use_ago) * 8
                dev_usage.append({'dev': i, 'rx': rx_diff_usage, 'tx': tx_diff_usage})
        else:
            for i, dev in enumerate(self.get_net_device()):
                dev_usage.append({'dev': i, 'rx': 0, 'tx': 0})
        return dev_usage

    def get_telnet_port(self):
        telnet_port = None
        service_port = None
        tree = ElementTree.fromstring(self._XMLDesc(0))
        for console in tree.findall('devices/console'):
            if console.get('type') == 'tcp':
                for elm in console:
                    if elm.tag == 'source':
                        if elm.get('service'):
                            service_port = elm.get('service')
                    if elm.tag == 'protocol':
                        if elm.get('type') == 'telnet':
                            if service_port is not None:
                                telnet_port = service_port
        return telnet_port

    def get_console_listen_addr(self):
        listen_addr = util.get_xml_path(self._XMLDesc(0),
                                        "/domain/devices/graphics/@listen")
        if listen_addr is None:
            listen_addr = util.get_xml_path(self._XMLDesc(0),
                                            "/domain/devices/graphics/listen/@address")
            if listen_addr is None:
                return "127.0.0.1"
        return listen_addr

    def get_console_socket(self):
        socket = util.get_xml_path(self._XMLDesc(0),
                                   "/domain/devices/graphics/@socket")
        return socket

    def get_console_type(self):
        console_type = util.get_xml_path(self._XMLDesc(0),
                                         "/domain/devices/graphics/@type")
        return console_type

    def set_console_type(self, console_type):
        current_type = self.get_console_type()
        if current_type == console_type:
            return True
        if console_type == '' or console_type not in QEMU_CONSOLE_TYPES:
            return False
        xml = self._XMLDesc(VIR_DOMAIN_XML_SECURE)
        root = ElementTree.fromstring(xml)
        try:
            graphic = root.find("devices/graphics[@type='%s']" % current_type)
        except SyntaxError:
            # Little fix for old version ElementTree
            graphic = root.find("devices/graphics")
        graphic.set('type', console_type)
        newxml = ElementTree.tostring(root)
        self._defineXML(newxml)

    def v2v_set_disk_type_virtio(self, disk_type):
        if disk_type == '' :
            return False
        xml = self._XMLDesc(VIR_DOMAIN_XML_SECURE)
        root = ElementTree.fromstring(xml)
        disklist = root.findall("devices/disk")
        disktag = ['vda','vdb','vdc','vdd','vde','vdf','vdg','vdh','vdi']
        i=0
        for disk in disklist:
            print disk.get('device')

            if disk.get('device') == 'disk':
                children = disk.getchildren()
                for child in children:
                    if child.tag == 'address':
                        disk.remove(child)
                diskbus = disk.find('target')
                diskbus.set('bus', disk_type)
                diskbus.set('dev',disktag[i])
                i= i+1
        newxml = ElementTree.tostring(root)
        self._defineXML(newxml)

    def v2v_set_nic_type(self,nic_type):
        if nic_type == '' :
            return False
        xml = self._XMLDesc(VIR_DOMAIN_XML_SECURE)
        root = ElementTree.fromstring(xml)
        disklist = root.findall("devices/interface")
        for disk in disklist:
            diskbus = disk.find('model')
            diskbus.set('type', nic_type)
        newxml = ElementTree.tostring(root)
        self._defineXML(newxml)

    def get_console_port(self, console_type=None):
        if console_type is None:
            console_type = self.get_console_type()
        port = util.get_xml_path(self._XMLDesc(0),
                                 "/domain/devices/graphics[@type='%s']/@port" % console_type)
        return port

    def get_console_websocket_port(self):
        console_type = self.get_console_type()
        websocket_port = util.get_xml_path(self._XMLDesc(0),
                                           "/domain/devices/graphics[@type='%s']/@websocket" % console_type)
        return websocket_port

    def get_console_passwd(self):
        return util.get_xml_path(self._XMLDesc(VIR_DOMAIN_XML_SECURE),
                                 "/domain/devices/graphics/@passwd")

    def set_console_passwd(self, passwd):
        xml = self._XMLDesc(VIR_DOMAIN_XML_SECURE)
        root = ElementTree.fromstring(xml)
        console_type = self.get_console_type()
        try:
            graphic = root.find("devices/graphics[@type='%s']" % console_type)
        except SyntaxError:
            # Little fix for old version ElementTree
            graphic = root.find("devices/graphics")
        if graphic is None:
            return False
        if passwd:
            graphic.set('passwd', passwd)
        else:
            try:
                graphic.attrib.pop('passwd')
            except:
                pass
        newxml = ElementTree.tostring(root)
        return self._defineXML(newxml)

    def set_console_keymap(self, keymap):
        xml = self._XMLDesc(VIR_DOMAIN_XML_SECURE)
        root = ElementTree.fromstring(xml)
        console_type = self.get_console_type()
        try:
            graphic = root.find("devices/graphics[@type='%s']" % console_type)
        except SyntaxError:
            # Little fix for old version ElementTree
            graphic = root.find("devices/graphics")
        if keymap:
            graphic.set('keymap', keymap)
        else:
            try:
                graphic.attrib.pop('keymap')
            except:
                pass
        newxml = ElementTree.tostring(root)
        self._defineXML(newxml)

    def get_console_keymap(self):
        return util.get_xml_path(self._XMLDesc(VIR_DOMAIN_XML_SECURE),
                                 "/domain/devices/graphics/@keymap") or ''

    def change_settings(self, description, cur_memory, memory, cur_vcpu, vcpu):
        """
        Function change ram and cpu on vds.
        """
        memory = int(memory) * 1024
        cur_memory = int(cur_memory) * 1024

        xml = self._XMLDesc(VIR_DOMAIN_XML_SECURE)
        tree = ElementTree.fromstring(xml)

        set_mem = tree.find('memory')
        set_mem.text = str(memory)
        set_cur_mem = tree.find('currentMemory')
        set_cur_mem.text = str(cur_memory)
        set_desc = tree.find('description')
        set_vcpu = tree.find('vcpu')
        set_vcpu.text = vcpu
        set_vcpu.set('current', cur_vcpu)

        if not set_desc:
            tree_desc = ElementTree.Element('description')
            tree_desc.text = description
            tree.insert(2, tree_desc)
        else:
            set_desc.text = description

        new_xml = ElementTree.tostring(tree)
        self._defineXML(new_xml)


    def change_vm_cpu(self, cur_vcpu, vcpu):
        """
        Function change cpu when vm stop.
        """

        xml = self._XMLDesc(VIR_DOMAIN_XML_SECURE)
        tree = ElementTree.fromstring(xml)

        set_vcpu = tree.find('vcpu')
        set_vcpu.text = vcpu
        set_vcpu.set('current', cur_vcpu)

        new_xml = ElementTree.tostring(tree)
        self._defineXML(new_xml)


    def change_vm_cpu_active(self, vcpu):
        """
        Function change cpu when vm is starting.
        """
        flags = 0
        flags |= VIR_DOMAIN_AFFECT_LIVE
        flags |= VIR_DOMAIN_AFFECT_CONFIG
        self.instance.setVcpusFlags(int(vcpu), flags)


    def change_vm_memory(self, cur_memory, memory):
        """
        Function change memory when vm is stopping.
        """
        memory = int(memory) * 1024
        cur_memory = int(cur_memory) * 1024

        xml = self._XMLDesc(VIR_DOMAIN_XML_SECURE)
        tree = ElementTree.fromstring(xml)

        set_mem = tree.find('memory')
        set_mem.text = str(memory)
        set_cur_mem = tree.find('currentMemory')
        set_cur_mem.text = str(cur_memory)

        new_xml = ElementTree.tostring(tree)
        self._defineXML(new_xml)


    def change_vm_memory_active(self, vm_memory):
        """
        Function change cpu when vm is starting.
        """
        memory = int(vm_memory) * 1024 * 1024
        flags = 0
        flags |= VIR_DOMAIN_AFFECT_LIVE
        flags |= VIR_DOMAIN_AFFECT_CONFIG
        self.instance.setMemoryFlags(int(memory), flags)

    def get_iso_media(self):
        iso = []
        storages = self.get_storages()
        for storage in storages:
            stg = self.get_storage(storage)
            if stg.info()[0] != 0:
                try:
                    stg.refresh(0)
                except:
                    pass
                for img in stg.listVolumes():
                    if img.lower().endswith('.iso'):
                        iso.append(img)
        return iso

    def delete_disk(self):
        disks = self.get_disk_device()
        for disk in disks:
            vol = self.get_volume_by_path(disk.get('path'))
            vol.delete(0)


    def _snapshotCreateXML(self, xml, flag):
        self.instance.snapshotCreateXML(xml, flag)


    def create_snapshot(self, name):
        xml = """<domainsnapshot>
                     <name>%s</name>
                     <state>shutoff</state>
                     <creationTime>%d</creationTime>""" % (name, time.time())
        xml += self._XMLDesc(VIR_DOMAIN_XML_SECURE)
        xml += """<active>0</active>
                  </domainsnapshot>"""
        self._snapshotCreateXML(xml, 16)

    def create_disk_snapshot(self, image_disk_list, nowtime):
        nowtime = str(nowtime)
        xml = """<domainsnapshot>
				    <description>%s</description>
				    <disks>""" % nowtime
        for image_data in image_disk_list:
            snapshot_data = image_data + '.snapshot'
            xml += """<disk name ='%s'>
                        <source file='%s'/>
                      </disk>""" % (image_data, snapshot_data)
        xml += """</disks>
                </domainsnapshot>"""
        flags = VIR_DOMAIN_SNAPSHOT_CREATE_DISK_ONLY | VIR_DOMAIN_SNAPSHOT_CREATE_NO_METADATA | VIR_DOMAIN_SNAPSHOT_CREATE_ATOMIC
        self._snapshotCreateXML(xml, flags)

    def create_single_disk_snapshot(self, image_data, nowtime, undo_dev):
        nowtime = str(nowtime)
        desc = nowtime + '_' + image_data.split('/')[-1]
        snapshot_data = image_data + '.snapshot'
        xml = """<domainsnapshot>
                    <description>%s</description>
                    <disks>
                    <disk name ='%s'>
                    <source file='%s'/>
                    </disk>""" % (desc, image_data, snapshot_data)
        for dev in undo_dev:
            xml += """<disk name='%s' snapshot='no'/>""" % dev
        xml +=     """</disks>
                  </domainsnapshot>"""
        self._snapshotCreateXML(xml, 16)

    def get_snapshot(self):
        snapshots = []
        snapshot_list = self.instance.snapshotListNames(0)
        for snapshot in snapshot_list:
            snap = self.instance.snapshotLookupByName(snapshot, 0)
            snap_time_create = util.get_xml_path(snap.getXMLDesc(0), "/domainsnapshot/creationTime")
            snapshots.append({'date': datetime.fromtimestamp(int(snap_time_create)), 'name': snapshot})
        return snapshots

    def ex_disk_snapshot_commit(self, disk_tag, snap_url):
        flag = VIR_DOMAIN_BLOCK_COMMIT_ACTIVE | VIR_DOMAIN_BLOCK_COMMIT_RELATIVE
        print 'flag is %s' % flag
        ret = self._blockcommit(disk_tag, flag, snap_url)
        return ret

    def snapshot_delete(self, snapshot):
        snap = self.instance.snapshotLookupByName(snapshot, 0)
        snap.delete(0)

    def snapshot_revert(self, snapshot):
        snap = self.instance.snapshotLookupByName(snapshot, 0)
        self.instance.revertToSnapshot(snap, 0)

    def get_managed_save_image(self):
        return self.instance.hasManagedSaveImage(0)

    def close(self):
        self.wvm.close()

    # modify by denis guo at 20170508
    def clone_instance(self, clone_data):
        stg_refresh = self.get_storage(clone_data['src_uuid'])
        stg_refresh.refresh(0)

        clone_dev_path = []

        xml = self._XMLDesc(VIR_DOMAIN_XML_SECURE)
        tree = ElementTree.fromstring(xml)
        name = tree.find('name')
        name.text = clone_data['name']
        uuid = tree.find('uuid')
        tree.remove(uuid)

        """
        for num, net in enumerate(tree.findall('devices/interface')):
            # remove all configuration os network
            elm = net.find('mac')
            elm.set('address', randomMAC())
            # tree.remove(net)
        """
        device_node = tree.find('devices')
        for net in device_node.findall('interface'):
            device_node.remove(net)

        for disk in tree.findall('devices/disk'):
            if disk.get('device') == 'disk':
                elm = disk.find('target')
                device_name = elm.get('dev')
                if device_name:
                    target_file = clone_data[device_name]
                    meta_prealloc = False
                    elm.set('dev', device_name)

                elm = disk.find('source')
                source_file = elm.get('file')
                if source_file:
                    clone_dev_path.append(source_file)
                    clone_path = os.path.join('/app/image/' + clone_data['uuid'],
                                              target_file)
                    elm.set('file', clone_path)

                    vol = self.get_volume_by_path(source_file)
                    vol_format = util.get_xml_path(vol.XMLDesc(0),
                                                   "/volume/target/format/@type")

                    if vol_format == 'qcow2' and meta_prealloc:
                        meta_prealloc = True
                    vol_clone_xml = """
                                    <volume>
                                        <name>%s</name>
                                        <capacity>0</capacity>
                                        <allocation>0</allocation>
                                        <target>
                                            <format type='%s'/>
                                        </target>
                                    </volume>""" % (target_file, vol_format)
                    # stg = vol.storagePoolLookupByVolume()
                    stg = self.get_storage(clone_data['uuid'])
                    stg.createXMLFrom(vol_clone_xml, vol, meta_prealloc)

        clone_instance_xml = ElementTree.tostring(tree)
        uuid = "<uuid>" + clone_data['uuid'] + "</uuid>"
        xml_left, xml_rigth = clone_instance_xml.rsplit("<domain type=\"kvm\">", 1)
        clone_instance_xml_new = "<domain type=\"kvm\">\n  " + uuid + xml_rigth

        self._defineXML(clone_instance_xml_new)


    # 更新qemu-guest-agent到最新版本
    def update_qemu_agent_version(self,centostype):
        """
        :param command:
        :param centostype: CentOS 7 or CentOS 6
        :return:
        """
        try:
            ret = libvirt_qemu.qemuAgentCommand(self.instance,'{"execute":"exe-cmd","arguments":{"cmd":"%s"}}' % 'hostname', 60, 0)
            if not isinstance(eval(ret)['return'],dict):
                libvirt_qemu.qemuAgentCommand(self.instance,
                                              '{"execute":"exe-cmd","arguments":{"cmd":"%s"}}' % 'yum clean all;yum update qemu-guest-agent -y', 60, 0)
                # 更新后重启服务
                return self.restart_qemu_ga_service(centostype)
            # 测试是否更新成功
            return self.test_update_command()
        except libvirtError as e:
            # 可能更新断开连接，跳转至异常，同样重启服务
            return self.restart_qemu_ga_service(centostype)

    # 检查是否更新成功
    def test_update_command(self):
        """
        用于检测更新是否真的成功，hostname检测
        :return:
        """
        try:
            time.sleep(2)
            ret = libvirt_qemu.qemuAgentCommand(self.instance,
                                                '{"execute":"exe-cmd","arguments":{"cmd":"%s"}}' % 'hostname',
                                                60, 0)
            if not isinstance(eval(ret)['return'], dict):
                return False, 'update error.'
            else:
                return True, 'update'
        except libvirtError as e:
            return False, 'test update error.'

    # 重启qemu-guest-agent服务
    def restart_qemu_ga_service(self, centostype):
        try:
            if centostype == CentOS_Version.CentOS_7:
                libvirt_qemu.qemuAgentCommand(self.instance,
                                              '{"execute":"exe-cmd","arguments":{"cmd":"%s"}}' % 'systemctl restart qemu-guest-agent.service',
                                              60, 0)
            else:
                libvirt_qemu.qemuAgentCommand(self.instance,
                                              '{"execute":"exe-cmd","arguments":{"cmd":"%s"}}' % '/etc/init.d/qemu-ga restart',
                                              60, 0)
            return self.test_update_command()
        except libvirtError as e:
            return self.test_update_command()

    # 通过最新版本的qemu-guest-agent执行命令
    def exec_qemu_command(self,command):
        """
            通过qemu-guest-agent执行linux命令
        :param command: 命令
        :return:
        """
        try:
            ret = libvirt_qemu.qemuAgentCommand(self.instance,'{"execute":"exe-cmd","arguments":{"cmd":"%s"}}' % command, 60, 0)
            output = base64.decodestring(eval(ret)['return']['output'])
            return True,output
        except libvirtError as e:
            return False,'execute qemu command error.'

    def get_netcard_state(self):

        def networks(ctx):
            result = []
            for net in ctx.xpathEval('/domain/devices/interface'):
                mac = net.xpathEval('mac/@address')[0].content
                bridge = net.xpathEval('source/@network|source/@bridge|source/@dev')[0].content
                if net.xpathEval('link/@state'):
                    state = net.xpathEval('link/@state')[0].content
                else:
                    state = 'up'
                result.append({'mac': mac, 'bridge': bridge, 'state': state})
            return result

        return util.get_xml_path(self._XMLDesc(0), func=networks)
