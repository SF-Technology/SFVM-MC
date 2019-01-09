# # coding=utf8
# '''
#     镜像websocket服务
# '''
#
# from lib.websocket.my_socket import socketio, emit, app
# from flask import copy_current_request_context
# from flask.ext.login import current_user
# from flask import request
#
#
# @socketio.on('request_for_response')
# def test_websocket():
#     #data = request.values.get('param')
#     return_msg = {
#         'code': '200',
#         'msg': 'start to process...'
#     }
#     with app.test_request_context():
#         emit('response', return_msg, namespace='/', broadcast=True)
#
#
# test_websocket()
