# PUT /user

更新某个用户信息

## Request parameters

需要先登陆，登陆态中会带有cookie

### URL parameter
| key | Requried | type | description | value |
|-----|----------|------|-------------|------
| userid| Y| string| 用户账户| 如 062076 |
| where_field| Y| string| 用户表中的列名| 如 email |
| where_field_value| Y| string| 用户表中列的值| 如 1234567@qq.com|





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
  "data": null,
  "msg": "success"
}

```
