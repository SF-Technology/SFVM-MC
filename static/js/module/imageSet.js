/**
 * Created by 80002473 on 2017/7/6.
 */
window.onload = function() {
  init_table()
  $('#image-create-show').click(function() {
    //获取系统版本以及操作系统
    CreateImageFun.getInitImageVersions()
    CreateImageFun.checkOutPage(
      '.create-image-page',
      '#imageMain',
      { left: '15px' },
      { left: '-100%' }
    )
  })
  $('#backBtn').click(function() {
    CreateImageFun.checkOutPage(
      '#imageMain',
      '.create-image-page',
      { left: '0' },
      { left: '100%' }
    )
  })

  // 标签页的切换
  $('a[data-toggle="tab"]').on('show.bs.tab', function(e) {
    //e.target // 激活的标签页
    //e.relatedTarget // 前一个激活的标签页
    CreateImageFun.initValue(CreateImageFun.createInputArr)
  })

  /*
     搜索查询下拉框
     */
  $('#display_name_input').focus(function() {
    $('.select_list_used').slideDown()
  })
  $('#display_name_input').blur(function() {
    $('.select_list_used').slideUp(500)
  })
  $('.select_list_used').on('click', 'li', function(e) {
    var that = e.target
    var selected_image = CreateImageFun.getSelectedOs(that)
    $('#display_name_input').val(selected_image)
    CreateImageFun.image_list_used.forEach(function(item, index) {
      if (item.name == selected_image) {
        $('#new_system_used').html(
          `<option value="${item.system}">${item.system}</option>`
        )
        $('#display_name_input_os').val(item.version)
        CreateImageFun.tag = item.tag
      }
    })
  })
  $('#create_used_image').click(function() {
    var old_name = $('#display_name_input').val()
    var version = $('#display_name_input_os').val()
    var image_name = $('#new_name_used').val()
    var displayname = $('#new_display_name_used').val()
    //var write_image = $(this).val();
    var imageArr = []
    CreateImageFun.image_list_used.forEach(function(item, index) {
      imageArr.push(item.name)
    })
    if (imageArr.indexOf(old_name) != -1) {
      CreateImageFun.imageIsExist = true
      $('#create_used_image').attr('disabled', false)
    } else {
      CreateImageFun.imageIsExist = false
      $('#create_used_image').attr('disabled', true)
      $('#new_system_used').html(``)
      $('#display_name_input_os').val('')
    }
    if (!CreateImageFun.imageIsExist) {
      showMessage('请选择已有镜像进行创建新镜像', 'danger', 200)
      return false
    }
    if (!CreateImageFun.checkReg(image_name)) {
      showMessage('镜像名称只能由a-zA-X._组成', 'danger', 200)
      return false
    }
    if (!displayname) {
      showMessage('请输入镜像显示名称', 'danger', 200)
      return false
    }
    $.ajax({
      url: '/image_manage/create_by_exist',
      type: 'post',
      dataType: 'json',
      data: {
        version: version,
        image_name: image_name,
        displayname: displayname,
        //"tag": CreateImageFun.tag,
        source_img_name: old_name,
        os_type: $('#new_system_used').val()
      },
      beforeSend: function() {
        $('#loading').css('display', 'block')
      },
      success: function(res) {
        $('#loading').css('display', 'none')
        if (res.code != 0) {
          res.msg != ''
            ? showMessage(res.msg, 'danger', 200)
            : showMessage('获取信息失败', 'danger', 200)
          return false
        }
        showMessage('创建成功', 'success', 200)
        CreateImageFun.checkOutPage(
          '#imageMain',
          '.create-image-page',
          { left: '0' },
          { left: '100%' }
        )
        $('#image_list').bootstrapTable('refresh', { slient: true })
        CreateImageFun.initValue(CreateImageFun.createInputArr)
      },
      error: function(res) {}
    })
  })
  // 创建新镜像选择版本
  $('#new_system').change(function() {
    var sysValue = $(this).val()
    $('#image_os').val('')
    $('#new_name').val('')
    $('#new_display_name').val('')
    for (var i = 0; i < CreateImageFun.sysOsList.length; i++) {
      var tmp = CreateImageFun.sysOsList[i]
      if (tmp.OS_TYPE == sysValue) {
        // 生成os类型化
        var os_list = tmp.OS_VER,
          os_html = ''
        select_os_list = os_list
        for (var i = 0, len = os_list.length; i < len; i++) {
          os_html += `<li class="select_item_os"><a href="javascript:void(0)">${
            os_list[i]
          }</a></li>`
        }
        $('.select_list_os').html(os_html)
      }
    }
  })
  $('#image_os').focus(function() {
    $('.select_list_os').slideDown()
  })
  $('#image_os').blur(function() {
    $('.select_list_os').slideUp(500)
  })
  $('.select_list_os').on('click', 'li', function(e) {
    var that = e.target
    $('#image_os').val(CreateImageFun.getSelectedOs(that))
  })
  $('.create_new_image_btn').click(function() {
    var newSys = $('#new_system').val()
    var newSysOs = $('#image_os').val()
    var newSysName = $('#new_name').val()
    var newSysDisplayName = $('#new_display_name').val()
    if (!newSysOs) {
      showMessage('请选择系统版本', 'danger', 200)
      return false
    }
    if (!newSysDisplayName) {
      showMessage('请输入请输入镜像名称', 'danger', 200)
      return false
    }
    if (!CreateImageFun.checkReg(newSysName)) {
      showMessage('镜像名称只能由a-zA-X._组成', 'danger', 200)
      return false
    }
    $.ajax({
      url: '/image_manage/create_new',
      type: 'post',
      dataType: 'json',
      data: {
        version: newSysOs,
        image_name: newSysName,
        displayname: newSysDisplayName,
        os_type: $('#new_system').val()
      },
      beforeSend: function() {
        $('#loading').css('display', 'block')
      },
      success: function(res) {
        $('#loading').css('display', 'none')
        if (res.code != 0) {
          res.msg != ''
            ? showMessage(res.msg, 'danger', 30000)
            : showMessage('创建失败,请刷新重试', 'danger', 30000)
          return false
        }
        showMessage('创建成功', 'success', 200)
        CreateImageFun.checkOutPage(
          '#imageMain',
          '.create-image-page',
          { left: '0' },
          { left: '100%' }
        )
        $('#image_list').bootstrapTable('refresh', { slient: true })
        CreateImageFun.initValue(CreateImageFun.createInputArr)
      },
      error: function(res) {}
    })
  })
  // 用已有镜像创建新镜像
  $('#create_used').click(function() {
    CreateImageFun.getImageInfo(
      '.select_list_used',
      '#new_system_used',
      '#display_name_input_os',
      '#display_name_input'
    )
  })
  $('#image_os').focus(function() {
    $('.select_list_os').slideDown()
  })
  $('#image_os').blur(function() {
    $('.select_list_os').slideUp(500)
  })
  $('.select_list_os').on('click', 'li', function(e) {
    var that = e.target
    $('#image_os').val(CreateImageFun.getSelectedOs(that))
  })

  // 操作提交
  $('#operate_submit').click(function() {
    switch (CreateImageFun.operateObj.type) {
      case 1:
        CreateImageFun.compileImage()
        break
      case 2:
        CreateImageFun.build_image()
        break
      case 3:
        break
      case 4:
        switch (CreateImageFun.operateObj.params.create_type) {
          case '-1':
            CreateImageFun.releaseNewImage()
            break
          case '0':
            CreateImageFun.releaseNewImage()
            break
          case '1':
            CreateImageFun.releaseNewImage()
            break
          case '2':
            CreateImageFun.releaseUsedImage()
            break
        }
        $('#checkOperate').modal('hide')
        $('#image_list').bootstrapTable('refresh', { slient: true })
        break
      case 5:
        break
    }
  })

  //镜像补录
  $('#image-type-in').click(function() {
    CreateImageFun.getImageInfo(
      '.select_list_type_in',
      '#new_system_type_in',
      '#display_name_type_in_os',
      '#display_name_type_in'
    )
    $('#type_in_image').modal('show')
  })
  $('#display_name_type_in').focus(function() {
    $('.select_list_type_in').slideDown()
  })
  $('#display_name_type_in').blur(function() {
    $('.select_list_type_in').slideUp(500)
  })
  $('.select_list_type_in').on('click', 'li', function(e) {
    var that = e.target
    var selected_image = CreateImageFun.getSelectedOs(that)
    $('#display_name_type_in').val(selected_image)
    CreateImageFun.image_list_used.forEach(function(item, index) {
      if (item.name == selected_image) {
        $('#new_system_type_in').html(
          `<option value="${item.system}">${item.system}</option>`
        )
        $('#display_name_type_in_os').val(item.version)
        CreateImageFun.tag = item.tag
        CreateImageFun.displayname = item.displayname
      }
    })
  })
  $('#type_in_submit').click(function() {
    var eimage_name = $('#display_name_type_in').val()
    var version = $('#display_name_type_in_os').val()
    var displayname = CreateImageFun.displayname
    var imageArr = []
    CreateImageFun.image_list_used.forEach(function(item, index) {
      imageArr.push(item.name)
    })
    if (imageArr.indexOf(eimage_name) != -1) {
      CreateImageFun.imageIsExist = true
      $('#type_in_submit').attr('disabled', false)
    } else {
      CreateImageFun.imageIsExist = false
      $('#type_in_submit').attr('disabled', true)
      $('#new_system_type_in').html(``)
      $('#display_name__type_in_os').val('')
    }
    if (!CreateImageFun.imageIsExist) {
      showMessage('请选择已有镜像进行创建新镜像', 'danger', 200)
      return false
    }
    if (!CreateImageFun.checkReg(eimage_name)) {
      showMessage('镜像名称只能由a-zA-X._组成', 'danger', 200)
      return false
    }
    if (!displayname) {
      showMessage('请输入镜像显示名称', 'danger', 200)
      return false
    }
    $.ajax({
      url: '/image_manage/update_by_exist',
      type: 'post',
      dataType: 'json',
      data: {
        version: version,
        eimage_name: eimage_name,
        displayname: displayname,
        os_type:$("#new_system_type_in").val()
      },
      beforeSend: function() {
        $('#loading').css('display', 'block')
      },
      success: function(res) {
        $('#loading').css('display', 'none')
        if (res.code != 0) {
          res.msg != ''
            ? showMessage(res.msg, 'danger', 1000)
            : showMessage('补录失败', 'danger', 1000)
          return false
        }
        showMessage('补录成功', 'success', 200)
        $('#type_in_image').modal('hide')
        $('#image_list').bootstrapTable('refresh', { slient: true })
      },
      error: function(res) {}
    })
  })
}

