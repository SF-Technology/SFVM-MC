#!/bin/bash
user_pass=$1
root_pass=$2
(echo $user_pass;sleep 1;echo $user_pass)|/sbin/saslpasswd2 -a libvirt cloudkvm
echo $user_pass | /bin/passwd --stdin cloudkvm
echo $root_pass | /bin/passwd --stdin root