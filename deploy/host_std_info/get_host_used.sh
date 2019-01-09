#!/bin/bash

export PATH=/sbin:/bin:/usr/sbin:/usr/bin

#RemoteDir="username@192.168.1.45:/app/info"

url=$1

get_cpu_p95(){
     #获取过去n天cpu的p95,参数为过去的n天
    local days=$1
    if [ $1 -lt 1 ]; then
        echo "Input day must larger than 1."
        exit 1
    fi
    local week_cpu_useds=""
    local day_cpu_useds=""
    for i in `seq 1 ${days}`; do
        d=`date -d "$i days ago" "+%d"`
        if [ -f "/var/log/sa/sa$d" ]; then
            day_cpu_useds=`sar -f "/var/log/sa/sa$d" -u | egrep "M     all" | \
                    awk '{print (100-$NF)}' |  sed 's@\.[0-9]*@@'`
            week_cpu_useds="$week_cpu_useds\n$day_cpu_useds"
        else
            continue
        fi
    done
    local week_cpu_useds=`echo -e "${week_cpu_useds}" | sed '1d' | sort -rn`
    local point_num=`echo "${week_cpu_useds}" | wc -l`
    local point_line_num=`echo "${point_num}/20" | bc`
    local week_cpu_p95_used=`echo "${week_cpu_useds}" | head -n "${point_line_num}" | tail -n 1`
    echo ${week_cpu_p95_used}
}

get_mem_p95(){
    # 获取过去n天内存的p95,参数为过去的n天 
    local days=$1
    if [ $1 -lt 1 ]; then
        echo "Input day must larger than 1."
        exit 1
    fi
    local week_mem_useds=""
    local day_mem_useds=""
    for i in `seq 1 ${days}`; do
        d=`date -d "$i days ago" "+%d"`
        if [ -f "/var/log/sa/sa$d" ]; then
            day_mem_useds=`sar -f "/var/log/sa/sa$d" -r | egrep "M\s+[0-9]" | \
                    awk -v mem_size="$mem_size" 'BEGIN{mem_size=mem_size*1024}{print (mem_size-$3-$11)*100/mem_size}' | \
                    sed 's@\.[0-9]*@@'`
            week_mem_useds="$week_mem_useds\n$day_mem_useds"
        else
            continue
        fi
    done
    local week_mem_useds=`echo -e "${week_mem_useds}" | sed '1d' | sort -rn`
    local point_num=`echo "${week_mem_useds}" | wc -l`
    local point_line_num=`echo "${point_num}/20" | bc`
    local week_mem_p95_used=`echo "${week_mem_useds}" | head -n "${point_line_num}" | tail -n 1`
    echo ${week_mem_p95_used}
}

# ==== main ====
if ! command -v sar &>/dev/null; then
    echo "sar do not exist."
    exit 1
fi

if [ "`rpm -q sysstat | cut -c '1-9'`" == "sysstat-9" ]; then
    echo "sysstat version must greater than 10."
    exit 1
fi

hosttime=`date +%Y-%m-%d\ %H:%M:%S`
major_nic=`route -n | awk '/^0\.0\.0\.0.*UG/ {print $NF}'`
major_ip=`ip a | awk -v nic="${major_nic}" '$NF == nic {print $2}' | head -n 1 | awk -F'/' '{print $1}'`

cpu_core=`grep -c "processor" /proc/cpuinfo`
mem_size=`awk '/MemTotal/ {print $2}' /proc/meminfo`
mem_size=`echo "${mem_size}/1024" | bc`
disk_size=`df -P -B 1G | awk '/\/app/ {print $2}'`

#current_cpu_idle=`sar -u | tail -n 1 | awk '{print $NF}'`
current_cpu_idle=`sar -u | grep '^[0-9]' | tail -n 60 | awk '{cup_idle+=$NF;num++} END{print cup_idle/num}'`
current_cpu_used=`echo "(10000-${current_cpu_idle}*100)/100" | bc | sed 's@\.[0-9]*@@'`

current_mem_kbmemfree=`sar -r | grep '^[0-9]' | tail -n 60 | awk '{kbmemfree+=$3;num++} END{print kbmemfree/num}'`
current_mem_kbinact=`sar -r | grep '^[0-9]' | tail -n 60 | awk '{kbinact+=$11;num++} END{print kbinact/num}'`
current_mem_used=`gawk -v a="$mem_size" -v b="$current_mem_kbinact" -v c="$current_mem_kbmemfree" 'BEGIN{printf (a*1024-b-c)*100/(a*1024) }'| sed 's@\.[0-9]*@@'`

