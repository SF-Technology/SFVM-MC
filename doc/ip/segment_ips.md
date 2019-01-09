# GET segment/<int:segment_id>/<int:page> 获取指定网段下所有IP地址


## 请求参数
| 参数 | 是否必须 | 类型 | 描述 | 
|-----|----------|------|-------------|-------|
| segment_id   | 是| int| 网段ID|
| page   | 是| int| 当前的页码 默认第一页|


## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": {
            "ips": [
                    {
                      "id": "IP ID",
                      "ip_address": " IP地址",
                      "net_area": "网络区域名",
                      "netmask": "网络掩码",
                      "segment": "网段",
                      "status": "1  状态，0表示未使用，1表示已使用，2表示已保留"
                     }
            ],
            "len": 512,
            "segment_id": 1,
            "segment": "192.168.1.0", 
            "netmask": "23",
            "pages": 2  
       }
    }

```
