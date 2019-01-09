# flask-d
	flask框架的二次封装,更加方便的添加接口,能启动多个服务,并提供常用的组件
	
## 原生方式启动
	cd bin/
	python main.py api_web_0 start
	
	api_web_0来自配置文件default.py中GLOBAL_CONFIG中的flask变量
	'flask' : {
        'api_web_0' : {
            'host' : '0.0.0.0',
            'port' : 19400,  
            #只有开发环境和测试环境才开启debug模式  线上环境一般情况不要开启该选项 不需要的话请去掉该项
            #开启debug模式之后 代码修改之后会自动加载  不需要重启应用程序
            'debug_mode' : False,
            'reg_module_name' : 'web_api',   #这里对应reg_route文件中的相关名字
            'logLevel' : 'DEBUG',
            'logPath' : './api_web_0.log'
        },
    },
    
    
## uwsgi方式启动
	bin目录中添加2个与uwsgi相关的文件main_uwsgi.py和uwsgi_config.xml


## 目录结构
### bin
    main.py   可执行文件
    
### collect_data
    host目录 收集host相关状态信息
    instances目录 收集instance相关状态信息
    
### common_data_struct
    通用用于前端展示的数据实体
    
### config
    default.py 默认的配置文件
    develop.py 默认的开发环境配置文件,在这里能通过覆盖default.py中的变量 让开发环境拥有不同的配置
    
                               
### consumer_handler
    handler_register.py 消息队列消息体中KEY与处理函数的映射
    
### controller
    web_api 不同的项目可以分不同的目录
        --reg_route   url路由文件
        
        #路由的代码
	    app.add_url_rule(rule='/dashboard/v1', view_func=dashboard_v1, methods=['GET'])
    other_api 不同的项目可以分不同的目录
        --reg_route   url路由文件
    reg_route.py  总的路由文件
    
### deploy
    pypi_requirement.txt  该项目依赖的外部包定义 使用pip来安装的包定义
                          pip install -r pypi_requirement.txt
    pip_cache  项目依赖的python安装包
    pip_other  项目预留的python安装包
    install_package_local.sh  安装到本地环境的执行脚本
    install_package.sh  安装到虚拟环境的执行脚本
    
### doc
    项目相关文档，包括各模块的接口说明的md文档
    
### helper
    encrypt_helper.py  des加密和解密库
    hash_helper.py
    http_helper.py     封装simple_get操作和simple_post操作
    ip_helper.py       获取客户端的真实ip地址
    json_helper.py     json的read 和 write操作
                       flask返回json数据 或 jsonp数据
    log_helper.py      日志组件  可以新建每天一个log文件的日志或日志按照指定大小切割
    md5_helper.py
    regex_helper.py    常用正则封装
    time_helper.py     常用时间和日期操作封装

### lib
    常用主键的类库封装
    cache
    core 对flask调用方式进行了包装
    dbs 数据库
    other
    monitor Balent监控方法封装
    serveroperate 物理机IPML调用
    shell Ansible方法调用封装
    
### model
	数据模型文件夹
	
### script
	脚本文件夹  跟flask没有关联,放在这里是为了能调用到config和helper和libs的代码

### service
    各模块的服务层
    
### static
    项目前端静态资源文件
	
### test
    单元测试目录
 
    
## 核心文件介绍

	--lib/core/flask_app.py   #对flask进行的简单的封装

	class My_Flask(Flask):
	
		#这里继承Flask,主要是想在一个总的入口的地方打印出每次请求的耗时,客户端的真实ip地址,请求的GET或POST参数
		
		
		def dispatch_request(self):
			''' 这里重写了Falsk中的该方法 '''
			#省略
			pass

	def get_flask_app():
    	global FLASK_GLOBAL_APP
    	if not FLASK_GLOBAL_APP:
        	FLASK_GLOBAL_APP = My_Flask(__name__)
		#注册每次请求之前的hook
    	FLASK_GLOBAL_APP.before_request(my_before_request)
    	#定义异常处理handler
    	FLASK_GLOBAL_APP.register_error_handler(BaseException, global_error_handler)
    	return FLASK_GLOBAL_APP			
    	
    def global_error_handler( exception ):
        #全局的错误处理handler
    	from flask import request
    	errinfo = traceback.format_exc()
    	errinfo = 'path:%s args:%s %s'%(request.full_path,request.values,errinfo)
    	log_helper.log_error( errinfo , True)
    	resp = {
        'code' : ErrorCode.SYS_ERR,
    	}
    	return json_helper.write(resp)
    	
    	
