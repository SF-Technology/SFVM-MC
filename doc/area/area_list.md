# GET /area/list 区域列表


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
	    "total": "7  #总共有多少条数据，用于显示总数，和计算分页用",               
	    "rows": [
            {
                "area_id": 16,
                "child_areas_nums": "子区域数量",
                "datacenter_nums": "机房数量",
                "displayname": "区域名",
                "host_nums": "host数量",
                "host_run_nums": "host运行中数量",
                "hostpool_nums": "集群数量",
                "instance_nums": "vm数量",
                "instance_run_nums": "vm运行中数量",
                "manager": "管理员"
            }
        ]
      }
    }
```