function init_table() {
  $('#image_list').bootstrapTable({
    url: '/image_manage/list',
    method: 'GET',
    dataType: 'json',
    detailView: false,
    uniqueId: 'image_id', //删除时能用到 removeByUniqueId
    queryParamsType: 'search',
    showRefresh: true,
    contentType: 'application/x-www-form-urlencoded',
    pagination: true,
    pageList: [10, 20, 50, 100, 'all'],
    pageSize: 10,
    pageNumber: 1,
    search: false, //不显示全表模糊搜索框
    //            searchText: getQueryString('search'),
    showColumns: true, //不显示下拉框（选择显示的列）
    sidePagination: 'server', //服务端请求
    clickToSelect: false,
    singleSelect: false,
    onBeforeLoadParams: {}, //查询参数设置，供导出使用，在search_form.js里赋值
    sortable: false,
    responseHandler: function(res) {
      if (res.code == 0) {
        return res.data
      } else {
        return null
      }
    },
    queryParams: function(q) {
      var searchContent = q.searchText
      return {
        page_size: q.pageSize,
        page_no: q.pageNumber
      }
    },
    onLoadSuccess: function($element) {},
    onClickRow: function($element, row) {},
    columns: [
      {
        checkbox: true
      },
      {
        title: '显示名称',
        field: 'displayname',
        valign: 'middle',
        align: 'left'
      },
      {
        title: '操作系统',
        field: 'system',
        valign: 'middle',
        align: 'left'
      },
      {
        title: '模板机IP',
        field: 'template_vm_ip',
        valign: 'middle',
        align: 'left'
      },
      {
        title: '模板机状态',
        field: 'template_status',
        valign: 'middle',
        align: 'left',
        formatter: function(value, row, index) {
          var template_status_str = ''
          switch (value) {
            case '0':
              template_status_str = '运行中'
              break
            case '1':
              template_status_str = '已关机'
              break
          }
          return template_status_str
        }
      },
      {
        title: '镜像状态',
        field: 'status',
        valign: 'middle',
        align: 'left',
        formatter: function(value, row, index) {
          return CreateImageFun.judgeImageStatus(value)
        }
      },
      {
        title: '镜像版本',
        field: 'version',
        valign: 'middle',
        align: 'left'
      },
      {
        title: '创建时间',
        field: 'create_time',
        valign: 'middle',
        align: 'left'
      },
      {
        title: '任务详情',
        field: 'image_manage_message',
        valign: 'middle',
        class: 'taskDet',
        align: 'left',
        formatter: function(value, row, index) {
          if (value != '') {
            return `<div class="taskDetails" id="taskDet" title="${value}">${value} </div>`
          } else {
            return ''
          }
        },
        events: {
          'click .taskDetails': function(row, value, index) {
            $('.errorTask').html(value)
            $('#errorInfo').modal('show')
          }
        }
      },
      {
        title: '操作',
        field: 'operation',
        align: 'left',
        events: operateEvents,
        formatter: operateFormatter
      }
    ]
  })
}

