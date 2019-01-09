# GET instance/init 获取创建虚拟机所需的数据

## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": {
	    "area_DQ": [  // 区域层级 - 地区
	        {
	            "area_name": "区域名",
                "child_area_name": "子区域名，如果没有子区域，则为null",
                "datacenter_name": "机房名",
                "dc_type": "机房类型",
                "hostpool_id": "集群ID",
                "hostpool_name": "集群名",
                "net_area_name": "网络区域名"
	        }
	    ],
	    "area_ZB": [  // 区域层级 - 总部
	        {
	            "hostpool_id": "集群ID",
                "hostpool_name": "集群名",
                "net_area_name": "网络区域名",
                "dc_type": "机房类型 0:其他、1:测试SIT、2:准生产STG、3:研发DEV、4:生产PRD、5:容灾DR"
	        }
	    ],
	    "flavors": [   // 规格列表
            {
                "flavor_id": 1,
                "memory_mb": 1,
                "name": "1c1g",
                "root_disk_mb": 500,
                "vcpu": 1
            }
        ],
        "images_linux": [   // 镜像列表 - linux
            {
                "image_id": "镜像ID",
                "name": "centos7.2  镜像名"
                "displayname": "Centos7.2纯净模板  显示名  ******镜像列表的下拉格式 eg: Centos7.2纯净模板(centos7.2)******"
            }
        ],
        "images_windows": [   // 镜像列表 - windows
            {
                "image_id": "镜像ID",
                "name": "镜像名",
                "displayname": "显示名"    
            }
        ],
        "groups": [  // 组列表
            {
                "displayname": "组名",
                "group_id": "组ID",
                "owner": "所属管理员 ******暂不使用******"
            }
         ]
    }

```
