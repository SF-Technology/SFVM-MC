/**
 * Created by 80002473 on 2017/5/2.
 */
var TableFun = function () {
};
var OpenstackFun = function () {
};
var EsxFun = function () {
};

function DoOnMsoNumberFormat(cell, row, col) {
    var result = "";
    if (row > 0 && col == 0)
        result = "\\@";
    return result;
}
var length_export;
function inittable() {
    deg = 1;
    $('#migrateTable').bootstrapTable({
        url: '/v2v/list', // 接口 URL 地址
        method: 'get',
        dataType: "json",
        uniqueId: "id", //删除时能用到 removeByUniqueId
        showExport: true,//显示导出按钮
        exportDataType: "all",//导出类型
        exportTypes: ['all'],  //导出文件类型
        exportOptions: {
            ignoreColumn: [0, 10],  //忽略某一列的索引
            fileName: '迁移信息',  //文件名称设置
            worksheetName: 'sheet1',  //表格工作区名称
            tableName: '迁移详情',
            //excelstyles: ['background-color', 'color', 'font-size', 'font-weight'],
            onMsoNumberFormat: DoOnMsoNumberFormat
        },
        queryParamsType: "search",
        detailView: false,
        showRefresh: false,
        contentType: "application/x-www-form-urlencoded",
        pagination: true,
        //maintainSelected: true,
        pageList: [10,20, 50,100, "all"],
        pageSize: 10,
        pageNumber: 1,
        //search: true, //不显示全表模糊搜索框
        showColumns: false, //不显示下拉框（选择显示的列）
        sidePagination: "server", //服务端请求
        checkboxHeader: true,
        clickToSelect: false,
        singleSelect: false,
        //maintainSelected: true,
        onBeforeLoadParams: {}, //查询参数设置，供导出使用，在search_form.js里赋值
        //toolbar: '#mybar',
        sortable: false,
        responseHandler: function (res) {
            TableFun.export_data = res.data.rows;
            if (res.code == 0) {
                return res.data;
            } else {
                return {rows: [], total: 0, deg: 1};
            }
        },
        queryParams: function (q) {
            var searchContent = q.searchText;
            var key = '';
            var superadmin;
//                key = isIP(searchContent) ? JSON.stringify({'ip': searchContent}) : JSON.stringify({'name': searchContent})
            role_id_arr.indexOf(1) != -1 ? superadmin = 1 : superadmin = 0;
            return {
                //"sortName" : q.sortName,
                //"sortOrder" : q.sortOrder,
                "page_size": q.pageSize,
                "page_no": q.pageNumber,
                "user_id": user_id_num,
                "superadmin": superadmin
            };
        },
        onLoadSuccess: function (data) {
             rowCount = data.length - 1;
            $("#migrateTable").bootstrapTable('hideRow', {index: rowCount});
            $("#migrateTable td").attr("data-tableexport-msonumberformat", "\@");
            $("#migrateTable tr").attr("data-tableexport-display", "always");

            if (data.deg != 1) {
                var list = data.rows;
                length_export = list.length;
                list.forEach(function (tmp, index) {
                    if (tmp.status != "1") {
                        TableFun.judgeStatu();
                    }
                });

            }
        },
        onClickCell: function (field, value, row, $element) {

        },
        onPageChange: function (number, size) {  //表格翻页事件
            $("#migrateTable").bootstrapTable('hideRow', {index: rowCount});
            $("#migrateTable td").attr("data-tableexport-msonumberformat", "\@");
            $("#migrateTable tr").attr("data-tableexport-display", "always");
        },
        onCheckAll: function () {
            TableFun.judgeStatu();
        },
        onUncheckAll: function () {
            TableFun.judgeStatu();
        },
        onCheck: function () {
            TableFun.judgeStatu();
        },
        onUncheck: function () {
            TableFun.judgeStatu();
        },
        columns: [{ // 列设置
            field: 'state',
            checkbox: true, // 使用复选框
            align: "center",
            valign: "middle"
        },
            {
                title: "VMIP",
                field: "vm_ip",
                align: "center",
                valign: "middle",
            },
            {
                title: "任务ID",
                field: "request_id",
                align: "center",
                valign: "middle",
            },
            {
                title: "开始时间",
                field: "start_time",
                align: "center",
                valign: "middle",
            },
            {
                title: "结束时间",
                field: "finish_time",
                align: "center",
                valign: "middle",
            },
            {
                title: "任务进程",
                field: "step_done",
                align: "center",
                valign: "middle",
                formatter: TableFun.getprocess
            },
            {
                title: "任务状态",
                field: "status",
                align: "center",
                valign: "middle",
                formatter: function (value, row, index) {
                    var arr = ["进行中", "已完成", "错误", "已取消"];
                    return arr[parseInt(row.status)];
                }
            },
            {
                title: "任务来源",
                field: "status",
                align: "center",
                valign: "middle",
                formatter: function (value, row, index) {
                    var source = ""
                    row.source == "1" && (source = "OPENSTACK迁移");
                    row.source == "2" && (source = "ESX迁移");
                    return source;
                }
            },
            {
                title: "任务详情",
                field: "message",
                align: "center",
                valign: "middle",
            },
            {
                title: "操作者",
                field: "username",
                align: "center",
                valign: "middle",
            },
            {
                title: "操作",
                align: "center",
                valign: "middle",
                events: window.operateVmEvents,
                formatter: function (value, row, index) {
                    if (row.status == "0") {
                        return ['<button class="btn btn-warning" id="cacel-vm">取消</button>'
                            //'<button class="btn btn-info" id="retry-vm">重试</button>'
                        ];
                    }
                    var arr = [2, 3];
                    if (arr.indexOf(row.status) != -1) {
                        return ['<button class="btn btn-danger" id="delete-vm">删除</button>'];
                    }
                }
            }
        ]
    });
}
window.operateVmEvents =
{
    "click #cacel-vm": function (e, value, row, index) {
        var request_id = row.request_id;
        $.ajax({
            url: "/v2v/openstack/cancel",
            type: "put",
            dataType: "json",
            data: {
                "request_id": request_id,
                "cancel": 1,
            },
            success: function (res) {
                if (res.code != 0) {
                    res.msg != null ? showMessage(res.msg, "danger", 2000) : showMessage("操作失败，请刷新重试", "danger", 2000);
                } else {
                    showMessage("提交成功！！！", "success", 1100);
                }
                $('#migrateTable').bootstrapTable('refresh', {silent: true});
            }
        });
    },
    "click #delete-vm": function (e, value, row, index) {
        $("#delete-vm-btn").attr('request-id', row.request_id)
        $(".delete-vm-ip").html(row.vm_ip)
        $(".delete-start-time").html(row.start_time)
        $("#delete-vm-modal").modal('show')
    }
};
if (!Array.prototype.forEach) {
    Array.prototype.forEach = function (callback, thisArg) {
        var T, k;
        if (this == null) {
            throw new TypeError(" this is null or not defined");
        }
        var O = Object(this);
        var len = O.length >>> 0; // Hack to convert O.length to a UInt32
        if ({}.toString.call(callback) != "[object Function]") {
            throw new TypeError(callback + " is not a function");
        }
        if (thisArg) {
            T = thisArg;
        }
        k = 0;
        while (k < len) {
            var kValue;
            if (k in O) {
                kValue = O[k];
                callback.call(T, kValue, k, O);
            }
            k++;
        }
    };
};
OpenstackFun.handleData = function (res) {
    var area_arr = res.data.area, type_str = "", hostpool_name, net_area_name, type_arr = [], toarea = [], areatohostpool = {},
        flavors_arr = res.data.flavors, cpu_str = "", cpu_arr = [], mem_arr = {}, disk_arr = {},
        groups_arr = res.data.groups,
        data_obj = {},
        dcmap = allEnvArr;
    //1           2            3

    for (var i = 0; i < area_arr.length; i++) {
        net_area_name = area_arr[i].net_area_name;
        hostpool_name = area_arr[i].hostpool_name;
        hostpool_id = area_arr[i].hostpool_id;

        type_arr.push(area_arr[i].dc_type.toString());
        if (!toarea[area_arr[i].dc_type]) {
            toarea[area_arr[i].dc_type] = [area_arr[i].net_area_name];
        } else {
            toarea[area_arr[i].dc_type].push(area_arr[i].net_area_name);
        }

        if (!areatohostpool[area_arr[i].dc_type + "to" + net_area_name]) {
            areatohostpool[area_arr[i].dc_type + "to" + net_area_name] = [[hostpool_name, hostpool_id]];
        } else {
            areatohostpool[area_arr[i].dc_type + "to" + net_area_name].push([hostpool_name, hostpool_id]);
        }
    }

    type_arr = type_arr.unique();


    for (var j = 0; j < type_arr.length; j++) {
        type_str += '<option value=' + type_arr[j] + '>' + dcmap[type_arr[j]] + '</option>';
    }


    for (var k = 0, group_str = ""; k < groups_arr.length; k++) {
        group_str += "<option value=" + groups_arr[k]['group_id'] + ">" + groups_arr[k]['name'] + "</option>";
    }


    for (var n = 0; n < flavors_arr.length; n++) {
        cpu_arr.push(flavors_arr[n].vcpu);
        if (!mem_arr["cpu" + flavors_arr[n].vcpu])
            mem_arr["cpu" + flavors_arr[n].vcpu] = [flavors_arr[n].memory_mb];
        else
            mem_arr["cpu" + flavors_arr[n].vcpu].push(flavors_arr[n].memory_mb);

        if (!disk_arr["cpu" + flavors_arr[n].vcpu + flavors_arr[n].memory_mb])
            disk_arr["cpu" + flavors_arr[n].vcpu + flavors_arr[n].memory_mb] = [[flavors_arr[n].flavor_id, flavors_arr[n].root_disk_gb]];
        else
            disk_arr["cpu" + flavors_arr[n].vcpu + flavors_arr[n].memory_mb].push([flavors_arr[n].flavor_id, flavors_arr[n].root_disk_gb]);
    }
    cpu_arr = cpu_arr.unique().sort(function (a, b) {
        return a - b;
    });

    for (var m = 0; m < cpu_arr.length; m++) {
        cpu_str += "<option value=" + cpu_arr[m] + ">" + cpu_arr[m] + "核</option>";
    }

    data_obj.toarea = toarea;//区域集合
    data_obj.areatohostpool = areatohostpool;//集群集合
    data_obj.cpu_arr = cpu_arr;//cpu集合
    data_obj.type_str = type_str;//vm环境初始化内容
    data_obj.group_str = group_str;//应用组初始化内容
    data_obj.cpu_str = cpu_str;//cpu初始化内容
    data_obj.mem_arr = mem_arr;//内存容量集合
    data_obj.disk_arr = disk_arr;//disk集合
    if (res.data.segment)data_obj.segment = res.data.segment;
    return data_obj;
};
OpenstackFun.data = null;
OpenstackFun.group_str = null;
OpenstackFun.batchdata = [];
OpenstackFun.initInfo = function () {
    $("#openstacktokvm-modal input").val("");
    $("#openstack-group").attr("data-group-id","");
    $(".init-content option:not(:first-child)").remove();
    $("#openstack-enviroment").val("-1");
    $.ajax({
        url: "/v2v/openstack/init",
        type: "get",
        success: function (res) {
            if (res.code != 0) {
                res.msg == null ? showMessage("请求失败,请刷新重试！！！", "danger", 1000) : showMessage(res.msg, "danger", 1000);
            } else {
                var list = OpenstackFun.handleData(res);
                $("#vm-openstack-enviroment").append(list.type_str);
                $("#cpu-openstack-number").append(list.cpu_str);
                $("#openstacktokvm-modal").modal("show");
                OpenstackFun.group_str = res.data.groups
                delete(list["type_str"]);
                delete(list["group_str"]);
                delete(list["cpu_str"]);
                OpenstackFun.data = list;
            }
        },
        error: function () {
            showMessage("请求错误,请刷新重试", "danger", 2000);
        }
    });
};
OpenstackFun.setSegement = function (envi) {
    var segment_list = OpenstackFun.data.segment, segment_html = "";
    for (var i = 0, len = segment_list.length; i < len; i++) {
        var tmp = segment_list[i];
        if (tmp.env == envi) {
            segment_html += "<option value=" + tmp.seg + ">" + tmp.seg + "</option>";
        }
    }
    return segment_html;
};
OpenstackFun.gotoarea = function (value) {
    if (value == "-1") {
        return;
    }
    var area_arr = OpenstackFun.data.toarea[value], area_str = "";
    $.each(area_arr, function (index, tmp) {
        area_str += " <option value=" + tmp + ">" + tmp + "</option>"
    });
    return area_str;
};
OpenstackFun.gotohostpool = function (area_selected) {
    var host_pool_arr = OpenstackFun.data.areatohostpool[area_selected], host_pool_str = "";
    for (var i = 0; i < host_pool_arr.length; i++) {
        host_pool_str += " <option value=" + host_pool_arr[i][1] + ">" + host_pool_arr[i][0] + "</option>"
    }
    return host_pool_str
};
OpenstackFun.gotomem = function (cpu_selected) {
    var cpu = cpu_selected, mem, mem_str = "";
    var mem_arr = OpenstackFun.data.mem_arr["cpu" + cpu];
    mem_arr = mem_arr.unique().sort(function (a, b) {
        return a - b;
    });
    for (var i = 0; i < mem_arr.length; i++) {
        parseInt(mem_arr[i]) > 1024 ? mem = parseInt(mem_arr[i]) / 1024 + "G" : mem = parseInt(mem_arr[i]) + "MB";
        mem_str += "<option value=" + mem_arr[i] + ">" + mem + "</option>"
    }
    return mem_str;
};
OpenstackFun.submitopenstackkvm = function (modal) {
    var hostpool_id, flavor_id, group_id, vm_ostype,
        cloud_area, retry, form_str, cpu, mem, data;

    hostpool_id = $("#vm-openstack-hostpool").val();
    form_str = $("#openstack-form").serialize();
    cloud_area = $("#openstack-enviroment option:selected").html();
    segment = $("#vm-openstack-segment").val();
    vm_ostype = $("#openstack-vm-type option:selected").html();
    retry = 0;
    group_id = $("#openstack-group").attr('data-group-id');
    var group = $("#openstack-group").val();
    if (!blurCheckGroup("#openstack-group", OpenstackFun.groupListSimple)) {
        showMessage("所选应用组的名称不存在", "danger", 600)
        return;
    }


    cpu = $("#cpu-openstack-number").val();
    mem = $("#mem-openstack-number").val();

    var list = $("#openstack-form input");
    for (var i = 0; i < list.length; i++) {
        if (list[i].value == "") {
            showMessage("请填写完整信息", "danger", 1000);
            return;
        }
    }

    var patt1 = new RegExp("^(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|[1-9])\\." + "(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|\\d)\\." + "(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|\\d)\\." + "(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|\\d)$");
    var result1 = patt1.test($("#vm-openstack-ip").val());
    if (result1 != true) {
        showMessage("请输入正确的ip地址", "danger", 1200);
        return;
    }
    if (segment == -1) {
        showMessage("请选择VM所属网段", "danger", 1000);
        return;
    }
    if (hostpool_id == -1) {
        showMessage("请选择所属集群", "danger", 1000);
        return;
    }
    if (!group_id) {
        showMessage("请选择所属应用组", "danger", 1000);
        return;
    }
    if (cpu == -1) {
        showMessage("请选择CPU数量", "danger", 1000);
        return;
    }
    if (mem == -1) {
        showMessage("请选择内存容量", "danger", 1000);
        return;
    }


    flavor_id = OpenstackFun.data.disk_arr["cpu" + cpu + mem][0][0];

    data = form_str;
    data += "&cloud_area=" + cloud_area;
    data += "&segment=" + segment;
    data += "&vm_ostype=" + vm_ostype;
    data += "&group_id=" + group_id;
    data += "&flavor_id=" + flavor_id;
    data += "&user_id=" + user_id_num;
    data += "&retry=" + retry;

    $.ajax({
        url: "/v2v/openstack/" + hostpool_id,
        type: "post",
        dataType: "json",
        data: data,
        beforeSend: function () {
            $("#loading").css("display", "block");

        },
        success: function (res) {
            $("#loading").css("display", "none");
            if (res.code != 0) {
                res.msg != null ? showMessage(res.msg, "danger", 2000) : showMessage("操作失败，请刷新重试", "danger", 2000);
            } else {
                showMessage("提交成功！！！", "success", 1100);
                $("#openstacktokvm-modal").modal("hide");
                $('#migrateTable').bootstrapTable('refresh', {silent: true});
            }
        },
        error: function () {
            showMessage("请求失败，请刷新重试！！！", "danger", 2000);
        }
    });
};
OpenstackFun.batchHtmlInit = function (arr1, arr2, arr3) {
    if (arr1) {
        arr1.forEach(function (tmp, index) {
            $(tmp).val("");
        });
    }
    if (arr2) {
        arr2.forEach(function (tmp, index) {
            $(tmp + " option:not(:first-child)").remove();
        })
    }
    if (arr3) {
        arr3.forEach(function (tmp, index) {
            $(tmp).val("-1");
        });
    }

};
OpenstackFun.group_str_batch = null;
OpenstackFun.batchInfoInit = function () {
    var input_arr = ["#openstack-batch-vmname", "#openstack-batch-vmip", "#openstack-batch-group", "#openstack-batch-appinfo", "#openstack-batch-admin"];
    var sel_arr = ["#openstack-batch-segment", "#openstack-batch-hostpool", "#openstack-batch-vmenvi", "#openstack-batch-netarea", "#openstack-batch-cpu", "#openstack-batch-mem"];
    var sel_default_arr = ["#openstack-batch-env", "#openstack-batch-ostype"];
    $("#openstack-batch-group").attr("data-group-id", '')
    OpenstackFun.batchHtmlInit(input_arr, sel_arr, sel_default_arr);
    $.ajax({
        url: "/v2v/openstack/init",
        type: "get",
        success: function (res) {
            if (res.code != 0) {
                res.msg == null ? showMessage("请求失败,请刷新重试！！！", "danger", 1000) : showMessage(res.msg, "danger", 1000);
            } else {
                var list = OpenstackFun.handleData(res);
                $("#openstack-batch-vmenvi").append(list.type_str);
                OpenstackFun.group_str_batch = res.data.groups
                $("#openstack-batch-cpu").append(list.cpu_str);
                delete(list["type_str"]);
                delete(list["group_str"]);
                delete(list["cpu_str"]);
                OpenstackFun.data = list;
                $("#main-paper").css("display", "none");
                $("#openstack-paper").css("display", "block");
            }
        },
        error: function () {
            showMessage("请求错误,请刷新重试", "danger", 2000);
        }
    });
};
OpenstackFun.getBatchInfo = function () {
    var hostpool_id = $("#openstack-batch-hostpool").val();
    var group_id = $("#openstack-batch-group").attr("data-group-id");
    var group = $("#openstack-batch-group").val();
    var flavor_id;
    var vm_ostype = $("#openstack-batch-ostype").val();
    var cloud_area = $("#openstack-batch-env").val();
    var segment = $("#openstack-batch-segment").val();

    if (hostpool_id == -1) {
        showMessage("请选择集群", "danger", 1000);
        return false;
    }
    if (!group_id) {
        showMessage("请选择应用组", "danger", 1000);
        return false;
    }
    if (vm_ostype == -1) {
        showMessage("请选择操作系统类型", "danger", 1000);
        return false;
    }
    if (cloud_area == -1) {
        showMessage("请选择openstack环境", "danger", 1000);
        return false;
    }
    if (segment == -1) {
        showMessage("请选择vm所在网段", "danger", 1000);
        return false;
    }
    if (!blurCheckGroup("#openstack-batch-group", OpenstackFun.groupListSel)) {
        showMessage("所选应用组的名称不存在", "danger", 600)
        return false;
    }
    var cpu = $("#openstack-batch-cpu").val();
    var mem = $("#openstack-batch-mem").val();
    if (cpu == -1) {
        showMessage("请选择CPU数量", "danger", 600);
        return false;
    }
    if (mem == -1) {
        showMessage("请选择内存容量", "danger", 600);
        return false;
    }
    var name = "cpu" + cpu + mem;
    var list = OpenstackFun.data.disk_arr[name];
    //console.log(name);
    //console.log(OpenstackFun.data.disk_arr);
    //console.log(list);
    if (list) {
        list.forEach(function (tmp) {
            flavor_id = tmp[0];
        });
    } else {
        return false;
    }

    var vm_app_info = $("#openstack-batch-appinfo").val();
    var vm_owner = $("#openstack-batch-admin").val();
    var vm_name = $("#openstack-batch-vmname").val();
    var vm_ip = $("#openstack-batch-vmip").val();
    var user_id = user_id_num;

    if (vm_app_info == "") {
        showMessage("应用系统信息不能为空", "danger", 2000);
        return false;
    }
    if (vm_owner == "") {
        showMessage("应用管理员不能为空", "danger", 2000);
        return false;
    }
    if (vm_name == "") {
        showMessage("VM名称不能为空", "danger", 2000);
        return false;
    }
    var patt1 = new RegExp("^(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|[1-9])\\." + "(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|\\d)\\." + "(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|\\d)\\." + "(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|\\d)$");
    var result1 = patt1.test(vm_ip);
    if (!result1) {
        showMessage("VMIP格式不正确,请重新输入", "danger", 2000);
        return false;
    }
    var arr_set = [];
    OpenstackFun.batchdata.forEach(function (tmp) {
        if (tmp.vm_ip == vm_ip || tmp.vm_name == vm_name) {
            arr_set.push(1);
        }
    });
    if (arr_set.length > 0) {
        showMessage("VM IP VM名称不能重复,请重新填写 ", "danger", 2000);
        return false;
    }

    var vm_envi = $("#openstack-batch-vmenvi option:selected").html();
    var net_area = $("#openstack-batch-netarea").val();
    var hostpool = $("#openstack-batch-hostpool option:selected").html();
    var group = $("#openstack-batch-group").val();
    var obj = {
        "hostpool_id": hostpool_id,
        "group_id": group_id,
        "vm_ostype": vm_ostype,
        "cloud_area": cloud_area,
        "segment": segment,
        "flavor_id": flavor_id,
        "vm_app_info": vm_app_info,
        "vm_owner": vm_owner,
        "vm_name": vm_name,
        "vm_ip": vm_ip,
        "user_id": user_id,
        "vm_envi": vm_envi,
        "net_area": net_area,
        "hostpool": hostpool,
        "group": group,
        "cpu": cpu,
        "mem": mem
    };
    OpenstackFun.batchdata.push(obj);
    return true;
};
OpenstackFun.batchNum = 0;
OpenstackFun.errList = [];
OpenstackFun.checkBatch = function(){
    var index =parseInt( OpenstackFun.batchNum);
    var list = OpenstackFun.batchdata[index];
    var obj ={};
    obj.flavor_id = list.flavor_id;
    obj.vm_ostype = list.vm_ostype;
    obj.cloud_area = list.cloud_area;
    obj.segment = list.segment;
    obj.vm_ip = list.vm_ip;
    $.ajax({
        url:"/v2v/openstack/task_check?t="+Math.random(),
        type:"post",
        dataType:"json",
        data:obj,
        //beforeSend:function(){
        //    $("#migrate-batch-vm").attr("disabled",true);
        //},
        success:function(res){
            var that = $("#batch-info-table").children().children('[data-vmname='+list.vm_name+']');
            $(that).html('<a  href="#" class="delete-one"><i class="fa fa-trash-o text-danger"></i></a>');
            if(res.code!=0){
                obj.vm_name = list.vm_name;
                if(res.msg){
                   obj.error_message = res.msg;
                }else{
                     obj.error_message  = "请求错误,请删除重新添加";
                }
                OpenstackFun.errList.push(obj);
            }else{
                OpenstackFun.batchdata[index].vm_disk = res.data.vm_disk;
                OpenstackFun.batchdata[index].vm_osver = res.data.vm_osver;
            }
            //console.log(OpenstackFun.errList);

        }
    });
};
OpenstackFun.createTableInfo = function () {
    var html = "";
    var i = parseInt(OpenstackFun.batchNum)+1;
    var tmp = OpenstackFun.batchdata[OpenstackFun.batchNum];
    //list.forEach(function (tmp, index) {
    //    var i = index + 1;
        var mem = tmp.mem;
        parseInt(mem) > 1024 ? mem = parseInt(mem) / 1024 + "G" : mem = parseInt(mem) + "MB";
        html += '<tr data-row='+tmp.vm_name+'>';
        html += '<td>' + i + '</td>';
        html += '<td title="cloud_area">' + tmp.cloud_area + '</td>';
        html += '<td title="vm_name">' + tmp.vm_name + '</td>';
        html += '<td title="vm_ip">' + tmp.vm_ip + '</td>';
        html += '<td title="segment">' + tmp.segment + '</td>';
        html += '<td title="vm_envi">' + tmp.vm_envi + '</td>';
        html += '<td title="net_area">' + tmp.net_area + '</td>';
        html += '<td title="hostpool">' + tmp.hostpool + '</td>';
        html += '<td title="vm_ostype">' + tmp.vm_ostype + '</td>';
        html += '<td title="group">' + tmp.group + '</td>';
        html += '<td title="cpu">' + tmp.cpu + '核</td>';
        html += '<td title="mem">' + mem + '</td>';
        html += '<td title="vm_app_info">' + tmp.vm_app_info + '</td>';
        html += '<td title="vm_owner">' + tmp.vm_owner + '</td>';
        html += '<td data-vmname = '+tmp.vm_name+'><img src="img/transform.gif" alt=""></td>';
        //html += '<td class="sel-deg"><a  href="#" class="delete-one"><i class="fa fa-trash-o text-danger"></i></a></td>';
        html += '</tr>';

    //});

    return html;
};
OpenstackFun.err_show = function(list,html,bool,requestBool){
    var list = list || [];
    var middle_arr = [];
    list.forEach(function (tmp) {
        $("#batch-info-table").children('[data-row=' + tmp.vm_name + ']').css("color", "#f00");
        html += '<tr>';
        html += '<td>' + tmp.vm_name + '</td>';
        html += '<td>' + tmp.error_message + '</td>';
        html += '</tr>';
        if(bool)OpenstackFun.errList.push({"vm_name":tmp.vm_name,"error_message":tmp.error_message});
        if(requestBool){middle_arr.push(tmp.vm_name)};
    });
    if (requestBool) {
        var _list_ = OpenstackFun.batchdata;
        _list_.forEach(function (item, index) {
            if (middle_arr.indexOf(item.vm_name) == -1) {
               OpenstackFun.batchdata.splice(index, 1);
                $("#batch-info-table").children('[data-row=' + item.vm_name + ']').remove();
                OpenstackFun.batchNum -= 1;
                var ele_list = $("#batch-info-table").children().children(":first-child");
                for (var i = 0; i < ele_list.length; i++) {
                    $(ele_list[i]).html(i + 1);
                }
            }
        });
    }
    $("#err-box").html(html);
    $("#warning-text").html("请先删除错误信息再重新提交迁移信息！");
    $("#batch-err-modal").modal("show");
};
OpenstackFun.openstackbatchSubmit = function () {
    var ele_list = $("#batch-info-table").children().children(":last-child"),arr_wait = [];
    for (var i = 0; i < ele_list.length; i++) {
        var tmp = ele_list[i];
        var className = $(tmp).children().attr("class");
        if(!className){
            arr_wait.push($(tmp).attr("data-vmname"));
        };
    }
    if(arr_wait.length>0){
        showMessage("您添加的数据正在验证是否可用,请稍等...","danger",2000);
        return;
    }
    if (OpenstackFun.batchdata.length > 0 ) {
        if (OpenstackFun.errList.length <= 0) {
            var openstack_batch = [];
            OpenstackFun.batchdata.forEach(function (tmp, index) {
                var obj = {};
                obj["hostpool_id"] = tmp.hostpool_id;
                obj["flavor_id"] = tmp.flavor_id;
                obj["vm_app_info"] = tmp.vm_app_info;
                obj["group_id"] = tmp.group_id;
                obj["vm_owner"] = tmp.vm_owner;
                obj["vm_ostype"] = tmp.vm_ostype;
                obj["cloud_area"] = tmp.cloud_area;
                obj["segment"] = tmp.segment;
                obj["vm_name"] = tmp.vm_name;
                obj["vm_ip"] = tmp.vm_ip;
                obj["user_id"] = tmp.user_id;
                obj["vm_disk"] = tmp.vm_disk;
                obj["vm_osver"] = tmp.vm_osver;
                openstack_batch.push(obj);
            });
            openstack_batch = JSON.stringify(openstack_batch);
            $.ajax({
                url: '/v2v/openstack/batch_2',
                type: "post",
                dataType: 'json',
                data: {"openstack_batch": openstack_batch},
                beforeSend: function () {
                    $("#loading").css("display", "block");
                },
                success: function (res) {
                    $("#loading").css("display", "none");
                    if (res.code != 0) {
                        if(res.data && res.data.length>0){
                            var err_list = res.data;
                            var html ="";
                            OpenstackFun.err_show(err_list,html,true,false);
                        }else{
                            showMessage("请求失败,请刷新重试","danger",1000);
                        }
                    } else {
                        if (res.data.length > 0) {
                                var _err_list = res.data;
                                var _html = "";
                                OpenstackFun.err_show(_err_list, _html,true,true);
                        } else {
                            $("#batch-info-table").html("");
                            OpenstackFun.batchdata = [];
                            OpenstackFun.batchNum = 0;
                            OpenstackFun.errList = [];
                            $("#main-paper").css("display", "block");
                            $("#openstack-paper").css("display", "none");
                        }
                         $("#migrateTable").bootstrapTable('refresh', {silent: true});
                    }
                },
                error: function () {
                    showMessage("请求失败,请刷新重试", "danger", 2000);
                }
            });
        }else{
            var list = OpenstackFun.errList, html = "";
            OpenstackFun.err_show(list,html,false,false);
            //list.forEach(function (tmp) {
            //    $("#batch-info-table").children('[data-row=' + tmp.vm_name + ']').css("color", "#f00");
            //    html += '<tr>';
            //    html += '<td>' + tmp.vm_name + '</td>';
            //    html += '<td>' + tmp.error_message + '</td>';
            //    html += '</tr>';
            //});
            //$("#err-box").html(html);
            //$("#warning-text").html("请先删除错误信息再重新提交迁移信息！");
            //$("#batch-err-modal").modal("show");
        }

    } else {
        showMessage("暂无数据可提交迁移,请添加数据！", "danger", 2000);
    }
};

