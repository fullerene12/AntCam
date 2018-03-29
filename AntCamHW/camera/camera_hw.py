'''
Created on Aug 9, 2017

@author: Hao Wu
'''

from ScopeFoundry import HardwareComponent
from AntCamHW.camera.camera_dev import CameraDev

class CameraHW(HardwareComponent):
    '''
    Hardware Component Class for receiving AI input for breathing, licking etc
    '''
    
    name='camera'

    def setup(self,camera_id = 0):
        self.settings.New(name='camera_id',dtype=int,initial=camera_id,ro=True)
        self.settings.New(name ='model', dtype = str, initial ='N/A',ro = True)
        self.settings.New(name = 'width', dtype = int, initial = 1920, ro = True)
        self.settings.New(name = 'height', dtype = int, initial = 1200, ro = True)
        self.settings.New(name = 'auto_exposure', dtype = bool, initial = True, ro = False)
        self.settings.New(name = 'exposure_time', dtype = float, initial = 1000, ro = False)
        
        
                
    def connect(self):
        #connect to the camera device
        self._dev=CameraDev(self.settings.camera_id.value())
        
        #define read functions
        self.settings.model.hardware_read_func = self._dev.get_model
        self.settings.width.hardware_read_func = self._dev.get_width
        self.settings.height.hardware_read_func = self._dev.get_height
        self.settings.auto_exposure.hardware_read_func = self._dev.get_auto_exposure
        self.settings.exposure_time.hardware_read_func = self._dev.get_exp
        
        #define set functions
        self.settings.auto_exposure.hardware_set_func = self._dev.set_auto_exposure
        self.settings.exposure_time.hardware_set_func = self._dev.set_exp
        
        #read camera info
        self.read_from_hardware()
        
        
    
    def start(self):
        self._dev.start()
    
    def stop(self):
        self._dev.stop()
        
    def read(self):
        return self._dev.read()
    
    def read_disp(self):
        return self._dev.get_disp_buffer()
    
    def write(self):
        self._dev.write()
        
    def disconnect(self):
        '''
        need bug fix for pointer issues
        '''
        try:
            self.settings.model.hardware_read_func = None
            self.settings.width.hardware_read_func = None
            self.settings.height.hardware_read_func = None
            self.settings.auto_exposure.hardware_read_func = None
            self.settings.exposure_time.hardware_read_func = None
            
            #define set functions
            self.settings.auto_exposure.hardware_set_func = None
            self.settings.exposure_time.hardware_set_func = None
        
            
            self._dev.close()
            del self._dev
            
        except AttributeError:
            pass