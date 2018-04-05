from numpy import zeros,reshape
from PyDAQmx import *
from queue import Queue
import time
from ctypes import byref

"""This example is a PyDAQmx version of the ContAcq_IntClk.c example
It illustrates the use of callback functions

This example demonstrates how to acquire a continuous amount of
data using the DAQ device's internal clock. It incrementally stores the data
in a Python list.
"""

class DAQaiDev(Task):
    
    def __init__(self,channels='Dev2/ai13:14',num_of_chan=2,rate=10.0,buffer_size=10,queue_size=10000):
        Task.__init__(self)
        self.buffer_size=buffer_size
        self.num_of_chan=num_of_chan
        self.data = zeros(self.buffer_size*self.num_of_chan)
        self.buffer = Queue()
        self.CreateAIVoltageChan(channels,"",DAQmx_Val_RSE,-10.0,10.0,DAQmx_Val_Volts,None)
        self.CfgSampClkTiming("",rate,DAQmx_Val_Rising,DAQmx_Val_ContSamps,self.
                              buffer_size)
        self.AutoRegisterEveryNSamplesEvent(DAQmx_Val_Acquired_Into_Buffer,self.buffer_size,0)
        self.AutoRegisterDoneEvent(0)
        
    def EveryNCallback(self):
        read = int32()
        self.ReadAnalogF64(self.buffer_size,10.0,DAQmx_Val_GroupByScanNumber,self.data,self.buffer_size*self.num_of_chan,byref(read),None)
        self.buffer.put(reshape(self.data,(self.buffer_size,self.num_of_chan)))
        #print(self.data)
        return 0 # The function should return an integer
    
    def DoneCallback(self, status):
        print("Status",status.value)
        return 0 # The function should return an integer
    
    def read_data(self):
        return self.buffer.get(True,1.0)
        
    def read_current_data(self):
        return self.data
    
    def get_size(self):
        return self.buffer.qsize()
    #def ReadData

if __name__ == '__main__':
    task=DAQaiDev()
    task.StartTask()
    input('Acquiring samples continuously. Press Enter to interrupt\n')
    
    task.StopTask()
    task.ClearTask()