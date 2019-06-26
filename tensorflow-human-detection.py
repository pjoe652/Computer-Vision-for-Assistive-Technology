# Code adapted from Tensorflow Object Detection Framework
# https://github.com/tensorflow/models/blob/master/research/object_detection/object_detection_tutorial.ipynb
# Tensorflow Object Detection Detector

from imageai.Prediction.Custom import CustomImagePrediction
import os
import numpy as np
import tensorflow as tf
import cv2
import time
import glob

config = tf.ConfigProto()
config.gpu_options.allow_growth = True
sess = tf.Session(config=config)

class DetectorAPI:
    def __init__(self, path_to_ckpt):
        self.path_to_ckpt = path_to_ckpt

        self.detection_graph = tf.Graph()
        with self.detection_graph.as_default():
            od_graph_def = tf.GraphDef()
            with tf.gfile.GFile(self.path_to_ckpt, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')

        self.default_graph = self.detection_graph.as_default()
        self.sess = tf.Session(graph=self.detection_graph)

        # Definite input and output Tensors for detection_graph
        self.image_tensor = self.detection_graph.get_tensor_by_name('image_tensor:0')
        # Each box represents a part of the image where a particular object was detected.
        self.detection_boxes = self.detection_graph.get_tensor_by_name('detection_boxes:0')
        # Each score represent how level of confidence for each of the objects.
        # Score is shown on the result image, together with the class label.
        self.detection_scores = self.detection_graph.get_tensor_by_name('detection_scores:0')
        self.detection_classes = self.detection_graph.get_tensor_by_name('detection_classes:0')
        self.num_detections = self.detection_graph.get_tensor_by_name('num_detections:0')

    def processFrame(self, image):
        # Expand dimensions since the trained_model expects images to have shape: [1, None, None, 3]
        image_np_expanded = np.expand_dims(image, axis=0)
        # Actual detection.
        start_time = time.time()
        (boxes, scores, classes, num) = self.sess.run(
            [self.detection_boxes, self.detection_scores, self.detection_classes, self.num_detections],
            feed_dict={self.image_tensor: image_np_expanded})
        end_time = time.time()

        print("Elapsed Time:", end_time-start_time)

        im_height, im_width,_ = image.shape
        boxes_list = [None for i in range(boxes.shape[1])]
        for i in range(boxes.shape[1]):
            boxes_list[i] = (int(boxes[0,i,0] * im_height),
                        int(boxes[0,i,1]*im_width),
                        int(boxes[0,i,2] * im_height),
                        int(boxes[0,i,3]*im_width))

        return boxes_list, scores[0].tolist(), [int(x) for x in classes[0].tolist()], int(num[0])

    def close(self):
        self.sess.close()
        self.default_graph.close()

if __name__ == "__main__":
    model_path = 'B:/Users/PJoe9/Desktop/tensorflow/faster_rcnn_inception_v2_coco_2018_01_28/frozen_inference_graph.pb'
    odapi = DetectorAPI(path_to_ckpt=model_path)
    threshold = 0.7

    # Parameters initialize prediction module
    execution_path = os.getcwd()
    prediction = CustomImagePrediction()
    prediction.setModelTypeAsResNet()
    prediction.setModelPath("model_ex-129_acc-0.860215.h5")
    prediction.setJsonPath("pose_model_class.json")
    prediction.loadModel(num_objects=3)

    # For Model Training
    ''' files = os.listdir("B:/Users/PJoe9/Desktop/recognition/idenprof/train/standing")

    for i in range(len(files)):
        files[i] = "B:/Users/PJoe9/Desktop/recognition/idenprof/train/standing/" + files[i]
        img = cv2.imread(files[i], 1)
        img = cv2.resize(img, (1280, 720))
        boxes, scores, classes, num = odapi.processFrame(img)
        box = boxes[0]
        crop_img = img[box[0]:box[2],box[1]:box[3]]
        cv2.imwrite('standing'+ str(i) + ".jpg",crop_img)
    '''

    cap = cv2.VideoCapture(0)

    while True:
        r, img = cap.read()
        img = cv2.resize(img, (1280, 720))

        boxes, scores, classes, num = odapi.processFrame(img)

        # Visualization of the results of a detection.

        for i in range(len(boxes)):
            # Class 1 represents human
            if classes[i] == 1 and scores[i] > threshold:
                box = boxes[i]
                cv2.rectangle(img,(box[1],box[0]),(box[3],box[2]),(255,0,0),2)
                crop_img = img[box[0]:box[2],box[1]:box[3]]
                break

    #     # crop_img = img[box[0]:box[2],box[1]:box[3]]
    #     # print(box[1],box[0],box[3],box[2])
    #     cv2.rectangle(img,(box[1],box[0]),(box[3],box[2]),(255,0,0),2)

        predictions, probabilities = prediction.predictImage(crop_img, result_count=3, input_type="array")

        for eachPrediction, eachProbability in zip(predictions, probabilities):
            print(eachPrediction , " : " , eachProbability)

        print("------------------------------")
        print("------------------------------")
        cv2.imshow("preview", img)
        key = cv2.waitKey(3000)
        if key & 0xFF == ord('q'):
            break

