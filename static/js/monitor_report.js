/**
 * Created by fengxingwang on 17/4/18.
 */

/**
 * 展示图标配置
 */
function init_echart()
    {
        var xdata = []
        var ydata = []
        // 指定图表的配置项和数据
        var option = {
            title: [
                {left: '0%', text: 'CPU使用(%):'},
                {left: '48%', text:'内存使用(%):'},
                {left: '0%', top:'34%', text:'接收流量(kb/s):'},
                {left: '48%', top:'34%', text: '发送流量(kb/s):'},
                {left: '0%', top:'68%', text:'写入速率(kb/s):'},
                {left: '48%', top:'68%', text: '读取速率(kb/s):'}],

            tooltip: {
                trigger: 'axis',
                axisPointer: {animation: true}
            },

            grid:[
                {top:'4%',left:'5%', width: '40%', height: '21%'},
                {top:'4%',left:'54%', width: '40%', height: '21%'},
                {top:'38%', left:'5%', width:'40%', height: '21%'},
                {top:'38%', left:'54%', width:'40%', height: '21%'},
                {top:'72%', left:'5%', width:'40%', height: '21%'},
                {top:'72%', left:'54%', width:'40%', height: '21%'}
            ],

            toolbox:{
                show: true,
                feature:{
                    my_range_button:{
                            show:true,
                            title:'选择时间范围',
                            icon:'path://M432.45,595.444c0,2.177-4.661,6.82-11.305,6.82c-6.475,0-11.306-4.567-11.306-6.82s4.852-6.812,11.306-6.812C427.841,588.632,432.452,593.191,432.45,595.444L432.45,595.444z M421.155,589.876c-3.009,0-5.448,2.495-5.448,5.572s2.439,5.572,5.448,5.572c3.01,0,5.449-2.495,5.449-5.572C426.604,592.371,424.165,589.876,421.155,589.876L421.155,589.876z M421.146,591.891c-1.916,0-3.47,1.589-3.47,3.549c0,1.959,1.554,3.548,3.47,3.548s3.469-1.589,3.469-3.548C424.614,593.479,423.062,591.891,421.146,591.891L421.146,591.891zM421.146,591.891',
                            option:{},
                            onclick:function(opt){
                                $("#time_range").modal('show');
                                }
                    },
                    magicType : {show: true, type: ['line', 'bar']},
                    dataZoom:{show: true, yAxisIndex:true},

                }
            },

        //    legend: {data:['监控项1']},

            //暂未发现用途，现行注释（2017/04/24 10:39）
            // dataZoom:[{
            //     id: 'dataZoomX',
            //     type: 'slider',
            //     xAxisIndex: [0],
            //     filterMode: 'filter',
            //     top:'29%'
            // },{
            //     id: 'dataZoomX2',
            //     type: 'slider',
            //     xAxisIndex: [1],
            //     filterMode: 'filter',
            //     top:'29%'
            // },{
            //     id: 'dataZoomX3',
            //     type: 'slider',
            //     xAxisIndex: [2],
            //     filterMode: 'filter',
            //     top:'63%'
            // },{
            //     id: 'dataZoomX4',
            //     type: 'slider',
            //     xAxisIndex: [3],
            //     filterMode: 'filter',
            //     top:'63%'
            // },
            // {
            //     id: 'dataZoomX5',
            //     type: 'slider',
            //     xAxisIndex: [4],
            //     filterMode: 'filter',
            //     top:'97%'
            // },{
            //     id: 'dataZoomX6',
            //     type: 'slider',
            //     xAxisIndex: [5],
            //     filterMode: 'filter',
            //     top:'97%'
            // }
            // ],

        xAxis: [
            {gridIndex: 0, type:'time'},
            {gridIndex: 1, type:'time'},
            {gridIndex: 2, type:'time'},
            {gridIndex: 3, type:'time'},
            {gridIndex: 4, type:'time'},
            {gridIndex: 5, type:'time'}

        ],

        yAxis: [
            {gridIndex: 0,type:'value',minInterval:10},
            {gridIndex: 1,type:'value',minInterval:10},
            {gridIndex: 2,type:'value',minInterval:10},
            {gridIndex: 3,type:'value',minInterval:10},
            {gridIndex: 4,type:'value',minInterval:10},
            {gridIndex: 5,type:'value',minInterval:10}
        ],
            series: []
        };

        // 使用刚指定的配置项和数据初始化图表。
        myChart.setOption(option,true);
    }

