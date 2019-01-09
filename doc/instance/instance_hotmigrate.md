# PUT /instance/hotmigrate/<int:instance_id>/to/<int:host_id> 虚机热迁移


## 请求参数
| 参数 | 是否必须 | 类型 | 描述 | 
|-----|----------|------|-------------|-------|
| instance_id   | 是| int| 虚拟机ID|
| host_id   | 是| int| 目标主机ID|
| speed_limit   | 是| int| 迁移速度|



## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": {}
    }

```
