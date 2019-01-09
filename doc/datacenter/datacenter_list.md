# GET /datacenter/list 机房列表


## 请求参数
| 参数 | 是否必须 | 类型 | 描述 | 
|-----|----------|------|-------------|-------|
| page_size   | 否| int| 每页多少条 默认20|
| page_no   | 否| int| 当前的页码 默认第一页|


## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": {
	    "total": 7,            #总共有多少条数据，用于显示总数，和计算分页用
	    "rows": [
            {
                "datacenter_id": "机房ID",
                "dc_type": "机房类型 1:测试SIT 2:准生产STG 3:研发DEV 4:生产PRD 5:容灾DR 0:其他",
                "displayname": "机房名",
                "hostpool_nums": "集群数量"
            },
        ]

```
