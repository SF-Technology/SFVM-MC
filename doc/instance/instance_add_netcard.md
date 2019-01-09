# POST /instance/configure/netcard/<int:instance_id>  虚拟机新增一块网卡，虚拟机最大网卡数量为3



## 请求参数
| 参数 | 是否必须 | 类型 | 描述 | 
|-----|----------|------|-------------|-------|
| instance_id   | 是| int| 虚拟机ID|


## 成功返回
```json

	{
	  "msg": "虚拟机网卡创建成功",
	  "code": 0,
	  "data": []
    }

```


## 失败返回
```json

	{
	  "msg": "无法找到待添加网卡虚拟机",
	  "code": -10002,
	  "data": []
    }

```