# GET /instance/migrate/init/<int:instance_id> 虚机迁移时获取目标主机及其他信息


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
	    "host_list": [
            {
                "current_cpu_used": "当前CPU使用率",
                "current_mem_used": "当前内存使用率",
                "free_disk_space": "剩余磁盘 单位：MB",
                "host_id": "host ID",
                "host_name": "host名"
            }
        ],
        "instance_cpu": "CPU",
        "instance_disk": "磁盘",
        "instance_ip": "IP",
        "instance_mem": "内存",
        "instance_name": "实例名",
        "instance_status": "状态"
	  }
    }

```
