# GET /group/list

应用组列表

### URL parameter
| key | Requried | type | description | value |
|-----|----------|------|-------------|------
| userid| Y| string| 用户账户| 如 062076 |
| search| Y| dict| search字段| 如 {"owner":"01223805"} 或者{"group_name":"111"}|

##response

```json

 {
  "code": 0, 
  "data": {
    "rows": [
      {
        "cpu": 50, 
        "disk": 500, 
        "group_id": 85, 
        "mem": 200, 
        "name": "5rrr5", 
        "owner": "01190200", 
        "role_id": 2, 
        "vm": 10
      }
    ], 
    "total": 3
  }, 
  "msg": "success"
}

```
