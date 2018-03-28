'''
Created on Aug 9, 2017

@author: Hao Wu
'''

from ScopeFoundry import HardwareComponent
from VOTAScopeHW.camera.camera_dev import CameraDev

class CameraHW(HardwareComponent):
    '''
    Hardware Component Class for receiving AI input for breathing, licking etc
    '''
    
    name='camera'

    def setup(self,camera_id=0):
        self.settings.New(name='camera_id',dtype=int,initial=camera_id,ro=False)
        self.setting.New(name ='model', dtype = str, initial ='N/A',ro = True)
        self.setting.New(name ='serial_number', dtype = str, initial ='N/A',ro = True)
        self.settings.New(name='file_name',dtype=str,initial='D:\Hao\Data\Twitch.avi',ro=True)
                
    def connect(self):
        self._dev=CameraDev(self.settings.camera_id.value())
    
    def start(self):
        self._dev.start()
    
    def stop(self):
        self._dev.start()
        
    def read(self):
        return self._dev.read()
    
    def write(self):
        self._dev.write()
        
    def disconnect(self):
        try:
            self._dev.close()
            del self._dev
            
        except AttributeError:
            pass