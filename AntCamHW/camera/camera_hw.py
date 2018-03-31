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

    def setup(self,camera_sn = ''):
        self.settings.New(name='camera_sn',dtype=str,initial=camera_sn,ro=True)
        self.settings.New(name ='model', dtype = str, initial ='N/A',ro = True)
        self.settings.New(name = 'width', dtype = int, initial = 1920, ro = True)
        self.settings.New(name = 'height', dtype = int, initial = 1200, ro = True)
        self.settings.New(name = 'auto_exposure', dtype = bool, initial = True, ro = False)
        self.settings.New(name = 'exposure_time', dtype = float, initial = 1000, ro = False)
        self.settings.New(name = 'video_mode', dtype = int, initial = 0, ro = False, vmin = 0, vmax = 2)
        self.settings.New(name = 'frame_rate', dtype = float, initial = 30, ro = False, vmin = 0, vmax = 100)
        
        
                
    def connect(self):
        #connect to the camera device
        self._dev=CameraDev(self.settings.camera_sn.value())
        
        #define read functions
        self.settings.model.hardware_read_func = self._dev.get_model
        self.settings.width.hardware_read_func = self._dev.get_width
        self.settings.height.hardware_read_func = self._dev.get_height
        self.settings.auto_exposure.hardware_read_func = self._dev.get_auto_exposure
        self.settings.exposure_time.hardware_read_func = self._dev.get_exp
        self.settings.video_mode.hardware_read_func = self._dev.get_video_mode
        self.settings.frame_rate.hardware_read_func = self._dev.get_frame_rate
        
        #define set functions
        self.settings.auto_exposure.hardware_set_func = self._dev.set_auto_exposure
        self.settings.exposure_time.hardware_set_func = self._dev.set_exp
        self.settings.video_mode.hardware_set_func = self._dev.set_video_mode
        self.settings.frame_rate.hardware_set_func = self._dev.set_frame_rate
        
        #read camera info
        self.read_from_hardware()
        
        
    
    def start(self):
        self._dev.start()
    
    def stop(self):
        self._dev.stop()
        
    def read(self):
        return self._dev.read()
    
    def read_output_data(self):
        return self._dev.get_output_buffer_data()
    
    def write(self):
        self._dev.write()
        
    def config_event(self,run_func):
        self._dev.config_event(run_func)
        
    def remove_event(self):
        self._dev.remove_event()
        
    def disconnect(self):
        '''
        need bug fix for pointer issues
        '''
        try:
            # remove read functions
            self.settings.model.hardware_read_func = None
            self.settings.width.hardware_read_func = None
            self.settings.height.hardware_read_func = None
            self.settings.auto_exposure.hardware_read_func = None
            self.settings.exposure_time.hardware_read_func = None
            self.settings.video_mode.hardware_read_func = None
            self.settings.frame_rate.hardware_read_func = None
            #remove set functions
            self.settings.auto_exposure.hardware_set_func = None
            self.settings.exposure_time.hardware_set_func = None
            self.settings.video_mode.hardware_set_func = None
            self.settings.frame_rate.hardware_set_func = None
            
            self._dev.close()
            del self._dev
            
        except AttributeError:
            pass