'''
Created on Aug 9, 2017

@author: Hao Wu
'''

from ScopeFoundry import HardwareComponent
from .daqmotor_dev import DAQMotorDev
import numpy as np
from .motor_helper_funcs import rotate_cord
import h5py,os

class DAQMotorHW(HardwareComponent):
    '''
    Hardware Component Class for controlling two stepper motor tracker
    '''
    
    name='daqmotor'

    def setup(self):
        self.settings.New(name ='x', dtype = float, initial = 0, ro = True)
        self.settings.New(name ='y', dtype = float, initial = 0, ro = True)
        
        self.settings.New(name = 'x_steps', dtype = int, initial = 0, ro = True)
        self.settings.New(name = 'y_steps', dtype = int, initial = 0, ro = True)
        
        self.settings.New(name ='move_to_x', dtype = float, initial = 0, 
                          vmin = 0, vmax = 450, ro = False)
        self.settings.New(name ='move_to_y', dtype = float, initial = 0, 
                          vmin = 0, vmax = 430, ro = False)
        
        self.settings.New(name ='bound_x', dtype = float, initial = 7, 
                          vmin = 0, vmax = 450, ro = False)
        self.settings.New(name ='bound_y', dtype = float, initial = 7, 
                          vmin = 0, vmax = 430, ro = False)
        
        self.settings.New(name ='home_x', dtype = float, initial = 251.4, 
                          vmin = 0, vmax = 450, ro = True)
        
        self.settings.New(name ='home_y', dtype = float, initial = 7, 
                          vmin = 0, vmax = 430, ro = True)
        
        self.settings.New(name ='x_factor', dtype = float, initial = 0.01733812949, 
                          ro = True)
        self.settings.New(name ='y_factor', dtype = float, initial = 0.01733812949, 
                          ro = True)
        
        self.settings.New(name ='angle', dtype = float, initial = 45, 
                          ro = True, vmin = -180, vmax = 180)
        
        self.settings.New(name ='do_chans', dtype = str, 
                          initial = 'Dev2/port0/line5,Dev2/port1/line0,Dev2/port0/line1,Dev2/port1/line1', 
                          ro = True)
        self.settings.New(name ='counter0', dtype = str, 
                          initial = 'Dev2/ctr0', ro = True)
        self.settings.New(name ='counter1', dtype = str, 
                          initial = 'Dev2/ctr1', ro = True)
        self.settings.New(name ='terminal0', dtype = str, 
                          initial = '/Dev2/PFI12', ro = True)
        self.settings.New(name ='terminal1', dtype = str, 
                          initial = '/Dev2/PFI13', ro = True)
        
        self.settings.New(name ='frequency', dtype = float, initial = 4000, 
                          ro = False, vmin = 1, vmax = 10000)
        
        self.settings.New(name ='duty_cycle', dtype = float, initial = 0.5, 
                          ro = True, vmin = 0, vmax = 1)
        
        self.settings.New(name = 'max_steps', dtype = int, initial = 70,
                          ro = True, vmin = 100, vmax =300)
        
        self.settings.New(name = 'manual', dtype = bool, initial = False)
        self.settings.New(name = 'manual_steps', dtype = int, initial = 500,
                          ro = False, vmin = 0, vmax = 2000)
        
        self.settings.New(name ='path', dtype = 'file', is_dir = True, initial = './motor_location.h5')
        
        self.add_operation('reset',self.reset)
        self.add_operation('up',self.manual_up)
        self.add_operation('down',self.manual_down)
        self.add_operation('left',self.manual_left)
        self.add_operation('right',self.manual_right)
        self.add_operation('move_to',self.move_to)
        self.add_operation('zero',self.zero)
        self.add_operation('home',self.home)
    def connect(self):
        #connect to the camera device
        do_chans = self.settings.do_chans.value()
        counters = [self.settings.counter0.value(),
                   self.settings.counter1.value()]
        terminals = [self.settings.terminal0.value(),
                   self.settings.terminal1.value()]
        frequency = self.settings.frequency.value()
        duty_cycle = self.settings.duty_cycle.value()
        self.open_location_file()
        self.read_location()
        
        self._dev=DAQMotorDev(chans = do_chans, counter = counters, 
                              term = terminals, freq = frequency, 
                              dc = duty_cycle)
        
    def reset(self):
        self.settings.x_steps.update_value(0)
        self.settings.y_steps.update_value(0)
        self.update_cord()
        self.write_location()
        
    def move_to(self):
        if self.settings.manual.value():
            self.move_to_auto()
            
    def move_to_auto(self):
        new_x = self.settings.move_to_x.value()
        new_y = self.settings.move_to_y.value()
        old_x = self.settings.x.value()
        old_y = self.settings.y.value()
        x_factor = self.settings.x_factor.value()
        y_factor = self.settings.y_factor.value()
        
        move_steps_x = int((new_x - old_x)/x_factor)
        move_steps_y = int((new_y - old_y)/y_factor)
        
        pulses = np.array([move_steps_x,move_steps_y])
        self.move_cartesian(pulses)
            
    def zero(self):
        if self.settings.manual.value():
            self.settings.move_to_x.update_value(0)
            self.settings.move_to_y.update_value(0)
            self.move_to()
            
    def home(self):
        if self.settings.manual.value():
            self.settings.move_to_x.update_value(self.settings.home_x.value())
            self.settings.move_to_y.update_value(self.settings.home_y.value())
            self.move_to()
        
    def move_cartesian(self,num_pulses):
        angle = self.settings.angle.value()
        old_cord = np.array(num_pulses)
        old_cord[1] *= -1
        direction, new_pulses = rotate_cord(old_cord,angle)
        self._dev.move(direction,new_pulses)
        
        x_steps = self.settings.x_steps.value()
        self.settings.x_steps.update_value(x_steps + old_cord[0])
        y_steps = self.settings.y_steps.value()
        self.settings.y_steps.update_value(y_steps - old_cord[1])
        self.update_cord()
        self.write_location()
        
    def update_cord(self):
        x_steps = self.settings.x_steps.value()
        y_steps = self.settings.y_steps.value()
        x_factor = self.settings.x_factor.value()
        y_factor = self.settings.y_factor.value()
        self.settings.x.update_value(x_steps * x_factor)
        self.settings.y.update_value(y_steps * y_factor)
        
    def manual_left(self):
        if self.settings.manual.value():
            pulses = np.array([-self.settings.manual_steps.value(),0])
            self.move_cartesian(pulses)
        
    def manual_right(self):
        if self.settings.manual.value():
            pulses = np.array([self.settings.manual_steps.value(),0])
            self.move_cartesian(pulses)
        
    def manual_up(self):
        if self.settings.manual.value():
            pulses = np.array([0,self.settings.manual_steps.value()])
            self.move_cartesian(pulses)
        
    def manual_down(self):
        if self.settings.manual.value():
            pulses = np.array([0,-self.settings.manual_steps.value()])
            self.move_cartesian(pulses)
        
    def open_location_file(self):
        fname = self.settings.path.value()
        if os.path.isfile(fname):
            self.loc_file = h5py.File(fname,'r+')
            self.loc_dset = self.loc_file['/loc_data']
        else:
            self.loc_file = h5py.File(fname,'w')
            self.loc_dset = self.loc_file.create_dataset('loc_data',(2,),dtype ='longlong')
    
    def write_location(self):
        self.loc_dset[0] = self.settings.x_steps.value()
        self.loc_dset[1] = self.settings.y_steps.value()
        
    def read_location(self):
        self.settings.x_steps.update_value(self.loc_dset[0])
        self.settings.y_steps.update_value(self.loc_dset[1])
        self.update_cord()
    
    def close_location_file(self):
        del self.loc_dset
        self.loc_file.close()
        del self.loc_file
        
        
    def disconnect(self):
        '''
        need bug fix for pointer issues
        '''
        try:
            self._dev.close()
            self.write_location()
            self.close_location_file()
            del self._dev
            
        except AttributeError:
            pass