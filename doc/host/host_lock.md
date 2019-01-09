# PUT /host/lock/<int:host_id> 锁定/解除锁定物理机


## 请求参数
| 参数 | 是否必须 | 类型 | 描述 | 
|-----|----------|------|-------------|-------|
| host_id   | 是| int| 物理机ID|
| flag   | 是| string| 操作，1：锁定  0：解除锁定|


## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": {}
    }

```
