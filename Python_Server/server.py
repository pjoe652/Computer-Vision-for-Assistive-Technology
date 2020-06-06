#!/usr/bin/python
""" server.py

    Part IV Computer Systems Engineering
    Author: Peter Joe (p.joe97@hotmail.com)

    This program uses the CherryPy web server (from www.cherrypy.org).
"""
# Requires:  CherryPy 3.2.2  (www.cherrypy.org)
#            Python  (We use 2.7)

# The address we listen for connections on
listen_ip = "0.0.0.0"
listen_port = 1237

import cherrypy
import database_control
from imageai.Prediction.Custom import CustomImagePrediction
from imageai.Detection import ObjectDetection
import base64
import json
import numpy as np
import cv2
import os
import traceback
import threading
import datetime
import time
import queue
import tensorflow as tf
import atexit
import requests
from pyngrok import ngrok

'''
    This section may or may not be necessary, in the event that you are able to portforward then this does not need to be set. However the mobile application and
    the Raspberry Pi server need to be configured so that they can connect to the recognition server's url. Otherwise if you are not able to portforward, you can uncomment
    the next few lines of code and use pyngrok to bypass your firewall/nat but you need the middleware server.
'''
# # Replace with your own Ngrok auth_token
# ngrok.set_auth_token("")

# # Server runs on port 1237
# public_url = ngrok.connect(1237)
# print(public_url)

# middleware = "https://p4-hoster.herokuapp.com/log"
# data = {
#     "user": "111",
#     "url": public_url,
#     "type": "server"
# }

# print(data)

# r = requests.post(url = middleware, json = data)
# print("Response is :%s", r.text)

config = tf.ConfigProto()
config.gpu_options.allow_growth = True
sess = tf.Session(config=config)

#---------------------Threading for pose identification--------------------------
def thread_start():
    global stop_event
    stop_event = threading.Event()
    global img_queue
    img_queue = queue.Queue()
    store = False
    # First test image to initialize Keras
    test_img = cv2.imread('server.jpg', flags = 1)
    img_queue.put(("Invalid User", test_img, store))

    pose = threading.Thread(target=poseThread, args=(img_queue,)).start()

def poseThread(img_queue):
    # Initializing detectors

    print("Here again!")

    execution_path = os.getcwd()
    global prediction 
    prediction = CustomImagePrediction()
    prediction.setModelTypeAsResNet()

    # Old Model - Higher Accuracy
    prediction.setModelPath("model_ex-129_acc-0.860215.h5")
    prediction.setJsonPath("pose_model_class.json")
    prediction.loadModel(num_objects=3)

    # Parameter initialize detection module for bed
    global detector 
    detector = ObjectDetection()
    detector.setModelTypeAsRetinaNet()
    detector.setModelPath(os.path.join(execution_path , "resnet50_coco_best_v2.0.1.h5"))
    detector.loadModel()

    global human_objects
    human_objects = detector.CustomObjects(person=True)
    global bed_objects 
    bed_objects = detector.CustomObjects(bed=True)   

    while(True):
        if not stop_event.is_set():
            try:
                findPose(img_queue.get(timeout=2))
                print("Logged!")
            except queue.Empty:
                print("Unable to Log!")
                stop_event.set()


