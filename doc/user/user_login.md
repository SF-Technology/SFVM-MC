# POST /login

登录 用户

## Request parameters

需要先登陆，登陆态中会带有cookie

### URL parameter
| key | Requried | type | description | value |
|-----|----------|------|-------------|------
| userid| Y| string| 用户账户| 如 062076 |
| password | Y| string| 用户密码| password |



## Response Body Json

| key | Requried | type | description |
|-----|----------|------|-------------|
| code   | y    | number| 返回码|
| data   | y    | object| 信息|
| msg   | y    | object|  消息说明|



##response

```json

    {
      "msg": "success",
      "code": 0,
      "data": None
    }

```
