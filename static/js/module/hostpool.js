/**
 * Created by 80002473 on 2017/3/30.
 */
var hostPoolObject = {
    hostpoolInfo: null,//创建集群中的联动筛选信息变量
    minusCount: function (className) {
        var num = parseInt($('.' + className).val());
        num -= 1;
        if (num < 0) {
            return;
        }
        $('.' + className).val(num);
    },//减
    plusCount: function (className) {
        var num = parseInt($('.' + className).val());
        num += 1;
        if (num >= 1000) {
            return;
        }
        $('.' + className).val(num);
    },//加
    addHost: function () {//单行操作创建主机
        var str = $('#myform').serialize();
        var ip_address = $("#new_ipaddress").val();
        var manage_ip = $("#new_manage_ip").val();
        var hostpool_id = parseInt($("#createHostOpera").attr('data-hostpoolId'));

        var patt1 = new RegExp("^(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|[1-9])\\." + "(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|\\d)\\." + "(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|\\d)\\." + "(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|\\d)$");
        var result1 = patt1.test(ip_address);
        var result2 = patt1.test(manage_ip);
        if (result1 != true || result2 != true) {
            showMessage("请输入正确的ip地址", "danger", 1200);
            return;
        }
        if ($("#new_hostname").val().length > 16) {
            showMessage("主机名称长度不能超过16个字符", "danger", 1200);
            return;
        }
        str = str + "&ip_address=" + ip_address + "&manage_ip=" + manage_ip;
           console.log(str);
        $.ajax({
            url: "/host/" + hostpool_id,
            type: "post",
            data: str,
            dataType: "json",
            beforeSend: function () {
                $("#loading").css("display", "block");
                $('#addHostModal').modal("hide");
            },
            success: function (result) {
                $("#loading").css("display", "none");
                if (result.code != 0) {
                    result.msg != null ? showMessage(result.msg, "danger", 2000) : showMessage("操作失败请刷新重试", "danger", 2000);
                } else {
                    showMessage("创建成功", "success", 1000);
                }
                //console.log("添加成功");
                $('#host_pool_list').bootstrapTable('refresh');
            }
        });

    },
    createHostpoolInfoInit: function () { //创建集群中的连动筛选
        hostPoolObject.htmlInit.areaHtml();
        hostPoolObject.htmlInit.hostHtml();
        hostPoolObject.htmlInit.netAreaHtml();
        $(".childAreaShow").removeClass("show").addClass("hidden");


        $("#createHostPool input").val("");
        $(".hostCount-limit").val(2);
        var hostpool = this;
        $.ajax({
            url: "/net_area/levelinfo",
            type: "get",
            dataType: "json",
            success: function (result) {
                if (result.code != 0) {
                     result.msg != null ? showMessage(result.msg, "danger", 1000) :showMessage("操作失败", "danger", 1000);
                    return;
                }
                var list = result.data.level_info;

                var areaArr = [];
                var html = '<option value="-1">请选择区域</option>';
                hostpool.hostpoolInfo = list;
                $.each(list, function (index, tmp) {
                    areaArr.push(tmp.area);
                });
                areaArr = areaArr.unique();
                for (var i = 0; i < areaArr.length; i++) {
                    html += '<option value=' + i + '>' + areaArr[i] + '</option>';
                }
                $("#some-area").html(html);
            }
        });
    },
    htmlInit: {
        areaHtml: function () {
            $('#some-area-child').html('<option value="-1">请选择子区域</option>')
        },
        hostHtml: function () {
            $('#host-house').html('<option value="-1">请选择机房名</option>')
        },
        netAreaHtml: function () {
            $('#net-area').html('<option value="-1">请选择网络区域</option>')
        },
        initHostPool: function () {
            $("#hostpoolName").val("");
        },
       initHostPool: function () {
            $("#hostpoolmessage").val("");
        },
    },
    getIndex:function(str){
        var environments_arr = allEnvArr;
        return environments_arr.indexOf(str);
    },
    areaChild: function () {
        var areaSelected = $('#some-area option:selected').html();
        var childAreaArr = [];
        var datacenterArr = [];
        var childHtml = '<option value="-1">请选择子区域</option>';
        var datacenterHtml = '<option value="-1">请选择机房</option>';

        $.each(this.hostpoolInfo, function (index, tmp) {
            if (tmp.area == areaSelected) {
                 var environments_arr = allEnvArr;
                if (tmp.child_area == null) {
                    $(".childAreaShow").removeClass("show").addClass("hidden");
                    datacenterArr.push(tmp.datacenter+"-"+environments_arr[tmp.dc_type]);
                } else {
                    $(".childAreaShow").removeClass("hidden").addClass("show");
                    childAreaArr.push(tmp.child_area);
                }
            }

        });

        //如果存在子区域，则生成子区域下拉列表
        childAreaArr = childAreaArr.unique();
        datacenterArr = datacenterArr.unique();
        //console.log(datacenterArr);
        var childAreaLength = childAreaArr.length;

        if (childAreaLength != 0) {
            for (var i = 0; i < childAreaLength; i++) {
                childHtml += '<option value=' + childAreaArr[i] + ">" + childAreaArr[i] + '</option>';
            }
            $('#some-area-child').html(childHtml);
            hostPoolObject.htmlInit.hostHtml();
        } else {
            for (var i = 0; i < datacenterArr.length; i++) {
                datacenterHtml += '<option value=' + datacenterArr[i].substring(0,datacenterArr[i].lastIndexOf('-'))+ ">" + datacenterArr[i] + '</option>';
            }
            $('#host-house').html(datacenterHtml);
            hostPoolObject.htmlInit.netAreaHtml();
        }

    },
    childHostChoice: function () {//存在子区域时发生change事件生成host下拉列表
        var parentArea = $('#some-area option:selected').html();
        var childArea = $("#some-area-child").val();
        var hostArr = [];
        var hostHtml = '<option value="-1">请选择机房名</option>';
        $.each(this.hostpoolInfo, function (index, tmp) {
            //if(parentArea==tmp.area && childArea=="本部" && tmp.child_area==null){
            //    hostHtml+='<option value="-2">'+tmp.datacenter+'</option>';
            //}else
            if (tmp.child_area == childArea) {
                 environments = allEnvArr;
                 hostArr.push(tmp.datacenter+'-'+environments[tmp.dc_type]);
            }
        })
        hostArr = hostArr.unique();
        var hostArrLength = hostArr.length;
        for (var i = 0; i < hostArrLength; i++) {
            hostHtml += '<option value=' + hostArr[i].substring(0,hostArr[i].lastIndexOf('-')) + ">" + hostArr[i] + '</option>';
        }
        $('#host-house').html(hostHtml);
        hostPoolObject.htmlInit.netAreaHtml();
    },
    netAreaChoice: function () {//机房被选中之后生成网络区域下拉列表
        var hostName = $("#host-house").val();
        var hostName_dctype = $("#host-house option:selected").html();
        var _dc_type = this.getIndex(hostName_dctype.substring(hostName_dctype.lastIndexOf('-')+1,hostName_dctype.length));
        var netAreaHtml = '<option value="-1">请选择网络区域</option>';
        $.each(this.hostpoolInfo, function (index, tmp) {
            if (tmp.datacenter == hostName && tmp.dc_type == _dc_type) {
                netAreaHtml += '<option value=' + tmp.net_area_id + ">" + tmp.net_area_name + '</option>';
            }
        })
        $('#net-area').html(netAreaHtml);
    },
    createHostpool: function () {
        var name = $('#hostpoolName').val();
        var net_area_id = $('#net-area option:selected').val();
        if(net_area_id == -1){
            showMessage("请选择网络区域", "danger", 1000);
            return;
        }
        var least_host_num = $('.hostCount-limit').val();
        var hostpoolmessage   = $('#hostpoolmessage').val();
        //        console.log(name +'..'+net_area_id+'..'+least_host_num);
        if(least_host_num == "" || least_host_num>=1000){
            showMessage("Host数量下限不能为空且不能大于1000,请输入!","danger",1000);
            return;
        }

        $.ajax({
            url: '/hostpool/' + net_area_id,
            type: "post",
            data: {"name": name, "least_host_num": least_host_num,"app_code":hostpoolmessage},
            dataType: 'json',

            success: function (result) {
                // console.log(result.code);
                // console.log(result);
                // console.log(this.data)
                if (result.code != 0) {
                    result.msg ? showMessage(result.msg, "danger", 2000) : showMessage("操作失败请刷新重试", "danger", 2000);
                } else {
                    showMessage("创建成功", "success", 1000);
                }
                $('#host_pool_list').bootstrapTable('refresh');
                $('#createHostPool').modal("hide");
            }
        });
    },
    isEmpty: function (sel) {
        var list = $(sel);
        var listLength = list.length;
        for (var i = 0; i < listLength; i++) {
            if (list[i].value == '') {
                console.log(list[i].value);
                list[i].focus();
                return false;
            }
        }
    },
    table_formatter_oprate: function (value, row, index) {
        // '<a  class="seeInfo" data-toggle="modal" data-target="#hostMonitor" id="monitorPage" title="监控"><i class="fa fa-signal text-primary"></i></a>&nbsp;&nbsp;&nbsp;',
        var opreate_arr = [
            '<a class="addHostBtn" title="创建host" data-toggle="modal" data-target="#addHostModal"><i class="fa fa-plus text-info"></i></a>&nbsp;&nbsp;&nbsp;',
             '<a id="update_hostpool"  title="修改信息"><i class="fa fa-pencil-square"></i></a>&nbsp;&nbsp;',
            '<a class="deleteHostBtn" title="删除集群" data-toggle="modal" data-target="#deleteHostPool"><i class="fa fa-trash-o text-danger"></i></a>',
        ];
        if (row.hosts_nums != 0) {
            opreate_arr.pop();
        }
        return opreate_arr.join("");
    },
    //删除hostpool交互事件
    hostpool_delete:function(id_str){
        $.ajax({
            url:"/hostpool",
            type:"delete",
            data:{
               hostpool_ids:id_str
            },
            dataType: "json",
            beforeSend: function () {
                $("#loading").css("display", "block");
                 $("#deleteHostPool").modal('hide')
            },
            success:function(res){
                $("#loading").css("display", "none");
                if(res.code!=0){
                    res.msg!=null ? showMessage(res.msg,"danger",1000) : showMessage("操作失败请刷新重试","danger",1000)
                }else{
                     showMessage("操作成功","success",1000);
                }
                 $(".deleteHostpoolBtn").attr("disabled", true);
                $("#host_pool_list").bootstrapTable("refresh", {silent: true});
            },
            error:function(){
                $("#loading").css("display", "none");
                showMessage("操作失败请刷新重试","danger",1000);
            }

        });
    },
     //table选中删除按钮显示操作
    getselected_option: function () {
        var selected_list = $("#host_pool_list").bootstrapTable("getSelections");
        if (selected_list.length > 0) {
            $(".deleteHostpoolBtn").attr("disabled", false);
        } else {
            $(".deleteHostpoolBtn").attr("disabled", true);
        }
    }
}

