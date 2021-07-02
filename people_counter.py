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
input = "./vid/LRT Encoded V6.1.mkv"

class Camera(BaseCamera):
    @staticmethod
    def frames():
        frame_counter = 0
        cap = cv2.VideoCapture(input)
        total_frames = 0
        object_id_list = []
        frameCount = 0
        frameRate = 10
        status = "N/A"

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

                    # if CLASSES[idx] == "train":
                    #     print("Train")

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
                # text = "ID: {}".format(objectId)
                # cv2.putText(frame, text, (x1, y1 - 5), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 0, 255), 1)

                # if objectId not in object_id_list:
                #    object_id_list.append(objectId)

            # Person Count Indicator
            lpc_count = len(objects)
            lpc_txt = "Live Person Count: {}".format(lpc_count)
            cv2.putText(frame, lpc_txt, (5, 30), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 255), 1)

            # Video Length Indicator
            length = frameCount / 30
            length = "Video Length: {:.2f}".format(length)
            cv2.putText(frame, length, (5, 60), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 255, 255), 1)

            # Crowd Status Indicator
            if (lpc_count) > 5:
                status = "Crowded"
                cv2.putText(frame, status, (5, 90), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 0, 255), 2)
            else:
                status = "Not Crowded"
                cv2.putText(frame, status, (5, 90), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 128, 0), 2)

            # Pass as JPG frames to Flask Web App
            yield cv2.imencode('.jpg', frame)[1].tobytes()

            # # OpenCV Window
            # cv2.imshow("Application", frame)
            # key = cv2.waitKey(1)
            # if key == ord('q'):
            #     break