# GET instance/list 虚拟机列表


## 请求参数
| 参数 | 是否必须 | 类型 | 描述 | 
|-----|----------|------|-------------|-------|
| page_size   | 否| int| 每页多少条 默认20|
| page_no   | 否| int| 当前的页码 默认第一页|
| search | 否 | string| json 见下文 |


## search  json格式  可任选一个或者多个
```json
	{
		"name": "主机名  模糊匹配",
		"uuid": "虚拟机的UUID  模糊匹配",
		"ip_address": "VM IP  模糊匹配",
		"host_ip": "host IP 模糊匹配",
		"status": "状态 精确匹配",
		"owner": "应用管理员 模糊匹配",
		"group_name": "所属应用组 模糊匹配"
	}
```


## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": {
	    "total": 7,            #总共有多少条数据，用于显示总数，和计算分页用
	    "rows": [
	        instance_id,
            hostname,
            displayname,
            status,
            typestatus,
            ip_address,
            hostpool,
            hostip,
	    ]
    }

```
