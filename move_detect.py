try:
    import cv2
except ImportError:
    print("ERROR python-opencv must be installed")
    exit(1)

from buffercleaner import *
import time


cap = cv2.VideoCapture(2)
#cap = cv2.VideoCapture(1)

if not cap.isOpened():
    print("Camera not found!")
    exit(1)
try:
    cap_cleaner = CameraBufferCleanerThread(cap)
    time.sleep(1)

    print(f"Resolution : {cap.get(3)}x{cap.get(4)}")
    print(f"FPS : {cap.get(5)}")

    first_frame = cap_cleaner.last_frame
    first_frame = cv2.cvtColor(first_frame, cv2.COLOR_RGB2GRAY)
    first_frame = cv2.flip(first_frame,-1)

    #subtractor = cv2.createBackgroundSubtractorMOG2(history=10,varThreshold=100,detectShadows=False)

    print("Running, ESC or Ctrl-c to exit...")
    i = 0
    while True:
        ret, img = cap.read()
        if ret == False:
            print("Error reading image")
            break
        img = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
        img = cv2.flip(img,-1)

        diff = cv2.absdiff(first_frame, img)
        _, diff = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

        # mask = subtractor.apply(img)    
        
        cv2.imshow("diff", diff)
        k = cv2.waitKey(30) # cam 27
        #print(k)

        if k == 27: # 20fps
            break
finally:
    cap_cleaner.raise_exception()
    cap_cleaner.join()
    cap.release()
    cv2.destroyAllWindows()
