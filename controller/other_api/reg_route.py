#coding=utf8

from controller.other_api.i_util import rate_limit
from controller.other_api.e_host_metric import host_metric_manage as hmm


def reg(app):
    '''
    '''

    ##### example  ####
    app.add_url_rule(rule='/rate_limit',  view_func=rate_limit.rate_limit, methods=['POST','GET'])
    #提供 给思远的restful api 接口，把传入的数据插入到数据库 表 tb_host_performance。
    app.add_url_rule(rule='/host_data_todb', view_func=hmm.flush_host_perform_data_to_db, methods=['POST'])
    # 获取最新的一条host 性能数据【没限制是哪台物理机】
    app.add_url_rule(rule='/get_host_data', view_func=hmm.get_host_perform_data, methods=['GET'])
    # 提供给思远的 restful api 接口，根据传入的host ip 获取最新的一条数据。
    app.add_url_rule(rule='/get_host_data/hostip', view_func=hmm.get_host_perform_data_by_hostip, methods=['POST'])