/**
 * Created by fengxingwang on 2017/8/22.
 * 文件上传公共组件，依赖bootstrap fileinput插件
 *
 */

let initFileInput = (uploadId, uploadUrl)=> {
    let control = $('#' + uploadId);
    control.fileinput({
        uploadUrl: uploadUrl,//上传的地址
        uploadAsync: true,
        language: "zh",//设置语言
        showCaption: true,//是否显示标题
        showUpload: true, //是否显示上传按钮
        showPreview: false,//是否显示预览图
        browseClass: "btn btn-primary", //按钮样式
        allowedFileExtensions: ["xls", "xlsx"], //接收的文件后缀
        maxFileCount: 11,//最大上传文件数限制
        uploadAsync: true,
        previewFileIcon: '<i class="glyphicon glyphicon-file"></i>',
        allowedPreviewTypes: null,
        previewFileIconSettings: {
            'docx': '<i class="glyphicon glyphicon-file"></i>',
            'xlsx': '<i class="glyphicon glyphicon-file"></i>',
            'pptx': '<i class="glyphicon glyphicon-file"></i>',
            'jpg': '<i class="glyphicon glyphicon-picture"></i>',
            'pdf': '<i class="glyphicon glyphicon-file"></i>',
            'zip': '<i class="glyphicon glyphicon-file"></i>',
        },
        uploadExtraData: ()=> {
            var extraValue = null;
            var radios = document.getElementsByName('excelType');
            for (var i = 0; i < radios.length; i++) {
                if (radios[i].checked) {
                    extraValue = radios[i].value;
                }
            }
            return {"excelType": extraValue};
        }
    });
    control.on("fileuploaded", (event, data, previewId, index)=> {
        let returnCode = data.response.code + '';
        if (returnCode == '0') {
            showMessage("批量上传成功！", "info", 2000);
            window.location.href="/kvm/migrate.html"
        } else {
            let errorMsg = data.response.data;
            showMessage(data.response.msg, "danger", 2000);
            if (errorMsg) {
                let msg = '';
                for (let elem of errorMsg.values()) {
                    msg += elem + '<br>';
                }
                $('.modalContent').html(msg);
                $('#uploadError').modal("show");
            }
            $(".kv-file-remove").click();
        }
    });
}


export default {initFileInput}