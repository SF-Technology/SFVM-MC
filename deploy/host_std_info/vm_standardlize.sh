#!/bin/sh

#入参获取vm名称和磁盘文件路径
vmip=$1
dir=$2
vlan=$3
vmname=$4
vmmac=$5
vmuuid=$6
vmcpu=$7
vmmem=$8
ostype=$9
echo $vmip
echo $dir
echo $vlan
echo $vmname
echo $vmmac
echo $vmuuid
echo $vmcpu
echo $vmmem
echo $ostype

#设置vm的网卡信息
vmvlan=br_bond0.$vlan

#拷贝原始xml文件至当前目录
cd $dir
echo > diskfile
echo "the dest xml is "$vmip.xml

if [ $ostype = "Linux" ];then
cp /root/orginal_windows.xml $vmip.xml
else 
cp /root/orginal_windows.xml $vmip.xml
fi

#修改系统盘名称并写入disk文件
cd $dir
imgdisk=`ls $dir|grep qcow2|grep -v 'vd'`
echo "var imgdisk is "$imgdisk

mv $imgdisk $vmip.img
echo "the sys img is "$vmip.img

cat << EOF >> diskfile
 <disk type='file' device='disk'>
     <driver name='qemu' type='qcow2'/>
     <source file='$dir/$vmip.img'/>
     <target dev='vda' bus='virtio'/>
 </disk>
EOF

disktag=(vdb vdc vdd vde vdf vdg vdh vdi vdj)

#修改数据盘名称并写入disk文件
i=0
m=1
for n in `ls $dir|grep qcow2|grep vd`
do 
mv $n $vmip.disk$m
echo $vmip.disk$m
cat << EOF >> diskfile
	<disk type='file' device='disk'>
		<driver name='qemu' type='qcow2'/>
	    <source file='$dir/$vmip.disk$m'/>
	    <target dev='${disktag[$i]}' bus='virtio'/>
    </disk>
EOF
let i+=1
let m+=1		
done

#将disk文件添加到vm的xml文件中
sed -i '/<devices>/r diskfile' $vmip.xml

#获取vm的cpu和mem值并写入xml文件

sed -i "s/vmcpusize/$vmcpu/g" $vmip.xml
sed -i "s/vmmemsize/$vmmem/g" $vmip.xml

#修改xml中vm名称
sed -i "s/orginal/$vmname/g" $vmip.xml

#修改xml中的bridge网卡
sed -i "s/vmnet/$vmvlan/g" $vmip.xml

#修改xml中的vmuuid
sed -i "s/vmuuid/$vmuuid/g" $vmip.xml

#修改xml中的MAC地址
sed -i "s/vmmac/$vmmac/g" $vmip.xml

#修改xml中的vmvlan
sed -i "s/vmvlan/$vmvlan/g" $vmip.xml


