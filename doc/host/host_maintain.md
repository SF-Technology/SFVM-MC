# PUT /host/maintain/<int:host_id> 维护/结束维护物理机


## 请求参数
| 参数 | 是否必须 | 类型 | 描述 | 
|-----|----------|------|-------------|-------|
| host_id   | 是| int| 物理机ID|
| flag   | 是| string| 操作，2：维护  0：结束维护|


## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": {}
    }

```
