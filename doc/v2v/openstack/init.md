# GET v2v/openstack/init 获取v2v openstack 虚拟机所需的数据

## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": {
	    "area": [  # 区域层级
	        {
	            "hostpool_id": "集群ID",
                "hostpool_name": "集群名",
                "net_area_name": "网络区域名",
                "dc_type": "机房类型 1:测试SIT、2:准生产STG、3:研发DEV"
	        }
	    ],
	    "flavors": [   # 规格列表
            {
                "flavor_id": 1,
                "memory_mb": 1,
                "name": "1c1g",
                "root_disk_mb": 500,******暂不使用******
                "vcpu": 1
            }
        ],
        "groups": [  # 组列表
            {
                "displayname": "组名",
                "group_id": "组ID"，
                "owner": "所属管理员 ******暂不使用******"
            }
         ]
    }

```
