/**
 * Created by 80002473 on 2017/3/30.
 */
window.onload = function () {
    init_table()
    refreshChart();
    (function(){
        let envHtml = ''
       for(var i = 0;i<allEnvArr.length;i++){
           envHtml= envHtml + ' <option value='+i+'>'+allEnvArr[i]+'</option>'
       }
        $("#new_dc_type").html(envHtml)
    })()
    //关闭监控信息模态框同时关闭时间选项模态框
    $('#dcMonitor').on('hidden.bs.modal', function (e) {
        $('#time_range').modal('hide');
    });
    createDatacenterInfo.chocieProvince("#local-province");
    $('#new_area_id').change(function () {
         $("#new_dc_name").attr("data-id","");
        createDatacenterInfo.getChildArea();
    });
    $("#new_child_area_id").change(function () {
         $("#new_dc_name").attr("data-id","");
        createDatacenterInfo.getAreaId();
    });


    $("#datacenter-delete-show").click(function () {
        $("#delete_table_datacenter").html("");
        var selected_arr = $("#datacenter_list").bootstrapTable("getSelections"), datacenter_ids = [];
        for (var i = 0, len = selected_arr.length, html = ""; i < len; i++) {
            var item = selected_arr[i];
            datacenter_ids.push(item.datacenter_id);
            html += "<tr>"
            html += "<td>" + item.displayname + "</td><td>" + dctypeFormatter(item.dc_type) + "</td>";
            html += "</tr>";
        }

            datacenter_ids = datacenter_ids.join(",");
            $("#deletedatacenterSure").attr("data-datacenter-ids", datacenter_ids);
            $("#delete_table_datacenter").html(html);
            $("#deleteDatacenter").modal("show");
    });

    $("#deletedatacenterSure").click(function () {
        var datacenter_ids = $(this).attr("data-datacenter-ids");
        $.ajax({
            url: "/datacenter",
            type: "delete",
            data: {
                "datacenter_ids": datacenter_ids
            },
            dataType: "json",
            beforeSend: function () {
                $("#loading").css("display", "block");
                $("#deleteDatacenter").modal('hide')
            },
            success: function (res) {
                $("#loading").css("display", "none");
                if (res.code != 0) {
                    res.msg != null ? showMessage(res.msg, "danger", 1000) : showMessage("操作失败请刷新重试", "danger", 1000)
                } else {
                    showMessage("操作成功", "success", 1000);
                }
                $("#datacenter-delete-show").attr("disabled", true);
                $("#datacenter_list").bootstrapTable("refresh", {silent: true});
            },
            error: function () {
                $("#loading").css("display", "none");
                showMessage("操作失败请刷新重试", "danger", 1000);
            }

        });
    });

    $("#update_datacenter_sure").click(function () {
        var datacenter_id = $(this).attr("data-datacenterid");
        var displayname = $("#update-datacenter-name").val();
        var province = $("#update-province-name").val();
        var address = $("#update-address-name").val();
        var description = $("#update-description-name").val();
        if(displayname == ""){
            showMessage("机房名不能为空,请输入!","danger",1000);
            return;
        }
        if(province == ""){
            showMessage("所在省份不能为空,请输入!","danger",1000);
            return;
        }
        //console.log(datacenter_id,displayname,province,address,description);
        $.ajax({
            url: "/datacenter/" + datacenter_id,
            type: "put",
            dataType: "json",
            data: {
               "name":displayname,
               "province":province,
               "address":address,
               "description":description,
            },
            success: function (res) {
                if (res.code != 0) {
                    res.msg != null ? showMessage(res.msg, "danger", 1000) : showMessage("修改失败,请刷新重试", "danger", 1000)
                } else {
                    showMessage("修改成功", "success", 2000);
                    $("#updateDatacenterModal").modal("hide");
                }
                $("#datacenter_list").bootstrapTable("refresh", {silent: true});
            },
            error: function () {
                showMessage("请求不成功,请重试", "danger", 2000);
            }
        });
    });
}

    function operateFormatter(value, row, index) {
        // '<a  class="seeInfo" data-toggle="modal" data-target="#dcMonitor" id="monitorPage" title="监控"><i class="fa fa-signal text-primary"></i></a>&nbsp;&nbsp;&nbsp;',
        return [
            '<a id="update_datacenter"  title="修改信息"><i class="fa fa-pencil-square"></i></a>&nbsp;&nbsp;',
            '<a class="deleteNetArea" title="删除网络区域"><i class="fa fa-trash-o text-danger"></i></a>',
        ].join('');
    }

    var dctypeCNArray = allEnvArrNo;
    function dctypeFormatter(value, row, index) {
        var index = parseInt(value);
        var html='';
        if (index > 0 && index < dctypeCNArray.length) {
            return dctypeCNArray[index];
        } else {
            return "其他";
        }
    }



    function init_table() {
        $('#datacenter_list').bootstrapTable({
            url: '/datacenter/list',
            method: 'get',
            dataType: "json",
            detailView: false,
            uniqueId: "datacenter_id",//删除时能用到 removeByUniqueId
            queryParamsType: "search",
            showRefresh: true,
            contentType: "application/x-www-form-urlencoded",
            pagination: true,
            pageList: [10,20, 50,100, "all"],
            pageSize: 10,
            pageNumber: 1,
            search: false, //不显示全表模糊搜索框
//            searchText: getQueryString('search'),
            showColumns: false, //不显示下拉框（选择显示的列）
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
            onLoadSuccess: function($element){

            },
            onClickRow: function ($element, row) {

            },
            queryParams: function (q) {
                return {
                    "page_size": q.pageSize,
                    "page_no": q.pageNumber,
                    //"user_id":user_id_num
                };
            },
            onCheckAll:function(){
                createDatacenterInfo.getselected_option();
            },
            onUncheckAll:function(){
                createDatacenterInfo.getselected_option();
            },
            onCheck: function () {
                createDatacenterInfo.getselected_option();

            },
            onUncheck: function () {
                createDatacenterInfo.getselected_option();
            },
            columns: [
                {
                    checkbox: true
                },
                {
                    title: "机房名",
                    field: "displayname",
                    align: "left",
                },
                {
                    title: "机房类型",
                    field: "dc_type",
                    align: "left",
                    formatter: dctypeFormatter
                },
                {
                    title: "集群数量",
                    field: "hostpool_nums",
                    align: "left",
                },
                {
                    title: "所在省份",
                    field: "province",
                    align: "left",
                },
                {
                    title: "机房地址",
                    field: "address",
                    align: "left",
                },
                {
                    title: "备注",
                    field: "description",
                    align: "left",
                },
                {
                    title: "操作",
                    field: "operation",
                    align: "left",
                    events:window.operateDcEvents,
                    formatter: operateFormatter
                }
            ]
        })
    }

    var createDatacenterInfo={
        areaInfo:null,//区域子区域信息
        //获取区域信息
        addAreaSelect: function () {
            var areaInfoList=this;
            $("#addDatacenterModal input").val("");
             $("#childDiv").removeClass("show").addClass("hidden");
            $("#new_dc_name").attr("data-id","");
            $.ajax({
                url: "/area/levelinfo",
                type: "GET",
                dataType: "json",
                success:function(req) {
                    if (req.code != 0) {
                        req.msg != null ? showMessage(req.msg, "danger", 1000) : showMessage("获取信息失败,请刷新重试", "danger", 1000);
                    } else {
                        areaInfoList.areaInfo = req.data.level_info;
                        var html = '<option value="-1">请选择区域</option>';
                        var areaArr = [];
                        $.each(areaInfoList.areaInfo, function (index, tmp) {
                            areaArr.push(tmp.area);
                        });
                        areaArr = areaArr.unique();
                        var areaArrLength = areaArr.length;
                        for (var i = 0; i < areaArrLength; i++) {
                            html += '<option value=' + i + '>' + areaArr[i] + '</option>';
                        }
                        $('#new_area_id').html(html);
                    }
                },
                error:function(){
                    console.log('ajax error');
                }
            });
        },
        //获取子区域信息
        getChildArea:function(){
//            console.log(this.areaInfo);
            var area= $('#new_area_id option:selected').html();
            var childArea=[];
            var noneChildArea=[];
            var html='<option value="-1">请选择子区域</option>';
            $.each(this.areaInfo,function(index,tmp){
                    if(tmp.area==area && tmp.child_area!=null){
                        childArea.push(tmp.child_area);
                    }
                    if(tmp.area==area && tmp.child_area==null){
                        //noneChildArea.push("直属大区");
                        $("#new_dc_name").attr("data-id",tmp.id);
                    }
            });
            childArea=childArea.unique();
            var childAreaLength=childArea.length;
            if(childAreaLength==0){
                 $("#childDiv").removeClass("show").addClass("hidden");
            }else{
                 for(var i=childAreaLength-1;i>=0;i--){
                    html+='<option value='+i+'>'+childArea[i]+'</option>';
                 }
                 $("#childDiv").removeClass("hidden").addClass("show");
                 $("#new_child_area_id").html(html);
            }
        },
        getAreaId:function(){
              var childArea= $('#new_child_area_id option:selected').html();
              var area=$("#new_area_id option:selected").html();
              var area_id='';

              $.each(this.areaInfo,function(index,tmp){
                  if(tmp.child_area==childArea){
                      area_id=tmp.id;
                  }
                  //if(childArea=="直属大区" && tmp.area==area && tmp.child_area==null){
                  //      area_id=tmp.id;
                  //}
              })
            $("#new_dc_name").attr("data-id",area_id);
        },
        add_datacenter: function () {
            var area_id = parseInt($("#new_dc_name").attr("data-id"));
            var datacenter_name = $("#new_dc_name").val();
            var datacenter_type = $("#new_dc_type").val();
            var datacenter_address = $("#new_dc_address").val();
            var datacenter_remasks = $("#new_dc_remarks").val();
            var province=$("#local-province option:selected").html();

            if(!area_id ){
                showMessage("请选择区域","danger",1000);
                return;
            }
            if(!datacenter_name){
                showMessage("请输入机房名","danger",1000);
                return;
            }
            if(!datacenter_address){
                showMessage("请输入机房地址","danger",1000);
                return;
            }
            $.ajax({
                url: "/datacenter/" + area_id,
                type: "POST",
                dataType: "json",
                data: {
                    "name": datacenter_name,
                    "address": datacenter_address,
                    "description": datacenter_remasks,
                    "dc_type": datacenter_type,
                    "province":province
                },
                success:function(req) {
                    if (req.code != 0) {
                        req.msg != null ? showMessage(req.msg, "danger", 1000) : showMessage("操作失败,请刷新重试", "danger", 1000);
                    } else {
                         showMessage("新建机房成功", "success", 1200);
                         $("#datacenter_list").bootstrapTable('refresh', {silent: true});
                        $("#addDatacenterModal").modal("hide");
                    }
                },
                error:function(){
                    console.log('ajax error');
                }
            });
        },
        data:[
                        {province: '北京' },
                        {province: '天津' },
                        {province: '上海' },
                        {province: '重庆' },
                        {province: '河北' },
                        {province: '河南' },
                        {province: '云南' },
                        {province: '辽宁' },
                        {province: '黑龙江' },
                        {province: '湖南' },
                        {province: '安徽' },
                        {province: '山东' },
                        {province: '新疆' },
                        {province: '江苏' },
                        {province: '浙江' },
                        {province: '江西' },
                        {province: '湖北' },
                        {province: '广西' },
                        {province: '甘肃' },
                        {province: '山西' },
                        {province: '内蒙古' },
                        {province: '陕西' },
                        {province: '吉林' },
                        {province: '福建' },
                        {province: '贵州' },
                        {province: '广东' },
                        {province: '青海' },
                        {province: '西藏' },
                        {province: '四川' },
                        {province: '宁夏' },
                        {province: '海南' },
                        {province: '台湾' },
                        {province: '香港' },
                        {province: '澳门' }
                    ],
        chocieProvince: function (id,sel) {
            var html = "";
            var list = this.data;
            for (var i = 0; i < list.length; i++) {
                if(sel!= "" && sel == list[i].province){
                    html += "<option value=" + sel + " selected>" + sel + "</option>"
                }else{
                     html += "<option value=" + list[i].province + ">" + list[i].province + "</option>"
                }

            }
            $(id).html(html);
        },
        //table选中删除按钮显示操作
        getselected_option: function () {
            var selected_list = $("#datacenter_list").bootstrapTable("getSelections");
            if (selected_list.length > 0) {
                $("#datacenter-delete-show").attr("disabled", false);
            } else {
                $("#datacenter-delete-show").attr("disabled", true);
            }
        }
    }



   window.operateDcEvents={
        //绑定监控信息事件
       "click #monitorPage":function (e,value,row,index) {

         myChart = echarts.init(document.getElementById('main'));
          init_echart_cpu_mem();

          $("#model-title").html(row.displayname);

           var datacenter_id =  row.datacenter_id;
           console.info("datacenter_id");
           console.info(datacenter_id);
           var start_time = 30;
           var end_time = 30;
           var rep_url = "/datacenter/"+datacenter_id+"/monitor";
           sessionStorage.setItem("displayname", row.displayname);
           sessionStorage.setItem("datacenter_id", row.datacenter_id);
           sessionStorage.setItem("rep_url", rep_url);
          refresh_mon_cluser(row.displayname,datacenter_id,start_time,end_time,rep_url);

      },
       "click .deleteNetArea":function(e,value,row,index){
            $("#delete_table_datacenter").html("");
           var datacenter_ids = row.datacenter_id,html="<tr>";
            html += "<td>"+row.displayname+"</td><td>"+dctypeFormatter(row.dc_type)+"</td>";
            html += "</tr>";
            $("#delete_table_datacenter").html(html);
            $("#deletedatacenterSure").attr("data-datacenter-ids",datacenter_ids);
            $("#deleteDatacenter").modal("show");
       },
       "click #update_datacenter":function(e,value,row,index){
                $("#datacenter-form input").val("");
                createDatacenterInfo.chocieProvince("#update-province-name",row.province);
                $("#datacenter-form input[name=displayname]").val(row.displayname);
                $("#datacenter-form input[name=address]").val(row.address);
                $("#datacenter-form input[name=description]").val(row.description);
                $("#update_datacenter_sure").attr("data-datacenterid",row.datacenter_id);
                $("#updateDatacenterModal").modal("show");
       }
    };
 function refreshChart(){

        $('.btn-outline').on('click',function(){
           var value = $(this).attr("value");
           var displayname = sessionStorage.getItem("displayname");
           var datacenter_id = sessionStorage.getItem("datacenter_id");
           var rep_url = sessionStorage.getItem("rep_url");
           refresh_mon_cluser(displayname,datacenter_id,value,value,rep_url);
           $('#time_range').modal("hide");
          });
        $('.refresh-chart').on('click',function(){
           var startDate = $("#start_date").val()+' 00:00:00';
           var endDate = $("#end_date").val()+' 00:00:00';
           var value = $(this).attr("value");
           var displayname = sessionStorage.getItem("displayname");
           var datacenter_id = sessionStorage.getItem("datacenter_id");
           var rep_url = sessionStorage.getItem("rep_url");
           refresh_mon_cluser(displayname,datacenter_id,startDate,endDate,rep_url);
           $('#time_range').modal("hide");
          });
    }