function operateFormatter(value, row, index) {
  let imageHtml = `<div class="dropdown image-btn-list">
                            <button class="btn btn-primary dropdown-toggle" type="button" id="image-operate-menu" data-toggle="dropdown">更多
                            <span class="caret"></span></button>
                            <ul class="dropdown-menu" role="menu" aria-labelledby="menu1">
                              <li class="compile_image ${
                                row.status == '-1' ||
                                row.status == '0' ||
                                row.status == '2'
                                  ? ''
                                  : 'is_dis'
                              }" data-num="1" role="presentation"><a role="menuitem" tabindex="-1" href="#">编辑镜像</a></li>
                              <li class="build_image ${
                                row.status == '1' ? '' : 'is_dis'
                              }" data-num="2" role="presentation"><a role="menuitem" tabindex="-1" href="#">生成镜像</a></li>
                              <li class="console_image ${
                                row.status == '1' ? '' : 'is_dis'
                              }" data-num="3" role="presentation"><a role="menuitem" tabindex="-1" href="#">console</a></li>
                              <li class="release_image ${
                                row.status == '2' ? '' : 'is_dis'
                              }" data-num="4" role="presentation"><a role="menuitem" tabindex="-1" href="#">发布镜像</a></li>
                              <!--<li class="repair_image ${
                                row.status == '-10000' ? '' : 'is_dis'
                              }" data-num="5" role="presentation"><a role="menuitem" tabindex="-1" href="#">修复</a></li>-->
                            </ul>
                          </div>`
  return imageHtml
}

