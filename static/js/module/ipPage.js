/**
 * Created by 01377836 on 2018/11/14.
 */
var ipBoxInfo = {
    datacenterToarea: null,
    areaTosegment: null,//存储后台返回的联动查询信息
    //获取id
    ipPara: null,//保存ip段
    getId: function () {
        //net-segment是请选择网段的ID
        return id = $('#net-segment').val();
    },
    //获取当前页面页码
    getPage: function () {
        return page = parseInt($('.pagination').children('.active').children().html());
    },

    // 获取IP地址
    getIpAddress: function (className) {
        return ip_address = $('.' + className + '>span:first-child').html();
    },

    //初始化搜索框
    initSelect: function () {
        $('#net-area').html('<option value="-1">请选择网络区域</option>');
        $('#net-segment').html('<option value="-1">请选择网段</option>');
    },

    //动态生成ip格子的请求交互
    findIpInfo: function (page, id) {
        $.ajax({
            url: "/segment/" + id + "/" + page,
            type: 'get',
            dataType: 'json',
            beforeSend: function () {
                $("#loading").css("display", 'block');
            },
            success: function (result) {
                $("#loading").css("display", 'none');
                if (result.code != 0) {
                    $("#initOrCancel").attr("data-target", "").addClass("disabled");
                    $("#holdOrCancel").attr("data-target", "").addClass("disabled");
                    return;
                }
                //该网段是非法的
                if (result.data.len == 0) {
                    $(".ip-details").html('<h3 class="text-primary">您搜索的网段没有对应的IP！！！</h3>');
                    $("#initOrCancel").attr("data-target", "").addClass("disabled");
                    $("#holdOrCancel").attr("data-target", "").addClass("disabled");
                    return;
                }

                var list = result.data;
                var ips = list.ips;
                var strIp = list.segment.substring(0, list.segment.lastIndexOf('.'));
                var strIpNum = parseInt(strIp.substring(strIp.lastIndexOf('.') + 1)) + parseInt(page - 1);//形如28
                strIp = strIp.substring(0, strIp.lastIndexOf('.') + 1);//形如192.168
                $('.choiceIpAlready').html(
                    "<button class='btn btn-md btn-default segmentNow'>所在网段:" + list.segment + '/' + list.netmask + "</button> <button class='btn btn-md btn-default ipNow'>当前IP段:" + strIp + strIpNum + '.*</button>'
                );
//                  //ip格子
                var html1 = '';
                for (var i = 0, a; i < 254; i++) {
                    //通过不同的状态给每个格子设置不同的颜色
                    a = i + 1;
                    html1 += "<button class='btn ip-box-size btn-default' data_ip_num = " + a + ">" + a + "</button>";
                }
                //分页器
                var html2 = '<li class="page-start"><a href="#">&laquo;</a></li>';
                for (var i = 1; i <= list.pages; i++) {
                    if (i == page) {
                        html2 += "<li class='active'><a href='#'>" + i + "</a></li>";
                    } else {
                        html2 += "<li><a href='#'>" + i + "</a></li>";
                    }
                }
                html2 += '<li class="page-end"><a href=' + list.pages + '>&raquo;</a></li>';
                $(".ip-details").html(html1);
                $('.page-box ul').html(html2);
                //根据状态修改对应ip格子的颜色
                if (ips !== null) {
                    $.each(ips, function (i, tmp) {
                        var str = tmp.ip_address;
                        str = parseInt(str.substring(str.lastIndexOf('.') + 1));
                        if (tmp.status == "0") {
                            $('.ip-details button:nth-child(' + str + ')').addClass('btn-success').removeClass('btn-default');
                        } else if (tmp.status == "1") {
                            $('.ip-details button:nth-child(' + str + ')').addClass('btn-danger').removeClass('btn-default');
                        } else if (tmp.status == "2") {
                            $('.ip-details button:nth-child(' + str + ')').addClass('btn-warning').removeClass('btn-default');
                        }
                    });
                }

                role_id_num = id_arr[0][0];
                if (role_id_num != 3 && role_id_num != null) {//批量操作的权限设置
                    $("#initOrCancel").attr("data-target", "#initIP-modal").removeClass("disabled");
                    $("#holdOrCancel").attr("data-target", "#HoldIpModalIs").removeClass("disabled");
                }

            }
        });
    },
    dcNetSegementInfo: {},
    initHostInfo: function () {//联动查询机房下拉框初始化
        var listInfo = this;
        $.ajax({
            url: '/segment/init',
            dataType: 'json',
            type: 'get',
            beforeSend: function () {
                $("#loading").css("display", 'block');
            },
            success: function (result) {
                $("#loading").css("display", 'none');
                ipBoxInfo.dcNetSegementInfo = result.data
                var datacenterToarea = {}, areaTosegment = {}, arr = allEnvArr;
                $.each(result.data, function (index, tmp) {
                    var name1 = tmp.datacenter + "-" + arr[parseInt(tmp.dc_type)];
                    var name2 = name1 + "|" + tmp.net_area
                    if (!datacenterToarea[name1]) {
                        datacenterToarea[name1] = [tmp.net_area];
                    } else {
                        datacenterToarea[name1].push(tmp.net_area);
                    }
                    if (!areaTosegment[name2]) {
                        areaTosegment[name2] = [[tmp.segment, tmp.id]];
                    } else {
                        areaTosegment[name2].push([tmp.segment, tmp.id]);
                    }
                });

                for (var j in datacenterToarea) {
                    datacenterToarea[j] = datacenterToarea[j].unique().sort(function (a, b) {
                        return a - b;
                    });
                }

                ipBoxInfo.datacenterToarea = datacenterToarea;
                ipBoxInfo.areaTosegment = areaTosegment;

                var html = '<option value="-1">请选择机房</option>';
                for (var index in datacenterToarea) {
                    html += "<option value=" + index + ">" + index + "</option>";
                }

                $('#sel-computer-box').html(html);
                $("#dcSelect").html(html);
                $("#dcSelect2").html(html);
            }
        });
    },
    hostSlelected: function (id1, id2) {
        var html = '', datacenter = $(id1).val();
        $(id2).html('<option value="-1">请选择网络区域</option>');
        var datacenterToarea = ipBoxInfo.datacenterToarea[datacenter];
        if (datacenter != -1) {
            for (var i = 0; i < datacenterToarea.length; i++) {
                var _area = datacenterToarea[i];
                html += "<option value=" + _area + ">" + _area + "</option>";
            }
        }
        $(id2).append(html);
    },
    netAreaSelected: function () {
        $("#vipApply").attr("disabled", true);
        $('#net-segment').html('<option value="-1">请选择网段</option>');
        var html = '', areaTosegment = ipBoxInfo.areaTosegment, net_area = $("#net-area").val(),
            datacenter_name = $("#sel-computer-box").val();
        var areaToip_name = datacenter_name + "|" + net_area;
        if (net_area != -1 && datacenter_name != -1) {
            for (var i = 0; i < areaTosegment[areaToip_name].length; i++) {
                var _segment = areaTosegment[areaToip_name][i]
                html += "<option value=" + _segment[1] + ">" + _segment[0] + "</option>";
            }
        }
        $('#net-segment').append(html);
    },

    singleIp: function (url, type, data, idName) {
        $.ajax({
            url: url,
            type: type,
            dataType: 'json',
            data: data,
            beforeSend: function () {
                $("#loading").css("display", 'block');
            },
            success: function (result) {
                $("#loading").css("display", 'none');
                if (result.code == '0') {
                    showMessage("操作成功", "success", 1000);
                    ipBoxInfo.getId();
                    ipBoxInfo.getPage();
                    ipBoxInfo.findIpInfo(page, id);
                } else {
                    result.msg != null ? showMessage(result.msg, "danger", 1000) : showMessage("操作失败", "danger", 1000);
                }
                $(idName).modal("hide");
            }
        });
    },
    //批量数据模态框信息读取
    ManyIpInfo: function (className, id1, id2) {
        $(className + " input").val("");
        var str = $(".ipNow").html();
        if (str) {
            str = str.substring(str.indexOf(":") + 1, str.lastIndexOf(".") + 1)
            var netArea = $("#net-area option:selected").html();
            this.ipPara = str;
            $(className + " h3:first-child span").html(netArea);
            $(className + " h3:nth-child(2) span").html(str + "*");
            $(id1 + " span").html(str);
            $(id2 + " span").html(str);
        }
        ;
    },
    //判断对象是否为空
    isEmptyObject: function (e) {
        var t;
        for (t in e)
            return !1;
        return !0
    },
    //已使用IP信息展示
    used_info: function (ip_address) {
        $.ajax({
            url: "/ip/info",
            type: "get",
            dataType: "json",
            data: {"ip_address": ip_address},
            beforeSend: function () {
                $("#loading").css("display", 'block');
            },
            success: function (res) {
                $("#loading").css("display", 'none');
                if (res.code != 0) {
                    $('#usedIPModal').modal('hide');
                    res.msg != null ? showMessage(res.msg, "danger", 1000) : showMessage("请求失败,请刷新重试", "danger", 1000);
                } else {
                    $('#usedIPModal').modal('show');
                    var list = res.data;
                    if (!ipBoxInfo.isEmptyObject(list)) {
                        var inputList = $("#usedIpInfo input");
                        if (list.is_vip == "0") {
                            $(".vip-item").css("display", "none");
                            $(".ip-item").css("display", "block");
                        } else if (list.is_vip == "1") {
                            $(".vip-item").css("display", "block");
                            $(".ip-item").css("display", "none");
                        }
                        $.each(list, function (index, tmp) {
                            for (var i = 0; i < inputList.length; i++) {
                                if ($(inputList[i]).attr("name") == index) {
                                    $(inputList[i]).val(tmp);
                                }
                            }
                        });
                    }
                }
            },
            error: function () {
                $('#usedIPModal').modal('hide');
                showMessage("请求失败,请刷新重试", "danger", 1000);
            }
        });
    },

    //批量操作IP功能
    operaSomeIp: function (id1, id2, url, id3, type, operatetype) {
        var num1 = $(id1 + " input").val();
        var num2 = $(id2 + " input").val();
        if (num2 == "" || num1 == "" || num1 <= 0 || num1 >= 255 || num2 <= 0 || num2 >= 255) {
            showMessage("输入IP非法，请重新输入", "danger", 1000);
        } else {
            var begin_ip = this.ipPara + num1;
            var end_ip = this.ipPara + num2;
            var btn_list = $(".ip-details button"), ip_arr_operate = [];
            for (var i = 0, len = btn_list.length; i < len; i++) {
                var item = parseInt($(btn_list[i]).attr('data_ip_num'));
                if (item >= parseInt(num1) && item <= parseInt(num2) && $(btn_list[i]).hasClass(operatetype)) {
                    ip_arr_operate.push(item);
                }
            }
            if (ip_arr_operate.length == 0) {
                showMessage("所选ip全部不符合条件,请重新筛选", "danger", 2000);
                return
            }
            ;

            $.ajax({
                url: url,
                type: type,
                data: {"begin_ip": begin_ip, "end_ip": end_ip},
                dataType: "json",
                beforeSend: function () {
                    $("#loading").css("display", 'block');
                },
                success: function (result) {
                    $("#loading").css("display", 'none');
                    if (result.code != 0 && (result.code != 1)) {
                        result.msg != null ? showMessage(result.msg, "danger", 1000) : showMessage("操作的IP不符合条件", "danger", 1000);
                        return;
                    }
                    if (result.code == 1) {
                        showMessage("部分Ip操作失败", "info", 1000);
                    } else {
                        showMessage("操作成功", "success", 1000);
                    }
                    var id = ipBoxInfo.getId();
                    var page = $(".pagination li.active a").html();
                    ipBoxInfo.findIpInfo(page, id);
                    $(id3).modal("hide");
                }
            });
        }

    },

}

