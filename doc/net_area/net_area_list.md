# GET /net_area/list   获取网络区域列表


### URL parameter
| key | Requried | type | description | value |
|-----|----------|------|-------------|------
| page_size   | 否| int| 每页多少条 默认20|
| page_no   | 否| int| 当前的页码 默认第一页|

##response

```json

{
  "code": 0, 
  "data": {
    "rows": [
      {
        "datacenter_name": "机房名",
        "dc_type": "机房类型",
        "hostpool_nums": "集群数量", 
        "net_area_id": "网络区域ID", 
        "net_area_name": "网络区域名"
      }
    ], 
    "total": 2
  }, 
  "msg": "success"
}
```
