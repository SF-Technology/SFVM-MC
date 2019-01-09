#!/bin/bash
input=`cat dstip`

rip=`echo $input | awk -F ',' '{print $1}'`
pwd=tsPWD@`echo $input | awk -F ',' '{print $2}'`
user=tskvm

timeout 60 ipmitool -I lanplus -H $rip -U $user -P $pwd sol deactivate
timeout 1800 ipmitool -I lanplus -H $rip -U $user -P $pwd sol activate