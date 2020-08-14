# import the necessary packages
from imutils.video import VideoStream
from imutils.video import FPS
import face_recognition
import threading
import argparse
import imutils
import pickle
import serial
import time
import cv2
import VL53L1X

#main calss for facial recognition for alphabot
class alphabotFaceRecognition:

    def __init__(self,lock, person):
        print("[INFO] loading encodings + face detector...")
        #initializing distance sensor
        self.UPDATE_TIME_MICROS = 66000
        self.INTER_MEASUREMENT_PERIOD_MILLIS = 70
        self.tof = VL53L1X.VL53L1X(i2c_bus=1, i2c_address=0x29)
        self.tof.open()
        self.tof.set_timing(self.UPDATE_TIME_MICROS, self.INTER_MEASUREMENT_PERIOD_MILLIS)
        self.tof.start_ranging(0)
        #classifer location of haarcascade
        classifierXML = 'haarcascade_frontalface_default.xml'
        self.detector = cv2.CascadeClassifier(classifierXML)
        # loading database of the recognized faces
        self.data = pickle.loads(open("encodings.pickle", "rb").read())
        self.viweingImage = None
        self.lock = lock
        self.targetPerson =  person
        self.currentPerson = [] #global list of currently detected person
        #initial value for the camera base
        self.servoProperties = {'servoHeadVal'  :90,
                                'servoBaseVal'  :90,
                                'servoMaxVal'   :160,
                                'servoMinVal'   :20,
                                'servoDir'      :'toMax' #other value is toMin

                            }

        #arduino driving command
        self.arduinoComnd = {'stop'     :'{"Car":"Stop"}',
                            'forward'   :'{"Car":"Forward"}',
                            'backward'  :'{"Car":"Backward"}',
                            'turnleft_deg'  :'{"Car":"Left","Value":[',
                            'turnright_deg' :'{"Car":"Right","Value":[',
                            'turnLeft'  :'{"Car":"Left"}',
                            'turnRight' :'{"Car":"Right"}'
                        }
        

        # initialize the video stream and allow the camera sensor to warm up
        print("[INFO] starting video stream...")
        #camera and serial comm for PC
        #self.vs = VideoStream(src=0).start()
        #self.serialComm=serial.Serial("/dev/ttyUSB0",115200)

        #uncomment this line for raspberry pi
        self.vs = VideoStream(usePiCamera=True).start()
        self.serialComm=serial.Serial("/dev/ttyS0",115200)
        
        time.sleep(2.0)
        #setting up servo initially
        #self.initialServoSetup()

    #It is the main function of the class which calls other functions. this method is to get an image and find faces, 
    def imageProcessMain(self):
        while True:
            # grab the frame from the threaded video stream and resize it
            # to 500px (to speedup processing)
            self.frame = self.vs.read()
            self.frame = imutils.resize(self.frame, width=500)
            
            # convert the input frame from (1) BGR to grayscale (for face
            # detection) and (2) from BGR to RGB (for face recognition)
            gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
            rgb = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)

            # detect faces in the grayscale frame
            rects = self.detector.detectMultiScale(gray, scaleFactor=1.1, 
                minNeighbors=5, minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE)

            # OpenCV returns bounding box coordinates in (x, y, w, h) order
            # but we need them in (top, right, bottom, left) order, so we
            # need to do a bit of reordering
            boxes = [(y, x + w, y + h, x) for (x, y, w, h) in rects]

            # compute the facial embeddings for each face bounding box
            encodings = face_recognition.face_encodings(rgb, boxes)
            self.currentPerson = self.identifyFaces(encodings)
            self.drawBoxOnFaces(boxes,self.currentPerson)

    		# acquire the lock, set the output frame, and release the
            # lock
            with self.lock:
                self.viweingImage = self.frame.copy()
            #continue scanning with camera
            if self.targetPerson not in self.currentPerson:
                self.scanForPerson()
            
            
            # display the image to our screen
            #cv2.imshow("Frame", self.frame)
            key = cv2.waitKey(1) & 0xFF
            
            # if the `q` key was pressed, break from the loop
            if key == ord("q"):
                break
        cv2.destroyAllWindows()


    #this function dig through all the detected faces and try to recognize them from the data base
    #this function input is detected faces  and return identified faces
    def identifyFaces(self,detectedFaces):
        #dictonary in which face is being identyfied
        names = []
        # loop over the facial embeddings
        for encoding in detectedFaces:
            # attempt to match each face in the input image to our known
            # encodings
            matches = face_recognition.compare_faces(self.data["encodings"],encoding)
            name = "Unknown"

            # check to see if we have found a match
            if True in matches:
                # find the indexes of all matched faces then initialize a
                # dictionary to count the total number of times each face
                # was matched
                matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                counts = {}

                # loop over the matched indexes and maintain a count for
                # each recognized face face
                for i in matchedIdxs:
                    name = self.data["names"][i]
                    counts[name] = counts.get(name, 0) + 1

                # determine the recognized face with the largest number
                # of votes (note: in the event of an unlikely tie Python
                # will select first entry in the dictionary)
                name = max(counts, key=counts.get)
            
            # update the list of names
            names.append(name)
        #returning all the recognized faces
        return names

    #draw rectangles around the faces on the image
    def drawBoxOnFaces(self,boxes, identifiedFaces):
        # loop over the recognized faces
        for ((top, right, bottom, left), name) in zip(boxes, identifiedFaces):
            # draw the predicted face name on the image
            cv2.rectangle(self.frame, (left, top), (right, bottom),
                (0, 255, 0), 2)
            y = top - 15 if top - 15 > 15 else top + 15
            cv2.putText(self.frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
                0.75, (0, 255, 0), 2)

    #this function is run on a different thread to simultiniously move the camera to find the desired person
    def scanForPerson(self):
        #{"Servo":"Servo1","Angle":180}
        #change direction of camera movement
                   
        if self.servoProperties.get('servoBaseVal') >= self.servoProperties.get('servoMaxVal'):
            self.servoProperties['servoDir'] = 'toMin' #change direction toMin
        if self.servoProperties.get('servoBaseVal') <= self.servoProperties.get('servoMinVal'):
            self.servoProperties['servoDir'] = 'toMax' #change direction toMin

        servoBase = '{"Servo":"Servo1","Angle":'+str(self.servoProperties.get('servoBaseVal'))+'}'
        #print ('sending speed value: ',servoBase)
        self.serialComm.write(bytes(servoBase.encode("ascii"))) 
        #print ('finisehed sending ')
        
        #update curent camera value
        if self.servoProperties.get('servoDir') == 'toMax':
            self.servoProperties['servoBaseVal'] = self.servoProperties.get('servoBaseVal') + 3 
        else:
            self.servoProperties['servoBaseVal'] = self.servoProperties.get('servoBaseVal') - 3 

        time.sleep(0.5)

    #this function runs only initially to set the servo at good position
    def initialServoSetup(self):
        
        servoBase = '{"Servo":"Servo1","Angle":'+str(90)+'}'
        servoHead = '{"Servo":"Servo2","Angle":'+str(80)+'}'

        self.serialComm.write(bytes(servoHead.encode("ascii"))) 
        time.sleep(0.2)
        self.serialComm.write(bytes(servoBase.encode("ascii")))

    def driveToPerson(self):
        while True:
            if self.targetPerson in self.currentPerson:
                #check if the robot is aligined with the person by checking the servo position
                servoPostion = int(self.servoProperties.get('servoBaseVal'))
                if servoPostion not in range(80,100):
                    
                    turnAngle = (abs(servoPostion - 90))# deviding the value by 10 now need to adjust
                    print ('trying to turn with angle :', turnAngle)
                    #if servoPostion < 90:
                        #serialCommand = self.arduinoComnd.get('turnleft')+ str(turnAngle) +']}'
                        #SerialCommand = self.arduinoComnd.get('')
                        #self.serialComm.write(bytes(serialCommand.encode("ascii")))
                    #else:
                        #serialCommand = self.arduinoComnd.get('turnright')+ str(turnAngle) +']}'
                        #self.serialComm.write(bytes(serialCommand.encode("ascii")))
                    
                    self.servoProperties['servoBaseVal'] = 90
                    servoBase = '{"Servo":"Servo1","Angle":'+str(self.servoProperties.get('servoBaseVal'))+'}'
                    #print ('sending speed value: ',servoBase)
                    #self.serialComm.write(bytes(servoBase.encode("ascii"))) 
                #drive forward if the person is found 
    def driveAround(self):
        # flag toi keep tarck of direction
        stopFlag = False
        #defines for state
        forward = 1        
        stop = 2
        left = 3
        right = 4
        #distance to stop in mm
        distToStop = 500 
        # setting current state to move forward
        curState = forward 
        currentDistance = 0
        #making sure that speed it set might not be necessary
        for i in range(4):
            self.driveSetSpeed(150)
            time.sleep(0.3)
        #main loop for driving
        while 1:
            #checking distance for negetive value
            tempDistance  = self.tof.get_distance()
            if tempDistance >0:
                currentDistance = tempDistance

            if currentDistance > distToStop and curState == forward:
                self.driveForward()
                #forward = True
                #stop = False
                #print ("continue driving, distance :",currentDistance)
            elif currentDistance <= distToStop and stopFlag == False:
                self.driveStop()
                curState = left
                #forward = False
                stopFlag = True
                #print('stopped,distance is :',currentDistance)
            elif currentDistance <= distToStop and curState == left:
                self.driveLeft()
                curState = forward
                stopFlag = False 
            else:
                curState = forward
                stopFlag = False
                print('unknown state :', stopFlag, curState,currentDistance)
            key = cv2.waitKey(1) & 0xFF
            print("current state :",curState," current distance :", currentDistance)
            # if the `q` key was pressed, break from the loop
            if key == ord("q"):
                break
            time.sleep(self.INTER_MEASUREMENT_PERIOD_MILLIS / 1000.0) 
        print('exiting programm')
        self.driveStop()
        self.vs.release()
        cv2.destroyAllWindows()
        


    #function to move forward
    def driveForward(self):
        serialCmnd = self.arduinoComnd.get('forward')
        self.serialComm.write(bytes(serialCmnd.encode('ascii')))

    #function to drive backward
    def driveBackward(self):
        serialCmnd = self.arduinoComnd.get('backward')
        self.serialComm.write(bytes(serialCmnd.encode('ascii')))

    #function to stop the robot
    def driveStop(self):
        serialCmnd = self.arduinoComnd.get('stop')
        self.serialComm.write(bytes(serialCmnd.encode('ascii')))
   
    #function to turn left
    def driveLeft(self):
        serialCmnd = self.arduinoComnd.get('turnLeft')
        self.serialComm.write(bytes(serialCmnd.encode('ascii')))
        time.sleep(0.9)
        self.driveStop()

    #function to turn left
    def driveRight(self):
        serialCmnd = self.arduinoComnd.get('turnRight')
        self.serialComm.write(bytes(serialCmnd.encode('ascii')))
        time.sleep(0.1)
        self.driveStop()

    #function to set speed
    def driveSetSpeed(self, speed):
        #templet speed command == {"Car":"SetSpeed","Value":[250,200]}
        speedVal = '{"Car":"SetSpeed","Value":[' + str(speed) +','+ str(speed) + ']}'
        self.serialComm.write(bytes(speedVal.encode('ascii')))




    



# create an empty face for the image

lock = threading.Lock()
namesss = 'golam'
runIt = alphabotFaceRecognition(lock,namesss)
time.sleep(0.2)
#runIt.imageProcessMain()
print('starting proscess for imageProcess')
imageProcess 	= threading.Thread(target=runIt.imageProcessMain,daemon=True)
imageProcess.start()
print('staing driveAround process')
drive = threading.Thread(target=runIt.driveAround,daemon=True)
drive.start()
while True:
    time.sleep(0.5)
    #print('going infinie')
