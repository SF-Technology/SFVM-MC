# GET /user/info

获取某个用户的详细信息

## Request parameters

需要先登陆，登陆态中会带有cookie

### URL parameter
| key | Requried | type | description | value |
|-----|----------|------|-------------|------
| userid| Y| string| 用户账户| 如 01223805 |






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
        "isdeleted": "0",
        "status": 1,
        "user_id": "01223805",
        "user_name": "\u949f\u8212"
      }
    ]
  },
  "msg": "success"
}

```
