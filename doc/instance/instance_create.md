# POST instance/hostpool/<int:hostpool_id> 创建虚拟机


## 请求参数
| 参数 | 是否必须 | 类型 | 描述 | 
|-----|----------|------|-------------|-------|
| hostpool_id   | 是| int| 集群ID|
| image_name   | 是| string| 镜像名 |
| flavor_id   | 是| int| flavor ID|
| disk_gb   | 是| int| 数据盘容量|
| count   | 是| int| 创建虚拟机数量 |
| app_info   | 是| string| 应用信息 |
| group_id   | 是| int| 组ID|
| owner   | 是| string| 应用管理员 |
| password   | 是| string| 管理员密码 |


## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": {}
    }

```
