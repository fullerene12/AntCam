'''
Created on Aug 9, 2017

@author: Hao Wu
'''

from ScopeFoundry import HardwareComponent
from AntCamHW.daq_timer.daq_timer_dev import DAQTimerDev
import time

class DAQTimerHW(HardwareComponent):
    '''
    Hardware Component Class for receiving AI input for breathing, licking etc
    '''
    
    name='daq_timer'

    def setup(self,channels='Dev2/ai0',num_of_chan=1,rate=10.0):
        '''
        add settings for analog input events
        '''
        self.settings.New(name='channels',initial=channels,dtype=str,ro=False)
        self.settings.New(name='num_of_chan',initial=num_of_chan,dtype=int,ro=False)
        self.settings.New(name='rate',initial=rate,dtype=float,ro=False)
                
    def connect(self):
        self._dev=DAQTimerDev(self.settings.channels.value(),
                          self.settings.num_of_chan.value(),
                          self.settings.rate.value())
        
        self.bind_ex_func = self._dev.bind_ex_func
        
    def start(self):
        self._dev.StartTask()
        
    def stop(self):
        self._dev.StopTask()
        
    def disconnect(self):
        try:
            self._dev.StopTask()
            self._dev.ClearTask()
            del self._dev
            del self.bind_ex_func
            
        except AttributeError:
            pass
        
if __name__ == '__main__':
    ai=DAQaiHW()
    ai.connect()
    print(ai._data)
    time.sleep(1)
    ai.disconnect()