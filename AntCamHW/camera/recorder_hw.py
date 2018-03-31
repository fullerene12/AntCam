'''
Created on Aug 9, 2017

@author: Hao Wu
'''

from ScopeFoundry import HardwareComponent
from AntCamHW.camera.recorder_dev import RecorderDev
import os

class RecorderHW(HardwareComponent):
    '''
    Hardware Component Class for receiving AI input for breathing, licking etc
    '''
    
    name='recorder'

    def setup(self,camera_id = 0):
        initial_data_save_dir = os.path.abspath(os.path.join('.', 'data'))
        self.settings.New(name ='path', dtype = 'file', is_dir = True, initial = initial_data_save_dir)
        self.settings.New(name = 'compress', dtype = bool, initial = True)
        
    def connect(self):
        #connect to the camera device
        self._dev=RecorderDev(self.settings.path.value())
        
        #define read functions
        self.settings.path.hardware_read_func = self._dev.get_path
        
        #define set functions
        self.settings.path.hardware_set_func = self._dev.set_path
        
        
    
    def create_file(self,name,frame_rate):
        self._dev.create_file(name,frame_rate,self.settings.compress.value())
    
    def save_frame(self,name,image):
        self._dev.save_frame(name,image)
        
    def close_file(self,name):
        self._dev.close_file(name)
        
    def close(self):
        self._dev.close()
        
    def remove_event(self):
        self._dev.remove_event()
        
    def disconnect(self):
        '''
        need bug fix for pointer issues
        '''
        try:
            #remove read functions
            self.settings.path.hardware_read_func = None
            
            #remove set functions
            self.settings.path.hardware_set_func = self._dev.set_path
        
            self._dev.close()
            del self._dev
            
        except AttributeError:
            pass