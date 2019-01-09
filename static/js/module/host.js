/**
 * Created by 80002473 on 2017/3/29.
 */
var SyncFun = function () {
};
$(function () {
    var urlName = getUrlPath();
    if (role_id_arr.length == 1 && role_id_arr[0] == 3) {
        $(".promission").css("display", "none");
        return;
    }
    var list = $(".promission");
    $.each(user_permisson_arr, function (i, tmp) {
        if (tmp[urlName].length > 0) {
            $.each(list, function (k, ele) {
                var num = tmp[urlName].indexOf(ele.getAttribute("data-promission"));
                if (num != -1) {
                    ele.style.display = "inline-block";
                }
                if (num == -1) {
                    ele.style.display = "none";
                }
            });
        } else {
            list.style.display = "none";
        }
    });
});


window.onload = function () {
    createHostInfo.init_table();
     $('#host_list').bootstrapTable('hideColumn', 'manage_ip');
     $('#host_list').bootstrapTable('hideColumn', 'hold_mem_gb');
     $('#host_list').bootstrapTable('hideColumn', 'hostpool');
    refreshChart();

    //关闭监控信息模态框同时关闭时间选项模态框
    $('#hostMonitor').on('hidden.bs.modal', function (e) {
        $('#time_range').modal('hide');
    });

    //选中checkbox则启动开关机按钮

    if (createHostInfo.myBrowser() == "IE") {
        $('#host_list').on('click', 'input[type="checkbox"]', function () {
            createHostInfo.checkSelect();
        });
    } else {
        $('#host_list').on('change', 'input[type="checkbox"]', function () {
            createHostInfo.checkSelect();
        });
    }


    //创建host
    $("#createSure").click(function () {
        if (isEmpty("#addHostModal input")) {
            createHostInfo.create_host();
        }

    });

    //批量开机
    $("#onPower").click(function () {
        createHostInfo.batchOperaInfoInit(0, "#poweron-table");
    });
    $("#powerOnBtn").click(function () {
        createHostInfo.batchOpera(0, "#poweronModal");
    });

    //批量关机
    $("#offPower").click(function () {
        createHostInfo.batchOperaInfoInit(1, "#powerOff-table");
        $(".i-checks1 input[type='radio']")[0].checked = true;
        $(".i-checks1 input[type='radio']")[1].checked = false;
        $(".i-checks1")[2].style.display = "none"
    });

    $("#shutdownModal .i-checks1 input[name='hostoff']").change(function () {
        var thisOne = this;
        createHostInfo.checkOne(thisOne, "#shutdownModal .i-checks1", "#powerOffBtn")
    });
    $("#shutdownModal .i-checks1 input[type='checkbox']").change(function () {
        var thisTwo = this;
        createHostInfo.checkTwo(thisTwo, "#powerOffBtn")

    });
    $("#powerOffBtn").click(function () {
        var flag = "";
        var n = $(".i-checks1 input[name='hostoff']:checked").val();
        //console.log(n);
        n == "option1" && (flag = 2);
        n == "option2" && (flag = 1);

        //console.log(flag);
        if (flag != '') {
            createHostInfo.batchOpera(flag, "#shutdownModal");
        } else {
            showMessage("请点击关机按钮", 'info', 1000);

        }
    });


    //批量重启
    $("#restart").click(function () {
        createHostInfo.batchOperaInfoInit(3, "#restart-table");
        $(".i-checks2 input[type='radio']")[0].checked = true;
        $(".i-checks2 input[type='radio']")[1].checked = false;
        $(".i-checks2")[2].style.display = "none"
    });
    $("#restartModal .i-checks2 input[name='restart']").change(function () {
        var thisOne = this;
        createHostInfo.checkOne(thisOne, "#restartModal .i-checks2", "#restartBtn")
    });
    $("#restartModal .i-checks2 input[type='checkbox']").change(function () {
        var thisTwo = this;
        createHostInfo.checkTwo(thisTwo, "#restartBtn")
    });
    $("#restartBtn").click(function () {
        var flag = "";
        var n = $(".i-checks2 input[name='restart']:checked").val();
        console.log(n);
        n == "option1" && (flag = 4);
        n == "option2" && (flag = 3);

        //console.log(flag);
        if (flag != '') {
            createHostInfo.batchOpera(flag, "#restartModal");
        } else {
            showMessage("请点击关机按钮", 'info', 1000);
            return;
        }
        createHostInfo.checkSelect();
    });


    //批量删除
    createHostInfo.isSingle = true
    $("#host-delete-some").click(function () {
        createHostInfo.batchOperaInfoInit(5, "#host-delete-some-table");
        createHostInfo.isSingle = false
        $(".delete-check input").prop("checked", false);
        $("#host-delete-someBtn").attr("disabled", true);
    });
    $(".delete-check input").click(function () {
        //console.log(!$(this).prop("checked"));
        $("#host-delete-someBtn").attr("disabled", !$(this).prop("checked"));
    });

    $("#host-delete-someBtn").click(function () {
        var data = {};
       if (createHostInfo.isSingle) {
            data.host_id = $("#host-delete-someBtn").attr('hostId')
       } else {
          data.host_id = getIds();
       }
        createHostInfo.operaHostRequest("/host/delete", data);
        $("#host-delete-some-modal").modal("hide");
        $("#host-delete-someBtn").attr('hostId', '');
        createHostInfo.isSingle = true
        createHostInfo.checkSelect();
    });
    function getIds() {
        var host_id = "";
        var arr = [];
        var list = $('#host_list').bootstrapTable('getSelections');

        $.each(list, function (index, tmp) {
            arr.push(tmp.host_id);
        });
        host_id = arr.join(",");
        return host_id
    }

    //锁定或者取消锁定、开机 强制关机 关机 强制重启 重启
    $("#host_list").on("click", "#operaHost li", function () {
        var host_id = createHostInfo.hostID;
        var str = $(this).children().html();
        if (str == "删除") {
            return;
        }
        createHostInfo.operaHostResponse(str, host_id);
    });


    //host主副页面切换
    $("#returnBtn li>a").click(function (e) {
        e.preventDefault();
        $("#mainHost").css("display", "block");
        $("#mainHost").animate({left: '15px'}, 'slow');
        $("#secondHost").animate({left: "100%"}, 'slow', function () {
            $(this).css("display", "none");
        });
        $("#host_list").bootstrapTable('refresh', {silent: true});
    });


    timer = setInterval(function () {
        if ($("#secondHost").css("display") == "block") {
            refreshTable(createHostInfo.hostID);
        }
    }, 3000);

    $("body").click(function () {
        createHostInfo.judgeopera();
    });

    $("#host-search-sel").change(function () {
        var text_selected = $(this).val();
        if (text_selected == "status") {
            $("#host-search-text").css("display", "none").val("");
            $("#host-statu-text").css("display", "block").val("-1");
        } else {
            $("#host-search-text").css("display", "block").val("");
            $("#host-statu-text").css("display", "none").val("-1");
        }
    });
    function searchHost () {
        var text_selected = $("#host-search-sel").val(), search_text = "", str = "", params = {};
        text_selected == "status" && (search_text = $("#host-statu-text").val());
        text_selected != "status" && (search_text = $("#host-search-text").val());
        if (text_selected == "status" && search_text == "-1") {
            showMessage("请选择要查询的主机的状态", "danger", 1000);
            return;
        }
        if (search_text == "") {
            str = "";
            $("#host-search-text").attr("data-search-text", "");
        } else {
            params[text_selected] = search_text;
            str = JSON.stringify(params);
            $("#host-search-text").val(" ").attr("data-search-text", JSON.stringify({"search": str}));
        }
        $("#host-statu-text").val("-1")
        $('#host_list').bootstrapTable('refresh', {silent: true});
    }
    $("#host-search-text").keyup(function(event){
        if (event.keyCode == 13) {
            searchHost()
        }
    })
    $("#host-search-btn").click(function () {
        searchHost()
    });

    $("#update_host_sure").click(function () {
        var host_id = $(this).attr("data-hostid");
        var name = $("#update-host-name").val();
        var ip_address = $("#update-ip-name").val();
        var manage_ip = $("#update-manageip-name").val();
        var patt1 = new RegExp("^(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|[1-9])\\." + "(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|\\d)\\." + "(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|\\d)\\." + "(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|\\d)$");
        var hold_mem_gb = $("#update-memory").val();
        if (
            name == "" || ip_address == "" || manage_ip == "" || hold_mem_gb == ""
        ) {
            showMessage("请输入完整信息", "danger", 2000);
            return;
        }
        if (!patt1.test(ip_address)) {
            showMessage("IP地址格式不正确,请重输", "danger", 2000);
            return;
        }
        if (!patt1.test(manage_ip)) {
            showMessage("管理IP地址格式不正确,请重输", "danger", 2000);
            return;
        }
        $.ajax({
            url: "/host/" + host_id,
            type: "put",
            dataType: "json",
            data: {
                "name": name,
                "ip_address": ip_address,
                "manage_ip": manage_ip,
                "hold_mem_gb": hold_mem_gb,
            },
            success: function (res) {
                if (res.code != 0) {
                    res.msg != null ? showMessage(res.msg, "danger", 1000) : showMessage("修改失败,请刷新重试", "danger", 1000)
                } else {
                    showMessage("修改成功", "success", 2000);
                    $("#updateHostModal").modal("hide");
                }
                $("#host_list").bootstrapTable("refresh", {silent: true});
            },
            error: function () {
                showMessage("请求不成功,请重试", "danger", 2000);
            }
        });
    });


//镜像同步
    $(".searchImage").keyup(function () {
        $(".list-group").empty();
        var imageName = $(this).val(),
            remoteImageList = createHostInfo.remoteImageList,
            arr = [];
        if (imageName === "")return;
        for (var i = 0, tmp; tmp = remoteImageList[i++];) {
            var image = tmp.displayname;
            arr.push(image);
        }
        arr = arr.unique();
        for (var i = 0, tmp; tmp = arr[i++];) {
            if (tmp.toLowerCase().indexOf(imageName.toLowerCase()) >= 0) {
                $(".list-group").append("<li class='list-group-item'>" + tmp + "</li>");
            }
        }

        $(".list-group").slideDown();
    });

    $(".list-group").on("click", "li", function () {
        $(".noneImage").remove();
        var imagename = $(this).text().trim(),
            remoteImageList = createHostInfo.remoteImageList,
            html = "";
        if (createHostInfo.addImageList.length > 0) {
            for (var i = 0, item; item = createHostInfo.addImageList[i++];) {
                if (item.displayname === imagename) {
                    showMessage("该镜像已添加至列表", "warning", 2000);
                    return;
                }
            }
        }


        for (var i = 0, tmp; tmp = remoteImageList[i++];) {
            if (imagename === tmp.displayname) {
                createHostInfo.addImageList.push({
                    "displayname": tmp.displayname,
                    "actual_size_mb": tmp.actual_size_mb,
                    "name": tmp.name,
                    "system": tmp.system,
                    "description": tmp.description,
                    "id": tmp.id,
                    "task_info": {}
                })
                html += "<tr> <td><input type='checkbox' value=" + tmp.name + "(" + tmp.id + ")></td>";
                html += "<td>" + tmp.displayname + "</td>";
                html += "<td>" + tmp.system + "</td>";
                html += "<td>" + tmp.description + "</td>";
                html += "</tr>";
            }
        }
        $("#getImage-table").append(html);
        $(".searchImage").val("");
        $(".list-group").slideUp();
        $(".list-group").html("");
    });


    SyncFun._image_list = {};//所有镜像的数据集合
    SyncFun.selectedImage = [];//用户选择需要同步的镜像集合
    SyncFun.oldtaskTimearr = [];//已有任务任务时间数据集合
    SyncFun.selectImageArr = [];//用户已选镜像名称和描述组合的集合
    //SyncFun.getmintimearr = [];
    SyncFun.getmaxtimearr = [];//所有任务中的结束时间的集合
    SyncFun.taxkDetails = {};//添加任务临时存储数据集合
    SyncFun.hostid = 0;//添加任务临时存储数据集合
    SyncFun.dataParams = {};//提交任务信息集合
    SyncFun.isEmptyObject = function (e) {//判断一个对象是否为空
        var t;
        for (t in e)
            return !1;
        return !0
    };
    SyncFun.getSelected = function () {
        this._image_list = createHostInfo.addImageList.concat(
            createHostInfo.localImageList
        );
        var selectedArr = $("#getImage-table tr").children("td:first-child").children(":checked");
        check_val = [];
        for (var k = 0, tmp; tmp = selectedArr[k++];) {
            if (tmp.checked) {
                check_val.push(tmp.value);
                var name = tmp.value;
                for (var i = 0, item; item = this._image_list[i++];) {

                    if (name === (item.name + "(" + item.id + ")")) {
                        this.selectedImage.push(item);
                    }
                }
            }
        }
        //console.log(this.selectedImage);
        return check_val;
    };
    SyncFun.syncInitInfo = function () {
        SyncFun.oldtaskTimearr.length = 0;
        SyncFun.selectImageArr.length = 0;
        for (var i = 0, tmp; tmp = this.selectedImage[i++];) {
            SyncFun.selectImageArr.push(tmp.name + "(" + tmp.description + ")");
            if (i === 1) {
                $("#imageList").append(
                    '<li class="active" data-name = "' + tmp.name + "(" + tmp.description + ")" + '"><a href=' + tmp.id + '>' + tmp.displayname + "(" + tmp.description + ")" + '</a></li>'
                );

                if (this.isEmptyObject(tmp.task_info) || tmp.task_info.ondo_task === "1") {
                    $("#oldtasktimeList").html("").parent().slideUp();
                    $("#speed_limit").val("").attr("disabled", false);
                    $("#needTime").html(0);
                    $("#residueNum").html(7);
                } else {
                     tmp.task_info.ondo_task === "1" && $("#oldtasktimeList").parent().slideUp();
                    tmp.task_info.ondo_task === "0" && $("#oldtasktimeList").parent().slideDown();
                    $("#speed_limit").val(tmp.task_info.speed_limit).attr("disabled", true);
                    $("#needTime").html(
                        (tmp.actual_size_mb / tmp.task_info.speed_limit / 60).toFixed(2) > 0
                            ? (tmp.actual_size_mb / tmp.task_info.speed_limit / 60).toFixed(2)
                            : "小于1"
                    );
                    $("#residueNum").html(7 - parseInt(tmp.task_info.task_sch_ondo_num));
                    for (var j = 0, item; item = tmp.task_info.task_sch_ondo_list[j++];) {
                        $("#oldtasktimeList").append(
                            '<li data-num=' + tmp.task_info.task_sch_ondo_num + '>' +
                            '<span style="padding-right: 10px">任务' + j + ':</span>' +
                            '<span>' + item.sch_starttime + ' </span>至' +
                            '&nbsp;&nbsp;<span>' + item.sch_endtime + '</span> </li>'
                        );
                        SyncFun.oldtaskTimearr.push([item.sch_starttime, item.sch_endtime]);
                    }
                }
            } else {
                if (!this.isEmptyObject(tmp.task_info) && tmp.task_info.ondo_task === "0") {
                    for (var j = 0, item; item = tmp.task_info.task_sch_ondo_list[j++];) {
                        SyncFun.oldtaskTimearr.push([item.sch_starttime, item.sch_endtime]);
                    }
                }
                $("#imageList").append(
                    '<li data-name = "' + tmp.name + "(" + tmp.description + ")" + '"><a href=' + tmp.id + '>' + tmp.displayname + "(" + tmp.description + ")" + '</a></li>'
                );
            }
        }
    };
    SyncFun.switchImage = function (imagename) {
        var list = this.selectedImage;
        $("#oldtasktimeList").html("");
        for (var i = 0, tmp; tmp = list[i++];) {
            //console.log(tmp.displayname + "(" + tmp.description + ")");
            if (imagename === (tmp.displayname + "(" + tmp.description + ")" )) {
                if (this.isEmptyObject(tmp.task_info) || tmp.task_info.ondo_task === "1") {
                    $("#oldtasktimeList").parent().slideUp();
                    $("#speed_limit").val("").attr("disabled", false);
                    $("#needTime").html(0);
                    $("#residueNum").html(7);
                } else {
                    $("#speed_limit").val(tmp.task_info.speed_limit).attr("disabled", true);
                    $("#needTime").html(
                        (tmp.actual_size_mb / tmp.task_info.speed_limit / 60).toFixed(2) > 0
                            ? (tmp.actual_size_mb / tmp.task_info.speed_limit / 60).toFixed(2)
                            : "小于1"
                    );

                    $("#residueNum").html(7 - parseInt(tmp.task_info.task_sch_ondo_num));
                    tmp.task_info.ondo_task === "1" && $("#oldtasktimeList").parent().slideUp();
                    tmp.task_info.ondo_task === "0" && $("#oldtasktimeList").parent().slideDown();

                    for (var j = 0, item; item = tmp.task_info.task_sch_ondo_list[j++];) {
                        $("#oldtasktimeList").append(
                            '<li data-num=' + tmp.task_info.task_sch_ondo_num + '>' +
                            '<span style="padding-right: 10px">任务' + j + ':</span>' +
                            '<span>' + item.sch_starttime + ' </span>至' +
                            '&nbsp;&nbsp;<span>' + item.sch_endtime + '</span> </li>'
                        );
                        SyncFun.oldtaskTimearr.push([item.sch_starttime, item.sch_endtime]);
                    }
                }
                if (SyncFun.taxkDetails[(tmp.name + "(" + tmp.description + ")" )]) {
                    $("#speed_limit").val("").attr("disabled", true).val(
                        SyncFun.taxkDetails[(tmp.name + "(" + tmp.description + ")" )]._speed_limit
                    );
                    $("#needTime").html(
                        SyncFun.taxkDetails[(tmp.name + "(" + tmp.description + ")" )].need_time
                    );
                    $("#residueNum").html(
                        SyncFun.taxkDetails[(tmp.name + "(" + tmp.description + ")" )].remainNum
                    )
                }
            }
        }
        ;
        $("#statrtTime").val('');
        $("#endTime").val('');
        SyncFun.setTimeType();
    };
    SyncFun.countTaskTime = function ()//计算出最晚的结束时间作为下一个添加的任务时间的开始时间
    {
        var tiemarr = createHostInfo.addImageList.concat(
            createHostInfo.localImageList
        );
        this.getmaxtimearr.length = 0;

        for (var i = 0, tmp; tmp = tiemarr[i++];) {
            var list = tmp.task_info.task_sch_ondo_list;
            if (list) {
                for (var j = 0, item; item = list[j++];) {
                    this.getmaxtimearr.push(new Date(item.sch_endtime).getTime());
                }
            } else {
                this.getmaxtimearr.push(new Date().getTime());
            }
        }
        ;
    };
    SyncFun.setTimeType = function () //清除样式并重新生成一个时间控件
    {
        $("#statrtTime").datetimepicker('remove');
        $("#endTime").datetimepicker('remove');
        //console.log(Math.max.apply(null,SyncFun.getmaxtimearr));
        var startTime = Math.max.apply(null, SyncFun.getmaxtimearr);
        var nowTime = new Date().getTime();
        if (nowTime > startTime) {
            startTime = nowTime;
        }
        $("#statrtTime").datetimepicker({
            format: 'yyyy-mm-dd hh:ii',//日期的格式
            startDate: new Date(startTime + 5 * 60 * 1000),//选择器的开始日期
            autoclose: true,//日期选择完成后是否关闭选择框
            bootcssVer: 3,//显示向左向右的箭头
            language: 'zh_CN',//语言
            minView: 0,//表示日期选择的最小范围，默认是hour
            todayBtn: true,
        }).on("changeDate", function () {
            var userStartTime = $("#statrtTime").val();
            userStartTime = new Date(userStartTime).getTime() + 35 * 60 * 1000;
            $("#endTime").datetimepicker("setStartDate", new Date(userStartTime));
        });
        ;
        $("#endTime").datetimepicker({
            format: 'yyyy-mm-dd hh:ii',//日期的格式
            autoclose: true,//日期选择完成后是否关闭选择框
            bootcssVer: 3,//显示向左向右的箭头
            language: 'zh_CN',//语言
            minView: 0,//表示日期选择的最小范围，默认是hour
            todayBtn: true,
        });
    };

    SyncFun.judgeInput = function (data, str)//判断用户是否输入
    {
        if (data === "") {
            showMessage(str, "warning", 2000);
            return false;
        }
        return true;
    };
    SyncFun.addTaskist = function (data)//添加计划任务
    {
        var startTime = new Date(+new Date(data.startTime) + 8 * 3600 * 1000).toISOString().replace(/T/g, ' ').replace(/\.[\d]{3}Z/, '');
        var endTime = new Date(+new Date(data.endTime) + 8 * 3600 * 1000).toISOString().replace(/T/g, ' ').replace(/\.[\d]{3}Z/, '');
        var tasksingle = {"sch_starttime": startTime, "sch_endtime": endTime};
        var imagename = data.imagename;

        if (!SyncFun.taxkDetails[imagename]) {
            SyncFun.taxkDetails[imagename] = {};
            SyncFun.taxkDetails[imagename].image_id = data.image_id;
            SyncFun.taxkDetails[imagename].tasknumber = 1;
            SyncFun.taxkDetails[imagename]._speed_limit = data.speed_limit;
            SyncFun.taxkDetails[imagename].need_time = data.need_time;
            //SyncFun.taxkDetails[imagename].remainNum = parseInt(data.remainNum);
            SyncFun.taxkDetails[imagename].tasksingle = [tasksingle];
            SyncFun.setTaskTable(startTime, endTime, data);
        } else {
            SyncFun.taxkDetails[imagename].tasknumber = parseInt(SyncFun.taxkDetails[imagename].tasknumber) + 1;
            SyncFun.taxkDetails[imagename].tasksingle.push(tasksingle);
            //SyncFun.taxkDetails[imagename].remainNum = parseInt(data.remainNum)-1;
            var html = "<li>";
            html += "<label>任务" + SyncFun.taxkDetails[data.imagename].tasknumber + ":</label>";
            html += "<span>" + startTime + "</span>&nbsp;&nbsp;至&nbsp;&nbsp;";
            html += "<span>" + endTime + "</span>";
            html += "&nbsp;&nbsp;<span><a><i class='fa fa-times text-danger deleteTask'></i></a></span>";
            html += "</li>";
            $("[data-imagename='" + data.imagename + "']").children().children(".tasktimeList").append(html);
        }
        //console.log(SyncFun.taxkDetails);
    };
    SyncFun.setTaskTable = function (startTime, endTime, data)//动态生成任务表格
    {
        var html = "<tr data-imagename = " + data.imagename + ">";
        html += "<td>" + data.displayname + "</td>";
        html += "<td>" + data.speed_limit + "MB/S</td>";
        html += "<td>";
        html += "<ul class='list-unstyled tasktimeList'>";
        html += "<li>";
        html += "<label>任务" + SyncFun.taxkDetails[data.imagename].tasknumber + ":</label>";
        html += "<span>" + startTime + "</span>&nbsp;&nbsp;至&nbsp;&nbsp;";
        html += "<span>" + endTime + "</span>";
        html += "&nbsp;&nbsp;<span><a><i class='fa fa-times text-danger deleteTask'></i></a></span>";
        html += "</li>";
        html += "</ul>";
        html += "</td>";
        html += "<td><span><a><i class='fa fa-trash-o text-danger deleteImageOne'></i></a></span></td>";
        html += "</tr>";
        $("#newtasktable").append(html);


    };
    SyncFun.submitImageTask = function () {
            $.ajax({
            url: "/image_sync/host_task_intodb",
            type: "post",
            dataType: "json",
            data: JSON.stringify(SyncFun.dataParams),
            success: function (res) {
                if (res.code === -10000) {
                    showMessage("请求失败,请刷新重试", "danger", 2000);
                } else {
                    var fail_task_list = res.data.fail_task_list;
                    var succss_task_list = res.data.succss_task_list;
                    if (fail_task_list.length === 0) {
                        showMessage("任务添加成功", "success", 2000);
                        createHostInfo.addImageList = [];
                        createHostInfo.localImageList = [];
                        createHostInfo.remoteImageList = [];
                        $("#statrtTime").datetimepicker('remove');
                        $("#endTime").datetimepicker('remove');
                        $(".searchImage").val("");
                        $(".list-group").slideUp();
                        $(".list-group").html("");
                        $("#getImage-table").html("");
                        $("#oldtasktimeList").html("");
                        $("#mainHost").css("display", "block");
                        $("#mainHost").animate({left: "15px"}, "slow");
                        $("#thirdHost").animate({left: "100%"}, 'slow', function () {
                            $(this).css("display", "none")
                        });
                    } else {
                        var successImageId = [], list = SyncFun.taxkDetails;
                        for (var i = 0, tmp; tmp = fail_task_list[i++];) //错误任务标红
                        {
                            var message = tmp.error_message.error_message;
                            var error = message.substring(0, message.indexOf("相关镜像为")-1).trim();
                            var imageName = message.substring(message.indexOf("相关镜像为") + 5, message.indexOf("错误的开始时间为")).trim();
                            var startTime = message.substring(message.indexOf("错误的开始时间为") + 8, message.indexOf("错误的结束时间为")).trim();
                            var endTime = message.substring(message.indexOf("错误的结束时间为") + 8).trim();
                            var li = $("#newtasktable").children("[data-imagename='" + imageName + "']").find(".tasktimeList").children();
                            for (var j = 0, item; item = $(li)[j++];) {
                                var oldendTime = $(item).children("span+span").html();
                                var oldstartTime = $(item).children("span")[0].innerHTML;
                                if (
                                    new Date(startTime).getTime() === new Date(oldstartTime).getTime() ||
                                    new Date(endTime).getTime() === new Date(oldendTime).getTime()
                                ) {
                                    $(item).addClass("errorColor");
                                    $(item).children(":last-child").before("<span>&nbsp;&nbsp;"+error+"&nbsp;&nbsp;</span>");
                                }
                            }

                        }
                        for (var i = 0, s; s = succss_task_list[i++];) //获取成功镜像的id
                        {
                            successImageId.push(s.image_id);
                        }
                        for(var i in list){
                             if (successImageId.indexOf(list[i].image_id) >= 0) {
                                //SyncFun.getmaxtimearr.splice(SyncFun.getmaxtimearr.indexOf(new Date(endTime).getTime()), 1);
                                $("#newtasktable").children("[data-imagename='" + i + "']").remove();
                                $("#imageList").children("[data-name='" + i + "']").remove();
                                $("#imageList").children(":first-child").addClass("active").siblings().removeClass("active");
                                delete  SyncFun.taxkDetails[i];
                                 SyncFun.selectImageArr.splice(SyncFun.selectImageArr.indexOf(i),1);
                            }
                        }
                        $("#statrtTime").val('');
                        $("#endTime").val('');
                        SyncFun.setTimeType();
                    }
                }
            },
            error: function () {
                showMessage("请求失败,请刷新重试", "danger", 2000);
            }
        });

    };

    $("#getImageBtn").click(function () //切换到镜像添加任务页面
    {
        $("#imageList").html("");
        SyncFun._image_list = {};
        SyncFun.selectedImage = [];
        SyncFun.taxkDetails = [];
        SyncFun.getSelected();
        if (SyncFun.selectedImage.length <= 0) {
            showMessage("没有选中的镜像", "danger", 2000);
            return;
        }
        SyncFun.syncInitInfo();
        SyncFun.countTaskTime();
        SyncFun.setTimeType();
        $("#getImageModal").modal("hide");
        $("#thirdHost").css("display", "block");
        $("#thirdHost").animate({left: "3%"}, "slow");
        $("#mainHost").animate({left: "-100%"}, 'slow', function () {
            $(this).css("display", "none")
        });
    });
    $(".gotomainhost").click(function (e)//回到主页
    {
        e.preventDefault();
        createHostInfo.addImageList = [];
        createHostInfo.localImageList = [];
        createHostInfo.remoteImageList = [];
        $("#statrtTime").datetimepicker('remove');
        $("#endTime").datetimepicker('remove');
        $(".searchImage").val("");
        $(".list-group").slideUp();
        $(".list-group").html("");
        $("#getImage-table").html("");
        $("#oldtasktimeList").html("");
        $("#mainHost").css("display", "block");
        $("#mainHost").animate({left: "15px"}, "slow");
        $("#thirdHost").animate({left: "100%"}, 'slow', function () {
            $(this).css("display", "none")
        });
    });

    $("#speed_limit").change(function () {
        var speed = $(this).val();
        var image = $("#imageList").children("li.active").children().text();
        var list = SyncFun.selectedImage;
        for (var i = 0, tmp; tmp = list[i++];) {
            if ((tmp.displayname + "(" + tmp.description + ")" ) === image) {
                $("#needTime").html(
                    (tmp.actual_size_mb / speed / 60).toFixed(2) > 1
                        ? (tmp.actual_size_mb / speed / 60).toFixed(2)
                        : "小于1"
                );
            }
        }
    });

    $("#imageList").on("click", "li a", function (e) //选择添加任务的镜像
    {
        e.preventDefault();
        $(this).parent().addClass("active").siblings().removeClass("active");
        var imageName = $(this).text();
        SyncFun.switchImage(imageName);
    });

    $("#addTask").click(function () {
        var data = {}, remainTime = 0;
        var imageTarget = $("#imageList").children("li.active").children();
        var imagename = $("#imageList").children("li.active").attr("data-name");

        data.image_id = $(imageTarget).attr("href");
        data.imagename = imagename;
        data.displayname = $(imageTarget).text();
        data.speed_limit = $("#speed_limit").val();
        data.startTime = $("#statrtTime").val();
        data.endTime = $("#endTime").val();
        data.need_time = $("#needTime").text();
        data.remainNum = parseInt($("#residueNum").text());
        //remainTime = data.need_time - ((new Date(data.endTime)-new Date(data.startTime))/60000).toFixed(2);

        if (
            !SyncFun.judgeInput(data.speed_limit, "请设置限速") || !SyncFun.judgeInput(data.startTime, "请选择任务开始时间") || !SyncFun.judgeInput(data.endTime, "请选择任务结束时间")
        ) {
            return;
        }

        if (data.remainNum === 0) {
            showMessage("该镜像已有7个计划任务,不能再创建任务！", 'danger', 2000);
            return;
        }


        SyncFun.addTaskist(data);

        SyncFun.getmaxtimearr.push(new Date(data.endTime).getTime());
        SyncFun.setTimeType();


        $("#residueNum").html(data.remainNum - 1);
        SyncFun.taxkDetails[imagename].remainNum = data.remainNum - 1;
        $("#speed_limit").attr("disabled", true);
        $("#statrtTime").val("");
        $("#endTime").val("");
    });


    //计划任务提交
    $("#submitNewtask").click(function () {
         var deg = false,liList = $("#newtasktable").find("li");
        for(var n = 0,d;d = liList[n++];){
            if($(d).hasClass("errorColor")){
                deg = true;
            }
        }
        if(deg){
            showMessage("任务列表有错误数据,请删除再提交","danger",2000);
            return;
        }

        var data = {}, image_list = [], noneImageArr = [];
        var selectedImageArr = SyncFun.selectImageArr.concat([]);
        data.host_id = SyncFun.hostid;
        for (var i in SyncFun.taxkDetails) {
            var tmp = SyncFun.taxkDetails[i];
            if (selectedImageArr.indexOf(i) >= 0) {
                    image_list.push({
                        'image_id': tmp.image_id,
                        'task_list': tmp.tasksingle,
                        "speed_limit": tmp._speed_limit,
                        'start_time': new Date(+new Date() + 8 * 3600 * 1000).toISOString().replace(/T/g, ' ').replace(/\.[\d]{3}Z/, '')
                    });
                selectedImageArr.splice(selectedImageArr.indexOf(i), 1);
            }
        }
        if (image_list.length === 0) {
            showMessage("您还没有为您的镜像添加任务哦！", "danger", 2000);
            return;
        }
        data.image_list = image_list;
        //console.log(data);
        SyncFun.dataParams = data;


        $("#someImageNone").html("");
        if (selectedImageArr.length > 0) {
            for (var j = 0, item; item = selectedImageArr[j++];) {
                $("#someImageNone").css("display", "block").append('<li class="list-group-item">' + item + '</li>');
            }
            $("#showImageModal").modal({backdrop: 'static', keyboard: false});
            return;
        } else {
            SyncFun.submitImageTask();
        }

    });

    $("#sureSubmit").click(function () {
        $("#showImageModal").modal("hide");
        $("#someImageNone").html("");
        console.log(SyncFun.dataParams);
        SyncFun.submitImageTask();
    });

    $("#newtasktable").on("click", ".deleteTask", function ()//删除image下的单个任务时间
    {
        var tr = $(this).parents("tr");
        var li = $(this).parents("li");
        var imagename = $(tr).attr("data-imagename");

        var startTime = $(this).parents("li").children("span")[0].innerHTML;
        var endTime = $(this).parents("li").children("span+span").text();

        startTime = new Date(startTime).getTime();
        endTime = new Date(endTime).getTime();


        //比对taxkDetails中的task_info，并删除该任务,以及页面的静态
        //重置任务序号以及可添加任务时间,设置可添加任务时间数量
        var list = SyncFun.taxkDetails[imagename];
        for (var i = 0, tmp; tmp = list.tasksingle[i++];) {
            if (
                new Date(tmp.sch_endtime).getTime() === endTime &&
                new Date(tmp.sch_starttime).getTime() === startTime
            ) {

                SyncFun.taxkDetails[imagename].tasksingle.splice(i - 1, 1);
            }
        }
        SyncFun.taxkDetails[imagename].remainNum += 1;
        SyncFun.taxkDetails[imagename].tasknumber -= 1;
        SyncFun.getmaxtimearr.splice(SyncFun.getmaxtimearr.indexOf(endTime), 1);
        $("#residueNum").html(SyncFun.taxkDetails[imagename].remainNum);


        if (SyncFun.taxkDetails[imagename].tasknumber > 0) {
            var labelList = $(li).parent().children().children("label");
            var num = SyncFun.taxkDetails[imagename].tasknumber;
            while (num > 0) {
                $(labelList)[num].innerHTML = "任务" + num + ":";
                num--;
            }
            $(li).remove();
        } else if (SyncFun.taxkDetails[imagename].tasknumber === 0) {
            $(tr).remove();
            delete  SyncFun.taxkDetails[imagename];
        }
        $("#statrtTime").val('');
        $("#endTime").val('');
        //console.log(Math.max.apply(null,SyncFun.getmaxtimearr))
        SyncFun.setTimeType();


    });

    $("#newtasktable").on("click", ".deleteImageOne", function ()//删除image任务
    {
        //获取tr 以及该镜像下的所有任务结束时间
        var tr = $(this).parents("tr");
        var li = $(tr).children().children(".tasktimeList").children();
        var imageName = $(tr).attr("data-imagename");

        for (var i = 0, tmp; tmp = li[i++];) {
            var endTime = $(tmp).children("span+span").html();
            endTime = new Date(endTime).getTime();
            SyncFun.getmaxtimearr.splice(SyncFun.getmaxtimearr.indexOf(endTime), 1);
        }

        $(tr).remove();
        delete  SyncFun.taxkDetails[imageName];
        $("#statrtTime").val('');
        $("#endTime").val('');
        //console.log(Math.max.apply(null,SyncFun.getmaxtimearr))
        SyncFun.setTimeType();
    });

};


