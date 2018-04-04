'''
Created on Mar 26, 2018

@author: Hao Wu
'''

import numpy as np
import cv2
import PySpin
import time
from queue import Queue
from .cam_helper_classes import ImageEventHandler
'''
Camera Dev is the FoundryScope Driver for Point-Grey cameras. It is calling the 
FLIR Spinnaker Python binding PySpin. The newest version of PySpin can be
obtained from the FLIR official website
'''
class CameraDev(object):
    data_qsize = 1000
    recording = False
    
    def __init__(self,camera_sn):
        '''
        camera id is 0,1,2,..., the maximum is the number of point-grey camera
        connected to the computer
        '''
        self.camera_sn=camera_sn
        self.open()
        
        
    '''
    Camera operations
    '''
    def open(self):
        '''
        open up the connection to the camera
        '''
        try:
            #find the list of camera and choose the right camera
            self.system = PySpin.System.GetInstance()
            self.cam_list = self.system.GetCameras()
            
            #get the camera by id
            self.cam = self.cam_list.GetBySerial(self.camera_sn)
            
            #read camera device information
            self.nodemap_tldevice = self.cam.GetTLDeviceNodeMap()
            self.nodemap_tlstream = self.cam.GetTLStreamNodeMap()
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
            
            #setup buffer queue
            self.data_q = Queue(self.data_qsize)
            self.record_q = Queue(self.data_qsize)
                   
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
            
    def config_event(self):
        try:
            self.event = ImageEventHandler(self)
            self.cam.RegisterEvent(self.event)
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
        
    def remove_event(self):
        try:
            self.cam.UnregisterEvent(self.event)
            del self.event
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
            
    def stop(self):
        '''
        stop the continuous acquisition mode
        '''
        try:
            self.cam.EndAcquisition()
            self.data_q = Queue(self.data_qsize)
        except PySpin.SpinnakerException as ex:
                print("Error: %s" % ex)
        
    def close(self):
        '''
        close the camera instance and delete itself
        '''
        try:
            #release the devices properly
            self.cam.DeInit()
            del self.data_q
            del self.record_q
            num_cam = self.cam_list.GetSize()
            num_init = 0
            for i in range(num_cam):
                if self.cam_list.GetByIndex(i).IsInitialized():
                    num_init += 1
            
            if num_init > 0 :
                print('Camera system still in use, removing camera %s' % self.camera_sn)
                del self.cam
            else:
                print('Camera system not in use, removing camera %s and shutting down system' % self.camera_sn)
                del self.cam
                self.cam_list.Clear()
                self.system.ReleaseInstance()
                del self.cam_list
                del self.system
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)

    '''
    Data operations
    '''
    def to_numpy(self,image):
        status = image.GetImageStatus()
        if not status == 0:
            print('corrupted image %i' % status)
            return np.ones((self.height,self.width),dtype = np.uint8)
        buffer_size = image.GetBufferSize()
        if buffer_size == 0:
            print('corrupted image %i' % buffer_size)
            return np.ones((self.height,self.width),dtype = np.uint8)
        try:
            data = self.get_data(image)
            if type(data) == np.ndarray:
                new_data = np.copy(data)
                if new_data.size == self.height * self.width:
                    output_data = new_data.reshape((self.height,self.width))
                    return output_data
                else:
                    print(status)
                    print('Error: Data size %i is not the right size, returning ones' % new_data.size)
                    return np.ones((self.height,self.width),dtype = np.uint8)
            else:
                print(status)
                print('Error: data is %s, returning ones' % type(data))
                return np.ones((self.height,self.width),dtype = np.uint8)
        except PySpin.SpinnakerException as ex:
            print("Error: %s, returning ones" % ex)
            return np.ones((self.height,self.width),dtype = np.uint8)
        except Exception as ex:
            print("Error: %s, returning ones" % ex)
            return np.ones((self.height,self.width),dtype = np.uint8)
        
    
    def get_data(self,image):
        status = image.GetImageStatus()
        if not status == 0:
            print('corrupted image %i' % status)
            return np.ones((self.height,self.width),dtype = np.uint8)
        try:
            data = image.GetData()
            if type(data) == np.ndarray:
                return np.copy(data)
            else:
                return np.ones((self.height,self.width),dtype = np.uint8)
        except Exception as ex:
            print('Error: %s' % ex)
            return np.ones((self.height,self.width),dtype = np.uint8)
    
    def save_image(self,image):
        image.Save('buffer')
            
    def empty(self):
        return self.data_q.empty()
            
    def read(self):
        return self.data_q.get()
    
    def write(self,data):
        self.data_q.put(data)
        
    def record_empty(self):
        return self.record_q.empty()
    
    def read_record_frame(self):
        return self.record_q.get()
    
    def write_record_frame(self,image):
        try:
            self.record_q.put(PySpin.Image.Create(image))
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
            
    '''
    Setting Functions
    '''
        
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
            
    def get_frame_rate(self):
        '''
        get frame rate in Hz
        '''
        try:
            return self.cam.AcquisitionFrameRate.GetValue()

        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
    
    def set_frame_rate(self,fr):
        '''
        set frame rate in Hz
        '''
        try:
            return self.cam.AcquisitionFrameRate.SetValue(fr)

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
        
    def get_video_mode(self):
        try:
            node_video_mode = PySpin.CEnumerationPtr(self.nodemap.GetNode("VideoMode"))
            return int(node_video_mode.GetCurrentEntry().GetSymbolic()[4])
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
            
    def set_video_mode(self,mode_number):
        try:
            node_video_mode = PySpin.CEnumerationPtr(self.nodemap.GetNode("VideoMode"))
            Mode0 = node_video_mode.GetEntryByName("Mode0")
            Mode1 = node_video_mode.GetEntryByName("Mode1")
            Mode2 = node_video_mode.GetEntryByName("Mode2")
            mode_list = [Mode0,Mode1,Mode2]
            
            node_video_mode.SetIntValue(mode_list[mode_number].GetValue())
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
    
    '''
    Streaming information
    '''
    def get_feature(self,nodemap,node_name,feature_name):
        try:
            node = PySpin.CCategoryPtr(nodemap.GetNode(node_name))
            if PySpin.IsAvailable(node) and PySpin.IsReadable(node):
                features = node.GetFeatures()
                for feature in features:
                    node_feature = PySpin.CValuePtr(feature)
                    if node_feature.GetName() == feature_name:
                        return node_feature.ToString()
            else:
                print('No feature named %s found' % feature_name)
                return None
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)         

    def set_feature(self,nodemap,node_name,feature_name,value):
        try:
            node = PySpin.CCategoryPtr(nodemap.GetNode(node_name))
            if PySpin.IsAvailable(node) and PySpin.IsReadable(node):
                features = node.GetFeatures()
                for feature in features:
                    node_feature = PySpin.CValuePtr(feature)
                    if node_feature.GetName() == feature_name:
                            node_feature.FromString(value)
                            
            else:
                print('No feature named %s found' % feature_name)
                return None
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)            
            
    def get_buffer_count(self):
        """
        This function get the buffer count of the stream
        """
        return int(self.get_feature(self.nodemap_tlstream,
                                    'BufferHandlingControl',
                                    'StreamDefaultBufferCount'))
    
    def set_buffer_count(self,value):
        """
        This function set the buffer count of the stream
        """
        return self.set_feature(self.nodemap_tlstream,
                                'BufferHandlingControl',
                                'StreamDefaultBufferCount',
                                str(value))
    
    def get_crc(self):
        return int(self.get_feature(self.nodemap_tlstream,
                                    'BufferHandlingControl',
                                    'StreamCRCCheckEnable'))
        
    def set_crc(self,value):
        """
        This function set the buffer count of the stream
        """
        return self.set_feature(self.nodemap_tlstream,
                                'BufferHandlingControl',
                                'StreamCRCCheckEnable',
                                str(value))
    
            
