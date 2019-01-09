# -*- coding:utf-8 -*-
# __author__ =  ""

# !/usr/bin/env python

import os
import sys
import logging
import json

def init_env():
    import sys
    import os
    reload(sys)
    sys.setdefaultencoding('utf-8')
    file_basic_path = os.path.dirname(os.path.abspath(__file__))
    print file_basic_path
    basic_path = file_basic_path[0:-17]
    os.environ["BASIC_PATH"] = basic_path  # basic path 放到全局的一个变量当中去
    sys.path.append(basic_path)
    sys.path.append(basic_path + '/config')
    sys.path.append(basic_path + '/helper')
    sys.path.append(basic_path + '/lib')
    sys.path.append(basic_path + '/model')
    sys.path.append(basic_path + '/controller')
    sys.path.append(basic_path + '/service')
    print sys.path


init_env()

DIR_PATH = os.path.dirname(os.path.abspath(__file__))
ROOT_PATH = os.path.abspath(os.path.join(DIR_PATH, '..', ''))

CERT = DIR_PATH + '/cert.pem'


import Cookie
import socket
import requests
# from config.default import WS_PORT, WS_HOST, WS_CERT, WS_KEY

# from vrtManager.connection import CONN_SSH, CONN_SOCKET

# import re

# from tunnel import Tunnel

from optparse import OptionParser

parser = OptionParser()

parser.add_option("-v",
                  "--verbose",
                  dest="verbose",
                  action="store_true",
                  help="Verbose mode",
                  default=False)

parser.add_option("-d",
                  "--debug",
                  dest="debug",
                  action="store_true",
                  help="Debug mode",
                  default=False)

parser.add_option("-H",
                  "--host",
                  dest="host",
                  action="store",
                  help="Listen host",
                  default='0.0.0.0')

parser.add_option("-p",
                  "--port",
                  dest="port",
                  action="store",
                  help="Listen port",
                  default=6080 or 6080)

parser.add_option("-c",
                  "--cert",
                  dest="cert",
                  action="store",
                  help="Certificate file path",
                  default=None or CERT)

parser.add_option("-k",
                  "--key",
                  dest="key",
                  action="store",
                  help="Certificate key file path",
                  default=None)

parser.add_option("--ssl-only",
                  dest="ssl_only",
                  action="store_true",
                  help="Deny non-ssl connections",
                  default=False)

(options, args) = parser.parse_args()

FORMAT = "%(asctime)s - %(name)s - %(levelname)s : %(message)s"
if options.debug:
    logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    options.verbose = True
elif options.verbose:
    logging.basicConfig(level=logging.INFO, format=FORMAT)
else:
    logging.basicConfig(level=logging.WARNING, format=FORMAT)

try:
    from websockify import WebSocketProxy

    try:
        from websockify import ProxyRequestHandler
    except ImportError:
        USE_HANDLER = False
    else:
        USE_HANDLER = True
except ImportError:
    try:
        from novnc.wsproxy import WebSocketProxy
    except ImportError:
        print('Unable to import a websockify implementation, ' +
              'please install one')
        sys.exit(1)
    else:
        USE_HANDLER = False



