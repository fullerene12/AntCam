'''
Created on Aug 9, 2017

@author: Hao Wu
'''

from ScopeFoundry import HardwareComponent
from PyDAQmx import *
import numpy as np
import time

class DAQaiHW(object):
    '''
    Hardware Component Class for receiving AI input for breathing, licking etc
    '''
    
    name='daq_ai'

    def setup(self,channels='Dev2/ai14',rate=1000.0):
        '''
        add settings for analog input event
        '''
        self._channels=channels
        self._rate=rate
                
    def connect(self):
        self.setup()
        self._task=Task()
        self._data=np.zeros((1000,),dtype=float)
        read=int32()
        self._value=float64()
        channels=self._channels
        rate=self._rate
        self._task.CreateAIVoltageChan(channels,"",DAQmx_Val_Cfg_Default,-10.0,10.0,DAQmx_Val_Volts,None)
        #self._task.CfgSampClkTiming("",rate,DAQmx_Val_Rising,DAQmx_Val_FiniteSamps,1000)
        #self._task.StartTask()
        self._task.ReadAnalogScalarF64(10.0,byref(self._value),None)
        
    def disconnect(self):
        del self._task
        
        
        
if __name__ == '__main__':
    ai=DAQaiHW()
    ai.connect()
    print(ai._value.value)
    time.sleep(1)
    ai.disconnect()