# UPDATE  /user_group/<int:group_id>

更新应用组中的过期时间

## Request parameters

需要先登陆，登陆态中会带有cookie

### URL parameter
| key | Requried | type | description |
|-----|----------|------|-------------|
| user_id   | y    | number| 用户id|
| group_id   | y    | object|  用户组id|


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
