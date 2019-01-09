# GET /user/list

用户列表

## Request parameters

需要先登陆，登陆态中会带有cookie

### URL parameter
| key | Requried | type | description | value |
|-----|----------|------|-------------|------
| page_size   | 否| int| 每页多少条 默认20|
| page_no   | 否| int| 当前的页码 默认第一页|
| search | 否 | string| json 见下文 |




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
        "user_id": "01223805"
      },
      {
        "user_id": "062076"
      }
    ],
    "total": 2
  },
  "msg": "success"
}

```
