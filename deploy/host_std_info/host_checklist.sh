#!/bin/bash
#host checklist
hostip=$1

#check if BIOS Virtual open
host_bios_check=`virt-host-validate |grep FAIL`
if [ "$host_bios_check" != "" ]
then
	echo "$hostip BIOS Virtual not open" 
	exit 1
fi

#check if image pool is ready
image_pool=`virsh pool-list --all|grep image`
if [ "$image_pool" = "" ]
then
	echo "$hostip image pool is not open"
	exit 1
else
	image_pool_status=`virsh pool-list --all|grep image|grep -E "inactive|no"`
	if [ "$image_pool_status" != "" ]
	then
		echo "$hostip image pool is not active or not autoactive"
		exit 1
	fi
fi


#check if clone pool is ready
clone_pool=`virsh pool-list --all|grep clone`
if [ "$clone_pool" = "" ]
then
	echo "$hostip clone pool is not open"
	exit 1
else
	clone_pool_status=`virsh pool-list --all|grep clone|grep -E "inactive|no"`
	if [ "$clone_pool_status" != "" ]
	then
		echo "$hostip clone pool is not active or not autoactive"
		exit 1
	fi
fi


#check if ntp service is running
ntp_server_status=`systemctl status chronyd|grep active`
if [ "$ntp_server_status" = "" ]
then
	echo "$hostip ntp service is not running"
	exit 1
fi

#check if libvirt service is running
libvirt_server_status=`systemctl status libvirtd|grep active`
if [ "$libvirt_server_status" = "" ]
then
	echo "$hostip libvirtd service is not running"
	exit 1
fi

#check libvirt version 2.0.0
libvirt_res=`rpm -qa|grep libvirt-2.0.0-10.el7.x86_64`
if [ "$libvirt_res" = "" ]
then
        echo "libvirt version is not 2.0.0,please check"
        exit 1
fi

#check qemu version 2.0.0-e17.3
qemu_res=`rpm -qa|grep qemu-2.0.0-1.el7.3.x86_64`
if [ "$qemu_res" = "" ]
then
        echo "qemu version is not 2.0.0-1.el7.3,please check"
        exit 1
fi

#check virt-v2v version 1.32.7-3.el7
v2v_res=`rpm -qa|grep virt-v2v-1.32.7-3.el7`
if [ "$v2v_res" = "" ]
then
        echo "virt-v2v version is not 1.32.7-3.el7,please check"
        exit 1
fi

#all check ok
echo "all check done,ok!"
exit 0
