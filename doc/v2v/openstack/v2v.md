# POST /v2v/openstack/<int:hostpool_id>


## 请求参数
| 参数 | 是否必须 | 类型 | 描述 |
|-----|----------|------|-------------|-------|
| hostpool_id   | 是| string| 集群ID|
| flavor_id   | 是| string| flavor ID|
| vm_app_info   | 是| string| 应用信息 |
| group_id   | 是| string| 组ID|
| vm_owner   | 是| string| 应用管理员 |
| vm_ostype   | 是| string| 操作系统类型 |
| cloud_area   | 是| string| openstack环境 |
| segment   | 是| int| vm所在网段 |
| vm_name   | 是| string| 虚拟机名称 |
| vm_ip   | 是| string| 虚拟机IP |
| retry   | 是| string| 是否重试() |
| user_id   | 是| string| 用户id |



## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": {}
    }

```
