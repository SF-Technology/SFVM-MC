# POST /segment/add 添加一个网段到网络区域中


## 请求参数
| 参数 | 是否必须 | 类型 | 描述 | 
|-----|----------|------|-------------|-------|
| net_area_id   | 是| int| 网络区域ID|
| segment   | 是| string| 用户要录入网段，如：192.168.1.0|
| segment_type   | 是| string| 网段类型，目前只提供两种，'0'代表内网，'4'代表NAS网|
| netmask   | 是| string| 子网掩码，16到28之间的数字|
| vlan   | 是| string| vlan，如66|
| gateway   | 是| string| 网关，如：192.168.1.254|
| dns1   | 是| string| dns服务器1，如：8.8.8.8.8|
| dns2   | 是| string| dns服务器2，如：4.4.4.4|


## 返回参数
```json
{
  "code": -10000, 
  "data": null, 
  "msg": "\u6307\u5b9a\u7f51\u6bb5\u5df2\u5b58\u5728\u4e8e\u6307\u5b9a\u7f51\u7edc\u533a\u57df\u4e0b\uff0c\u8bf7\u91cd\u65b0\u786e\u8ba4"
}

```
