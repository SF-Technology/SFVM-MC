/**
 * Created by 80002473 on 2017/3/31.
 */
$(function () {
    if (role_id_arr.length == 1 && role_id_arr[0] == 3) {
        $(".promission").css("display", "none");
    } else {
        $(".promission").css("display", "block");
    }
});


window.onload = function () {
        (function(){
        let envHtml = ''
       for(var i = 0;i<allEnvArrChinese.length;i++){
           envHtml= envHtml + ' <option value='+i+'>'+allEnvArr[i]+'</option>'
       }
        $("#group_env").html(envHtml)
    })()
    //列表生成
    applicationObj.init_table();

    //设置隐藏列
    $('#groupList').bootstrapTable('hideColumn', 'group_id');

    //选择成员权限期限
    //applicationObj.getTime();


    //创建应用组的模态框信息初始化
    $("#groupCreattomain").click(function ()//切换到主页面
    {
        backtomain("#main-page", "#create-application-page");
    });
    $("#groupaffirmtomain").click(function ()//修改组页面切换到主页面
    {
        backtomain("#main-page", "#affirm-application-page");
    });
    function backtomain(id1, id2) {
        $(id1).css("display", "block").animate({"left": "0"}, "slow");
        $(id2).animate({"left": "100%"}, "slow", function () {
            $(this).css("display", "none");
        });
    }


    //创建应用组触发事件
    $(function () {
        var create = new CreateGroupFun();
        $("#group-add-submit").click(function () {
            var area_str = create.area_ids;
            area_str == null ? (showMessage("请选择组所属区域", "danger", 1000)) : create.createGroup(area_str);
        });
        $("#add-01").click(function ()//切换到创建页面
        {
            create.area_ids = null;
            applicationObj.inputInit("#group-name-a", "#owner-name-a", "#cmdb-host-id", "#form-info input");
            $("#area-sel-table").html("").parent().parent().css("display", "none");
            create.bulidTree();
            $("#create-application-page").css("display", "block").animate({"left": "0"}, "slow");
            $("#main-page").animate({"left": "-100%"}, "slow", function () {
                $(this).css("display", "none");
            });
            $("#create-application-page").css("display", "block").animate({"left": "0"}, "slow");
            $("#main-page").animate({"left": "-100%"}, "slow", function () {
                $(this).css("display", "none");
            });
        });


        $("#area-tree").on('click.jstree', function ()//动态生成已选区域展示信息以及获取已选区域ID
        {
            create.area_ids = create.openId("#area-sel-table", "#area-tree");

            //create.area_ids = create.openId();
        });

        $("#area-sel-table").on("click", "i", function ()//删除已选区域列表
        {
            var id = $(this).parent().attr("data-ids");
            var ref = $('#area-tree').jstree(true);
            ref.uncheck_node(id);
            create.area_ids = create.openId("#area-sel-table", "#area-tree");

            //create.area_ids = create.openId();
        });
    });


    //删除应用组信息
    $("#deletegroupBtn").click(function () {
        applicationObj.deleteGroup();

    });

    //修改应用组信息
    $(function () {
        var revisionArea = new CreateGroupFun();
        $("#affirm-area-sel-table").on("click", "i", function ()//修改区域
        {
            var id = $(this).parent().attr("data-ids");
            var ref = $('#affirm-area-tree').jstree(true);
            ref.uncheck_node(id);
            revisionArea.area_ids = revisionArea.openId("#affirm-area-sel-table", "#affirm-area-tree", applicationObj.roleAreaList);
        });

        $("#affirm-area-tree").on('click.jstree', function ()//动态生成已选区域展示信息以及获取已选区域ID
        {
            revisionArea.area_ids = revisionArea.openId("#affirm-area-sel-table", "#affirm-area-tree", applicationObj.roleAreaList);
            //console.log(ramTree.area_ids);
        });
        $("#group-affirm-submit").click(function ()// 提交修改组信息
        {
            var name = $("#group-name-b").val();
            var owner = $("#owner-name-b").val();
            var p_cluster_id = $("#cmdb-host-id-b").val();
            var group_id = $("#group-affirm-submit").attr("data-group-id");
            var role_id = $("#group-affirm-submit").attr("data-role-id");


            var cpu = $("#quato_cpu").val();
            var disk = $("#quato_disk").val();
            var mem = $("#quato_mem").val();
            var vm = $("#quato_vm").val();


            var area_str = revisionArea.area_ids;

            if (!area_str) {
                area_str = applicationObj.ids;
                if (!area_str) {
                    showMessage("请分配组所属区域", "danger", 1000);
                    return;
                }
            }
            var data = "name=" + name + "&owner=" + owner + "&role_id=" + role_id + "&area_str=" + area_str + "&cpu=" + cpu+"&disk=" + disk+"&mem=" + mem+"&vm=" + vm + "&p_cluster_id=" + p_cluster_id;

            $.ajax({
                url: "/group/" + group_id,
                type: "PUT",
                dataType: "json",
                data: data,
                success: function (res) {
                    if (res.code != 0) {
                        res.msg != null ? showMessage(res.msg, "danger", 2000) : showMessage("请求失败,请刷新重试", "danger", 2000);
                    } else {
                        showMessage("修改成功", "success", 1000);
                    }
                    $('#groupList').bootstrapTable('refresh');
                    $("#main-page").css("display", "block").animate({"left": "0"}, "slow");
                    $("#affirm-application-page").animate({"left": "100%"}, "slow", function () {
                        $(this).css("display", "none");
                    });
                }
            });
        })
    });


    //按应用组或者所有者查询信息
    $("#singleCheck").click(function () {
        applicationObj.seekGroupInfo();

        $('#groupList').bootstrapTable('refresh', {silent: true});

    });

    //删除成员模态框信息初始化
    $("#groupList").on("click", '.deleteMemberBtnSingle', function (e) {
        var targetEle = e.target;
        applicationObj.getMemberInfo(targetEle);
    });

    //删除成员功能
    $("#deletMember").click(function () {
        var deleteMem = this;
        applicationObj.deletMember(deleteMem);
    });

    //选择角色
    $("#sel-region").change(function () {
        applicationObj.roleSel();
    });


    //用户域选择事件
    $("#sel-region").on("change", function () {
        $("#addMember input").val("");
    })

    //效验密码规则
    $("#user_password_addmember").blur(function () {
        var res = checkPassword();
        if (!res) {
            showMessage("所输密码不符合规则，请重新输入", "danger", 1200);
            $("#user_password_addmember").val('');
        }
    })


    //效验用户输入密码是否符合规则
    function checkPassword() {
        var password = $("#user_password_addmember").val();
        var result = false;
        var reg = /(?:(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[~!@#$%^&*()_+{}\:"<>?,./;'=-]+)).{10,}/;
        if (reg.test(password))
            result = true;
        return result;
    }

    //增加成员功能
    $("#addMemberOneBtn").click(function () {
        var data = {};
        var group_id = $(this).attr("data-groupidone");
        var group_name = $(this).attr("data-groupName");
        var user_id = $("#user_id_addmember").val();
        var auth_type = $("#sel-region").val();
        var user_name = $("#user_name_addmember").val();
        var password = $("#user_password_addmember").val();
        var email = $("#user_email_addmember").val();

        //效验密码确认
        var password_affirm = $("#user_password_addmember_affirm").val();
        if (password != password_affirm) {
            showMessage("两次密码输入不同，请重新输入", "danger", 1200);
            $("#user_password_addmember_affirm").val('').focus();
            return;
        }


        auth_type == "-1" && showMessage("请选择用户域", "danger", 1000);
        if (auth_type == "0") {
            if (group_name == "" || user_id == "") {
                showMessage("请填写完整信息", "danger", 1000);
                return;
            }
            data.auth_type = auth_type;
            data.group_name = group_name;
            data.user_id = user_id;
            applicationObj.addMember("/user_group/user/" + group_id, data);
        }
        if (auth_type == "1") {
            var reg = /^([a-zA-Z0-9_-])+@([a-zA-Z0-9_-])+(.[a-zA-Z0-9_-])+/;
            if (reg.test(email) == true) {
                data.email = email
            } else {
                showMessage("邮箱格式不正确,请重新填写！！！", "danger", 1000);
                return;
            }

            if (group_name == "" || user_id == "" || user_name == "" || password == "" || email == "") {
                showMessage("请填写完整信息", "danger", 1000);
                return;
            }
            data.auth_type = auth_type;
            data.group_name = group_name;
            data.user_id = user_id;
            data.user_name = user_name;
            var base = new Base64();
            var password = base.encode(password);
            data.password = password;
            applicationObj.addMember("/user_group/otheruser/" + group_id, data);
        }


    });


}
var applicationObj = {
    roleAreaList: null,//保存创建成员表中的区域信息
    ids: null,//修改组信息中的初始id集合
    envArr: allEnvArrChinese,
            // 0       1          2             3          4         5             6
    init_table: function () {
        $('#groupList').bootstrapTable({
            url: '/group/list',
            method: 'get',
            dataType: "json",
            detailView: true,
            uniqueId: "id",//删除时能用到 removeByUniqueId
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
            checkboxHeader: false,
            clickToSelect: false,
            singleSelect: false,
            onBeforeLoadParams: {},//查询参数设置，供导出使用，在search_form.js里赋值
            sortable: false,
            responseHandler: function (res) {
                if (res.code == 0) {
                    return res.data;
                } else {
                    return {rows: [], total: 0};
                }
            },
            onSearch: function (text) {
                search_text = text;
            },
            queryParams: function (q) {
                var str = "";
                if ($("#owner-group").attr("data-search-text")) {
                    str = JSON.parse($("#owner-group").attr("data-search-text")).search;
                }


                return {
                    "page_size": q.pageSize,
                    "page_no": q.pageNumber,
                    "search": str
                };
            },
            onLoadSuccess: function (data) {
                var row = data.rows;
                applicationObj.quotaInfo(row);
                //tableOperaShow();

            },
            onClickCell: function (field, value, row, $element) {

            },
            onClickRow: function ($element, row) {

            },
            columns: [
                {
                    title: "组ID",
                    field: "group_id",
                    align: "center",
                },
                {
                    title: "应用组名",
                    field: "name",
                    align: "left",
                    class: "getgroupId",
                },
                {
                    title: "环境类型",
                    field: "dc_type",
                    align: "left",
                    formatter: function (value, row, index) {
                         return applicationObj.envArr[parseInt(row.dc_type)]
                    }
                },
                {
                    title: "所有者",
                    field: "owner",
                    align: "left",
                },
                {
                    title: "配额 (CPU / MEM / DISK / VM)",
                    field: "quota",
                    align: "left",
                    class: "quota"
                },
                {
                    title: "角色",
                    field: "role_id",
                    align: "left",
                    formatter: function (value, row, index) {
                        var role_id = row.role_id;
                        role_id == 1 && (role_id = "系统管理员");
                        role_id == 2 && (role_id = "应用管理员");
                        role_id == 3 && (role_id = "只读用户");
                        return role_id;
                    }
                },
                {
                    title: "操作",
                    field: "operation",
                    align: "left",
                    events: window.operateEvents,
                    formatter: function (value, row, index) {
                        if (userList.user_permisson.length == 0) {
                            return "--";
                        } else {
                            for (var i = 0; i < id_arr.length; i++) {
                                var role_id_num = id_arr[i][0];
                                var group_id_num = id_arr[i][1];
                                var group_id_name = id_arr[i][2];
                                if (row.group_id == group_id_num && group_id_name != 'supergroup') {
                                    if (row.owner == user_id_num) {
                                        if (role_id_num == 1) {
                                            return ['<a id="addMemberOne" class="showIf" data-target="#addMember" data-toggle="modal" tittle="add"><i class="fa fa-plus-circle text-info"></i></a>&nbsp;',
                                                '<a id="reviseGroupOne" class="showIf"  tittle="create"><i class="fa fa-pencil-square text-success"></i></a>&nbsp;'
                                            ].join('');
                                        }
                                        if (role_id_num == 2 || role_id_num == 3) {
                                            return ['<a id="addMemberOne" class="showIf" data-target="#addMember" data-toggle="modal" tittle="add"><i class="fa fa-plus-circle text-info"></i></a>&nbsp;',
                                                '<a id="reviseGroupOne" class="showIf"  tittle="create"><i class="fa fa-pencil-square text-success"></i></a>&nbsp;'
                                            ].join('');
                                        }
                                    } else {
                                        return "--";
                                    }
                                } else if (group_id_name == 'supergroup') {
                                    if (row.group_id == group_id_num) {
                                        return ['<a id="addMemberOne" class="showIf" data-target="#addMember" data-toggle="modal" tittle="add"><i class="fa fa-plus-circle text-info"></i></a>&nbsp;',
                                            '<a id="reviseGroupOne" class="showIf"  tittle="create"><i class="fa fa-pencil-square text-success"></i></a>&nbsp;'
                                        ].join('');
                                    } else {
                                        return ['<a id="addMemberOne" class="showIf" data-target="#addMember" data-toggle="modal" tittle="add"><i class="fa fa-plus-circle text-info"></i></a>&nbsp;',
                                            '<a id="reviseGroupOne" class="showIf"  tittle="create"><i class="fa fa-pencil-square text-success"></i></a>&nbsp;',
                                            '<a id="deleteGroupOne" class="showIf" data-target="#deleteGroup" data-toggle="modal" tittle="delete"><i class="fa fa-trash-o text-danger"></i></a>&nbsp;',
                                        ].join('');
                                    }
                                }
                            }
                        }
                    }
                }
            ],
            onExpandRow: function (index, row, $detail) {
                applicationObj.showMemberInfo(index, row, $detail);
            }
        })
    },
    inputInit: function (id1, id2, id3, id4) {
        var arr = [20, 40, 2000, 10];
        $(id1).val("");
        $(id2).val("");
        $(id3).val("");
        for (var i = 0; i < arr.length; i++) {
            $(id4)[i].value = arr[i];
        }
    },
    quotaInfo: function (row)//配额拼接
    {

        var list = $(".quota:not(:first-child)");
        for (var i = 1; i < list.length; i++) {
            ( row[i - 1].cpu == null) && ( row[i - 1].cpu = 0);
            ( row[i - 1].disk == null) && ( row[i - 1].disk = 0);
            ( row[i - 1].mem == null) && ( row[i - 1].mem = 0);
            ( row[i - 1].vm == null) && ( row[i - 1].vm = 0);
            list[i].innerHTML = row[i - 1].cpu + '核&nbsp;/&nbsp;' + row[i - 1].mem + 'G&nbsp;/&nbsp;' + row[i - 1].disk + 'G&nbsp;/&nbsp;' + row[i - 1].vm + '&nbsp;个';
            $(".getgroupId")[i].setAttribute("data-id", row[i - 1].group_id);
        }
    },
    showMemberInfo: function (index, row, $detail)//生成子表
    {
        var getMember = this;
        $.ajax({
            url: "/user_group/" + row.group_id,
            type: "get",
            dataType: "json",
            success: function (res) {
                if (res.code != 0) {
                    showMessage("操作失败", "danger", 1000);
                    return;
                }
                var list = res.data.rows;

                var html = "<table class='table text-left table-hover-one'>";
                var super_html = "<table class='table text-left table-hover-one'>";
                var super_variate = false;
                var isSuper = true;
                    for (var j = 0; j < id_arr.length; j++) {
                        var role_id_num = id_arr[j][0];
                        var group_id_num = id_arr[j][1];
                        var group_id_name = id_arr[j][2];
                        if (group_id_num == row.group_id && group_id_name != 'supergroup') {
                            if (row.owner == user_id_num) {
                                $.each(list, function (i, tmp) {
                                    html += '<tr><td><a data-target="#deleteMember"  data-toggle="modal"  tittle="delete" class="deleteMemberBtnSingle"><i class="fa fa-times text-danger"></i></a></td><td>' + tmp.user_id + '</td><td>' + tmp.user_name + '</td></tr>';
                                })
                            } else {
                                 $.each(list, function (i, tmp) {
                                    html += '<tr><td></td><td>' + tmp.user_id + '</td><td>' + tmp.user_name + '</td></tr>';
                                })
                            }
                        }else if (group_id_name == 'supergroup' && group_id_num == row.group_id) {
                                super_variate = true;
                                $.each(list, function (i, tmp) {
                                    super_html += '<tr><td><a data-target="#deleteMember"  data-toggle="modal"  tittle="delete" class="deleteMemberBtnSingle"><i class="fa fa-times text-danger"></i></a></td><td>' + tmp.user_id + '</td><td>' + tmp.user_name + '</td></tr>';
                                })
                        } else{
                            if (isSuper) {
                                $.each(list, function (i, tmp) {
                                    html += '<tr><td><a data-target="#deleteMember"  data-toggle="modal"  tittle="delete" class="deleteMemberBtnSingle"><i class="fa fa-times text-danger"></i></a></td><td>' + tmp.user_id + '</td><td>' + tmp.user_name + '</td></tr>';
                                })
                                isSuper = false;
                            }
                        }
                    }
                html += '</table>';
                super_html += '</table>';
                if(super_variate){
                    $detail.html(super_html);
                }else{
                    $detail.html(html);
                }
            }
        })
    },
    seekGroupInfo: function ()//查询
    {
        var val = $("#groupOwn option:selected").val();
        var str1 = "", str2;
        var params = {};
        val == 0 && (str1 = "group_name");
        val == 1 && (str1 = "owner");
        val == 2 && (str1 = "user_id");
        var owner = $("#owner-group").val();
        if (owner == "") {
            str2 = "";
            $("#owner-group").val("").attr("data-search-text", "");
        } else {
            params[str1] = owner;
            str2 = JSON.stringify(params);
            $("#owner-group").val("").attr("data-search-text", JSON.stringify({"search": str2}));
        }

        return {
            search: str2
        }

    },
    getMemberInfo: function (targetEle) {
        var html = "";
        var td = $(targetEle).parent().parent().siblings();
        var group = $(targetEle).parents(".detail-view").prev().children(".getgroupId");
        var group_id = group.attr("data-id");


        html += '<td>' + td[0].innerHTML + '</td>';
        html += '<td>' + td[1].innerHTML + '</td>';
        html += '<td>' + group.html() + '</td>';
        //html+='<td>'+td[2].innerHTML+'</td>';


        $("#deleteMemberInfo").html(html);
        $("#deletMember").attr("data-groupId", group_id);

    },
    deletMember: function (deleteMem) {
        var user_id = $("#deleteMemberInfo td:first-child").html();
        var group_id = $(deleteMem).attr("data-groupId");
        var data = {user_id: user_id, group_id: group_id};
        applicationObj.operaAjax("/user_group", "", "DELETE", data, "#deleteMember");
    },
    deleteGroup: function () {
        var group_id = $("#deletegroupBtn").attr("data-groupidone");
        applicationObj.operaAjax("/group/", group_id, "DELETE", "", "#deleteGroup");
    },
    roleSel: function ()//用户域选择
    {
        var getThis = this;
        var role = $("#sel-region option:selected").html();
        if (role == "FF") {
            $("#others-role").css("display", "none");
        } else if (role == "MC") {
            $("#others-role").css("display", "block");
            $("#f-role").css("display", "none");
        }
    },
    addMember: function (url, data) {
        $.ajax({
            url: url,
            type: "post",
            dataType: "json",
            data: data,
            success: function (res) {
                if (res.code != 0) {
                    res.msg != null ? showMessage(res.msg, "danger", 1000) : showMessage("操作失败,请刷新重试", "danger", 1000);
                    ;
                } else {
                    showMessage("操作成功", "success", 1000);
                }
                $("#addMember").modal("hide");
                $('#groupList').bootstrapTable('refresh', {silent: true});
            }
        });
    },
    operaAjax: function (url, group_id, type, data, id) {
        $.ajax({
            url: url + group_id,
            type: type,
            data: data,
            dataType: "json",
            success: function (res) {
                if (res.code != 0) {
                    res.msg != null ? showMessage(res.msg, "danger", 1000) : showMessage("删除失败,请刷新重试", "danger", 1000);
                } else {
                    showMessage("操作成功", "success", 1000);
                }
                $('#groupList').bootstrapTable('refresh', {silent: true});
                $(id).modal("hide");
            }
        })
    },
    affirmGroupInfoInit: function (group_id) {
        $.ajax({
            url: "/group/init_info/" + group_id,
            type: "get",
            cache: false,
            success: function (res) {
                var list = res.data.all_area;
                var row = res.data.used_area[0];
                var default_row = row.area_list;
                var ids = [];
                //初始化默认信息
                $("#group-name-b").val(row.name);
                $("#owner-name-b").val(row.owner);
                $("#cmdb-host-id-b").val(row.p_cluster_id != null ? row.p_cluster_id : "");
                $(".qutao_b[name='cpu']").val(row.cpu);
                $(".qutao_b[name='mem']").val(row.mem);
                $(".qutao_b[name='disk']").val(row.disk);
                $(".qutao_b[name='vm']").val(row.vm);

                $("#group-affirm-submit").attr("data-group-id", group_id);
                $("#group-affirm-submit").attr("data-role-id", row.role_id);

                $.each(default_row, function (index, tmp) {

                    if (tmp.children) {
                        for (var i = 0; i < tmp.children.length; i++) {
                            ids.push(tmp.children[i].id);
                        }
                    } else {
                        ids.push(tmp.parent_id);
                    }
                });


                var arr = {};
                var data_params = [];

                $.each(list, function (index, tmp) {
                    if (!arr[tmp.parent_name]) {
                        arr[tmp.parent_name] = [[tmp.name, tmp.id, tmp.parent_id]];
                    } else {
                        arr[tmp.parent_name].push([tmp.name, tmp.id, tmp.parent_id]);
                    }
                });
                applicationObj.roleAreaList = arr;

                //console.log(ids);
                //console.log(arr);
                for (var i in arr) {
                    var parentInfo = {
                        "id": null,//parent_id
                        "text": null,//parentname
                        "children": [],
                        //"icon": "none",
                        "state": {
                            "opened": true,
                            "selected": false,
                            "disabled": false
                        }
                    };
                    parentInfo.text = i;

                    for (var a = 0; a < id_arr.length; a++) {
                        if (id_arr[a][0] == 1 && id_arr[a][2] == 'supergroup') {
                            parentInfo.state["disabled"] = false;
                        } else {
                            parentInfo.state["disabled"] = true;
                        }
                    }


                    for (var j = 0; j < arr[i].length; j++) {
                        parentInfo.id = arr[i][j][2];
                        if (arr[i][0][0] == null || arr[i][0][1] == null) {
                            if (ids.indexOf(arr[i][0][2]) != -1) {
                                parentInfo.state["selected"] = true;
                                parentInfo.state["opened"] = false;
                                parentInfo.children = "";
                            }
                        } else {
                            var childInfo = {
                                "id": null,//chidl_id
                                "text": null,//child_name
                                //"icon": "none",
                                "state": {
                                    "selected": false,
                                    "disabled": false
                                }
                            };
                            for (var a = 0; a < id_arr.length; a++) {
                                if (id_arr[a][0] == 1 && id_arr[a][2] == 'supergroup') {
                                    childInfo.state["disabled"] = false;
                                } else {
                                    childInfo.state["disabled"] = true;
                                }
                            }
                            childInfo.text = arr[i][j][0];
                            childInfo.id = arr[i][j][1];

                            if (ids.indexOf(arr[i][j][1]) != -1 || ids.indexOf(arr[i][0][2]) != -1) {
                                parentInfo.state["opened"] = true;
                                childInfo.state["selected"] = true;
                            }
                            parentInfo.children.push(childInfo);
                        }
                    }
                    data_params.push(parentInfo);
                }
                $('#area-tree').data('jstree', false).empty();
                $('#affirm-area-tree').data('jstree', false).empty();
                $("#affirm-area-tree").jstree({
                    "types": {
                        "default": {
                            "icon": false  // 删除默认图标
                        },
                    },
                    "plugins": ["wholerow", "checkbox", "types"],
                    //plugins: ["checkbox", "types", "themes", "state"],  // state保存选择状态
                    "checkbox": {  // 去除checkbox插件的默认效果
                        //tie_selection: true,
                        keep_selected_style: false,
                        //whole_node: true
                    },
                    "core": {
                        "themes": {"stripes": false},  // 条纹主题
                        "data": data_params
                    }
                });

                $("#affirm-area-tree").on("loaded.jstree", function (e, data) {
                    var initObj = new CreateGroupFun();
                    var dataarr = arr;
                    var area_str = initObj.openId("#affirm-area-sel-table", "#affirm-area-tree", dataarr);
                    applicationObj.ids = area_str;
                });

            },
            error: function () {
                showMessage("请求失败，请刷新页面重试", "danger", 1000);
                return;
            }
        });
    },
}


//删除应用组的信息初始化
window.operateEvents =
{
    "click #addMemberOne": function (e, value, row, index) {
        $("#addMemberOneBtn").attr("data-groupidone", row.group_id);
        $("#addMemberOneBtn").attr("data-groupName", row.name);
        $("#addMember input").val("");
        $("#others-role").css("display", "none");
        $("#sel-region").val("-1");
        $("#user_group").html(row.name);
    },
    "click #reviseGroupOne": function (e, value, row, index) {
        if (row.owner == user_id_num || (role_id_arr.indexOf("1"))) {
            row.role_id == 1 && ($("#role_id_show").val("系统管理员"));
            row.role_id == 2 && ($("#role_id_show").val("应用管理员"));
            row.role_id == 3 && ($("#role_id_show").val("只读用户"));
            getpremission(row);
            applicationObj.affirmGroupInfoInit(row.group_id);
            $("#affirm-application-page").css("display", "block").animate({"left": "0"}, "slow");
            $("#main-page").animate({"left": "-100%"}, "slow", function () {
                $(this).css("display", "none");
            });
        } else {
            showMessage("您没有此权限！！！", "danger", 2000);
        }
    },
    'click #deleteGroupOne': function (e, value, row, index) {
        $('#updateAreaModal').modal({
            backdrop: 'static',
            keyboard: false
        })
        var list = $("#groupInfoOne td");
        $("#deletegroupBtn").attr("data-groupidone", row.group_id);
        list[0].innerHTML = row.name;
        list[1].innerHTML = row.owner;
        list[2].innerHTML = row.cpu + '核&nbsp;' + row.disk + 'G&nbsp;' + row.mem + 'G&nbsp;' + row.vm + '个&nbsp;';
    }

}

var CreateGroupFun = function () {
};

function getpremission(row) {

    //设置所有者修改权限
    for (var i = 0; i < id_arr.length; i++) {
        var group_id_num = id_arr[i][1];
        var group_id_name = id_arr[i][2];
        //var role_id_num = id_arr[i][0];
        if (user_id_num == row.owner) {
            $("#owner-name-b").attr("disabled", false);
            if (row.role_id == 3 || row.role_id == 2) {
                $("#form-info-show input").attr("disabled", true);
                $("#cmdb-host-id-b").attr("disabled", true);
            } else {
                $("#form-info-show input").attr("disabled", false);
                $("#cmdb-host-id-b").attr("disabled", false)
            }
        } else {
            if (group_id_name == 'supergroup') {
                if (row.group_id == 1) {
                    $("#owner-name-b").attr("disabled", true);
                } else {
                    $("#owner-name-b").attr("disabled", false);
                }
                $("#cmdb-host-id-b").attr("disabled", false)
                $("#form-info-show input").attr("disabled", false);
            } else {
                $("#owner-name-b").attr("disabled", true);
                $("#cmdb-host-id-b").attr("disabled", true)
                $("#form-info-show input").attr("disabled", true);
            }
        }
    }


}


CreateGroupFun.prototype =
{
    area_ids: null,
    treedata: null,
    openId: function (id1, id2, data)//获取被选中区域的id
    {
        if (data == null) {
            data = this.treedata;
        }

        //获取选中的节点
        var nodes = $(id2).jstree("get_checked");

        nodes.length > 0 && $(id1).parent().parent().css("display", "block");
        nodes.length == 0 && $(id1).parent().parent().css("display", "none");


        var a = 0, html = "", area_str = [], default_id_obj = {}, default_area_obj = {};

        for (var key in data) {
            var list = data[key];
            if (list.length == 1 && (list[0][0] == null || list[0][1] == null)) {
                default_id_obj[key + "|" + data[key][0][2]] = "";
            } else {
                for (var i = 0; i < list.length; i++) {
                    var index = key + "|" + list[i][2];
                    if (!default_id_obj[index]) {
                        default_id_obj[index] = [list[i][1]];
                    } else {
                        default_id_obj[index].push(list[i][1]);
                    }

                    if (!default_area_obj[index]) {
                        default_area_obj[index] = [list[i][0]];
                    } else {
                        default_area_obj[index].push(list[i][0]);
                    }

                }
            }
        }


        for (var key in default_id_obj) {
            var parent_id = key.substring(key.indexOf("|") + 1);
            var child_id_arr = default_id_obj[key];
            var child_area_arr = default_area_obj[key];
            var childarea = "", parentarea = "", data_id = "";
            if (nodes.indexOf(parent_id) != -1) {
                a++;
                parentarea = key.substring(0, key.lastIndexOf("|"));
                data_id = parent_id;
                if (child_id_arr == "") {
                    childarea = "无";
                    area_str.push(parent_id);
                } else {
                    for (var i = 0; i < child_area_arr.length; i++) {
                        area_str.push(child_id_arr[i]);
                        if (i == child_area_arr.length - 1) {
                            childarea += child_area_arr[i];
                        } else {
                            childarea += child_area_arr[i] + "、";
                        }
                    }
                }
                html += "<tr>";
                html += '<td>' + a + '</td>';
                html += '<td>' + parentarea + '</td>';
                html += '<td>' + childarea + '</td>';
                var deg1 = false;
                for (var b = 0; b < id_arr.length && deg1 == false; b++) {
                    if (id_arr[b][0] == 1 && id_arr[b][2] == 'supergroup') {
                        deg1 = true;
                        html += '<td data-ids=' + data_id + '><i class="fa fa-trash-o text-danger" style="cursor: pointer" id="remove-select-area"></i></td></tr>';
                    }
                }
                if (deg1 == false) {
                    html += '<td data-ids=' + data_id + '></td></tr>';
                }

            } else {
                for (var n = 0; n < nodes.length; n++) {
                    if (child_id_arr.indexOf(parseInt(nodes[n])) != -1) {
                        var id_index = child_id_arr.indexOf(parseInt(nodes[n]));
                        a++;
                        parentarea = key.substring(0, key.lastIndexOf("|"));
                        childarea = child_area_arr[id_index];
                        data_id = nodes[n];
                        area_str.push(nodes[n]);
                        html += "<tr>";
                        html += '<td>' + a + '</td>';
                        html += '<td>' + parentarea + '</td>';
                        html += '<td>' + childarea + '</td>';
                        var deg = false;
                        for (var c = 0; c < id_arr.length && deg == false; c++) {
                            if (id_arr[c][0] == 1 && id_arr[c][2] == 'supergroup') {
                                deg = true;
                                html += '<td data-ids=' + data_id + '><i class="fa fa-trash-o text-danger" style="cursor: pointer" id="remove-select-area"></i></td></tr>';
                            }
                        }
                        if (deg == false) {
                            html += '<td data-ids=' + data_id + '></td></tr>';
                        }
                    }
                }
            }
        }

        $(id1).html(html);
        return area_str.toString();

    },
    bulidTree: function ()//jstree的生成
    {
        var groupObj = this;
        var data = [];
        $.ajax({
            url: "/user_group/init_area",
            type: "get",
            success: function (res) {
                if (res.code != 0) {
                    res.msg != null ? showMessage(res.msg, "danger", 2000) : showMessage("获取创建信息失败,请稍后重试", "danger", 2000);
                    return;
                } else {
                    var list = res.data.rows;

                    if(list.length==0){
                        showMessage("获取创建信息失败,请稍后重试", "danger", 2000);
                        return;
                    }
                    var arr = {};
                    $.each(list, function (index, tmp) {
                        if (!arr[tmp.parent_name]) {
                            arr[tmp.parent_name] = [[tmp.name, tmp.id, tmp.parent_id]];
                        } else {
                            arr[tmp.parent_name].push([tmp.name, tmp.id, tmp.parent_id]);
                        }
                    });

                    groupObj.treedata = arr;
                    for (var i in arr) {
                        var parentInfo = {
                            "id": null,//parent_id
                            "text": null,//parentname
                            //"state": {"opened": false},
                            "children": []
                        };

                        parentInfo.text = i;
                        if (arr[i].length == 1 && arr[i][0][0] == null) {
                            parentInfo["children"] = "";
                            parentInfo.id = arr[i][0][2];
                            //console.log(arr[i],i);
                        } else {
                            for (var j = 0; j < arr[i].length; j++) {
                                var childInfo = {
                                    "id": null,//chidl_id
                                    "text": null,//child_name
                                    //"state": {"opened": false}
                                };
                                childInfo.text = arr[i][j][0];
                                childInfo.id = arr[i][j][1];
                                parentInfo.id = arr[i][j][2];
                                parentInfo["children"].push(childInfo);
                            }
                        }
                        data.push(parentInfo);

                    }
                    $('#area-tree').data('jstree', false).empty();
                    $('#affirm-area-tree').data('jstree', false).empty();
                    //区域树生成
                    $("#area-tree").jstree({
                        "types": {
                            "default": {
                                "icon": false  // 删除默认图标
                            },
                        },
                        plugins: ["checkbox", "types", "themes"],  // state保存选择状态
                        "checkbox": {  // 去除checkbox插件的默认效果
                            tie_selection: false,
                            keep_selected_style: false,
                            whole_node: false
                        },
                        "core": {
                            "themes": {"stripes": false},  // 条纹主题
                            "data": data
                        }
                    })
                }
            },
            error: function () {
                showMessage("请求失败", "danger", 2000);
            }
        });
    },
    createGroup: function (area_str) //创建应用组
    {
        let data = {};
        data.name = $("#group-name-a").val();
        data.area_str = area_str;
        data.owner = $("#owner-name-a").val();
        data.role_id = $("#role_id").val();
        data.p_cluster_id = $("#cmdb-host-id").val();
        data.dc_type = $("#group_env").val();
        let formData = $("#form-info").serialize().split("&");
        console.log(formData)
        for (var i = 0 ; i< formData.length; i++) {
            let item = formData[i].split("=");
            data[item[0]] = item[1]
        }

        if (data.role_id == "-1") {
            showMessage("请选择角色", "danger", 600)
            return;
        }
        if (data.dc_type == "-1") {
            showMessage("请选择组所属环境", "danger", 600)
            return;
        }

        //var str1 = "name=" + name + "&owner=" + owner + "&" + str + "&area_str=" + area_str +"dc_type="+ dc_type + "&role_id=" + role_id + "&p_cluster_id=" + p_cluster_id;
        //console.log(str1);
        if (!isEmpty("#create-application-page input")) return false;
        $.ajax({
            url: "/group",
            type: "post",
            data: data,
            dataType: "json",
            success: function (res) {
                if (res.code != 0) {
                    res.msg != null ? showMessage(res.msg, "danger", 1000) : showMessage("创建失败,请刷新重试", "danger", 1000);
                } else {
                    showMessage("创建成功", "success", 1000);
                    $('#groupList').bootstrapTable('refresh');
                    $("#main-page").css("display", "block").animate({"left": "0"}, "slow");
                    $("#create-application-page").animate({"left": "100%"}, "slow", function () {
                        $(this).css("display", "none");
                    });
                }
            }
        });

    },

}