## 辅助函数介绍
### helper/encrypt_helper.py
	加密:
              print encrypt('123456')
              输出  wBeB+BZ0ABg=

    解密:
              print decrypt("wBeB+BZ0ABg=")
              输出 123456

    encrypt和decrypt中的key参数可以自行更换,但是必须是16个字节或24个字节
### helper/hash_helper.py
	计算字符串的sha1指和md5指
    
    sha1('123456')
    
    md5('123456')
### helper/http_helper.py    
	get 和 post 方法的简单封装

    #url
    #params dict  {'name':'zhansan',  'blog':'hiroguo.me'}
    #timeout 超时时间
    #decode_json_resp  True/False 是否需要对结果json解码
    simple_get(url, params, timeout, decode_json_resp)
    simple_post(url, params, timeout, decode_json_resp)
### helper/ip_helper.py
	get_real_ip(request)   #获取用户的真实ip地址,request是flask中的对象
### helper/log_helper.py
    日志文件自动按照每天的日期切分
    
    filename log文件名 包含路径
    **kwargs  backupCount  最多保存多少天
              logLevel  可选指  DEBUG INFO ERROR WARNGING  
    add_timed_rotating_file_handler(filename, **kwargs)

### helper/time_helper.py
	get_datetime_str()  #获取当前的日期 2015-10-20 14:21:01
	get_date_ymd_str()  #获取当前的日志 年月日 2015-10-20
	get_timestamp(is_int=1)  #return 时间戳, is_int指是1或0 表示 时间戳是否需要整形返回
	get_future_datetime(seconds) #未来的日期 seconds表示未来的多少秒 return 2015-10-11 21:11:03
	get_before_datetime(seconds) #过去的日期 seconds表示未来的多少秒 return 2015-10-11 21:11:03
	datetime_to_str(the_datetime) #datetime类型转换成标准时间字符串 2015-10-11 21:11:03
	datetime_to_timestamp(the_datetime,is_float=False) #datetime类型转换成时间戳 return int/float
	
	
## 类库介绍
### lib/dbs/mysql.py
    使用DBUtils为MySQLDB客户端的连接池二次封装 (线程安全的)

    依赖config default.py当中的配置文件
        'db':{
            'user' : {
                        'db_type' : 'mysql',
                        'maxconnections' : 30,  #允许的最大连接数,
                        'user' : 'test_user',
                        'passwd' : 's5IQABSd8G4=',
                        'host' : '127.0.0.1',
                        'port' : 3306,
                        'charset' : 'utf8',   #不指定的话,默认utf8
                        'database_name' : 'test_db_nmae' #数据库的名字
                    },
            'goods' : {
                        'db_type' : 'mysql',
                        'maxconnections' : 30,  #允许的最大连接数,
                        'user' : 'test_user_2',
                        'passwd' : 's5IQABSd8G4=',
                        'host' : '127.0.0.1',
                        'port' : 3306,
                        'charset' : 'utf8',   #不指定的话,默认utf8
                        'database_name' : 'test_db_name2', #数据库的名字
                    },
        },

    用法:
        from dbs.mysql import Mysql
        db_pool = Mysql.get_instance('goods')    #这里的goods字符串来自于上面的配置前面可key
        #从连接池中获取一个可用的连接
        db_connection = db_pool.get_connection()

        #select语句
        sql = "select * from test_table where id = %s"
        args = [222]
        res = db_pool.query(db_connection, sql, args)  #还有query_one方法

        #insert语句
        sql = "insert into test_table (name) values (%s)"
        args = ["name2"]
        #请传入刚才获取的db连接db_connection变量
        lastrowid = db_pool.insert(db_connection, sql, ['g3'])   #插入成功则返回主键id
        #请显式的提交事务  不要开启auto_commit
        db_pool.commit(db_connection)

        #update语句
        sql = "update test_table set name = %s where id = %s"
        args = ['name_333', 66]
        #请传入刚才获取的db连接db_connection变量
        db_pool.execute(db_connection, sql, args)
        #请显式的提交事务  不要开启auto_commit
        db_pool.commit(db_connection)
         
         

	

	
    
   
                   
