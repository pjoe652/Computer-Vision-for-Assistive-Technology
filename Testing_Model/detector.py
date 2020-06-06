from imageai.Prediction.Custom import CustomImagePrediction
from imageai.Detection import ObjectDetection
import tensorflow as tf
import os
import cv2
import time
import requests
import traceback
import base64

config = tf.ConfigProto()
config.gpu_options.allow_growth = True
sess = tf.Session(config=config)

execution_path = os.getcwd()
prediction = CustomImagePrediction()
prediction.setModelTypeAsResNet()
prediction.setModelPath("model_ex-129_acc-0.860215.h5")
prediction.setJsonPath("pose_model_class.json")
prediction.loadModel(num_objects=3)

detector = ObjectDetection()
detector.setModelTypeAsRetinaNet()
detector.setModelPath(os.path.join(execution_path , "resnet50_coco_best_v2.0.1.h5"))
detector.loadModel()

human_objects = detector.CustomObjects(person=True)
bed_objects = detector.CustomObjects(bed=True)

'''
    Use if creating a video with the bounding boxes
'''
fourcc = cv2.VideoWriter_fourcc(*'XVID')
# Output file
out = cv2.VideoWriter("demo_dark_lying_3.mp4",fourcc, 3, (1920,1080))

# Input file
cap = cv2.VideoCapture('new_lying.mp4')

correct = 0
count = 0
frameCount = 0

while(cap.isOpened()):
    ret, frame = cap.read()
    count += 1
    img = frame
    crop_img = frame
    pose = "not identified"
    human_detected = False
    percentage_human = []
    human_boxes = []
    human_lowest = 0
    human_real = []
    # Capture frame every 30 frames
    if((count % 30) == 0) :
        frameCount += 1
        # Human detection
        try:
            human_returned_image, human_detections = detector.detectCustomObjectsFromImage(custom_objects=human_objects, input_type="array", input_image=img, output_type="array", minimum_percentage_probability=10)
            for eachObject in human_detections:
                percentage_human.append(eachObject['percentage_probability'])
                human_boxes.append(eachObject['box_points'])
        except Exception as e:
            # Break from loop if video ended
            break

        # If humans are detected
        if(len(percentage_human) != 0):
            highest_percent = max(percentage_human)
            box = human_boxes[percentage_human.index(highest_percent)]
            human_lowest = box[0]
            human_real = [box[0],box[1],box[2],box[3]]
            cv2.rectangle(img,(box[0],box[1]), (box[2],box[3]),(0,255,255),2)
            if(box[0] < 0):
                box[0] = 0
            elif (box[1] < 0):
                box[1] = 0
            elif (box[2] < 0):
                box[2] = 0
            elif (box[3] < 0):
                box[3] = 0
            print(box)
            human_detected = True
            # Get bounding box around human
            crop_img = img[box[1]:box[3], box[0]:box[2]]

        # Posture detection
        if(human_detected):
            predictions, probabilities = prediction.predictImage(crop_img, result_count=3, input_type="array")
            pose = predictions[0]
            percentage_bed = []
            bed_boxes = []
            # If lying check if resting
            if(pose == "lying"):
                # Bed detection
                bed_returned_image, bed_detections = detector.detectCustomObjectsFromImage(custom_objects=bed_objects, input_type="array", input_image=img, output_type="array", minimum_percentage_probability=50)
                for eachObject in bed_detections:
                    percentage_bed.append(eachObject['percentage_probability'])
                    bed_boxes.append(eachObject['box_points'])
                    
                # If bed detected
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
                    # If human is above the bed
                    if((human_real[0] >= box[0]) & (human_real[1] >= box[1]) & (human_real[2] <= box[2]) & (human_real[3] <= box[3])):
                        pose = "sleeping"
                    print(box)

        # Attach text of pose and percentage certainty
        if(human_detected):
            cv2.putText(img, pose + " - " + '{0:.2f}'.format(float(probabilities[0])) ,(human_real[0],human_real[1]), cv2.FONT_HERSHEY_COMPLEX, 2, (255,255,255), 2, cv2.LINE_AA)

        # Counts number of correct poses, should be changed to whatever the footage of it. i.e. if using input video of someone standing, then pose should == 'standing'
        if(pose == 'sleeping'):
            correct += 1

        # Write image out to output video
        out.write(img)
        print("--------------------------------------")
        print(frameCount)
        print(pose)
        # Print percentage correct
        print((correct/frameCount)*100)
        