TableFun.judgeStatu = function () {
    if (typeof timer_migrate != "undefined")clearTimeout(timer_migrate);
    var sel_arr = $("#migrateTable").bootstrapTable("getSelections");
    if (sel_arr.length > 0)return;
    var statu_arr = [];
    for (var i = 0; i < sel_arr.length; i++) {
        statu_arr.push(sel_arr[i].status);
    }
    if (statu_arr.indexOf(1) != "-1") {
        showMessage("选中的任务有不可操作项,请查看任务状态！", "danger", 1000);
        return;
    }
    timer_migrate = setTimeout(function () {
        $("#migrateTable").bootstrapTable('refresh', {silent: true});
    }, 15000);
};
TableFun.getprocess = function (value, row, index) {

    function bg3() {
        var r = Math.floor(Math.random() * 150 + 100);
        var g = Math.floor(Math.random() * 150 + 100);
        var b = Math.floor(Math.random() * 150 + 80);
        return "rgb(" + r + ',' + g + ',' + b + ")";//所有方法的拼接都可以用ES6新特性`其他字符串{$变量名}`替换
    }

    var num;
    if (row.source == 1) {
        var status_arr = {
            "begin": "0",
            "create_destination_dir": "1",
            "create_storage_pool": "2",
            "get_vm_file": "3",
            "copy_vm_disk_to_desthost": "4",
            "copy_vm_xml_to_desthost": "5",
            "standardlize_target_vm": "6",
            "define_target_vm": "7",
            "start_target_vm": "8",
            "inject_vm_ip_configuration": "9"
        };
        num = parseInt(parseInt(status_arr[row.step_done]) / 9 * 100) + "%";
    } else if (row.source == 2) {
        var arr = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13];
        if (row.vm_ostype == "Windows") {
            num = parseInt(parseInt(arr[row.step_done]) / 13 * 100) + "%";
        }
        if (row.vm_ostype == "Linux") {
            num = parseInt(parseInt(arr[row.step_done]) / 9 * 100) + "%";
        }
    }


    var html = '';
    html += '<div class="progress" style="background:rgba(0, 204, 255, 0.258823529411765);margin-bottom: 0px">';
    if (row.status == 1)
        html += '        <div class="progress-bar" style="width: ' + num + '; background: #19CEE6;"> ';
    else if (row.status == 2 || row.status == 3)
        html += '        <div class="progress-bar" style="width: ' + num + '; background: #f00;"> ';
    else
        html += '        <div class="progress-bar" style="width: ' + num + '; background: linear-gradient(to right,' + bg3() + ' 20%,' + bg3() + ' 60%,' + bg3() + ' 100%);"> ';

    html += '              <div class="progress-value">' + num + '</div>';
    html += '        </div></div>';
    return html;
};
TableFun.retrymigratevm = function () {
    var selected_arr = $("#migrateTable").bootstrapTable("getSelections");
    if (selected_arr.length == 0) {
        showMessage("没有可以操作的任务", "danger", 2000);
        return;
    }
    var request_id_arr = [], request_id, retry = 1;
    for (var i = 0; i < selected_arr.length; i++) {
        request_id_arr.push(selected_arr[i].request_id)
    }
    request_id = request_id_arr.join(",");
    $.ajax({
        url: "/v2v/openstack/retry",
        type: "put",
        dataType: "json",
        data: {"request_id": request_id, "retry": retry},
        success: function (res) {
            if (res.code != 0) {
                res.msg != null ? showMessage(res.msg, "danger", 2000) : showMessage("操作失败,请刷新重试", "danger", 2000);
            } else {
                showMessage("操作成功", "success", 2000);
            }
            $('#migrateTable').bootstrapTable('refresh', {silent: true});
        }
    });
};
TableFun.deletemigratevm = function (request_id) {
    $.ajax({
        url: "/v2v/openstack",
        type: "delete",
        dataType: "json",
        data: {
            "request_id": request_id,
            "delete": 1
        },
        beforeSend: function () {
            $("#loading").css("display", "block");
        },
        success: function (res) {
            $("#loading").css("display", "none");
            if (res.code != 0) {
                res.msg != null ? showMessage(res.msg, "danger", 1000) : showMessage("操作失败,请刷新重试", "danger", 1000);
            } else {
                showMessage("操作成功", "success", 1000);
            }
            deg = 1;
            $('#migrateTable').bootstrapTable('refresh', {silent: true});
            $("#delete-vm-modal").modal('hide')
        },
        error: function () {
            showMessage("请求错误,请刷新重试", "danger", 1000)
        }
    });
};