window.operateEvents = {
  'click .compile_image': function(e, value, row, index) {
    CreateImageFun.operateObj.type = 1
    CreateImageFun.operateObj.params = row
    CreateImageFun.setConfirm(1)
  },
  'click .build_image': function(e, value, row, index) {
    CreateImageFun.operateObj.type = 2
    CreateImageFun.operateObj.params = row
    CreateImageFun.setConfirm(2)
  },
  'click .console_image': function(e, value, row, index) {
    CreateImageFun.operateObj.params = row

    var url = window.location.href
    var position = url.indexOf('/kvm')
    var imgUrl = url.substring(0, position)
    var consoleUrl = imgUrl + '/image_manage/console?image_name=' + row.name
    window.open(consoleUrl)

  },
  'click .release_image': function(e, value, row, index) {
    CreateImageFun.operateObj.type = 4
    CreateImageFun.operateObj.params = row
    CreateImageFun.setConfirm(4)
  },
  'click .repair_image': function(e, value, row, index) {
    CreateImageFun.operateObj.type = 5
    CreateImageFun.operateObj.params = row
    CreateImageFun.setConfirm(5)
  }
}

var CreateImageFun = (function() {
  var select_os_list = []
  return {
    operateObj: {
      type: '', // 1 编辑镜像 2 生成镜像 3 console 4 发布镜像 5 修复镜像
      params: {}
    },
    createInputArr: [
      '#image_os',
      '#new_name',
      '#new_display_name',
      '#display_name_input',
      '#new_name_used',
      '#display_name_input_os',
      '#new_display_name_used'
    ],
    imageIsExist: true,
    tag: '',
    image_list_used: [], //已有镜像信息列表
    // 获取已有镜像信息
    getImageInfo: function(id1, id2, id3, id4) {
      $.ajax({
        url: '/image_manage/create_exist_init',
        type: 'get',
        dataType: 'json',
        success: function(res) {
          if (res.code != 0) {
            res.msg != ''
              ? showMessage(res.msg, 'danger', 30000)
              : showMessage('获取信息失败', 'danger', 30000)
            return false
          }
          var list = (CreateImageFun.image_list_used = res.data)
          for (var i = 0, len = list.length, str = ''; i < len; i++) {
            if (i == 0) {
              $(id2).html(
                `<option value="${list[i].system}">${list[i].system}</option>`
              )
              $(id3).val(list[i].version)
              $(id4).val(list[i].name)
              CreateImageFun.tag = list[i].tag
              CreateImageFun.displayname = list[i].displayname
            }
            str += `<li class="select_item_used"><a href="javascript:void(0)">${
              list[i].name
            }</a></li>`
          }
          $(id1).html(str)
        },
        error: function(res) {}
      })
    },
    // 生成镜像
    build_image: function() {
      $.ajax({
        url: '/image_manage/image_checkout',
        type: 'post',
        dataType: 'json',
        data: {
          image_name: CreateImageFun.operateObj.params.name
        },
        beforeSend: function() {
          $('#loading').css('display', 'block')
        },
        success: function(res) {
          $('#loading').css('display', 'none')
          if (res.code != '0') {
            res.msg != '0'
              ? showMessage(res.msg, 'danger', 1000)
              : showMessage('生成镜像失败,请刷新重试', 'danger', 1000)
            return false
          }
          showMessage('生成镜像成功', 'success', 1000)
          $('#checkOperate').modal('hide')
          $('#image_list').bootstrapTable('refresh', { slient: true })
        },
        error: function() {
          $('#loading').css('display', 'none')
        }
      })
    },
    // 编辑镜像
    compileImage: function() {
      $.ajax({
        url: '/image_manage/image_edit',
        type: 'post',
        dataType: 'json',
        data: {
          image_name: CreateImageFun.operateObj.params.name
        },
        beforeSend: function() {
          $('#loading').css('display', 'block')
        },
        success: function(res) {
          $('#loading').css('display', 'none')
          if (res.code != '0') {
            res.msg != '0'
              ? showMessage(res.msg, 'danger', 1000)
              : showMessage('编辑镜像失败,请刷新重试', 'danger', 1000)
            return false
          }
          showMessage('编辑镜像成功', 'success', 1000)
          $('#checkOperate').modal('hide')
          $('#image_list').bootstrapTable('refresh', { slient: true })
        },
        error: function() {
          $('#loading').css('display', 'none')
        }
      })
    },
    // 新镜像发布
    releaseNewImage: function() {
      $.ajax({
        url: '/image_manage/image_release_by_new',
        type: 'post',
        dataType: 'json',
        data: {
          name: CreateImageFun.operateObj.params.name,
          displayname: CreateImageFun.operateObj.params.displayname,
          version: CreateImageFun.operateObj.params.version,
          system: CreateImageFun.operateObj.params.system
        },
        success: function(res) {
          if (res.code != '0') {
            res.msg != '0'
              ? showMessage(res.msg, 'danger', 1000)
              : showMessage('发布镜像失败,请刷新重试', 'danger', 1000)
            return false
          }
        },
        error: function() {}
      })
    },
    releaseUsedImage: function() {
      $.ajax({
        url: '/image_manage/image_release_by_exist',
        type: 'post',
        dataType: 'json',
        data: {
          name: CreateImageFun.operateObj.params.name
        },
        success: function(res) {
          if (res.code != '0') {
            res.msg != '0'
              ? showMessage(res.msg, 'danger', 1000)
              : showMessage('发布镜像失败,请刷新重试', 'danger', 1000)
            return false
          }
          showMessage('发布成功', 'success', 1000)
          $('#checkOperate').modal('hide')
          $('#image_list').bootstrapTable('refresh', { slient: true })
        },
        error: function() {}
      })
    },
    // 正则验证
    checkReg: function(text) {
      var reg = new RegExp('^[a-zA-Z0-9._]+$')
      return reg.test(text)
    },
    // 初始化输入框的值
    initValue: function(idArr) {
      for (var i = 0, len = idArr.length; i < len; i++) {
        $(idArr[i]).val('')
      }
    },
    //切换到创建页面
    checkOutPage: function(id1, id2, site1, site2) {
      $(id1)
        .css('display', 'block')
        .animate(site1, 'slow')
      $(id2).animate(site2, 'slow', function() {
        $(this).css('display', 'none')
      })
    },
    // 状态转换
    judgeImageStatus: function(status) {
      var status_str = ''
      switch (status) {
        case '-1':
          status_str = '初始化'
          break
        case '0':
          status_str = '使用中'
          break
        case '1':
          status_str = '编辑中'
          break
        case '2':
          status_str = '待发布'
          break
        case '3':
          status_str = '发布中'
          break
        case '-10000':
          status_str = '错误'
          break
      }
      return status_str
    },
    // 确认弹框的内容设置
    setConfirm: function(num) {
      var title = ''
      switch (num) {
        case 1:
          title = '编辑镜像'
          break
        case 2:
          title = '生成镜像'
          break
        case 3:
          title = '进入console'
          break
        case 4:
          title = '发布镜像'
          break
        case 5:
          title = '进行修复'
          break
      }
      $('.confirm_body').html(title)
      $('#checkOperate').modal('show')
    },
    // 获取操作系统版本
    getInitImageVersions: function() {
      $.ajax({
        url: '/image_manage/create_new_init',
        type: 'get',
        dataType: 'json',
        success: function(res) {
          if (res.code != '0') {
            res.msg != '0'
              ? showMessage(res.msg, 'danger', 500)
              : showMessage('获取信息失败', 'danger', 500)
            return false
          }
          // 生成系统下拉
          var sysArr = res.data.os_type,
            sysHtml = '<option value="-1">请选择</option>'
          for (var i = 0, len = sysArr.length; i < len; i++) {
            sysHtml += `<option value="${sysArr[i]}">${sysArr[i]}</option>`
          }
          $('#new_system').html(sysHtml)
          CreateImageFun.sysOsList = res.data.os_ver_list
        },
        error: function() {}
      })
    },
    // 获取选中系统版本
    getSelectedOs: function(e) {
      var os_str = $(e).text()
      return os_str
    }
  }
})()

/**
 * Created by 80002473 on 2018/2/5.
 */
