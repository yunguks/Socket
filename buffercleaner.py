import ctypes
import threading

# Define the thread that will continuously pull frames from the camera
class CameraBufferCleanerThread(threading.Thread):
    def __init__(self, camera, name='camera-buffer-cleaner-thread'):
        self.camera = camera
        self.last_frame = None
        super(CameraBufferCleanerThread, self).__init__(name=name)
        self.start()

    def run(self):
        try:
            while True:
                ret, self.last_frame = self.camera.read()
        finally:
            print("CameraBufferCleanerThread Ended")

    def get_id(self):
        # returns id of the respective thread 
        if hasattr(self, '_thread_id'): 
            return self._thread_id 
        for id, thread in threading._active.items(): 
            if thread is self: 
                return id

    def raise_exception(self): 
        thread_id = self.get_id() 
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 
              ctypes.py_object(SystemExit)) 
        if res > 1: 
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0) 
            print('Exception raise failure') 

if __name__ == "__main__":
    import cv2
    # Start the camera
    camera = cv2.VideoCapture(0)

    # Start the cleaning thread
    cam_cleaner = CameraBufferCleanerThread(camera)

    # Use the frame whenever you want
    while True:
        if cam_cleaner.last_frame is not None:
            cv2.imshow('The last frame', cam_cleaner.last_frame)
            print("Capture")
        if cv2.waitKey(100) == 27:
            cam_cleaner.raise_exception() 
            break
    cam_cleaner.join()
    camera.release()