EsxFun.data = {};
EsxFun.requestParams = {};
EsxFun.handleEsxData = function (res) {
    var list = res.data;
    var dataParams = {};

    //dataParams = {
    //    "hasSubrange": {
    //        "toenvi": [],
    //        "toparent": [],
    //        "tochild": [],
    //        "todatacenter": [],
    //        "todatacenter": [],
    //        "tonetarea": [],
    //        "tohostpool": []
    //    },
    //    "noneSubrange": {
    //        "envi": [],
    //        "toparent": [],
    //        "todatacenter": [],
    //        "todatacenter": [],
    //        "tonetarea": [],
    //        "tohostpool": []
    //    },
    //      "quota":{
    //        "tocpu":[],
    //        "tomem":[]
    //      },
    //"grouplist":[]
    //}
    var arealist = EsxFun.handleHostpoolInfo(list);
    var quota = EsxFun.handlequato(list.flavors);
    //var grouplist = EsxFun.handlegroup(list.groups);
    var grouplist = list.groups;
    var segmentlist = EsxFun.handleSegment(list.segment);
    dataParams.arealist = arealist;
    dataParams.quota = quota;
    dataParams.grouplist = grouplist;
    dataParams.segmentlist = segmentlist;
    return dataParams;
};
EsxFun.handleHostpoolInfo = function (list) {
    var area_DQ = list.area_DQ;
    var area_ZB = list.area_ZB;
    var envi_arr = allEnvArr, area_list = {};
    var zb_info = {}, toenvi_ZB = [], tonetarea_ZB = {}, tohostpool_ZB = {}, todatacenter_ZB = {};
    var dq_info = {};
    var envitype_dq = [], toarea_dq = {};
    var hastochildarea_dq = {}, hastodatacenter_dq = {}, hastonetarea_dq = {}, hastohostpool_dq = {};
    var nonetodatacenter_dq = {}, nonetonetarea_dq = {}, nonetohostpool_dq = {};
    if (area_ZB.length != 0) {
        for (var i = 0, len = area_ZB.length; i < len; i++) {
            var item = area_ZB[i];
            var dctype_name = "to" + item.dc_type;
            var enviNetarea = item.dc_type + "to" + item.datacenter_name;
            var envinetareahostpool = item.dc_type + "to" + item.datacenter_name + "to" + item.net_area_name;
            toenvi_ZB.push(item.dc_type);
            if (!todatacenter_ZB[dctype_name])todatacenter_ZB[dctype_name] = [item.datacenter_name];
            else todatacenter_ZB[dctype_name].push(item.datacenter_name);

            if (!tonetarea_ZB[enviNetarea])tonetarea_ZB[enviNetarea] = [item.net_area_name];
            else tonetarea_ZB[enviNetarea].push(item.net_area_name);

            if (!tohostpool_ZB[envinetareahostpool])tohostpool_ZB[envinetareahostpool] = [[item.hostpool_id, item.hostpool_name]];
            else tohostpool_ZB[envinetareahostpool].push([item.hostpool_id, item.hostpool_name]);
        }
    }
    toenvi_ZB = toenvi_ZB.unique();
    zb_info.toenvi_ZB = toenvi_ZB;
    zb_info.todatacenter_ZB = todatacenter_ZB;
    zb_info.tonetarea_ZB = tonetarea_ZB;
    zb_info.tohostpool_ZB = tohostpool_ZB;


    if (area_DQ.length != 0) {
        for (var i = 0, len = area_DQ.length; i < len; i++) {
            var item = area_DQ[i];
            var name = item.dc_type;
            name1 = name + "to" + item.area_name,
                name2 = name1 + "to" + item.child_area_name,
                name3 = name1 + "to" + item.datacenter_name,//无子区域
                name4 = name2 + "to" + item.datacenter_name,//有子区域
                name5 = name3 + "to" + item.net_area_name,//无子区域
                name6 = name4 + "to" + item.net_area_name;//有子区域

            envitype_dq.push(item.dc_type);
            if (!toarea_dq["to" + item.dc_type])toarea_dq["to" + item.dc_type] = [item.area_name];
            else toarea_dq["to" + item.dc_type].push(item.area_name);

            if (item.child_area_name != null) {
                if (!hastochildarea_dq[name1])hastochildarea_dq[name1] = [item.child_area_name];
                else hastochildarea_dq[name1].push(item.child_area_name);

                if (!hastodatacenter_dq[name2])hastodatacenter_dq[name2] = [item.datacenter_name];
                else hastodatacenter_dq[name2].push(item.datacenter_name);

                if (!hastonetarea_dq[name4])hastonetarea_dq[name4] = [item.net_area_name];
                else hastonetarea_dq[name4].push(item.net_area_name);

                if (!hastohostpool_dq[name6])hastohostpool_dq[name6] = [[item.hostpool_id, item.hostpool_name]];
                else hastohostpool_dq[name6].push([item.hostpool_id, item.hostpool_name]);
            } else {
                if (!nonetodatacenter_dq[name1])nonetodatacenter_dq[name1] = [item.datacenter_name];
                else nonetodatacenter_dq[name1].push(item.datacenter_name);

                if (!nonetonetarea_dq[name3])nonetonetarea_dq[name3] = [item.net_area_name];
                else nonetonetarea_dq[name3].push(item.net_area_name);

                if (!nonetohostpool_dq[name5])nonetohostpool_dq[name5] = [[item.hostpool_id, item.hostpool_name]];
                else nonetohostpool_dq[name5].push([item.hostpool_id, item.hostpool_name]);
            }
        }
    }
    envitype_dq = envitype_dq.unique();
    dq_info.envitype_dq = envitype_dq;
    dq_info.toarea_dq = toarea_dq;
    dq_info.hastochildarea_dq = hastochildarea_dq;
    dq_info.hastodatacenter_dq = hastodatacenter_dq;
    dq_info.hastonetarea_dq = hastonetarea_dq;
    dq_info.hastohostpool_dq = hastohostpool_dq;
    dq_info.nonetodatacenter_dq = nonetodatacenter_dq;
    dq_info.nonetonetarea_dq = nonetonetarea_dq;
    dq_info.nonetohostpool_dq = nonetohostpool_dq;


    area_list.zb_info = zb_info;
    area_list.dq_info = dq_info;
    return area_list;
};
EsxFun.handlequato = function (flavors_arr) {
    var cpu_arr = [], mem_arr = {}, disk_arr = {}, quatolist = {};
    for (var n = 0; n < flavors_arr.length; n++) {
        cpu_arr.push(flavors_arr[n].vcpu);
        if (!mem_arr["cpu" + flavors_arr[n].vcpu])
            mem_arr["cpu" + flavors_arr[n].vcpu] = [flavors_arr[n].memory_mb];
        else
            mem_arr["cpu" + flavors_arr[n].vcpu].push(flavors_arr[n].memory_mb);

        if (!disk_arr["cpu" + flavors_arr[n].vcpu + flavors_arr[n].memory_mb])
            disk_arr["cpu" + flavors_arr[n].vcpu + flavors_arr[n].memory_mb] = [[flavors_arr[n].flavor_id, flavors_arr[n].root_disk_gb]];
        else
            disk_arr["cpu" + flavors_arr[n].vcpu + flavors_arr[n].memory_mb].push([flavors_arr[n].flavor_id, flavors_arr[n].root_disk_gb]);
    }
    cpu_arr = cpu_arr.unique().sort(function (a, b) {
        return a - b;
    });
    var mem_list = {};
    var disk_list = {};

    $.each(mem_arr, function (index, tmp) {
        mem_list[index] = tmp.unique().sort(function (a, b) {
            return a - b;
        });
    });
    $.each(disk_arr, function (index, tmp) {
        disk_list[index] = tmp.unique().sort(function (a, b) {
            return a - b;
        });
    });

    quatolist.cpu_arr = cpu_arr;
    quatolist.mem_arr = mem_list;
    quatolist.disk_arr = disk_list;
    return quatolist;
};
EsxFun.handleSegment = function (segment) {
    var segmentList = {};
    var i = 0;
    len = segment.length;
    for (; i < len; i++) {
        var tmp = segment[i];
        var name = tmp.dc_type + "to" + tmp.datacenter + "to" + tmp.net_area;
        if (!segmentList[name])segmentList[name] = [tmp.segment];
        else segmentList[name].push(tmp.segment)
    }
    return segmentList;
};
EsxFun.handlegroup = function (grouplist) {
    var groupInfo = {};
    for (var i = 0, len = grouplist.length; i < len; i++) {
        var item = grouplist[i];
        if (!groupInfo[item.name]) {
            groupInfo[item.name] = [[item.name, item.group_id]];
        } else {
            groupInfo[item.name].push([item.name, item.group_id]);
        }
    }
    return groupInfo;
};
EsxFun.initInfo = function () {
    $(".resetInput").val("");
    $("#esx-user-environment").val("-1");
    $.ajax({
        url: "/v2v/esx/init",
        type: "get",
        dataType: "json",
        success: function (res) {
            if (res.code != 0) {
                res.msg != null ? showMessage(res.msg, "danger", 2000) : showMessage("获取数据失败，请刷新重试", "danger", 2000)
            } else {
                var list = EsxFun.handleEsxData(res);
                EsxFun.data = list;
                $("#esxtokvm-user-modal").modal("show");
            }
        },
        error: function () {
            showMessage("获取数据失败，请刷新重试", "danger", 2000);
        }
    });
};
EsxFun.submitosinfo = function () {
    var esx_passwd = $("#esx-user-paseeword").val();
    var esx_env = $("#esx-user-environment").val();
    var esx_ip = $("#esx-user-ip").val();
    var vm_name = $("#vm-user-name").val();
    var patt1 = new RegExp("^(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|[1-9])\\." + "(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|\\d)\\." + "(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|\\d)\\." + "(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|\\d)$");
    var result1 = patt1.test(esx_ip);
    if (esx_env == "-1") {
        showMessage("请选择Esx环境", "danger", 2000);
        return;
    }
    ;
    if (esx_passwd == "" || vm_name == "" || esx_ip == "") {
        showMessage("请填写完整信息", "danger", 2000);
        return;
    }
    ;
    if (!result1) {
        showMessage("IP格式不对,请重新填写", "danger", 2000);
        return;
    }
    ;
    var base = new Base64();
    //esx_passwd = base.encode(esx_passwd);

    esx_passwd = base.encode(esx_passwd);//2017/7/27
    //console.log(esx_passwd);
    $("#esxtokvm-modal .resetInput").val("");
    $("#esx-ip-vmuser").val(esx_ip);
    $("#vm-datacenter-area").val("-1");
    $("#vm-group").attr("data-group-id", '');
    $("#vm-type").val("-1");
    EsxFun.objInit("#mem-number", "请选择内存容量");
    EsxFun.objInit("#cpu-number", "请选择cpu数量");
    EsxFun.objInit("#vm-area-room", "请选择VM区域");
    EsxFun.objInit("#vm-childarea-room", "请选择子区域");
    EsxFun.objInit("#vm-datacenter-room", "请选择VM所属机房");
    EsxFun.objInit("#vm-net-area", "请选择网络区域");
    EsxFun.objInit("#vm-net-area-segment", "请选择VM网段");
    EsxFun.objInit("#vm-hostpool", "请选择VM集群");
    $("#areabox").css("display", "none");
    $.ajax({
        url: "/v2v/esx/define",
        type: "post",
        dataType: "json",
        data: {
            "esx_passwd": esx_passwd,
            "esx_env": esx_env,
            "esx_ip": esx_ip,
            "vm_name": vm_name
            //"esx_passwd": esx_passwd,
            //"esx_env": "1",


        },
        beforeSend: function () {
            $("#loading").css("display", "block");
        },
        success: function (res) {
            $("#loading").css("display", "none");
            if (res.code != 0) {
                res.msg != null ? showMessage(res.msg, "danger", 2000) : showMessage("操作失败", "danger", 2000);
            } else {
                $("#esxtokvm-user-modal").modal("hide");
                var data = res.data;
                var arr = allEnvArr;
                var cpu_list = EsxFun.data.quota["cpu_arr"];

                $("#esx-envi-vm").val(arr[parseInt(data.esx_env)]);
                $("#esx-name-vm").val(data.vm_osname);
                $("#esx-ip-vmos").val(data.vm_ip);
                $("#esxtokvm-modal").modal("show");
                $("#vm-enviroment-room").val(arr[parseInt(data.esx_env)]);

                for (var i = 0; i < cpu_list.length; i++) {
                    $("#cpu-number").append("<option value=cpu" + cpu_list[i] + ">" + cpu_list[i] + "核</option>");
                }


                EsxFun.requestParams.esx_env = data.esx_env;
                EsxFun.requestParams.vm_osver = data.vm_osver;
                EsxFun.requestParams.vm_ip = data.vm_ip;
                EsxFun.requestParams.vm_name = data.vm_osname;
                EsxFun.requestParams.vm_disk = data.vm_disk;
                EsxFun.requestParams.esx_passwd = esx_passwd;
                EsxFun.requestParams.esx_ip = esx_ip;
                EsxFun.requestParams.vmware_vm = vm_name;
                EsxFun.getHostpoolId();
                EsxFun.getQuato();
            }
        },
        error: function () {
            showMessage("操作失败", "danger", 2000);
        }
    });
};
EsxFun.objInit = function (obj,str) {
        $(obj).html("<option value='-1'>" + str + "</option>");
};
EsxFun.getHostpoolId = function () {
    var data = EsxFun.data.arealist;
    //console.log(data);
    var envi = EsxFun.requestParams.esx_env, name = "to" + envi;
    $("#vm-datacenter-area").change(function () {
        EsxFun.objInit("#vm-area-room", "请选择VM区域");
        EsxFun.objInit("#vm-childarea-room", "请选择子区域");
        EsxFun.objInit("#vm-datacenter-room", "请选择VM所属机房");
        EsxFun.objInit("#vm-net-area", "请选择网络区域");
        EsxFun.objInit("#vm-net-area-segment", "请选择VM网段");
        EsxFun.objInit("#vm-hostpool", "请选择VM集群");
        var area_datacenter = $("#vm-datacenter-area").val();
        if (area_datacenter == '地区') {
            //area_datacenter = area_datacenter.unique();
            $("#areabox").css("display", "block");
            $(".child_area_show").css("display", "none");
            var list = data.dq_info.toarea_dq[name];
            if (list) {
                list = list.unique();//2017/7/27
                for (var i = 0; i < list.length; i++) {
                    var tmp = list[i];
                    $("#vm-area-room").append("<option value=" + envi + "to" + tmp + ">" + tmp + "</option>")
                }
            }
        } else if (area_datacenter == '总部') {
            $("#areabox").css("display", "none");
            $(".child_area_show").css("display", "none");
            var list = data.zb_info.todatacenter_ZB[name];
            if (list) {
                list = list.unique();
                for (var i = 0; i < list.length; i++) {
                    var tmp = list[i];
                    $("#vm-datacenter-room").append("<option value=" + envi + "to" + tmp + ">" + tmp + "</option>")
                }
            }
        } else {
            EsxFun.objInit("#vm-area-room", "请选择VM区域");
            EsxFun.objInit("#vm-childarea-room", "请选择子区域");
            EsxFun.objInit("#vm-datacenter-room", "请选择VM所属机房");
            EsxFun.objInit("#vm-net-area", "请选择网络区域");
            EsxFun.objInit("#vm-net-area-segment", "请选择VM网段");
            EsxFun.objInit("#vm-hostpool", "请选择VM集群");
        }
    });
    $("#vm-area-room").change(function () {
        EsxFun.objInit("#vm-childarea-room", "请选择子区域");
        EsxFun.objInit("#vm-datacenter-room", "请选择VM所属机房");
        EsxFun.objInit("#vm-net-area", "请选择网络区域");
        EsxFun.objInit("#vm-net-area-segment", "请选择VM网段");
        EsxFun.objInit("#vm-hostpool", "请选择VM集群");
        var name1 = $(this).val();
        var area_arr1 = data.dq_info.hastochildarea_dq;
        var area_arr2 = data.dq_info.nonetodatacenter_dq;
        if (area_arr1[name1]) {
            $(".child_area_show").css("display", "block");
            var list = area_arr1[name1], i = 0;
            list = list.unique();
            len = list.length;
            for (; i < len; i++) {
                var tmp = list[i];
                $("#vm-childarea-room").append("<option value=" + name1 + "to" + tmp + ">" + tmp + "</option>");
            }
        } else if (area_arr2[name1]) {
            $(".child_area_show").css("display", "none");
            var _list = area_arr2[name1], j = 0;
            _list = _list.unique();
            _len = _list.length
            for (; j < _len; j++) {
                var item = _list[j];
                $("#vm-datacenter-room").append("<option value=" + name1 + "to" + item + ">" + item + "</option>");
            }
        } else {
            $(".child_area_show").css("display", "none");
            EsxFun.objInit("#vm-childarea-room", "请选择子区域");
            EsxFun.objInit("#vm-datacenter-room", "请选择VM所属机房");
            EsxFun.objInit("#vm-net-area", "请选择网络区域");
            EsxFun.objInit("#vm-net-area-segment", "请选择VM网段");
            EsxFun.objInit("#vm-hostpool", "请选择VM集群");
        }
    });
    $("#vm-childarea-room").change(function () {
        EsxFun.objInit("#vm-datacenter-room", "请选择VM所属机房");
        EsxFun.objInit("#vm-net-area", "请选择网络区域");
        EsxFun.objInit("#vm-net-area-segment", "请选择VM网段");
        EsxFun.objInit("#vm-hostpool", "请选择VM集群");
        var name2 = $(this).val();
        var datacenter_list = data.dq_info.hastodatacenter_dq[name2];
        datacenter_list = datacenter_list.unique();
        if (datacenter_list && name2 != "-1") {
            for (var i = 0, len = datacenter_list.length; i < len; i++) {
                $("#vm-datacenter-room").append("<option value=" + name2 + "to" + datacenter_list[i] + ">" + datacenter_list[i] + "</option>");
            }
        } else {
            EsxFun.objInit("#vm-datacenter-room", "请选择VM所属机房");
            EsxFun.objInit("#vm-net-area", "请选择网络区域");
            EsxFun.objInit("#vm-net-area-segment", "请选择VM网段");
            EsxFun.objInit("#vm-hostpool", "请选择VM集群");
        }
    });
    $("#vm-datacenter-room").change(function () {
        EsxFun.objInit("#vm-net-area", "请选择网络区域");
        EsxFun.objInit("#vm-net-area-segment", "请选择VM网段");
        EsxFun.objInit("#vm-hostpool", "请选择VM集群");
        var name3 = $(this).val();
        var net_area_list_01 = data.dq_info.hastonetarea_dq[name3];
        var net_area_list_02 = data.dq_info.nonetonetarea_dq[name3];
        var area_arr3 = data.zb_info.tonetarea_ZB[name3];

        function setHtml(list, name) {
            if (name != "-1") {
                list = list.unique();
                for (var i = 0, len = list.length; i < len; i++) {
                    $("#vm-net-area").append("<option value=" + name + "to" + list[i] + ">" + list[i] + "</option>");
                }
            } else {
                EsxFun.objInit("#vm-net-area", "请选择网络区域");
                EsxFun.objInit("#vm-net-area-segment", "请选择VM网段");
                EsxFun.objInit("#vm-hostpool", "请选择VM集群");
            }
        }

        if (net_area_list_01) {
            setHtml(net_area_list_01, name3);
        } else if (net_area_list_02) {
            setHtml(net_area_list_02, name3);
        } else if (area_arr3) {
            setHtml(area_arr3, name3);
        } else {
            EsxFun.objInit("#vm-net-area", "请选择网络区域");
            EsxFun.objInit("#vm-net-area-segment", "请选择VM网段");
            EsxFun.objInit("#vm-hostpool", "请选择VM集群");
        }
    });
    $("#vm-net-area").change(function () {
        EsxFun.objInit("#vm-net-area-segment", "请选择VM网段");
        EsxFun.objInit("#vm-hostpool", "请选择VM集群");
        var arr = allEnvArr;
        var envi = $("#vm-enviroment-room").val();
        var dc_type = arr.indexOf(envi);
        var datacenter = $("#vm-datacenter-room option:selected").text();
        var net_area = $("#vm-net-area option:selected").text();
        var segment_key = dc_type + "to" + datacenter + "to" + net_area;
        var segmentlist = EsxFun.data.segmentlist[segment_key];

        if (segmentlist) {
            segmentlist = segmentlist.unique();
            for (var j = 0, len = segmentlist.length; j < len; j++) {
                var item = segmentlist[j];
                $("#vm-net-area-segment").append("<option value=" + j + ">" + item + "</option>")
            }
        }else{
            showMessage("该网络区域没有网段信息","danger",2000);
        }


        var name4 = $(this).val();
        var hostpool_list_01 = data.dq_info.hastohostpool_dq[name4];
        var hostpool_list_02 = data.dq_info.nonetohostpool_dq[name4];
        var hostpool_list_03 = data.zb_info.tohostpool_ZB[name4];

        function setHostpool(list, name) {
            if (name != "-1") {
                for (var i = 0, len = list.length; i < len; i++) {
                    $("#vm-hostpool").append("<option value=" + list[i][0] + ">" + list[i][1] + "</option>");
                }
            } else {
                EsxFun.objInit("#vm-net-area-segment", "请选择VM网段");
                EsxFun.objInit("#vm-hostpool", "请选择VM集群");
            }
        }

        if (hostpool_list_01) {
            setHostpool(hostpool_list_01, name4);
        } else if (hostpool_list_02) {
            setHostpool(hostpool_list_02, name4);
        } else if (hostpool_list_03) {
            setHostpool(hostpool_list_03, name4);
        } else {
            EsxFun.objInit("#vm-net-area-segment", "请选择VM网段");
            EsxFun.objInit("#vm-hostpool", "请选择VM集群");
        }
    });
};
EsxFun.getQuato = function () {

    $("#cpu-number").change(function () {
        EsxFun.objInit("#mem-number", "请选择内存容量");
        var name = $(this).val();
        var list = EsxFun.data.quota["mem_arr"];
        list = list[name];
        if (name != "-1") {
            for (var i = 0; i < list.length; i++) {
                var tmp = list[i];
                tmp >= 1024 && (tmp = tmp / 1024 + "G");
                tmp < 1024 && (tmp = tmp  + "MB");
                $("#mem-number").append("<option value=" + name + list[i] + ">" + tmp + "</option>");
            }
        } else {
            EsxFun.objInit("#mem-number", "请选择内存容量");
        }
    });


};
EsxFun.esxsubmit = function () {
    var hostpool_id = $("#vm-hostpool").val();
    if (hostpool_id == "-1") {
        showMessage("请选择VM集群", "danger", 600);
        return;
    }
    var mem_str = $("#mem-number").val();
    if (mem_str != "-1") {
        EsxFun.requestParams.flavor_id = EsxFun.data.quota.disk_arr[mem_str][0][0];
    } else {
        showMessage("请选择内存容量", "danger", 600);
        return;
    }
    if ($("#vm-app-info").val() != "") {
        EsxFun.requestParams.vm_app_info = $("#vm-app-info").val()
    }
    else {
        showMessage("请填写应用系统信息", "danger", 600);
        return;
    }

    let list = EsxFun.data.grouplist;
    let arr = allEnvArr;
    let envCode = arr.indexOf($("#esx-envi-vm").val());
    let groupList_ = [];
    for (var i = 0, len = list.length; i < len; i++) {
        if (envCode == list[i].dc_type) {
            groupList_.push(list[i])
        }
    }
    if (blurCheckGroup("#vm-group", groupList_)) {
        EsxFun.requestParams.vm_group_id = $("#vm-group").attr("data-group-id")
    }
    else {
        showMessage("应用组不合法", "danger", 600);
        return;
    }

    if ($("#vm-admin").val() != "") {
        EsxFun.requestParams.vm_app_info = $("#vm-admin").val()
    }
    else {
        showMessage("请填写VM应用管理员", "danger", 600);
        return;
    }

    if (!$("#vm-type").val() != "-1") {
        EsxFun.requestParams.vm_app_info = $("#vm-type").val()
    }
    else {
        showMessage("请选择VM类型", "danger", 600);
        return;
    }

    if ($("#vm-net-area-segment option:selected").text() != "请选择VM网段") {
        EsxFun.requestParams.vm_app_info = $("#vm-net-area-segment option:selected").text()
    }
    else {
        showMessage("请选择VM网段", "danger", 600);
        return;
    }

    EsxFun.requestParams.vm_app_info = $("#vm-app-info").val();
    EsxFun.requestParams.vm_group_id = $("#vm-group").attr("data-group-id");
    EsxFun.requestParams.vm_owner = $("#vm-admin").val();
    EsxFun.requestParams.vm_ostype = $("#vm-type").val();
    EsxFun.requestParams.segment = $("#vm-net-area-segment option:selected").text();
    EsxFun.requestParams.retry = 0;
    EsxFun.requestParams.user_id = user_id_num;
    console.log(EsxFun.requestParams);
    $.ajax({
        url: "/v2v/esx/" + hostpool_id,
        type: "post",
        dataType: "json",
        data: EsxFun.requestParams,
        beforeSend: function () {
            $("#loading").css("display", "block");
        },
        success: function (res) {
            $("#loading").css("display", "none");
            if (res.code != 0) {
                res.msg != null ? showMessage(res.msg, "danger", 2000) : showMessage("操作失败,请刷新重试", "danger", 2000);
                return;
            } else {
                $("#esxtokvm-modal").modal("hide");
                showMessage("操作成功", "success", 2000);
                $('#migrateTable').bootstrapTable('refresh', {silent: true});
            }
        },
        error: function () {

        }
    });

};