class CompatibilityMixIn(object):
    def _new_client(self, daemon, socket_factory):
        cookie = Cookie.SimpleCookie()
        cookie.load(self.headers.getheader('cookie'))
        if 'token' not in cookie:
            self.msg('No token cookie found !')
            return False
        token = str(cookie['token'].value)
        session = str(cookie['session'].value)
        # session = ""
        # token = ""

        # 验证cookie是否合法
        user_url = 'http://localhost:8080/login/user'
        cookie = {'session': session}
        r = requests.get(user_url, cookies=cookie)
        if r.status_code != 200:
            return 0

        ret = json.loads(r.text.decode('utf-8'), encoding='utf-8')
        if ret['code'] == -10005:
            return 0
        elif ret['code'] != 0:
            return 0

        temptoken = token.split('-', 1)
        host = str(temptoken[0])
        port = int(temptoken[1])
        """
        cnx_debug_msg = "Connexion infos :\n"
        cnx_debug_msg += "- connhost : '%s'\n" % connhost
        cnx_debug_msg += "- connport : '%s'\n" % connport
        cnx_debug_msg += "- connuser : '%s'\n" % connuser
        cnx_debug_msg += "- conntype : '%s'\n" % conntype
        cnx_debug_msg += "- console_host : '%s'\n" % console_host
        cnx_debug_msg += "- console_port : '%s'\n" % console_port
        cnx_debug_msg += "- console_socket : '%s'\n" % console_socket
        logging.debug(cnx_debug_msg)
        """
        tsock = socket_factory(host, port, connect=True)
        tunnel = None
        """
        if console_socket and conntype == CONN_SOCKET:
            # Local socket on local host
            self.msg('Try to open local socket %s' % console_socket)
            tsock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            tsock.connect(console_socket)
        elif console_socket or re.match('^127\.', console_host) and conntype != CONN_SOCKET:
            # Need tunnel to physical host
            if conntype != CONN_SSH:
                self.msg("Need a tunnel to access console but can't mount " +
                         "one because it's not a SSH host")
                raise
            try:
                # generate a string with all placeholders to avoid TypeErrors
                # in sprintf
                # https://github.com/retspen/webvirtmgr/pull/497
                error_msg = "Try to open tunnel on %s@%s:%s on console %s:%s "
                error_msg += "(or socket %s)"
                self.msg(error_msg % (connuser, connhost, connport,
                                      console_host, console_port, console_socket))
                tunnel = Tunnel()
                fd = tunnel.open(connhost, connuser, connport,
                                 console_host, console_port, console_socket)
                tsock = socket.fromfd(fd, socket.AF_INET, socket.SOCK_STREAM)
            except Exception as e:
                self.msg("Fail to open tunnel : %s" % e)
                raise
            self.msg("Tunnel openned")
        else:
            # Direct access
            self.msg("connecting to: %s:%s" % (connhost, console_port))
            tsock = socket_factory(connhost, console_port, connect=True)
            tunnel = None
        """

        if self.verbose and not daemon:
            print(self.traffic_legend)

        # Start proxying
        try:
            self.msg("Start proxying")
            self.do_proxy(tsock)
        except:
            if tunnel:
                """
                self.vmsg(
                    "%s:%s (via %s@%s:%s) : Target closed" %
                    (console_host, console_port, connuser, connhost, connport))
              """
                if tsock:
                    tsock.shutdown(socket.SHUT_RDWR)
                    tsock.close()
                if tunnel:
                    tunnel.close()
            raise


if USE_HANDLER:
    class NovaProxyRequestHandler(ProxyRequestHandler, CompatibilityMixIn):
        def msg(self, *args, **kwargs):
            self.log_message(*args, **kwargs)

        def vmsg(self, *args, **kwargs):
            if self.verbose:
                self.msg(*args, **kwargs)

        def new_websocket_client(self):
            """
            Called after a new WebSocket connection has been established.
            """
            # Setup variable for compatibility
            daemon = self.server.daemon
            socket_factory = self.server.socket

            self._new_client(daemon, socket_factory)

else:
    class NovaWebSocketProxy(WebSocketProxy, CompatibilityMixIn):

        def new_client(self):
            """
            Called after a new WebSocket connection has been established.
            """
            # Setup variable for compatibility
            daemon = self.daemon
            socket_factory = self.socket

            self._new_client(daemon, socket_factory)

if __name__ == '__main__':
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webvirtmgr.settings")
    if USE_HANDLER:
        # Create the WebSocketProxy with NovaProxyRequestHandler handler
        server = WebSocketProxy(RequestHandlerClass=NovaProxyRequestHandler,
                                listen_host=options.host,
                                listen_port=options.port,
                                source_is_ipv6=False,
                                verbose=options.verbose,
                                cert=options.cert,
                                key=options.key,
                                ssl_only=options.ssl_only,
                                daemon=False,
                                record=False,
                                web=False,
                                traffic=False,
                                target_host='ignore',
                                target_port='ignore',
                                wrap_mode='exit',
                                wrap_cmd=None)
    else:
        # Create the NovaWebSockets proxy
        server = NovaWebSocketProxy(listen_host=options.host,
                                    listen_port=options.port,
                                    source_is_ipv6=False,
                                    verbose=options.verbose,
                                    cert=options.cert,
                                    key=options.key,
                                    ssl_only=options.ssl_only,
                                    daemon=False,
                                    record=False,
                                    web=False,
                                    target_host='ignore',
                                    target_port='ignore',
                                    wrap_mode='exit',
                                    wrap_cmd=None)
    server.start_server()
