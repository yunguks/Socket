try:
    import cv2
except ImportError:
    print("ERROR python-opencv must be installed")
    exit(1)
import datetime
import pandas as pd
import time
from buffercleaner import *
from bh1750 import readLight
cap = cv2.VideoCapture(2)
#cap = cv2.VideoCapture(1)
cap_cleaner = CameraBufferCleanerThread(cap)

if not cap.isOpened():
    print("Camera not found!")
    exit(1)

#cap.set(3,640)
#cap.set(4,480)
print(f"Resolution : {cap.get(3)}x{cap.get(4)}")
print(f"FPS : {cap.get(5)}")

cv2.namedWindow("C920", cv2.WINDOW_NORMAL | cv2.WINDOW_AUTOSIZE)
print("Running, ESC or Ctrl-c to exit...")
i = 0

while True:
    start = time.time()
    #ret, img = cap.read()
    img = cap_cleaner.last_frame
    img = cv2.flip(img,-1)
    #print(img.shape)
    cv2.imshow("C920", img)
    k = cv2.waitKey(27) # cam 27
    #print(k)

    if k == ord('s'): # k = m
        f = f'sample{i}.jpg'
        cv2.imwrite(f,img)
        print(f'sample{i}.jpg saved')
        
        i +=1
    elif k == ord('t'):
        print(f'Light = {readLight()}')
    if k == 27: # 20fps
        break
    end = time.time()
    delay = 5-(start-end)
    #time.sleep(delay)
cv2.destroyAllWindows()
cap_cleaner.raise_exception()
cap_cleaner.join()
cap.release()