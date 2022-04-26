try:
    import cv2
except ImportError:
    print("ERROR python-opencv must be installed")
    exit(1)

from buffercleaner import *
import time


cap = cv2.VideoCapture(2)
#cap = cv2.VideoCapture(1)
filter_size = 5
img_list = []
delay = 0.1
img_size = int(3/delay)
mid = int(img_size/2)

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
    first_frame = cv2.blur(first_frame,(filter_size,filter_size))


    #subtractor = cv2.createBackgroundSubtractorMOG2(history=10,varThreshold=100,detectShadows=False)

    print("Running, ESC or Ctrl-c to exit...")
    i = 0
    while True:
        start = time.time()
        
        img = cap_cleaner.last_frame
       
        img = cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
        img = cv2.flip(img,-1)
        #img = cv2.blur(img,(filter_size,filter_size))
        
        if len(img_list) < img_size:
            img_list.insert(0,img)
        else:
            img_list.pop()
            img_list.insert(0,img)

            sub1 = cv2.absdiff(img_list[0],img_list[mid])
            #sub1 = np.where(sub1>1,sub1,0)
            _,sub1 = cv2.threshold(sub1,30,255,cv2.THRESH_BINARY)
            sub2 = cv2.absdiff(img_list[mid],img_list[-1])
            #sub2 = np.where(sub2>5,sub2,0)
            _,sub2 = cv2.threshold(sub2,30,255,cv2.THRESH_BINARY)

            sub3 = cv2.bitwise_and(sub1,sub2)
            
            back = cv2.absdiff(sub3,img_list[mid])
            
            
            mov = cv2.bitwise_or(back,img_list[mid])
            result = cv2.absdiff(mov,img_list[mid])
            #_,result = cv2.threshold(result,100,255,cv2.THRESH_BINARY)
            
            cv2.imshow("diff", result)
        # mask = subtractor.apply(img)    
        
        k = cv2.waitKey(30) # cam 27
        #print(k)
        end= time.time()
        if k == 27: # 
            break
        if (end-start) < 0.1:
            time.sleep(0.1-(end-start))
        end = time.time()
        print(f'1 cycle time {round(end-start,2)}')
finally:
    cap_cleaner.raise_exception()
    cap_cleaner.join()
    cap.release()
    cv2.destroyAllWindows()
