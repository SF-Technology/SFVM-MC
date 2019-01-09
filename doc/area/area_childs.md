# GET  /area/child/<int:area_id> 获取区域的子区域信息


## 请求参数
| 参数 | 是否必须 | 类型 | 描述 | 
|-----|----------|------|-------------|-------|
| area_id   | 是| int| 区域ID|


## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": [
        {
            "child_id": "子区域ID", 
            "child_name": "子区域名",
            "datacenter_nums": "机房数量",
            "manager": "管理员"
        }
      ] 
    }

```
