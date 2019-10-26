#!/usr/bin/python
# -*- coding:utf-8 -*-
from bottle import get,post,run,route,request,template,static_file
import threading
import socket #ip
import os,sys
import serial

arduinoComnd = {'stop'      :'{"Car":"Stop"}',
                'forward'   :'{"Car":"Forward"}',
                'backward'  :'{"Car":"Backward"}',
                'turnleft'  :'{"Car":"Left"}',
                'turnright' :'{"Car":"Right"}',
                'speed'     :'{"Car":"SetSpeed","Value":[250,250]}'

                }


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
    robotDirection = arduinoComnd.get(code)
    print('Recived serial command   :', code)
    print('Serial command to arduino direction:', robotDirection)
    print('Serial command to arduino direction:', speed)

    try:
        ser.write(bytes(robotDirection.encode("ascii"))) 
        if speed != None:
            #templet speed command == {"Car":"SetSpeed","Value":[250,200]}
            speedVal = '{"Car":"SetSpeed","Value":[' + str(speed) +','+str(speed) + ']}'
            print ('got speed val: ',speedVal)
            #ser.write(bytes(speedVal.encode("ascii"))) 

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
