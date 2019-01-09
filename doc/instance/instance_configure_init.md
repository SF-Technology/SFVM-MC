# GET /instance/configure/init/<int:instance_id> 修改配置时获取初始数据


## 请求参数
| 参数 | 是否必须 | 类型 | 描述 | 
|-----|----------|------|-------------|-------|
| instance_id   | 是| int| 虚拟机ID|


## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": {
	    "c_instance_name": "主机名",
	    "c_app_info": "应用系统信息",
        "net_card": [
        {
          "ip_addr": "192.168.1.1",
          "mac_addr": "fe:54:00:71:52:87",
          "nic_status": "1代表已连接，0代表断开"
        },
        {
          "ip_addr": "192.168.1.2",
          "mac_addr": "fe:54:00:71:52:87",
          "nic_status": "1代表已连接，0代表断开"
        }
        ],
        "c_ips":[
        {
          "value": "192.168.1.3", 
          "vlan":"39",
          "ip_type": "0"
        },
        {
          "value": "192.168.1.4", 
          "vlan":"39",
          "ip_type": "4"
          }
        ],
        "c_flavor_id": "flavor ID",
        "c_group_id": "组ID",
        "c_system": "主机类型",
        "c_owner": "管理员姓名",
        "flavors": [
          {
            "flavor_id": 1,
            "memory_mb": 512,
            "name": "1-512-500",
            "root_disk_gb": 500,
            "vcpu": 1
          }
        ],
        "groups": [
          {
            "group_id": 3,
            "name": "mcdonalds"
          }
        ],
        "mount_point_list":[
          {
            "mount_point":"/app",
            "mount_point_size":20,
            "mount_point_use":50,
            "mount_partition_name":"VGapp-LVapp",
            "mount_partition_type":"lvm"
          }
        ],
        "qemu-ga_update":True
	  }
    }

```
