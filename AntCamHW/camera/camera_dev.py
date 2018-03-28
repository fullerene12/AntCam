'''
Created on Mar 26, 2018

@author: Hao Wu
'''

import numpy as np
import cv2
import PySpin

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
            return None
        
    def read(self):
        try:
            image_result = self.cam.GetNextImage()
            
            image_converted = image_result.Convert(PySpin.PixelFormat_Mono8, PySpin.HQ_LINEAR)
            image_data = image_converted.GetData()[:]
            w = image_converted.GetWidth()
            h = image_converted.GetHeight()
            image_data = image_data.reshape((h,w))
            image_result.Release()
            
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
            return None
        return image_data
    
    def stop(self):
        '''
        stop the continuous acquisition mode
        '''
        try:
            self.cam.EndAcquisition()
        except PySpin.SpinnakerException as ex:
                print("Error: %s" % ex)
                return None
        
    def close(self):
        '''
        close the camera instance and delete itself
        '''
        try:
            #release the devices properly
            self.cam.DeInit()
            del self.cam
            self.cam_list.Clear()
            self.system.ReleaseInstance()
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
    
if __name__ == '__main__':
    print('begin test')
    camera = CameraDev(1)
    camera2 = CameraDev(0)
    print(camera.get_model())
    print('connecting camera')
    print('starting camera')
    camera.start()
    camera2.start()
    print('read frame')
    while(True):
    # Display the resulting frame
        image = camera.read()
        image2 = camera2.read()
        cv2.imshow('frame',image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
 
# When everything done, release the capture
    cv2.destroyAllWindows()
    
    print('stop acquisition')
    
    camera.stop()
    camera.close()
    camera2.stop()
    camera2.close()