# POST hostpool/<int:net_area_id> 新增集群


## 请求参数
| 参数 | 是否必须 | 类型 | 描述 | 
|-----|----------|------|-------------|-------|
| net_area_id   | 是| int| 网络区域ID|
| name  | 是| string| 集群名|
| least_host_num   | 是| int| Host数量下限|



## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": {}
    }

```
