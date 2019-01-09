# POST  /user

添加应用组信息

## Request parameters

需要先登陆，登陆态中会带有cookie

### URL parameter
| key | Requried | type | description | value |
|-----|------|--------|-------------|------
| name| Y| string| 组名称| 如 administors |
| displayname| Y| string| 组显示名| 如 超级系统管理员组 |
| description| Y| string| 组描述| 如 拥有kvm管理平台的所有权限 |





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
