#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import html
import threading
import struct
import socket
import time


import upnp_templates

currentURI = None

MCAST_GRP = '239.255.255.250'
MCAST_PORT = 1900
IS_ALL_GROUPS = True

ssdpResponseSock = None
ssdpMulticastSock = None
ssdpThread = None
httpThread = None

def SSDPServerLoop():
    global ssdpMulticastSock, ssdpResponseSock
    ssdpMulticastSock = socket.socket(
        socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    ssdpMulticastSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if IS_ALL_GROUPS:
        # on this port, receives ALL multicast groups
        ssdpMulticastSock.bind(('', MCAST_PORT))
    else:
        # on this port, listen ONLY to MCAST_GRP
        ssdpMulticastSock.bind((MCAST_GRP, MCAST_PORT))
    mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
    ssdpMulticastSock.setsockopt(
        socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    ssdpResponseSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        req, sender = ssdpMulticastSock.recvfrom(10240)
        req = req.decode('utf8')
        if req.startswith('M-SEARCH'):
            print('Handling SSDP search request: ')
            #print(req)
            print('Sender: %s:%d' % (sender))
            handleSSDPSearchRequest(req, sender)

def SSDPThread():
    global ssdpMulticastSock, ssdpResponseSock
    while True:
        try:
            print('Starting SSDP server on udp:%d' % MCAST_PORT)
            SSDPServerLoop()
        except KeyboardInterrupt as e:
            print('SSDP Exception: ')
            print(e)
        if ssdpMulticastSock != None:
            try:
                ssdpMulticastSock.close()
                ssdpMulticastSock = None
            except:
                pass
        if ssdpResponseSock != None:
            try:
                ssdpResponseSock.close()
                ssdpResponseSock = None
            except:
                pass
        time.sleep(5)




def startSSDPService():
    global ssdpThread

    ssdpThread = threading.Thread(target=SSDPThread)
    ssdpThread.daemon = True
    ssdpThread.start()



def handleSSDPSearchRequest(req, sender):
    st = 'urn:schemas-upnp-org:service:AVTransport:1'
    for line in req.split('\n'):
        l = line.strip()
        if l.startswith('ST:'):
            requiredST = l.split(':', 1)[1].strip()
            st = requiredST
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(sender)
    myIP = s.getsockname()[0]
    print('My IP Address is: %s' % myIP)
    resp = (upnp_templates.TEMPLATE_SSDP_RESPONSE % (myIP, st, st))
    resp = resp.replace('\n', '\r\n')
    #print('Response: ')
    #print(resp)
    s.send(resp.encode('utf8'))
    s.close()


def handleControl(req, reqType):
    global currentURI
    resp = ''
    action = ''
    respVal = ''
    if req.find('<u:') != -1:
        action = req.split('<u:', 1)[1].split('>', 1)[
            0].split(' ', 1)[0].strip()
    print('Handle %s, action: %s' % (reqType, action))
    if action == 'SetAVTransportURI':
        arr = req.split('<CurrentURI>', 1)
        if len(arr) > 1:
            uri = arr[1].split('</CurrentURI>', 1)[0]
            uri = html.unescape(uri)
            print("====== SetAVTransportURI called, url: ")
            print(uri)
            print('======')
            currentURI = uri
    if action == 'GetVolume':
        respVal = '<CurrentVolume>100</CurrentVolume>'
    resp = upnp_templates.TEMPLATE_CONTROL_RESPONSE % (action, reqType, respVal, action)
    #print(resp)
    return resp


import tornado.ioloop
import tornado.web
import asyncio

class MainHandler(tornado.web.RequestHandler):
    def get(self, name):
        path = self.request.path
        if path == '/':
            self.sendXMLResponse(upnp_templates.TEMPLATE_MAIN_XML)
        if path == '/AVTransport/scpd.xml':
            self.sendXMLResponse(upnp_templates.TEMPLATE_AVTRANSPORT_SCPD)
        if path == '/ConnectionManager/scpd.xml':
            self.sendXMLResponse(upnp_templates.TEMPLATE_CONNECTIONMANAGER_SCPD)
        if path == '/RenderingControl/scpd.xml':
            self.sendXMLResponse(upnp_templates.TEMPLATE_RENDERINGCONTROL_SCPD)
    
    def post(self, name):
        path = self.request.path
        resp = ''
        postData = self.request.body.decode('utf8')
        #print(postData)
        if self.request.path == '/AVTransport/control.xml':
            resp = handleControl(postData, 'AVTransport')
        if self.request.path == '/RenderingControl/control.xml':
            resp = handleControl(postData, 'RenderingControl')
        self.sendXMLResponse(resp)
    
    def sendXMLResponse(self, xml):
        self.set_status(200)
        self.set_header('Content-type', 'text/xml; charset="utf-8"')
        self.write(xml.replace('\n', '\r\n'))

def make_app():
    return tornado.web.Application([
        (r"/(.*)", MainHandler),
    ])


def HTTPServerThread():
    asyncio.set_event_loop(asyncio.new_event_loop())
    app = make_app()
    while True:
        try:
            print('Starting HTTP server on port 1288...')
            app.listen(1288)
            tornado.ioloop.IOLoop.current().start()
        except Exception as e:
            print('HTTP server failed, retry...')
            print(e)
        time.sleep(5)
    


def startHTTPServer():
    global httpThread
    httpThread = threading.Thread(target=HTTPServerThread)
    httpThread.daemon = True
    httpThread.start()


if __name__ == "__main__":
    startSSDPService()
    HTTPServerThread()
    sys.exit()
