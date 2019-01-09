# POST /host/<int:hostpool_id> 新增物理机


## 请求参数
| 参数 | 是否必须 | 类型 | 描述 | 
|-----|----------|------|-------------|-------|
| hostpool_id   | 是| int| 集群ID|
| name   | 否| string| 物理机名|
| sn   | 是| string| 序列号|
| ip_address   | 是| string| IP地址|
| hold_mem_gb   | 是| int| 保留内存|
| manage_ip   | 否| string| 管理IP|


## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": {}
    }

```
