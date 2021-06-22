from imutils.video import VideoStream
import numpy as np
import imutils
import cv2

print("[INFO] loading model...")
protopath = "models/MobileNetSSD_deploy.prototxt"
modelpath = "models/MobileNetSSD_deploy.caffemodel"
net = cv2.dnn.readNetFromCaffe(protopath, modelpath)

print("[INFO] starting video stream...")
vs = VideoStream("../vid/LRT Encoded V8.3.mkv").start()

while True:
    frame = vs.read()
    frame = imutils.resize(frame, width=1000)

    (h, w) = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(frame)

    net.setInput(blob)
    detections = net.forward()

    for i in range(0, detections.shape[2]):
        confidence = detections[0, 0, i, 2]

        if confidence < 0.5:
             continue

        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
        (startX, startY, endX, endY) = box.astype("int")

        text = "{:.2f}%".format(confidence * 100)
        y = startY - 10 if startY - 10 > 10 else startY + 10
        cv2.rectangle(frame, (startX, startY), (endX, endY),
                      (0, 255, 0), 2)
        cv2.putText(frame, text, (startX, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 2)

    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

# cv2.destroyAllWindows()
# vs.stop()