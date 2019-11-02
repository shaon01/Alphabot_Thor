# import the necessary packages
from imutils.video import VideoStream
from imutils.video import FPS
import face_recognition
import threading
import argparse
import imutils
import pickle
import time
import cv2


#main calss for facial recognition for alphabot
class alphabotFaceRecognition:

    def __init__(self,lock):
        print("[INFO] loading encodings + face detector...")
        #classifer location of haarcascade
        classifierXML = 'haarcascade_frontalface_default.xml'
        self.detector = cv2.CascadeClassifier(classifierXML)
        # loading database of the recognized faces
        self.data = pickle.loads(open("encodings.pickle", "rb").read())
        self.viweingImage = None
        self.lock = lock

        # initialize the video stream and allow the camera sensor to warm up
        print("[INFO] starting video stream...")
        self.vs = VideoStream(src=1).start()
        # self.vs = VideoStream(usePiCamera=True).start()
        time.sleep(2.0)

        # start the FPS counter
        self.fps = FPS().start()

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
            names = self.identifyFaces(encodings)
            self.drawBoxOnFaces(boxes,names)

    		# acquire the lock, set the output frame, and release the
            # lock
            with self.lock:
                self.viweingImage = self.frame.copy()
            
            # display the image to our screen
            cv2.imshow("Frame", self.frame)
            key = cv2.waitKey(1) & 0xFF

            # if the `q` key was pressed, break from the loop
            if key == ord("q"):
                break

            # update the FPS counter
            self.fps.update()

        self.fps.stop()
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
                    print ('Found some one: ',str (counts[name]))

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



'''
# create an empty face for the image
imageFrame = None

runIt = alphabotFaceRecognition(imageFrame)
runIt.imageProcessMain()

print("[INFO] elasped time: {:.2f}".format(runIt.fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(runIt.fps.fps()))
'''


