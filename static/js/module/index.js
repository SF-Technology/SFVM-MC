/**
 * Created by fengxingwang on 2017/4/27.
 */

$(function () {
    var app;
    app = new Vue({
        el: '#app',

        data: {
            area_nums: 0,//区域数量
            datacenter_nums: 0,//机房数量
            hostpool_nums: 0,//集群数量
            host_nums: 0,//主机数量
            dc_na:"",//机房名称
            index_data:''//第一次请求回来的数据
        },
        created: function () {
            this.get_index_map_data();
            this.get_index_data();
        },
        methods: {
            //获取地图展示所需数据
            get_index_map_data: function () {
                this.$http.get("/dashboard/v1/map")
                    .then(function (response) {
                        this.creat_dc_china_highcharts(response.data);
                    })
                    .catch(function (response) {
                        console.log(response)
                    })
            },
            //渲染地图
            creat_dc_china_highcharts: function (result) {
                var map = null,
                    geochina = 'https://data.jianshukeji.com/jsonp?filename=geochina/',
                    unDrilldown = ['taiwan', 'xianggang', 'aomen'];

                //使用本地数据渲染地图
                 $.getJSON("/kvm/js/config/china.json",function(mapdata){
                // 获取中国地图数据并初始化图表
          //      $.getJSON(geochina + 'china.json&callback=?', function (mapdata) {
                    var data = result.data;

                    map = new Highcharts.Map('dc_china', {
                        chart: {
                            // events: {
                            //     drilldown: function (e) {
                            //         // 异步下钻
                            //         if (e.point.drilldown && unDrilldown.indexOf(e.point.drilldown) === -1) {
                            //             var pointName = e.point.properties.fullname;
                            //             map.showLoading('下钻中，请稍后...');
                            //             // 获取二级行政地区数据并更新图表
                            //             $.getJSON(geochina + e.point.drilldown + '.json&callback=?', function (data) {
                            //                 data = Highcharts.geojson(data);
                            //                 Highcharts.each(data, function (d) {
                            //                     d.value = Math.floor((Math.random() * 100) + 1); // 生成 1 ~ 100 随机值
                            //                 });
                            //                 map.hideLoading();
                            //                 map.addSeriesAsDrilldown(e.point, {
                            //                     name: e.point.name,
                            //                     data: data,
                            //                     dataLabels: {
                            //                         enabled: true,
                            //                         format: '{point.name}'
                            //                     }
                            //                 });
                            //                 map.setTitle({
                            //                     text: pointName
                            //                 });
                            //             });
                            //         }
                            //     },
                            //     drillup: function () {
                            //         map.setTitle({
                            //             text: '中国'
                            //         });
                            //     }
                            // }
                        },
                        title: {
                            text: ''
                        },
                        mapNavigation: {
                            enabled: true,
                            buttonOptions: {
                                verticalAlign: 'bottom'
                            }
                        },
                        tooltip: {
                            useHTML: true,
                            headerFormat: '<table><tr><td>{point.name}</td></tr>',
                            pointFormat: '<tr><td>全称</td><td>{point.name}</td></tr>' +
                            '<tr><td>机房数量：</td><td>{point.dc}</td></tr>' +
                            '<tr><td>主机数量：</td><td>{point.host}</td></tr>' +
                            '<tr><td>VM数量：</td><td>{point.vm}</td></tr>',
                            footerFormat: '</table>'
                        },
                        colorAxis: {
                            dataClasses: [{
                                color: "#13b93d",
                                from: 0,
                                name: "正常",
                                to: 0,
                            },
                                {
                                    color: "#f7f517",
                                    from: 1,
                                    name: "主机异常",
                                    to: 1,
                                },
                                {

                                    color: "#ff0806",
                                    from: 2,
                                    name: "严重异常",
                                    to: 1000,
                                }
                            ]
                        },
                        series: [{
                            data: data,
                            mapData: mapdata,
                            joinBy: 'name',
                            name: '中国地图',
                            states: {
                                hover: {
                                    color: '#f9f9ff'
                                }
                            }
                        }]
                    });
                    //隐藏不必要功能标签
                    $('.highcharts-contextbutton').hide();
                    $('.highcharts-credits').hide();
                });

            },
            //获取饼状图渲染所需数据
            get_index_data: function () {
                this.$http.get("/dashboard/v1")
                    .then(function (response) {
                        this.index_data = response;
                        this.creat_select(response.data.data.dc_vms);
                        this.creat_overview(response.data.data.overview);
                        this.creat_vm_bar(response.data.data.dc_vms);
                        this.creat_cpu_bar(response.data.data.dc_cpu);
                        this.creat_mem_bar(response.data.data.dc_mem);
                    })
                    .catch(function (response) {
                        console.log(response)
                    })
            },
            //赋值下拉列表
           creat_select:function(result) {
               let dcnList;
               dcnList = "";
               environments = allEnvArr
               this.dc_na = result[0].dc_name+'-'+environments[result[0].dc_type] ;
               for(var i=0;i<result.length;i++){

                    dcnList += "<option value="+result[i].dc_name+">" + result[i].dc_name+'-'+environments[result[i].dc_type] + "</option>";
               }
               // for (var obj in result) {
               //         dcnList += "<option>" + result[obj].dc_name + "</option>";
               // }
               $("#dc_n").html(dcnList);


           },
            //渲染vm柱状图
            creat_vm_bar: function (result) {
                var vm_bar_data_on;
                var vm_bar_data_off;
                var vm_bar_data_others;
                environments = allEnvArr
                for (var obj in result) {
                    if (result[obj].dc_name == this.dc_na.substring(0,this.dc_na.lastIndexOf('-'))&&environments[result[obj].dc_type] ==this.dc_na.substring(this.dc_na.lastIndexOf('-')+1,this.dc_na.length)) {

                        vm_bar_data_on = result[obj].startup_vms;
                        vm_bar_data_off = result[obj].shutdown_vms;
                        vm_bar_data_others = result[obj].other_vms;
                    }
                }
                var vmChart = echarts.init(document.getElementById('vm_pie'));


                var option = {
                    tooltip : {
                        // trigger: 'axis',
                        formatter: '{a}-{b}:{c} ' ,

                    },
                    xAxis: {
                        data:['运行中','关机','其他']
                    },
                    yAxis: {
                        show : false,
                        splitLine:{ show:false}  //改设置不显示坐标区域内的y轴分割线
                    },
                    series: [{
                            name: 'VM',
                            type: 'bar',
                            label: {
                                                normal: {
                                                    show: true,
                                                    formatter: '{c}' ,
                                                    position: 'inside'
                                                }
                                            },
                            data: [vm_bar_data_on, vm_bar_data_off, vm_bar_data_others],
                          //  data: [75, 105,175],
                            //设置柱子的宽度
                            barWidth : 40,
                            //配置样式
                            itemStyle: {
                                //通常情况下：
                                normal:{
                　　　　　　　　　　　　//每个柱子的颜色即为colorList数组里的每一项，如果柱子数目多于colorList的长度，则柱子颜色循环使用该数组
                                    color: function (params){
                                        var colorList = ['rgb(32,71,146)','rgb(239,59,42)','rgb(247,178,15)'];
                                        return colorList[params.dataIndex];
                                    }
                                },
                            },
                        }],
                　　　　　//控制边距　
                        grid: {
                                left: '0%',
                                right:'10%',
                                containLabel: false,
                        },
                    };



                vmChart.setOption(option, true);
            },

            //渲染mem柱状图
            creat_mem_bar: function (result) {

                var mem_pie_data_used;
                var mem_pie_data_unuse;
                 environments = allEnvArr
                for (var obj in result) {
                    if (result[obj].dc_name == this.dc_na.substring(0,this.dc_na.lastIndexOf('-'))&&environments[result[obj].dc_type] ==this.dc_na.substring(this.dc_na.lastIndexOf('-')+1,this.dc_na.length)) {

                        mem_pie_data_used = result[obj].used;
                        mem_pie_data_unuse = result[obj].unused;

                    }
                }
                var memChart = echarts.init(document.getElementById('mem_pie'));

                 var option = {
                    tooltip : {
                        // trigger: 'axis',
                        formatter: '{a}-{b}:{c} ' ,

                    },
                    xAxis: {
                        data:['使用','未使用']
                    },
                    yAxis: {
                        show : false,
                        splitLine:{ show:false}  //改设置不显示坐标区域内的y轴分割线
                    },
                    series: [{
                            name: 'MEM',
                            type: 'bar',
                            label: {
                                                normal: {
                                                    show: true,
                                                    formatter: '{c}' ,
                                                    position: 'inside'
                                                }
                                            },
                            data: [mem_pie_data_used, mem_pie_data_unuse],
                          //  data: [75, 105],
                            //设置柱子的宽度
                            barWidth : 40,
                            //配置样式
                            itemStyle: {
                                //通常情况下：
                                normal:{
                　　　　　　　　　　　　//每个柱子的颜色即为colorList数组里的每一项，如果柱子数目多于colorList的长度，则柱子颜色循环使用该数组
                                    color: function (params){
                                        var colorList = ['rgb(32,71,146)','rgb(239,59,42)','rgb(247,178,15)'];
                                        return colorList[params.dataIndex];
                                    }
                                },
                            },
                        }],
                　　　　　//控制边距　
                        grid: {
                                left: '0%',
                                right:'10%',
                                containLabel: false,
                        },
                    };
                memChart.setOption(option, true);

            },


            //渲染cpu饼图
            creat_cpu_bar: function (result) {

                var cpu_pie_data_used;
                var cpu_pie_data_unuse;
                environments = allEnvArr
                for (var obj in result) {
                    if (result[obj].dc_name == this.dc_na.substring(0,this.dc_na.lastIndexOf('-'))&&environments[result[obj].dc_type] ==this.dc_na.substring(this.dc_na.lastIndexOf('-')+1,this.dc_na.length)) {
                        cpu_pie_data_used = result[obj].used;
                        cpu_pie_data_unuse = result[obj].unused;


                    }
                }
                var cpuChart = echarts.init(document.getElementById('cpu_pie'));
                var option = {
                    tooltip : {
                        // trigger: 'axis',
                        formatter: '{a}-{b}:{c} ' ,

                    },
                    xAxis: {
                        data:['使用','未使用']
                    },
                    yAxis: {
                        show : false,
                        splitLine:{ show:false}  //改设置不显示坐标区域内的y轴分割线
                    },
                    series: [{
                            name: 'CPU',
                            type: 'bar',
                            label: {
                                                normal: {
                                                    show: true,
                                                    formatter: '{c}' ,
                                                    position: 'inside'
                                                }
                                            },
                          //  data: [1200, 2500],
                          data: [cpu_pie_data_used, cpu_pie_data_unuse],
                            //设置柱子的宽度
                            barWidth : 40,
                            //配置样式
                            itemStyle: {
                                //通常情况下：
                                normal:{
                　　　　　　　　　　　　//每个柱子的颜色即为colorList数组里的每一项，如果柱子数目多于colorList的长度，则柱子颜色循环使用该数组
                                    color: function (params){
                                        var colorList = ['rgb(32,71,146)','rgb(239,59,42)'];
                                        return colorList[params.dataIndex];
                                    }
                                },
                            },
                        }],
                　　　　　//控制边距　
                        grid: {
                                left: '0%',
                                right:'10%',
                                containLabel: false,
                        },
                    };
                cpuChart.setOption(option, true);

            },
            //渲染vm饼图
            creat_vm_pie: function (result) {
                var vm_pie_data_on;
                var vm_pie_data_off;
                var vm_pie_data_others;
                for (var obj in result) {
                    if (result[obj].dc_name == this.dc_na.substring(0,this.dc_na.lastIndexOf('-'))) {
                        vm_pie_data_on = result[obj].startup_vms;
                        vm_pie_data_off = result[obj].shutdown_vms;
                        vm_pie_data_others = result[obj].other_vms;
                    }
                }
                var vmChart = echarts.init(document.getElementById('vm_pie'));


                var option = {
                    tooltip: {
                        trigger: 'item',
                        formatter: "{a} <br/>{b}: {c} ({d}%)"
                    },
                    // legend: {
                    //     orient: 'horizontal',
                    //     x: 'left',
                    //     data: ['已关机', '已开机', '其他']
                    // },
                    series: [{
                        name: 'VM状态',
                        type: 'pie',
                        radius: ['50%', '70%'],
                        avoidLabelOverlap: false,
                        label: {
                            normal: {
                                show: true,
                                position: 'left'
                            },
                            emphasis: {
                                show: true,
                                textStyle: {
                                    fontSize: '10',
                                    fontWeight: 'bold'
                                }
                            }
                        },
                        labelLine: {
                            normal: {
                                show: true
                            }
                        },
                        data: [
                            {value: vm_pie_data_off, name: '已关机'},
                            {value: vm_pie_data_on, name: '已开机'},
                            {value: vm_pie_data_others, name: '其他'}
                        ],
                        itemStyle:{
                            normal:{
                                  label:{
                                    show: true,
                                    formatter: '{b} : {c} ({d}%)'
                                  },
                                  labelLine :{show:true}
                                }

                        }

                    }
                    ]
                };

                vmChart.setOption(option, true);
            },

            //渲染cpu饼图
            creat_cpu_pie: function (result) {

                var cpu_pie_data_used;
                var cpu_pie_data_unuse;
                for (var obj in result) {
                    if (result[obj].dc_name == this.dc_na.substring(0,this.dc_na.lastIndexOf('-'))) {
                        cpu_pie_data_used = result[obj].used;
                        cpu_pie_data_unuse = result[obj].unused;


                    }
                }
                var cpuChart = echarts.init(document.getElementById('cpu_pie'));
                var option = {
                    tooltip: {
                        trigger: 'item',
                        formatter: "{a} <br/>{b}: {c} ({d}%)"
                    },
                    // legend: {
                    //     orient: 'horizontal',
                    //     x: 'left',
                    //     data: ['已使用', '未使用']
                    // },
                    series: [
                        {
                            name: 'cpu使用率',
                            type: 'pie',
                            radius: ['50%', '70%'],
                            avoidLabelOverlap: false,
                            label: {
                                normal: {
                                    show: true,
                                    position: 'left'
                                },
                                emphasis: {
                                    show: true,
                                    textStyle: {
                                        fontSize: '10',
                                        fontWeight: 'bold'
                                    }
                                }
                            },
                            labelLine: {
                                normal: {
                                    show: true
                                }
                            },
                            data: [
                                {value: cpu_pie_data_used, name: '已使用'},
                                {value: cpu_pie_data_unuse, name: '未使用'}
                            ],
                            itemStyle:{
                                normal:{
                                      label:{
                                        show: true,
                                        formatter: '{b} : {c} ({d}%)'
                                      },
                                      labelLine :{show:true}
                                    }
                                }
                        }
                    ]
                };
                cpuChart.setOption(option, true);

            },
            //渲染mem饼图
            creat_mem_pie: function (result) {

                var mem_pie_data_used;
                var mem_pie_data_unuse;
                for (var obj in result) {
                    if (result[obj].dc_name == this.dc_na.substring(0,this.dc_na.lastIndexOf('-'))) {
                        mem_pie_data_used = result[obj].used;
                        mem_pie_data_unuse = result[obj].unused;

                    }
                }
                var memChart = echarts.init(document.getElementById('mem_pie'));

                var option;
                option = {
                    tooltip: {
                        trigger: 'item',
                        formatter: "{a} <br/>{b}: {c} ({d}%)"
                    },
                    // legend: {
                    //     orient: 'horizontal',
                    //     x: 'left',
                    //     data: ['已使用', '未使用']
                    // },
                    series: [
                        {
                            name: '内存使用率',
                            type: 'pie',
                            radius: ['50%', '70%'],
                            avoidLabelOverlap: false,
                            label: {
                                normal: {
                                    show: true,
                                    position: 'left'
                                },
                                emphasis: {
                                    show: true,
                                    textStyle: {
                                        fontSize: '10',
                                        fontWeight: 'bold'
                                    }
                                }
                            },
                            labelLine: {
                                normal: {
                                    show: true
                                }
                            },
                            data: [
                                {value: mem_pie_data_used, name: '已使用'},
                                {value: mem_pie_data_unuse, name: '未使用'}
                            ],
                            itemStyle:{
                                normal:{
                                      label:{
                                        show: true,
                                        formatter: '{b} : {c} ({d}%)'
                                      },
                                      labelLine :{show:true}
                                    }
                                }

                        }
                    ],
                    color: ['#ff0401',
                        '#13b93d']
                };
                memChart.setOption(option, true);

            },
            //绑定综述数据
            creat_overview: function (result) {
                this.area_nums = result.area_nums;
                this.datacenter_nums = result.datacenter_nums;
                this.hostpool_nums = result.hostpool_nums;
                this.host_nums = result.host_nums;
            },
            //选择机房
            get_selected_dcn:function () {
               this.dc_na = ($("#dc_n option:selected").html());
                this.creat_vm_bar(this.index_data.data.data.dc_vms);
                this.creat_cpu_bar(this.index_data.data.data.dc_cpu);
                this.creat_mem_bar(this.index_data.data.data.dc_mem);
                }


            }
    });
});