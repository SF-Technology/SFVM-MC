# POST  /area 新增区域


## 请求参数
| 参数 | 是否必须 | 类型 | 描述 | 
|-----|----------|------|-------------|-------|
| name   | 是| string| 区域名|
| manager   | 是| string| 管理员工号|
| parent_id   | 是| int| 父区域ID，如果没有父区域，则传-1|


## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": {}
    }

```
