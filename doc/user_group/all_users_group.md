# GET /user_group/<int:group_id>

应用组中组下所有的用户列表

## Request parameters

需要先登陆，登陆态中会带有cookie

### URL parameter
| key | Requried | type | description | value |
|-----|----------|------|-------------|------
| group_id| Y| string| 应用组id| 如 1 |




## Response Body Json

| key | Requried | type | description |
|-----|----------|------|-------------|
| code   | y    | number| 返回码|
| data   | y    | object| 信息|
| msg   | y    | object|  消息说明|



##response

```json
{
  "code": 0, 
  "data": {
    "rows": [
      {

        "user_id": "01225002", 
        "user_name": "\u738b\u541b\u54f2"
      }, 
      {
        "user_id": "01223805", 
        "user_name": "\u949f\u8212"
      }
    ], 
    "total": 2
  }, 
  "msg": "success"
}
```
