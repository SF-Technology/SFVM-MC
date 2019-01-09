list_get = [
    {"vmname":"v1","group_id":"1"},
    {"vmname":"v2","group_id":"1"},
    {"vmname":"v3","group_id":"2"},
    {"vmname":"v4","group_id":"3"},
    {"vmname":"v5","group_id":"3"},
    {"vmname":"v6","group_id":"3"}
]
list_value = []
for list in list_get:
    list_value.append(list['group_id'])
for value in list_value:
    while list_value.count(value) > 1:
        del list_value[list_value.index(value)]

n = len(list_value)

list = [
    [],[],[],[],[],[],[],[],[],[]
]
return_list = []

num = 0
for v in list_value:
    v_str = str(v)
    for task_info in list_get:
        if task_info['group_id'] == v_str:
            list[num].append(task_info)
    return_list.append(list[num])
    num = num + 1

print return_list






