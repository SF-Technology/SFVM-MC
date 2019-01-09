# POST /instance/clone/<int:instance_id> 虚机克隆


## 请求参数
| 参数 | 是否必须 | 类型 | 描述 | 
|-----|----------|------|-------------|-------|
| instance_id   | 是| int| 虚拟机ID|
| instance_newname   | 是| string| 虚拟机名|
| apiOrigin   | 是| string| 克隆来源，kvm平台默认为"self"|


## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": {}
    }

```
