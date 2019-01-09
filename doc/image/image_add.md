# POST /image 新增镜像


## 请求参数
| 参数 | 是否必须 | 类型 | 描述 | 
|-----|----------|------|-------------|-------|
| name  | 是| string| 镜像名|
| displayname   | 是| string| 镜像显示名|
| system   | 是| string| 操作系统|
| version   | 是| string| 系统版本|
| description   | 是| string| 描述|
| md5   | 是| string| 描述|
| format   | 是| string| 格式|
| actual_size_mb   | 是| string| 镜像实际大小(MB)|
| size_gb   | 是| string| 镜像大小(GB)|
| url   | 是| string| 镜像url地址|
| type   | 是| string| 镜像类型|  #'0':系统盘;'1':数据盘


## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": {}
	}

```