window.operateClusterEvents = {

    //绑定监控信息事件
    "click #monitorPage": function (e, value, row, index) {
        console.info(document.getElementById('main'));
        myChart = echarts.init(document.getElementById('main'));
        init_echart_cpu_mem();
        $("#model-title").html(row.displayname);

        var hostpool_id = row.hostpool_id;
        var start_time = 30;
        var end_time = 30;
        var rep_url = "/hostpool/" + hostpool_id + "/monitor";
        sessionStorage.setItem("displayname", row.displayname);
        sessionStorage.setItem("hostpool_id", row.hostpool_id);
        sessionStorage.setItem("rep_url", rep_url);
        refresh_mon_cluser(row.displayname, hostpool_id, start_time, end_time, rep_url);
    },
    //删除集群事件
    "click .deleteHostBtn":function(e, value, row, index){
        $("#hostpool_table_list").html("");
            var html = "<tr>";
            html += "<td>"+row.displayname+"</td><td>"+row.net_area+"</td><td>"+row.datacenter+"</td>";
            html += "</tr>";
        $("#deleteHostPoolSure").attr("data-hostpool-ids",row.hostpool_id);
        $("#hostpool_table_list").html(html);
    },
    "click #update_hostpool":function(e, value, row, index){
        $("#updateHostpoolModal input").val("");
        $("#update-hostpool-name").val(row.displayname);
        $("#update-number-limit").val(row.least_host_num);
        $("#update_hostpool_sure").attr("data-hostpoolid",row.hostpool_id);
        $("#updateHostpoolModal").modal("show");
    }
}

