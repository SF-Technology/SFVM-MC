# GET hostpool/<int:hostpool_id>/monitor 集群监控


## 请求参数
| 参数 | 是否必须 | 类型 | 描述 | 
|-----|----------|------|-------------|-------|
| hostpool_id   | 是| int| 集群ID|
| start_time  | 是| int| 开始时间|
| end_time   | 是| int| 结束时间|



## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": [
        [
          [
            "1493119644  # 时间戳", 
            "3.0  # 监控值"
          ],
        ]
      ]
    }

```
