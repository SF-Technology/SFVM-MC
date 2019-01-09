# POST /feedback/add 创建用户反馈内容


## 请求参数
| 参数 | 是否必须 | 类型 | 描述 |
|-----|----------|------|-------------|-------|
| user_id   | 是| int| 用户工号|
| problem_id  | 是| int| 问题类型的ID值|
| problem_description   | 是| string| 问题描述|
| network_address   | 是| string| 相关页面的网址|



## 返回参数
```json

	{
      "code": 0, 
      "data": null, 
      "msg": "success"
    }

```