# GET /v2v/openstack/list 虚拟机列表


## 请求参数
| 参数 | 是否必须 | 类型 | 描述 |
|-----|----------|------|-------------|-------|
| page_size   | 是| string| 每页多少条 |
| page_no   | 是| string| 当前的页码 |
| user_id | 是 | string| 用户的user_id |
| superadmin | 是 | string| 如果为超级管理机,入参为'1';其他角色入参为'0' |




## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": {
	    "total": 7,            #总共有多少条数据，用于显示总数，和计算分页用
	    "rows": [
	        vm_ip,  #VMIP
	        request_id, #任务ID
	        start_time, #开始时间
	        finish_time,    #结束时间
	        status, #任务状态
	        step_done,  #任务进程
	        user_id #操作者
	    ]
    }

#任务进度说明：
第一步:"create_destination_dir"
第二步:"get_vm_file"
第三步:"copy_vm_disk_to_desthost"
第四步:"copy_vm_xml_to_desthost"
第五步:"standardlize_target_vm"
第六步:"define_target_vm"
第七步:"start_target_vm"
第八步:"inject_vm_ip_configuration"
```

