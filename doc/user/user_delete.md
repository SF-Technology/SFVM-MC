# DELETE /user

某个用户添加删除标签

## Request parameters

需要先登陆，登陆态中会带有cookie

### URL parameter
| key | Requried | type | description | value |
|-----|----------|------|-------------|------
| userid| Y| string| 用户账户| 如 062076 |
| where_field| Y| string| 是否删除|  isdeleted |
| where_field_value| Y| string| 删除| 如 1表示已删除，0表示可用|





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
