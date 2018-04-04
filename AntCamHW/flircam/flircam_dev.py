'''
Created on Mar 26, 2018

@author: Hao Wu
'''

import numpy as np
import PySpin
'''
FLIRCamDev is the FoundryScope Driver for Point-Grey cameras. It is calling the 
FLIR Spinnaker Python binding PySpin. The newest version of PySpin can be
obtained from the FLIR official website
'''
class FLIRCamDev(object):
    
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

        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
            return None
        
    def start(self):
        '''
        Start the continuous acquisition mode
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
        '''
        Convert an image object to data
        There is a internal bug with the PySpin driver,
        The program have a chance to crash when the camera drops frame
        Use with caution
        
        2018/04/04 - I am contacting FLIR for this bug
        
        image: image object to get data from
        return: numpy array containing image data if collection is successful
        otherwise return an array of 1s
        '''
        status = image.GetImageStatus()
        if not status == 0:
            print('corrupted image %i' % status)
            return np.ones((self.height,self.width),dtype = np.uint8)
        buffer_size = image.GetBufferSize()
        if buffer_size == 0:
            print('corrupted image %i' % buffer_size)
            return np.ones((self.height,self.width),dtype = np.uint8)
        if image.IsIncomplete():
            print('incomplete iamge, returning ones')
            return np.ones((self.height,self.width),dtype = np.uint8)
        try:
            data = image.GetData()
            if type(data) == np.ndarray:
                new_data = np.copy(data)
                if new_data.size == (self.height * self.width):
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
            print("Error: %s, returning ones, exception" % ex)
            return np.ones((self.height,self.width),dtype = np.uint8)
    
    def save_image(self,image):
        '''
        Save current image to a JPEG file
        image: image object
        '''
        image.Save('buffer')
            
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
        
        exp_time: exposure time in microseconds
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
        get frame rate in fps
        '''
        try:
            return self.cam.AcquisitionFrameRate.GetValue()

        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
    
    def set_frame_rate(self,fr):
        '''
        set frame rate in fps
        
        fr: framerate in fps
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
        
        mode: boolean value of True(on) or False(off)
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
        
    def get_video_mode(self):
        '''
        get the video mode of the camera
        '''
        try:
            node_video_mode = PySpin.CEnumerationPtr(self.nodemap.GetNode("VideoMode"))
            return int(node_video_mode.GetCurrentEntry().GetSymbolic()[4])
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
            
    def set_video_mode(self,mode_number):
        '''
        set the video mode of the camera, depends on the model, certain mode
        might not exist 
        
        mode_number: integer number of the video mode
        '''
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
        '''
        method to get any stt from a camera
        
        nodemap: the node map of a collection of camera properties,
                e.g. TLDEVICE
        
        node_name: Name of the specific node, such as DeviceInformation
        
        feature_name: Name of the specific feature, such as ModelNumber
        '''
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
        '''
        method to get any stt from a camera
        
        nodemap: the node map of a collection of camera properties,
                e.g. TLDEVICE
        
        node_name: Name of the specific node, such as DeviceInformation
        
        feature_name: Name of the specific feature, such as ModelNumber
        '''
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