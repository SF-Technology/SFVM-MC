# POST ip/apply 单独申请IP


## 请求参数
| 参数 | 是否必须 | 类型 | 描述 | 
|-----|----------|------|-------------|-------|
| datacenter   | 是| string| 机房名称，如：host-SIT|
| env   | 是| string| 环境类型，如：SIT|
| net_area   | 是| string| 网络区域，如：DCN1|
| segment   | 是| string| 网段，如：192.168.1.0|
| cluster_id| 是| string| 物理集群id，和cmdb保持一致，纯数字的|
| service_id| 是| string| 应用集群id，和cmdb保持一致，纯数字的|
| service_ha| 是| string| 应用服务HA软件，和cmdb保持一致，如：HAPROXY|
| sys_code| 是| string| 系统编码，和cmdb保持一致，如：sas-core|
| opUser| 是| string| 申请用户账号：如01198773|



## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": {
          "vip": "192.168.1.33"
       }
    }

```