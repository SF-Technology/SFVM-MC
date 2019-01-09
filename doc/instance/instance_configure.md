# PUT /instance/configure/<int:instance_id> 修改配置


## 请求参数
| 参数 | 是否必须 | 类型 | 描述 | 
|-----|----------|------|-------------|-------|
| instance_id   | 是| int| 虚拟机ID|
| flavor_id   | 是| int| 新flavor ID|
| disk_gb_list   | 是| list| 新数据盘，[{"mount_point":"/app", "size_gb":100}]|
| app_info   | 是| string| 新应用系统信息|
| owner   | 是| string| 新管理员姓名|
| group_id   | 是| int| 新组ID|
| net_status_list   | 是| list| 虚拟机网卡状态，[{"ip_addr":"192.168.1.1", "ip_addr_new":"192.168.1.2", "vlan_new":"35", "mac_addr":"52:54:00:4c:17:18", "nic_status":"1", "ip_type":"0"}]，ip没有修改ip_addr_new字段为空，否则值为新ip地址，同时vlan_new为新ip的vlan值。ip_type取值：网段类型，0为内网，1为外网电信，2为外网联通，3为镜像模板机使用，4为内网NAS网段|
| extend_list   | 是| list| 扩展磁盘信息，[{"mount_point":"/app", "mount_point_size":100,"mount_point_use":50,"mount_partition_name":"VGapp-LVapp","mount_partition_type":"lvm","mount_extend_size":50}]|
|qemu_ga_update   | 是|boolean | qemu是否更新成功


## 返回参数
```json

	{
	  "msg": "success",
	  "code": 0,
	  "data": {}
    }

```
