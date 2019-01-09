/**
 * Created by lisiyuan on 2017/3/22.
 */

function initNav()
{
    var nav = "";
    nav += '<div class="sidebar-collapse">'
    nav += '  <ul class="nav metismenu" id="side-menu">'
    nav += '    <li class="nav-header">'
    nav += '      <div class="dropdown profile-element">'
    nav += '        <img alt="image" class="img-circle" src="img/IMG20.png" style="width: 48px;height:48px;background: #fff"/>'
    nav += '        <a data-toggle="dropdown" class="dropdown-toggle" href="index.html">'
    nav += '          <span class="clear">'
    nav += '            <span class="block m-t-xs"> <strong id="login_user_name" class="font-bold">未登录</strong></span>'
    nav += '            <span class="text-muted text-xs block">Cloud<b class="caret"></b></span>'
    nav += '          </span>'
    nav += '        </a>'
    nav += '        <ul class="dropdown-menu animated fadeInRight m-t-xs">'
    nav += '          <li onclick="logout()"><a>Logout</a></li>'
    nav += '        </ul>'
    nav += '      </div>'
    nav += '      <div class="logo-element">'
    nav += '        IN+'
    nav += '      </div>'
    nav += '    </li>'
    nav += '    <li>'
    nav += '      <a  href="index.html" class="role-index">'
    nav += '        <span class="nav-label">概览</span></a>'
    nav += '      </a>'
    nav += '    </li>'
    nav += '    <li id="area-menu">'
    nav += '      <a href="">'
    nav += '        <span class="nav-label">区域管理</span><span class="fa arrow"></span>'
    nav += '      </a>'
    nav += '      <ul class="nav nav-second-level collapse">'
    nav += '        <li title="area" class="active"><a href="area.html">区域</a></li>'
    nav += '        <li title="datacenter"><a href="datacenter.html">机房</a></li>'
    nav += '        <li title="net_area"><a href="net_area.html">网络区域</a></li>'
    nav += '        <li title="hostpool"><a href="hostpool.html">集群</a></li>'
    nav += '      </ul>'
    nav += '    </li>'
    nav += '    <li id="source-menu">'
    nav += '      <a href="">'
    nav += '        <span class="nav-label">资源管理 </span><span class="fa arrow"></span>'
    nav += '      </a>'
    nav += '      <ul class="nav nav-second-level collapse">'
    nav += '        <li title="host" class="active"><a href="host.html">HOST</a></lititle>'
    nav += '        <li title="instance"><a href="vm.html">VM</a></li>'
    nav += '        <li title="ip"><a href="ip.html">IP</a></li>'
    nav += '      </ul>'
    nav += '    </li>'
     nav += '    <li id="mirror-menu">'
    nav += '      <a href="">'
    nav += '        <span class="nav-label">镜像</span><span class="fa arrow"></span>'
    nav += '      </a>'
    nav += '      <ul class="nav nav-second-level collapse">'
    nav += '        <li title="image"><a href="image.html">镜像列表</a></li>'
    nav += '        <li title="imageSet"><a href="imageSet.html">镜像管理</a></li>'
    nav += '      </ul>'
    nav += '    </li>'
    nav += '    <li id="group-menu">'
    nav += '      <a href="applicationGroup.html">'
    nav += '        <span class="nav-label">组管理</span>'
    nav += '      </a>'
    nav += '    </li>'
    nav += '    <li id=widgets-menu>'
    nav += '      <a href="migrate.html">'
    nav += '        <span class="nav-label">迁移</span>'
    nav += '      </a>'
    nav += '    </li>'
     nav += '    <li id="recordLog">'
    nav += '      <a href="recordLog.html">'
    nav += '        <span class="nav-label">操作记录</span>'
    nav += '      </a>'
    nav += '    </li>'
    nav += '    <li id="feedback-menu">'
    nav += '      <a href="feedback.html">'
    nav += '        <span class="nav-label">用户反馈</span>'
    nav += '      </a>'
    nav += '    </li>'
    nav += '  </ul>'
    nav += '</div>'

    $("#navbar").html(nav);
}

$(document).ready(function() {
    initNav();
    getUser();
});

function logout() {
    $.ajax({
        url: "/logout",
        type: "GET",
        dataType: "json",
        success:function(req) {
            sessionStorage.removeItem("user");
            location.replace('http://' + window.location.host +'/kvm/login.html');

        },
        error:function(){

        }
    });
};

