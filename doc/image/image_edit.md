# PUT /image 新增镜像

## 请求参数
| 参数 | 是否必须 | 类型 | 描述 | 
|-----|----------|------|-------------|-------|
| image_id   | 是| int| 镜像ID|
| actual_size_mb  | 是| string| 镜像实际大小(MB)|
| size_gb   | 是| string| 镜像大小(GB)|
| md5   | 是| string| md5值|



## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": {}
    }
