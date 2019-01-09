/**
 * Created by 80002473 on 2017/7/6.
 */
window.onload = function () {
    init_table();
    $("#image-create-show").click(function(){
        addImageInfo.image_info_init()
        $("#addImageModal").modal('show')
    })
}

function init_table() {
    $('#image_list').bootstrapTable({
        url: '/image/list',
        method: 'GET',
        dataType: "json",
        detailView: false,
        uniqueId: "image_id", //删除时能用到 removeByUniqueId
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
        clickToSelect: false,
        singleSelect: false,
        onBeforeLoadParams: {},//查询参数设置，供导出使用，在search_form.js里赋值
        sortable: false,
        responseHandler: function (res) {
            if (res.code == 0) {
                return res.data;
            } else {
                return null;
            }
        },
        queryParams: function (q) {
            var searchContent = q.searchText;
            return {
                "page_size": q.pageSize,
                "page_no": q.pageNumber
            };
        },
        onLoadSuccess: function ($element) {

        },
        onClickRow: function ($element, row) {
        },
        columns: [
            {
                checkbox: true
            },
            {
                title: "镜像显示名称",
                field: "displayname",
                align: "left",
            },
            {
                title: "操作系统",
                field: "system",
                align: "left",
            },
            {
                title: "版本",
                field: "version",
                align: "left",
            },
            {
                title: "创建时间",
                field: "create_time",
                align: "left",
                formatter: function (value, row, index) {
                    var create_time = value;
                    var date = new Date(create_time).toISOString().replace(/T/g, ' ').replace(/\.[\d]{3}Z/, '');
                    create_time = date.substring(0, date.lastIndexOf(":"));
                    return create_time;
                }
            },
            {
                title: "描述",
                field: "description",
                align: "left",
            },
            {
                title: "操作",
                field: "operation",
                align: "left",
                events: operateEvents,
                formatter: operateFormatter
            }
        ]
    })
};

function operateFormatter(value, row, index) {
    return [
        '<a title="同步镜像" class="edit-image"><i class="fa fa-edit"></i></a>',
    ].join('');
}

window.operateEvents = {
    "click .edit-image": function (e, value, row, index) {
        $("#edit_display_name").val(row.displayname).attr("data-image-id", row.image_id);
        $("#edit_md5").val(row.md5);
        $("#edit_actual_size_mb").val(row.actual_size_mb);
        $("#edit_size_gb").val(row.size_gb);
        $("#editImageModal").modal('show')
    }
};

var addImageInfo = {
    image_info_init: function () {
        let input_list = $("#addImageModal input")
        let select_list = $("#addImageModal select")
        input_list.each(function(index,item){
            $(item).val('')
        })
        select_list.each(function(index,item){
            $(item).val('-1')
        })
        $("#new_system").val("1")
    },
    changeSystem: function () {
        var system = document.getElementById("new_system").value;
        var new_version_linux = document.getElementById("new_version_linux");
        var new_version_win = document.getElementById("new_version_win");

        if (system == "1") {
            new_version_linux.style.display = "block";
            new_version_win.style.display = "none";
        }else if (system == "2") {
            new_version_linux.style.display = "none";
            new_version_win.style.display = "block";
        }
    },
    add_image: function () {
        var new_displayname = $("#new_displayname").val();
        var new_system = $("#new_system option:selected").html();
        var new_file = $("#new_file").val();
        if (new_system == "linux") {
            var new_version = $("#new_version_linux").val();
        }
        if (new_system == "windows") {
            var new_version = $("#new_version_win").val();
        }
        if (new_version == -1) {
            showMessage("请选择系统版本", "danger", 200);
            return;
        }
        if (new_file == '') {
            showMessage("请选择文件路径", "danger", 200);
            return;
        }

        var new_name = $("#new_name").val();

        if (new_name == '') {
            showMessage("镜像名不能为空", "danger", 200);
            return;
        }
        if (new_displayname == '') {
            showMessage("镜像显示名不能为空", "danger", 200);
            return;
        }
        if (new_name.match(/[\u4e00-\u9fa5]/g)) {
            showMessage("镜像名不能使用中文", "danger", 200);
            return;
        }
        var image_type = $("#new_type").val()
        if (image_type == -1) {
            showMessage('请选择镜像类型', 'danger', 200)
            return;
        }
        var new_format = $("#new_format").val()
        if (new_format == '-1') {
            showMessage('请选择镜像格式', 'danger', 200)
            return;
        }
        var new_md5 = $("#new_md5").val()
        if (new_md5 == '') {
            showMessage('请输入镜像md5', 'danger', 200)
            return;
        }

        var new_actual_size_mb = $("#new_actual_size_mb").val()
        if (!parseFloat(new_actual_size_mb)) {
            showMessage('镜像实际大小输入不正确,请重新输入', 'danger', 200)
            return;
        }

        var new_size_gb = $("#new_size_gb").val()
        if (!parseFloat(new_size_gb)) {
            showMessage('镜像大小输入不正确,请重新输入', 'danger', 200)
            return;
        }
        if (parseFloat(new_actual_size_mb) > parseFloat(new_size_gb) * 1024) {
            showMessage('镜像大小不能小于镜像实际大小', 'danger', 200)
            return;
        }
        let params = {
            'name':  new_name,
            'displayname': new_displayname,
            'system': new_system,
            'version': new_version,
            'md5': new_md5,
            'format': new_format,
            'actual_size_mb': new_actual_size_mb,
            'size_gb': new_size_gb,
            'url': new_file,
            'type': image_type
        }
        $.ajax({
            url: "/image",
            type: "POST",
            dataType: "json",
            data: params,
            success: function (req) {
                if (req.code != 0) {
                    req.msg != null ? showMessage(req.msg, "danger", 600) : showMessage("新建镜像失败", "danger", 1200);
                } else {
                    showMessage("新建镜像成功", "success", 200);
                    $("#image_list").bootstrapTable('refresh', {silent: true});
                    $("#addImageModal").modal("hide");
                }
            },
            error: function () {
                showMessage("新建镜像请求失败", "danger", 600);
            }
        });
    }
};

function editImage () {
    let image_id = $("#edit_display_name").attr("data-image-id");
    let actual_size_mb = $("#edit_actual_size_mb").val();
    let md5 = $("#edit_md5").val();
    let size_gb = $("#edit_size_gb").val();
    if (!actual_size_mb || !md5 || !size_gb) {
        showMessage('请完善信息再提交', 'danger', 600);
        return;
    }
    if (!parseFloat(size_gb)) {
        showMessage('镜像大小输入不正确,请重新输入', 'danger', 200)
        return;
    }
    if (parseFloat(actual_size_mb) > parseFloat(size_gb) * 1024) {
        showMessage('镜像大小不能小于镜像实际大小', 'danger', 200)
        return;
    }
    $.ajax({
        url: '/image',
        type: 'put',
        data: {
           'image_id':  image_id,
           'actual_size_mb':  actual_size_mb,
           'size_gb':  size_gb,
           'md5':  md5,
        },
        success: function (req) {
            if (req.code != 0) {
                req.msg != null ? showMessage(req.msg, "danger", 600) : showMessage("编辑镜像失败", "danger", 600);
            } else {
                showMessage("编辑镜像成功", "success", 600);
                $("#image_list").bootstrapTable('refresh', {silent: true});
                $("#editImageModal").modal("hide");
            }
        }
    })

}