def findPose(input_item):
    # Check if there's something inside image buffer
    start = time.time()
    img = input_item[1]
    crop_img = img
    pose = "not_identified"
    human_detected = False
    percentage_human = []
    human_boxes = []
    human_lowest = 0
    human_real = []
    # Get the highest probable human in image
    try:
        human_returned_image, human_detections = detector.detectCustomObjectsFromImage(custom_objects=human_objects, input_type="array", input_image=img, output_type="array", minimum_percentage_probability=10)
        for eachObject in human_detections:
            percentage_human.append(eachObject['percentage_probability'])
            human_boxes.append(eachObject['box_points'])
    except Exception as e:
        print(e)
        traceback.print_exc()
    if(len(percentage_human) != 0):
        highest_percent = max(percentage_human)
        box = human_boxes[percentage_human.index(highest_percent)]
        # Lowest point of the human
        human_lowest = box[0]
        human_real = [box[0],box[1],box[2],box[3]]
        cv2.rectangle(img,(box[0],box[1]), (box[2],box[3]),(255,0,0),2)
        if(box[0] < 0):
            box[0] = 0
        elif (box[1] < 0):
            box[1] = 0
        elif (box[2] < 0):
            box[2] = 0
        elif (box[3] < 0):
            box[3] = 0
        human_detected = True
        crop_img = img[box[1]:box[3], box[0]:box[2]]

    # If a human is detected then perform pose detection
    if(human_detected):
        predictions, probabilities = prediction.predictImage(crop_img, result_count=4, input_type="array")
        pose = predictions[0]
        percentage_bed = []
        bed_boxes = []
        # If human is lying down, then perform bed detection
        if(pose == "lying"):
            bed_returned_image, bed_detections = detector.detectCustomObjectsFromImage(custom_objects=bed_objects, input_type="array", input_image=img, output_type="array", minimum_percentage_probability=10)
            for eachObject in bed_detections:
                percentage_bed.append(eachObject['percentage_probability'])
                bed_boxes.append(eachObject['box_points'])
            
            # If bed is detected then check whether the human is above the bed
            if(len(percentage_bed) != 0):
                highest_percent = max(percentage_bed)
                box = bed_boxes[percentage_bed.index(highest_percent)]
                cv2.rectangle(img,(box[0],box[1]), (box[2],box[3]),(0,255,0),2)
                cv2.putText(img, "Bed - " + '{0:.2f}'.format(float(highest_percent)), (box[0],box[1]), cv2.FONT_HERSHEY_COMPLEX, 2, (255,255,255), 2, cv2.LINE_AA)
                if(box[0] < 0):
                    box[0] = 0
                elif (box[1] < 0):
                    box[1] = 0
                elif (box[2] < 0):
                    box[2] = 0
                elif (box[3] < 0):
                    box[3] = 0
                # cv2.line(img, (box[0],box[1]), (box[2],box[3]), (0,255,0),2)
                if((human_real[0] >= box[0]) & (human_real[1] >= box[1]) & (human_real[2] <= box[2]) & (human_real[3] <= box[3])):
                    pose = "resting"

    if(human_detected):
        cv2.putText(img, pose + " - " + '{0:.2f}'.format(float(probabilities[0])) ,(human_real[0],human_real[1]), cv2.FONT_HERSHEY_COMPLEX, 2, (255,255,255), 2, cv2.LINE_AA)
    done = time.time()
    elapsed_time = (done-start)
    print("====================================")
    print("Computational Time: " + str(elapsed_time) + "s")
    print(pose)

    if input_item[2]:
        retval, buffer = cv2.imencode('.jpg', img)
        jpg_as_text = base64.b64encode(buffer).decode("utf-8")
        database_control.handlePoseLogFile(input_item[0], pose, jpg_as_text)
    else:
        database_control.handlePoseLog(input_item[0], pose)
    
    # cv2.imwrite("lying2.png", img)
    stop_event.set()