EsxFun.batchData = {};
EsxFun.pivot = false;
EsxFun.batcharr = [];
EsxFun.errList = [];
EsxFun.requsetErr = [];
EsxFun.batchNum = 0;
EsxFun.groupList = [];
EsxFun.esxbatchInitInfo = function () {
    var input_arr1 = ["#esx-batch-paseeword","#esx-batch-ip", "#esx-batch-admin", "#esx-batch-group", "#esx-batch-appinfo", "#esx-batch-hostpool", "#esx-batch-vmware-name", "#esx-batch-vmos-name", "#esx-batch-vmos", "#esx-batch-vmip"];
    var sel_arr2 = ["#esx-batch-mem", "#esx-batch-cpu", "#esx-batch-vmsegment"];
    var sel_default_arr3 = ["#esx-batch-vmstyle", "#esx-batch-env"];
    OpenstackFun.batchHtmlInit.call(this, input_arr1, sel_arr2, sel_default_arr3);
    $("#esx-batch-group").attr("data-group-id", '')
    $("#main-paper").css("display", "none");
    $("#esx-paper").css("display", "block");
    $.ajax({
        url: "/v2v/esx/init",
        type: "get",
        dataType: "json",
        success: function (res) {
            if (res.code != 0) {
                res.msg != null ? showMessage(res.msg, "danger", 2000) : showMessage("获取数据失败，请刷新重试", "danger", 2000)
            } else {
                var list = EsxFun.handleEsxData(res);
                EsxFun.batchData = list;
                var cpu_list = list.quota.cpu_arr;
                EsxFun.groupList = list.grouplist;
                for (var i = 0; i < cpu_list.length; i++) {
                    $("#esx-batch-cpu").append("<option value=cpu" + cpu_list[i] + ">" + cpu_list[i] + "核</option>");
                }
            }
        },
        error: function () {
            showMessage("获取数据失败，请刷新重试", "danger", 2000);
        }
    });


};
EsxFun.esxBatchHostpool = function () {
    //console.log(EsxFun.batchData);
    var input_arr1 = ["#esx-vm-enviroment-room"];
    var sel_arr2 = ["#esx-vm-hostpool", "#esx-vm-net-area", "#esx-vm-datacenter-room", "#esx-vm-childarea-room", "#esx-vm-area-room"];
    var sel_default_arr3 = ["#esx-vm-datacenter-area"];
    OpenstackFun.batchHtmlInit.call(this, input_arr1, sel_arr2, sel_default_arr3);
    var env_code = $("#esx-batch-env").val();
    var env = $("#esx-batch-env").children(':selected').text();
    if (env_code == "-1") {
        showMessage("请先选择ESX环境","danger",2000);
        return;
    }
    var areaList = EsxFun.batchData.arealist;
    var list_dq = areaList.dq_info.toarea_dq["to"+env_code];
    var list_zb = areaList.zb_info.todatacenter_ZB["to"+env_code];

        if (!list_dq && !list_zb) {
            showMessage(env + "环境下没有集群信息，请重新选择环境", "danger", 2000);
            return;
        } else if (!list_dq) {
            $("#esx-vm-datacenter-area").html('<option value="-1">请选择机房区域</option><option value="总部">总部</option>');
        } else if (!list_zb) {
            $("#esx-vm-datacenter-area").html('<option value="-1">请选择机房区域</option><option value="地区">地区</option>');
        } else {
            $("#esx-vm-datacenter-area").html('<option value="-1">请选择机房区域</option><option value="总部">总部</option><option value="地区">地区</option>');
        }



    //console.log(EsxFun.batchData);
    $("#esx-vm-enviroment-room").val(env).attr("data-dctype", env_code);
    $("#esx-areabox").css("display", "none");
    $(".esx_child_area_show").css("display", "none");
    $("#esxtokvm-hostpool-modal").modal("show");

};
EsxFun.isemptyObject = function(e)//判断一个对象是否为空
{
        var t;
        for (t in e)
            return !1;
        return !0
};

