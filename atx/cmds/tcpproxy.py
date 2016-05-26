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


def main(forward=26944, host='127.0.0.1', listen=5555):
    '''
    Args:
        - forward(int): local forward port
        - host(string): local forward host
        - listen(int): listen port
    '''
    # HTTP->HTTP: On your computer, browse to "http://127.0.0.1:81/" and you'll get http://www.google.com
    server = maproxy.proxyserver.ProxyServer("127.0.0.1", forward)
    server.listen(listen)
    print("Local IP:", socket.gethostbyname(socket.gethostname()))
    print("0.0.0.0:{} -> {}:{}".format(listen, host, forward))
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()