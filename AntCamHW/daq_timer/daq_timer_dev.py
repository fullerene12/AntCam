from numpy import zeros,reshape
from PyDAQmx import *
from queue import Queue
import time
from ctypes import byref
import numpy as np

"""This example is a PyDAQmx version of the ContAcq_IntClk.c example
It illustrates the use of callback functions

This example demonstrates how to acquire a continuous amount of
data using the DAQ device's internal clock. It incrementally stores the data
in a Python list.
"""

class DAQTimerDev(Task):
    
    def __init__(self,channels='Dev2/ai13:14',num_of_chan=2,rate=10.0):
        Task.__init__(self)
        self.num_of_chan=num_of_chan
        self.CreateAIVoltageChan(channels,"",DAQmx_Val_RSE,-10.0,10.0,DAQmx_Val_Volts,None)
        self.CfgSampClkTiming("",rate,DAQmx_Val_Rising,DAQmx_Val_ContSamps,1)
        self.AutoRegisterEveryNSamplesEvent(DAQmx_Val_Acquired_Into_Buffer,1,0)
        self.AutoRegisterDoneEvent(0)
        self.data = np.zeros((1,))
        
    def bind_ex_func(self, func):
        self.ex_func = func
        
    def EveryNCallback(self):
        self.ex_func()
        read = int32()
        self.ReadAnalogF64(1,10.0,DAQmx_Val_GroupByScanNumber,self.data,1*self.num_of_chan,byref(read),None)
        
        #print(self.data)
        return 0 # The function should return an integer
    
    def DoneCallback(self, status):
        print("Status",status.value)
        return 0 # The function should return an integer
    #def ReadData

if __name__ == '__main__':
    task=DAQaiDev()
    task.StartTask()
    input('Acquiring samples continuously. Press Enter to interrupt\n')
    
    task.StopTask()
    task.ClearTask()