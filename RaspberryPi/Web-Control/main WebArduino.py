#!/usr/bin/python
# -*- coding:utf-8 -*-
from bottle import get,post,run,route,request,template,static_file
from AlphaBot import AlphaBot
import threading
import socket #ip
import os,sys
import serial

arduinoComnd = {'stop'      :'{"Car":"Stop"}',
                'forward'   :'{"Car":"Forward"}',
                'backward'  :'{"Car":"Backward"}',
                'turnleft'  :'{"Car":"Left"}',
                'turnright' :'{"Car":"Right"}',
                'speed'     :''

                }

car = AlphaBot()
ser=serial.Serial("/dev/ttyAMA0",115200)  

@get("/")
def index():
	return template("index")
	
@route('/<filename>')
def server_static(filename):
    return static_file(filename, root='./')

@route('/fonts/<filename>')
def server_fonts(filename):
    return static_file(filename, root='./fonts/')
	
@post("/cmd")
def cmd():
    code = request.body.read().decode()
    speed = request.POST.get('speed')
    serialCmnd = arduinoComnd.get(code)
    print('Recived serial command   :', code)
    print('Serial command to arduino:', serialCmnd)
    try:
        ser.write(bytes(serialCmnd.encode("ascii"))) 
        pass
    except expression as identifier:
        print ('Serial send error :', identifier)
        pass

def camera():
    lastpath = os.path.abspath(os.path.join(os.getcwd(), "../"))
    print("lastpath = %s" %lastpath)
    campath = lastpath + '/mjpg-streamer-experimental/'
    print("campath = %s" %campath)
    os.system(campath  + './mjpg_streamer -i "' + campath + './input_uvc.so" -o "' + campath + './output_http.so -w ' + campath + './www"') 

tcamera = threading.Thread(target = camera)
tcamera.setDaemon(True)
tcamera.start()

s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
s.connect(('8.8.8.8',80))
localhost=s.getsockname()[0]
run(host = localhost, port = 8000)
