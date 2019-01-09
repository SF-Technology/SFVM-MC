
权限格式：
0：表示没有该权限
1：表示有该权限

{
    "instance":{
        "create":0, # 创建
        "delete":0, # 删除
        "shutdomn":0,  # 关机
        "startup":0,   # 开机
        "reboot":0,   # 重启
        "configure":0,   # 修改配置
        "console":1,   # 控制台
         "migrate": 0, #  热迁移
         "cold_migrate": 0, # 冷迁移
    },
    "host":{
        "add":1, # 创建
        "delete":0,  # 删除
        "lock":0,   # 锁定
        "unlock":1,  # 解除锁定
        "maintain":0,   # 维护
        "unmaintain":1,  # 结束维护
        "start":0,   # 开机
        "stop":0,   # 关机
        "softstop":0,   # 软关机
        "reset":0,   # 重启
        "softreset":0,   # 软重启
        "console":1,  # 控制台            
    }
}