function refreshTable(host_id) {
    $.ajax({
        url: "/host/info/" + host_id,
        type: "get",
        dataType: "json",
        success: function (result) {
            var td_list = $("#infoList tr").children(":last-child");
            var list = result.data;
            if (result.code != 0) {
                result.msg != null ? showMessage(result.msg, "danger", 1000) : showMessage("请求失败,请刷新重试", "danger", 1000);
                for (var i = 0; i < td_list.length; i++) {
                    var td = td_list[i];
                    $(td).html("");
                }
            } else {
                for (var i = 0; i < td_list.length; i++) {
                    var td = td_list[i];
                    var name = $(td).attr("title");
                    if (list[name] != null) {
                        if (name == "status") {
                            list[name] == 0 && (list[name] = "运行中");
                            list[name] == 1 && (list[name] = "关机");
                            list[name] == 99 && (list[name] = "Unknown");
                        }
                        name == "current_disk_used" && (list[name] += "%");
                        name == "current_mem_used" && (list[name] += "%");
                        name == "current_cpu_used" && (list[name] += "%");
                        name == "disk_size" && (list[name] += "G");
                        name == "mem_size" && (list[name] += "MB");
                        name == "cpu_core" && (list[name] += "核");
                        $(td).html(list[name]);
                    } else {
                        $(td).html("");
                    }
                }
            }
        }
    });
}
window.operateHostEvents = {

    //绑定远程事件
    "click #consolePage": function (e, value, row, index) {

        var consoleUrl;
        $.getJSON("/kvm/js/config/config.json", function (data) {
            var consoleAddress = data.consoleAddress;
            console.info(consoleAddress);
            consoleUrl = consoleAddress + "?manage_ip=" + row.manage_ip + "&sn=" + row.sn + "&dc_type=" + row.dc_type;
            window.open(consoleUrl);
        });
        // var url = window.location.href;
        //var position = url.indexOf("/");
        //var  imgUrl = url.substring(0, position);
        // var consoleUrl = imgUrl + ":4200/?manage_ip="+row.manage_ip;
        console.info(consoleUrl)
        // window.open(consoleUrl)
    },
    //绑定监控信息事件
    "click #monitorPage": function (e, value, row, index) {

        myChart = echarts.init(document.getElementById('main'));
        init_echart();
        $("#model-title").html(row.displayname);
        var ip = row.ipaddress;
        //console.info(ip);
        var ipList = {};
        ipList[ip] = [];
        console.info(ipList);
        var start_time = 30;
        var end_time = 30;
        sessionStorage.setItem("ip", ip);
        sessionStorage.setItem("ipList", JSON.stringify(ipList));
        refresh_mon(ip, ipList, start_time, end_time);
    },
    "click .operamore": function (e, value, row, index) {
        createHostInfo.judgeopera();
    },
    "click #update_host": function (e, value, row, index) {
        $("#updateHostModal input").val("");
        $("#update-host-name").val(row.displayname);
        $("#update-ip-name").val(row.ipaddress);
        $("#update-manageip-name").val(row.manage_ip);
        $("#update-memory").val(row.hold_mem_gb);
        $("#update_host_sure").attr("data-hostid", row.host_id);
        $("#updateHostModal").modal("show");
    },
    "click #host-delete": function(e, value, row, index){
        if (row.typestatus != 2) {
            showMessage("只有维护状态下的机器才允许删除！", "danger", 2000);
            return;
        }
        if (row.instance_nums != 0) {
                showMessage("物理机上有虚拟机，请先迁移虚拟机再重新执行删除操作", "danger", 2000);
                return;
        }
        var delete_str = '<tr><td>' + row.displayname +
            '</td><td>' + row.ipaddress +
            '</td><td>' + row.instance_nums +
            '</td><td>' + row.hostpool +
            '</td><td>' + row.datacenter +
            '</td></tr>'
        createHostInfo.isSingle = true
        $("#host-delete-someBtn").attr('hostId', row.host_id)
        $("#host-delete-some-table").html(delete_str)
        $("#host-delete-some-modal").modal('show')
        $(".delete-check input").prop("checked", false);
        $("#host-delete-someBtn").attr("disabled", true);
    }
};
 function DoOnMsoNumberFormat(cell, row, col) {
       var result = "";
       if (row > 0 && col == 0)
           result = "\\@";
       return result;
   }
