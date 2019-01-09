# GET hostpool/list 集群列表


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
                "datacenter": "机房名", 
                "displayname": "集群名", 
                "hostpool_id": "集群ID", 
                "hosts_nums": "host数量", 
                "instances_nums": "vm数量", 
                "net_area": "网络区域名",
                "area": "区域名",
                "cpu_nums": "cpu数量",
                "mem_nums": "mem总量",
                "mem_assign": "已分配内存",
                "mem_assign_per": "已分配内存百分比",
                "cpu_used_per": "cpu使用率",
                "mem_used_per": "mem使用率"
            },
         ]
    }

```
