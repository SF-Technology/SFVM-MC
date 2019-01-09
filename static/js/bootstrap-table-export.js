/**
 * Created by 80002473 on 2017/6/28.
 */
/**
 * @author zhixin wen <wenzhixin2010@gmail.com>
 * extensions: https://github.com/kayalshri/tableExport.jquery.plugin
 */

(function ($) {
    'use strict';
    var sprintf = $.fn.bootstrapTable.utils.sprintf;

    var TYPE_NAME = {
        json: 'JSON',
        xml: 'XML',
        png: 'PNG',
        csv: 'CSV',
        txt: 'TXT',
        sql: 'SQL',
        doc: '导出Word文档',
        excel: '导出Excel表格',
        powerpoint: 'MS-Powerpoint',
        pdf: 'PDF',
        all:'导出Excel数据'
    };

    $.extend($.fn.bootstrapTable.defaults, {
        showExport: false,
        exportDataType: 'basic', // basic, all, selected
        // 'json', 'xml', 'png', 'csv', 'txt', 'sql', 'doc', 'excel', 'powerpoint', 'pdf'
        exportTypes: ['json', 'xml', 'csv', 'txt', 'sql', 'excel','all'],
        exportOptions: {}
    });

    $.extend($.fn.bootstrapTable.defaults.icons, {
        export: 'glyphicon glyphicon-share'
    });

    $.extend($.fn.bootstrapTable.locales, {
        formatExport: function () {
            return 'Export data';
        }
    });
    $.extend($.fn.bootstrapTable.defaults, $.fn.bootstrapTable.locales);
    var BootstrapTable = $.fn.bootstrapTable.Constructor,
        _initToolbar = BootstrapTable.prototype.initToolbar;
    BootstrapTable.prototype.initToolbar = function () {

        this.showToolbar = this.options.showExport;

        _initToolbar.apply(this, Array.prototype.slice.apply(arguments));

        if (this.options.showExport) {
            var that = this,
                $btnGroup = this.$toolbar.find('>.btn-group'),
                $export = $btnGroup.find('div.export');

            if (!$export.length) {
                $export = $([
                    '<div class="export btn-group">',
                        '<button class="btn btn-default' +
                            sprintf(' btn-%s', this.options.buttonsClass) +
                            sprintf(' btn-%s', this.options.iconSize) +
                            ' dropdown-toggle" ' +
                            'title="' + this.options.formatExport() + '" ' +
                            'data-toggle="dropdown" type="button">',
                            sprintf('<i class="%s %s"></i> 导出', this.options.iconsPrefix, this.options.icons.export),
                            '<span class="caret"></span>',
                        '</button>',
                        '<ul class="dropdown-menu" role="menu" style="min-width: 65px">',
                        '</ul>',
                    '</div>'].join('')).appendTo($btnGroup);

                var $menu = $export.find('.dropdown-menu'),
                    exportTypes = this.options.exportTypes;

                if (typeof this.options.exportTypes === 'string') {
                    var types = this.options.exportTypes.slice(1, -1).replace(/ /g, '').split(',');

                    exportTypes = [];
                    $.each(types, function (i, value) {
                        exportTypes.push(value.slice(1, -1));
                    });
                }

                $.each(exportTypes, function (i, type) {
                    if (TYPE_NAME.hasOwnProperty(type)) {
                        $menu.append(['<li data-type="' + type + '">',
                                '<a href="javascript:void(0)">',
                                    TYPE_NAME[type],
                                '</a>',
                            '</li>'].join(''));
                    }
                });
                var url_name = location.href.substring(location.href.lastIndexOf('/')+1,location.href.lastIndexOf('.'));

                $menu.find('li').click(function () {
                    if(length_export <= 0){
                        showMessage("无数据可导出","danger",2000);
                        return;
                    }
                    var type = $(this).data('type'),
                        doExport = function () {
                            that.$el.tableExport($.extend({}, that.options.exportOptions, {
                                type: type,
                                escape: false
                            }));
                        };
                    if (type == "all") {//付太平加
                        if(url_name == "hostpool"){
                            location.href = "/hostpool/excel";
                            return;
                        }
                        var search = $(".export-excel").attr("data-search-text");

                        if(!search){
                            search = "";
                        }else{
                           search = JSON.parse(search).search;
                        }
                        url_name == "vm" && (location.href = "/instance/excel?search="+search);
                        url_name == "host" && (location.href = "/host/excel?search="+search);
                        url_name == "migrate" && (location.href = "/v2v/task/excel?search="+search);
                    } else {
                        if (that.options.exportDataType === 'all' && that.options.pagination) {
                            that.$el.one(that.options.sidePagination === 'server' ? 'post-body.bs.table' : 'page-change.bs.table', function () {
                                doExport();
                                that.togglePagination();
                            });
                            that.togglePagination();
                        } else if (that.options.exportDataType === 'selected') {
                            var data = that.getData(),
                                selectedData = that.getAllSelections();

                            that.load(selectedData);
                            doExport();
                            that.load(data);
                        } else {
                            doExport();
                        }
                    }

                });
            }
        }
    };
})(jQuery);