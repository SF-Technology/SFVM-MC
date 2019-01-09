/**
 * Created by 80002473 on 2017/8/30.
 */

function setSearchType(id, arr,str) {
    var html = '<select name="" id="' + id + '" class="form-inline searchTableRecord"><option value="-1">'+str+'</option>';
    for (var i = 0, len = arr.length; i < len; i++) {
        html += '<option value="' + arr[i] + '">' + arr[i] + '</option>'
    }
    html += '</select>';
    return html;
}
$("#record-start-time").datetimepicker({
    format: 'yyyy-mm-dd hh:ii:ss',//日期的格式
    autoclose: true,//日期选择完成后是否关闭选择框
    bootcssVer: 3,//显示向左向右的箭头
    language: 'zh_CN',//语言
    minView: 0,//表示日期选择的最小范围，默认是hour
    todayBtn: true,
    startTime: new Date()
}).on("changeDate", function () {
    var userStartTime = $("#record-start-time").val();
    userStartTime = new Date(userStartTime).getTime();
    $("#record-end-time").datetimepicker("setStartDate", new Date(userStartTime));
});
;
$("#record-end-time").datetimepicker({
    format: 'yyyy-mm-dd hh:ii:ss',//日期的格式
    autoclose: true,//日期选择完成后是否关闭选择框
    bootcssVer: 3,//显示向左向右的箭头
    language: 'zh_CN',//语言
    minView: 0,//表示日期选择的最小范围，默认是hour
    todayBtn: true
});
function initTable() {
    $('#recordTable').bootstrapTable({
        url: '/operation/list',
        method: 'get',
        dataType: "json",
        toolbar: '#toolbar',
        detailView: false,
        uniqueId: "id",//删除时能用到 removeByUniqueId
        queryParamsType: "search",
        showRefresh: true,
        contentType: "application/x-www-form-urlencoded",
        pagination: true,
        pageList: [10, 20, 50, 100, "all"],
        pageSize: 10,
        pageNumber: 1,
        search: false, //不显示全表模糊搜索框
//            searchText: getQueryString('search'),
//        showColumns: true, //不显示下拉框（选择显示的列）
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
            var key = JSON.stringify(searchFun.data);
            return {
                "page_size": q.pageSize,
                "page_no": q.pageNumber,
                "search": key
            };
        },
        onLoadSuccess: function (data) {
        },
        onClickCell: function (field, value, row, $element) {
        },
        onClickRow: function ($element, row) {
//                console.log(row);

        },
        onCheckAll: function () {

        },
        onUncheckAll: function () {

        },
        onCheck: function () {

        },
        onUncheck: function () {
        },
        columns: [
            {
                title: "操作用户",
                field: "operator",
                align: "left",
                width: '120',
                class: 'cellWidth'
            },
            //{
            //    title: "用户IP",
            //    field: "operator_ip",aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
            //    align: "left",
            //    class: "click"
            //},
            {
                title:  setSearchType(
                    "operateObj", ["登录/登出", "区域", "机房",
                        "网络区域", "集群", "HOST", "VM", "IP", "应用组"],
                    '操作对象'
                ),
                field: "operation_object",
                align: "left",
                width: '120',
                class: 'cellWidth'
            },
            {
                title: setSearchType(
                    "operatType", searchFun.showTypeArr,
                    '操作类型'
                ),
                field: "operation_action",
                align: "left",
                width: '120',
                class: 'cellWidth'
            },
             {
                title: "操作IP",
                field: "operator_ip",
                align: "left",
                width: '120',
                class: 'cellWidth'
            },
            {
                title: "操作时间",
                field: "operation_date",
                align: "left",
                width: '120',
                class: 'littleStyle'
            },
            {
                title: "操作结果",
                field: "operation_result",
                align: "left",
                width: '120',
                class: 'littleStyle'
            },
            {
                title: "描述详情",
                field: "extra_data",
                align: "left",
                cellStyle: function (value, row, index) {
                    return {
                        css: {
                            "max-width": "300px",
                            "word-wrap": "break-word",
                            "word-break": "normal",
                        }
                    };
                },
                class: 'smallStyle'
            }
        ]
    });
}
window.onload = function () {
    initTable();
    $("#searchBtn").click(function () {
        var result1;
        searchFun.data.start_time = $("#record-start-time").val(),
            searchFun.data.end_time = $("#record-end-time").val();
        //var patt1 = new RegExp("^(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|[1-9])\\." + "(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|\\d)\\." + "(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|\\d)\\." + "(1\\d{2}|2[0-4]\\d|25[0-5]|[1-9]\\d|\\d)$");
        searchFun.data.operation_object == "-1" && delete data["operation_object"];
        searchFun.data.operation_action == "-1" && delete data["operation_action"];

        for (var i in searchFun.data) {
            if (!searchFun.data[i]) {
                delete searchFun.data[i];
            }
            //else{
            //    i == "operator_ip" && (result1 = patt1.test(operator_ip));
            //}
        }
        if (result1) {
            showMessage("IP格式不正确", "danger", 2000);
            return;
        }
        $('#recordTable').bootstrapTable('refresh');
    });
    $(".searchBox").on("keyup", ".searchRecord", function () {
        var id = $(this).attr("id");
        var that = this
        switch (id) {
            case "operator":
                searchFun.operator(that);
                break;
            case "record-extra-data":
                searchFun.extraData(that);
                break;
        }
    });
    $("#recordTable").on("change", ".searchTableRecord", function () {
        var id = $(this).attr("id");
        var that = this
        switch (id) {
            case "operateObj":
                searchFun.operateObj(that);
                break;
            case "operatType":
                searchFun.operatType(that);
                break;
        }
    });

};
var searchFun = {
    data: {},
    operatTypeArr: {
        "login": ["登录", "登出"],
        "area": ["新增", "修改", "删除"],
        "datacenter": ["新增", "修改", "删除"],
        "netArea": ["新增", "修改", "删除"],
        "hostpool": ["新增", "修改", "删除"],
        "host": ["新增", "修改", "删除","锁定", "维护", "其他操作"],
        "vm": ["修改", "删除", "新增", "开机", "关机", "迁移", "克隆", "打开控制台"],
        "ip": ["申请IP", "保留IP", "初始化IP", "取消保留IP", "取消初始化IP"],
        "group": ["新增", "修改", "删除","移除用户", "新增域用户", "新增外部用户"]
    },
    initialTypeArr: ["登录", "登出", "新增", "修改",
        "删除", "创建", "开机", "迁移", "克隆", "锁定",
        "维护", "移除用户", "新增域用户", "新增外部用户",
        "申请IP", "保留IP", "初始化IP", "打开控制台",
        "取消保留IP", "取消初始化IP", "物理机批量操作"
    ],
    showTypeArr: ["登录", "登出", "新增", "修改",
        "删除", "创建", "开机", "迁移", "克隆", "锁定",
        "维护", "移除用户", "新增域用户", "新增外部用户",
        "申请IP", "保留IP", "初始化IP", "打开控制台",
        "取消保留IP", "取消初始化IP", "物理机批量操作"
    ],
    operator: function (that) {
        this.data.operator = $(that).val();
        $('#recordTable').bootstrapTable('refresh');
    },
    extraData: function (that) {
        this.data.extra_data = $(that).val();
        $('#recordTable').bootstrapTable('refresh');
    },
    operateObj: function (that) {
        var val = $(that).val();
        this.data.operation_action = ""
        if (val == "-1") {
            this.data.operation_object = ""
            this.showTypeArr = this.initialTypeArr
        } else {
            this.data.operation_object = val
            switch (val) {
                case "登录/登出":
                    this.showTypeArr = this.operatTypeArr.login;
                    break;
                case "区域":
                    this.showTypeArr = this.operatTypeArr.area;
                    break;
                case "机房":
                    this.showTypeArr = this.operatTypeArr.datacenter;
                    break;
                case "网络区域":
                    this.showTypeArr = this.operatTypeArr.netArea;
                    break;
                case "集群":
                    this.showTypeArr = this.operatTypeArr.hostpool;
                    break;
                case "HOST":
                    this.showTypeArr = this.operatTypeArr.host;
                    break;
                case "VM":
                    this.showTypeArr = this.operatTypeArr.vm;
                    break;
                case "IP":
                    this.showTypeArr = this.operatTypeArr.ip;
                    break;
                case "应用组":
                    this.showTypeArr = this.operatTypeArr.group;
                    break;
                default:
                    this.showTypeArr = this.initialTypeArr
            }
        }
        var str ="<option value='-1'>操作类型</option>"
        for (var i = 0, len = this.showTypeArr.length; i < len; i++) {
            str += "<option value=" + this.showTypeArr[i] + ">" + this.showTypeArr[i] + "</option>"
        }
        $("#operatType").html(str);
        $('#recordTable').bootstrapTable('refresh');
    },
    operatType: function (that) {
        var val = $(that).val();
        if (val == "-1") {
            this.data.operation_action = ""
        } else {
            this.data.operation_action = val
        }
        $('#recordTable').bootstrapTable('refresh');
    }
}