class MainApp(object):

    #CherryPy Configuration
    _cp_config = {'tools.encode.on': True, 
                  'tools.encode.encoding': 'utf-8',
                  'tools.sessions.on' : 'True',
                 }       

    database_control.createTable()

    thread_start()

    # If they try somewhere we don't know, catch it here and send them to the right place.
    @cherrypy.expose
    def default(self, *args, **kwargs):
        """The default page, given when we don't recognise where the request is for."""
        Page = "I don't know where you're trying to go, so have a 404 Error."
        cherrypy.response.status = 404
        return Page

    # GET /
    @cherrypy.expose
    def index(self):
        Page = "Hello World!"
        return Page

    # POST /log
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def log(self):
        '''Logs pose into database'''
        try:
            log_details = cherrypy.request.json
            database_control.handlePoseLog(log_details["username"], log_details["pose"])
        except:
            cherrypy.response.status = 400
            print("Error with the JSON")

    # GET /userPose
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def userPose(self, username = "NONE"):
        '''Returns user records from database'''
        try:
            user = database_control.sendPose(username)
            json_user = {
                "username" : user[0],
                "standing" : user[1],
                "sitting" : user[2],
                "lying" : user[3],
                "resting" : user[4],
                "not identified" : user[5]
            }
            return json_user
        except:
            cherrypy.response.status = 400
            print("Error with the JSON") 

    # GET /userRecords
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def userRecords(self, username = "NONE"):
        '''Returns specific captured instance'''
        try:
            records = database_control.sendRecords(username)
            json_records = []
            for record in records:
                temp_record = {
                    "id" : record[0],
                    "username" : record[1],
                    "pose" : record[2],
                    "available" : record[3],
                    "timestamp" : record[4]
                }
                json_records.append(temp_record)
            return json_records
        except:
            cherrypy.response.status = 400
            traceback.print_exc()
            print("Error with the JSON") 

    # GET /clearUser
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def clearUser(self, username = "NONE"):
        '''Clears all user records from database'''
        try:
            database_control.clearUserLog(username)
            complete = username + "'s record has been cleared"
            return complete
        except:
            cherrypy.response.status = 400
            print("Error with the JSON")

    # GET /image?username=X&id=Y
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def getImage(self, username = "NONE", id = 0):
        '''Returns image if username and id are valid'''
        try:
            image = database_control.getImage(username, id)
            temp_img = {
                "id" : image[0],
                "username" : image[1],
                "pose" : image[2],
                "file" : image[3],
                "available" : image[4],
                "timestamp" : image[5]
            }

            return temp_img
        except:
            cherrypy.response.status = 400

    # POST /signin
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def signin(self):
        '''Verifies user credentials'''
        try:
            login_details = cherrypy.request.json
            if(database_control.handleSignin(login_details["username"], login_details["password"])):
                success = login_details["username"] + " has successfully logged in!"
                return success
            else:
                failure = "Incorrect Credentials"
                cherrypy.response.status = 400
                return failure
        except:
            cherrypy.response.status = 400
            print("Error with the JSON")
            traceback.print_exc()

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def identifyPose(self):
        '''Converts base64 to numpy array and places image in global queue'''
        try:
            picture_detail = cherrypy.request.json
            encoded = picture_detail["img"]
            jpg_original = base64.b64decode(encoded)
            jpg_as_np = np.frombuffer(jpg_original, dtype = np.uint8)
            image_buffer = cv2.imdecode(jpg_as_np, flags = 1)
            if picture_detail["store"] == "False" :
                img_queue.put((picture_detail["username"], image_buffer, False))
            else :
                img_queue.put((picture_detail["username"], image_buffer, True))
            stop_event.clear()
            
            # if not thread_started:
            #     pose = threading.Thread(target=poseThread)
            #     pose.start()
            #     pose.join()
            
        

            # cv2.imwrite('server.jpg', image_buffer)
            # img_detect.poseDetection(cv2.imread('server.jpg', flags = 1))

        except Exception as e:  
            print(e)
            cherrypy.response.status = 400
            traceback.print_exc()

def runMainApp():
    # Create an instance of MainApp and tell Cherrypy to send all requests under / to it. (ie all of them)

    cherrypy.tree.mount(MainApp(), "/")

    # Tell Cherrypy to listen for connections on the configured address and port.
    cherrypy.config.update({'server.socket_host': listen_ip,
                            'server.socket_port': listen_port,
                            'engine.autoreload.on': True,
                           })

    print("=========================")
    print("University of Auckland")
    print("COMPSYS302 - Software Design Application")
    print("========================================")                  
    
    # Start the web server
    cherrypy.engine.start()

    # And stop doing anything else. Let the web server take over.
    cherrypy.engine.block()
 
if __name__ == "__main__":
    runMainApp()

#Run the function to start everything


def removeServer():
    url = "https://p4-hoster.herokuapp.com/clearServer?username=111"
    PARAMS = {"username" : "111"}
    r = requests.get(url = url, param = PARAMS)
    return_json = r.json()
    print(return_json)

atexit.register(removeServer)