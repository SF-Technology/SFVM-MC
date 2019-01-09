# GET /instance/info/<int:instance_id> 获取虚拟机详情


## 请求参数
| 参数 | 是否必须 | 类型 | 描述 | 
|-----|----------|------|-------------|-------|
| instance_id  | 是| int| 虚拟机ID|


## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": {
            "app_info": "应用系统信息", 
            "cpu": "cpu", 
            "dc_type": "环境类型", 
            "disk_gb": "数据盘容量", 
            "group_name": "应用组", 
            "image_name": "使用模板", 
            "instance_name": "实例名", 
            "ip_address": "IP地址", 
            "memory_mb": "内存", 
            "net_area": "网络区域", 
            "owner": "应用管理员", 
            "root_disk_gb": "系统盘容量", 
            "sys_version": "操作系统版本", 
            "system": "主机类型", 
            "uuid": "UUID"
        },
    }

```
