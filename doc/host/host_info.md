# GET /host/info/<int:host_id> 获取物理机详情


## 请求参数
| 参数 | 是否必须 | 类型 | 描述 | 
|-----|----------|------|-------------|-------|
| host_id   | 是| int| 集群ID|


## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": {
            "datacenter": "机房名",
            "displayname": "物理机显示名",
            "hold_mem_gb": "保留内存",
            "host_id": "物理机ID",
            "hostpool": "集群名",
            "instance_nums": "vm数量",
            "ipaddress": "IP地址",
            "manage_ip": "管理IP",
            "name": "物理机名",
            "net_area": "网络区域名",
            "sn": "序列号",
            "status": "状态 正常0，开机中1，关机中2",
            "typestatus": "业务状态 正常0，锁定1，维护2",
            "cpu_core": "CPU核数 单位：核",
            "current_cpu_used": "CPU使用率",
            "disk_size": "磁盘容量  单位：G",
            "current_disk_used": "磁盘使用率",
            "mem_size": "内存 单位：M",
            "current_mem_used": "内存使用率",
            "images": "物理机上所有镜像",
            "start_time": "物理机开机时间",
            "libvirt_status": "libvirtd服务状态",
            "libvirt_port": "libvirtd服务端口",
            "ostype": "物理机操作系统版本",
            "mem_assign_per": "物理机内存分配率"
        }
    }

```
