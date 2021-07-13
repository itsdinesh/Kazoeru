import cv2
import imutils
import numpy as np
from video_thread import VideoThread
from tracker.centroid_tracker import CentroidTracker

protopath = "models/MobileNetSSD_deploy.prototxt"
modelpath = "models/MobileNetSSD_deploy.caffemodel"
net = cv2.dnn.readNetFromCaffe(protopath, modelpath)

CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
           "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
           "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
           "sofa", "train", "tvmonitor"]

detector = cv2.dnn.readNetFromCaffe(prototxt=protopath, caffeModel=modelpath)
tracker = CentroidTracker()
input_video = "./vid/LRT Pasar Seni.mkv"
status = [0, 0, 0]


class Video(VideoThread):
    @staticmethod
    def frames():
        cap = cv2.VideoCapture(input_video)
        frameCount = 0
        frameRate = 10
        train_indicator = 0
        train_duration = 8
        train_status = "N/A"

        if not cap.isOpened():
            raise RuntimeError('Could not find the video or start the video.')

        while True:
            # Capture every 10th frame of the footage
            frameCount += frameRate
            cap.set(1, frameCount)
            ret, frame = cap.read()
            # Resize frames to width of 700.
            frame = imutils.resize(frame, width=700)

            # If the last frame is almost reached, restart the footage from the first frame.
            if (frameCount + frameRate) > cap.get(cv2.CAP_PROP_FRAME_COUNT):
                frameCount = 0
                train_indicator = 0  # Reset train indicator for video loop
                cv2.putText(frame, "Train Departed", (5, 120), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 128, 0), 2)
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

            # Slice frames
            (H, W) = frame.shape[:2]
            # Input frame into DNN with the frame, scale factor and size.
            blob = cv2.dnn.blobFromImage(frame, 0.01, (W, H))
            detector.setInput(blob)
            person_detections = detector.forward()
            rects = []

            # Confidence Level Tracking
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

            # Create bounding boxes around people and track their movement.
            boundingboxes = np.array(rects)
            boundingboxes.astype(int)
            objects = tracker.update(rects)  # Tracking via the Centroid Tracker algorithm.

            # Update the person's coordinates when they move.
            for (objectId, bbox) in objects.items():
                x1, y1, x2, y2 = bbox
                x1 = int(x1)
                y1 = int(y1)
                x2 = int(x2)
                y2 = int(y2)

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)

            # Person Count Indicator
            crowd_count = len(objects)
            lpc_txt = "Live Person Count: {}".format(crowd_count)
            cv2.putText(frame, lpc_txt, (5, 30), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 255), 1)

            # Video Length Indicator
            length = frameCount / 30
            length = "Video Length: {:.2f}".format(length)
            cv2.putText(frame, length, (5, 60), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 255, 255), 1)

            # Crowd Status Indicator
            if crowd_count > 4:
                crowd_status = "Crowded"
                cv2.putText(frame, crowd_status, (5, 90), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 0, 255), 2)
            else:
                crowd_status = "Not Crowded"
                cv2.putText(frame, crowd_status, (5, 90), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 128, 0), 2)

            if train_indicator == 0 or train_indicator > train_duration:
                train_status = "Train Departed"
                cv2.putText(frame, train_status, (5, 120), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 0, 255), 2)

            if 0 < train_indicator < train_duration:
                train_status = "Train Arrived"
                cv2.putText(frame, train_status, (5, 120), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 128, 0), 2)

            # Pass crowd counting data in a list to be shown in raw text on the website.
            status[0] = crowd_count
            status[1] = crowd_status
            status[2] = train_status

            yield cv2.imencode('.jpg', frame)[1].tobytes()

    @staticmethod
    def get_crowd_count():
        return status