#current_mem_used=`sar -r | tail -n 1 | \
#                  awk -v mem_size="$mem_size" 'BEGIN{mem_size=mem_size*1024}{print (mem_size-$2-$10)*100/mem_size}' | \
#                  sed 's@\.[0-9]*@@'`

net_size=`cat /sys/devices/virtual/net/bond0/speed`
current_net_rx=`sar -n DEV | grep '^[0-9]' |grep bond0|grep -v bond0.[0-9][0-9]| tail -n 60 | awk '{rxkB+=$6;num++} END{print rxkB/num}'`
current_net_tx=`sar -n DEV | grep '^[0-9]' |grep bond0|grep -v bond0.[0-9][0-9]| tail -n 60 | awk '{txkB+=$7;num++} END{print txkB/num}'`
current_net_rx_used=`gawk -v a="$net_size" -v b="$current_net_rx" 'BEGIN{printf (b*100)/(a/8*1024)}'| sed 's@\.[0-9]*@@'`
current_net_tx_used=`gawk -v a="$net_size" -v b="$current_net_tx" 'BEGIN{printf (b*100)/(a/8*1024)}'| sed 's@\.[0-9]*@@'`

current_disk_used=`df -P -B 1G | awk '/\/app/ {print $5}' | sed 's@%@@'`

week_mem_p95_used=`get_mem_p95 7`
week_cpu_p95_used=`get_cpu_p95 7`

start_time=`date -d "$(awk -F. '{print $1}' /proc/uptime) second ago" +"%Y-%m-%d %H:%M:%S"`
ostype=`cat /etc/redhat-release`
libvirt_port=`netstat -anpt | grep libvirtd | head -n 1 | awk '{print $4}' | awk -F: '{print $2}'`

libvirt_process_count=`ps -ef | grep libvirtd | grep -v grep | wc -l`
if [ $libvirt_process_count -gt 0 ]; then
    libvirt_status='running'
else
    libvirt_status='not running'
fi

images=`cd /app/image;ls -x | grep -v '.*-.*-.*-.*-.*' | xargs`

if [ ! -n "$disk_size" ];then
  disk_size=0
fi

if [ ! -n "$net_size" ];then 
  net_size=0
fi

if [ ! -n "$current_cpu_used" ];then 
  current_cpu_used=0
fi

if [ ! -n "$current_mem_used" ];then
  current_mem_used=0
fi

if [ ! -n "$current_disk_used" ];then
  current_disk_used=0
fi

if [ ! -n "$week_cpu_p95_used" ];then
  week_cpu_p95_used=0
fi

if [ ! -n "$week_mem_p95_used" ];then
  week_mem_p95_used=0
fi

if [ ! -n "$current_net_rx_used" ];then
  current_net_rx_used=0
fi

if [ ! -n "$current_net_tx_used" ];then
  current_net_tx_used=0
fi


hostname=`hostname`

curl -u hostdata:Bodr8m8T# -H "Content-Type: application/json" -X POST -k --data '{
  "ip":"'"$major_ip"'",
  "hostname":"'"$hostname"'",
  "ostype":"'"$ostype"'",
  "cpu_core":"'"$cpu_core"'",
  "mem_size":"'"$mem_size"'",
  "disk_size":"'"$disk_size"'",
  "net_size":"'"$net_size"'",
  "current_cpu_used":"'"$current_cpu_used"'",
  "current_mem_used":"'"$current_mem_used"'",
  "current_disk_used":"'"$current_disk_used"'",
  "week_cpu_p95_used":"'"$week_cpu_p95_used"'",
  "week_mem_p95_used":"'"$week_mem_p95_used"'",
  "current_net_rx_used":"'"$current_net_rx_used"'",
  "current_net_tx_used":"'"$current_net_tx_used"'",
  "start_time":"'"$start_time"'",
  "libvirt_port":"'"$libvirt_port"'",
  "libvirt_status":"'"$libvirt_status"'",
  "images":"'"$images"'",
  "collect_time":"'"$hosttime"'"
}' ${url}/host/host_perform_data


if [ $? -eq 0 ]; then
  echo "[OK]: `date` Copy file /root/${major_ip} to ${RemoteDir}/ successful." > /root/up_host_used_file.log
else
  echo "[ALERT]: `date` Copy file /root/${major_ip} to ${RemoteDir}/ failed!" > /root/up_host_used_file.log
fi