var length_export;
var createHostInfo = {
    selHtml: function () {
        var html = "";
        0;
        html += '<div class="btn-group operamore">';
        html += '<button type="button" class="btn btn-primary dropdown-toggle btn-xs"  data-toggle="dropdown">更多';
        html += '<span class="fa fa-angle-down"></span>';
        html += '</button>';
        html += ' <ul id="operaHost" class="dropdown-menu" role="menu" style="min-width: 120px">';
        html += '<li id="lock" data-table-promission="lock" class="promission-table">';
        html += '<a href="#">锁定</a>';
        html += '</li>';
        html += '  <li id="cancelLock" data-table-promission="unlock" class="promission-table">';
        html += ' <a href="#">解除锁定</a>';
        html += '  </li>';
        html += '<li id="maintain" data-table-promission="maintain" class="promission-table">';
        html += ' <a href="#">维护</a>';
        html += ' </li>';
        html += ' <li id="maintainOver" data-table-promission="unmaintain" class="promission-table">';
        html += '<a href="#">结束维护</a>';
        html += ' </li>';
        html += ' <li id="syncImageOpera" data-table-promission="unmaintain" class="promission-table">';
        html += '<a href="#">镜像同步</a>';
        html += ' </li>';
        html += '<li id="restart" data-table-promission="reset" class="promission-table">';
        html += ' <a href="#">强制重启</a>';
        html += '</li>';
        html += '<li id="soft_restart" data-table-promission="softreset" class="promission-table">';
        html += ' <a href="#">重启</a>';
        html += '</li>';
        html += ' <li id="powerOn" data-table-promission="start" class="promission-table">';
        html += '<a href="#">开机</a>';
        html += '</li>';
        html += '<li id="powerOff" data-table-promission="stop" class="promission-table">';
        html += '<a href="#">强制关机</a>';
        html += ' </li>';
        html += '<li id="soft_powerOff" data-table-promission="softstop" class="promission-table">';
        html += ' <a href="#">关机</a>';
        html += '</li>';
        html += '<li id="host-delete" data-table-promission="delete" class="promission-table">';
        html += ' <a href="#">删除</a>';
        html += '</li>';
        html += '</ul>';
        html += '</div>';
        return html;
    },
    flagStaus: null,//存储状态码
    flagtypestatus: null,//存储状态码
    hostID: null,
    vmNum: null,//存储单行vm数量
    hostInfo: null,//存储后台返回的host信息

    init_table: function ()  //生成表格
    {
        var getHostId = this;
        $('#host_list').bootstrapTable({
            url: '/host/list',
            method: 'get',
            dataType: "json",
            detailView: false,
            showExport: true,//显示导出按钮
            exportDataType: "all",//导出类型
            exportTypes: ['all'],  //导出文件类型
            exportOptions: {
                ignoreColumn: [0, 14],  //忽略某一列的索引
                fileName: 'HOST信息',  //文件名称设置
                worksheetName: 'sheet1',  //表格工作区名称
                tableName: 'HOST详情',
                //excelstyles: ['background-color', 'color', 'font-size', 'font-weight'],
                onMsoNumberFormat: DoOnMsoNumberFormat
            },
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
                    return {rows: [], total: 0};
                }
            },
            onSearch: function (text) {
                search_text = text;
            },
            queryParams: function (q) {
                var key = '';
                if ($("#host-search-text").val("").attr("data-search-text")) {
                    key = JSON.parse($("#host-search-text").attr("data-search-text")).search;
                }
                return {
                    "page_size": q.pageSize,
                    "page_no": q.pageNumber,
                    "search": key
                };
            },
            onLoadSuccess: function (data) {
                //tableOperaShow();
                length_export = data.rows.length;
                //定时刷新列表
                createHostInfo.judgeopera();
            },
            onClickCell: function (field, value, row, $element) {
                getHostId.hostID = row.host_id;
                getHostId.vmNum = row.instance_nums;
                getHostId.flagStaus = row.status;
                getHostId.flagtypestatus = row.typestatus;
                //console.log(field);
                if (field == "displayname") {
                    createHostInfo.sliderHost();
                }
            },
            onClickRow: function ($element, row) {
//                console.log(row);

            },
            onCheckAll: function () {
                createHostInfo.judgeopera();
            },
            onUncheckAll: function () {
                createHostInfo.judgeopera();
            },
            onCheck: function () {
                if (createHostInfo.myBrowser() == "IE") {
                    createHostInfo.checkSelect();
                }
                createHostInfo.judgeopera();

            },
            onUncheck: function () {
                if (createHostInfo.myBrowser() == "IE") {
                    createHostInfo.checkSelect();
                }
                createHostInfo.judgeopera();
            },
            columns: [
                {
                    checkbox: true,
                },
                {
                    title: "序列号(主键)",
                    field: "sn",
                    align: "left",
                },
                {
                    title: "主机名",
                    field: "displayname",
                    align: "left",
                    class: "click"
                },
                {
                    title: "IP地址",
                    field: "ipaddress",
                    align: "left",
                },
                {
                    title: "状态",
                    field: "status",
                    align: "left",
                    formatter: createHostInfo.statusFormatter
                },
                {
                    title: "业务状态",
                    field: "typestatus",
                    align: "left",
                    formatter: createHostInfo.typestatusFormatter
                },
                {
                    title: "集群",
                    field: "hostpool",
                    align: "left",
                },
                {
                    title: "网络区域",
                    field: "net_area",
                    align: "left",
                },
                {
                    title: "所在机房",
                    field: "datacenter",
                    align: "left",
                },
                {
                    title: "机房类型",
                    align: "left",
                    valign: "middle",
                    formatter: function (value, row, index) {
                        var arr = allEnvArrChinese;
                        var dc_type = parseInt(row.dc_type);
                        return arr[dc_type];
                    }
                },
                {
                    title: "管理IP",
                    field: "manage_ip",
                    align: "left",
                },
                {
                    title: "VM数量",
                    field: "instance_nums",
                    align: "left",
                },
                {
                    title: "保留内存",
                    field: "hold_mem_gb",
                    align: "left",
                },
                {
                    title: "内存分配率(%)",
                    field: "mem_assign_per",
                    align: "left",
                },
                {
                    title: "操作",
                    field: "operation",
                    align: "left",
                    events: window.operateHostEvents,
                    formatter: function (value, row, index) {
                        return ['<a  class="seeInfo" data-toggle="modal" data-target="#hostMonitor" id="monitorPage" title="监控"><i class="fa fa-signal text-primary"></i></a>&nbsp;',
                            '<a id="update_host"  title="修改信息"><i class="fa fa-pencil-square"></i></a>&nbsp;',
                            '<a class="remote promission-table" tittle="VNC" data-table-promission="console"  id="consolePage" target="_blank"><i class="fa fa-laptop text-warning"></i></a>&nbsp;',
                            createHostInfo.selHtml()
                        ].join('');
                    }
                }
            ]
        })
    },

    judgeopera: function () {
        if (typeof timer2 != "undefined")clearTimeout(timer2);
        timer2 = setTimeout(function () {
            var sel_arr = $("#host_list").bootstrapTable("getSelections");
            var type = $(".operamore"), type_arr = [];
            var search_text = $("#host-search-text").val();
            for (var i = 0; i < type.length; i++) {
                if (type[i].className == "btn-group operamore open") {
                    type_arr.push("1");
                }
            }
            if ($("#mainHost").css("display") != "block" || sel_arr.length > 0 || type_arr.length > 0 || search_text != "")return;
            $("#host_list").bootstrapTable('refresh', {silent: true});
        }, 3000); //time是指本身,延时递归调用自己,100为间隔调用时间,单位毫秒

    },
    //host信息展示
    sliderHost: function () {
        var host_id = this.hostID;
        refreshTable(host_id);
        $("#mainHost").animate({left: '-100%'}, 'slow', function () {
            $(this).css('display', 'none');
        });
        $("#secondHost").css("display", "block").animate({left: '0px'}, 'slow');

    },

    //表格中业务状态信息转换
    typestatusFormatter: function (value, row, index) {
        var num = parseInt(value);
        var html = "";

        if (num >= 0) {
            num == 0 && (html = '正常');
            num == 1 && (html = '<i class="glyphicon glyphicon-lock text-danger"></i>&nbsp;锁定');
            num == 2 && (html = '<i class="glyphicon glyphicon-wrench text-warning"></i>&nbsp;维护');
            return html;
        } else {
            return "未知";
        }
    },

    //表格中状态信息转换
    statusFormatter: function (value, row, index) {
        var index = parseInt(value);
        if (index >= 0) {
            index == 0 && (html = '<i class="fa fa-desktop text-info"></i>&nbsp;运行中');
            index == 1 && (html = '<i class="fa fa-desktop text-danger"></i>&nbsp;关机');
            index == 99 && (html = '<i class="fa fa-desktop text-warning"></i>&nbsp;Unknown');
            return html;
        } else {
            return "未知";
        }
    },

    //表格中锁定和取消锁定操作互请交求
    operaHostRequest: function (url, data) {
        $.ajax({
            url: url,
            type: "put",
            data: data,
            dataType: "json",
            beforeSend: function () {
                $("#loading").css("display", "block");
            },
            success: function (result) {
                $('#onPower').addClass('disabled').attr('data-target', '');
                $('#offPower').addClass('disabled').attr('data-target', '');
                $('#restart').addClass('disabled').attr('data-target', '');
                $('#host-delete-some').addClass('disabled').attr('data-target', '');
                $("#loading").css("display", "none");
                $("#host_list").bootstrapTable('refresh', {silent: true});

                if (result.code != 0) {
                    result.msg != null ? showMessage(result.msg, "danger", 1000) : showMessage("操作失败", "danger", 1000);
                } else {
                    showMessage("操作成功", "success", 1000);
                }
            }
        });
    },

    //锁定或者取消锁定、维护取消维护、开机 强制关机 关机 强制重启 重启方法
    operaHostResponse: function (str, host_id, status, typestatus) {
        var flag = '', num, data = {};

        (status == undefined) ? (status = this.flagStaus) : status;
        (typestatus == undefined) ? (typestatus = this.flagtypestatus) : typestatus;

        //console.log(str);
        //console.log(typestatus);
        //console.log(status);

        //## KVM物理机状态流程
        //```
        //运行中：不可以开机
        //关机：不可以关机、强制关机
        //错误：不可
        //锁定：可以做物理机所有操作：开机、关机、强制关机、重启、强制重启
        //维护：可以做物理机所有操作：开机、关机、强制关机、重启、强制重启
        str == "锁定" && (typestatus == 0) && (flag = "1", num = 0);
        str == "解除锁定" && (typestatus == 1) && (flag = "0", num = 0);
        str == "开机" && (status != 0) && (flag = "0", num = 2);
        str == "强制关机" && (status != 1 && status != 2) && (flag = "1", num = 2);
        str == "关机" && (status != 1 && status != 2) && (flag = "2", num = 2);
        str == "强制重启" && (status != 2) && (flag = "3", num = 2);
        str == "重启" && (status != 2) && (flag = "4", num = 2);
        str == "维护" && (typestatus == 0) && (flag = "2", num = 1);
        str == "结束维护" && (typestatus == 2) && (flag = "0", num = 1);
        str == "删除" && (num = 3);
        str == "镜像同步" && (num = 4);

        data.flag = flag;

        if (num == 0 && flag != "") {//锁定或者取消锁定
            this.operaHostRequest("/host/lock/" + host_id, data);
        } else if (num == 1 && flag != "") {
            this.operaHostRequest("/host/maintain/" + host_id, data);
        } else if (num == 2 && flag != "") {//开机 强制关机 关机 强制重启 重启
            data.host_id = host_id;
            //console.log(data);
            this.operaHostRequest("/host/operate", data);
        } else if (num == 3) {
            this.operaHostRequest("/host/delete", {"host_id": host_id});
        } else if (num == 4) {
            this.addImageList = [];
            this.localImageList = [];
            this.remoteImageList = [];
            $(".searchImage").val("");
            SyncFun.oldtaskTimearr.length = 0;
            SyncFun.hostid = host_id;
            $("#getImage-table").html("");
            $("#newtasktable").html("");
            $(".list-group").slideUp();
            $(".list-group").html("");
            $("#oldtasktimeList").html("");
            this.syncImage(host_id);
        } else {
            showMessage("不能进行此操作", "danger", 500);
        }

    },
    remoteImageList: [],//远端的镜像但是本地没有
    localImageList: [],//本地需要更新的镜像
    addImageList: [],//需要添加新的远端镜像到本地
    syncImage: function (host_id)//获取需要更新的镜像信息
    {
        var that = this;
        $.ajax({
            url: "/image_sync/host_list2/" + host_id,
            type: "get",
            dataType: "json",
            beforeSend: function () {
                $(".warn-text-title").text("正在比对镜像版本,可能需要1-2分钟请耐心等候...");
                $("#loading").css("display", "block");
            },
            success: function (res) {
                $("#loading").css("display", "none");
                $(".warn-text-title").text("正在处理,请耐心等候...");
                if (res.code != 0) {
                    res.msg != null ? showMessage(res.msg, "danger", 2000) : showMessage("请求失败,请重试", "danger", 2000);
                } else {
                    var localList = res.data.local_image_data,
                        remoteList = res.data.remote_image_data,
                        html = "";
                    for (var i = 0, tmp; tmp = localList[i++];) {
                        if (tmp.check_data === "1") {
                            html += "<tr> <td><input type='checkbox' name='getsel' value=" + tmp.image_info.name + "(" + tmp.image_info.id + ")></td>";
                            html += "<td>" + tmp.image_info.displayname + "</td>";
                            html += "<td>" + tmp.image_info.system + "</td>";
                            html += "<td>" + tmp.image_info.description + "</td>";
                            html += "</tr>";
                            that.localImageList.push({
                                "displayname": tmp.image_info.displayname,
                                "name": tmp.image_info.name,
                                "actual_size_mb": tmp.image_info.actual_size_mb,
                                "system": tmp.image_info.system,
                                "description": tmp.image_info.description,
                                "id": tmp.image_info.id,
                                "task_info": tmp.task_info
                            });
                        }
                    }
                    for (var i = 0, item; item = remoteList[i++];) {
                        that.remoteImageList.push({
                            "displayname": item.displayname,
                            "name": item.name,
                            "actual_size_mb": item.actual_size_mb,
                            "system": item.system,
                            "description": item.description,
                            "id": item.id
                        });
                    }

                    if (html === "") {
                        html += '<tr class="noneImage"><td colspan="4">本地镜像无需更新,如需添加新镜像请搜索添加！！！</td></tr>';
                    };
                    $("#getImage-table").html(html);
                    if (that.localImageList.length > 0) {
                        $("#getImageModal").modal({backdrop: 'static', keyboard: false})
                    } else {
                        if (that.remoteImageList.length > 0) {
                            $("#getImageModal").modal({backdrop: 'static', keyboard: false})
                            $(".addImageBox").css("display", "blcok");
                        } else {
                            $(".addImageBox").css("display", "none");
                            showMessage("镜像已经是最新的了！", "warning", 2000);
                        }
                    }
                }
            },
            error: function () {
                showMessage("获取信息失败,请重试", "danger", 2000);
            }
        });
    },
    //批量开机 强制关机 关机 强制重启 重启数据初始化
    batchOperaInfoInit: function (flagId, id) {
        var arr = $('#host_list').bootstrapTable('getSelections');
        var html = "";

        if (arr.length == 0) {
            showMessage("没有选中的Host,请重新选择", "danger", 1000);
        } else if (arr.length == 1) {
            var host_id = arr[0].host_id;
            flagId == 0 && $(id).html("<tr> <td>" + arr[0].displayname + "</td> <td>" + arr[0].ipaddress + "</td> <td>" + arr[0].hostpool + "</td> <td>" + arr[0].datacenter + "</td> </tr>");
            (flagId == 1 || flagId == 3 || flagId == 5) && $(id).html("<tr> <td>" + arr[0].displayname + "</td> <td>" + arr[0].ipaddress + "</td> <td>" + arr[0].instance_nums + "</td> <td>" + arr[0].hostpool + "</td><td>" + arr[0].datacenter + "</td> </tr>")
        } else if (arr.length > 8) {
            (flagId == 0 || flagId == 1 || flagId == 3) && $(id).html("<tr><td colspan='5'>您所选数据超过操作数量，请重新选择！</td></tr>");
            showMessage("最多只能批量操作8条数据", "warning", 1000);
        } else {
            for (var i = 0; i < arr.length; i++) {
                flagId == 0 && (html += "<tr> <td>" + arr[i].displayname + "</td> <td>" + arr[i].ipaddress + "</td> <td>" + arr[i].hostpool + "</td> <td>" + arr[i].datacenter + "</td> </tr>");
                (flagId == 1 || flagId == 3 || flagId == 5) && (html += "<tr> <td>" + arr[i].displayname + "</td> <td>" + arr[i].ipaddress + "</td> <td>" + arr[i].instance_nums + "</td> <td>" + arr[i].hostpool + "</td><td>" + arr[i].datacenter + "</td> </tr>")
            }
            $(id).html(html);
        }
    },

    //批量关机、重启中的checkbox筛选操作
    checkOne: function (thisOne, id1, id2) {
        $(thisOne).attr("value") == "option2" && ($(id1)[2].style.display = "inline-block") && $(id2).attr("disabled", true);
        $(thisOne).attr("value") == "option1" && (($(id1)[2].style.display = "none") && $(id1 + " input[type='checkbox']").prop("checked", false)) && $(id2).attr("disabled", false);
    },
    checkTwo: function (thisTwo, id) {
        if ($(thisTwo).prop("checked")) {
            $(id).attr("disabled", false)
        } else {
            ($(id).attr("disabled", true));
        }
    },

    //批量开机 强制关机 关机 强制重启 重启
    batchOpera: function (flag, id) {
        var host_id = "";
        var arr = [], data = {};
        var list = $('#host_list').bootstrapTable('getSelections');

        $.each(list, function (index, tmp) {
            arr.push(tmp.host_id);
        });
        host_id = arr.join(",");
        data.host_id = host_id;
        data.flag = flag;
        createHostInfo.operaHostRequest("/host/operate", data);
        $(id).modal("hide");
    },


    //内存减
    minusMemory: function (classname) {
        var num = parseInt($(classname).val());
        num -= 1;
        if (num < 0) {
            return;
        }
        $(classname).val(num);
    },
    //内存加
    plusMemroy: function (classname) {
        var num = parseInt($(classname).val());
        num += 1;
        if (num >= 1000) {
            return;
        }
        $(classname).val(num);
    },
