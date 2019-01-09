# GET  /net_area/levelinfo 获取网络区域以上的层级关系  区域 - 子区域 - 机房 - 网络区域


## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": {
        "level_info": [
            {
                "area": "区域名",
                "child_area": "子区域名，若无，则为null",
                "datacenter": "机房名",
                "dc_type": "机房类型",
                "net_area_id": "网络区域ID",
                "net_area_name": "网络区域名"
            }
        ]
      }

```
