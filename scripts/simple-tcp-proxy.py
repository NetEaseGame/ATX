#!/usr/bin/env python
import tornado.ioloop
import maproxy.proxyserver
import socket

# HTTP->HTTP: On your computer, browse to "http://127.0.0.1:81/" and you'll get http://www.google.com
server = maproxy.proxyserver.ProxyServer("127.0.0.1", 26944)
server.listen(5555)
print("Local IP:", socket.gethostbyname(socket.gethostname()))
print("0.0.0.0:5555 -> 127.0.0.1:26944")
tornado.ioloop.IOLoop.instance().start()