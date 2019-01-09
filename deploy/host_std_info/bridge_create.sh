#!/usr/bin/env bash
#/bin/bash
vlan=$1
bond=$2

#set variable
bondx=$bond.${vlan}
bridgex=br_$bond.${vlan}
ifcfg_bondx=ifcfg-${bondx}
ifcfg_bridgex=ifcfg-${bridgex}

#check bridge exist or not
check_bridge=`/usr/sbin/ip a|grep -w ${bridgex}`
if [ "$check_bridge" != "" ]
then
        exit 0
fi

#config bond0.x file
echo "DEVICE=${bondx}" >> /etc/sysconfig/network-scripts/${ifcfg_bondx}
echo "BOOTPROTO=none" >> /etc/sysconfig/network-scripts/${ifcfg_bondx}
echo "ONBOOT=yes" >> /etc/sysconfig/network-scripts/${ifcfg_bondx}
echo "VLAN=yes" >> /etc/sysconfig/network-scripts/${ifcfg_bondx}
echo "BRIDGE=${bridgex}" >> /etc/sysconfig/network-scripts/${ifcfg_bondx}

#up bond0.x
/usr/sbin/ifup $bondx

#config br_bond0.x file
echo "DEVICE=${bridgex}" >> /etc/sysconfig/network-scripts/${ifcfg_bridgex}
echo "TYPE=Bridge" >> /etc/sysconfig/network-scripts/${ifcfg_bridgex}
echo "BOOTPROTO=static" >> /etc/sysconfig/network-scripts/${ifcfg_bridgex}
echo "ONBOOT=yes" >> /etc/sysconfig/network-scripts/${ifcfg_bridgex}

#up br_bond0.x
/usr/sbin/ifup $bridgex
