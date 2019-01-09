# GET /dashboard/v1 获取dashboard数据


## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": {
	    "dc_cpu": [
            {
            "dc_name": "机房名",
            "dc_type": "机房类型",
            "unused": "未使用 单位：核",
            "unused_per": "未使用百分比",
            "used": "已使用 单位：核",
            "used_per": "已使用百分比"
            }
         ],
         "dc_mem": [
            {
            "dc_name": "机房名",
            "dc_type": "机房类型",
            "unused": "未使用 单位：mb",
            "unused_per": "未使用百分比",
            "used": "已使用 单位：mb",
            "used_per": "已使用百分比"
            }
         ],
         "dc_vms": [
            {
            "all_vms": "总数",
            "dc_name": "机房名",
            "dc_type": "机房类型",
            "other_vms": "其他数",
            "shutdown_vms": "关机数",
            "startup_vms": "开机数"
            }
         ],
         "overview": {
            "area_nums": "区域数",
            "datacenter_nums": "机房数",
            "host_nums": "host数",
            "hostpool_nums": "集群数"
         }
        }
    }

```
