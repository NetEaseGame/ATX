#!/usr/bin/env python
# coding: utf-8

from __future__ import print_function

import sys
try:
    import maproxy.proxyserver
except:
    sys.exit("Require maproxy installed. Run: pip install maproxy")

import tornado.ioloop
import socket


def main(local_port=26944, local_host='127.0.0.1', listen_port=5555):
    # HTTP->HTTP: On your computer, browse to "http://127.0.0.1:81/" and you'll get http://www.google.com
    server = maproxy.proxyserver.ProxyServer("127.0.0.1", local_port)
    server.listen(listen_port)
    print("Local IP:", socket.gethostbyname(socket.gethostname()))
    print("0.0.0.0:{} -> {}:{}".format(listen_port, local_host, local_port))
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()