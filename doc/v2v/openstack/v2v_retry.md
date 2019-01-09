# PUT /v2v/openstack/retry 虚拟机列表


## 请求参数
| 参数 | 是否必须 | 类型 | 描述 |
|-----|----------|------|-------------|-------|
| request_id   | 是| string| 任务ID |
| retry   | 是| string| 任务是否取消，1为重试，0为不重试 |





## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0

    }

```