window.onload = function () {
    init_hostpool_table();
    $('#host_pool_list').bootstrapTable('hideColumn', 'cpu_nums');
    $('#host_pool_list').bootstrapTable('hideColumn', 'mem_nums');
    $('#host_pool_list').bootstrapTable('hideColumn', 'least_host_num');
    refreshChart();

    $("#update_hostpool_sure").click(function(){
        var hostpool_id = $(this).attr("data-hostpoolid");
        var name = $("#update-hostpool-name").val();
         var least_host_num = $("#update-number-limit").val();
        if(name == ""){
            showMessage("集群名不能为空,请输入!","danger",1000);
            return;
        }
        if(least_host_num == "" || least_host_num>=1000){
            showMessage("Host数量下限不能为空且不能大于1000,请输入!","danger",1000);
            return;
        }
        $.ajax({
            url: "/hostpool/" + hostpool_id,
            type: "put",
            dataType: "json",
            data: {
               "name":name,
               "least_host_num":least_host_num,
            },
            success: function (res) {
                if (res.code != 0) {
                    res.msg != null ? showMessage(res.msg, "danger", 1000) : showMessage("修改失败,请刷新重试", "danger", 1000)
                } else {
                    showMessage("修改成功", "success", 2000);
                    $("#updateHostpoolModal").modal("hide");
                }
                $("#host_pool_list").bootstrapTable("refresh", {silent: true});
            },
            error: function () {
                showMessage("请求不成功,请重试", "danger", 2000);
            }
        });
    });

    $('#hostMonitor').on('hidden.bs.modal', function (e) {
        $('#time_range').modal('hide');
    });

    $('.minus-count').click(function () {
        hostPoolObject.minusCount('hostCount-limit');
    });
    $('.plus-count').click(function () {
        hostPoolObject.plusCount('hostCount-limit');
    });
    $('.minus-micro').click(function () {
        hostPoolObject.minusCount('memoryInfo');
    });
    $('.plus-micro').click(function () {
        hostPoolObject.plusCount('memoryInfo');
    });
    $("#createHostOpera").click(function () {
        //创建host
        if (hostPoolObject.isEmpty("#addHostModal input") == false) {
            return;
        } else {
            hostPoolObject.addHost();
        }
    });
    $(".createHostpoolBtn").click(function () {//初始化创建集群联动信息
        hostPoolObject.createHostpoolInfoInit();
    });


    $("#some-area").change(function () {
        hostPoolObject.htmlInit.initHostPool();
        hostPoolObject.areaChild();
    });
    $("#some-area-child").change(function () {
        hostPoolObject.htmlInit.initHostPool();
        hostPoolObject.childHostChoice();
    });
    $("#host-house").change(function () {
        hostPoolObject.htmlInit.initHostPool();
        hostPoolObject.netAreaChoice();
    });

    $('#createHostPoolSure').click(function () {
        if (hostPoolObject.isEmpty("#createHostPool input") == false) {
            //当录入信息不全时提示
            showMessage("录入失败，请检查","danger",1000);
            return;
        } else {
            hostPoolObject.createHostpool();

        }
    });

    $("#deleteHostPoolSure").click(function(){
        var  hostpool_ids =   $("#deleteHostPoolSure").attr("data-hostpool-ids");
        hostPoolObject.hostpool_delete(hostpool_ids);
    });

    $(".deleteHostpoolBtn").click(function(){
        $(".hostpool_table_list").html("");
        var selected_hostpool_list = $("#host_pool_list").bootstrapTable("getSelections");
        if(selected_hostpool_list==0){
            showMessage("请选择要删除的hostpool","danger",1000);
            return;
        }else{
            var hostpool_ids = [],host_nums = [],html = "";
            for(var i = 0, len = selected_hostpool_list.length ; i< len ;i++ ){
                var item = selected_hostpool_list[i];
                hostpool_ids.push(item.hostpool_id);
                host_nums.push(item.hosts_nums);
                html +="<tr>"
                html += "<td>"+item.displayname+"</td><td>"+item.net_area+"</td><td>"+item.datacenter+"</td>";
                html += "</tr>";
            }
           host_nums=host_nums.unique();
            if(host_nums.length>1){
                showMessage("选中的集群存在HOST,不能删除请重新删除","danger",2000);
                return;
            }
            $("#deleteHostPool").modal("show");
            hostpool_ids = hostpool_ids.join(",");
            $("#deleteHostPoolSure").attr("data-hostpool-ids",hostpool_ids);
            $("#hostpool_table_list").html(html);
        }
    });
}

