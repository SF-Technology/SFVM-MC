# POST  /user_group/outuser/<int:group_id>

添加外部用户到某个组中

## Request parameters

需要先登陆，登陆态中会带有cookie

### URL parameter
| key | Requried | type | description |
|-----|----------|------|-------------|
| user_id   | y    | number| 用户id|
| user_name   | y    | string|  用户名|
| password   | y    | string|  用户密码|
| group_id   | y    | number|  用户组id|
| group_name   | y    | string|  用户组名|
| auth_type   | y    | number| 用户类型，麦当劳为1|
| email   | y    | string| sdffsd@afds.com|

## Response Body Json

| key | Requried | type | description |说明 |
|-----|----------|------|-------------|-------------|
| code   | y    | number| 返回码|0:成功；-10000:系统错误；|
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
