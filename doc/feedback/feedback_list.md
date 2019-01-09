# GET /feedback/list 查询历史反馈记录


## 请求参数
| 参数 | 是否必须 | 类型 | 描述 | 
|-----|----------|------|-------------|-------|
| user_id   | 是| int| 用于获取该用户的历史反馈记录|




## 返回参数

```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": {
	    "rows": [
      {
        "network_address": "相关页面的网址", 
        "problem_description": "问题描述", 
        "submit_time": "提交反馈的时间"
      }
    ], 
    "total": 1
    }
    }

```