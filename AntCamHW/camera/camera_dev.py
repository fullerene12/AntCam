'''
Created on Mar 26, 2018

@author: Hao Wu
'''

import numpy as np
import cv2
import PySpin
import time

'''
Camera Dev is the FoundryScope Driver for Point-Grey cameras. It is calling the 
FLIR Spinnaker Python binding PySpin. The newest version of PySpin can be
obtained from the FLIR official website
'''
class CameraDev(object):
    
    def __init__(self,camera_id):
        '''
        camera id is 0,1,2,..., the maximum is the number of point-grey camera
        connected to the computer
        '''
        self.camera_id=camera_id
        self.open()


    def open(self):
        '''
        open up the connection to the camera
        '''
        try:
            #find the list of camera and choose the right camera
            self.system = PySpin.System.GetInstance()
            self.cam_list = self.system.GetCameras()
            
            #get the camera by id
            self.cam = self.cam_list.GetByIndex(self.camera_id)
            
            #read camera device information
            self.nodemap_tldevice = self.cam.GetTLDeviceNodeMap()
            
            #initialize camera
            self.cam.Init()
            
            #read camera control information
            self.nodemap = self.cam.GetNodeMap()
            
            #enable auto exposure
            self.set_auto_exposure(False)
            self.set_exp(500)
            
            
            #get height and width of the field of view
            self.height = self.get_height()
            self.width = self.get_width()
             
            #load first frame of image for the first image buffer
            self.start()
            self.update_buffer()
            self.stop()
            
            
