# GET /group/init_info/<int:group_id>   应用组编辑功能时的接口


### URL parameter
| key | Requried | type | description | value |
|-----|----------|------|-------------|------


##response

```json
{
  "code": 0, 
  "data": {
    "all_area": [
      {
        "id": null,
        "name": null,
        "parent_id": 1,
        "parent_name": "\u603b\u533a"
      },
      {
        "id": 7,
        "name": "\u4e1c\u5317\u533a\u4e00\u533a",
        "parent_id": 6,
        "parent_name": "\u4e1c\u5317\u533a"
      }
    ],
    "used_area": [
      {
        "area_list": [
          {
            "children": [
              {
                "id": 15,
                "name": "\u534e\u5317\u533a\u56db\u533a"
              },
              {
                "id": 22,
                "name": "\u534e\u5317\u533a\u4e00\u533a"
            ],
            "parent_id": 2,
            "parent_name": "\u534e\u5317\u533a"
          }
        ],
        "cpu": 50,
        "disk": 500,
        "mem": 200,
        "name": "zongbu",
        "owner": "80002473",
        "role_id": 1,
        "vm": 10, 
        "p_cluster_id": "CMDB物理集群ID"
      }
    ]
  }, 
  "msg": "success"
}
```
