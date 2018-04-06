'''
Created on Apr 5, 2018

@author: Hao Wu
'''
from .daq_do_dev import DAQCOTask,DAQSimpleDOTask
from .motor_helper_funcs import trans_cord
import numpy as np


class DAQMotorDev(object):
    '''
    This the device wrapper for stepper motor driver controlled by NIDAQ
    '''
    def __init__(self,chans,counter,term,freq,dc):
        '''
        This initialize the device
        
        ena_chan: name of the enable channel
        dir_chan: name of the direction channel
        counter: name of the counter
        term: name of the PFI terminal
        freq: frequency(Hz) of the pulse
        dc: duty cycle of the pulse, 0.0 - 1.0
        '''
        self.chans = chans
        self.counter = counter
        self.term = term
        self.freq = freq
        self.dc = dc
        
        self.do_task = DAQSimpleDOTask(self.chans)
        self.co_task1 = DAQCOTask(self.counter[0],self.term[0],self.freq,self.dc)
        self.co_task2 = DAQCOTask(self.counter[1],self.term[1],self.freq,self.dc)

    def move_manual(self,direction_id,num_pulses = [100,100]):
        '''
        Move in a selected direction for number of steps
        direction_id: 0 = left, 1 = right, 2 = up, 3 = down
        num_pulses: two integer number for 
        '''

        directions = []
        directions.append(np.array([0,0,0,0],dtype = np.uint8))
        directions.append(np.array([0,0,1,1],dtype = np.uint8))
        directions.append(np.array([0,0,1,0],dtype = np.uint8))
        directions.append(np.array([0,0,0,1],dtype = np.uint8))
        
        self.do_task.write(directions[direction_id])
        self.send_pulses(num_pulses)
        
    def send_pulses(self,num_pulses = [100,100]):
        self.co_task1.set_pulses(num_pulses[0])
        self.co_task2.set_pulses(num_pulses[1])
        if not num_pulses[0] == 0:
            self.co_task1.start()
        if not num_pulses[1] == 0:
            self.co_task2.start()
        while not self.done():
            pass
        if not num_pulses[0] == 0:
            self.co_task2.stop()
        if not num_pulses[1] == 0:
            self.co_task2.stop()
        
    def move(self,direction_signs,num_pulses):
        direction = np.zeros((4,),dtype = np.uint8)
        direction[2:4] = direction_signs
        print(direction)
        self.do_task.write(direction)
        self.send_pulses(num_pulses)
        
    def move_cartesian(self,num_pulses,angle = 45):
        old_cord = np.array(num_pulses)
        old_cord[1] *= -1
        direction, new_pulses = trans_cord(old_cord,angle)
        self.move(direction,new_pulses)

    def done(self):
        return (self.co_task1.done() and self.co_task2.done())
    
    def close(self):
        self.do_task.close()
        self.co_task1.close()
        self.co_task2.close()
        
if __name__ == '__main__':
    motor = DAQMotorDev(chans ='Dev2/port0/line5,Dev2/port1/line0,Dev2/port0/line1,Dev2/port1/line1',
                        counter = ['Dev2/ctr0','Dev2/ctr1'],
                        term =  ['/Dev2/PFI12','/Dev2/PFI13'],
                        freq = 4000,
                        dc = 0.5)
    motor.move_cartesian([0,800], 45)

    motor.close()
    
        
        