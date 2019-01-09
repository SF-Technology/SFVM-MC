#coding = utf8




import sys,os

def init_env():
    '''
        导入sys path
    :return:
    '''
    file_basic_path = os.path.dirname(os.path.abspath(__file__))

    basic_path = file_basic_path[0:-len('/script')]
    os.environ["BASIC_PATH"] = basic_path
    sys.path.append( basic_path )
    sys.path.append( basic_path+'/config')
    sys.path.append( basic_path+'/helper')
    sys.path.append( basic_path+'/lib')
    sys.path.append( basic_path+'/model')
    sys.path.append( basic_path+'/interface')
