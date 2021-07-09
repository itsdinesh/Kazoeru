import cv2
import datetime
import imutils
import numpy as np
from base_camera import BaseCamera
from centroid_tracker import CentroidTracker

protopath = "models/MobileNetSSD_deploy.prototxt"
modelpath = "models/MobileNetSSD_deploy.caffemodel"
net = cv2.dnn.readNetFromCaffe(protopath, modelpath)

CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
           "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
           "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
           "sofa", "train", "tvmonitor"]

detector = cv2.dnn.readNetFromCaffe(prototxt=protopath, caffeModel=modelpath)
tracker = CentroidTracker(maxDisappeared=10)
fps_start_time = datetime.datetime.now()
input_camera = "./vid/LRT Encoded V8.3.mkv"
crowd_count = []


class Camera(BaseCamera):
    @staticmethod
    def frames():
        cap = cv2.VideoCapture(input_camera)
        frameCount = 0
        frameRate = 10
        train_indicator = 0
        train_duration = 8

        if not cap.isOpened():
            raise RuntimeError('Could not find the video or start the camera.')

        while True:
            # Capture every 10th frame of the footage
            frameCount += frameRate
            cap.set(1, frameCount)

            ret, frame = cap.read()
            frame = imutils.resize(frame, width=700)

            # If the last frame is almost reached, restart the footage from the first frame.
            if (frameCount + frameRate) > cap.get(cv2.CAP_PROP_FRAME_COUNT):
                frameCount = 0
                train_indicator = 0  # Reset train indicator for video loop
                cv2.putText(frame, "Train Departed", (5, 120), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 128, 0), 2)
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

            (H, W) = frame.shape[:2]
            blob = cv2.dnn.blobFromImage(frame, 0.007843, (W, H), 127.5)

            detector.setInput(blob)
            person_detections = detector.forward()
            rects = []

            for i in np.arange(0, person_detections.shape[2]):
                confidence = person_detections[0, 0, i, 2]
                if confidence > 0.75:
                    idx = int(person_detections[0, 0, i, 1])

                    if CLASSES[idx] == "train":
                        train_indicator += 1  # Train has been detected

                    if CLASSES[idx] != "person":
                        continue

                    person_box = person_detections[0, 0, i, 3:7] * np.array([W, H, W, H])
                    (startX, startY, endX, endY) = person_box.astype("int")
                    rects.append(person_box)
                    label = "{}: {:.2f}%".format(CLASSES[idx], confidence * 100)
                    cv2.putText(frame, label, (startX, startY), cv2.FONT_HERSHEY_PLAIN, 1.5, (0, 255, 0), 2)

            boundingboxes = np.array(rects)
            boundingboxes.astype(int)
            objects = tracker.update(rects)

            for (objectId, bbox) in objects.items():
                x1, y1, x2, y2 = bbox
                x1 = int(x1)
                y1 = int(y1)
                x2 = int(x2)
                y2 = int(y2)

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)

            # Person Count Indicator
            lpc_count = len(objects)
            crowd_count.append(lpc_count)
            lpc_txt = "Live Person Count: {}".format(lpc_count)
            cv2.putText(frame, lpc_txt, (5, 30), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 255), 1)

            # Video Length Indicator
            length = frameCount / 30
            length = "Video Length: {:.2f}".format(length)
            cv2.putText(frame, length, (5, 60), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 255, 255), 1)

            # Crowd Status Indicator
            if lpc_count > 5:
                status = "Crowded"
                cv2.putText(frame, status, (5, 90), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 0, 255), 2)
            else:
                status = "Not Crowded"
                cv2.putText(frame, status, (5, 90), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 128, 0), 2)

            if train_indicator == 0 or train_indicator > train_duration:
                cv2.putText(frame, "Train Departed", (5, 120), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 0, 255), 2)

            if 0 < train_indicator < train_duration:
                cv2.putText(frame, "Train Arrived", (5, 120), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 128, 0), 2)

            # Pass as JPG frames to Flask Web App
            yield cv2.imencode('.jpg', frame)[1].tobytes()

    @staticmethod
    def get_crowd_count():
        return crowd_count[-1]