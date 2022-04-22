# -*- coding: utf-8 -*-

from uvctypes import *
import datetime
import pandas as pd
import sys
import os
from bh1750 import readLight
from buffercleaner import *
try:
  from queue import Queue
except ImportError:
  from Queue import Queue
import platform
from find_homo import *

BUF_SIZE = 2
q = Queue(BUF_SIZE)

def py_frame_callback(frame, userptr):

  array_pointer = cast(frame.contents.data, POINTER(c_uint16 * (frame.contents.width * frame.contents.height)))
  data = np.frombuffer(
    array_pointer.contents, dtype=np.dtype(np.uint16)
  ).reshape(
    frame.contents.height, frame.contents.width
  )
  if frame.contents.data_bytes != (2 * frame.contents.width * frame.contents.height):
    return

  if not q.full():
    q.put(data)

PTR_PY_FRAME_CALLBACK = CFUNCTYPE(None, POINTER(uvc_frame), c_void_p)(py_frame_callback)

def raw_to_8bit(data):
  cv2.normalize(data, data, 0, 65535, cv2.NORM_MINMAX)
  np.right_shift(data, 8, data)
  return cv2.cvtColor(np.uint8(data), cv2.COLOR_GRAY2RGB)

def ktoc(val):
  val = np.where(val>0, (val-27315)/100.0, 0)

  return val

def main():
  if len(sys.argv) < 2 or len(sys.argv) > 3:
    print("Usage : lepton (experiment number) [,(try number)]")
    exit(1)
  dirname = "/home/pi/Socket/images/" + sys.argv[1]
  if os.path.isdir(dirname) == False:
      os.mkdir(dirname)
  else:
    print(f"{dirname} is exist.")
  
  
  cap = cv2.VideoCapture(2)
  if not cap.isOpened():
    print("Camera not found!")
    exit(1)
  else:
    print("Camera is Opened")
  
  ctx = POINTER(uvc_context)()
  dev = POINTER(uvc_device)()
  devh = POINTER(uvc_device_handle)()
  ctrl = uvc_stream_ctrl()

  res = libuvc.uvc_init(byref(ctx), 0)
  if res < 0:
    print("uvc_init error")
    exit(1)

  try:
    res = libuvc.uvc_find_device(ctx, byref(dev), PT_USB_VID, PT_USB_PID, 0)
    if res < 0:
      print("uvc_find_device error")
      exit(1)

    try:
      res = libuvc.uvc_open(dev, byref(devh))
      if res < 0:
        print("uvc_open error")
        exit(1)

      print("device opened!")

      print_device_info(devh)
      print_device_formats(devh)

      frame_formats = uvc_get_frame_formats_by_guid(devh, VS_FMT_GUID_Y16)
      if len(frame_formats) == 0:
        print("device does not support Y16")
        exit(1)

      libuvc.uvc_get_stream_ctrl_format_size(devh, byref(ctrl), UVC_FRAME_FORMAT_Y16,
        frame_formats[0].wWidth, frame_formats[0].wHeight, int(1e7 / frame_formats[0].dwDefaultFrameInterval)
      )

      res = libuvc.uvc_start_streaming(devh, byref(ctrl), PTR_PY_FRAME_CALLBACK, None, 0)
      if res < 0:
        print("uvc_start_streaming failed: {0}".format(res))
        exit(1)
      
      if cap is not None:
        cap_cleaner = CameraBufferCleanerThread(cap)
        time.sleep(1)
        cv2.namedWindow("Temperature",cv2.WINDOW_NORMAL | cv2.WINDOW_AUTOSIZE)
        #cv2.resizeWindow("Temperature", width=480, height=360)

        find_img = cap_cleaner.last_frame
        find_img = cv2.flip(find_img,-1)
        _, coordinates = initcapture(find_img,1)
        
        y1,y2,x1,x2 = coordinates[0]
        find_img = find_img[y1:y2,x1:x2].copy()
        find_img_name = dirname + '/' + sys.argv[1]
        cv2.imwrite(f"{find_img_name}_base.jpg",find_img)
        print(f"File {find_img_name}_base.jpg is Saved")
      try:
        while True:
          start = time.time()

          data = q.get(True, 500)

          if cap is not None:
            img2 = cap_cleaner.last_frame
            img2 = cv2.flip(img2,-1)
            ret = True
          if data is None:
            break

          if ret:
            homo_img, rectangle = homography(find_img,img2)
            #print(f'rectangle : {rectangle}')
            cv2.imshow("Temperature", homo_img)

          data = cv2.flip(data,-1)
          data_temp = data.copy()
          data_crop = data.copy()
          data_crop = masktoIR(data_crop,rectangle)
          
          img = raw_to_8bit(data)
          img = cv2.applyColorMap(img, cv2.COLORMAP_INFERNO)
          img_mask = masktoIR(img,rectangle)
          cv2.imshow("Lepton Radiometry", img_mask)

          k = cv2.waitKey(50) # 10fps
          if k == 27:
            break
          elif k == ord('l'):
            print(f'Light : {Light}')
          elif k == 13: # enter저장
            now = datetime.datetime.now()
            fname = dirname + now.strftime("/%m%d_%H%M%S")
          
            cv2.imwrite(f"{fname}.jpg",img)
            print(f"File {fname}.jpg is Saved")
            
            data_temp = ktoc(data_temp)
            df = pd.DataFrame(data_temp)
            #df = df.loc[::-1].loc[:,::-1]
            df.to_csv(f"{fname}.csv",index=False, header=None)
            
            data_crop = ktoc(data_crop)
            df1 = pd.DataFrame(data_crop)
            #df1 = df1.loc[::-1].loc[:,::-1]
            df1.to_csv(f"{fname}_crop.csv",index=False, header=None)
            
            if ret:
              cv2.imwrite(f"{fname}_.jpg",homo_img)
            
            Light = readLight()
            print(f'Light : {round(Light,2)}')
        cv2.destroyAllWindows()
        end= time.time()
        #print(f'1 cycle time : {round(end-start,2)}s')
      finally:
        libuvc.uvc_stop_streaming(devh)
      print("done")
    finally:
      libuvc.uvc_unref_device(dev)
  finally:
    libuvc.uvc_exit(ctx)
    cap_cleaner.raise_exception()
    cap_cleaner.join()
    cap.release()

if __name__ == '__main__':
  main()
