# -*- coding: utf-8 -*-

from labquest_ocr import *
from buffercleaner import *
import alarm

from uvctypes import *
import datetime
import pandas as pd
import numpy as np
import time

try:
  from queue import Queue
except ImportError:
  from Queue import Queue

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

def ktoc(val):
  return (val - 27315) / 100.0

def raw_to_8bit(data):
  cv2.normalize(data, data, 0, 65535, cv2.NORM_MINMAX)
  np.right_shift(data, 8, data)
  return cv2.cvtColor(np.uint8(data), cv2.COLOR_GRAY2RGB)

def main():
  if len(sys.argv) < 3 or len(sys.argv) > 4:
    print("Usage : lepton (experiment number) [,(try number),(distance)]")
    exit(1)
  dirname = "/home/pi/JThermal/images/" + sys.argv[1]
  
  if sys.argv[1] == '3' or sys.argv[1] == '4':
    if len(sys.argv) < 4:
      print("Expirement 3,4 must need try number and distance")
      exit(1)
    dirname += "/" + sys.argv[2]
    if os.path.isdir(dirname) == False:
      os.mkdir(dirname)
    else:
      print(f"{dirname} is exist.")
    dirname += "/" + sys.argv[3]
    if os.path.isdir(dirname) == False:
      os.mkdir(dirname)
    else:
      print(f"{dirname} is exist.")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
      print("Camera not found!")
      exit(1)
    else:
      alarm_list = [30.1,35.1,40.1,45.1,50.2]
      print("Camera is Opened")
  else:
    cap = None
    ret = False
  
  ctx = POINTER(uvc_context)()
  dev = POINTER(uvc_device)()
  devh = POINTER(uvc_device_handle)()
  ctrl = uvc_stream_ctrl()
  # 10~20 temp, 4m 20s
  delay = 230
  my_time = 0

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
        # Start the cleaning thread
        cap_cleaner = CameraBufferCleanerThread(cap)
        time.sleep(1)
        cv2.namedWindow("Temperature",cv2.WINDOW_NORMAL)
        #cv2.resizeWindow("Temperature", width=480, height=360)
        img_labquest = cap_cleaner.last_frame

      try:
        while True:
          start = time.time()
          ret = True
          # Labquest read
          if cap is not None:
            img_labquest = cap_cleaner.last_frame

          # Lepton read
          data = q.get(True, 500)
          if data is None:
            break
          data_temp = data.copy()
          img = raw_to_8bit(data)
          img = cv2.applyColorMap(img, cv2.COLORMAP_HOT)
          img = cv2.flip(img,-1)

          cv2.imshow("Lepton Radiometry", img)
          if img_labquest is not None:
            cv2.imshow("Temperature", img_labquest)
          k = cv2.waitKey(27)
          if k == 27: # ESC - terminate
            print("Terminate")
            break
          elif delay < my_time: # Save
            now = datetime.datetime.now()
            fname = dirname + now.strftime("/%m%d_%H%M%S")
            cv2.imwrite(f"{fname}.jpg",img)
            print(f"File {fname}.jpg is Saved")
            data_temp = ktoc(data_temp)
            df = pd.DataFrame(data_temp)
            df = df.loc[::-1].loc[:,::-1]
            df.to_csv(f"{fname}.csv",index=False, header=None)
            if img_labquest is not None:
              cv2.imwrite(f"{fname}_.jpg",img_labquest)
            delay += 30
            my_time = 0
            print('delay:',delay)
          else:
            pass
          #time.sleep(5)
          end = time.time()
          my_time +=(end-start)
          #print('all time:',end-start, 'my_time :',my_time)
          if delay > 930:
            break
        cv2.destroyAllWindows()
      finally:
        libuvc.uvc_stop_streaming(devh)
    finally:
      libuvc.uvc_unref_device(dev)
  finally:
    libuvc.uvc_exit(ctx)
    cap_cleaner.raise_exception()
    cap_cleaner.join()
    cap.release()

if __name__ == '__main__':
  main()