window.onload = function () {

    //联动框信息交互初始化
    ipBoxInfo.initHostInfo();
    //网段添加
    $("#segAdd").click(function () {
        $("#segementAdd").modal('show')
    });
    //联动机房和环境的交互信息
    $("#dcSelect").change(function () {
        $('#netAreaSelect').val('');
        ipBoxInfo.hostSlelected("#dcSelect", "#netAreaSelect");
        if ($("#dcSelect").val() != -1) {
            $(".envType").val($("#dcSelect").val().split("-")[$("#dcSelect").val().split("-").length - 1]);
        } else {
            $(".envType").val('')
        }
    });
    $("#dcSelect2").change(function () {
        $('#netAreaSelect2').val('');
        ipBoxInfo.hostSlelected("#dcSelect2", "#netAreaSelect2");
        if ($("#dcSelect2").val() != -1) {
            $(".envType2").val($("#dcSelect2").val().split("-")[$("#dcSelect2").val().split("-").length - 1]);
        } else {
            $(".envType2").val('')
        }
    });

    //定义checkIP函数
    function checkIp(ip) {
        let reg = new RegExp(
            '^(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|[1-9])\\.' +
            '(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|\\d)\\.' +
            '(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|\\d)\\.' +
            '(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|\\d)$'
        )
        return reg.test(ip)
    }

    //点击提交后，提交给后端的信息

    //网段录入提交动作与后台信息联动
    $("#segSubmit").click(function () {
        var network_segment_match = [];
        var reg = /^[0-9]*$/;
        var dc = $("#dcSelect").val();
        var env_type = allEnvArr.indexOf(dc.split('-')[dc.split('-').length - 1]);
        var net_area_name = $("#netAreaSelect").val();
        var segment = $("#segment").val();
        var netmask = $("#netmask").val();
        var vlan = $("#vlanId").val();
        var gateway = $("#gateway").val();
        var dns1 = $("#dns1").val();
        var dns2 = $("#dns2").val();

        if (dc == '-1') {
            showMessage("请选择机房", "danger", 100);
            return;
        }
        if (net_area_name == '-1') {
            showMessage("请选择网络区域", "danger", 100);
            return;
        }
        if (!checkIp(segment)) {
            showMessage("请输入正确的网段", "danger", 100);
            return;
        }
        if (netmask < 16 || netmask > 28 || !reg.test(netmask)) {
            showMessage("输入的掩码不在16-28范围之内或者格式不正确", "danger", 120);
            return;
        }
        if (vlan < 1 || vlan > 4097 || !reg.test(vlan)) {
            showMessage("输入的VLAN ID格式不正确", "danger", 120);
            return;
        }
        if (!checkIp(gateway)) {
            showMessage("请输入正确的网关地址", "danger", 100);
            return;
        }
        if (!checkIp(dns1)) {
            showMessage("请输入正确的dns1服务器地址", "danger", 100);
            return;
        }
        if (!checkIp(dns2)) {
            showMessage("请输入正确的dns2服务器地址", "danger", 100);
            return;
        }
        // 定义net_area_id
        for (var i = 0, len = ipBoxInfo.dcNetSegementInfo.length, net_area_id = ''; i < len; i++) {
            if (net_area_name == ipBoxInfo.dcNetSegementInfo[i].net_area && env_type == ipBoxInfo.dcNetSegementInfo[i].dc_type) {
                net_area_id = ipBoxInfo.dcNetSegementInfo[i].net_area_id
            }
        }
        //将前端数据push进列表里
        network_segment_match.push({
            net_area_id: net_area_id,
            segment: segment,
            netmask: netmask,
            segment_type: $("#netType").val(),
            vlan: vlan,
            gateway: gateway,
            dns1: dns1,
            dns2: dns2
        })

        // 右边网段录入
        if ($(".envType").val() == "PRD" || $(".envType").val() == "DR") {
            var reg2 = /^[0-9]*$/;
            var dc2 = $("#dcSelect2").val();
            var env_type2 = allEnvArr.indexOf(dc.split('-')[dc.split('-').length - 1]);
            var net_area_name2 = $("#netAreaSelect2").val();
            var segment2 = $("#segment2").val();
            var netmask2 = $("#netmask2").val();
            var vlan2 = $("#vlanId2").val();
            var gateway2 = $("#gateway2").val();
            var dns12 = $("#dns1_2").val();
            var dns22 = $("#dns2_2").val();
            if (dc2 == '-1') {
                showMessage("请选择机房", "danger", 100);
                return;
            }
            if (net_area_name2 == '-1') {
                showMessage("请选择网络区域", "danger", 100);
                return;
            }
            if (!checkIp(segment2)) {
                showMessage("请输入正确的网段", "danger", 100);
                return;
            }
            if (netmask2 < 16 || netmask2 > 28 || !reg2.test(netmask2)) {
                showMessage("输入的掩码不在16-28范围之内或者格式不正确", "danger", 120);
                return;
            }
            if (vlan2 < 1 || vlan2 > 4097 || !reg2.test(vlan2)) {
                showMessage("输入的VLAN ID格式不正确", "danger", 120);
                return;
            }
            if (!checkIp(gateway2)) {
                showMessage("请输入正确的网关地址", "danger", 100);
                return;
            }
            if (!checkIp(dns12)) {
                showMessage("请输入正确的dns1服务器地址", "danger", 100);
                return;
            }
            if (!checkIp(dns22)) {
                showMessage("请输入正确的dns2服务器地址", "danger", 100);
                return;
            }
            for (var i = 0, len = ipBoxInfo.dcNetSegementInfo.length, net_area_id2 = ''; i < len; i++) {
                if (net_area_name2 == ipBoxInfo.dcNetSegementInfo[i].net_area && env_type2 == ipBoxInfo.dcNetSegementInfo[i].dc_type) {
                    net_area_id2 = ipBoxInfo.dcNetSegementInfo[i].net_area_id
                }
            }

            network_segment_match.push(
                {
                    net_area_id: net_area_id2,
                    segment: segment2,
                    netmask: netmask2,
                    segment_type: $("#netType2").val(),
                    vlan: vlan2,
                    gateway: gateway2,
                    dns1: dns12,
                    dns2: dns22
                });
        }


        send_data = {"network_segment_match": network_segment_match};

        console.log(send_data);
        //提交信息给后端
        $.ajax({
            url: '/segment/add',
            type: 'post',
            dataType: 'json',
            contentType: 'application/json; charset=UTF-8',
            data: JSON.stringify(send_data),
            beforeSend: function () {
                console.log("bbbb")
                $("#loading").css("display", 'block');
            },
            success: function (res) {
                console.log("ccccc")
                console.log(res);
                $("#loading").css("display", 'none');
                if (res.code != 0) {
                    console.log("ddd")
                    res.msg != null
                        ? showMessage(res.msg, "danger", 1000)
                        : showMessage("操作失败,请刷新重试", "danger", 1000);
                } else {
                    $("#dcSelect").val('')
                    $("#netAreaSelect").val('')
                    $("#segment").val('')
                    $("#netmask").val('')
                    $("#vlanId").val('')
                    $("#gateway").val('')
                    $("#dns1").val('')
                    $("#dns2").val('')

                    $("#dcSelect2").val('')
                    $("#netAreaSelect2").val('')
                    $("#segment2").val('')
                    $("#netmask2").val('')
                    $("#vlanId2").val('')
                    $("#gateway2").val('')
                    $("#dns1_2").val('')
                    $("#dns2_2").val('')
                    //提交成功后关闭弹窗
                    showMessage("网段录入成功", "success", 1000);
                    $("#segementAdd").modal('hide')
                }
            },
            error: function () {
                console.log("dddddd")
                showMessage("操作失败,请刷新重试", "danger", 1000);
            }
        })
    })


    //机房选中，生成区域下拉框
    $("#sel-computer-box").change(function () {
        ipBoxInfo.initSelect();
        ipBoxInfo.hostSlelected("#sel-computer-box", "#net-area");
        $("#vipApply").attr("disabled", true);
    });
    $("#net-area").change(function () {
        ipBoxInfo.netAreaSelected();
    });
    var $deg = false;
    //查询所在网段下的所有ip
    $("#ipQuery").click(function () {
        var id = ipBoxInfo.getId();
        var pageCurrent = 1;
        if (id == -1) {
            $deg = false;
            showMessage("请选择网段", "danger", 1000);
            return;
        } else {
            $deg = true;
            var page = pageCurrent;
            ipBoxInfo.findIpInfo(page, id);
        }

    })


    //每个ip格子的模态框显示隐藏以及信息展示

    $('.ip-details').on('click', 'button', function () {
        var num = $(this).html();
        var str1 = "网络区域：" + $('#net-area option:selected').html();
        var str2 = $('.ipNow').html();
        var str3 = str2.substring(str2.indexOf(':') + 1, str2.lastIndexOf('.') + 1) + num;
        str2 = "当前IP段：" + str2.substring(str2.indexOf(':') + 1);
        if (role_id_num != 3 && role_id_num != null) {
            if ($(this).hasClass('btn-default')) {
                $('#initIPModal').modal('show');
                $('.initIPModalInfo h3:nth-child(1)').html(str1);
                $('.initIPModalInfo h3:nth-child(2)').html(str2);
                $('.initIPModalInfo h3:nth-child(3)').html("<span>" + str3 + "</span><span>此IP未初始化</span>");
            } else if ($(this).hasClass('btn-success')) {
                $('#unusedIPModal').modal('show');
                $('.unusedIPModalLabel>h3:nth-child(1)').html(str1);
                $('.unusedIPModalLabel>h3:nth-child(2)').html(str2);
                $('.unusedIPModalLabel>h3:nth-child(3)').html("<span>" + str3 + "</span><span>此IP未被使用</span>");
            } else if ($(this).hasClass('btn-danger')) {
                ipBoxInfo.used_info(str3);

            } else if ($(this).hasClass('btn-warning')) {
                $('#holdedIPModal').modal('show');
                $(".holdedIPModalLabel>h3:nth-child(1)").html(str1);
                $(".holdedIPModalLabel>h3:nth-child(2)").html(str2);
                $(".holdedIPModalLabel>h3:nth-child(3)").html("<span>" + str3 + "</span><span>此IP已被保留</span>");
            }
        }

    });

    //分页
    $('.page-box>.pagination').on('click', 'a', function (e) {
        e.preventDefault();
        var page = '';
        var page1 = $(this).html();
        var pageCount = parseInt($(".page-end").children().attr('href'));
        var pageCurrent = ipBoxInfo.getPage();

//        判断页数
        if (page1 == "»") {
            page = pageCurrent + 1;
            if (page > pageCount) {
                return;
            }
        } else if (page1 == '«') {
            page = pageCurrent - 1;
            if (page <= 0) {
                return;
            }
        } else {
            page = parseInt(page1);
        }
        //设置分页器样式
        $(this).parent().addClass('active').siblings('.active').removeClass('active');
        ipBoxInfo.findIpInfo(page, id);
    });


    //IP批量初始化模态框信息初始化
    $("#initOrCancel").click(function () {
        ipBoxInfo.ManyIpInfo(".init-ip", "#init-begin-ip", "#init-end-ip");
    });


    //IP初始化
    $("#initIpmodalBtn").click(function () {
        var ip_address = ipBoxInfo.getIpAddress('ip-init-name');
        var url = "/ip/init/" + ipBoxInfo.getId();
        ipBoxInfo.singleIp(url, "post", {"ip_address": ip_address}, "#initIPModal");
    });

    //IP取消初始化
    $("#init-one-btn").click(function () {
        ipBoxInfo.singleIp("/ip/init/cancel", "DELETE", {"ip_address": ipBoxInfo.getIpAddress('ip-use-name')}, "#unusedIPModal");
    });


    //批量初始化
    $("#init-btn").click(function () {
        var url = "/ip/batch/init/" + ipBoxInfo.getId();
        ipBoxInfo.operaSomeIp("#init-begin-ip", "#init-end-ip", url, "#initIP-modal", "post", "btn-default");
    });

    //批量取消初始化
    $("#cancel-init-btn").click(function () {
        ipBoxInfo.operaSomeIp("#init-begin-ip", "#init-end-ip", "/ip/batch/init/cancel", "#initIP-modal", "delete", "btn-success");
    });


    //IP保留
    $("#retainIp").click(function () {
        ipBoxInfo.singleIp('/ip/hold', "PUT", {"ip_address": ipBoxInfo.getIpAddress('ip-use-name')}, "#unusedIPModal");
    });

    //IP取消保留
    $("#cancelIpHold").click(function () {
        ipBoxInfo.singleIp('/ip/hold/cancel', "PUT", {"ip_address": ipBoxInfo.getIpAddress('ip-hold-name')}, "#holdedIPModal");
    });

    //批量保留模态框信息初始化
    $("#holdOrCancel").click(function () {
        ipBoxInfo.ManyIpInfo(".hold-ip", "#hold-begin-ip", "#hold-end-ip");
    });

    //批量保留操作
    $("#hold-ip-btn").click(function () {
        ipBoxInfo.operaSomeIp("#hold-begin-ip", "#hold-end-ip", "/ip/batch/hold", "#HoldIpModalIs", "put", "btn-success");
    });

    //批量取消保留操作
    $("#cancel-hold-ip-btn").click(function () {
        ipBoxInfo.operaSomeIp("#hold-begin-ip", "#hold-end-ip", "/ip/batch/hold/cancel", "#HoldIpModalIs", "put", "btn-warning");
    });

    (function () {
        $("#net-segment").change(function () {
            var _segmentId = $(this).val();
            if (_segmentId == "-1") {
                $("#vipApply").attr("disabled", true);
            } else {
                $("#vipApply").attr("disabled", false);
            }
        });
        $("#vipApply").click(function () {
            $(".vipItemBox input").val("");
            var env_arr = allEnvArr;
            var _datacenter = $("#sel-computer-box").val();
            var _env = _datacenter.substring(_datacenter.lastIndexOf("-") + 1);
            _datacenter = _datacenter.substring(0, _datacenter.lastIndexOf("-"));
            var _netArea = $("#net-area").val();
            var _netSegment = $("#net-segment option:selected").text();
            $('.vipItemBox input[name=datacenter-vip]').val(_datacenter);
            $('.vipItemBox input[name=envi-vip]').val(_env).attr("data-env-id", env_arr.indexOf(_env));
            $('.vipItemBox input[name=net-area-vip]').val(_netArea);
            $('.vipItemBox input[name=segment-vip]').val(_netSegment);
            $("#vipModalIs").modal("show");
        });
        $("#set-vip-btn").click(function () {
            var _params = {};
            _params.datacenter = $('.vipItemBox input[name=datacenter-vip]').val();
            _params.env = $('.vipItemBox input[name=envi-vip]').val();
            _params.net_area = $('.vipItemBox input[name=net-area-vip]').val();
            _params.segment = $('.vipItemBox input[name=segment-vip]').val();
            _params.opUser = user_id_num;

            _params.cluster_id = $('.vipItemBox input[name=cluster-id]').val();
            //_params.service_id =  $('.vipItemBox input[name=service-id]').val();
            //_params.service_ha =  $('.vipItemBox input[name=service-ha]').val();
            _params.sys_code = $('.vipItemBox input[name=sys-code]').val();

            if (!_params.cluster_id ||
                !_params.sys_code
            ) {
                showMessage("请填写完整信息", "danger", 1000);
                return;
            }
            $.ajax({
                url: '/ip/apply',
                type: "post",
                dataType: "json",
                data: _params,
                beforeSend: function () {
                    $("#loading").css("display", 'block');
                },
                success: function (res) {
                    $("#loading").css("display", 'none');
                    if (res.code != 0) {
                        res.msg != null
                            ? showMessage(res.msg, "danger", 1000)
                            : showMessage("操作失败,请刷新重试", "danger", 1000);
                    } else {
                        $("#vipViewBox").html(res.data.vip);
                        if ($deg) {
                            ipBoxInfo.getId();
                            var page = ipBoxInfo.getPage();
                            $(this).parent().addClass('active').siblings('.active').removeClass('active');
                            ipBoxInfo.findIpInfo(page, id);
                        }
                        $("#vipModalIs").modal("hide");
                        $("#vipView").modal("show");
                    }

                },
                error: function () {
                    showMessage("操作失败,请刷新重试", "danger", 1000);
                }
            });

        });
    })(window);

}