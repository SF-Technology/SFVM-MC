# GET /dashboard/v2 获取dashboard数据


## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": {
	    "info_list": [
            {
                "cpu_used": "已使用CPU",
                "mem_used": "已使用MEM",
                "disk_used": "已使用DISK",
                "vm_used": "已使用VM",
                "cpu_all": "总CPU",
                "mem_all": "总MEM",
                "disk_all": "总DISK",
                "cpu_usable_per": "cpu可使用百分比",
                "disk_usable_per": "disk可使用百分比",
                "mem_usable_per": "mem可使用百分比",
                "group_name": "应用组名",
                "all_vms": "总VM数",
                "running_vms": "运行中VM数",
                "stop_vms": "已停止VM数",
                "vm_usable_per": "VM可使用百分比"
            }
        ]
      }
    }

```
