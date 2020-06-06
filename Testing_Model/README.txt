detector.py reads video files that places a bounding box around detected humans and their poses. It will output a video once it has finished reading through the entire video.

To run this, you must update the input and output files specified in detector.py

You will also need the following files:
- model_ex-129_acc-0.860215 (Posture detection, can be found in "../Python_Server")
- resnet50_coco_best_v2.0.1 (Human and bed detection, can be downloaded from https://github.com/OlafenwaMoses/ImageAI/releases/tag/1.0)