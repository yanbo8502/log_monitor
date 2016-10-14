#!/bin/bash
server_host=$1
deploy_root_dir=/data/dist/scripts

ssh root@$server_host "if [ ! -d /data ];then mkdir /data; fi"
ssh root@$server_host "if [ ! -d /data/dist ];then mkdir /data/dist; fi"
ssh root@$server_host "if [ ! -d $deploy_root_dir ];then mkdir $deploy_root_dir; fi"

#把执行服务需要的文件部署到目标路径
scp *.py root@$server_host:$deploy_root_dir
scp *.sh root@$server_host:$deploy_root_dir
scp *.ini root@$server_host:$deploy_root_dir