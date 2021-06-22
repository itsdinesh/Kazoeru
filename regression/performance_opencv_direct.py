from imutils.video import VideoStream
import cv2

# # For threads define a function
def cam1():
    cap = VideoStream("../vid/Test Video.mp4").start()
    n = 0

    while True:
        img = cap.read()
        n = n + 1
        cv2.putText(img, str(n), (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
        cv2.imshow('frame', img)
        cv2.waitKey(1)

cam1()