function getUser(){
    var user = sessionStorage.user;
    if (user == undefined) {
        window.location.href = 'login.html';
    } else {
        // 直接从sessionStorage中获取
        var objUser = JSON.parse(user);

        $("#login_user_name").text(objUser['user_info']);
    }



}

$(function(){
//权限设置
    userList = JSON.parse(sessionStorage.user);

    var promissionList = $(".promission");
        user_id_num=userList.user_id;
    if(user_id_num==null){
        window.location.href = 'http://' + window.location.host + '/kvm/login.html';
        sessionStorage.removeItem("user");
    };
    var urlName = getUrlPath();

    //导航栏展开的问题
    var arrNav1=["area","datacenter","net_area","hostpool"];
    for(var i=0;i<arrNav1.length;i++){
       if( arrNav1[i]==urlName){
           $("#area-menu").addClass("active").children("ul").addClass("in");
           $("#area-menu").children("ul").children("[title="+urlName+"]").addClass("active").siblings().removeClass("active");
       }
    }

    var arrNav2=["host","instance","ip"];
     for(var i=0;i<arrNav2.length;i++){
       if( arrNav2[i]==urlName){
           $("#source-menu").addClass("active").children("ul").addClass("in");
           $("#source-menu").children("ul").children("[title="+urlName+"]").addClass("active").siblings().removeClass("active");
       }
    }

    var arrNav3=["image","imageSet"];
    for(var i=0;i<arrNav3.length;i++){
       if( arrNav3[i]==urlName){
           $("#mirror-menu").addClass("active").children("ul").addClass("in");
           $("#mirror-menu").children("ul").children("[title="+urlName+"]").addClass("active").siblings().removeClass("active");
       }
    }

    role_id_arr=[];
    id_arr=[];


    if (userList.user_permisson != null) {
         user_permisson_arr=userList.user_permisson
        $.each(user_permisson_arr,function(index,tmp){
            id_arr.push([tmp.role_id,tmp.group_id,tmp.group_name]);
            role_id_arr.push(tmp.role_id);
        });
        role_id_arr=role_id_arr.unique();
    }
    else{

        //sessionStorage.removeItem("user");
        role_id_arr=[3];
        id_arr=[3,0];
    }

     if (//导航栏页面权限
            (role_id_arr.indexOf(2) != -1 ||
            role_id_arr.indexOf(3) != -1) &&
             role_id_arr.indexOf(1) == -1
        )
        {
             $(".role-index").attr("href","index2.html");
            $("#area-menu").css("display", "none");
            $("#source-menu").children("ul").children("[title=host]").css("display", "none");
            $("#source-menu").children("ul").children("[title=ip]").css("display", "none");
            $("#mirror-menu").css("display", "none");
            $("#widgets-menu").css("display", "none");
            $("#recordLog").css("display", "none");

        }
        else if ( role_id_arr.indexOf(1) != -1 && role_id_arr.length == 1)
        {
            var deg_n =false;
            for(var k = 0 ;k<id_arr.length && deg_n == false;k++){
                if(id_arr[k][0]==1 && id_arr[k][2]== 'supergroup'){
                    deg_n = true;
                    $("#add-01").css("display", "block");//组管理创建按钮
                }
            }
            if(!deg_n){
                 $("#add-01").css("display", "none");//组管理创建按钮
            }
            $("#new-added").css("display", "inline-block");//area页面新增按钮
            $("#datacenter-create-show").css("display", "inline-block");//datacenter创建按钮
            $("#datacenter-delete-show").css("display", "inline-block");//datacenter创建按钮
            $("#addNetarea").css("display", "inline-block");//net_area 新增按钮
            $("#deleteNetarea-modal-btn").css("display", "inline-block");//net_area 删除按钮
            $(".createHostpoolBtn").css("display", "inline-block"); //hostpool创建按钮
            $(".deleteHostpoolBtn").css("display", "inline-block");//hostpool删除按钮
            $("#image-create-show").css("display", "inline-block");//镜像创建按钮
            $("#image-type-in").css("display", "inline-block");//镜像补录按钮
            $("#syncImage").css("display", "inline-block");
        }else
        {
            window.location.href = 'http://' + window.location.host + '/kvm/login.html';
            sessionStorage.removeItem("user");
        }

})

function getUrlPath()//获取跳转的urlpath
{
    var urlStr = location.href;
    urlStr = urlStr.split(".html")[0];
    urlStr = urlStr.substring(urlStr.lastIndexOf("/") + 1);
    //console.log(urlStr);
    urlStr=="vm" && (urlStr="instance");
    return urlStr;
}

