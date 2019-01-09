# POST  /group

添加用户组，这个页面还需要调用#GET /user_group/init_area接口


### URL parameter
| key | Requried | type | description |
|-----|----------|------|-------------|
| owner  | Y | int | 用户ID|
| role_id  | Y | int    | 角色id|
| name  | Y | string    | 应用组名称|
| area_str  | Y | string    | 全部区域的id,格式"10,11,12,13"|
| cpu| Y| int| 应用组cup配额 如 2000 |
| mem| Y| int| 应用组mem配额 如 2000 |
| disk| Y| int| 应用组disk配额 如 2000 |
| vm| Y| int| 应用组vm配额 如 2000 |
| p_cluster_id| N| int| CMDB中物理集群ID|  



##response

```json

{
  "code": 0,
  "data": null,
  "msg": "success"
}

```
