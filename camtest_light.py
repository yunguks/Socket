try:
    import cv2
except ImportError:
    print("ERROR python-opencv must be installed")
    exit(1)
from bh1750 import readLight
import datetime
import pandas as pd
import time
from buffercleaner import *

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
count = []
while True:
    start = time.time()
    ret, img = cap.read()
    if ret == False:
        print("Error reading image")
        break

    img = cv2.flip(img,-1)
    #print(img.shape)
    cv2.imshow("C920", img)
    k = cv2.waitKey(27) # cam 27
    #print(k)
    now = datetime.datetime.now()
    now_time = now.strftime("%m%d_%H%M%S")
    print(now_time)
    count.append([now_time,readLight()])
    dirname = '/home/pi/Socket/images/sunset'
    
    fname = dirname +'/'+now_time+'.jpg'
    print(fname)
    cv2.imwrite(fname,img)

    if k == 109: # k = m
        f = f'sample{i}.jpg'
        cv2.imwrite(f,img)
        print(f'sample{i}.jpg saved')
        print(f'Light = {readLight()}')
        i +=1
    elif k == ord('t'):
        print(f'Light = {readLight()}')
    if k == 27: # 20fps
        df = pd.DataFrame(count)
        
        df.to_csv(f"Light.csv",mode = 'a', index=False, header=None)
        
        break
    end = time.time()
    delay = 60-(start-end)
    time.sleep(delay)
cv2.destroyAllWindows()
cap_cleaner.raise_exception()
cap_cleaner.join()
cap.release()