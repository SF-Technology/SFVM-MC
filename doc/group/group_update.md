# PUT /group/<group_id>

更新某个应用组信息

## Request parameters

需要先登陆，登陆态中会带有cookie

### URL parameter
| key | Requried | type | description | value |
|-----|----------|------|-------------|------
| owner  | Y | int | 用户ID|
| name| Y| string| 应用组名| 如 数据中心管理员组 |
| role_id| Y| int| 角色id| 如 1 |
| area_str| Y| string| 区域id| 如 "2,3,4,5" |
| cpu| Y| int| 应用组cup配额| 如 2000 |
| mem| Y| int| 应用组mem配额| 如 2000 |
| disk| Y| int| 应用组disk配额| 如 2000 |
| vm| Y| int| 应用组vm配额| 如 2000 |





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