if __name__ == '__main__':
    print('begin test')
    camera = CameraDev('16130612')
    print(camera.get_buffer_count())
    camera.set_buffer_count(20)
    print(camera.get_buffer_count())
    print(camera.get_crc())
    camera.set_crc(1)
    print(camera.get_crc())
    
#     print(camera.get_video_mode())
#     camera.set_video_mode(1)
#     print(camera.get_video_mode())
#     print(camera.get_frame_rate())
    

#     camera.config_event(camera.repeat)
#     camera.start()
    
#     #camera.get_auto_framerate()
#     camera2 = CameraDev(0)
#     print(camera.get_model())
#     print('connecting camera')
#     print('starting camera')
#     camera.start()
#     camera2.start()
#     print('read frame')
#     tot_time = 0
#     i = 0
#     image = np.zeros((2048,2048),dtype=np.uint8)
#     image2 = np.zeros((1200,1920),dtype=np.uint8)
#     start_t = time.time()
#     
#     for j in range(100):
#         camera.update_buffer()
#         camera.update_output_buffer()
#     end_t = time.time()
#     print(end_t-start_t)
#     camera
#     while(True):
#     # Display the resulting frame
#         time.sleep(0.2)
#         print('running')
#          
#          
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break
#      
#     # When everything done, release the capture
#     cv2.destroyAllWindows()
#        
#     print('stop acquisition')
#      
#     camera2.stop()
#     camera2.close()
#     camera.remove_event()
#     camera.stop()
    camera.close()