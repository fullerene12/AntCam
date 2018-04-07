from PyDAQmx import *
from ctypes import byref, c_ulong,c_int32
import numpy as np

class DAQSimpleDOTask(Task):
    '''
    a simple task that set one digital output line to high or low
    '''
    
    def __init__(self,chan= 'Dev2/port0/line5'):
        '''
        chan: name of the chanel, in the format of Dev2/port0/line0
        '''
        Task.__init__(self)
        self.chan = chan
        self.CreateDOChan(self.chan,'',DAQmx_Val_ChanPerLine)
        
    def write(self,value,timeout = 0.0001):
        '''
        write a single sample to the digital line
        
        value: 1-D array with the size of the number of channels take np.uint8 array
        timeout: timeout in seconds
        '''
        written = c_int32(0)
        self.WriteDigitalLines(1,True,timeout,DAQmx_Val_GroupByScanNumber,value,byref(written),None)
        
    def high(self,timeout = 0.0001):
        '''
        change the digital line to high
        
        timeout: timeout in seconds
        '''
        self.write(np.array([1],dtype = np.uint8),timeout)
        
    def low(self,timeout =0.0001):
        '''
        change the digital line to low
        
        timeout: timeout in seconds
        '''
        self.write(np.array([0],dtype = np.uint8),timeout)
        
    def close(self):
        '''
        close task
        '''
        self.ClearTask()
        
class DAQContDOTask(Task):
    '''
    a task that set one digital output to high/low for a selected period of time
    '''
    
    def __init__(self,chan= 'Dev2/port0/line5', rate = 1000):
        '''
        chan: name of the chanel, in the format of Dev2/port0/line0
        rate: sampling rate in Hz
        '''
        Task.__init__(self)
        self.chan = chan
        self.rate = rate
        
        self.CreateDOChan(self.chan,'',DAQmx_Val_ChanPerLine)
        self.CfgSampClkTiming('',self.rate,DAQmx_Val_Rising,DAQmx_Val_ContSamps,1000)

        
    def write(self,value):
        '''
        write a single sample to the digital line
        '''
        val_array = np.zeros((10,),dtype = np.uint8)
        val_array[:] = value

        self.WriteDigitalLines(1,False,0,DAQmx_Val_GroupByScanNumber,val_array,byref(written),None)
        
    def high(self):
        '''
        change the digital line to high
        '''
        self.write(1)
        
    def start(self):
        '''
        start task
        '''
        self.StartTask()
        
    def done(self):
        '''
        returns if a started task is done outputting
        if done, returns True
        '''
        value = c_ulong(False)
        self.IsTaskDone(byref(value))
        return bool(value)
        
    def stop(self):
        '''
        stop task
        '''
        self.StopTask()
        
    def low(self):
        '''
        change the digital line to low
        '''
        self.write(0)
        
    def close(self):
        '''
        close task
        '''
        self.ClearTask()
        
class DAQCOTask(Task):
    '''
    This is a task where you can generate precisely time pulses with a certain frequency
    '''
    
    def __init__(self,counter = 'Dev2/ctr0',term = '/Dev2/PFI12',freq = 4000,dc = 0.5):
        '''
        Initialize the task
        
        counter: name of the counter used, e.g. Dev2/ctr0
        term: name of terminal used, e.g. /Dev2/PFI10, note that the first slash has to be there
        freq: frequency in Hz
        dc: pulse duty cycle of the high period, from 0.0 - 1.0
        '''
        Task.__init__(self)
        self.counter = counter
        self.term = term
        
        self.CreateCOPulseChanFreq(self.counter,'',DAQmx_Val_Hz,DAQmx_Val_Low,0,freq,dc)
        self.SetCOPulseTerm(self.counter, self.term)
        
    def set_pulses(self,num_pulses = 800):
        '''
        Set the number of pulses to be generated for the next sample
        
        num_pulses: number of pulses to output
        '''
        self.CfgImplicitTiming(DAQmx_Val_FiniteSamps,num_pulses)
        
    def start(self):
        '''
        start task
        '''
        self.StartTask()
        
    def done(self):
        '''
        returns if a started task is done outputting
        if done, returns True
        '''
        value = c_ulong(False)
        self.IsTaskDone(byref(value))
        return bool(value)
        
    def stop(self):
        '''
        stop task
        '''
        self.StopTask()

    def close(self):
        '''
        close task
        '''
        self.ClearTask()