EsxFun.esxBatchQuato = function (that) {
     OpenstackFun.batchHtmlInit.call(that, [], ["#esx-batch-mem"], []);
    var cpu = $(that).val();
    if(cpu == "-1"){
        return;
    }
    var list = EsxFun.batchData.quota.mem_arr[cpu];
    list.forEach(function(tmp){
        var mem = parseInt(tmp) >= 1024 ? (parseInt(tmp)/1024+"G") : (tmp +"MB");
        $("#esx-batch-mem").append("<option value="+cpu+tmp+">"+mem+"</option>");
    })
};
EsxFun.removeEventFun = function(arr){
    for(var i = 0,tmp;tmp = arr[i++];){
         $(tmp).unbind("change");
    }

};
EsxFun.esxBatch_ZB = function(){
    var env_code = $("#esx-vm-enviroment-room").attr("data-dctype")
    var name = "to"+env_code;
    var list = EsxFun.batchData.arealist.zb_info;
    var datacenter_ZB = list.todatacenter_ZB[name];
    if(datacenter_ZB){
        datacenter_ZB = datacenter_ZB.unique();
        datacenter_ZB.forEach(function(tmp){
            $("#esx-vm-datacenter-room").append("<option value="+env_code+"to"+tmp+">"+tmp+"</option>");
        });
    }else{
        showMessage("该环境下的总部没有资源","danger",2000);
        return;
    }
    $("#esx-vm-datacenter-room").change(function(){
        var name1 = $(this).val();
        var netarea_ZB = list.tonetarea_ZB[name1];
        OpenstackFun.batchHtmlInit.call(this, [], ["#esx-vm-hostpool","#esx-batch-vmsegment", "#esx-vm-net-area"], []);
        if(netarea_ZB){
            netarea_ZB = netarea_ZB.unique();
            netarea_ZB.forEach(function (tmp) {
                $("#esx-vm-net-area").append("<option value=" + name1 + "to" + tmp + ">" + tmp + "</option>");
            });
        }
    });
    $("#esx-vm-net-area").change(function(){
        var name2 = $(this).val();
        var hostpool_ZB = list.tohostpool_ZB[name2];
        var segment_ZB = EsxFun.batchData.segmentlist[name2]
        OpenstackFun.batchHtmlInit.call(this, [], ["#esx-vm-hostpool","#esx-batch-vmsegment"], []);
        if(hostpool_ZB){
            hostpool_ZB.forEach(function (tmp) {
                $("#esx-vm-hostpool").append("<option value=" + tmp[0] + ">" + tmp[1] + "</option>");
            });
        }
        if(segment_ZB){
            segment_ZB.forEach(function (tmp) {
                $("#esx-batch-vmsegment").append("<option value=" + tmp + ">" + tmp + "</option>");
            });
        }
    });
};
EsxFun.esxBatch_DQ = function(){
    var list_dq = EsxFun.batchData.arealist.dq_info;
    var env_code = $("#esx-vm-enviroment-room").attr("data-dctype")
    var name1 = "to" + env_code;
    var area_dq = list_dq.toarea_dq[name1];
    if(area_dq){
        area_dq = area_dq.unique();
        area_dq.forEach(function(tmp){
            $("#esx-vm-area-room").append("<option value="+env_code+"to"+tmp+">"+tmp+"</option>");
        })
    }else{
      showMessage("该环境下的地区没有资源","danger",2000);
      return;
    }
    $("#esx-vm-area-room").change(function(){
        OpenstackFun.batchHtmlInit.call(this, ["#esx-batch-hostpool"], ["#esx-vm-hostpool","#esx-batch-vmsegment", "#esx-vm-net-area", "#esx-vm-datacenter-room", "#esx-vm-childarea-room"], []);
        var area_name = $(this).val();
        var has_area_list = list_dq.hastochildarea_dq[area_name];
        var none_area_list = list_dq.nonetodatacenter_dq[area_name];
        if(has_area_list){
            has_area_list = has_area_list.unique();
            has_area_list.forEach(function(tmp){
                $("#esx-vm-childarea-room").append("<option value="+area_name+"to"+tmp+">"+tmp+"</option>");
            });
            $(".esx_child_area_show").css("display","block");
            EsxFun.pivot = true;
        }
        if (none_area_list) {
            $(".esx_child_area_show").css("display","none");
            none_area_list = none_area_list.unique();
            EsxFun.pivot = false;
            none_area_list.forEach(function (tmp) {
                $("#esx-vm-datacenter-room").append("<option value=" + area_name + "to" + tmp + ">" + tmp + "</option>");
            });
        }
    });
    $("#esx-vm-childarea-room").change(function(){
         OpenstackFun.batchHtmlInit.call(this, ["#esx-batch-hostpool"], ["#esx-vm-hostpool","#esx-batch-vmsegment", "#esx-vm-net-area", "#esx-vm-datacenter-room"], []);
        var child_area_name = $(this).val();
        var child_area_dq = list_dq.hastodatacenter_dq[child_area_name];
        if(EsxFun.pivot && child_area_dq){
             child_area_dq = child_area_dq.unique();
             child_area_dq.forEach(function (tmp) {
                $("#esx-vm-datacenter-room").append("<option value=" + child_area_name + "to" + tmp + ">" + tmp + "</option>");
            });
        }
    });
    $("#esx-vm-datacenter-room").change(function () {
        OpenstackFun.batchHtmlInit.call(this, ["#esx-batch-hostpool"], ["#esx-vm-hostpool", "#esx-batch-vmsegment", "#esx-vm-net-area"], []);
        var _datacenter_dq = $(this).val();
        var netarea_dq;
        if (EsxFun.pivot) {
            netarea_dq = list_dq.hastonetarea_dq[_datacenter_dq];
        } else {
            netarea_dq = list_dq.nonetonetarea_dq[_datacenter_dq];
        }
        netarea_dq = netarea_dq.unique();
        netarea_dq.forEach(function (tmp) {
            $("#esx-vm-net-area").append("<option value=" + _datacenter_dq + "to" + tmp + ">" + tmp + "</option>");
        });
    });
    $("#esx-vm-net-area").change(function(){
         OpenstackFun.batchHtmlInit.call(this, ["#esx-batch-hostpool"], ["#esx-vm-hostpool", "#esx-batch-vmsegment"], []);
         var _netarea_dq = $(this).val();
         var hostpool_dq ;
        if(EsxFun.pivot){
            hostpool_dq = list_dq.hastohostpool_dq[_netarea_dq];
        }else{
            hostpool_dq = list_dq.nonetohostpool_dq[_netarea_dq];
        }
        //hostpool_dq = hostpool_dq.unique();
         hostpool_dq.forEach(function (tmp) {
            $("#esx-vm-hostpool").append("<option value=" +  tmp[0] + ">" + tmp[1] + "</option>");
        });

        var hj_name = $("#esx-vm-enviroment-room").attr("data-dctype");
        var jf_name = $("#esx-vm-datacenter-room option:selected").text();
        var wq_name = $("#esx-vm-net-area option:selected").text();
        var name = hj_name + "to" + jf_name + "to" + wq_name;
        var segment_list = EsxFun.batchData.segmentlist[name];
        //segment_list = segment_list.unique();
        if (segment_list != undefined) {
            segment_list.forEach(function (tmp) {
                $("#esx-batch-vmsegment").append("<option value=" + tmp + ">" + tmp + "</option>");
            })
        }else{
            showMessage("该网络区域下没有网段","danger",2000);
        }


    });
};
EsxFun.judgeNull = function(input_list,sel_list){
    var deg = true;
    input_list.forEach(function(tmp){
        if (deg) {
            if (tmp[0] == "") {
                showMessage(tmp[1], "danger", 1000);
                deg = false;
                return false;
            }
        }
    });

    sel_list.forEach(function (tmp) {
        if (deg) {
            if (tmp[0] == "-1") {
                deg = false;
                showMessage(tmp[1], "danger", 1000);
                return false;
            }
        }

    });

    if(deg){return true;}
};
EsxFun.getesxaddInfo = function(){
     if(EsxFun.batcharr.length>=10){
        showMessage("最多只能添加10条数据","danger",1000);
        return false;
    }
    var esx_passwd =  $("#esx-batch-paseeword").val();
    var base = new Base64();
    esx_passwd = base.encode(esx_passwd);
    var esx_ip = $("#esx-batch-ip").val();
    var patt1 = new RegExp("^(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|[1-9])\\." + "(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|\\d)\\." + "(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|\\d)\\." + "(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|\\d)$");
    var result2 = patt1.test(esx_ip);
    if (result2 != true) {
        showMessage("请输入正确的ESX IP地址", "danger", 1200);
        return false;
    }
    var vmware_vm = $("#esx-batch-vmware-name").val();
    var vm_name = $("#esx-batch-vmos-name").val();
    var vm_osver = $("#esx-batch-vmos").val();
    var vm_ip = $("#esx-batch-vmip").val();
    var result3 = patt1.test(vm_ip);
    if (result3 != true) {
        showMessage("请输入正确的VM IP地址", "danger", 1200);
        return false;
    }
    var hostpool_id = $("#esx-batch-hostpool").attr("data-hostpool-id");
    var hostpool = $("#esx-batch-hostpool").val();
    var vm_app_info = $("#esx-batch-appinfo").val();
    var vm_owner = $("#esx-batch-admin").val();

    var esx_env = $("#esx-batch-env").val();
    var env = $("#esx-batch-env option:selected").text();
    var vm_segment = $("#esx-batch-vmsegment").val();
    var vm_ostype = $("#esx-batch-vmstyle").val();
    var vm_group_id = $("#esx-batch-group").attr('data-group-id');
    var group = $("#esx-batch-group").val();
    if (!blurCheckGroup("#esx-batch-group", EsxFun.groupSel)) {
        showMessage("所选应用组的名称不存在", "danger", 600)
        return;
    }
    var  user_id = user_id_num;

    var input_list = [
         [esx_passwd,"请输入ROOT密码"],
        [vmware_vm,"请输入VM WARE虚拟机名称"],
        [vm_name,"请输入VM名称"],
        [vm_name,"请输入VM OS名称"],
        [vm_osver,"请输入VM OS版本"],
        [hostpool_id,"请编辑VM集群"],
        [vm_app_info,"请输入应用系统信息"],
        [vm_owner,"请输入应用管理员"],
        [vm_group_id,"请选择应用组"]
    ];
    var sel_list = [
        [esx_env,"请选择ESX环境"],
        [vm_segment,"请选择VM网段"],
        [vm_ostype,"请选择VM类型"]
    ];
    var obj = {};
    if (EsxFun.judgeNull(input_list, sel_list)) {
        var mem_index = $("#esx-batch-mem").val();
        var mem = $("#esx-batch-mem option:selected").text();
        var cpu = $("#esx-batch-cpu option:selected").text();
        if (mem == "-1") {
            showMessage("请选择	内存容量", "danger", 2000);
            return false;
        }
        var flavor_list = EsxFun.batchData.quota.disk_arr;
        flavor_list = flavor_list[mem_index];
        flavor_id = flavor_list[0][0];
        var _deg_ = true;
        if(EsxFun.batcharr.length>0){
            EsxFun.batcharr.forEach(function(tmp){
                if(
                    tmp.vmware_vm == vmware_vm ||
                    tmp.vm_name == vm_name ||
                    tmp.vm_ip == vm_ip
                ){
                    showMessage("VM WARE、VM OS名称、VM IP不能重复添加","danger",2000);
                    _deg_ = false;
                }
            });
        }

        if (_deg_) {
            obj.esx_passwd = esx_passwd;
            obj.esx_env = esx_env;
            obj.esx_ip = esx_ip;
            obj.vmware_vm = vmware_vm;
            obj.vm_name = vm_name;
            obj.vm_osver = vm_osver;
            obj.vm_ip = vm_ip;
            obj.vm_app_info = vm_app_info;
            obj.vm_owner = vm_owner;
            obj.hostpool_id = hostpool_id;
            obj.vm_segment = vm_segment;
            obj.vm_ostype = vm_ostype;
            obj.vm_group_id = vm_group_id;
            obj.flavor_id = flavor_id;
            obj.user_id = user_id;
            obj.env = env;
            obj.group = group;
            obj.cpu = cpu;
            obj.mem = mem;
            obj.hostpool = hostpool;
            EsxFun.batcharr.push(obj);
            return true;
        }
    }
};
EsxFun.esxcreateTable = function(){
    var list = EsxFun.batcharr;
    var num = parseInt(EsxFun.batchNum)+1;
    var tmp = list[EsxFun.batchNum];
    var html ="";

        html += '<tr data-row='+tmp.vm_name+'>';
        html += '<td>' + num + '</td>';
        html += '<td title="ESX 环境">' + tmp.env + '</td>';
        html += '<td title="ESX IP">' + tmp.esx_ip + '</td>';
        html += '<td title="VM WARE虚拟机名称">' + tmp.vmware_vm + '</td>';
        html += '<td title="VM OS名称">' + tmp.vm_name + '</td>';
        html += '<td title="VM OS版本">' + tmp.vm_osver + '</td>';
        html += '<td title="VM IP">' + tmp.vm_ip + '</td>';
        html += '<td title="VM环境">' + tmp.env + '</td>';
        html += '<td title="VM所在网段">' + tmp.vm_segment + '</td>';
        html += '<td title="VM集群">' + tmp.hostpool + '</td>';
        html += '<td title="VM系统版本">' + tmp.vm_ostype + '</td>';
        html += '<td title="应用组">' + tmp.group + '</td>';
        html += '<td title="CPU数量">' + tmp.cpu + '</td>';
        html += '<td title="内存容量">' + tmp.mem + '</td>';
        html += '<td title="应用系统信息">' + tmp.vm_app_info + '</td>';
        html += '<td title="VM管理员">' + tmp.vm_owner + '</td>';
        html += '<td><a href="" class="delete-esx-one">删除</a></td>';
        html += '</tr>';

    return html;
};
EsxFun.handleErr = function(list,html,bool,requestBool){
    var list = list || [];
    var middle_arr = [];

     list.forEach(function (tmp) {
        $("#esx-batch-info-table").children('[data-row=' + tmp.vm_name + ']').css("color", "#f00");
        html += '<tr>';
        html += '<td>' + tmp.vm_name + '</td>';
        html += '<td>' + tmp.error_message + '</td>';
        html += '</tr>';
         if(bool){
             EsxFun.errList.push(tmp);
         }
         if(requestBool){
             middle_arr.push(tmp.vm_name)
         }
    });
    if (requestBool) {
        var _list_ = EsxFun.batcharr;
        _list_.forEach(function (item, index) {
            if (middle_arr.indexOf(item.vm_name) == -1){
                EsxFun.batcharr.splice(index,1);
                $("#esx-batch-info-table").children('[data-row=' + item.vm_name + ']').remove();
                EsxFun.batchNum -= 1;
                var ele_list = $("#esx-batch-info-table").children().children(":first-child");
                for (var i = 0; i < ele_list.length; i++) {
                    $(ele_list[i]).html(i + 1);
                }
            }
        });
    }

    $("#err-box").html(html);
    $("#warning-text").html("请认真核对信息,再做提交");
    $("#batch-err-modal").modal("show");
};
EsxFun.esxBatchSubmit = function () {
    if(EsxFun.errList.length>0){
        var html = "";
        EsxFun.handleErr(EsxFun.errList,html,false);
        return;
    }

    if (EsxFun.batcharr.length > 0) {
        var paramsList = [];
        EsxFun.batcharr.forEach(function (tmp) {
            var params = {};
            params.esx_passwd = tmp.esx_passwd;
            params.esx_env = tmp.esx_env;
            params.esx_ip = tmp.esx_ip;
            params.vmware_vm = tmp.vmware_vm;
            params.vm_name = tmp.vm_name;
            params.vm_osver = tmp.vm_osver;
            params.vm_ip = tmp.vm_ip;
            params.vm_app_info = tmp.vm_app_info;
            params.vm_owner = tmp.vm_owner;
            params.hostpool_id = tmp.hostpool_id;
            params.vm_segment = tmp.vm_segment;
            params.vm_ostype = tmp.vm_ostype;
            params.vm_group_id = tmp.vm_group_id;
            params.flavor_id = tmp.flavor_id;
            params.user_id = tmp.user_id;
            paramsList.push(params);
        });
        esx_batch = JSON.stringify(paramsList);
        $.ajax({
            url: '/v2v/esx/batch',
            type: "post",
            dataType: 'json',
            data: {"esx_batch": esx_batch},
            beforeSend: function () {
                $("#loading").css("display", "block");
            },
            success: function (res) {
                $("#loading").css("display", "none");
                if (res.code != 0) {
                    if (res.data) {
                         var err_list = res.data;
                        var html ="";
                        EsxFun.handleErr(err_list,html,true);
                    } else {
                        res.msg == null ? showMessage("请求失败,请刷新重试！！！", "danger", 1000) : showMessage(res.msg, "danger", 1000);

                    }
                } else {
                    if (res.data.length > 0) {
                        var list = res.data;
                        var html ="";
                        EsxFun.handleErr(list,html,true,true);
                    } else {
                        showMessage("操作成功", "success", 1000);
                        EsxFun.batcharr = [];
                        EsxFun.pivot = false;
                        EsxFun.batchData = [];
                        EsxFun.errList = [];
                        $("#esx-batch-info-table").html("");
                        $("#main-paper").css("display", "block");
                        $("#esx-paper").css("display", "none");
                    }
                     $("#migrateTable").bootstrapTable('refresh', {silent: true});
                }
            },
            error: function () {
                showMessage("请求失败,请刷新重试", "danger", 2000);
            }
        });
    } else {
        showMessage("暂无数据可提交迁移,请添加数据！", "danger", 2000);
    }
};
function Base64() {

    // private property
    _keyStr = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";

    // public method for encoding
    this.encode = function (input) {
        var output = "";
        var chr1, chr2, chr3, enc1, enc2, enc3, enc4;
        var i = 0;
        input = _utf8_encode(input);
        while (i < input.length) {
            chr1 = input.charCodeAt(i++);
            chr2 = input.charCodeAt(i++);
            chr3 = input.charCodeAt(i++);
            enc1 = chr1 >> 2;
            enc2 = ((chr1 & 3) << 4) | (chr2 >> 4);
            enc3 = ((chr2 & 15) << 2) | (chr3 >> 6);
            enc4 = chr3 & 63;
            if (isNaN(chr2)) {
                enc3 = enc4 = 64;
            } else if (isNaN(chr3)) {
                enc4 = 64;
            }
            output = output +
                _keyStr.charAt(enc1) + _keyStr.charAt(enc2) +
                _keyStr.charAt(enc3) + _keyStr.charAt(enc4);
        }
        return output;
    }

    // public method for decoding
    this.decode = function (input) {
        var output = "";
        var chr1, chr2, chr3;
        var enc1, enc2, enc3, enc4;
        var i = 0;
        input = input.replace(/[^A-Za-z0-9\+\/\=]/g, "");
        while (i < input.length) {
            enc1 = _keyStr.indexOf(input.charAt(i++));
            enc2 = _keyStr.indexOf(input.charAt(i++));
            enc3 = _keyStr.indexOf(input.charAt(i++));
            enc4 = _keyStr.indexOf(input.charAt(i++));
            chr1 = (enc1 << 2) | (enc2 >> 4);
            chr2 = ((enc2 & 15) << 4) | (enc3 >> 2);
            chr3 = ((enc3 & 3) << 6) | enc4;
            output = output + String.fromCharCode(chr1);
            if (enc3 != 64) {
                output = output + String.fromCharCode(chr2);
            }
            if (enc4 != 64) {
                output = output + String.fromCharCode(chr3);
            }
        }
        output = _utf8_decode(output);
        return output;
    }

    // private method for UTF-8 encoding
    _utf8_encode = function (string) {

        string = string.replace(/\r\n/g, "\n");

        var utftext = "";
        for (var n = 0; n < string.length; n++) {
            var c = string.charCodeAt(n); //返回返回指定位置的字符的 Unicode 编码。这个返回值是 0 - 65535 之间的整数。
            if (c < 128) {
                utftext += String.fromCharCode(c); //接受一个指定的 Unicode 值，然后返回一个字符串。

            } else if ((c > 127) && (c < 2048)) {
                utftext += String.fromCharCode((c >> 6) | 192);
                utftext += String.fromCharCode((c & 63) | 128);

            } else {
                utftext += String.fromCharCode((c >> 12) | 224);
                utftext += String.fromCharCode(((c >> 6) & 63) | 128);
                utftext += String.fromCharCode((c & 63) | 128);

            }

        }
        return utftext;
    }

    // private method for UTF-8 decoding
    _utf8_decode = function (utftext) {
        var string = "";
        var i = 0;
        var c = c1 = c2 = 0;
        while (i < utftext.length) {
            c = utftext.charCodeAt(i);
            if (c < 128) {
                string += String.fromCharCode(c);
                i++;
            } else if ((c > 191) && (c < 224)) {
                c2 = utftext.charCodeAt(i + 1);
                string += String.fromCharCode(((c & 31) << 6) | (c2 & 63));
                i += 2;
            } else {
                c2 = utftext.charCodeAt(i + 1);
                c3 = utftext.charCodeAt(i + 2);
                string += String.fromCharCode(((c & 15) << 12) | ((c2 & 63) << 6) | (c3 & 63));
                i += 3;
            }
        }
        return string;
    }
}