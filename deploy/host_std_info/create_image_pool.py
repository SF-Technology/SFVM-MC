import libvirt
from libvirt import libvirtError

def pool_create():

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
    </pool>"""
    
    try:
       conn = libvirt.open('qemu+tcp://webvirtmgr@localhost/system')
       conn.storagePoolDefineXML(xml, 0)
       stg = conn.storagePoolLookupByName('image')
       stg.create(0)
       stg.setAutostart(1)
    except libvirtError,e:
       return 'create pool failed'
    return 'create pool success'

if __name__ == '__main__':
    msg = pool_create()
    print msg
