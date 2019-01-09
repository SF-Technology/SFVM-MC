/**
 * Created by 80002473 on 2017/5/18.
 */

    window.onload = function () {
        init_table();

        addDatacenterInfo.chocieProvince();
        $("#area_list").on("click","#update_area_child",function(e){
            e.preventDefault();
            var tr,area_id,child_name,manager;
             tr = $(this).parent().parent();
             area_id = $(tr).children(":first-child").children("[type=hidden]").val();
             child_name = $(tr).children(":first-child+td").text();
             manager = $(tr).children(":first-child+td+td+td").text();
            $("#update_name").attr('data-areaId',area_id);
            $("#update_name").val(child_name);
            $("#update_manager").val(manager);
            $("#updateAreaModal").modal("show");
        });
        $("#area_list").on("click","#add_child_datacenter",function(e){
             e.preventDefault();
             $("#addDatacenterModal input").val("");
             $("#datacenter_type").val("1");
             $("#local-province").val("0");

             $("#child_area_div").css("display","none");
             var tr,area_id,child_name;
              tr = $(this).parent().parent();
             area_id = $(tr).children(":first-child").children("[type=hidden]").val();
             child_name = $(tr).children(":first-child+td").text();
             $("#area_name_d").html(child_name);
             $("#add_datacenter").attr('data-areaId',area_id);
             $("#addDatacenterModal").modal("show");
         });
        $("#area_list").on("click", ".deletechildarea", function (e) {
            e.preventDefault();
            $("#area_table_list").html("");
            var area_ids = $(this).prev().val(), html = "<tr>";
            var area_name = $(this).parent().parent().children(":nth-child(2)").text();
            var manager = $(this).parent().parent().children(":nth-child(4)").text();

            html += "<td>" + area_name + "</td><td>" + manager + "</td>";
            html += "</tr>";
            $("#deleteareaSure").attr("data-area-ids", area_ids);
            $("#area_table_list").html(html);
            $("#deleteareamodal").modal("show");

        });
        $("#deleteareaSure").click(function(){
                var area_ids = $(this).attr("data-area-ids");
            createAreaInfo.delete_area(area_ids);
        });
    }

    function init_table() {
        $('#area_list').bootstrapTable({
            url: '/area/list',
            method: 'GET',
            dataType: "json",
            detailView: true,
            uniqueId: "area_id", //删除时能用到 removeByUniqueId
            queryParamsType: "search",
            showRefresh: true,
            contentType: "application/x-www-form-urlencoded",
            pagination: true,
            pageList: [10,20, 50,100, "all"],
            pageSize: 10,
            pageNumber: 1,
//            search: false, //不显示全表模糊搜索框
//            searchText: getQueryString('search'),
            showColumns: true, //不显示下拉框（选择显示的列）
            sidePagination: "server", //服务端请求
             checkboxHeader: false,
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
                var searchContent = q.searchText;
//                var key = '';
//                key = isIP(searchContent) ? JSON.stringify({'ip': searchContent}) : JSON.stringify({'name': searchContent})

                return {
                    //"sortName" : q.sortName,
                    //"sortOrder" : q.sortOrder,
                    "page_size": q.pageSize,
                    "page_no": q.pageNumber
//                    "search": key
                };
            },
            onLoadSuccess: function($element){
//                    tableOperaShow();
            },
            onClickRow: function ($element, row) {
            },
            columns: [
                {
                    title: "区域名称",
                    field: "displayname",
                    align: "left",
                },
                {
                    title: "子区域数量",
                    field: "child_areas_nums",
                    align: "left",
                },
                {
                    title: "机房数量",
                    field: "datacenter_nums",
                    align: "left",
                },
                {
                    title: "管理员",
                    field: "manager",
                    align: "left",
                },
                {
                    title: "操作",
                    align: "left",
//                    class:"hideAll",
                    events: operateEvents,
                    formatter:operateFormatter
                }
            ],
             onExpandRow: function (index, row, $detail) {
                    showChildAreaInfo(index, row, $detail);
            }
        })
    }

    function showChildAreaInfo(index, row, $detail){

        if(row.child_areas_nums == 0){
            return;
        }else{
            $.ajax({
                url:"/area/child/"+row.area_id,
                type:"get",
                dataType:"json",
                success:function(res){
                    if(res.code!=0){
                        res.msg !=null ? showMessage(res.msg,"danger",1000) :showMessage("操作失败,请刷新重试","danger",1000)
                        return;
                    }else{
                        //showMessage("操作成功","success",1000);
                        var  list = res.data;
                        if(list != null){
                             var html = '<table id="child_table" style="border:2px solid #31a1ff" class="table table-hover-one child_table_style table-striped"><thead><tr><th></th><th>子区域名称</th><th>机房数量</th><th>管理员</th><th>操作</th></tr></thead><tbody>';
                            $.each(list,function(index,tmp){
                                 html += '<tr class="text-left" style="padding-left: 30px">';
                                if(tmp.datacenter_nums != 0){
                                     html += '<td><input type="hidden" value='+tmp.child_id+'></td>';
                                }else{
                                    html += '<td><input type="hidden" value='+tmp.child_id+'><a  tittle="delete" class="deletechildarea"><i class="fa fa-times text-danger"></i></a></td>';
                                }
                                 html += '<td>'+tmp.child_name+'</td><td>'+tmp.datacenter_nums+'</td><td>'+tmp.manager+'</td><td><a id="update_area_child"  title="修改子区域信息" data-areaId=""><i class="fa fa-pencil-square text-info"></i></a>&nbsp;&nbsp;<a id="add_child_datacenter" title="新增子区域机房" data-areaId=""><i class="text-info fa fa-plus-square"></i></a></td>';
                                 html += '</tr>';
                            });
                            html += '</tbody></table>';
                        }
                       $detail.html(html);
                    }

                },
                error:function(){
                    showMessage("请求失败，请刷新重试","danger",1000);
                }
            });
        }

    }
    function operateFormatter(value,row,index) {
        var operate_arr = [
            '<a id="update_area" class="showIf" title="修改区域信息" data-areaId=""><i class="fa fa-pencil-square"></i></a>&nbsp;',
            '<a id="add_datacenter" class="showIf" title="新增机房" data-areaId="" data-childFlag=""><i class="fa fa-plus-square"></i></a>&nbsp;',
            '<a id="deletearea" title="删除区域"><i class="fa fa-trash-o text-danger"></i></a>',
        ];
        if(!(row.child_areas_nums==0 && row.datacenter_nums == 0)){
            operate_arr.pop();
        }
        return operate_arr.join("");
    }

    window.operateEvents = {
        'click #update_area': function (e, value, row, index) {
            $('#update_name').attr("data-areaId", row.area_id);
            $('#updateAreaModal').modal({
                backdrop: 'static',
                keyboard: false })
            $("#update_name").val(row.displayname);
            $("#update_manager").val(row.manager);
            $("#updateAreaModal").modal("show");
        },
        'click #add_datacenter': function (e, value, row, index) {
           $("#addDatacenterModal input").val("");
            $('#add_datacenter').attr("data-areaId", row.area_id);
            //子区域数为0则不去获取子区域信息
            //console.log(row.child_areas_nums);
            if(row.child_areas_nums != 0){
                addDatacenterInfo.addChildSelect();
                $("#child_area_div").css('display', 'block');
                $('#add_datacenter').attr("data-childFlag", 1);
            }else{
                //去掉子区域选择框
                $("#child_area_div").css('display', 'none');
                $('#add_datacenter').attr("data-childFlag", 2);
            }

            $('#addDatacenterModal').modal({
                backdrop: 'static',
                keyboard: false })
            $("#area_name_d").html(row.displayname);
            $("#addDatacenterModal").modal("show");
        },
        "click #deletearea":function(e, value, row, index){
            $("#area_table_list").html("");
            var area_ids = row.area_id,html = "<tr>";
            html += "<td>"+row.displayname+"</td><td>"+row.manager+"</td>";
            html += "</tr>";
            $("#area_table_list").html(html);
            $("#deleteareaSure").attr("data-area-ids",area_ids);
            $("#deleteareamodal").modal("show");
        }
    }


    var createAreaInfo={
        areaInfo:null,//保存后台提取到的信息
        //初始化获取父区域信息
        addParentSelect:function(){
             $("#addAreaModal input").val("");
            $("#parent_id option:not(:first-child)").remove();
            var getInfo=this;
            $.ajax({
                url: "/area/parent",
                type: "GET",
                dataType: "json",
                success:function(req) {
                    if (req.code != 0) {
                        console.warn('area/parent get failed');
                        return;
                    }
                    var list=req.data;
//                    console.log(list);
                    getInfo.areaInfo=list;
//                    sessionStorage.setItem('areaInfo',JSON.stringify(list));
                    var html='';
                    $.each(list,function(index,tmp){
                        html+="<option value="+tmp.parent_id+">"+tmp.parent_name+"</option>";
                    });
                    $('.searchParent').append(html);
                },
                error:function(){
                    console.log('ajax error');
                }
            });
        },
        create_area:function() {
            if(isEmpty("#addAreaModal input")==false){
                return;
            };
            var parent_id = $("#parent_id").val();
            var name = $("#new_name").val();
            var manager = $("#new_manager").val();
            $.ajax({
                url: "/area",
                type: "POST",
                dataType: "json",
                data: {
                    "parent_id": parent_id,
                    "name": name,
                    "manager": manager,
                },
                success:function(req) {
                    if (req.code == 0) {
                        showMessage("创建区域成功", "success", 1200);
                        $("#addAreaModal").modal("hide");
                        $("#area_list").bootstrapTable('refresh', {silent: true});
                    } else{
                        req.msg != null ?showMessage(req.msg, "danger", 1200) :showMessage("创建区域失败,请重新操作", "danger", 1200) ;
                    }
                },
                error:function(){

                }
            });
        },
        update_area:function() {
            updateAreaInfo();
        },
        delete_area: function (area_ids) {
            $.ajax({
                url: "/area",
                type: "delete",
                data: {
                    "area_ids": area_ids
                },
                dataType: "json",
                beforeSend: function () {
                    $("#loading").css("display", "block");
                    $("#deleteareamodal").modal('hide')
                },
                success: function (res) {
                    $("#loading").css("display", "none");
                    if (res.code != 0) {
                        res.msg != null ? showMessage(res.msg, "danger", 1000) : showMessage("操作失败请刷新重试", "danger", 1000)
                    } else {
                        showMessage("操作成功", "success", 1000);
                    }
                    $("#area_list").bootstrapTable("refresh", {silent: true});
                },
                error: function () {
                    $("#loading").css("display", "none");
                    showMessage("操作失败请刷新重试", "danger", 1000);
                }
            });
        }
    }
    function updateAreaInfo(area_id){
          var area_id = $("#update_name").attr('data-areaId');
          var name = $("#update_name").val();
          var manager = $("#update_manager").val();
        $.ajax({
                url: "/area/" + area_id,
                type: "PUT",
                dataType: "json",
                data: {
                    "name": name,
                    "manager": manager,
                },
                success:function(req) {
                    if (req.code == 0) {
                        showMessage("修改区域成功", "success", 1200);
                    } else {
                        req.msg != null ?showMessage(req.msg, "danger", 1200) :showMessage("修改区域失败,请重新操作", "danger", 1200) ;
                    }
                    $("#area_list").bootstrapTable('refresh', {silent: true});
                    $("#updateAreaModal").modal("hide");
                },
                error:function(){

                }
            });
    }
    var addDatacenterInfo={
        //初始化获取子区域信息
        addChildSelect:function(){
            var area_id = $("#add_datacenter").attr('data-areaId');
            $.ajax({
                url: "/area/child/" + area_id,
                type: "GET",
                dataType: "json",
                success:function(req) {
                    if (req.code != 0) {
                        console.warn('area/child get failed');
                        return;
                    }
                    var list=req.data;
//                    sessionStorage.setItem('areaInfo',JSON.stringify(list));
                    var html='<option value="-1">请选择子区域</option>';
                    $.each(list,function(index,tmp){
                        html+="<option value="+tmp.child_id+">"+tmp.child_name+"</option>";
                    });
                    $('.searchChildAreaD').html(html);
                },
                error:function(){
                    console.log('ajax error');
                }
            });
        },
        add_datacenter:function () {
            if(isEmpty("#addDatacenterModal input","remarks")==false){
                return;
            };
            var child_flag = $('#add_datacenter').attr("data-childFlag");
            var area_id;
//            console.log('flag ' + child_flag);
            //有子区域
            if (child_flag == 1) {
                area_id = $("#child_id_d").val();
            } else {
                //无子区域
                area_id = $('#add_datacenter').attr("data-areaId");

            }
             if (area_id == -1) {
                    showMessage("请选择区域", "danger", 1000);
                    return;
                }


            var datacenter_name = $("#datacenter_name_d").val();
            var datacenter_type = $("#datacenter_type").val();
            var datacenter_address = $("#datacenter_address_d").val();
            var datacenter_remasks = $("#datacenter_remarks_d").val();
            var province=$("#local-province option:selected").html();
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
                    if(req.code != 0) {
                       res.msg != null ? showMessage(req.msg,"danger",1000) : showMessage("操作失败,请重试","danger",1000)
                    }else{
                        showMessage("操作成功","success",1000)
                    }

                    $("#area_list").bootstrapTable('refresh', {silent: true});
                    $("#addDatacenterModal").modal("hide");
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
        chocieProvince:function(){
            var html="";
            var list=this.data;
            for(var i=0;i<list.length;i++){
                html+="<option value="+i+">"+list[i].province+"</option>"
            }
            $("#local-province").html(html);
        }
    }

