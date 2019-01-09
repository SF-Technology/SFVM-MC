# POST  /datacenter/<int:area_id> 新增机房


## 请求参数
| 参数 | 是否必须 | 类型 | 描述 | 
|-----|----------|------|-------------|-------|
| area_id   | 是| int| 区域ID|
| name   | 是| string| 机房名|
| province   | 是| string| 所在省份|
| address   | 是| string| 地址|
| description   | 是| string| 描述|
| dc_type   | 是| int| 机房类型 1:测试SIT 2:准生产STG 3:研发DEV 4:生产PRD 5:容灾DR 0:其他|


## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": {}
    }

```
