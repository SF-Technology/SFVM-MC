/**
 * Created by 80002473 on 2017/3/30.
 */
    function init_table() {
        $('#net_area_list').bootstrapTable({
            url: '/net_area/list',
            method: 'get',
            dataType: "json",
            detailView: false,
            uniqueId: "datacenter_name", //删除时能用到 removeByUniqueId
            queryParamsType: "search",
            showRefresh: true,
            contentType: "application/x-www-form-urlencoded",
            pagination: true,
            pageList: [10,20, 50,100, "all"],
            pageSize: 10,
            pageNumber:1,
            //search: false, //不显示全表模糊搜索框
//            searchText: getQueryString('search'),
            showColumns: true, //不显示下拉框（选择显示的列）
            sidePagination: "server", //服务端请求
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
            queryParams: function (q) {
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
            onLoadSuccess: function($element){

            },
            onClickRow: function ($element, row) {
            },
            onCheckAll:function(){
                netAreaInfoObj.getselected_option();
            },
            onUncheckAll:function(){
                netAreaInfoObj.getselected_option();
            },
            onCheck: function () {
                netAreaInfoObj.getselected_option();

            },
            onUncheck: function () {
                netAreaInfoObj.getselected_option();
            },
            columns: [
                {
                    checkbox: true
                },
                {
                    title: "网络区域名",
                    field: "net_area_name",
                    align: "left",
                },
                {
                    title: "所属机房",
                    field: "datacenter_name",
                    align: "left",
                },
                {
                    title: "机房类型",
                    field: "dc_type",
                    align: "left",
                    formatter:netAreaInfoObj.typestatusFormatter
                },
                    {
                    title: "集群数量",
                    field: "hostpool_nums",
                    align: "left",
                },
                {
                    title: "操作",
                    //field: "operation",
                    align: "left",
                    events:window.operateEvents,
                    formatter: netAreaInfoObj.operateFormatter
                }
            ]
        })
    }

var netAreaInfoObj= {
    areaInfo: null,//保存联动查询信息列表
    operateFormatter: function (value,row,index) {
        // '<a  class="seeInfo" data-toggle="modal" data-target="#netMonitor" id="monitor_button" title="监控"><i class="fa fa-signal text-primary"></i></a>&nbsp;&nbsp;&nbsp;',
        var netarea_opreate_arr = [
            '<a id="update_net_area"  title="修改信息"><i class="fa fa-pencil-square"></i></a>&nbsp;&nbsp;',
            '<a class="deleteNetArea" title="删除网络区域"><i class="fa fa-trash-o text-danger"></i></a>',
        ];
        if(row.hostpool_nums!=0){
            netarea_opreate_arr.pop();
        }
        return netarea_opreate_arr.join("");
    },
    initHtml: {
        childInitHtml: function () {
            $("#child-area").html('<option value="-1">请选择子区域</option>');
        },
        datacenterHtml: function () {
            $("#datacenterName").html('<option value="-1">请选择机房名</option>');
        }
    },
    areaInfoInit: function () {
        var getareaInfo = this;
        $("#netAreaName").val("");
        $(".childAreaShow").addClass("hidden").removeClass("show");
        $.ajax({
            url: "/net_area/init_info",
            type: "get",
            dataType: "json",
            success: function (res) {
                getareaInfo.areaInfo = res.data.rows;
                if (res.code != 0) {
                    res.msg != null ? showMessage(res.msg, "danger", 1000) : showMessage("获取信息失败,请刷新重试", "danger", 1000);
                    return;
                }
                var arr = [];
                var html = '<option value="-1">请选择区域</option>';
                $.each(res.data.rows, function (index, tmp) {
                    arr.push(tmp.parent_area_name);
                    //console.log(tmp.parent_area_name);
                });
                arr = arr.unique();
                //console.log(arr);
                for (var i = 0; i < arr.length; i++) {
                    html += '<option value=' + i + '>' + arr[i] + '</option>';
                }
                $("#parent-area").html(html);
            }
        });
    },
    childAreaInfo: function () {
        var list = this.areaInfo;
        var childArr = [];
        var parentArea = $("#parent-area option:selected").html();
        var datacenterHtml = '<option value="-1">请选择机房名</option>';
        var childHtml = '<option value="-1">请选择子区域</option>';
        //var nonechildArr=[];

        $.each(list, function (index, tmp) {
            if (tmp.parent_area_name == parentArea) {
                if (!tmp.area_name) {
                    //nonechildArr.push("本部");
                    var arr = allEnvArr;
                    $(".childAreaShow").addClass("hidden").removeClass("show");
                    datacenterHtml += '<option value=' + tmp.datacenter_id + '>' + tmp.datacenter_name + '-' + arr[parseInt(tmp.dc_type)] + '</option>';
                } else {
                    $(".childAreaShow").addClass("show").removeClass("hidden");
                    childArr.push(tmp.area_name);
                }
            }
        });
        //if(nonechildArr.length!=0){
        //    childHtml+='<option value="-2">本部</option>';
        //}
        childArr = childArr.unique();
        if (childArr.length != 0) {//存在子区域
            for (var i = childArr.length - 1; i >= 0; i--) {
                childHtml += '<option value=' + i + '>' + childArr[i] + '</option>';
            }
            $("#child-area").html(childHtml);
        } else {
            $("#datacenterName").html(datacenterHtml);
        }

    },
    datacenterInfo: function () {
        var list = this.areaInfo;
        var parentArea = $("#parent-area option:selected").html();
        var childArea = $("#child-area option:selected").html();
        var datacenterHtml = '<option value="-1">请选择机房名</option>';
        $.each(list, function (index, tmp) {
            //if(childArea=="本部" && tmp.area_name==null && parentArea==tmp.parent_area_name){
            //    datacenterHtml+='<option value='+tmp.datacenter_id+'>'+tmp.datacenter_name+'</option>';
            //}else
            var arr = allEnvArr;
            if (tmp.area_name == childArea) {
                datacenterHtml += '<option value=' + tmp.datacenter_id + '>' + tmp.datacenter_name + '-' + arr[parseInt(tmp.dc_type)] + '</option>';
            }
        });
        $("#datacenterName").html(datacenterHtml);
    },
    createNetArea: function () {
        var datacenter_id = $("#datacenterName").val();
        if (datacenter_id == -1) {
            showMessage("请选择机房", "danger", 1000);
            return;
        }
        var net_name = $("#netAreaName").val();
        if (net_name == '') {
            showMessage("网络区域不能为空", "danger", 1000);
            return;
        }
        var imagecache01 = $("#server_url_main").val();
        var imagecache02 = $("#server_url_second").val();
        if (imagecache01 == '') {
            showMessage("镜像缓存服务器地址(主)不能为空", "danger", 1000);
            return;
        }
        if (imagecache02 == '') {
            showMessage("镜像缓存服务器地址(副)不能为空", "danger", 1000);
            return;
        }
        $.ajax({
            url: "/net_area",
            type: "post",
            data: {
                "datacenter_id": datacenter_id,
                "name": net_name,
                "imagecache01": imagecache01,
                "imagecache02": imagecache02,
            },
            dataType: "json",
            success: function (res) {
                if (res.code != 0) {
                    res.msg != null ? showMessage(res.msg, "danger", 1000) : showMessage("创建失败", "danger", 1000);
                    return;
                } else {
                    showMessage("创建成功", "success", 1000);
                    $("#addAreaModal").modal("hide");
                    $('#net_area_list').bootstrapTable('refresh');
                }
            }
        });
    },
    //表格中机房类型转换
    typestatusFormatter: function (value, row, index) {
        environments = allEnvArr
        var num = parseInt(value);
        var html = environments[num];
        return html;
    },

    //table选中删除按钮显示操作
    getselected_option:function(){
         var selected_list = $("#net_area_list").bootstrapTable("getSelections");
        if(selected_list.length>0){
            $("#deleteNetarea-modal-btn").attr("disabled",false);
        }else{
             $("#deleteNetarea-modal-btn").attr("disabled",true);
        }
    }
}

window.onload = function () {
        init_table();
        refreshChart();
      //关闭监控信息模态框同时关闭时间选项模态框
      $('#netMonitor').on('hidden.bs.modal', function (e) {
        $('#time_range').modal('hide');
        });

       $("#addNetarea").click(function(){
            netAreaInfoObj.initHtml.childInitHtml();
           netAreaInfoObj.initHtml.datacenterHtml();
           netAreaInfoObj.areaInfoInit();

       });
    $("#parent-area").change(function(){
        netAreaInfoObj.initHtml.childInitHtml();
        netAreaInfoObj.initHtml.datacenterHtml();
        netAreaInfoObj.childAreaInfo();
    });
    $("#child-area").change(function(){
        netAreaInfoObj.initHtml.datacenterHtml();
        netAreaInfoObj.datacenterInfo();
    });
    $("#createNetAraSure").click(function(){
        netAreaInfoObj.createNetArea();
    });

    $("#deleteNetarea-modal-btn").click(function(){
        $("#delete_nerarea_table_list").html("");
        var selected_arr = $("#net_area_list").bootstrapTable("getSelections"),net_area_ids = [],hostpool_nums = [];
        for(var i = 0,len = selected_arr.length,html="";i<len;i++){
            var item = selected_arr[i];
            net_area_ids.push(item.net_area_id);
            hostpool_nums.push(item.hostpool_nums);
            html += "<tr>"
            html += "<td>" + item.net_area_name + "</td><td>" + item.datacenter_name + "</td><td>" + netAreaInfoObj.typestatusFormatter(item.dc_type) + "</td>";
            html += "</tr>";
        }
        hostpool_nums=hostpool_nums.unique();
        if(hostpool_nums.length>1){
            showMessage("选中的网络区域中存在集群,不能删除请重新选择！","danger",2000);
        }else{
            net_area_ids = net_area_ids.join(",");
            $("#deletenetareaSure").attr("data-net_area_ids",net_area_ids);
            $("#delete_nerarea_table_list").html(html);
            $("#deleteNetArea").modal("show");
        }
    });

    $("#deletenetareaSure").click(function(){
        var net_area_ids = $(this).attr("data-net_area_ids");
         $.ajax({
            url:"/net_area",
            type:"delete",
            data:{
               "net_area_ids":net_area_ids
            },
            dataType: "json",
            beforeSend: function () {
                $("#loading").css("display", "block");
                 $("#deleteNetArea").modal('hide')
            },
            success:function(res){
                $("#loading").css("display", "none");
                if(res.code!=0){
                    res.msg!=null ? showMessage(res.msg,"danger",1000) : showMessage("操作失败请刷新重试","danger",1000)
                }else{
                     showMessage("操作成功","success",1000);
                }
                $("#net_area_list").bootstrapTable("refresh", {silent: true});
                $("#deleteNetarea-modal-btn").attr("disabled",true);
            },
            error:function(){
                $("#loading").css("display", "none");
                showMessage("操作失败请刷新重试","danger",1000);
            }

        });
    });

    $("#update_btn_sure").click(function(){
        var name = $("#update-netarea-name").val();
        var imagecache01 = $("#image_cache_main").val();
        var imagecache02 = $("#image_cache_second").val();
        var net_area_id = $("#update-netarea-name").attr("data-update-id");
        if(name == ""){
            showMessage("请输入网络区域名","danger",1000);
            return;
        }
        if(imagecache01 == ""){
            showMessage("镜像缓存服务器地址(主)不能为空","danger",1000);
            return;
        }
        if(imagecache02 == ""){
            showMessage("镜像缓存服务器地址(副)不能为空","danger",1000);
            return;
        }
        $.ajax({
            url:"/net_area/"+net_area_id,
            type:"put",
            dataType:"json",
            data:{
                "name":name,
                "imagecache01":imagecache01,
                "imagecache02":imagecache02,
            },
            success:function(res){
                if(res.code!=0){
                    res.msg != null ?showMessage(res.msg,"danger",1000) :showMessage("操作失败,请刷新重试","danger",1000);
                }else{
                    showMessage("修改成功","success",1000);
                     $("#net_area_list").bootstrapTable("refresh", {silent: true});
                     $("#updateNetAreaModal").modal("hide");
                }
            },
            error:function(){
                showMessage("操作失败,请刷新重试","danger",1000);
            }
        });
    });
}

    //绑定监控信息事件
    window.operateEvents = {
        "click #monitor_button":function (e,value,row,index) {
          myChart = echarts.init(document.getElementById('main'));
           init_echart_cpu_mem();
            $("#model-title").html(row.displayname);

           var net_area_id =  row.net_area_id;
           //console.info("net_area_id");
           //console.info(net_area_id);
           var start_time = 30;
           var end_time = 30;
           var rep_url = "/net_area/"+net_area_id+"/monitor";
           sessionStorage.setItem("displayname", row.displayname);
           sessionStorage.setItem("net_area_id", row.net_area_id);
           sessionStorage.setItem("rep_url", rep_url);
          refresh_mon_cluser(row.displayname,net_area_id,start_time,end_time,rep_url);
      },
        "click .deleteNetArea" :function(e,value,row,index){
            $("#delete_nerarea_table_list").html("");
           var net_area_ids = row.net_area_id,html="<tr>";
            html += "<td>"+row.net_area_name+"</td><td>"+row.datacenter_name+"</td><td>"+netAreaInfoObj.typestatusFormatter(row.dc_type)+"</td>";
            html += "</tr>";
            $("#delete_nerarea_table_list").html(html);
            $("#deletenetareaSure").attr("data-net_area_ids",net_area_ids);
            $("#deleteNetArea").modal("show");
        },
        "click #update_net_area":function(e,value,row,index){
            if (row.imagecache_list === '获取失败') {
                showMessage('镜像服务器地址不存在', 'danger', 600)
                return;
            }
            $("#update-netarea-name").val(row.datacenter_name).attr("data-update-id",row.net_area_id);
            $("#image_cache_main").val(row.imagecache_list[0]);
            $("#image_cache_second").val(row.imagecache_list[1]);
            $("#updateNetAreaModal").modal("show");
        }

    }




     function refreshChart(){

        $('.btn-outline').on('click',function(){
           var value = $(this).attr("value");
           var displayname = sessionStorage.getItem("displayname");
           var net_area_id = sessionStorage.getItem("net_area_id");
           var rep_url = sessionStorage.getItem("rep_url");
           refresh_mon_cluser(displayname,net_area_id,value,value,rep_url);
           $('#time_range').modal("hide");
          });
         $('.refresh-chart').on('click',function(){
           var startDate = $("#start_date").val()+' 00:00:00';
           var endDate = $("#end_date").val()+' 00:00:00';
           var value = $(this).attr("value");
           var displayname = sessionStorage.getItem("displayname");
           var net_area_id = sessionStorage.getItem("net_area_id");
           var rep_url = sessionStorage.getItem("rep_url");
           refresh_mon_cluser(displayname,net_area_id,startDate,endDate,rep_url);
           $('#time_range').modal("hide");
          });
    }