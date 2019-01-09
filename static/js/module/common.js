/**
 * Created by 833903 on 2017/3/24.
 */
function showMessage( mes, type, time) {
    $.bootstrapGrowl(mes, {
        ele: 'body', // which element to append to
        type: type, // (null, 'info', 'danger', 'success')
        offset: {from: 'top', amount: 57}, // 'top', or 'bottom'
        align: 'center', // ('left', 'right', or 'center')
        width: 'auto', // (integer, or 'auto')
        delay: time*5, // Time while the message will be displayed. It's not equivalent to the *demo* timeOut!
        allow_dismiss: true, // If true then will display a cross to close the popup.
        stackup_spacing: 10 // spacing between consecutively stacked growls.
    });
}
function blurCheckGroup(that,list){ // 失去焦点之后验证组信息是否正确
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
    }

function focusGroupInfo(list, id)  // 获取焦点时生成组信息
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

    }
// 应用组模糊查询生成信息
function initAdmin(that, list, id)//应用管理员信息生成
    {
        if (list) {
            let new_group = $(that).val(),
                _str = '',
                all_str = '';
            for (var i = 0; i < list.length; i++) {
                let groupName = ''
                if (list[i]['name']) {
                    groupName = list[i]['name']
                } else if(list[i]['group_name']) {
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
    }
function initAdminObj(that, list, id)//应用管理员信息生成
    {
        if (list) {
            let new_group = $(that).val(),
                _str = '',
                all_str = '';
            for (var i in list) {
                let groupName = list[i][0][0]
                if (groupName.toLowerCase().indexOf(new_group.toLowerCase()) >= 0) {
                    _str += '<li data-id="' + list[i][0][1] + '">' + groupName + '</li>';
                }
                all_str += '<li data-id="' + list[i][0][1] + '">' + groupName + '</li>';
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
    }
//去重方法
Array.prototype.unique = function(){
     var res = [];
     var json = {};
     for(var i = 0; i < this.length; i++){
      if(!json[this[i]]){
       res.push(this[i]);
       json[this[i]] = 1;
      }
     }
     return res;
};

//判断input是否为空值
function isEmpty(id,name){
     var list=$(id);
             var listLength=list.length;
            for(var i=0;i<listLength;i++){
                if(list[i].name == name ) continue;
                if(list[i].value==''){
                    list[i].focus();
                    showMessage("请填写完整信息！！！","danger",1000);
                    return false;
                }
            }
            return true;

}
// 环境集合
allEnvArr = ['其他', 'SIT', 'STG', 'DEV', 'PRD', 'DR', "MINIARCHDR", 'TENCENTDR','PST','IST'];
allEnvArrChinese = ['其他', '测试SIT', '准生产STG', '研发DEV', '生产PRD', '容灾DR', '容灾微应用', '腾讯云双活','容灾压测PST','测试压测IST'];
allEnvArrNo =  ['', 'SIT', 'STG', 'DEV', 'PRD', 'DR', "MINIARCHDR", 'TENCENTDR','PST','IST'];