import serial, time

speed1 = 70
speed2 = 100
stopCmd = '{"Car":"Stop"}'
forward = '{"Car":"Forward"}'
speedVal1 = '{"Car":"SetSpeed","Value":[' + str(speed1) +','+ str(speed1) + ']}'
speedVal2 = '{"Car":"SetSpeed","Value":[' + str(speed2) +','+ str(speed2) + ']}'
ser=serial.Serial("/dev/ttyS0",115200) 

#ser.write(bytes(speedVal1.encode('ascii')))
#ser.write(bytes(forward.encode("ascii"))) 
#time.sleep(5)
#ser.write(bytes(speedVal2.encode('ascii')))
#ser.write(bytes(forward.encode("ascii"))) 
#time.sleep(5)
ser.write(bytes(stopCmd.encode("ascii"))) 