function tableOperaShow(list)//表格中的操作权限设置
{
    var urlName = getUrlPath();
    var promissionTableList = $(".promission-table");
    if (userList.user_permisson != null) {
        $.each(user_permisson_arr, function (i, tmp) {
            if (tmp[urlName].length > 0) {
                $.each(promissionTableList, function (k, ele) {
                    var num = tmp[urlName].indexOf(ele.getAttribute("data-table-promission"));
                    if (num != -1) {
                        ele.style.display = "inline-block";
                    }
                    if (num == -1) {
                        ele.style.display = "none";
                    }
                });
            } else {
                $(".operamore").css("display", "none");
                $(".promission-table").css("display", "none");
            }
        });
    }
}
function Base64() {

    // private property
    _keyStr = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";

    // public method for encoding
    this.encode = function (input) {
        var output = "";
        var chr1, chr2, chr3, enc1, enc2, enc3, enc4;
        var i = 0;
        input = _utf8_encode(input);
        while (i < input.length) {
            chr1 = input.charCodeAt(i++);
            chr2 = input.charCodeAt(i++);
            chr3 = input.charCodeAt(i++);
            enc1 = chr1 >> 2;
            enc2 = ((chr1 & 3) << 4) | (chr2 >> 4);
            enc3 = ((chr2 & 15) << 2) | (chr3 >> 6);
            enc4 = chr3 & 63;
            if (isNaN(chr2)) {
                enc3 = enc4 = 64;
            } else if (isNaN(chr3)) {
                enc4 = 64;
            }
            output = output +
                _keyStr.charAt(enc1) + _keyStr.charAt(enc2) +
                _keyStr.charAt(enc3) + _keyStr.charAt(enc4);
        }
        return output;
    }

    // public method for decoding
    this.decode = function (input) {
        var output = "";
        var chr1, chr2, chr3;
        var enc1, enc2, enc3, enc4;
        var i = 0;
        input = input.replace(/[^A-Za-z0-9\+\/\=]/g, "");
        while (i < input.length) {
            enc1 = _keyStr.indexOf(input.charAt(i++));
            enc2 = _keyStr.indexOf(input.charAt(i++));
            enc3 = _keyStr.indexOf(input.charAt(i++));
            enc4 = _keyStr.indexOf(input.charAt(i++));
            chr1 = (enc1 << 2) | (enc2 >> 4);
            chr2 = ((enc2 & 15) << 4) | (enc3 >> 2);
            chr3 = ((enc3 & 3) << 6) | enc4;
            output = output + String.fromCharCode(chr1);
            if (enc3 != 64) {
                output = output + String.fromCharCode(chr2);
            }
            if (enc4 != 64) {
                output = output + String.fromCharCode(chr3);
            }
        }
        output = _utf8_decode(output);
        return output;
    }

    // private method for UTF-8 encoding
    _utf8_encode = function (string) {

        string = string.replace(/\r\n/g, "\n");

        var utftext = "";
        for (var n = 0; n < string.length; n++) {
            var c = string.charCodeAt(n); //返回返回指定位置的字符的 Unicode 编码。这个返回值是 0 - 65535 之间的整数。
            if (c < 128) {
                utftext += String.fromCharCode(c); //接受一个指定的 Unicode 值，然后返回一个字符串。

            } else if ((c > 127) && (c < 2048)) {
                utftext += String.fromCharCode((c >> 6) | 192);
                utftext += String.fromCharCode((c & 63) | 128);

            } else {
                utftext += String.fromCharCode((c >> 12) | 224);
                utftext += String.fromCharCode(((c >> 6) & 63) | 128);
                utftext += String.fromCharCode((c & 63) | 128);

            }

        }
        return utftext;
    }

    // private method for UTF-8 decoding
    _utf8_decode = function (utftext) {
        var string = "";
        var i = 0;
        var c = c1 = c2 = 0;
        while (i < utftext.length) {
            c = utftext.charCodeAt(i);
            if (c < 128) {
                string += String.fromCharCode(c);
                i++;
            } else if ((c > 191) && (c < 224)) {
                c2 = utftext.charCodeAt(i + 1);
                string += String.fromCharCode(((c & 31) << 6) | (c2 & 63));
                i += 2;
            } else {
                c2 = utftext.charCodeAt(i + 1);
                c3 = utftext.charCodeAt(i + 2);
                string += String.fromCharCode(((c & 15) << 12) | ((c2 & 63) << 6) | (c3 & 63));
                i += 3;
            }
        }
        return string;
    }
}