// 连动搜索
    //机房初始化下拉框
    addHostSelect: function () {
        var infoList = this;
        $('#addHostModal input:not(".memoryInfo")').val('');
         $('.memoryInfo').val(12);
        $.ajax({
            url: '/hostpool/levelinfo',
            type: 'get',
            dataType: 'json',
            timeout: 5000,
            success: function (result) {
                if (result.code != 0) {
                     result.msg != null ? showMessage(result.msg, "danger", 1000) : showMessage("获取信息失败", "danger", 1000);
                    return;
                }
                var list = result.data;
                $('.searchNetArea option').not(":first").remove();
                $('#new_hostpool_id option').not(":first").remove();


                var html = '<option value="-1">请选择Host所在机房</option>';
                var arr = [], dactype_arr = [], dctypetodatacenter = [], datacentertonetarea_list = [],
                    datacentertonetarea = {},
                    data_list = {}, netareatohostpool = [];


                $.each(list, function (index, tmp) {
                    environments = allEnvArr;
                    dactype_arr.push(tmp.dc_type);
                    if (!dctypetodatacenter[tmp.dc_type]) {
                        dctypetodatacenter[tmp.dc_type] = [tmp.datacenter];
                    } else {
                        dctypetodatacenter[tmp.dc_type].push(tmp.datacenter);
                    }

                    if (!datacentertonetarea[tmp.datacenter + "-" + environments[tmp.dc_type]]) {
                        datacentertonetarea[tmp.datacenter + "-" + environments[tmp.dc_type]] = [tmp.net_area];
                    } else {
                        datacentertonetarea[tmp.datacenter + "-" + environments[tmp.dc_type]].push(tmp.net_area);
                    }

                    if (!netareatohostpool[tmp.datacenter + "-" + environments[tmp.dc_type] + "to" + tmp.net_area]) {
                        netareatohostpool[tmp.datacenter + "-" + environments[tmp.dc_type] + "to" + tmp.net_area] = [[tmp.hostpool, tmp.hostpool_id]];
                    } else {
                        netareatohostpool[tmp.datacenter + "-" + environments[tmp.dc_type] + "to" + tmp.net_area].push([tmp.hostpool, tmp.hostpool_id]);
                    }
                    arr.push(tmp.datacenter + '-' + environments[tmp.dc_type]);
                });

                dctypetodatacenter = dctypetodatacenter.map(function (item, index, array) {
                    return item.unique().sort(function (a, b) {
                        return a - b;
                    });
                });

                for (var i in datacentertonetarea) {
                    datacentertonetarea[i] = datacentertonetarea[i].unique().sort(function (a, b) {
                        return a - b;
                    });
                    datacentertonetarea_list[i] = datacentertonetarea[i];
                }

                arr = arr.unique();

                data_list.arr = arr;
                data_list.dctypetodatacenter = dctypetodatacenter;
                data_list.datacentertonetarea = datacentertonetarea;
                data_list.netareatohostpool = netareatohostpool;
                infoList.hostInfo = data_list;

                for (var i = 0, a; i < arr.length; i++) {
                    a = i + 1;
                    html += "<option value=" + arr[i].substring(0, arr[i].lastIndexOf('-')) + ">" + arr[i] + "</option>";
                }
                $('.searchHost').html(html);
                $("#addHostModal").modal("show");
            },
            error: function (xhr, textStatus) {
                console.warn('ajax error:', xhr, textStatus);
            }
        })
    },
    //网络区域下拉框
    searchNet: function () {
        var text1 = $('.searchHost').val();
        var name1 = $('.searchHost option:selected').html();
        $('.searchNetArea option').not(":first").remove();
        $('#new_hostpool_id option').not(":first").remove();
        if (text1 == -1) {
            return;
        } else {
            var list = this.hostInfo, html = "";
            var netarea_arr = list.datacentertonetarea[name1];
            $.each(netarea_arr, function (index, tmp) {
                html += "<option value=" + tmp + ">" + tmp + "</option>";
            });
            $('.searchNetArea').append(html);
        }
    },
    //集群下拉框
    searchGroup: function () {
        $('#new_hostpool_id option').not(":first").remove();
        var name1 = $('.searchHost option:selected').html();
        var name2 = $('.searchNetArea').val();
        var name = name1 + "to" + name2;
        var list = this.hostInfo;
        var hostpool_arr = list.netareatohostpool[name], html = "";
        if (name2 == '-1') {
            return
        } else {
            $.each(hostpool_arr, function (index, tmp) {
                html += "<option value=" + tmp[1] + ">" + tmp[0] + "</option>";
            });
            $('#new_hostpool_id').append(html);
        }
    },

    //获取用户输入的ip
    getIpInfo: function (id) {//获取用户输入的ip和管理ip
        var str = '';
        var ipArr = $(id).serializeArray();
        $.each(ipArr, function (index, tmp) {
            str += tmp.value + ".";
        });
        return str.substring(0, str.lastIndexOf('.'));
    },
    //    创建新Host
    create_host: function () {
        var new_hostname = $("#new_hostname").val();
        var new_sn = $("#new_sn").val();
        var new_hostpool_id = $("#new_hostpool_id").val();
        if (new_hostpool_id == -1) {
            showMessage("请选择所属集群", "danger", 1200);
            return;
        }
        var vlan_id = $("#new_vlan_id").val();
        var reg = /^[0-9]*$/;
        var new_hold_mem = $(".memoryInfo").val();
        var new_ipaddress = $("#new_ipaddress").val();
        var new_manage_ip = $("#new_manage_ip").val();
        var patt1 = new RegExp("^(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|[1-9])\\." + "(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|\\d)\\." + "(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|\\d)\\." + "(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|\\d)$");
        var result1 = patt1.test(new_ipaddress);
        var result2 = patt1.test(new_manage_ip);
        if (new_hostname.length > 16) {
            showMessage("主机名称长度不能超过16个字符", "danger", 1200);
            return;
        }
        if (vlan_id< 1 || vlan_id > 4097 || !reg.test(vlan_id)){
            showMessage("输入的VLAN ID格式不正确", "danger", 1200);
            return;
        }
        if (result1 != true || result2 != true) {
            showMessage("请输入正确的ip地址", "danger", 1200);
            return;
        }
        $.ajax({
            url: "/host/" + new_hostpool_id,
            type: "POST",
            dataType: "json",
            data: {
                "name": new_hostname,
                "sn": new_sn,
                "ip_address": new_ipaddress,
                "hold_mem_gb": new_hold_mem,
                "vlan_id": vlan_id,
                "manage_ip": new_manage_ip
            },
            beforeSend: function () {
                $("#loading").css("display", "block");
            },
            success: function (req) {
                $("#loading").css("display", "none");
                if (req.code != 0) {
                    req.msg != null ? showMessage(req.msg, "danger", 100000) : showMessage("操作失败", "danger", 100000);
                    return;
                } else {
                    $("#addHostModal").modal("hide");
                    showMessage("host创建成功", "success", 1200);
                    $("#host_list").bootstrapTable('refresh', {silent: true});
                }
            },
            error: function (xhr, textStatus) {
                console.warn('ajax error:', xhr, textStatus);
            }
        });
    },

    //判断浏览器版本
    myBrowser: function () {
        var userAgent = navigator.userAgent; //取得浏览器的userAgent字符串
        var isOpera = userAgent.indexOf("Opera") > -1;
        var isIE = userAgent.indexOf("compatible") > -1 && userAgent.indexOf("MSIE") > -1 && !isOpera;
        var isIE11 = (userAgent.toLowerCase().indexOf("trident") > -1 && userAgent.indexOf("rv") > -1);
        if (isOpera) {
            return "Opera"
        } //判断是否Opera浏览器
        if (userAgent.indexOf("Firefox") > -1) {
            return "FF";
        } //判断是否Firefox浏览器
        if (userAgent.indexOf("Chrome") > -1) {
            return "Chrome";
        }
        if (userAgent.indexOf("Safari") > -1) {
            return "Safari";
        } //判断是否Safari浏览器
        if (isIE11 || isIE) {
            return "IE";
        } //判断是否IE浏览器
    },


    //表格中的checkbox选中操作
    checkSelect: function () {
        var arr = $('#host_list').bootstrapTable('getSelections');
        console.log(arr);
        //console.log($('#host_list tr').hasClass('selected'));

        if ($('#host_list tr').hasClass('selected')) {
            if (arr.length <= 8) {

                if (!confirmDelete(arr)) {
                    console.info('包含维护状态');
                    //  showMessage("只有运维状态下的机器才能删除","warning",1500);
                    $('#onPower').removeClass('disabled').attr('data-target', '#poweronModal');
                    $('#offPower').removeClass('disabled').attr('data-target', '#shutdownModal');
                    $('#restart').removeClass('disabled').attr('data-target', '#restartModal');
                    if (isContainOtherStatus(arr)) {
                        console.info('包含其他状态！');
                        console.info($('#host-delete-some'));
                        $('#host-delete-some').addClass('disabled');

                        return;
                    }
                    $('#host-delete-some').removeClass('disabled').attr('data-target', '#host-delete-some-modal');
                }

                $('#onPower').removeClass('disabled').attr('data-target', '#poweronModal');
                $('#offPower').removeClass('disabled').attr('data-target', '#shutdownModal');
                $('#restart').removeClass('disabled').attr('data-target', '#restartModal');
                //  $('#host-delete-some').removeClass('disabled').attr('data-target','#host-delete-some-modal');

            } else {
                showMessage("最多只能批量操作8条数据", "warning", 1000);
                $('#onPower').addClass('disabled').attr('data-target', '');
                $('#offPower').addClass('disabled').attr('data-target', '');
                $('#restart').addClass('disabled').attr('data-target', '');
                $('#host-delete-some').addClass('disabled').attr('data-target', '');
            }

        } else {
            $('#onPower').addClass('disabled').attr('data-target', '');
            $('#offPower').addClass('disabled').attr('data-target', '');
            $('#restart').addClass('disabled').attr('data-target', '');
            $('#host-delete-some').addClass('disabled').attr('data-target', '');
        }
    },


};

