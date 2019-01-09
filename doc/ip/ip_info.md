# GET ip/info 获取已使用的IP的分配信息


## 请求参数
| 参数 | 是否必须 | 类型 | 描述 | 
|-----|----------|------|-------------|-------|
| ip_address   | 是|string| IP地址|


## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": {
        "datacenter": "机房名", 
        "gateway": "网关", 
        "instance_name": "虚机名，ip为虚拟机ip才做展示", 
        "ip_address": "IP地址", 
        "net_area": "网络区域名", 
        "netmask": "子网掩码", 
        "vlan": "VLAN",
        "sys_code": "系统编码,vip时才做展示",
        "is_vip": "0,0表示虚拟机ip，1表示vip" 
       }
    }

```
