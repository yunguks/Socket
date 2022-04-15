from calendar import c
import cv2
import numpy as np
import time
import math

def onMouse(event,x,y,flags,param):
    global drag,ix,iy,tx,ty,w,h,yellow,img
    if event == cv2.EVENT_LBUTTONDOWN:
        drag = True
        ix,iy=x,y
    elif event == cv2.EVENT_MOUSEMOVE:
        if drag:
            img_draw = img.copy()
            cv2.rectangle(img_draw,(ix,iy),(x,y),yellow,1)
            cv2.imshow('Img',img_draw)
    elif event == cv2.EVENT_LBUTTONUP:
        if drag:
            drag = False
            w = x - ix
            h = y - iy
            if w >= 0 and h >= 0:
                tx += ix
                ty += iy
                img_temp=img[iy:iy+h+1,ix:ix+w+1]
                cv2.imshow('Img',img_temp)

def initcapture(sample_img,n_roi):
    coordinates=[]
    for _ in range(n_roi):
        global drag,ix,iy,tx,ty,w,h,yellow,img
        img = sample_img.copy()
        drag = False
        ix,iy=-1,-1
        tx,ty=0,0
        w,h=0,0
        yellow = (0,255,255)
        cv2.namedWindow('Img',cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Img',(640,480))
        cv2.imshow('Img',img)
        cv2.setMouseCallback('Img',onMouse)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        coordinates.append((ty,ty+h+1,tx,tx+w+1))
        #coordinates.append((iy,iy+h+1,ix,ix+w+1))
        
    # ROI 확인
    for i in range(len(coordinates)):
        y1,y2,x1,x2 = coordinates[i]
        print(y1,y2,x1,x2)
        cv2.imshow("Img",sample_img[y1:y2,x1:x2])
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    ret = True
    # valid = input("want to continue? [y/n] : ").lower()
    # if valid == 'y':
    #     ret = True
    # else:
    #     ret = False
    return ret, coordinates

def homography(roi_img, base_img):
    
    mathcing_num = 50
    start = time.time()
    feature = cv2.KAZE_create()

    # 특징점 검출 및 기술자 계산
    keypoint1, desc1 = feature.detectAndCompute(roi_img,None)
    keypoint2, desc2 = feature.detectAndCompute(base_img,None)
    #print('desc1.shape:',desc1.shape)
    #print('desc2.shape:',desc2.shape)

    # 매칭
    matcher = cv2.BFMatcher_create()
    matches = matcher.match(desc1, desc2)
    #좋은 매칭 결과 선별

    matches = sorted(matches, key=lambda x: x.distance)
    good_matches = matches[:50]
    
    dst = cv2.drawMatches(roi_img,keypoint1,base_img,keypoint2,matches,None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)

    # 호모 그래피 계산
    pts1 = np.array([keypoint1[m.queryIdx].pt for m in good_matches])
    pts1 = pts1.reshape(-1,1,2).astype(np.float32)

    pts2 = np.array([keypoint2[m.trainIdx].pt for m in good_matches])
    pts2 = pts2.reshape(-1,1,2).astype(np.float32)

    H,_ = cv2.findHomography(pts1,pts2,cv2.RANSAC)

    # 호모그래피를 이용하여 기준 영상 영역 표시
    (h,w) = roi_img.shape[:2]

    # 입력 영상의 모서리 4점 좌표
    corners1 = np.array([[0,0],[0,h-1],[w-1,h-1],[w-1,0]]).reshape(-1,1,2).astype(np.float32)

    # 입력 영상에 호모그래피 H 행렬로 투시 변환
    corners2 = np.int32(cv2.perspectiveTransform(corners1, H))

    # 다각형 그리기
    cv2.polylines(base_img, [corners2], True, (0, 255, 0), 5, cv2.LINE_AA)
    #base_img = cv2.fillPloy(base_img,[corners2],(0,255,0))
    end = time.time()
    #print(f'homography time :{round(end-start,2)}s')
    #print(f'corners2 : {corners2.shape}')
    return base_img, corners2

def tran_corner(corner):
    # a = 320-(math.tan(math.radians(28.5))/math.tan(math.radians(31.1)) * 320)
    # print(a)
    # b = 240-(math.tan(math.radians(21.5))/math.tan(math.radians(24.4)) * 240)
    # print(b)

    # img_re = img[10:-int(b+40),32*2:-32*2].copy()
    # print(img_re.shape)
    temp = np.zeros(corner.shape,dtype=np.int32)
    for i in range(len(corner)):
        y,x = corner[i][0]
        y = int(120/399*(y-64))
        if y < 0:
            y = 0
        elif y > 399:
            y = 120
        x = int(160/512*(x-10))
        if x < 0:
            x = 0
        elif x > 512:
            x=160
        
        temp[i][0] = y,x
    
    return temp

def masktoIR(ir_img,corner):
    
    temp = ir_img.copy()
    corner_my = tran_corner(corner)
    #print(corner,type(corner[0][0][0]))
    #print(corner_my,type(corner_my[0][0][0]))
    mask = np.zeros(temp.shape[:2],dtype=np.uint8)
    cv2.fillConvexPoly(mask,corner_my,color=255)

    temp = cv2.bitwise_and(temp,temp, mask = mask)

    return temp
    

if __name__ =='__main__':
    print(__name__)