function init_echart_cpu_mem()
    {
        var xdata = []
        var ydata = []
        // 指定图表的配置项和数据
        var option = {
            title: [
                {left: '0%', text: 'CPU使用(%):'},
                {left: '48%',  text:'内存使用(%):'}],

            tooltip: {
                trigger: 'axis',
                axisPointer: {animation: true}
            },

            grid:[
                {top:'10%',left:'5%', width: '40%', height: '60%'},
                {top:'10%',left:'54%', width: '40%', height: '60%'}
            ],

            toolbox:{
                show: true,
                feature:{
                    my_range_button:{
                            show:true,
                            title:'选择时间范围',
                            icon:'path://M432.45,595.444c0,2.177-4.661,6.82-11.305,6.82c-6.475,0-11.306-4.567-11.306-6.82s4.852-6.812,11.306-6.812C427.841,588.632,432.452,593.191,432.45,595.444L432.45,595.444z M421.155,589.876c-3.009,0-5.448,2.495-5.448,5.572s2.439,5.572,5.448,5.572c3.01,0,5.449-2.495,5.449-5.572C426.604,592.371,424.165,589.876,421.155,589.876L421.155,589.876z M421.146,591.891c-1.916,0-3.47,1.589-3.47,3.549c0,1.959,1.554,3.548,3.47,3.548s3.469-1.589,3.469-3.548C424.614,593.479,423.062,591.891,421.146,591.891L421.146,591.891zM421.146,591.891',
                            option:{},
                            onclick:function(opt){
                                $("#time_range").modal('show');
                                }
                    },
                    magicType : {show: true, type: ['line', 'bar']},
                    dataZoom:{show: true, yAxisIndex:true},

                }
            },

        //    legend: {data:['监控项1']},

            //暂未发现用途，现行注释（2017/04/24 10:39）
            // dataZoom:[{
            //     id: 'dataZoomX',
            //     type: 'slider',
            //     xAxisIndex: [0],
            //     filterMode: 'filter',
            //     top:'29%'
            // },{
            //     id: 'dataZoomX2',
            //     type: 'slider',
            //     xAxisIndex: [1],
            //     filterMode: 'filter',
            //     top:'29%'
            // },{
            //     id: 'dataZoomX3',
            //     type: 'slider',
            //     xAxisIndex: [2],
            //     filterMode: 'filter',
            //     top:'63%'
            // },{
            //     id: 'dataZoomX4',
            //     type: 'slider',
            //     xAxisIndex: [3],
            //     filterMode: 'filter',
            //     top:'63%'
            // },
            // {
            //     id: 'dataZoomX5',
            //     type: 'slider',
            //     xAxisIndex: [4],
            //     filterMode: 'filter',
            //     top:'97%'
            // },{
            //     id: 'dataZoomX6',
            //     type: 'slider',
            //     xAxisIndex: [5],
            //     filterMode: 'filter',
            //     top:'97%'
            // }
            // ],

        xAxis: [
            {gridIndex: 0, type:'time'},
            {gridIndex: 1, type:'time'}

        ],

        yAxis: [
            {gridIndex: 0,type:'value',minInterval:10},
            {gridIndex: 1,type:'value',minInterval:10}
        ],
            series: []
        };

        // 使用刚指定的配置项和数据初始化图表。
        myChart.setOption(option,true);
    }

/**
 * 请求数据
 * @param ip
 * @param start_time
 * @param end_time
 */
function refresh_mon(ip,ipList,start_time,end_time){
                    var data_s = [];
                    data_s.push(ipList);
                    var data=JSON.stringify({"ip_list": data_s, "start_time": start_time, "end_time": end_time});
                   $.ajax({
                        type:"POST",
                        url:"/monitor",
                        data:data,
                        success:function(result){
                             if(JSON.stringify(result.data) == "{}"){
                                 showMessage("监控平台返回数据为空！", "danger", 1000);
                                 return;
                             }
                             var series=[];
                             var res =  result.data;
                             console.info('res');
                             console.info(res);
                             if(!res){return console.info('error')};
                                   $.each(res[ip], function (index, ip_data) {
                                       series.push(
                                           {
                                               name: ip,
                                               symbol:'none',
                                               type:'line',
                                               animationEasing: 'linear',
                                               xAxisIndex: index,
                                               yAxisIndex: index,
                                               data:ip_data
                                           }
                                   );
                                   });
                               myChart.setOption({series: series})
                        },
                        error: function(){
                            //请求出错处理
                        }

                    })
    }


/**
 * 获取集群监控信息
 * @param hostpool_id
 * @param start_time
 * @param end_time
 */
function refresh_mon_cluser(name,hostpool_id,start_time,end_time,rep_url){


                   $.ajax({
                        type:"GET",
                        url:rep_url,
                        data:{"start_time": start_time, "end_time": end_time},
                        success:function(result){
                             if(result.data[0].length == 0){
                                 showMessage("监控平台返回数据为空！", "danger", 1000);
                                 return;
                             }

                             var series=[];
                             var res =  result.data;
                                   $.each(res, function (index, ip_data) {
                                       series.push(
                                           {
                                               name: name,
                                               symbol:'none',
                                               type:'line',
                                               animationEasing: 'linear',
                                               xAxisIndex: index,
                                               yAxisIndex: index,
                                               data:ip_data
                                           }
                                   );
                                   });
                               myChart.setOption({series: series})
                        },
                        error: function(){
                            //请求出错处理
                        }

                    })
    }
