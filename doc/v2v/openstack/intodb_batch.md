# POST /v2v/openstack/batch


## 请求参数
| 参数 | 是否必须 | 类型 | 描述 |
|-----|----------|------|-------------|-------|
| openstack_batch   | 是| list| openstack_task清单|




## 返回参数
```json

	{
        'success_num':success_num,         #成功数量
        'fail_num':err_num,             #失败数量
        'error_info':error_info              #错误详细信息
    }
```
其中 error_info 格式如下
[
{
 'vm_name':vm1,
 'error_message':message1
},
{
 'vm_name':vm2,
 'error_message':message2
}
]