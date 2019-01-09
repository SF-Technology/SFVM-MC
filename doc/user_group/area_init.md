# GET /user_group/init_area

添加用户至组中时的区域选择初始化信息

## Request parameters

需要先登陆，登陆态中会带有cookie

### URL parameter
| key | Requried | type | description | value |
|-----|----------|------|-------------|------



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
        "id": 1, 
        "name": "344ll", 
        "parent_id": 2, 
        "parent_name": "testzs"
      }, 
      { "id": null, 
        "name": null,
        "parent_id": 2, 
        "parent_name": "testzs"
      }, 
    "total": 2
  }, 
  "msg": "success"
}

```
