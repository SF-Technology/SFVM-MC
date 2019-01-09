#!/bin/bash
source_bridge=$1
dest_bridge=$2
vlan_nic=$3
vlan_nic_dev=ifcfg-${vlan_nic}
source_bridge_dev=ifcfg-${source_bridge}
dest_bridge_dev=ifcfg-${dest_bridge}

# check brvlan exist or not
check_bridge=`/usr/sbin/ip a|grep -w ${source_bridge}`
if [ "$check_bridge" = "" ]
then
        echo "host bridge brvlan not exist,quit" > /tmp/host_bridge_ch.log
        exit 1
fi

# shutdown binding nic
/usr/sbin/ifconfig $vlan_nic down

# shutdown source bridge
/usr/sbin/ifconfig $source_bridge down

# del source bridge
/usr/sbin/brctl delbr $source_bridge

# edit vlan nic configuration
sed -i "s/BRIDGE=.*/BRIDGE=$dest_bridge/g" /etc/sysconfig/network-scripts/$vlan_nic_dev

# edit bridge nic configuration
sed -i "s/DEVICE=.*/DEVICE=$dest_bridge/g" /etc/sysconfig/network-scripts/$source_bridge_dev

# change bridge dev name
cd /etc/sysconfig/network-scripts;mv $source_bridge_dev $dest_bridge_dev

# ifup vlan_nic
/usr/sbin/ifup $vlan_nic

# ifup dest_bridge
/usr/sbin/ifup $dest_bridge

echo "host bridge change done" > /tmp/host_bridge_ch.log
exit 0
