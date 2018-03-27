'''
Created on Aug 9, 2017

@author: Hao Wu
'''

from ScopeFoundry import HardwareComponent
from .daq_ai_dev import DAQaiDev
from PyDAQmx import *
import numpy as np
import time

class DAQaiHW(HardwareComponent):
    '''
    Hardware Component Class for receiving AI input for breathing, licking etc
    '''
    
    name='daq_ai'

    def setup(self,channels='Dev2/ai0:3',num_of_chan=4,rate=1000.0,buffer_size=1,queue_size=1000):
        '''
        add settings for analog input eventsss
        '''
        self.settings.New(name='channels',initial=channels,dtype=str,ro=False)
        self.settings.New(name='num_of_chan',initial=num_of_chan,dtype=int,ro=False)
        self.settings.New(name='rate',initial=rate,dtype=float,ro=False)
        self.settings.New(name='data', initial=0, dtype=float, ro=True)
        self.settings.New(name='buffer_size', initial=buffer_size, dtype=int, ro=True)
        self.settings.New(name='queue_size', initial=queue_size, dtype=int, ro=False)

        
                
    def connect(self):
        self._dev=DAQaiDev(self.settings.channels.value(),
                          self.settings.num_of_chan.value(),
                          self.settings.rate.value(),
                          self.settings.buffer_size.value(),
                          self.settings.queue_size.value())
        
        self.read_data=self._dev.read_data
        self.get_size=self._dev.get_size
        
    def start(self):
        self._dev.StartTask()
        
    def stop(self):
        self._dev.StopTask()
        
    def disconnect(self):
        try:
            self._dev.StopTask()
            self._dev.ClearTask()
            del self._dev
            del self.read_data
            del self.get_size
            
        except AttributeError:
            pass
        
if __name__ == '__main__':
    ai=DAQaiHW()
    ai.connect()
    print(ai._data)
    time.sleep(1)
    ai.disconnect()