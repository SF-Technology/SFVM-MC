#
# Copyright (C) 2013 Webvirtmgr.
#
import string
from . import util
from connection import wvmConnect

QEMU_CONSOLE_DEFAULT_TYPE = 'vnc'

def get_rbd_storage_data(stg):
    xml = stg.XMLDesc(0)
    ceph_user = util.get_xml_path(xml, "/pool/source/auth/@username")

    def get_ceph_hosts(ctx):
        hosts = []
        for host in ctx.xpathEval("/pool/source/host"):
            name = host.prop("name")
            if name:
                hosts.append({'name': name, 'port': host.prop("port")})
        return hosts
    ceph_hosts = util.get_xml_path(xml, func=get_ceph_hosts)
    secret_uuid = util.get_xml_path(xml, "/pool/source/auth/secret/@uuid")
    return ceph_user, secret_uuid, ceph_hosts


class wvmCreate(wvmConnect):
    def get_storages_images(self):
        """
        Function return all images on all storages
        """
        images = []
        storages = self.get_storages()
        for storage in storages:
            stg = self.get_storage(storage)
            try:
                stg.refresh(0)
            except:
                pass
            for img in stg.listVolumes():
                if 'iso' in img or 'img' in img or 'xml' in img or 'disk' in img:
                    pass
                else:
                    images.append(img)
        return images

    def get_os_type(self):
        """Get guest capabilities"""
        return util.get_xml_path(self.get_cap_xml(), "/capabilities/guest/os_type")

    def get_host_arch(self):
        """Get guest capabilities"""
        return util.get_xml_path(self.get_cap_xml(), "/capabilities/host/cpu/arch")

    def get_cache_modes(self):
        """Get cache available modes"""
        return {
            'default': 'Default',
            'none': 'Disabled',
            'writethrough': 'Write through',
            'writeback': 'Write back',
            'directsync': 'Direct sync',  # since libvirt 0.9.5
            'unsafe': 'Unsafe',  # since libvirt 0.9.7
        }

    def create_volume(self, storage, name, size, format='qcow2', metadata=False):
        size = int(size) * 1073741824
        stg = self.get_storage(storage)
        storage_type = util.get_xml_path(stg.XMLDesc(0), "/pool/@type")
        if storage_type == 'dir':
            name += '.img'
            alloc = 0
        else:
            alloc = size
            metadata = False
        xml = """
            <volume>
                <name>%s</name>
                <capacity>%s</capacity>
                <allocation>%s</allocation>
                <target>
                    <format type='%s'/>
                </target>
            </volume>""" % (name, size, alloc, format)
        stg.createXML(xml, metadata)
        try:
            stg.refresh(0)
        except:
            pass
        vol = stg.storageVolLookupByName(name)
        return vol.path()

    def get_volume_type(self, path):
        vol = self.get_volume_by_path(path)
        vol_type = util.get_xml_path(vol.XMLDesc(0), "/volume/target/format/@type")
        if vol_type == 'unknown':
            return 'raw'
        if vol_type:
            return vol_type
        else:
            return 'raw'

    def get_volume_path(self, volume):
        storages = self.get_storages()
        for storage in storages:
            stg = self.get_storage(storage)
            if stg.info()[0] != 0:
                # stg.refresh(0)
                for img in stg.listVolumes():
                    if img == volume:
                        vol = stg.storageVolLookupByName(img)
                        return vol.path()

    def get_storage_by_vol_path(self, vol_path):
        vol = self.get_volume_by_path(vol_path)
        return vol.storagePoolLookupByVolume()

    def get_vol_by_path(self, vol_path):
        vol = self.get_volume_by_path(vol_path)
        return vol

    def clone_from_disk_and_template(self, clone_disk_name, template_path, uuid, disk_num, metadata=False):
        pool = self.get_storage('image')
        pool.refresh(0)
        vol = self.get_volume_by_path(template_path)
        stg = self.get_storage(uuid)
        storage_type = util.get_xml_path(stg.XMLDesc(0), "/pool/@type")
        format = util.get_xml_path(vol.XMLDesc(0), "/volume/target/format/@type")
        if disk_num == 0:
            clone_disk_name += '.img'
        else:
            clone_disk_name += '.disk' + str(disk_num)

        xml = """
                    <volume>
                        <name>%s</name>
                        <capacity>0</capacity>
                        <allocation>0</allocation>
                        <target>
                            <format type='%s'/>
                        </target>
                    </volume>""" % (clone_disk_name, format)
        stg.createXMLFrom(xml, vol, metadata)
        clone_vol = stg.storageVolLookupByName(clone_disk_name)
        return clone_vol.path()

    def refresh_image_storage_pool(self):
        pool = self.get_storage('image')
        pool.refresh(0)

    def refresh_storage_pool_by_name(self, stg_pool):
        pool = self.get_storage(stg_pool)
        pool.refresh(0)

    def resize_vol(self, vol_path, size):
        vol = self.get_volume_by_path(vol_path)
        vol.resize(size)

    def clone_from_template_uuid(self, clone, template, uuid, metadata=False):
        # pool = self.get_storage('image')
        # pool.refresh(0)
        vol = self.get_volume_by_path(template)
        stg = self.get_storage(uuid)
        storage_type = util.get_xml_path(stg.XMLDesc(0), "/pool/@type")
        format = util.get_xml_path(vol.XMLDesc(0), "/volume/target/format/@type")
        if storage_type == 'dir':
            if '.' not in clone:
                clone += '.img'

        else:
            metadata = False
        xml = """
            <volume>
                <name>%s</name>
                <capacity>0</capacity>
                <allocation>0</allocation>
                <target>
                    <format type='%s'/>
                </target>
            </volume>""" % (clone, format)
        stg.createXMLFrom(xml, vol, metadata)
        clone_vol = stg.storageVolLookupByName(clone)
        return clone_vol.path()

    def clone_from_template(self, clone, template, metadata=False):
        vol = self.get_volume_by_path(template)
        stg = vol.storagePoolLookupByVolume()
        storage_type = util.get_xml_path(stg.XMLDesc(0), "/pool/@type")
        format = util.get_xml_path(vol.XMLDesc(0), "/volume/target/format/@type")
        if storage_type == 'dir':
            clone += '.img'
        else:
            metadata = False
        xml = """
            <volume>
                <name>%s</name>
                <capacity>0</capacity>
                <allocation>0</allocation>
                <target>
                    <format type='%s'/>
                </target>
            </volume>""" % (clone, format)
        stg.createXMLFrom(xml, vol, metadata)
        clone_vol = stg.storageVolLookupByName(clone)
        return clone_vol.path()

    def _defineXML(self, xml):
        self.wvm.defineXML(xml)

    def delete_volume(self, path):
        vol = self.get_volume_by_path(path)
        vol.delete()

    def create_instance(self, hostname, memory_mb, vcpu, host_model, uuid, images, cache_mode,
                        networks, virtio,  mac=None,description='kvmmgr create'):
        """
        Create VM function
        """
        memory = int(memory_mb) * 1024

        if self.is_kvm_supported():
            hypervisor_type = 'kvm'
        else:
            hypervisor_type = 'qemu'

        xml = """
                <domain type='%s'>
                  <name>%s</name>
                  <description>%s</description>
                  <uuid>%s</uuid>
                  <memory unit='KiB'>%s</memory>
                  <vcpu current='%s'>128</vcpu>""" % (hypervisor_type, hostname,description, uuid, memory, vcpu)
        if host_model:
            xml += """<cpu mode='host-model'/>"""
        xml += """<os>
                    <type arch='%s'>%s</type>
                    <boot dev='hd'/>
                    <boot dev='cdrom'/>
                    <bootmenu enable='yes'/>
                  </os>""" % (self.get_host_arch(), self.get_os_type())
        xml += """<features>
                    <acpi/><apic/><pae/>
                  </features>
                  <clock offset="localtime"/>
                  <on_poweroff>destroy</on_poweroff>
                  <on_reboot>restart</on_reboot>
                  <on_crash>restart</on_crash>
                  <devices>"""

        disk_letters = list(string.lowercase)

        for image in sorted(images, key=lambda i: i["dev_name"]):
            stg = self.get_storage_by_vol_path(image['image_dir_path'])
            stg_type = util.get_xml_path(stg.XMLDesc(0), "/pool/@type")

            if stg_type == 'rbd':
                ceph_user, secret_uuid, ceph_hosts = get_rbd_storage_data(stg)
                xml += """<disk type='network' device='disk'>
                            <driver name='qemu' type='%s' cache='%s'/>
                            <auth username='%s'>
                                <secret type='ceph' uuid='%s'/>
                            </auth>
                            <source protocol='rbd' name='%s'>""" % ('qcow2', cache_mode, ceph_user, secret_uuid, image)
                if isinstance(ceph_hosts, list):
                    for host in ceph_hosts:
                        if host.get('port'):
                            xml += """
                                   <host name='%s' port='%s'/>""" % (host.get('name'), host.get('port'))
                        else:
                            xml += """
                                   <host name='%s'/>""" % host.get('name')
                xml += """
                            </source>"""
            else:
                xml += """<disk type='file' device='disk'>
                            <driver name='qemu' type='%s' cache='%s'/>
                            <source file='%s'/>""" % ('qcow2', cache_mode, image['image_dir_path'])

            if virtio:
                xml += """<target dev='%s' bus='virtio'/>""" % image['dev_name']
            else:
                xml += """<target dev='%s' bus='ide'/>""" % image['dev_name']
            xml += """</disk>"""
        #xml += disk_xml
        xml += """  <disk type='file' device='cdrom'>
                      <driver name='qemu' type='raw'/>
                      <source file=''/>
                      <target dev='hda' bus='ide'/>
                      <readonly/>
                      <address type='drive' controller='0' bus='1' target='0' unit='1'/>
                    </disk>"""
        for net in networks.split(','):
            xml += """<interface type='bridge'>"""
            if mac:
                xml += """<mac address='%s'/>""" % mac
            xml += """<source bridge='%s'/>""" % net
            xml += """<link state='up'/>"""
            if virtio:
                xml += """<model type='virtio'/>"""
            xml += """</interface>"""

        xml += """<channel type='unix'>
                  <source mode='bind' path='/var/lib/libvirt/qemu/channel/target/%s.agent'/>
                   <target type='virtio' name='org.qemu.guest_agent.0' state='connected'/>
              </channel>""" % hostname

        xml += """  <input type='mouse' bus='ps2'/>
                    <input type='tablet' bus='usb'/>
                    <graphics type='%s' port='-1' autoport='yes' listen='0.0.0.0'>
                      <listen type='address' address='0.0.0.0'/>
                    </graphics>
                    <console type='pty'/>
                    <video>
                      <model type='cirrus'/>
                    </video>
                    <memballoon model='virtio'/>
                  </devices>
                </domain>""" % QEMU_CONSOLE_DEFAULT_TYPE
        self._defineXML(xml)

    def create_instance_no_nic(self, hostname, memory_mb, vcpu, host_model, uuid, images, cache_mode,
                        networks, virtio,  mac=None,description='kvmmgr create'):
        """
        Create VM function
        """
        memory = int(memory_mb) * 1024

        if self.is_kvm_supported():
            hypervisor_type = 'kvm'
        else:
            hypervisor_type = 'qemu'

        xml = """
                <domain type='%s'>
                  <name>%s</name>
                  <description>%s</description>
                  <uuid>%s</uuid>
                  <memory unit='KiB'>%s</memory>
                  <vcpu current='%s'>16</vcpu>""" % (hypervisor_type, hostname,description, uuid, memory, vcpu)
        if host_model:
            xml += """<cpu mode='host-model'/>"""
        xml += """<os>
                    <type arch='%s'>%s</type>
                    <boot dev='hd'/>
                    <boot dev='cdrom'/>
                    <bootmenu enable='yes'/>
                  </os>""" % (self.get_host_arch(), self.get_os_type())
        xml += """<features>
                    <acpi/><apic/><pae/>
                  </features>
                  <clock offset="localtime"/>
                  <on_poweroff>destroy</on_poweroff>
                  <on_reboot>restart</on_reboot>
                  <on_crash>restart</on_crash>
                  <devices>"""

        disk_letters = list(string.lowercase)
        #images =[{"/app/image/xxxx/xxxx.img":"qcow2"}]
        # for image, img_type in images.items():
        for image in sorted(images, reverse=True):
            stg = self.get_storage_by_vol_path(image)
            stg_type = util.get_xml_path(stg.XMLDesc(0), "/pool/@type")

            if stg_type == 'rbd':
                ceph_user, secret_uuid, ceph_hosts = get_rbd_storage_data(stg)
                xml += """<disk type='network' device='disk'>
                            <driver name='qemu' type='%s' cache='%s'/>
                            <auth username='%s'>
                                <secret type='ceph' uuid='%s'/>
                            </auth>
                            <source protocol='rbd' name='%s'>""" % ('qcow2', cache_mode, ceph_user, secret_uuid, image)
                if isinstance(ceph_hosts, list):
                    for host in ceph_hosts:
                        if host.get('port'):
                            xml += """
                                   <host name='%s' port='%s'/>""" % (host.get('name'), host.get('port'))
                        else:
                            xml += """
                                   <host name='%s'/>""" % host.get('name')
                xml += """
                            </source>"""
            else:
                xml += """<disk type='file' device='disk'>
                            <driver name='qemu' type='%s' cache='%s'/>
                            <source file='%s'/>""" % ('qcow2', cache_mode, image)

            if virtio:
                xml += """<target dev='vd%s' bus='virtio'/>""" % (disk_letters.pop(0),)
            else:
                xml += """<target dev='sd%s' bus='ide'/>""" % (disk_letters.pop(0),)
            xml += """</disk>"""
        #xml += disk_xml
        xml += """  <disk type='file' device='cdrom'>
                      <driver name='qemu' type='raw'/>
                      <source file=''/>
                      <target dev='hda' bus='ide'/>
                      <readonly/>
                      <address type='drive' controller='0' bus='1' target='0' unit='1'/>
                    </disk>"""
        xml += """<channel type='unix'>
                  <source mode='bind' path='/var/lib/libvirt/qemu/channel/target/%s.agent'/>
                   <target type='virtio' name='org.qemu.guest_agent.0' state='connected'/>
              </channel>""" % hostname

        xml += """  <input type='mouse' bus='ps2'/>
                    <input type='tablet' bus='usb'/>
                    <graphics type='%s' port='-1' autoport='yes' listen='0.0.0.0'>
                      <listen type='address' address='0.0.0.0'/>
                    </graphics>
                    <console type='pty'/>
                    <video>
                      <model type='cirrus'/>
                    </video>
                    <memballoon model='virtio'/>
                  </devices>
                </domain>""" % QEMU_CONSOLE_DEFAULT_TYPE
        self._defineXML(xml)


    def v2v_esx_xml(self, hostname, memory_mb, vcpu, host_model, uuid, images, cache_mode,
                        networks, virtio, mac=None, description='kvmmgr create'):
        """
        Create VM function
        """
        memory = int(memory_mb) * 1024

        if self.is_kvm_supported():
            hypervisor_type = 'kvm'
        else:
            hypervisor_type = 'qemu'

        xml = """
                <domain type='%s'>
                  <name>%s</name>
                  <description>%s</description>
                  <uuid>%s</uuid>
                  <memory unit='KiB'>%s</memory>
                  <vcpu current='%s'>16</vcpu>""" % (hypervisor_type, hostname, description, uuid, memory, vcpu)
        if host_model:
            xml += """<cpu mode='host-model'/>"""
        xml += """<os>
                    <type arch='%s'>%s</type>
                    <boot dev='hd'/>
                    <boot dev='cdrom'/>
                    <bootmenu enable='yes'/>
                  </os>""" % (self.get_host_arch(), self.get_os_type())
        xml += """<features>
                    <acpi/><apic/><pae/>
                  </features>
                  <clock offset="localtime"/>
                  <on_poweroff>destroy</on_poweroff>
                  <on_reboot>restart</on_reboot>
                  <on_crash>restart</on_crash>
                  <devices>"""

        disk_letters = list(string.lowercase)
        # images =[{"/app/image/xxxx/xxxx.img":"qcow2"}]
        # for image, img_type in images.items():
        for image in images:
            stg = self.get_storage_by_vol_path(image)
            stg_type = util.get_xml_path(stg.XMLDesc(0), "/pool/@type")

            if stg_type == 'rbd':
                ceph_user, secret_uuid, ceph_hosts = get_rbd_storage_data(stg)
                xml += """<disk type='network' device='disk'>
                            <driver name='qemu' type='%s' cache='%s'/>
                            <auth username='%s'>
                                <secret type='ceph' uuid='%s'/>
                            </auth>
                            <source protocol='rbd' name='%s'>""" % (
                'qcow2', cache_mode, ceph_user, secret_uuid, image)
                if isinstance(ceph_hosts, list):
                    for host in ceph_hosts:
                        if host.get('port'):
                            xml += """
                                   <host name='%s' port='%s'/>""" % (host.get('name'), host.get('port'))
                        else:
                            xml += """
                                   <host name='%s'/>""" % host.get('name')
                xml += """
                            </source>"""
            else:
                xml += """<disk type='file' device='disk'>
                            <driver name='qemu' type='%s' cache='%s'/>
                            <source file='%s'/>""" % ('qcow2', cache_mode, image)

            if virtio:
                xml += """<target dev='vd%s' bus='virtio'/>""" % (disk_letters.pop(0),)
            else:
                xml += """<target dev='sd%s' bus='ide'/>""" % (disk_letters.pop(0),)
            xml += """</disk>"""
        # xml += disk_xml
        xml += """  <disk type='file' device='cdrom'>
                      <driver name='qemu' type='raw'/>
                      <source file=''/>
                      <target dev='hda' bus='ide'/>
                      <readonly/>
                      <address type='drive' controller='0' bus='1' target='0' unit='1'/>
                    </disk>"""
        for net in networks.split(','):
            xml += """<interface type='bridge'>"""
            if mac:
                xml += """<mac address='%s'/>""" % mac
            xml += """<source bridge='%s'/>""" % net

            xml += """<model type='virtio'/>"""
            xml += """</interface>"""

        xml += """<channel type='unix'>
                  <source mode='bind' path='/var/lib/libvirt/qemu/channel/target/%s.agent'/>
                   <target type='virtio' name='org.qemu.guest_agent.0' state='connected'/>
              </channel>""" % hostname

        xml += """  <input type='mouse' bus='ps2'/>
                    <input type='tablet' bus='usb'/>
                    <graphics type='%s' port='-1' autoport='yes' listen='0.0.0.0'>
                      <listen type='address' address='0.0.0.0'/>
                    </graphics>
                    <console type='pty'/>
                    <video>
                      <model type='cirrus'/>
                    </video>
                    <memballoon model='virtio'/>
                  </devices>
                </domain>""" % QEMU_CONSOLE_DEFAULT_TYPE
        self._defineXML(xml)