function DoOnMsoNumberFormat(cell, row, col) {
       var result = "";
       if (row > 0 && col == 0)
           result = "\\@";
       return result;
   };
var length_export;
function init_hostpool_table() {
    $('#host_pool_list').bootstrapTable({
        url: '/hostpool/list',
        method: 'get',
        dataType: "json",
        detailView: false,
        uniqueId: "hostpool_id",//删除时能用到 removeByUniqueId
        //queryParamsType: "search",
        showRefresh: true,
        contentType: "application/x-www-form-urlencoded",
         showExport: true,//显示导出按钮
        exportDataType: "all",//导出所有数据
        exportTypes:["all"],  //导出文件类型
        exportOptions:{
            ignoreColumn: [0,11],  //忽略某一列的索引
            fileName: '集群信息',  //文件名称设置
            worksheetName: 'sheet1',  //表格工作区名称
            tableName: '集群详情',
            //excelstyles: ['background-color', 'color', 'font-size', 'font-weight'],
            onMsoNumberFormat: DoOnMsoNumberFormat
        },
        pagination: true,
        pageList: [10,20, 50,100, "all"],
        pageSize: 10,
        queryParamsType: "search",
        pageNumber: 1,
        search: false, //不显示全表模糊搜索框
        //searchText: getQueryString('search'),
        showColumns: true, //不显示下拉框（选择显示的列）
        sidePagination: "server", //服务端请求
        checkboxHeader: true,
        clickToSelect: false,
        singleSelect: false,
        onBeforeLoadParams: {},//查询参数设置，供导出使用，在search_form.js里赋值
        sortable: false,
        responseHandler: function (res) {
             if (res.code == 0) {
                    return res.data;
                } else {
                    return{rows: [], total: 0};
                }
        },
        onSearch: function (text) {
            search_text = text;
        },
        queryParams: function (q) {
            var searchContent = q.searchText;
//                var key = '';
//                key = isIP(searchContent) ? JSON.stringify({'ip': searchContent}) : JSON.stringify({'name': searchContent})

            return {
                //"sortName" : q.sortName,
                //"sortOrder" : q.sortOrder,
                "page_size": q.pageSize,
                "page_no": q.pageNumber,
                //"user_id": user_id_num
            };
        },
        onLoadSuccess: function (data) {
            length_export = data.rows.length;

        },
//            onClickRow: function ($element, row) {
////                console.log(row);
//            },
        onClickCell: function (field, value, row) {
            var area, datacenter, net_area, displayname;
            area = row.area != null ? row.area : "";
            datacenter = row.datacenter != null ? row.datacenter : "";
            net_area = row.net_area != null ? row.net_area : "";
            displayname = row.displayname != null ? row.displayname : "";

            $('.placeInfo>li:nth-child(1)').html(area + "&nbsp;&nbsp;&nbsp;" + datacenter);
            $('.placeInfo>li:nth-child(2)').html(net_area + "&nbsp;&nbsp;&nbsp;" + displayname);
            $('#createHostOpera').attr('data-hostpoolId', row.hostpool_id);
            $('#addHostModal input').val('');
        },
        onCheckAll: function () {
            hostPoolObject.getselected_option();
        },
        onUncheckAll: function () {
            hostPoolObject.getselected_option();
        },
        onCheck: function () {
            hostPoolObject.getselected_option();

        },
        onUncheck: function () {
            hostPoolObject.getselected_option();
        },
        columns: [
            {
                checkbox: true
            },
//                {
//                    title:"地区",
//                    field:"area",
//                    align:"left"
//                },
            {
                title: "集群名",
                field: "displayname",
                align: "left",
            },
            {
                title: "网络区域",
                field: "net_area",
                align: "left",
            },
            {
                title: "所属机房",
                field: "datacenter",
                align: "left",
            },
            {
                title: "机房类型",
                field: "dc_type",
                align: "left",
                formatter:function(value,row,index){
                    var environments_arr = allEnvArr;
                    return environments_arr[parseInt(value)];
                }
            },
            {
                title: "Host数量",
                field: "hosts_nums",
                align: "left",
            },
            {
                title: "Host数量下限",
                field: "least_host_num",
                align: "left",
            },
            {
                title: "vm数量",
                field: "instances_nums",
                align: "left",
            },
            {
                title: "cpu数(核)",
                field: "cpu_nums",
                align: "left",
            },
            {
                title: "CPU使用率(%)",
                field: "cpu_used_per",
                align: "left",
            },
            {
                title: "MEM总量(MB)",
                field: "mem_nums",
                align: "left",
            },
            {
                title: "MEM分配率(%)",
                field: "mem_assign_per",
                align: "left",
            },
            {
                title: "MEM使用率(%)",
                field: "mem_used_per",
                align: "left",
            },
            {
                title: "可创建VM数",
                field: "available_create_vm_nums",
                align: "left",
            },
            {
                title: "可用IP",
                field: "available_ip_nums",
                align: "left",
            },
            {
                title: "操作",
                align: "left",
                events: window.operateClusterEvents,
                formatter:hostPoolObject.table_formatter_oprate
            },
              {
                title: "集群信息",
                field: "app_code",
                align: "left",
            }
        ]
    })
}

function refreshChart() {

    $('.btn-outline').on('click', function () {
        var value = $(this).attr("value");
        var displayname = sessionStorage.getItem("displayname");
        var hostpool_id = sessionStorage.getItem("hostpool_id");
        var rep_url = sessionStorage.getItem("rep_url");
        refresh_mon_cluser(displayname, hostpool_id, value, value, rep_url);



        $('#time_range').modal("hide");
    });

    $('.refresh-chart').on('click', function () {

        var startDate = $("#start_date").val() + ' 00:00:00';
        var endDate = $("#end_date").val() + ' 00:00:00';
        var value = $(this).attr("value");
        var displayname = sessionStorage.getItem("displayname");
        var hostpool_id = sessionStorage.getItem("hostpool_id");
        var rep_url = sessionStorage.getItem("rep_url");
        refresh_mon_cluser(displayname, hostpool_id, startDate, endDate, rep_url);
        $('#time_range').modal("hide");
    });
}