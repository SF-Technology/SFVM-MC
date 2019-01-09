# GET /hostpool/levelinfo 获取集群以上的层级关系  机房 - 网络区域 - 集群


## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": [
            {
                "dc_type": "机房类型",
                "datacenter": "机房名",
                "hostpool": "集群名",
                "hostpool_id": "集群ID",
                "net_area": "网络区域名"
            }
        ]
    }

```