#         
            
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
            return None
        
    def start(self):
        '''
        Start the continous acquisition mode
        '''
        try:
            #get handle for acquisition mode
            node_acquisition_mode = PySpin.CEnumerationPtr(self.nodemap.GetNode("AcquisitionMode"))
            if not PySpin.IsAvailable(node_acquisition_mode) or not PySpin.IsWritable(node_acquisition_mode):
                print("Unable to set acquisition mode to continuous (enum retrieval). Aborting...")
                return False
                 
            # Retrieve entry node from enumeration node
            node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName("Continuous")
            if not PySpin.IsAvailable(node_acquisition_mode_continuous) or not PySpin.IsReadable(node_acquisition_mode_continuous):
                print("Unable to set acquisition mode to continuous (entry retrieval). Aborting...")
                return False
                 
             
            # Retrieve integer value from entry node
            acquisition_mode_continuous = node_acquisition_mode_continuous.GetValue()
                 
            # Set integer value from entry node as new value of enumeration node
            node_acquisition_mode.SetIntValue(acquisition_mode_continuous)
            
            #Begin Acquisition
            self.cam.BeginAcquisition()
            
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
        
    def update_buffer(self):
        '''
        read to the image buffer
        '''
        try:
            self.buffer = self.cam.GetNextImage()
            self.buffer.Release()
            #return image_converted
            
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
            
    def get_buffer(self):
        '''
        read the numpy buffer
        '''
        try:
            return self.buffer.GetData().reshape((self.height,self.width))
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
        except ValueError as ex:
            print("Error: %s" % ex)
    
    def update_disp_buffer(self):
        try:
            self.disp_buffer = self.buffer.Convert(PySpin.PixelFormat_Mono8, PySpin.HQ_LINEAR)
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
            
    def get_disp_buffer(self):
        try:
            self.update_disp_buffer()
            return self.disp_buffer.GetData().reshape((self.height,self.width))
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
        except ValueError as ex:
            print("Error: %s" % ex)
            
    def read(self):
        self.update_buffer()
        return self.get_buffer()
    
    def save(self):
        pass
        
    def stop(self):
        '''
        stop the continuous acquisition mode
        '''
        try:
            self.cam.EndAcquisition()
        except PySpin.SpinnakerException as ex:
                print("Error: %s" % ex)
        
    def close(self):
        '''
        close the camera instance and delete itself
        '''
        try:
            #release the devices properly
            self.cam.DeInit()
            del self.buffer
            del self.cam
            self.cam_list.Clear()
            self.system.ReleaseInstance()
            del self.cam_list
            del self.system
            
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
            return None
        
    def get_model(self):
        """
        This function get the model name
        """
        try:
            node_device_information = PySpin.CCategoryPtr(self.nodemap_tldevice.GetNode("DeviceInformation"))
    
            if PySpin.IsAvailable(node_device_information) and PySpin.IsReadable(node_device_information):
                features = node_device_information.GetFeatures()
                for feature in features:
                    node_feature = PySpin.CValuePtr(feature)
                    if node_feature.GetName() == 'DeviceModelName':
                        return node_feature.ToString()
    
            else:
                return 'N/A'
            
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
            return 'N/A'
        
    def get_width(self):
        try:
            node_width = PySpin.CIntegerPtr(self.nodemap.GetNode("Width"))
            if PySpin.IsAvailable(node_width):
                return node_width.GetValue()
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
    
    def get_height(self):
        try:
            node_height = PySpin.CIntegerPtr(self.nodemap.GetNode("Height"))
            if PySpin.IsAvailable(node_height):
                return node_height.GetValue()
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
            
    def get_exp_min(self):
        '''
        get min exposure time in microseconds
        '''
        try:
            return self.cam.ExposureTime.GetMin()

        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
            
    def get_exp_max(self):
        '''
        get max exposure time in microseconds
        '''
        try:
            return self.cam.ExposureTime.GetMax()

        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
            
    def get_exp(self):
        '''
        get exposure time in microseconds
        '''
        try:
            return self.cam.ExposureTime.GetValue()

        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
    
    def set_exp(self,exp_time):
        '''
        set exposure time in microseconds
        '''
        try:
            if self.cam.ExposureTime.GetAccessMode() != PySpin.RW:
                print("Unable to set exposure time. Aborting...")
                return None
            
            exp_time = min(exp_time,self.get_exp_max())
            exp_time = max(exp_time,self.get_exp_min())
            self.cam.ExposureTime.SetValue(exp_time)
            
           
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
    
    def get_auto_exposure(self):
        '''
        get the status of auto exposure, either on or off
        '''
        try:
            val = self.cam.ExposureAuto.GetValue()
            
            if val == 2:
                return True
            elif val == 0:
                return False
            else:
                print('Unable to get auto exposure setting')

        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
    
    def set_auto_exposure(self, mode):
        '''
        set the status of auto exposure, either on or off
        '''
        try:
            if self.cam.ExposureAuto.GetAccessMode() != PySpin.RW:
                print("Unable to enable automatic exposure (node retrieval). Non-fatal error...")
                return None
            
            if mode:
                self.cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Continuous)
            else:
                self.cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
            
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
    
    def get_auto_framerate(self):
        try:
            val = self.cam.AcquisitionFrameRateAuto.GetValue()
            print(val)
            
            if val == 2:
                return True
            elif val == 0:
                return False
            else:
                print('Unable to get auto exposure setting')

        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
        
        
    
if __name__ == '__main__':
    print('begin test')
    camera = CameraDev(1)
    #camera.get_auto_framerate()
    camera2 = CameraDev(0)
    print(camera.get_model())
    print('connecting camera')
    print('starting camera')
    camera.start()
    camera2.start()
    print('read frame')
    tot_time = 0
    i = 0
    image = np.zeros((2048,2048),dtype=np.uint8)
    image2 = np.zeros((1200,1920),dtype=np.uint8)
    start_t = time.time()
    
    for j in range(100):
        camera.update_buffer()
        camera.update_disp_buffer()
    end_t = time.time()
    print(end_t-start_t)
    camera
    while(True):
    # Display the resulting frame
        i +=1
         
        
        image[:] = camera.read()
        image2[:] = camera2.read()
        cv2.imshow('frame',image)
        cv2.imshow('frame2',image2)
        
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
     
    # When everything done, release the capture
    cv2.destroyAllWindows()
       
    print('stop acquisition')
     
    camera2.stop()
    camera2.close()
    camera.stop()
    camera.close()