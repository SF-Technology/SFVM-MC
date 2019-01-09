/**
 * Created by 80002473 on 2017/4/6.
 */
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
                // alert(num);
                if (num != -1) {
                    ele.style.display = "inline-block";
                }
                if (num == -1) {
                    ele.style.display = "none";
                }
            });
        } else {
            $(".promission").css("display", "none");
        }
    });
});

//效验用户输入密码是否符合规则
function checkPassword(pwd) {
    var result = false;
    var reg = /(?:(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[~@*()_+{}\:"<>?,./;'=-]+)).{10,}/;
    if (reg.test(pwd))
        result = true;
    return result;
}


function judgeStatus(value, row, index)//状态转化中文
{
    var statu = value;

    var status = "";
    statu == "0" && (status = "创建中");
    statu == "1" && (status = '<i class="fa fa-power-off" style="color: #e4b9b9"></i><span>关机</span>');  // 灰色
    statu == "2" && (status = "关机中");
    statu == "3" && (status = '<i class="fa fa-dot-circle-o text-info"></i><span>运行中</span>'); // 2 绿色
    statu == "4" && (status = "开机中");
    statu == "5" && (status = "挂起");
    statu == "6" && (status = "暂停");
    statu == "7" && (status = "热迁移中");
    statu == "8" && (status = "冷迁移中");
    statu == "9" && (status = "转化中");
    statu == "10" && (status = "克隆中");
    statu == "98" && (status = "其他");
    statu == "99" && (status = '<i class="fa fa-times-circle-o text-danger"></i><span>Unknown</span>');  // 1 红色
    statu == "100" && (status = "创建失败");
    statu == "101" && (status = "克隆备份失败");
    statu == "102" && (status = "克隆创建失败");
    statu == "103" && (status = "被克隆中");
    statu == "104" && (status = "配置中");
    statu == "108" && (status = "MiniArch迁移中");
    statu == "109" && (status = "MiniArch完成");
    statu == "" && (status = "未知");
    return status;
}
var ConfigFun = function () {
};
ConfigFun.c_ips_back = [];// 保存后台返回的IP列表
ConfigFun.net_cart_list = [];// 保存已有网卡信息
ConfigFun.c_surplus_ips = [];// 保存修改后的剩余可用IP列表
ConfigFun.c_use_ips = [];// 保存筛选后可用IP列表
ConfigFun.ele = [];// 保存修改网卡IP的目标元素
ConfigFun.slideBool = false; // 是否触发mousemove事件
ConfigFun.slideLeft = 0; // 是否触发mousemove事件
ConfigFun.ipTypes = []; // 已有网卡的类型
ConfigFun.ipTypeArr = [];//所有网卡类型
ConfigFun.refreshNetCart = function (instance_id, status) {
    $.ajax({
        url: "/instance/configure/init/" + instance_id,
        type: 'get',
        dataType: 'json',
        success: function (res) {
            if (res.code != 0) {
                res.msg != null ? showMessage(res.msg, "danger", 400) : showMessage("获取信息失败,请刷新重试！", "danger", 400);
            } else {
                var netCartList = res.data;
                var net_cart_list = netCartList.c_net;
                ConfigFun.net_cart_list = netCartList.c_net;
                for (var k = 0, html = ""; k < net_cart_list.length; k++) {
                    html = ConfigFun.hasnetCart(
                        k,
                        net_cart_list[k],
                        html,
                        status,
                        netCartList.c_system,
                        netCartList.c_ips,
                        net_cart_list[k].ip_type
                    );
                }
                if (ConfigFun.net_cart_list.length >= 2) {
                    $(".add_cart_btn").attr('disabled', true)
                } else {
                    $(".add_cart_btn").attr('disabled', false)
                }
                $(".cart_body").html(html);
            }
        },
        error: function () {
        }
    })
}
ConfigFun.hasnetCart = function (index, tmp, html, statu_vm, sys, c_ips, ipType) {
    //ipType类型，0为内网，1为外网电信，2为外网联通，3为镜像模板机使用，4为内网NAS网段, -1为没有IP
    var i = parseInt(index) + 1;
    var label1 = "ip" + i;
    var label2 = "radio_a" + i;
    var label3 = "radio_b" + i;
    var str_ip_edit = "";
    html += '<div class="cart_item">';
    html += '   <span>' + i + '</span>';
    switch (ipType) {
        case '-1':
            html += '<span>无</span>';
            break;
        case '0':
            html += '<span>内网</span>';
            break;
        case '1':
            html += '<span>外网电信</span>';
            break;
        case '2':
            html += '<span>外网联通</span>';
            break;
        case '3':
            html += '<span>镜像模板机使用</span>';
            break;
        case '4':
            html += '<span>内网NAS网段</span>';
            break;
    }
    if (!tmp.ip_addr) {
        statu_vm == 1 && (html += '   <span>未分配IP</span>');
        statu_vm == 3 && (html += '   <span data-ip-type = ' + ipType + '><u>未分配IP</u> <i class="fa fa-pencil-square-o icon-large editIp" aria-hidden="true"></i></span>');
    } else {//data-ip-addr 保存初始化的ip_vlan 不会变  data-ipVlan保存为用户修改后的ip-vlan 会随着用户修改而改变
        sys == 'windows' ? (str_ip_edit = "") :
            ((statu_vm == 1 || tmp.nic_status == 0) ? (str_ip_edit += "") :
                (str_ip_edit += '<i class="fa fa-pencil-square-o icon-large editIp" aria-hidden="true"></i> '));
        c_ips.length <= 0
            ? html += '   <span>' + tmp.ip_addr + '</span>'
            : html += '   <span data-ip-type = ' + ipType + '  data-ip-addr=' + tmp.ip_addr + "_" + tmp.vlan + ' data-ipVlan=' + tmp.ip_addr + "_" + tmp.vlan + '>' +
            '<u>' + tmp.ip_addr + '</u>&nbsp;&nbsp' +
            str_ip_edit
            + '</span>'
    }
    html += '   <span>' + tmp.mac_addr + '</span>';
    if (sys != 'windows') {
        if (tmp.nic_status == 0) {
            if (statu_vm == 3) {
                html += '  <span>';
                html += '       <input type="radio" name="cart' + i + '" id=' + label2 + '> <label for=' + label2 + ' class="text-info">连接</label>';
                html += '       <input type="radio" name="cart' + i + '" id=' + label3 + '  checked="checked"> <label for=' + label3 + ' class="text-danger">断开</label>';
                html += '  </span>';
            }
            if (statu_vm == 1) {
                html += '   <span>关机状态不能操作</span>';
            }
        } else if (tmp.nic_status == 1) {
            if (statu_vm == 3) {
                html += '  <span>';
                html += '       <input type="radio" name="cart' + i + '" id=' + label2 + '  checked="checked"> <label for=' + label2 + ' class="text-info">连接</label>';
                html += '       <input type="radio" name="cart' + i + '" id=' + label3 + '> <label for=' + label3 + ' class="text-danger" >断开</label>';
                html += '  </span>';
            }
            ;
            if (statu_vm == 1) {
                html += '   <span>关机状态不能操作</span>';
            }
        } else if (tmp.nic_status == 2) {
            html += '<span class="text-danger">无法确认网卡状态</span>';
        }
    } else {
        html += '<span class="text-danger">windows请手动操作</span>';
    }
    html += '</div>';
    return html;
};
ConfigFun.getnetCartParams = function (list, c_ips, status) {
    var net_status_list = [];
    if (ConfigFun.status == 3) {//运行中才能进行网卡修改
        if (list.length > 0 && c_ips.length > 0 && status == 'linux') {
            for (var i = 0; i < list.length; i++) {
                var tmp = list[i],
                    item_obj = {},
                    index = parseInt(i) + 1,
                //var id1 = "#ip" + index; 分配IP所用
                    id2 = "#radio_a" + index, ip_addr, vlan, ip_addr_new, vlan_new,
                    _ip_addr_old = $($(".cart_item")[i]).children("span:nth-child(3)").attr("data-ip-addr"),
                    _ipVlan = $($(".cart_item")[i]).children("span:nth-child(3)").attr("data-ipVlan");
                _ipType = $($(".cart_item")[i]).children("span:nth-child(3)").attr("data-ip-type");
                if (_ipVlan) {
                    var ipVlan = _ipVlan.split("_");
                    ip_addr_new = ipVlan[0];
                    vlan_new = ipVlan[1];
                } else {
                    ip_addr_new = '';
                    vlan_new = '';
                }
                if (_ip_addr_old) {
                    var ip_addr_old = _ip_addr_old.split("_");
                    ip_addr = ip_addr_old[0];
                    vlan = ip_addr_old[1];
                    (ip_addr == ip_addr_new) && (ip_addr_new = "", vlan_new = "");
                } else {
                    ip_addr = '';
                    vlan = '';
                }

                item_obj.ip_addr = ip_addr;
                item_obj.vlan = vlan;
                item_obj.ip_addr_new = ip_addr_new;
                item_obj.vlan_new = vlan_new;
                item_obj.mac_addr = tmp.mac_addr;
                item_obj.ip_type = _ipType;

                if (tmp.nic_status == 0 || tmp.nic_status == 1) {
                    var statu = $(id2).parent().children("input:checked").next().text();
                    statu == "连接" && (item_obj.nic_status = 1);
                    statu == "断开" && (item_obj.nic_status = 0);
                } else {
                    item_obj.nic_status = "";
                }

                net_status_list.push(item_obj);
            }
        } else {
            net_status_list = []
        }
    }
    return net_status_list;
};
// 获取除本身以外已选IP类型
ConfigFun.filterIpType = function (type) {
    ConfigFun.ipTypes.length = 0;
    $(".cart_item").children("span:nth-child(3)").each(function (index, ele) {
        var ipTypeUsed = $(ele).attr("data-ip-type");
        if (type == '-1' || ipTypeUsed != type) {
            ConfigFun.ipTypes.push(ipTypeUsed)
        }
    });
    if (ConfigFun.ipTypes.indexOf('-1') >= 0) {
        ConfigFun.ipTypes.splice(ConfigFun.ipTypes.indexOf('-1'), 1)
    }
    switch (type) {
        case '-1':
            ConfigFun.ipTypeArr = [
                {key: 0, value: '内网'},
                {key: 1, value: '外网电信'},
                {key: 2, value: '外网联通'},
                {key: 3, value: '镜像模板机使用'},
                {key: 4, value: '内网NAS网段'}
            ];
            for (var j = 0; j < ConfigFun.ipTypes.length; j++) {
                if (ConfigFun.ipTypes[j]) {
                    ConfigFun.ipTypeArr.splice(parseInt(ConfigFun.ipTypes[j]), 1);
                }
            }
            break;
        case '0':
        case '4':
            ConfigFun.ipTypeArr = [
                {key: 0, value: '内网'}, , , ,
                {key: 4, value: '内网NAS网段'}
            ];
            for (var j = 0; j < ConfigFun.ipTypes.length; j++) {
                if (ConfigFun.ipTypes[j] && (ConfigFun.ipTypes[j] != type)) {
                    ConfigFun.ipTypeArr.splice(parseInt(ConfigFun.ipTypes[j]), 1);
                }
            }
            break;
        case '1':
            ConfigFun.ipTypeArr = [{key: 1, value: '外网电信'}];
            break;
        case '2':
            ConfigFun.ipTypeArr = [{key: 2, value: '外网联通'}];
            break;
        case '3':
            ConfigFun.ipTypeArr = [{key: 3, value: '镜像模板机使用'}];
            break;
    }
}
// 过滤可选IP
ConfigFun.filterIp = function (defaultIpType) {
    ConfigFun.c_use_ips.length = 0;
    for (var i = 0; i < ConfigFun.c_surplus_ips.length; i++) {
        if (
            ConfigFun.ipTypes.indexOf(defaultIpType) < 0 &&
            ConfigFun.c_surplus_ips[i].ip_type == defaultIpType
        ) {
            ConfigFun.c_use_ips.push(ConfigFun.c_surplus_ips[i])
        }
    }
}
// 过滤指定类型的IP
ConfigFun.filterAssignIp = function (ipType) {
    let ipList = ConfigFun.c_use_ips, ipArr = [];
    ipArr = ipList.filter(function (item, index) {
        return item.ip_type == ipType;
    })
    return ipArr;
}
// 过滤有主网的网卡不能修改IP类型
ConfigFun.filterNicType = function () {
    var oldIpStr = $(ConfigFun.ele).parent().attr('data-ip-addr'), nic_type_obj = {};
    if (oldIpStr) {
        var oldIp = oldIpStr.split('_')[0];
        for (var i = 0; i < ConfigFun.net_cart_list.length; i++) {
            if (oldIp == ConfigFun.net_cart_list[i].ip_addr) {
                nic_type_obj.nic_type = ConfigFun.net_cart_list[i].nic_type
                nic_type_obj.ip_type = ConfigFun.net_cart_list[i].ip_type
            }
        }
    }
    return nic_type_obj
}
// 渲染修改IP地址的option列表
ConfigFun.createOption = function (c_ips_back) {
    let html = '';
    for (let i = 0; i < c_ips_back.length; i++) {
        html += '<option value="' + c_ips_back[i].value + '_' + c_ips_back[i].vlan + '">' + c_ips_back[i].value + '</option>';
    }
    return html;
};
// 扩容
ConfigFun.vmInfo = {}; // 保存vmip vm id
ConfigFun.mountPointList = []; // 保存挂载点信息
ConfigFun.mountPointNameArr = []; //保存挂载点名称
ConfigFun.qemu_ga_update = false;
// 生成磁盘挂载点列表
ConfigFun.dilatateFun = function (data) {
    var list = data.mount_point_list, html = "", mount_point_arr = [];
    //console.log(data);
    //console.log(ConfigFun.c_system);
    ConfigFun.mountPointNameArr.length = 0;
    for (var i = 0, len = list.length; i < len; i++) {
        ConfigFun.mountPointNameArr.push(list[i].mount_point);
        mount_point_arr.push('<ul>');
        if (list[i].mount_point == '/') {
            mount_point_arr.push("<li data-value='/'>/</li>")
        } else {
            mount_point_arr.push("<li data-value=" + list[i].mount_point + ">" + list[i].mount_point + "</li>")
        }
        mount_point_arr.push("<li>" + list[i].mount_point_size + "G</li>")
        mount_point_arr.push("<li>" + list[i].mount_point_use + "</li>")

        if (parseInt(list[i].mount_point_size) >= 1025) {
            mount_point_arr.push('<li   title="磁盘容量已达上限" class="mountExtendSize" data-mount-point-size=' + list[i].mount_point_size + ' data-index=' + i + '>' +
                '<input class="ex1"  data-slider-id="ex1Slider"  type="text" data-slider-min=' + list[i].mount_point_size + ' ' +
                'data-slider-max="1024" data-slider-step="1" data-slider-enabled=false data-slider-value="0"></li>')
        } else {
            var ticks = [], ticksNum = parseInt(list[i].mount_point_size), enabled = true;
            ConfigFun.c_system == 'linux' && (enabled = true);
            ConfigFun.c_system == 'windows' && (enabled = false);
            ticks.push(ticksNum, 1024); // 可扩容范围
            mount_point_arr.push('<li class="mountExtendSize" data-mount-point-size=' + list[i].mount_point_size + ' data-index=' + i + '>' +
                '<input class="ex1"  data-slider-id="ex1Slider"  type="text" data-slider-min=' + list[i].mount_point_size + ' ' +
                'data-slider-max="1024" slider-ticks-snap-bounds="100" data-slider-ticks=' + JSON.stringify(ticks) + ' data-slider-ticks-labels=' + JSON.stringify(ticks) + ' data-slider-step="1" data-slider-enabled=' + enabled + ' data-slider-value="0"></li>')
        }
        mount_point_arr.push('</ul>')
    }
    $(".mountPointSize").val("")
    $(".diskMountPoint").val("")
    ConfigFun.c_system == 'linux' && $(".diskOrPoint").html('新增挂载点');
    ConfigFun.c_system == 'windows' && $(".diskOrPoint").html('新增磁盘');
    if (list.length < 20) {
        $(".addNewMount").css("display", 'block');
        $(".addNewBtn").css("display", 'block');
        $(".addMountPointBox").css("display", 'none');
    } else {
        $(".addNewMount").css("display", 'none');
    }

    return mount_point_arr.join("");
};
// 获取需要扩容的挂载点信息
ConfigFun.getMountedPointParams = function () {
    var list = $(".mountExtendSize"), newMountPointList = [];
    for (var j = 0, len = list.length; j < len; j++) {
        var index = parseInt($(list[j]).attr('data-index')),
            mountPointSize = parseFloat($(list[j]).attr('data-mount-point-size')),
            newNum = parseFloat($(list[j]).children(".ex1").slider("getValue")),
            marginNum = newNum - mountPointSize;
        //console.log(marginNum)
        if (parseInt(marginNum) > 0) {
            ConfigFun.mountPointList[index].mount_extend_size = marginNum;
            newMountPointList.push(ConfigFun.mountPointList[index]);
        }
    }
    if (!ConfigFun.getNewMountpoint()) {
        return newMountPointList;
    } else {
        newMountPointList.push(ConfigFun.getNewMountpoint());
        return newMountPointList;
    }
}
// 校验挂载点目录名称规则
ConfigFun.checkMountPoint = function (mountPoint) {
    var result = false;
    var reg = /^(?!_)[a-zA-Z0-9_]+$/;
    if (reg.test(mountPoint)) {
        result = true;
    }
    return result;
}

// 获取新增盘信息
ConfigFun.getNewMountpoint = function () {
    var mountPointArr = {
            'mount_partition_name': "",
            'mount_partition_type': "",
            'mount_point_size': '',
            'mount_point_use': "",
            'mount_point': "",
            "mount_extend_size": 0
        },
        mount_point = $('.diskMountPoint').val(),
        mount_extend_size = $('.mountPointSize').val();
    if (ConfigFun.c_system == 'linux') {
        if (!mount_point) {
            mountPointArr.mount_point = ''
        } else {
            mountPointArr.mount_point = '/' + mount_point;
        }
    }
    mountPointArr.mount_extend_size = mount_extend_size;
    if (!mount_point && !mount_extend_size) mountPointArr = "";
    return mountPointArr;
}


function DoOnMsoNumberFormat(cell, row, col) {
    var result = "";
    if (row > 0 && col == 0)
        result = "\\@";
    return result;
}


var CloneFun = function () {
};

CloneFun.flover_list = {};
CloneFun.mem_arr = function () {
    var id_arr = [];
    var div_list = $(".mem-reset");
    for (var i = 0, len = div_list.length; i < len; i++) {
        id_arr.push(parseInt($(div_list[i]).attr("data-id")));
    }
    return id_arr;
};
var length_export;
function inittable() {
    $('#myTable').bootstrapTable({
        url: '/instance/list', // 接口 URL 地址
        method: 'get',
        dataType: "json",
        uniqueId: "id", //删除时能用到 removeByUniqueId
        showExport: true,//显示导出按钮
        exportDataType: "all",//导出类型
        exportTypes: ['all'],  //导出文件类型
        exportOptions: {
            ignoreColumn: [0, 10],  //忽略某一列的索引
            fileName: '虚拟机信息',  //文件名称设置
            worksheetName: 'sheet1',  //表格工作区名称
            tableName: '虚拟机详情',
            //excelstyles: ['background-color', 'color', 'font-size', 'font-weight'],
            onMsoNumberFormat: DoOnMsoNumberFormat
        },
        queryParamsType: "search",
        detailView: false,
        showRefresh: true,
        contentType: "application/x-www-form-urlencoded",
        pagination: true,
        //maintainSelected: true,
        pageList: [10, 20, 50, 100, "all"],
        pageSize: 10,
        pageNumber: 1,
        //search: true, //不显示全表模糊搜索框
        showColumns: true, //不显示下拉框（选择显示的列）
        sidePagination: "server", //服务端请求
        checkboxHeader: true,
        clickToSelect: false,
        singleSelect: false,
        //sortable: true, //是否启用排序 sortOrder: "ID asc", //排序方式
        //sortOrder: "ip_address desc", //排序方式
        //maintainSelected: true,
        onBeforeLoadParams: {}, //查询参数设置，供导出使用，在search_form.js里赋值
        //toolbar: '#mybar',
        sortable: false,
        responseHandler: function (res) {
            tableOpera.export_data = res.data.rows;
            if (res.code == 0) {
                return res.data;
            } else {
                return {rows: [], total: 0};
            }
        },
        queryParams: function (q) {
            var searchContent = q.searchText;
            var key = '';
//                key = isIP(searchContent) ? JSON.stringify({'ip': searchContent}) : JSON.stringify({'name': searchContent})
            return {
                //"sortName" : q.sortName,
                //"sortOrder" : q.sortOrder,
                "page_size": q.pageSize,
                "page_no": q.pageNumber,
                "search": JSON.stringify(tableOpera.searchData)
            };
        },
        onLoadSuccess: function (data) {
            rowCount = data.length - 1;
            $("#myTable").bootstrapTable('hideRow', {index: rowCount});
            $("#myTable td").attr("data-tableexport-msonumberformat", "\@");
            $("#myTable tr").attr("data-tableexport-display", "always");


            list_timer = data.rows;
            length_export = list_timer.length;
            if (list_timer.length == 0 && this.pageNumber > 1) {
                $("#myTable").bootstrapTable("selectPage", this.pageNumber);
                return;
            }
            //表格中的操作限制
            tableOperaShow(list_timer);

            //定时刷新列表查询是否有创建中 开机中 迁移中等状态

            if (typeof timer != "undefined") {
                clearTimeout(timer);
            }
            tableOpera.interval_fun(list_timer);


        },
        onPageChange: function (number, size) {  //表格翻页事件
            $("#myTable").bootstrapTable('hideRow', {index: rowCount});
            $("#myTable td").attr("data-tableexport-msonumberformat", "\@");
            $("#myTable tr").attr("data-tableexport-display", "always");

        },
        onClickCell: function (field, value, row, $element) {
            tableOpera.instance_ids = [];
            tableOpera.instance_ids[0] = row.instance_id;
            tableOpera.rowInfo = row;

            //限制只有关机状态下的vm 才能删除

            if (row.status == "1" || row.status == "99" || row.status == "100" || row.status == "101" || row.status == "102") {
                $(".removeVmSure").attr("data-target", "#vm-delete-modal");
            } else {
                $(".removeVmSure").attr("data-target", "");
            }

            //限制只有关机状态下的vm才能迁移 migrateVmSure
            if (row.status != "1") {
                $(".migrateVmSure").attr("data-target", "");
            }

            //限制只有关机状态下的vm才能克隆
            if (row.status != "1") {
                $(".cloneVm").attr("data-target", "");
            }

            //vm详情页面跳转
            if (field == "displayname") {
                //console.log(row.name,row.displayname);
                tableOpera.vmDetails(row.instance_id);
            }
        },
        onCheck: function () {
            if (tableOpera.myBrowser() == "IE") {
                tableOpera.checkSelect();
            }
            clearTimeout(timer);
            tableOpera.interval_fun(list_timer);

        },
        onCheckAll: function () {
            clearTimeout(timer);
            tableOpera.interval_fun(list_timer);
        },
        onUncheckAll: function () {
            clearTimeout(timer);
            tableOpera.interval_fun(list_timer);
        },
        onUncheck: function () {
            if (tableOpera.myBrowser() == "IE") {
                tableOpera.checkSelect();
            }
            clearTimeout(timer);
            tableOpera.interval_fun(list_timer);
        },
        columns: [{ // 列设置
            field: 'state',
            checkbox: true, // 使用复选框
            align: "left",
            valign: "middle"
        }, {
            title: "主机名",
            field: "displayname",
            class: "click",
            align: "left",
            valign: "middle",
        },
            {
                title: "UUID",
                field: "uuid",
                align: "left",
                valign: "middle",
            },
            {
                title: "IP地址",
                field: "ip_address",
                align: "left",
                valign: "middle"
            },
            {
                title: "HOST IP",
                field: "host_ip",
                align: "left",
                valign: "middle",
                formatter: function (value, row, index) {
                    for (var i = 0; i < id_arr.length; i++) {
                        if (id_arr[i][0] == 1 && id_arr[i][1] == row.group_id) {
                            return row.host_ip
                        }
                    }
                }
            },
            {
                title: "状态",
                field: "status",
                align: "left",
                valign: "middle",
                formatter: judgeStatus
            }, {
                title: "应用管理员",
                field: "owner",
                align: "left",
                valign: "middle",
            }, {
                title: "所属应用组",
                field: "app_group",
                align: "left",
                valign: "middle",
            }, {
                title: "应用系统信息",
                field: "app_info",
                align: "left",
                valign: "middle",
            }, {
                title: "所属集群",
                field: "hostpool",
                align: "left",
                valign: "middle",
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
                title: "操作",
                align: "left",
                valign: "middle",
                events: window.operateVmEvents,
                formatter: function (value, row, index) {
                    var arr = [-100, 9];
                    var statu = row.status;
                    statu == "" && (statu = -100);
                    if (arr.indexOf(parseInt(statu)) == -1) {
                        for (var i = 0; i < id_arr.length; i++) {
                            if (id_arr[i][0] == 2 && id_arr[i][1] == row.group_id) {
                                return ['<a  class="seeInfo" data-toggle="modal" data-target="#hostMonitor" id="monitorPage" title="监控"><i class="fa fa-signal text-primary"></i></a>&nbsp;',
                                    tableOpera.selHtml(row)].join("");
                            } else if (id_arr[i][0] == 3 && id_arr[i][1] == row.group_id) {
                                return "";
                            } else if (id_arr[i][0] == 1 && id_arr[i][1] == row.group_id) {
                                return ['<a  class="seeInfo" data-toggle="modal" data-target="#hostMonitor" id="monitorPage" title="监控"><i class="fa fa-signal text-primary"></i></a>&nbsp;',
                                    tableOpera.selHtml(row)].join("");
                            }
                        }
                    } else {
                        return "--";
                    }
                }
            },

        ]
    });
}
var tipKey = 0;//文字轮播初始值
function startScroll() {
    tipKey--;
    if (tipKey <= -585) {
        tipKey = 585;
        document.getElementById('tipText').style.right = -585 + 'px';
    } else {
        document.getElementById('tipText').style.left = tipKey + 'px';
    }
    setTimeout(startScroll, 30);
}

window.onload = function () {

    setTimeout(startScroll, 1000);
    // 获取列表
    inittable();
    $('#myTable').bootstrapTable('hideColumn', 'uuid');
    $('#myTable').bootstrapTable('hideColumn', 'host_ip');
    $('#myTable').bootstrapTable('hideColumn', 'hostpool');
    refreshChart();
    // 显示搜索框
    $(".searchShow").click(function(e){
        e.preventDefault()
        $(".searchContent").slideDown();
    })
    // $(".queryBox").mouseleave(function(){
    //    $(".searchContent").slideUp()
    //})
    $(".searchTrigger").click(function(){
         $('#myTable').bootstrapTable('refresh', {silent: true});
    })
    //清除筛选
    $(".searchClear").click(function(){
        tableOpera.searchData = {}
         $("#vm_name_input").val('')
         $("#vm_name_input").val('')
         $("#vm_uuid_input").val('')
         $("#vm_group_input").val('')
         $("#vm_statu_input").val('-1')
         $("#vm_admin_input").val('')
         $("#host_ip_input").val('')
         $("#vm_ip_input").val('')
         $(".searchShow").html('请输入查询数据')
         $(".searchContent").slideUp()
         $('#myTable').bootstrapTable('refresh', {silent: true});
    })
    $("#clearSearch").click(function(){
        tableOpera.searchData = {}
        $("#vm_name_input").val('')
         $("#vm_name_input").val('')
         $("#vm_uuid_input").val('')
         document.getElementsByName("chooseRadio")[0].checked = true;
         $("#vm_group_input").val('')
         $("#vm_statu_input").val('-1')
         $("#vm_admin_input").val('')
         $("#host_ip_input").val('')
         $("#vm_ip_input").val('')
         $(".searchShow").html('请输入查询数据')
         $('#myTable').bootstrapTable('refresh', {silent: true});
    })
    // 筛选虚拟机
    $("#searchSubmit").click(function(){
        tableOpera.searchData = {}
        tableOpera.searchTextObj = ''
        if($("#vm_name_input").val()!=''){
            tableOpera.searchData.name = $("#vm_name_input").val()
            tableOpera.searchTextObj+=`<span>名称: </span>${$("#vm_name_input").val()}; `
        }
        if($("#vm_uuid_input").val()!=''){
             tableOpera.searchData.uuid = $("#vm_uuid_input").val()
            tableOpera.searchTextObj+=`<span>UUID: </span>${$("#vm_uuid_input").val()}; `
        }
        if($("#vm_group_input").val()!=''){
              tableOpera.searchData.group_name = $("#vm_group_input").val()
             tableOpera.searchTextObj+=`<span>应用组名: </span>${$("#vm_group_input").val()}; `
        }
         if($("#vm_statu_input").val()!='-1'){
               tableOpera.searchData.status = $("#vm_statu_input").val()
             tableOpera.searchTextObj+=`<span>状态: </span>${$("#vm_statu_input option:selected").text()}; `
        }
        if ($("#vm_admin_input").val() != '') {
            tableOpera.searchData.owner = $("#vm_admin_input").val()
             tableOpera.searchTextObj+=`<span>应用组名: </span>${$("#vm_admin_input").val()}; `
        }

        if ($("#host_ip_input").val()!='') {
            tableOpera.searchData.host_ip = $("#host_ip_input").val()
            tableOpera.searchTextObj+=`<span>物理机IP: </span>${$("#host_ip_input").val()}; `
        }


        if ($("#vm_ip_input").val()!='') {
            tableOpera.searchData.ip_address = $("#vm_ip_input").val()
            tableOpera.searchTextObj+=`<span>IP地址: </span>${$("#vm_ip_input").val()}; `

            var searchType = $('.seacrh_type input[name="chooseRadio"]:checked ').val();
            var changeType = "";
            if(searchType == 1){
                changeType = '模糊查询';
                tableOpera.searchData.ip_search_type = searchType
            }else{
                changeType = '精确查询';
            }
            tableOpera.searchTextObj+=`<span>查询类型: </span>` + changeType;
        }

        console.log(tableOpera.searchTextObj)
        $(".searchShow").html(tableOpera.searchTextObj)
        $(".searchContent").slideUp()
        $('#myTable').bootstrapTable('refresh', {silent: true});
    })

    // 修改系统版本
    $("#vm-details").on("click", '.edit_os', function () {
        $(".new_os").val("");
        $("#edit_os_vm").modal("show");
    })
    $("#check_os").click(function () {
        var os_version = $(".new_os").val();
        var reg = new RegExp("^[0-9.]+$");
        var instance_id = parseInt(tableOpera.vmDetailsId);
        if (!reg.test(os_version)) {
            showMessage('操作系统版本格式不正确', 'danger', 200);
            return false;
        }
        var params = {"os_version": os_version};
        $.ajax({
            url: "/instance/os_version_modify/" + instance_id,
            type: "POST",
            dataType: "json",
            contentType: "application/json; charset=utf-8",
            data: JSON.stringify(params),
            beforeSend: function () {
                $("#loading").css("display", "block");
            },
            success: function (res) {
                $("#loading").css("display", "none");
                if (res.code != 0) {
                    res.msg != null ? showMessage(res.msg, "danger", 2000) : showMessage("操作失败请刷新重试！！！", "danger", 2000)
                } else {
                    showMessage("修改成功", "success", 1000)
                }
                $("#edit_os_vm").modal("hide");
                $(".new_os").val("");
                tableOpera.vmDetails(instance_id);
            },
            error: function () {
                $("#loading").css("display", "none");
                showMessage("操作失败请刷新重试！！！", "danger", 2000);
            }
        });
    });
    // 磁盘扩容
    $(".addNewBtn").click(function () {
        $(this).css('display', "none");
        ConfigFun.c_system == 'linux' && $(".diskMountPoint").css("display", "inline-block").prev().css("display", "inline-block");
        ConfigFun.c_system == 'windows' && $(".diskMountPoint").css("display", "none").prev().css("display", "inline-block");
        $(".addMountPointBox").css('display', "inline-block");
    });
    $('.diskMountPoint').blur(function () {
        if (!ConfigFun.checkMountPoint($(this).val())) {
            showMessage('以数字或者字母开头,包含数字字母_,不能超过20位(大小写敏感,非必填项)', 'danger', 1000);
        }
    });
    $(".getmountPoint").click(function () { // 获取磁盘信息生成挂载点使用情况
        $.ajax({
            url: '/instance/extend/' + ConfigFun.vmInfo.instance_id,
            type: 'get',
            beforeSend: function () {
                $(".mountPointInfoLoad").css("display", "inline-block");
            },
            success: function (res) {
                $(".mountPointInfoLoad").css("display", "none");
                if (res.code != 0) {
                    res.msg != "" ? $(".errorTxt").html(res.msg).css({"display": "inline-block", 'color': '#f00'})
                        : $(".errorTxt").html('无法获取VM磁盘信息').css({"display": "inline-block", 'color': '#f00'})
                } else {
                    var list = res.data;
                    ConfigFun.qemu_ga_update = list.qemu_ga_update;
                    if (!list.qemu_ga_update || list.mount_point_list.length <= 0) {
                        $(".errorTxt").html('此虚拟机无法进行扩容').css({"display": "inline-block", 'color': '#f00'})
                        $("#config-disk-dilatation").children('.mountPointTable').css("display", "none");
                    } else {
                        $(".errorTxt").html("").css("display", "none");
                        $(".getmountPoint").css("display", "none");
                        $("#config-disk-dilatation").children('.mountPointTable').css("display", "table");
                        ConfigFun.mountPointList = list.mount_point_list.concat([])
                        $(".mountPointBody").html(ConfigFun.dilatateFun(list));
                        ConfigFun.c_system == 'windows' && $('.mountPointTable').children('.cart_caption').css('display', 'table-caption');
                        ConfigFun.c_system == 'linux' && $('.mountPointTable').children('.cart_caption').css('display', 'none');
                        $('.ex1').slider({
                            formatter: function (value) {
                                return value + 'G';
                            }
                        });
                    }
                }

            },
            error: function () {
            }
        });
    });

    // 进入配置页面生成下拉IP列表
    $(".cart_body").on("click", ".editIp", function () {
        $("#ipTypeSelect").html('<option value="-1">请选择网卡IP类型</option>');
        ConfigFun.ele = this;
        ConfigFun.filterIpType($(this).parent().attr("data-ip-type"));
        var defaultIp = $(this).parent().attr("data-ip-addr");
        if (defaultIp) {
            $('#oriIp').text(defaultIp.split("_")[0]);
        } else {
            $('#oriIp').text('暂无IP');
        }
        ConfigFun.ipTypeArr.forEach(function (item, index) {
            $("#ipTypeSelect").append('<option value=' + item.key + '>' + item.value + '</option>');
        })
        $(".drop_down_ip").css("display", "none");
        $("#ipTypeSelect").val("-1");
        $("#vm-editIp-modal").modal("show");
    });
    $("#ipTypeSelect").change(function () {
        var nic_type_obj = ConfigFun.filterNicType();
        if (nic_type_obj.nic_type == 0 && $(this).val() != nic_type_obj.ip_type) {
            showMessage('此网卡不能修改IP类型', 'danger', 400);
            $(".drop_down_ip").css("display", "none");
            $(".js-example-basic-single").html('');
            return;
        }
        ConfigFun.filterIp($(this).val());
        var html = ConfigFun.createOption(ConfigFun.c_use_ips);
        if (!html) {
            showMessage('没有该类型的IP资源,请联系管理员！', 'danger', 400);
            $(".drop_down_ip").css("display", "none");
            $(".js-example-basic-single").html('');
            return;
        }
        $(".js-example-basic-single").html(html);
        $(".js-example-basic-single").select2();
        $(".drop_down_ip").css("display", "block")
    });
    $('#vm-editIp-modal').on('hidden.bs.modal', function (e) {
        $(".js-example-basic-single").val(null).trigger("change");
        $(".js-example-basic-single").html('<option value=""></option>')
    });

    $(".changeVmIp").click(function () {
        if ($(".js-example-basic-single").select2("data").length == 0) {
            showMessage('未选择有效IP资源！', 'danger', 400);
            return;
        }
        var res = $(".js-example-basic-single").select2("data")[0];
        if (res.id) {
            let json = {}, demo,
                old_ip_vlan = $(ConfigFun.ele).parent().attr("data-ipVlan");

            demo = res.id.split('_');
            let ip_type = $(ConfigFun.ele).parent().attr("data-ip-type");
            if (old_ip_vlan) {
                old_ip_vlan = old_ip_vlan.split('_');
                ConfigFun.c_surplus_ips.push({
                    "value": old_ip_vlan[0],
                    "vlan": old_ip_vlan[1],
                    "ip_type": ip_type
                });
            }
            json['ip_addr_new'] = demo[0].trim();
            json['vlan_new'] = demo[1].trim();
            json['ip_addr'] = $('#oriIp').text().trim();
            $(ConfigFun.ele).parent().attr("data-ipVlan", res.id);
            $(ConfigFun.ele).parent().attr("data-ip-type", $("#ipTypeSelect").val());
            switch ($("#ipTypeSelect").val()) {
                case '-1':
                    $(ConfigFun.ele).parent().prev().html("无");
                    break;
                case '0':
                    $(ConfigFun.ele).parent().prev().html("内网");
                    break;
                case '1':
                    $(ConfigFun.ele).parent().prev().html("外网电信");
                    break;
                case '2':
                    $(ConfigFun.ele).parent().prev().html("外网联通");
                    break;
                case '3':
                    $(ConfigFun.ele).parent().prev().html("镜像模板机使用");
                    break;
                case '4':
                    $(ConfigFun.ele).parent().prev().html("内网NAS网段");
                    break;
            }
            let newIp = demo[0].trim();
            $(ConfigFun.ele).siblings("u").text(newIp);
            for (var i = 0; i < ConfigFun.c_surplus_ips.length; i++) {
                if (ConfigFun.c_surplus_ips[i].value === newIp) {
                    ConfigFun.c_surplus_ips.splice(i, 1);
                }
            }
        }
        $("#vm-editIp-modal").modal("hide");
    });

    $("#vm-clone-create-modal ").on("click", ".optionsmall", function () {
        if ($(this).hasClass("cpu-reset")) {
            var _cpu_ = $(this).attr("data-id");
            var mem_list = CloneFun.flover_list.cpu2mem[parseInt(_cpu_)]
            var id_arr = CloneFun.mem_arr(_cpu_);

            $(this).addClass("selected").siblings().removeClass("selected");
            for (var i = 0, len = mem_list.length; i < len; i++) {
                var tmp = mem_list[i];
                if (id_arr.indexOf(parseInt(tmp)) != -1) {
                    $(".mem-reset[data-id='" + tmp + "']").removeClass("disabled").removeClass("selected").siblings().removeClass("selected");
                    id_arr.splice(id_arr.indexOf(parseInt(tmp)), 1);
                }
            }

            for (var i = 0, len = id_arr.length; i < len; i++) {
                $(".mem-reset[data-id='" + id_arr[i] + "']").addClass("disabled").removeClass("selected").siblings().removeClass("selected");
            }
        }
        if ($(this).hasClass("mem-reset") && !$(this).hasClass("disabled")) {
            $(this).addClass("selected").siblings().removeClass("selected");
        }
    });
    $("#vm-clone-create-btn").click(function () {
        var _cpu = $(".cpu-reset.selected").attr("data-id");
        var _mem = $(".mem-reset.selected").attr("data-id");
        var flavor_id, instance_id, instance_name, hostpool_id, data = {};
        var str = $(this).attr("data-str").split("to");
        hostpool_id = str[0];
        instance_id = str[1];
        instance_name = str[2];
        if (!_cpu || !_mem) {
            showMessage("请选择cpu数量和内存容量", "danger", 2000);
            return;
        }

        var _flavors = creatinitdata['flavors'];
        for (var i = 0, len = _flavors.length; i < len; i++) {
            var tmp = _flavors[i];
            if (tmp.vcpu == _cpu && tmp.memory_mb == _mem) {
                flavor_id = tmp.flavor_id;
            }
        }
        var app_info = $("#appinfo").val().trim();
        if (!app_info) {
            showMessage("请填写应用系统信息", "danger", 2000);
            $("#appinfo").focus();
            return;
        }
        var count = parseInt($("#vmnumber").val());
        if (count < 0) {
            $("#vmnumber").focus();
            showMessage("请填写正确的主机数量", "danger", 2000);
            return;
        }
        var group_id = $("#group-box").attr('data-group-id');
        let group_list_check = getGroupList(creatinitdata['groups'], createVmObject.cloneEnv);
        if (!createVmObject.blurCheckGroup("#group-box", group_list_check)) {
            showMessage("所选应用组的名称不存在", "danger", 600)
            return;
        }
        var owner = $("#managename").val();
        var password = $("#rootPwd").val().trim();
        if (password != "" && !checkPassword(password)) {
            showMessage("ROOT密码格式不正确", "danger", 2000);
            $("#rootPwd").focus();
            return;
        }
        data.hostpool_id = hostpool_id;
        data.instance_id = instance_id;
        data.instance_name = instance_name;
        data.flavor_id = flavor_id;
        data.hostpool_id = hostpool_id;
        data.count = count;
        data.app_info = app_info;
        data.group_id = group_id;
        data.owner = owner;
        data.password = password;
        //console.log(data);
        $.ajax({
            url: "/instance/clone/create?apiOrigin=self",
            type: "post",
            dataType: "json",
            data: data,
            beforeSend(){
                $("#vm-clone-create-modal").modal("hide");
            },
            success: function (res) {
                if (res.code != 0) {
                    res.msg != null
                        ? showMessage(res.msg, "danger", 10 * 60 * 1000)
                        : showMessage("请求失败", "danger", 2000)
                } else {
                    showMessage("操作成功", "success", 2000)
                }
                setTimeout(function () {
                    $('#myTable').bootstrapTable('refresh', {silent: true});
                }, 15000);
            },
            error: function () {
                showMessage("服务器连接失败", "danger", 2000);
            }
        });
    });

    //关闭监控信息模态框同时关闭时间选项模态框
    $('#hostMonitor').on('hidden.bs.modal', function (e) {
        $('#time_range').modal('hide');
    });
    //选中checkbox则启动开关机按钮
    if (tableOpera.myBrowser() == "IE") {
        $('#myTable').on('click', 'input[type="checkbox"]', function () {
            tableOpera.checkSelect();
        });
    } else {
        $('#myTable').on('change', 'input[type="checkbox"]', function () {
            tableOpera.checkSelect();
        });
    }
    //获取创建虚拟机的信息
    createVmObject.vmInitInfo();

    $("#Headquarterstype").on('click', 'div', function () //总部
    {
        var areadq = creatinitdata['area_DQ'];
        var areazb = creatinitdata['area_ZB'];
        var type2net = {};
        typenet2clu = {};   // todo global variable

        var odom = $(this).html();
        var oval = $(this).attr('data-id');
        //console.log('5:', odom, oval);
        !$(this).hasClass('selected') && $(this).addClass('selected').siblings().removeClass('selected');

        for (var i = 0; i < areazb.length; i++) {
            var type = areazb[i]['dc_type'];
            var net = areazb[i]['net_area_name'];
            var hname = areazb[i]['hostpool_name'];
            var hid = areazb[i]['hostpool_id'];
            if (!type2net[type]) {
                type2net[type] = [net];
            } else {
                type2net[type].push(net);
            }

            if (!typenet2clu[type]) {
                typenet2clu[type] = {};
            }
            if (!typenet2clu[type][net]) {
                typenet2clu[type][net] = [
                    {
                        name: hname,
                        id: hid
                    }
                ]
            } else {
                typenet2clu[type][net].push({
                    name: hname,
                    id: hid
                })
            }
        }
        for (var index in type2net) {
            type2net[index] = type2net[index].unique();
        }

        // dom 操作
        var netArr = type2net[parseInt(oval)];
        var netStr = '';
        for (var j = 0; j < netArr.length; j++) {
            netStr += '<option value="' + netArr[j] + '">' + netArr[j] + '</option>';
        }
        $("#networkarea option:not(:first-child)").remove();
        $("#cluster option:not(:first-child)").remove();
        $("#networkarea").append(netStr);


        //console.info(type2net, typenet2clu);

    })
    $("#networkarea").change(function ()//总部的网络区域
    {
        if ($(".elevator.selected").html() != "总部") {
            return false;
        }
        var val = $(this).val();
        var dc = $("#Headquarterstype div.selected").attr('data-id');
        if (!val || !dc) {
            return
        }
        var clusters = typenet2clu[parseInt(dc)][val];
        var clusterStr = '';
        for (var i = 0; i < clusters.length; i++) {
            clusterStr += '<option value="' + clusters[i]["id"] + '">' + clusters[i]["name"] + '</option>';
        }

        $("#cluster option:not(:first-child)").remove();
        $("#cluster").append(clusterStr);
    })

    //机房地区是地区的联动查询
    $("#area").change(function ()//地区选择
    {
        var val = $(this).val();


        var substr = '';
        var engineroomStr = '';
        $("#subarea option:not(:first-child)").remove();
        $("#engineroom option:not(:first-child)").remove();
        $("#networkarea option:not(:first-child)").remove();
        $("#cluster option:not(:first-child)").remove();
//            var dc =
//            console.log('1:', val);
//            console.log(dqparams);
        if (val == "-1") {
            $(".subarea_show").css("display", "none");
            return;
        }
        if (dqparams.nonesub.body.indexOf(val) != '-1') { //none
            var nonesubarr = dqparams.nonesub.toengineroom[val];
            for (var i = 0; i < nonesubarr.length; i++) {
                engineroomStr += '<option value="' + nonesubarr[i] + '">' + nonesubarr[i] + '</option>';
            }

            $(".subarea_show").css("display", "none");
            $("#engineroom").append(engineroomStr);
        }
        if (dqparams.hassub.body.indexOf(val) != '-1') {//has
            var subarr = dqparams.hassub.tonext[val];
            for (var i = 0; i < subarr.length; i++) {
                substr += '<option value="' + subarr[i] + '">' + subarr[i] + '</option>';
            }
            $(".subarea_show").css("display", "block");
            $("#subarea").append(substr);
        }

    })
    $("#subarea").change(function () //子区域
    {
        $("#engineroom option:not(:first-child)").remove();   //机房
        $("#networkarea option:not(:first-child)").remove();  //网络
        $("#cluster option:not(:first-child)").remove();  //集群
        var val = $(this).val();
        var name = $("#area").val();
        var str = '';

        val = name + val;
        var arr = dqparams.hassub.toengineroom[val];

        arr = arr.unique();
        for (var i = 0; i < arr.length; i++) {
            str += '<option value="' + arr[i] + '">' + arr[i] + '</option>';
        }
        $("#engineroom").append(str);
    })

    $("#engineroom").change(function () //机房选择
    {
        $("#networkarea option:not(:first-child)").remove();  //网络
        $("#cluster option:not(:first-child)").remove();  //集群
        var val = $(this).val();
        var area = $("#area").val();
        var subarea = $("#subarea").val();
        //console.log(subarea);

        var arr = [];
        var str = "";
        // console.info('==', val, area, subarea);

        if (subarea == "0")//没有子区域
        {
            val = area + val;
            arr = dqparams.nonesub.tonetarea[val];
        } else if (subarea != "0") {
            val = area + subarea + val;
            arr = dqparams.hassub.tonetarea[val];
        }

        arr = arr.unique().sort(function (a, b) {
            return a - b;
        });
        for (var i = 0; i < arr.length; i++) {
            str += '<option value="' + arr[i] + '">' + arr[i] + '</option>';
        }
        $("#networkarea").append(str);

    })

    $("#networkarea").change(function () //网络区域
    {
        if ($(".elevator.selected").html() === "总部") {
            return false
        }
        $("#cluster option:not(:first-child)").remove();  //集群
        var val = $(this).val();
        var area = $("#area").val();
        var subarea = $("#subarea").val();
        var net = $("#engineroom").val();
        var arr = [];
        var str = "";

        //console.log("==:", area, subarea, net, val);

        if (subarea == "0")//没有子区域
        {
            val = area + net + val;
            arr = dqparams.nonesub.tocluster[val];
            //console.log(val);

        } else if (subarea != "0") {
            val = area + subarea + net + val;
            arr = dqparams.hassub.tocluster[val];
        }
        arr = arr.unique().sort(function (a, b) {
            return a - b;
        });
        for (var i = 0; i < arr.length; i++) {
            str += '<option value="' + arr[i]['id'] + '">' + arr[i]['name'] + '</option>';
        }
        $("#cluster").append(str);
    })

    $("#constructmodelhook").on('click', 'div', function ()//主机类型选择
    {
        var inner = $(this).html();

        !$(this).hasClass('selected') && $(this).addClass('selected').siblings().removeClass('selected');
        var _linux = creatinitdata['images_linux'];
        var _win = creatinitdata['images_windows'];
        _linux = tableOpera.removeRepeat(_linux);
        _win = tableOpera.removeRepeat(_win);
        $("#constructmodel option:not(:first-child)").remove();
        if (inner == 'linux') {
            var str = '';
            for (var i in _linux) {
                str += '<option value="' + i + '">' + _linux[i] + '(' + i + ')</option>';

            }
            $("#constructmodel").append(str);
        }
        if (inner == 'windows') {
            var str = '';
            for (var i in _win) {
                str += '<option value="' + i + '">' + _win[i] + '(' + i + ')</option>';

            }
            $("#constructmodel").append(str);
        }
    })
    $("#btnCreate").click(function ()//切换到创建页面
    {
        //cpu mem disk信息
        createVmObject.initSome(creatinitdata.flavors, "#cpu-hook", "#mem-hook", "#disk-hook");

        // 模板选择
        createVmObject.initmoban();
        // 应用管理员
        //createVmObject.initappadmin();
        $('#appadmin').val('')
        //初始化网盘容量信息
        createVmObject.initdatadisk();

        // cluster
        if (createVmObject.initcluster()) {
            $(".createContent .info").addClass("Headquarters").removeClass("regional");
            //$("#instancePlace").children(":first-child").addClass("selected").siblings().removeClass("selected");
            $("#constructmodelhook").children(":first-child").addClass("selected").siblings().removeClass("selected");
            $("#networkarea option:not(:first-child)").remove();
            $("#cluster option:not(:first-child)").remove();
            $("#instancenumber").val(1);
            $("#datadisk").val(100);
            $("#appsystem").val("");
            $("#adminname").val("");
            $("#adminnamepass").val("");

            $("#secondWrapper").css("display", "block");
            $("#secondWrapper").animate({left: '3%'}, 'slow');
            $("#mainWrapper").animate({left: '-100%'}, 'slow', function () {
                $(this).css('display', 'none');
            });
        } else {
            showMessage("没有可用的集群，无法创建虚拟机", "danger", 2000);
        }


    });
    $("#backtolist").click(function () //切换到主页
    {
        backtomainFun("#mainWrapper", "#secondWrapper")
    })
    $("#detailstomain").click(function () {
        backtomainFun("#mainWrapper", "#vm-details")
    });

    function backtomainFun(id1, id2) {
        $(id1).css('display', 'block').animate({left: '0px'}, 'slow');
        $(id2).animate({left: '100%'}, 'slow', function () {
            $(this).css('display', 'none');
        })
    }


    function back2list() {
        $("#mainWrapper").css('display', 'block');
        $("#mainWrapper").animate({left: '0px'}, 'slow');
        $("#secondWrapper").animate({"left": "100%"}, "slow");
        $("#vmInfoSure").animate({left: '100%'}, 'slow', function () {
            $(this).css('display', 'none');
        })
    }


    $(".optionlarge").click(function ()//父区域信息初始化
    {
        $(this).addClass('selected').siblings().removeClass('selected');
        var outerWrapper = $(".elevator.selected").parent().parent().parent();
        if ($(this).hasClass('elevator')) {
            $("#Headquarterstype div").removeClass("selected");
            $("#subarea option:not(:first-child)").remove();
            $("#engineroom option:not(:first-child)").remove();
            $("#networkarea option:not(:first-child)").remove();
            $("#cluster option:not(:first-child)").remove();
            if ($(".elevator.selected").html() == '总部') {
                outerWrapper.removeClass('Headquarters regional').addClass('Headquarters');
                $(".subarea_show").css("display", "none");
            } else {
                outerWrapper.removeClass('Headquarters regional').addClass('regional');
                // 地区
                //init

                var dqarr = [].concat(dqparams.hassub.body, dqparams.nonesub.body);
                var dqstr = '';
                dqarr = dqarr.unique();
                for (var i = 0; i < dqarr.length; i++) {
                    dqstr += '<option value="' + dqarr[i] + '">' + dqarr[i] + '</option>';
                }
                $("#area option:not(:first-child)").remove();
                $("#area").append(dqstr);
            }
        }
        if ($(this).hasClass('environmenttype-hook')) {
            if ($(this).html() == '生产') {
                outerWrapper.removeClass('disaster').addClass('disaster');
            } else {
                outerWrapper.removeClass('disaster');
            }
        }
    });

    $(".hook").on('click', 'div', function ()//选择配置
    {
        var thisdiv = this;
        createVmObject.configadd(thisdiv, "#cpu-hook", "#mem-hook", "#disk-hook")
    })

    $("#goToNext").click(function ()//下一步确认信息
    {
        createVmObject.createInfoInit();
    });
    $("#gotoPrev").click(function ()//回到上一步
    {
        $("#secondWrapper").css("display", "block");
        $("#secondWrapper").animate({"left": "3%"}, "slow");
        $("#vmInfoSure").animate({"left": "100%"}, "slow", function () {
            $(this).css("display", "none");
        });
    });
    function getGroupListArr(list, envCode) {
        let groupList = [];
        for (var i = 0, len = list.length; i < len; i++) {
            if (envCode == list[i].dc_type) {
                groupList.push(list[i])
            }
        }
        return groupList
    }

    $("#appadmin").focus(function () // 获取焦点生成下拉组信息
    {
        let that = this;
        let grouplist = creatinitdata['groups'];
        let zb_dq = $("#instancePlace").children(".selected").text();
        let envCode = '', msg = "";
        if (zb_dq == "总部") {
            envCode = $("#Headquarterstype").children(".selected").attr("data-id")
            msg = '请先选择组所在的环境'
        } else if (zb_dq == '地区') {
            let datacenter_env = $("#engineroom").val();
            datacenter_env == '0' && (msg = '请先选择组所在的机房', envCode = false)
            datacenter_env != '0' && (envCode = allEnvArr.indexOf(datacenter_env.split('-')[1]))
        }
        if (!envCode) {
            showMessage(msg, 'danger', 600);
            return;
        }
        let list = getGroupListArr(grouplist, envCode)
        if (list.length <= 0) {
            showMessage("所选环境没有可用应用组", 'danger', 600);
            return;
        }
        createVmObject.focusGroupInfo(list, "#group_list")
        $("#group_list").slideDown()
    })

    $("#appadmin").keyup(function () // 模糊匹配组信息
    {
        let that = this;
        let grouplist = creatinitdata['groups'];
        let envCode = $("#Headquarterstype").children(".selected").attr("data-id")
        if (!envCode) {
            showMessage("请先选择组所在的环境", 'danger', 600);
            return;
        }
        let list = getGroupListArr(grouplist, envCode)
        if (list.length <= 0) {
            showMessage("所选环境没有可用应用组", 'danger', 600);
            return;
        }
        createVmObject.initappadmin(that, list, "#group_list")
    })

    $("#appadmin").blur(function () // 获取焦点生成下拉组信息
    {
        $("#group_list").slideUp()
    })
    $("#group_list").on("click", "li", function () //获取用户选中的组
    {
        let group_id = $(this).attr("data-id"),
            group_name = $(this).text();
        $("#appadmin").attr("data-group-id", group_id);
        $("#appadmin").val(group_name);
    })


    $("#createinstance").click(function ()//数据提交创建VM
    {
        // flavor
        var cpu = $("#cpu-hook div.selected").attr("data-id");
        var mem = $("#mem-hook div.selected").attr("data-id");
        var disk = $("#disk-hook div.selected").attr("data-id");
        var flavor_id;
        //console.warn('==', cpu, mem, disk);
        if (!cpu || !mem || !disk) {
            console.warn('please select cpu mem disk all');
            return false;
        }
        var flavors = creatinitdata.flavors;
        for (var i = 0; i < flavors.length; i++) {
            var item = flavors[i];
            var _cpu = item.vcpu;
            var _mem = item.memory_mb;
            var _disk = item.root_disk_gb;
            if (cpu == _cpu && mem == _mem && disk == _disk) {
                flavor_id = flavors[i]['flavor_id'];
            }
        }
        // cluster
        var cluster = $("#cluster").val();
        if (cluster == 0) {
            showMessage('请选择集群', 'danger', 1000);
            return false;
        }
        // construct model
        var model = $("#constructmodel").val();
        if (model == '0') {
            showMessage('请选择模板', 'danger', 1000);
        }
        // 数据盘
        var _datadisk = $("#datadisk").val();
        // 主机数量
        var _instancenumber = $("#instancenumber").val();
        // 应用系统信息
        var _appsystem = $("#appsystem").val();
        // 应用管理员
        var _appadmin = $("#appadmin").attr("data-group-id");
        // 管理员姓名
        var _adminname = $("#adminname").val();
        // 管理与密码
        var _adminpass = $("#adminnamepass").val().trim();
        // 容灾机器数量 on type == 4
        var disasternumberflag = $(".zbtype.selected").attr('data-id');
        var disasternumber = undefined;
        if (disasternumberflag === '4') {
            disasternumber = $("#disaster").val();
        }

        if (!cluster || !model || !flavor_id || !_datadisk || !_instancenumber || !_appsystem || !_appadmin || !_adminname) {
            showMessage("请填写完整信息！", 'danger', 2000);
        } else {
            var _url = '/instance/hostpool/' + cluster;
            $.ajax({
                url: _url,
                type: 'POST',
                beforeSend: function () {
                    $("#loading").css("display", "block");
                },
                data: {
                    hostpool_id: cluster,
                    image_name: model,
                    flavor_id: flavor_id,
                    disk_gb: _datadisk,
                    count: _instancenumber,
                    app_info: _appsystem,
                    group_id: _appadmin,
                    owner: _adminname,
                    password: _adminpass
                },
                dataType: 'json',
                success: function (data, textStatus) {
                    $("#loading").css("display", "none");
                    // 数据处理
                    if (data.code != '0') {
                        data.msg != null ? showMessage(data.msg, "danger", 3000) : showMessage("请求失败,请刷新重试", "danger", 1000);
                    } else {
                        showMessage("VM创建中", 'success', 2000);
                    }

                    // 返回VM列表
                    $("#vmInfoSure").css("display", "none");
                    back2list();
                    $("#myTable").bootstrapTable('refresh', {silent: true});
                }
            })

        }
    });

//vm开机 关机 重启 快照 删除
    $("#myTable").on("click", "#operaVm li", function ()//模态框信息初始化
    {
        var _str = $(this).text().trim();
        if (_str == "重启") {
            tableOpera.operaSingleInit("#vm-restart-table")
        }
        ;
        if (_str == "删除") {
            tableOpera.operaSingleInit("#vm-delete-table")
        }
        ;

    })

    $("#vm-power-on-btn").click(function ()//开机
    {
        var data = {};
        data.instance_ids = tableOpera.instance_ids.toString();
        tableOpera.operaSingleRequest("/instance/startup", "#vm-power-on-modal", "put", data);
    });


    $(".i-checks input[name='vmoff']").change(function ()//选择是否强制关机
    {
        var thisOne = this;
        tableOpera.checkOne(thisOne, "#vm-power-off-modal .i-checks", "#vmpowerOff-btn")

    });
    $(".i-checks input[type='checkbox']").change(function () {
        var thisTwo = this;
        tableOpera.checkTwo(thisTwo, "#vmpowerOff-btn")
    });
    $("#vmpowerOff-btn").click(function ()//关机 强制关机
    {
        var flag = "", data = {};
        var n = $(".i-checks input[name='vmoff']:checked").val();

        n == "option1" && (flag = 1)
        n == "option2" && (flag = 2);

        data.instance_ids = tableOpera.instance_ids.toString();
        data.flag = flag;
        tableOpera.operaSingleRequest("/instance/shutdown", "#vm-power-off-modal", "put", data);
    });


    $(".i-checks-res input[name='vmres']").change(function ()//选择是否强制重启
    {
        var thisOne = this;
        tableOpera.checkOne(thisOne, "#vm-restart-modal .i-checks-res", "#vm-restart-btn")

    });
    $(".i-checks-res input[type='checkbox']").change(function () {
        var thisTwo = this;
        tableOpera.checkTwo(thisTwo, "#vm-restart-btn")
    });


    $("#VmpowerOn").click(function ()//批量开机信息初始化
    {
        tableOpera.operabatchInit("#vmpowerOn-table");
    });

    $("#VmpowerOff").click(function ()//批量关机信息初始化
    {
        $(".i-checks input[type='radio']")[0].checked = true;
        $(".i-checks input[type='radio']")[1].checked = false;
        $(".i-checks input[type='checkbox']")[0].checked = false;
        $(".i-checks")[2].style.display = "none";
        $("#vmpowerOff-btn").attr("disabled", false);
        tableOpera.operabatchInit("#vmpowerOff-table");
    });

    $("#Vmrestart").click(function ()//批量重启信息初始化
    {
        tableOpera.operabatchInit("#vm-restart-table");
    });

    $("#VmDelete").click(function ()//批量删除信息初始化
        {

            $("#removeChe").prop("checked", false);
            $("#removevmBtn").attr("disabled", true);
            if ($(this).attr("data-target") == "") {
                showMessage("只有关机或者错误状态以及创建失败的VM才能进行删除操作！", "danger", 2000);
                return;
            } else {
                tableOpera.operabatchInit("#vm-delete-table");
            }
        }
    );

    //VM创建重试
    $("#VmRetry").click(function () {
        if ($(this).attr("data-target") == "") {
            showMessage("只有创建失败或者克隆创建失败的VM才能进行重试操作！", "danger", 2000);
            return;
        } else {
            tableOpera.operabatchInit("#vm-retry-table");
        }
    });
    $("#retryvmBtn").click(function () {
        var request_ids = tableOpera.request_id;
        console.log(request_ids);
        tableOpera.operaSingleRequest("/instance/retry",
            "#vm-retry-modal",
            "put",
            {
                "createFailed": request_ids[0].join(","),
                "cloneFailed": request_ids[1].join(",")
            }
        );
    });


    $("#configtolist").click(function ()//返回到主页
    {
        tableOpera.configtoback();
    });

    $("#removeChe").change(function () {
        tableOpera.removeCheck();
    });
    $("#removevmBtn").click(function ()//删除vm
    {
        if (!$(this).attr("disabled")) {
            var data = {}
            data.instance_ids = tableOpera.instance_ids.toString();
            tableOpera.operaSingleRequest("/instance", "#vm-delete-modal", "delete", data);
        }
    });


    $(".config-hook").on("click", "div", function ()//修改配置中的cpu mem disk
    {
        var thisdiv = this;
        createVmObject.configadd(thisdiv, "#config-cpu-hook", "#config-mem-hook", "#config-disk-hook")
    })
    $("#config-appadmin").focus(function () // 获取焦点生成下拉组信息
    {
        let that = this;
        let list = ConfigFun.groupList.groups;
        createVmObject.focusGroupInfo(list, "#config-group-list")
        $("#config-group-list").slideDown()
    })

    $("#config-appadmin").keyup(function () // 模糊匹配组信息
    {
        let that = this;
        let list = ConfigFun.groupList.groups;
        createVmObject.initappadmin(that, list, "#config-group-list");
    })

    $("#config-appadmin").blur(function () // 获取焦点生成下拉组信息
    {
        $("#config-group-list").slideUp()
    })
    $("#config-group-list").on("click", "li", function () //获取用户选中的组
    {
        let group_id = $(this).attr("data-id"),
            group_name = $(this).text();
        $("#config-appadmin").attr("data-group-id", group_id);
        $("#config-appadmin").val(group_name);
    })
    $("#config-submit").click(function ()//修改配置提交
    {
        var instance_id = $(this).attr("data-instance_id");
        tableOpera.configrevise(instance_id);
        $("#ipTypeSelect").html('');
    });
    $("#removalBtn").click(function ()//迁移
    {
        var instance_id = $(this).attr("data-instance-id");
        tableOpera.migrate_status == 0 && tableOpera.removalVm(instance_id, "/instance/migrate/", false);
        tableOpera.migrate_status == 1 && tableOpera.removalVm(instance_id, "/instance/hotmigrate/", true);


    });

    $("#vm-clone-btn").click(function ()//克隆
    {
        var instance_id = $("#vm-clone-table").attr("data-instance-id");
        tableOpera.cloneVm(instance_id);
    });

    function getGroupList(list, env) {
        var envArr = [];
        for (var i = 0; i < list.length; i++) {
            if (env == list[i]['dc_type']) {
                envArr.push(list[i])
            }
        }
        return envArr
    }

    $("#group-box").focus(function () // 获取焦点生成下拉组信息
    {
        let that = this;
        let list = getGroupList(creatinitdata['groups'], createVmObject.cloneEnv);
        createVmObject.focusGroupInfo(list, "#group-box-list")
        $("#group-box-list").slideDown()
    })

    $("#group-box").keyup(function () // 模糊匹配组信息
    {
        let that = this;
        let list = getGroupList(creatinitdata['groups'], createVmObject.cloneEnv);
        createVmObject.initappadmin(that, list, "#group-box-list")
    })

    $("#group-box").blur(function () // 获取焦点生成下拉组信息
    {
        $("#group-box-list").slideUp()
    })
    $("#group-box-list").on("click", "li", function () //获取用户选中的组
    {
        let group_id = $(this).attr("data-id"),
            group_name = $(this).text();
        $("#group-box").attr("data-group-id", group_id);
        $("#group-box").val(group_name);
    })
    // 添加网卡
    $(".add_cart_btn").click(function () {
        var instance_name = $("#config-instance-hook").html();
        $(".netCartVmName").html(instance_name)
        $("#add_net_cart").modal('show')
    })
    $("#check_add_cart").click(function () {
        var instance_id = $("#config-submit").attr("data-instance_id");
        $.ajax({
            url: '/instance/configure/netcard/' + instance_id,
            type: 'post',
            dataType: 'json',
            success: function (res) {
                if (res.code != 0) {
                    res.msg != null ? showMessage(res.msg, "danger", 400) : showMessage("请求失败,请刷新重试", "danger", 400);
                } else {
                    ConfigFun.refreshNetCart(instance_id, 3)
                    $("#add_net_cart").modal('hide')
                }
            },
            error: function () {
            }
        })
    })

    $("body").click(function (event) {
        clearTimeout(timer);
        tableOpera.interval_fun(list_timer);
    });
};
window.operateVmEvents = //表格中操作事件
{
    "click .clone-copy": function (e, value, row, index) {
        if (row.status != "1" && row.status != "3") {
            showMessage("只有关机状态下的VM才能克隆", "danger", 1000);
            return;
        }
        $("#vm-clone-modal").modal("show");
        var html = "<tr><td>" + (row.name != null ? row.name : "") + "</td><td>" + (row.ip_address != null ? row.ip_address : "") + "</td></tr>";
        $("#vm-clone-table").html(html).attr("data-instance-id", row.instance_id);
    },
    "click .clone-create": function (e, value, row, index) {
        //console.log(row)
        $(".mem-list").html("");
        $("#group-box").html("");
        $(".cpu-list").html("");
        $("#appinfo").val("");
        $("#managename").val("");
        $("#vm-clone-create-btn").attr("data-str", "");
        if (row.status != "1") {
            showMessage("非关机状态下的虚拟机无法用于克隆创建", "danger", 1000);
            return;
        }
        ;
        if (row.system != "linux") {
            showMessage("非linux系统虚拟机无法用于克隆创建", "danger", 1000);
            return;
        }
        ;
        if (row.create_source != "0") {
            showMessage("v2v虚拟机无法用于克隆创建", "danger", 1000);
            return;
        }
        ;

        var groupname = row.app_group;
        var groupid = row.app_group_id;
        var flavorid = row.flavor_id, _cpu, _mem;
        if (creatinitdata) {
            var _groups = creatinitdata['groups'];
            for (var i = 0, len = _groups.length; i < len; i++) {
                var tmp = _groups[i];
                if (tmp.group_id === groupid) {
                    $("#group-box").val(tmp.name).attr("data-group-id", tmp.group_id);
                    createVmObject.cloneEnv = row.dc_type
                }
            }

            var _flavors = creatinitdata['flavors'];
            for (var i = 0, len = _flavors.length; i < len; i++) {
                var tmp = _flavors[i];
                if (tmp.flavor_id == flavorid) {
                    _cpu = tmp.vcpu;
                    _mem = tmp.memory_mb;
                }
            }

            for (var i = 0, len = CloneFun.flover_list.cpus.length; i < len; i++) {
                var item = CloneFun.flover_list.cpus[i];
                if (item == _cpu) {
                    $(".cpu-list").append('<div class="optionsmall cpu-reset selected" data-id=' + item + '>' + item + '核</div>');
                } else {
                    $(".cpu-list").append('<div class="optionsmall cpu-reset" data-id=' + item + '>' + item + '核</div>');
                }
            }

            _mem > 1024 ? _mem = _mem / 1024 + "G" : _mem = _mem + "MB";
            for (var i = 0, len = CloneFun.flover_list.mems.length; i < len; i++) {
                var item = CloneFun.flover_list.mems[i], mem_val;
                item > 1024 ? mem_val = item / 1024 + "G" : mem_val = item + "MB";

                if (mem_val == _mem) {
                    $(".mem-list").append('<div class="optionsmall mem-reset selected" data-id=' + item + '>' + mem_val + '</div>');
                } else {
                    if (CloneFun.flover_list.cpu2mem[parseInt(_cpu)].indexOf(item) != -1) {
                        $(".mem-list").append('<div class="optionsmall mem-reset" data-id=' + item + '>' + mem_val + '</div>');
                    } else {
                        $(".mem-list").append('<div class="optionsmall mem-reset disabled" data-id=' + item + '>' + mem_val + '</div>');
                    }

                }
            }
        }
        $("#appinfo").val(row.app_info);
        $("#managename").val(row.owner);

        var str = row.hostpool_id + "to" + row.instance_id + "to" + row.name;

        $("#vm-clone-create-btn").attr("data-str", str);
        $("#vm-clone-create-modal").modal("show");
    },
    "click #configuration": function (e, value, row, index) {
        if (row.status == "1" || row.status == "3") {
            tableOpera.configreviseInit(row);
            $("#config-submit").attr("data-instance_id", row.instance_id);
        } else {
            showMessage("只有运行中或者关机状态的VM才能修改配置", "danger", 2000);
        }
    },
    "click #removeVm": function (e, value, row, index) {
        if (row.status == "1" || row.status == "99" || row.status == "100" || row.status == "101" || row.status == "102") {
            $("#removeChe").prop("checked", false);
            $("#removevmBtn").attr({"disabled": true, "data-instance_id": row.instance_id});
            $("#vm-delete-table").html("<tr><td>" + row.name + "</td><td>" + row.ip_address + "</td><td>" + status + "</td></tr>");
        } else {
            showMessage("只有关机、错误以及创建失败或者克隆创建失败的VM才能删除", "danger", 2000);
            return;
        }
    },
    "click #migrateVm": function (e, value, row) {
        if (row.status != "1") {
            showMessage("只有关机状态下的VM才能迁移", "danger", 1000);
            return;
        }
        $("#vm-removal-clc").text("冷迁移");
        $("#vm-removal-modal input").val("");
        $("#speed-limit").css("display", "block")
        $("#speed-limit input").val(160);
        tableOpera.removalInit(row.instance_id, "/instance/migrate/init/");
        tableOpera.migrate_status = 0;
    },
    "click #powerOn": function (e, value, row, index) {
        if (row.status != 1) {
            showMessage("只有关机的VM才能开机", "danger", 2000);
            return;
        }
        tableOpera.operaSingleInit("#vmpowerOn-table");
        $("#vm-power-on-modal").modal("show");
    },
    "click #powerOff": function (e, value, row, index) {
        $(".i-checks input[type='radio']")[0].checked = true;
        $(".i-checks input[type='radio']")[1].checked = false;
        $(".i-checks input[type='checkbox']")[0].checked = false;
        $(".i-checks")[2].style.display = "none";
        if (row.status != 3 && row.status != 2) {
            showMessage("只有运行中的VM才能关机", "danger", 2000);
            return;
        }
        tableOpera.operaSingleInit("#vmpowerOff-table");
        $("#vm-power-off-modal").modal("show");
    },
    //绑定远程事件
    "click #consolePage": function (e, value, row, index) {
        if (row.status == "0" || row.status == "1" || row.status == "5" || row.status == "6" || row.status == "8" || row.status == "98" || row.status == "100" || row.status == "9" || row.status == "101") {
            return;
        }
        function setCookie(name, value) {
            var Days = 30;
            var exp = new Date();
            exp.setTime(exp.getTime() + Days * 24 * 60 * 60 * 1000);
            document.cookie = name + "=" + escape(value) + ";expires=" + exp.toGMTString();
        }

        setCookie('token', '192.168.66.202-5900');

        var url = window.location.href;
        var position = url.indexOf("/kvm");
        // var position = url.indexOf("/kvm");
        var imgUrl = url.substring(0, position);
        var consoleUrl = imgUrl + "/instance/console?instance=" + row.uuid;
        window.open(consoleUrl)
    },
    //绑定监控
    "click #monitorPage": function (e, value, row, index) {
        myChart = echarts.init(document.getElementById('main'));
        init_echart();
        $("#model-title").html(row.name);

        var ip = row.ip_address;
        console.info(ip);
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
        clearTimeout(timer);
        tableOpera.interval_fun(list_timer);
    },
    "click #hotmigrateVm": function (e, value, row, index) {
        if (row.status == 3) {
            $("#vm-removal-clc").text("热迁移");
            $("#vm-removal-modal input").val("");
            $("#speed-limit").css("display", "none");
            tableOpera.removalInit(row.instance_id, "/instance/hotmigrate/init/");
            tableOpera.migrate_status = 1;
        } else {
            showMessage('只有运行中的VM才能进行热迁移', "danger", 2000);
        }
    }
};
var tableOpera =
{
    searchTextObj:'', //搜搜字段的集合
    configflavors: "",//保存配置中的flavor
    instance_ids: [],//存储单个操作的instance_id
    request_id: [],//存储重试操作的request_id
    rowInfo: null,//保存单个操作的当行的所有数据
    export_data: [],//导出数据集合
    migrate_status: "",
    selHtml: function (row)//表格中操作列表生成
    {
        var urlName = getUrlPath();
        var html = "";
        html += '<a class="remote showIf" data-table-promission="console" tittle="VNC" id="consolePage" target="_blank"><i class="fa fa-laptop text-warning"></i></a>&nbsp;'
        html += '<div class="btn-group operamore">';
        html += '<button type="button" class="btn btn-primary dropdown-toggle btn-xs"  data-toggle="dropdown">更多';
        html += '<span class="fa fa-angle-down"></span>';
        html += '</button>';
        html += ' <ul id="operaVm" class="dropdown-menu" role="menu">';
        $.each(user_permisson_arr, function (i, tmp) {
            if (tmp[urlName] && tmp[urlName].length > 0) {
                if (tmp[urlName].indexOf('startup') >= 0) {
                    html += '<li id="powerOn" data-toggle="modal">';
                    html += '<a href="#">开机</a>';
                    html += '</li>'
                }
                if (tmp[urlName].indexOf('shutdown') >= 0) {
                    html += '  <li id="powerOff" data-toggle="modal">';
                    html += ' <a href="#">关机</a>';
                    html += '  </li>';
                }
                if (tmp[urlName].indexOf('configure') >= 0) {
                    html += ' <li id="configuration">';
                    html += '<a href="#">配置</a>';
                    html += '</li>';
                }
                if (tmp[urlName].indexOf('delete') >= 0) {
                    html += '<li id="removeVm" data-toggle="modal" class="removeVmSure">';
                    html += '<a href="#">删除</a>';
                    html += ' </li>';
                }
                if (tmp[urlName].indexOf('cold_migrate') >= 0) {
                    html += '<li id="migrateVm" data-toggle="modal"  class="migrateVmSure" >';
                    html += '<a href="#">冷迁移</a>';
                    html += ' </li>';
                }
                if (tmp[urlName].indexOf('clone') >= 0) {
                    html += '<li id="hotmigrateVm" data-toggle="modal" >';
                    html += '<a href="#">热迁移</a>';
                    html += ' </li>';
                }
                if (tmp[urlName].indexOf('cold_migrate') >= 0) {
                    html += '<li   class="disabled cloneVm" style="position: relative;">';
                    html += '<a href="#">克隆</a>';
                    html += '<ul class="list-group clone_box">';
                    html += '<li class="list-group-item clone-copy">克隆备份</li>';
                    html += '<li class="list-group-item clone-create">克隆创建</li>';
                    html += '</ul>';
                    html += ' </li>';
                }
                return false;
            }
        });
        html += '</ul>';
        html += '</div>';
        return html;
    },
    searchData:{
        //name:'',
        //uuid:'',
        //ip_address:"",
        //host_ip:"",
        //status:"",
        //owner:'',
        //group_name:""
    },
    interval_fun: function (list) {
        timer = setTimeout(function () {
            var type = $(".operamore"), type_arr = [];
            var sel_arr = $("#myTable").bootstrapTable("getSelections");
            for (var i = 0; i < type.length; i++) {
                if (type[i].className == "btn-group operamore open") {
                    type_arr.push("1");
                }
            }
            if (sel_arr.length > 0 || type_arr.length > 0)return;
            $("#myTable").bootstrapTable('refresh', {silent: true});
        }, 20000); //time是指本身,延时递归调用自己,10000为间隔调用时间,单位毫秒

    },
    vmDetailsId: '',
    vmDetails: function (instance_id)//VM详情
    {
        this.vmDetailsId = instance_id;
        $.ajax({
            url: "/instance/info/" + instance_id,
            type: "get",
            success: function (res) {
                if (res.code != 0) {
                    res.msg != null ? showMessage(res.msg, "danger", 1000) : showMessage("请求失败,请刷新重试", "danger", 1000);
                } else {
                    var data = res.data;
                    var titlearr = $(".vm-details-body tr").children(":last-child");
                    //console.log(titlearr);
                    $.each(data, function (index, tmp) {
                        for (var i = 0; i < titlearr.length; i++) {
                            //console.log(titlearr[i]); sys_version
                            //console.log(index);
                            if ($(titlearr[i]).attr("title") == index) {
                                if (tmp != null) {
                                    if (index == "memory_mb") {
                                        parseInt(tmp) > 1024 ? $(titlearr[i]).html(parseInt(tmp) / 1024 + "G") : $(titlearr[i]).html(tmp + "MB");
                                    } else if (index == "disk_gb") {
                                        $(titlearr[i]).html(tmp + "G");
                                    } else if (index == "cpu") {
                                        $(titlearr[i]).html(tmp + "核");
                                    } else if (index == "root_disk_gb") {
                                        $(titlearr[i]).html(tmp + "G");
                                    } else if (index == "dc_type") {
                                        var arr = allEnvArr;
                                        var dc_type = parseInt(tmp);
                                        $(titlearr[i]).html(arr[dc_type]);
                                    } else if (index == "image_name") {
                                        if (data["create_source"] == 0) {
                                            $(titlearr[i]).html(tmp).parent().css("visibility", "visible")
                                        }
                                    } else if (index == "sys_version" && tmp == "unknown") {
                                        $(titlearr[i]).html(tmp + '<i class="fa fa-pencil-square-o icon-large edit_os" aria-hidden="true"></i>');
                                    } else {
                                        $(titlearr[i]).html(tmp);
                                    }
                                } else {
                                    $(titlearr[i]).html("");
                                    if ((data["create_source"] == 1 || data["create_source"] == 2) && index == "image_name") {
                                        $(titlearr[i]).parent().css("visibility", "hidden");
                                    }
                                }
                            }
                        }
                    });
                    $("#vm-details").css("display", "block").animate({"left": "3%"}, "slow");
                    $("#mainWrapper").animate({"left": "-100%"}, "slow", function () {
                        $(this).css("display", "none");
                    });
                }
            }
        });
    },
    removeRepeat: function (arr)//搭建模板去重算法
    {
        var noReapeatArr = {};
        $.each(arr, function (index, tmp) {
            if (!noReapeatArr[tmp.name]) {
                noReapeatArr[tmp.name] = tmp.displayname;
            }
        });
        return noReapeatArr;
    },
    operaSingleInit: function (id)//单个操作的信息初始化
    {
        var list = this.rowInfo;
        var status = judgeStatus(list.status);
        for (var i in list) {
            list[i] == null && (list[i] = "");
        }
        $(id).html(" <tr><td>" + list.name + "</td><td>" + list.ip_address + "</td><td>" + status + "</td></tr>");

    },
    operaSingleRequest: function (url, id, type, data)//单个或者批量操作请求
    {
        $.ajax({
            url: url,
            type: type,
            data: data,
            dataType: "json",
            beforeSend: function () {
                $("#loading").css("display", "block");
                $(id).modal("hide");
                $('#VmpowerOn').attr('disabled', true).attr('data-target', '');
                $('#VmpowerOff').attr('disabled', true).attr('data-target', '');
                $('#Vmrestart').attr('disabled', true).attr('data-target', '');
                $('#VmDelete').attr('disabled', true).attr('data-target', '');
                $('#VmRetry').attr('disabled', true).attr('data-target', '');
            },
            success: function (res) {
                $("#loading").css("display", "none");
                $('#myTable').bootstrapTable("refresh", {slient: true});
                if (res.code == "1") {
                    showMessage("部分操作成功", "warning", 1000);
                } else if (res.code != 0 && res.code != "1") {
                    res.msg != null ? showMessage(res.msg, "danger", 1000) : showMessage("操作失败", "danger", 1000);
                } else {
                    showMessage("操作成功", "success", 1000);
                }
            },
            error: function () {
                showMessage("请求失败,请刷新页面再操作", "danger", 2000);
            }
        });
    },
    checkOne: function (thisOne, id1, id2) {
        $(thisOne).attr("value") == "option2" && ($(id1)[2].style.display = "inline-block") && $(id2).attr("disabled", true);
        $(thisOne).attr("value") == "option1" && (($(id1)[2].style.display = "none") && $(id1 + " input[type='checkbox']").prop("checked", false)) && $(id2).attr("disabled", false);
        ;
    },
    checkTwo: function (thisTwo, id) {
        if ($(thisTwo).prop("checked")) {
            $(id).attr("disabled", false)
        } else {
            ($(id).attr("disabled", true));
        }
    },
    operabatchInit: function (id)//批量操作数据
    {
        this.instance_ids = [];
        this.request_id = [[], []];
        var html = "";
        var arr = $("#myTable").bootstrapTable("getSelections");//被选中的数据

        for (var i = 0; i < arr.length; i++) {
            for (var j in arr[i]) {
                arr[i][j] == null && (arr[i][j] = "");
            }
            var status = judgeStatus(arr[i].status);
            this.instance_ids.push(arr[i].instance_id);
            arr[i].status == "100" && (this.request_id[0].push(arr[i].request_id));
            arr[i].status == "102" && (this.request_id[1].push(arr[i].request_id));


            html += " <tr><td>" + arr[i].name + "</td><td>" + arr[i].ip_address + "</td><td>" + status + "</td></tr>";
        }
        $(id).html(html);
    },
    myBrowser: function ()//判断浏览器版本
    {
        var userAgent = navigator.userAgent; //取得浏览器的userAgent字符串
        var isOpera = userAgent.indexOf("Opera") > -1;
        var isIE = userAgent.indexOf("compatible") > -1 && userAgent.indexOf("MSIE") > -1 && !isOpera;
        var isIE11 = (userAgent.toLowerCase().indexOf("trident") > -1 && userAgent.indexOf("rv") > -1);
        if (isOpera) {
            return "Opera"
        }
        ; //判断是否Opera浏览器
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
        }
        ; //判断是否IE浏览器
    },
    configtoback: function () {
        $('#myTable').bootstrapTable("refresh", {slient: true});
        $("#mainWrapper").css("display", "block");
        $("#mainWrapper").animate({left: '0px'}, 'slow');
        $("#configWrapper").animate({left: '100%'}, 'slow', function () {
            $(this).css('display', 'none');
        });
    },
    checkSelect: function ()//表格中的checkbox选中操作
    {
        var arr = $('#myTable').bootstrapTable('getSelections');
        var group_id_arr = [];
        var is_statu = true;

        for (var i = 0; i < id_arr.length; i++) {
            if (id_arr[i][0] == 3) {
                group_id_arr.push(id_arr[i][1]);
            }
        }
        ;

        $.each(arr, function (index, tmp) {
            var arr = [-100, 0, 4, 7, 8, 9, 10, 103, 104];
            var statu = tmp.status;
            statu == "" && (statu = -100);
            if (arr.indexOf(parseInt(statu)) != -1) {
                showMessage("所选的vm中有不可操作的,请仔细审查！！！", "danger", 1000);
                return is_statu = false;
            } else {
                return is_statu = true;
            }
        });
        if (is_statu) {
            if ($('#myTable tr').hasClass('selected')) {
                //console.log(arr.length);
                if (arr.length <= 100) {
                    $('#VmpowerOn').attr('disabled', false).attr('data-target', '#vm-power-on-modal');
                    $('#VmpowerOff').attr('disabled', false).attr('data-target', '#vm-power-off-modal');
                    $('#Vmrestart').attr('disabled', false).attr('data-target', '#vm-restart-modal');

                    for (var i = 0, statu_arr = [], retry_arr = [], no_arr = [0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 98];
                         i < arr.length; i++) {
                        if (no_arr.indexOf(parseInt(arr[i].status)) != -1) {
                            statu_arr.push(arr[i].status);
                        }
                        if (arr[i].status == "100" || arr[i].status == "102") {
                            retry_arr.push(arr[i].status);
                        }
                    }
                    if (statu_arr.length > 0) {
                        $('#VmDelete').attr('disabled', false).attr('data-target', '');
                    } else {
                        $('#VmDelete').attr('disabled', false).attr('data-target', '#vm-delete-modal');
                    }
                    retry_arr.length == 0 && $('#VmRetry').attr('disabled', false).attr('data-target', '');
                    retry_arr.length > 0 && $('#VmRetry').attr('disabled', false).attr('data-target', '#vm-retry-modal');

                } else {
                    showMessage("最多只能批量操作100条数据", "warning", 1000);
                    $('#VmpowerOn').attr('disabled', true).attr('data-target', '');
                    $('#VmpowerOff').attr('disabled', true).attr('data-target', '');
                    $('#Vmrestart').attr('disabled', true).attr('data-target', '');
                    $('#VmDelete').attr('disabled', true).attr('data-target', '');
                    $('#VmRetry').attr('disabled', true).attr('data-target', '');
                }
            } else {
                $('#VmpowerOn').attr('disabled', true).attr('data-target', '');
                $('#VmpowerOff').attr('disabled', true).attr('data-target', '');
                $('#Vmrestart').attr('disabled', true).attr('data-target', '');
                $('#VmDelete').attr('disabled', true).attr('data-target', '');
                $('#VmRetry').attr('disabled', true).attr('data-target', '');
            }
        }
    },
    configreviseInit: function (row)//修改配置信息初始化
    {
        var getflavors = this;
        ConfigFun.vmInfo.instance_id = row.instance_id;
        $(".mountPointInfoLoad").css("display", "none");
        $(".addNewMount").css("display", 'none');
        $("#config-disk-dilatation").children('.mountPointTable').css("display", "none");
        $(".errorTxt").css("display", "none");
        $(".getmountPoint").css("display", "inline-block");
        $('.ex1').slider({"destroy": true});
        if (row.status != 3) $(".dilatationShow").css("display", "none");
        else $(".dilatationShow").css("display", "block");
        $.ajax({
            url: "/instance/configure/init/" + row.instance_id,
            type: "get",
            beforeSend: function () {
                $("#loading").css("display", "block");
            },
            success: function (res) {
                $("#loading").css("display", "none");
                if (res.code != 0) {
                    res.msg != null ? showMessage(res.msg, "danger", 1000) : showMessage("操作失败", "danger", 1000);
                    return;
                }
                ConfigFun.c_ips_back = res.data.c_ips.concat([]);
                ConfigFun.c_surplus_ips = ConfigFun.c_ips_back.concat([]);
                var initList = res.data;
                ConfigFun.groupList = res.data
                var flavors = initList.flavors;
                getflavors.configflavors = flavors;
                var cpus = [];
                var mems = [];
                var disks = [];
                var cpu2mem = [];
                var cpumem2disk = [];

                for (var i = 0; i < flavors.length; i++) {
                    var item = flavors[i];
                    var cpu = item.vcpu;
                    var mem = item.memory_mb;
                    var disk = item.root_disk_gb;

                    cpus.push(cpu);
                    mems.push(mem);
                    disks.push(disk);

                    if (!cpu2mem[cpu]) {
                        cpu2mem[cpu] = [mem]
                    } else {
                        cpu2mem[cpu].push(mem);
                    }
                    if (!cpumem2disk[cpu]) {
                        cpumem2disk[cpu] = {};
                    }
                    if (!cpumem2disk[cpu][mem]) {
                        cpumem2disk[cpu][mem] = [disk]
                    } else {
                        cpumem2disk[cpu][mem].push(disk);
                    }
                }
                //去重
                cpus = cpus.unique().sort(function (a, b) {
                    return a - b;
                });
                mems = mems.unique().sort(function (a, b) {
                    return a - b;
                });
                disks = disks.unique().sort(function (a, b) {
                    return a - b;
                });

                cpu2mem = cpu2mem.map(function (item, index, array) {
                    return item.unique().sort(function (a, b) {
                        return a - b;
                    });
                });
                for (var j = 0; j < cpus.length; j++) {
                    var _cpu = cpus[j];
                    for (var k in cpumem2disk[_cpu]) {
                        cpumem2disk[_cpu][k] = cpumem2disk[_cpu][k].unique().sort(function (a, b) {
                            return a - b;
                        });
                    }
                }

                //console.log(cpus,mems,disks,cpu2mem,cpumem2disk);

                $("#config-cpu-hook").empty();
                $("#config-mem-hook").empty();
                $("#config-disk-hook").empty();

                var cpudomstr = '';
                var memdomstr = '';
                var diskdomstr = '';

                var cpudefault = '';
                var memdefault = "";
                var diskdefault = "";

                var flavor_id = initList.c_flavor_id;
                $.each(initList.flavors, function (index, tmp) {
                    if (tmp.flavor_id == flavor_id) {
                        cpudefault = tmp.vcpu;
                        memdefault = tmp.memory_mb;
                        diskdefault = tmp.root_disk_gb;
                        //console.log(cpudefault,memdefault,diskdefault);
                    }
                });


                //cpu mem disk 配置
                for (var i = 0; i < cpus.length; i++) {
                    if (cpus[i] == cpudefault) {
                        cpudomstr += '<div class="cpu config-optionsmall selected" data-id="' + cpus[i] + '">' + cpus[i] + '核</div>'
                    } else {
                        cpudomstr += '<div class="cpu config-optionsmall" data-id="' + cpus[i] + '">' + cpus[i] + '核</div>';
                    }
                }
                for (var i = 0; i < mems.length; i++) {
                    if (cpu2mem[cpudefault].indexOf(mems[i]) != -1) {
                        if (mems[i] == memdefault && parseInt(mems[i]) < 1024) {
                            memdomstr += '<div class="mem config-optionsmall selected" data-id="' + mems[i] + '">' + mems[i] + 'M</div>'
                        } else if (mems[i] == memdefault && parseInt(mems[i]) >= 1024) {
                            var val = parseInt(mems[i]) / 1024;
                            memdomstr += '<div class="mem config-optionsmall selected" data-id="' + mems[i] + '">' + val + 'G</div>'
                        } else {
                            if (parseInt(mems[i]) < 1024) {
                                memdomstr += '<div class="mem config-optionsmall" data-id="' + mems[i] + '">' + mems[i] + 'M</div>'
                            } else {
                                var val = parseInt(mems[i]) / 1024;
                                memdomstr += '<div class="mem config-optionsmall" data-id="' + mems[i] + '">' + val + 'G</div>'
                            }
                        }
                    } else {
                        if (parseInt(mems[i]) < 1024) {
                            memdomstr += '<div class="mem config-optionsmall disabled" data-id="' + mems[i] + '">' + mems[i] + 'M</div>'
                        } else {
                            var val = parseInt(mems[i]) / 1024;
                            memdomstr += '<div class="mem config-optionsmall disabled" data-id="' + mems[i] + '">' + val + 'G</div>'
                        }
                    }
                }
                for (var i = 0; i < disks.length; i++) {
                    if (cpumem2disk[cpudefault][memdefault].indexOf(disks[i] != -1)) {
                        if (disks[i] == diskdefault) {
                            diskdomstr += '<div class="disk config-optionsmall selected" data-id="' + disks[i] + '">' + disks[i] + 'G</div>'
                        } else {
                            diskdomstr += '<div class="disk config-optionsmall" data-id="' + disks[i] + '">' + disks[i] + 'G</div>'
                        }
                    } else {
                        diskdomstr += '<div class="disk config-optionsmall disabled" data-id="' + disks[i] + '">' + disks[i] + 'G</div>'
                    }
                }

                $("#config-cpu-hook").html(cpudomstr);//cpu
                $("#config-mem-hook").html(memdomstr);//mem
                $("#config-disk-hook").html(diskdomstr);//disk
                $("#config-appsystem").val(initList.c_app_info);
                $("#config-instance-hook").html(initList.c_instance_name);

                ConfigFun.net_cart_list = initList.c_net;
                ConfigFun.status = row.status;
                ConfigFun.c_system = initList.c_system;
                if (ConfigFun.net_cart_list.length >= 2 || row.status == 1) {
                    $(".add_cart_btn").attr('disabled', true)
                } else {
                    $(".add_cart_btn").attr('disabled', false)
                }

                if (row.status == 3 || row.status == 1) {
                    $(".net_card_box").css("display", "block");
                    var net_cart_list = initList.c_net;
                    if (net_cart_list.length > 0) {
                        $(".has-net-cart").css("display", "block");
                        $(".none-net-cart").css("display", "none");
                        for (var k = 0, html = ""; k < net_cart_list.length; k++) {
                            html = ConfigFun.hasnetCart(
                                k,
                                net_cart_list[k],
                                html,
                                row.status,
                                initList.c_system,
                                initList.c_ips,
                                net_cart_list[k].ip_type
                            );
                        }
                        $(".cart_body").html(html);
                    } else {
                        $(".cart_body").html("");
                        $(".has-net-cart").css("display", "none");
                        $(".none-net-cart").css("display", "block");
                    }
                } else {
                    $(".cart_body").html("");
                    $(".net_card_box").css("display", "none");
                }


                //应用组信息下拉框
                var group_id = initList.c_group_id;
                $.each(initList.groups, function (index, tmp) {
                    if (tmp.group_id == group_id) {
                        $("#config-appadmin").val(tmp.group_name).attr('data-group-id', tmp.group_id);
                    }
                });

                $("#config-dminname").val(initList.c_owner);
                $("#mainWrapper").animate({left: '-100%'}, 'slow', function () {
                    $(this).css('display', 'none');
                });
                $("#configWrapper").css("display", "block").animate({left: '5%'}, 'slow');

            }
        });
    },
    configrevise: function (instance_id)//提交配置信息
    {
        var cpu = $("#config-cpu-hook div.selected").attr("data-id");
        var mem = $("#config-mem-hook div.selected").attr("data-id");
        var disk = $("#config-disk-hook div.selected").attr("data-id");
        var flavor_id = "";
        var disk_gb_list = [];
        var disk_gb_obj = {};
        var list = this.configflavors;
        var mountPOint = $('.diskMountPoint').val();
        var extra_size = $('.mountPointSize').val();
        $.each(list, function (index, tmp) {
            if (tmp.vcpu == cpu && tmp.memory_mb == mem && tmp.root_disk_gb == disk) {
                flavor_id = tmp.flavor_id;
            }
        });
        if (!flavor_id) {
            showMessage("请选择配置信息", "danger", "2000");
            return;
        }
        var group_id = $("#config-appadmin").attr('data-group-id');
        let group_list_check = ConfigFun.groupList.groups;
        if (!createVmObject.blurCheckGroup("#config-appadmin", group_list_check)) {
            showMessage("所选应用组的名称不存在", "danger", 600)
            return;
        }
        var net_status_list = ConfigFun.getnetCartParams(ConfigFun.net_cart_list, ConfigFun.c_ips_back, ConfigFun.c_system);

        net_status_list = JSON.stringify(net_status_list);
        //console.log(net_status_list);


        var app_info = $("#config-appsystem").val();
        var owner = $("#config-dminname").val();

        //console.log(disk_gb_list, owner, app_info);
        if (owner == "" || app_info == "") {
            showMessage("请填写完整信息", "danger", 1000);
            return;
        }

        if (
            ((!mountPOint && extra_size) ||
            (!extra_size && mountPOint)) &&
            ConfigFun.c_system == 'linux'
        ) {
            showMessage('新增挂载点目录名和磁盘大小可同时为空但不能只填一项', 'danger', 1000);
            return;
        }
        if (ConfigFun.mountPointNameArr.indexOf('/' + mountPOint) != -1) {
            if (mountPOint) {
                showMessage('目录名已存在请重新输入', 'danger', 1000);
                return;
            }
        }
        $.ajax({
            url: "/instance/configure/" + instance_id,
            type: "PUT",
            dataType: "json",
            data: {
                "flavor_id": flavor_id,
                "group_id": group_id,
                "disk_gb_list": disk_gb_list,
                "app_info": app_info,
                "owner": owner,
                "net_status_list": net_status_list,
                "extend_list": JSON.stringify(ConfigFun.getMountedPointParams()),
                "qemu_ga_update": ConfigFun.qemu_ga_update,
                "flavor_id_old":ConfigFun.groupList.c_flavor_id
            },
            beforeSend: function () {
                $("#loading").css("display", "block");
            },
            success: function (res) {
                $("#loading").css("display", "none");
                if (res.code != 0) {
                    res.msg != null ? showMessage(res.msg, "danger", 1000) : showMessage("操作失败", "danger", 1000);
                    return;
                } else {
                    showMessage(res.msg, 'success', 2000);
                }
                $('#myTable').bootstrapTable('refresh', {silent: true});
                tableOpera.configtoback();

            },
            error: function () {
                showMessage("request error", "danger", 1000);
            }
        });
    },
    removeCheck: function ()//checkbox被选中时显示确认按钮
    {

        if ($("#removeChe").prop("checked")) {
            $("#removevmBtn").attr("disabled", false)
        } else {
            ($("#removevmBtn").attr("disabled", true));
        }


    },
    removalInit: function (instance_ids, url)//迁移弹框数据初始化
    {
        $.ajax({
            url: url + instance_ids,
            type: "get",
            beforeSend: function () {
                //$(".migrateVmSure").attr("data-target", "#vm-removal-modal");
                $("#loading").css("display", "block");
            },
            success: function (res) {
                $("#loading").css("display", "none");
                if (res.code != 0) {
                    //showMessage("操作失败","danger",1000);
                    $("#removal-info").css("display", "none");
                    $(".migrate_text").html('没有合适的目标主机提供迁移');
                    $("#warning-text").css("display", "block");
                } else {
                    var list = res.data;
                    if ($.isEmptyObject(list) || list.host_list.length == 0) {
                        $("#removal-info").css("display", "none");
                        $(".migrate_text").html(res.msg);
                        $("#warning-text").css("display", "block");
                    } else {
                        $("#removal-info").css("display", "block");
                        $("#warning-text").css("display", "none");
                        list.instance_mem == null ? '' : list.instance_mem;
                        var instance_mem = "";
                        if (parseInt(list.instance_mem) > 1024) {
                            instance_mem = list.instance_mem / 1024 + "G";
                        } else if (0 < parseInt(list.instance_mem) < 1024) {
                            instance_mem = list.instance_mem + "M";
                        }
                        var str = "<tr>";
                        str += "<td>" + (list.instance_name == null ? '' : list.instance_name) + "</td>";
                        str += "<td>" + (list.instance_ip == null ? '' : list.instance_ip) + "</td>";
                        str += "<td>" + (list.instance_status == null ? '' : judgeStatus(list.instance_status)) + "</td>";
                        str += "<td>" + (list.instance_cpu == null ? '' : list.instance_cpu) + "核</td>";
                        str += "<td>" + instance_mem + "</td>";
                        str += "<td>" + (list.instance_disk == null ? '' : list.instance_disk) + "M</td>";
                        str += "</tr>";
                        $("#vm-removal-table").html(str);
                        var _hoststr = "";
                        var hostList = list.host_list;
                        $.each(hostList, function (index, tmp) {
                            //console.log(tmp.free_disk_space);
                            _hoststr += "<tr class='text-center'><td><input type='radio' name='vm-host-sel' value=" + tmp.host_id + "></td><td>" + tmp.host_name + "</td><td>" + tmp.current_cpu_used + "</td><td>" + tmp.current_mem_used + "</td><td>" + tmp.free_disk_space + "</td></tr>";
                        });
                        $("#target-host-detail").html(_hoststr);
                        $("#removalBtn").attr("data-instance-id", instance_ids);
                    }
                }
                $("#vm-removal-modal").modal("show");
            },
            error: function () {
                showMessage("请求错误,请刷新页面重试", "danger", 1000);
            }
        });
    },
    removalVm: function (instance_id, url, isHot)//迁移vm
    {
        var host_id = $("#target-host-detail input:checked").val(), speed_limit;
        //console.log(host_id);
        if (host_id == undefined) {
            showMessage("没有合适的目标主机提供迁移！！！", "danger", 2000);
            return;
        }
        if (isHot) {
            speed_limit = 500
        } else {
            speed_limit = $("#speed-limit input").val();
            if (speed_limit < 160) {
                showMessage("迁移速度最小160Mbit/s", "danger", 2000);
                $("#speed-limit input").val("").focus();
                return;
            }
        }

        $.ajax({
            url: url + instance_id + "/to/" + host_id,
            type: "PUT",
            //timeout: 10000,
            dataType: "json",
            data: {"speed_limit": speed_limit},
            beforeSend: function () {
                $("#loading").css("display", "block");
                $("#vm-removal-modal").modal("hide");
            },
            success: function (res) {
                $("#loading").css("display", "none");
                if (res.code != 0) {
                    res.msg != null ? showMessage(res.msg, "danger", 3000) : showMessage("操作失败", "danger", 2000);
                } else {
                    showMessage("操作成功", "success", 1000);
                }
                $('#myTable').bootstrapTable("refresh", {slient: true});
            },
            error: function () {
                showMessage("请求失败，请刷新页面重新操作", "danger", 2000);
                $("#loading").css("display", "none");
            }
        });
    },
    cloneVm: function (instance_id)//cloneVm
    {
        var params = {
            apiOrigin: 'self'
        }
        $.ajax({
            url: "/instance/clone/" + instance_id,
            type: "POST",
            dataType: "json",
            contentType: "application/json; charset=utf-8",
            data: JSON.stringify(params),
            beforeSend: function () {
                $("#loading").css("display", "block");
            },
            success: function (res) {
                $("#loading").css("display", "none");
                if (res.code != 0) {
                    res.msg != null ? showMessage(res.msg, "danger", 2000) : showMessage("操作失败请刷新重试！！！", "danger", 2000)
                } else {
                    showMessage("克隆成功", "success", 1000)
                }
                $("#vm-clone-modal").modal("hide");
                $('#myTable').bootstrapTable("refresh", {slient: true});
            },
            error: function () {
                $("#loading").css("display", "none");
                showMessage("操作失败请刷新重试！！！", "danger", 2000);
                $("#vm-clone-modal").modal("hide");
                $('#myTable').bootstrapTable("refresh", {slient: true});
            }
        });
    }
};


var createVmObject = {
    arr: [],//保存vm创建需要提交的数据
    createInfoInit: function ()//创建确认vm创建数据初始化
    {
        var arr = {};
        // flavor
        var cpu = $("#cpu-hook div.selected").html();
        var mem = $("#mem-hook div.selected").html();
        var disk = $("#disk-hook div.selected").html();

        // cluster
        var cluster = $("#cluster").val();
        if (cluster == 0) {
            showMessage('请选择集群', 'danger', 1000);
            $("#cluster").focus();
            return false;
        }
        // construct model
        var model = $("#constructmodel").val();
        if (model == '0') {
            showMessage('请选择模板', 'danger', 1000);
            $("#constructmodel").focus();
            return false;
        }

        //机房区域
        var vmarea = $("#instancePlace").children(".selected").html();
        //console.log(vmarea);

        // 网络区域
        var netarea = $("#networkarea option:selected").html();

        // 主机类型
        var constructmodelType = $("#constructmodelhook").children(".selected").html();

        //搭建模板
        var constructmodel = $("#constructmodel option:selected").html();

        // 数据盘
        var _datadisk = $("#datadisk").val();
        // 主机数量
        var _instancenumber = $("#instancenumber").val();
        // 应用系统信息
        var _appsystem = $("#appsystem").val();
        // 应用组
        var _appadmin = $("#appadmin").val();
        if (_appadmin == '暂无数据') {
            showMessage("所选环境没有可用应用组", 'danger', 600);
            return;
        }
        let group_list_check = creatinitdata['groups'];
        if (!createVmObject.blurCheckGroup("#appadmin", group_list_check)) {
            showMessage("所选应用组的名称不存在", "danger", 600)
            return;
        }
        //console.log(_appadmin);
        // 管理员工号
        var _adminname = $("#adminname").val();
        // 管理与密码
        var _adminpass = $("#adminnamepass").val().trim();
        if (_adminpass == "") {
            _adminpass = _adminpass;
        } else {
            if (!checkPassword(_adminpass)) {
                showMessage("所输密码不符合规则，请重新输入", "danger", 1200);
                $("#adminnamepass").val("");
                return;
            }
        }


        // 容灾机器数量 on type == 4
        //var disasternumberflag = $(".zbtype.selected").attr('data-id');
        //var disasternumber = undefined;
        //if(disasternumberflag === '4') {
        //    disasternumber = $("#disaster").val();
        //}

        if (!cluster || !model || !cpu || !mem || !disk || !_datadisk || !_instancenumber || !_appsystem || !_appadmin || !_adminname) {
            showMessage("请填写完整信息！", 'danger', 2000);
            return;
        }
        //验证工号输入是否合法
        // if(!validateUserId(_adminname)){
        //     showMessage("工号输入有误！", 'danger', 2000);
        //     return;
        // }


        if (!$("#appadmin").val()) {
            showMessage("请选择应用管理组", "danger", 2000);
            return;
        }
        arr["datacenter_area"] = vmarea;
        if (vmarea == "总部") {
            $("#dq_area_show").css("display", "none");
            arr["enviroment_type"] = $("#Headquarterstype").children(".selected").html();
        }
        if (vmarea == "地区") {
            $("#dq_area_show").css("display", "block");
            var area = $("#area").val();
            if ($("#subarea option").length > 1) {
                var area_child = $("#subarea").val();
                if ($("#area_child").val() == "-1") {
                    showMessage("请选择子区域", "danger", 2000);
                    return;
                }
                $(".area_child_info").css("display", "block");
                arr["area_child"] = area_child;
            }
            if (!arr["area_child"]) {
                $(".area_child_info").css("display", "none");
            }

            var datacenter = $("#engineroom").val();
            if ($("#area").val() == "-1") {
                showMessage("请选择区域", "danger", 2000);
                return;
            }

            if ($("#datacenter").val() == "-1") {
                showMessage("请选择机房", "danger", 2000);
                return;
            }
            arr["area"] = area;
            arr["datacenter"] = datacenter;
            arr["enviroment_type"] = datacenter.substring(datacenter.lastIndexOf("-") + 1);
        }
        arr["net_area"] = netarea;
        arr["host_type"] = constructmodelType;
        arr["_cpu"] = cpu;
        arr["_mem"] = mem;
        arr["_disk"] = disk;
        arr["_disk_gb"] = _datadisk + "G";
        arr["host_num"] = _instancenumber;
        arr["sys_info"] = _appsystem;
        arr["application"] = _appadmin;
        arr["_group_name"] = _adminname;
        arr["model"] = constructmodel;

        this.arr = arr;

        $("#environmentype").css("display", $("#Headquarterstype").css("display"));
        var list = $("#vmForm input");
        for (var i = 0; i < list.length; i++) {
            var input_name = $(list[i]).attr("name");
            $(list[i]).val(arr[input_name]);
        }

        $("#vmInfoSure").css("display", "block");
        $("#vmInfoSure").animate({"left": "3%"}, "slow");
        $("#secondWrapper").animate({"left": "-100%"}, "slow", function () {
            $(this).css("display", "none");
        });
    },
    vmInitInfo: function ()//vm创建弹框初始化
    {
        $.ajax(
            {
                url: '/instance/init',
                type: 'GET',
                data: {},
                //timeout: 10000,
                dataType: 'json',
                success: function (data, textStatus) {
                    if (data.code != 0) {
                        console.warn('instance/init get failed')
                        return;
                    }
                    //console.log('ajax success:', data, textStatus);
                    // flavors
                    creatinitdata = data.data;

                    var flavors = creatinitdata.flavors;
                    //cpu mem disk信息
                    createVmObject.initSome(flavors, "#cpu-hook", "#mem-hook", "#disk-hook");

                    // 模板选择
                    createVmObject.initmoban();
                    // 应用管理员
                    //createVmObject.initappadmin();
                    // cluster
                    createVmObject.initcluster();

                },
                error: function (xhr, textStatus) {
                    showMessage("请求超时,请刷新重试", "danger", 2000);
                }
            }
        )
    },
    initSome: function (flavors, cpuId, memId, diskId)//cpu mem disk信息
    {
        var cpus = [];
        var mems = [];
        var disks = [];
//                flavorparams = {
//                    cpu2mem: [],
//                    cpumem2disk: []
//                };
//                var cpu2mem = flavorparams.cpu2mem;   // cup2mem[1] = [2, 4]
//                var cpumem2disk = flavorparams.cpumem2disk;
        cpu2mem = [];
        cpumem2disk = [];

        for (var i = 0; i < flavors.length; i++) {
            var item = flavors[i];
            var cpu = item.vcpu;//cpu数量
            var mem = item.memory_mb;//内存容量
            var disk = item.root_disk_gb; //系统盘容量
            // cpus mems disks
            cpus.push(parseInt(cpu));
            mems.push(parseInt(mem));
            disks.push(parseInt(disk));

            // cpu2mem cpumem2disk
            if (!cpu2mem[cpu]) {
                cpu2mem[cpu] = [mem];
            } else {
                cpu2mem[cpu].push(mem);
            }
            if (!cpumem2disk[cpu]) {
                cpumem2disk[cpu] = {};
            }
            if (!cpumem2disk[cpu][mem]) {
                cpumem2disk[cpu][mem] = [disk];
            } else {
                cpumem2disk[cpu][mem].push(disk);
            }
        }


        // 去重
        cpus = cpus.unique().sort(function (a, b) {
            return a - b;
        });
        mems = mems.unique().sort(function (a, b) {
            return a - b;
        });
        disks = disks.unique().sort(function (a, b) {
            return a - b;
        });
        cpu2mem = cpu2mem.map(function (item, index, array) {
            return item.unique().sort(function (a, b) {
                return a - b;
            });
        })
        for (var j = 0; j < cpus.length; j++) {
            var _cpu = cpus[j];
            for (var k in cpumem2disk[_cpu]) {
                cpumem2disk[_cpu][k] = cpumem2disk[_cpu][k].unique().sort(function (a, b) {
                    return a - b;
                });
            }
        }

        CloneFun.flover_list.cpus = cpus;
        CloneFun.flover_list.mems = mems;
        CloneFun.flover_list.cpu2mem = cpu2mem;
        CloneFun.flover_list.cpumem2disk = cpumem2disk;

        //console.info(cpus, mems, disks);
        //console.warn(cpu2mem, cpumem2disk);
        // DOM操作
        $(cpuId).empty();
        $(memId).empty();
        $(diskId).empty();

        var cpudomstr = '';
        var memdomstr = '';
        var diskdomstr = '';

        for (var i = 0; i < cpus.length; i++) {
            cpudomstr += '<div class="cpu optionsmall" data-id="' + cpus[i] + '">' + cpus[i] + '核</div>'
        }
        for (var i = 0; i < mems.length; i++) {
            if (parseInt(mems[i]) < 1024) {
                memdomstr += '<div class="mem optionsmall disabled" data-id="' + mems[i] + '">' + mems[i] + 'M</div>'
            } else {
                var val = parseInt(mems[i]) / 1024;
                memdomstr += '<div class="mem optionsmall disabled" data-id="' + mems[i] + '">' + val + 'G</div>'
            }
        }

        if (disks.length === 1) {
            for (var i = 0; i < disks.length; i++) {
                diskdomstr += '<div class="disk optionsmall selected" data-id="' + disks[i] + '">' + disks[i] + 'G</div>'
            }
        } else {
            for (var i = 0; i < disks.length; i++) {
                diskdomstr += '<div class="disk optionsmall disabled" data-id="' + disks[i] + '">' + disks[i] + 'G</div>'
            }
        }


        //初始化cpu 内存 系统盘容量信息
        $(cpuId).html(cpudomstr);
        $(memId).html(memdomstr);
        $(diskId).html(diskdomstr);
    },
    initmoban: function () //搭建模板信息
    {
        if (creatinitdata) {
            var _linux = creatinitdata['images_linux'];

            var _win = creatinitdata['images_windows'];
            _linux = tableOpera.removeRepeat(_linux);
            _win = tableOpera.removeRepeat(_win);
            //console.log(_linux);
            $("#constructmodel option:not(:first-child)").remove();
            var _linuxstr = '';
            for (var i in _linux) {
                _linuxstr += '<option value="' + i + '">' + _linux[i] + '(' + i + ')</option>';

            }
            //for (var i = 0; i < _linux.length; i++) {
            //    _linuxstr += '<option value="' + _linux[i]['name'] + '">' + _linux[i]['displayname'] + '(' + _linux[i]['name'] + ')</option>';
            //}
            $("#constructmodel").append(_linuxstr);
        }
    },
    initdatadisk: function ()//数据盘容量员信息生成
    {
        var arr = [];
        for (var i = 50; i <= 500; i = i + 50) {
            arr.push(i);
        }
        var _str = '';
        for (var i = 0; i < arr.length; i++) {
            _str += '<option value="' + arr[i] + '">' + arr[i] + 'G' + '</option>';
        }
        $("#datadisk").html(_str);
    },
    initappadmin: function (that, list, id)//应用管理员信息生成 keyUp
    {
        if (list) {
            let new_group = $(that).val(),
                _str = '',
                all_str = '';
            for (var i = 0; i < list.length; i++) {
                let groupName = ''
                if (list[i]['name']) {
                    groupName = list[i]['name']
                } else if (list[i]['group_name']) {
                    groupName = list[i]['group_name']
                }
                if (groupName.toLowerCase().indexOf(new_group.toLowerCase()) >= 0) {
                    _str += '<li data-id="' + list[i]['group_id'] + '">' + groupName + '</li>';
                }
                all_str += '<li data-id="' + list[i]['group_id'] + '">' + groupName + '</li>';
            }
            if (!new_group) {
                $(id).html(all_str);
            } else {
                if (!_str) {
                    $(id).html('<li>暂无数据</li>');
                } else {
                    $(id).html(_str);
                }
            }
        }
    },
    focusGroupInfo: function (list, id)  // 获取焦点时生成组信息
    {
        var groupStr = '';
        for (var i = 0; i < list.length; i++) {
            if (list[i]['name']) {
                groupName = list[i]['name']
            } else if (list[i]['group_name']) {
                groupName = list[i]['group_name']
            }
            groupStr += '<li data-id="' + list[i]['group_id'] + '">' + groupName + '</li>';
        }
        if (!groupStr) {
            $(id).html('<li>暂无数据</li>');
        } else {
            $(id).html(groupStr);
        }

    },
    blurCheckGroup: function (that, list) { // 失去焦点之后验证组信息是否正确
        var groupDefaultName = $(that).val(), deg = false;
        for (var i = 0; i < list.length; i++) {
            let groupName = ''
            if (list[i]['name']) {
                groupName = list[i]['name']
            } else if (list[i]['group_name']) {
                groupName = list[i]['group_name']
            }
            if (groupName == groupDefaultName) { // 所选应用组存在
                deg = true
            }
        }
        return deg
    },
    initcluster: function ()//联动信息
    {
        if (creatinitdata) {
            var areadq = creatinitdata['area_DQ'];
            var areazb = creatinitdata['area_ZB'];
            var dcmap = allEnvArr;
            // 0        1            2             3          4           5
            dcparams = {};

            dqparams = {
                nonesub: {  // child_area_name字段为null
                    body: [],
                    toengineroom: {},
                    tonetarea: {},
                    tocluster: {}
                },
                hassub: {
                    body: [],
                    tonext: {},
                    toengineroom: {},
                    tonetarea: {},
                    tocluster: {}
                }
            };
            if (areazb.length != 0) {
                var zbtypearr = [];
                var zbtypestr = '';
                $("#Headquarterstype div").remove();

                for (var i = 0; i < areazb.length; i++) {
                    //console.log(areazb[i]);
                    zbtypearr.push(areazb[i]['dc_type']);
                }

                zbtypearr = zbtypearr.unique();
                //zbtypearr = ["1","2","3"];

                if (role_id_arr.indexOf(2) != -1) {
                    if (zbtypearr.indexOf("3") != -1) {
                        zbtypestr += '<div class="optionlarge zbtype" data-id="3">  DEV </div>';
                    }
                } else {
                    for (var j = 0; j < zbtypearr.length; j++) {
                        //console.log(zbtypearr[j]);
                        zbtypearr[j] != null && (zbtypestr += '<div class="optionlarge zbtype" data-id="' + zbtypearr[j] + '">' + dcmap[zbtypearr[j]] + '</div>')
                    }
                }
                $("#instancePlace").children(":first-child").addClass("selected").siblings().removeClass("selected");
                $("#Headquarterstype").append(zbtypestr);
            }

            // dc
            if (areadq.length != 0) {
                for (var i = 0; i < areadq.length; i++) {
                    var item = areadq[i];
                    if (item['child_area_name']) // child_area_name 不为空
                    {
                        var name = item['area_name'] || '';
                        var next = item['child_area_name'] || '';
                        var enviroment_arr = allEnvArr;
                        var datacenter_name = item['datacenter_name'] + "-" + enviroment_arr[parseInt(item['dc_type'])];
                        var room = datacenter_name || '';
                        var net = item['net_area_name'] || '';
                        var cluster = {
                            name: item['hostpool_name'],
                            id: item['hostpool_id']
                        }
                        var name2 = name + next;
                        var name3 = name + next + room;
                        var name4 = name + next + room + net;

                        dqparams.hassub.body.push(name);

                        // 地区 -> 子区域
                        if (!dqparams.hassub.tonext[name]) {
                            dqparams.hassub.tonext[name] = [next];
                        } else {
                            dqparams.hassub.tonext[name].push(next);
                        }
                        // 地区 -> 机房
                        if (!dqparams.hassub.toengineroom[name2]) {
                            dqparams.hassub.toengineroom[name2] = [room];
                        } else {
                            dqparams.hassub.toengineroom[name2].push(room);
                        }
                        // 地区 -> 网络
                        if (!dqparams.hassub.tonetarea[name3]) {
                            dqparams.hassub.tonetarea[name3] = [net];
                        } else {
                            dqparams.hassub.tonetarea[name3].push(net);
                        }
                        // -> 集群
                        if (!dqparams.hassub.tocluster[name4]) {
                            dqparams.hassub.tocluster[name4] = [cluster];
                        } else {
                            dqparams.hassub.tocluster[name4].push(cluster);
                        }
                        //console.log(dqparams+"有子区域");

                    } else // 没有子区域
                    {
                        var name = item['area_name'] || '';
                        var enviroment_arr = allEnvArr;
                        var room = item['datacenter_name'] + "-" + enviroment_arr[parseInt(item['dc_type'])] || '';
                        var name2 = name + room;
                        var net = item['net_area_name'];
                        var name3 = name + room + net;
                        var cluster = {
                            name: item['hostpool_name'],
                            id: item['hostpool_id']
                        }
                        dqparams.nonesub.body.push(name);
                        // 地区 -> 机房
                        if (!dqparams.nonesub.toengineroom[name]) {
                            dqparams.nonesub.toengineroom[name] = [room]
                        } else {
                            dqparams.nonesub.toengineroom[name].push(room);
                        }
                        // 地区+机房 -> 网络
                        if (!dqparams.nonesub.tonetarea[name2]) {
                            dqparams.nonesub.tonetarea[name2] = [net];
                        } else {
                            dqparams.nonesub.tonetarea[name2].push(net);
                        }
                        // 地区+机房+网络 -> 集群
                        if (!dqparams.nonesub.tocluster[name3]) {
                            dqparams.nonesub.tocluster[name3] = [cluster];
                        } else {
                            dqparams.nonesub.tocluster[name3].push(cluster);
                        }
                    }
                }
            }
            //console.log(areadq.length);
            //console.log(areazb.length);

            if (areadq.length == 0) {
                $(".zbsel-a").css("display", "block").addClass("selected");
                $(".zbsel").css("display", "block");
                $(".dqsel-a").css("display", "none").removeClass("selected");
                $(".dqsel").css("display", "none");
            }
            if (areazb.length == 0) {
                $(".zbsel-a").css("display", "none").removeClass("selected");
                $(".zbsel").css("display", "none");
                $(".dqsel-a").css("display", "block").addClass("selected");
                $(".dqsel").css("display", "block");
                $("#subarea option:not(:first-child)").remove();
                $("#engineroom option:not(:first-child)").remove();
                $("#networkarea option:not(:first-child)").remove();
                $("#cluster option:not(:first-child)").remove();
                var dqarr = [].concat(dqparams.hassub.body, dqparams.nonesub.body);
                var dqstr = '';
                dqarr = dqarr.unique();
                for (var i = 0; i < dqarr.length; i++) {
                    dqstr += '<option value="' + dqarr[i] + '">' + dqarr[i] + '</option>';
                }
                $("#area option:not(:first-child)").remove();
                $("#area").append(dqstr);
            }
            $(".subarea_show").css("display", "none");
            if (areadq.length == 0 && areazb.length == 0) {
                return false;
            }
            return true;
        }
    },
    configadd: function (thisdiv, id, id1, id2)//修改配置信息
    {
        !$(thisdiv).hasClass('disabled') && $(thisdiv).addClass('selected').siblings().removeClass('selected');
        if ($(thisdiv).hasClass('cpu')) {
            var cpuval = $(thisdiv).attr('data-id');
            //console.log(cpuval);
            var memarr = cpu2mem[cpuval];
            //console.log('click cpu', cpu2mem);
            $(id1 + " div").each(function (i) {
                //console.log($(this));
                var itemval = $(this).attr('data-id');
                if (memarr.indexOf(parseInt(itemval)) != '-1') {
                    $(this).removeClass('disabled selected');
                } else {
                    $(this).removeClass('selected').addClass('disabled');
                }
            })
            $(id2 + " div").addClass("disabled");
        } else if ($(thisdiv).hasClass('mem')) {
            if ($(thisdiv).hasClass('disabled')) return;
            var _cpuval = $(id + " div.selected").attr('data-id');
            var _memval = $(id1 + " div.selected").attr('data-id');
//                var _diskarr = flavorparams.cpumem2disk[_cpuval][_memval];
//                console.log($(id+" div.selected"),$(id1+" div.selected"),_cpuval,_memval);
            var _diskarr = cpumem2disk[_cpuval][_memval];
            //console.log('click mem', _cpuval, _memval, _diskarr);
            $(id2 + " div").each(function (j) {
                //console.log($(this));
                //console.log($(id2));
                var _itemval = $(this).attr('data-id');
                if (_diskarr.indexOf(parseInt(_itemval)) != '-1') {
                    $(this).removeClass('disabled');
                } else {
                    $(this).addClass('disabled');
                }
            })
        }
    }
};


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
};

//校验用户输入工号信息
function validateUserId() {
    var userId = arguments[0];
    if (userId.length !== 6 && userId.length !== 8) {
        return false;
    }
    if (!checkNumber(userId)) {
        return false;
    }
    return true;
};

//验证字符串是否是数字
function checkNumber(theObj) {
    var reg = /^[0-9]+.?[0-9]*$/;
    if (reg.test(theObj)) {
        return true;
    }
    return false;
};

//删除模板
$("#downloadBtn").click(function () {
    // download();
    var url = '/instance/del_template';
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);    // 也可以使用POST方式，根据接口
    xhr.responseType = "blob";  // 返回类型blob
    // 定义请求完成的处理函数，请求前也可以增加加载框/禁用下载按钮逻辑
    xhr.onload = function () {
    // 请求完成
    if (this.status === 200) {
      // 返回200
      var blob = this.response;
      var reader = new FileReader();
      reader.readAsDataURL(blob);  // 转换为base64，可以直接放入a表情href
      reader.onload = function (e) {
        // 转换完成，创建一个a标签用于下载
        var a = document.createElement('a');
        a.download = 'data.xls';
        a.href = e.target.result;
        $("body").append(a);  // 修复firefox中无法触发click
        a.click();
        $(a).remove();
      }
    }
  };
  // 发送ajax请求
  xhr.send()
});

//批量删除
$("#pushFile").change(function () {
    var fileObj = document.getElementById("pushFile").files[0]; // js 获取文件对象
    var url =  "/instance/del_upload_ins"; // 接收上传文件的后台地址

    var form = new FormData(); // FormData 对象
    form.append("file", fileObj); // 文件对象

    $("#pushFile").val("");  //删除文件

    xhr = new XMLHttpRequest();  // XMLHttpRequest 对象
    xhr.open("DELETE", url, true); //post方式，url为服务器请求地址，true 该参数规定请求是否异步处理。
    xhr.onload = uploadComplete; //请求完成
    xhr.onerror =  uploadFailed; //请求失败
    xhr.send(form); //开始上传，发送form数据

})
//上传成功响应
function uploadComplete(evt) {
    //服务断接收完文件返回的结果
    var data = JSON.parse(evt.target.responseText);
    if(data.code == 0) {
        console.log("批量删除成功！");
        alert("批量删除成功！")
    }else{
        alert(data.msg);
        console.log(data.msg);
    }

}
//上传失败
function uploadFailed(evt) {
    var data = JSON.parse(evt.target.responseText);
    alert(data.msg);
}