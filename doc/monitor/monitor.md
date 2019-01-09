# POST  /monitor Balent监控


## 请求参数
| 参数 | 是否必须 | 类型 | 描述 | 
|-----|----------|------|-------------|-------|
| ip_list   | 是| string| 监控IP列表，格式：[{ip1:[m1,m2,m3,m4]},{ip2:[m1,m2,m3,m4]},{ip3:[]}]|
| start_time   | 是| datetime| 开始时间，格式：|
| end_time   | 是| datetime| 结束时间，格式：|

## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": {}
    }

```