//物理机删除前校验(只有运维状态下的主机才能被删除)
function confirmDelete(arr) {
    for (var i = 0; i < arr.length; i++) {
        console.info(arr[i].typestatus);
        if (arr[i].typestatus == 2) {
            return false;
        }
    }
    return true;
}

//选中机器中是否包含非维护状态
function isContainOtherStatus(arr) {
    for (var i = 0; i < arr.length; i++) {
        console.info(arr[i].typestatus);
        if (arr[i].typestatus != 2) {
            return true;
        }
    }
    return false;
}


//选择页面中时间区间，刷新监控数据
function refreshChart() {
    $('.btn-outline').on('click', function () {
        var value = $(this).attr("value");
        var ip = sessionStorage.getItem("ip");
        var ipList = JSON.parse(sessionStorage.getItem("ipList"));
        $('#hostMonitor').addClass('monitor_model_overflow');
        refresh_mon(ip, ipList, value, value);

        $('#time_range').modal("hide");
    });

    $('.refresh-chart').on('click', function () {

        var startDate = $("#start_date").val() + ' 00:00:00';
        var endDate = $("#end_date").val() + ' 00:00:00';
        var ip = sessionStorage.getItem("ip");
        var ipList = JSON.parse(sessionStorage.getItem("ipList"));
        $('#hostMonitor').addClass('monitor_model_overflow');
        refresh_mon(ip, ipList, startDate, endDate);
        $('#time_range').modal("hide");
    });
}
