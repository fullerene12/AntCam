'''
Created on Aug 9, 2017

@author: Hao Wu
'''

from ScopeFoundry import HardwareComponent
from .tinyg_dev import TinyGDev
import numpy as np
import time
from .motor_helper_funcs import rotate_cord
import h5py,os

class TinyGHW(HardwareComponent):
    '''
    Hardware Component Class for controlling two stepper motor tracker
    '''
    
    name='tinyg'

    def setup(self):
        self.settings.New(name ='x', dtype = float, initial = 0, ro = True)
        self.settings.New(name ='y', dtype = float, initial = 0, ro = True)
        
        self.settings.New(name ='xm', dtype = float, initial = 0, ro = True)
        self.settings.New(name ='ym', dtype = float, initial = 0, ro = True)
        
        self.settings.New(name = 'move_to_x',dtype = float,initial = 0, ro = False)
        self.settings.New(name = 'move_to_y',dtype = float,initial = 0, ro = False)
        self.settings.New(name = 'x_home',dtype = float,initial = 0, ro = True)
        self.settings.New(name = 'y_home',dtype = float,initial = 0, ro = True)
        self.settings.New(name = 'angle', dtype = float, initial = 45.0, ro = True)
        
        self.settings.New(name = 'manual', dtype = bool, initial = False)
        self.settings.New(name = 'manual_mm', dtype = float, initial = 10)
        
        self.settings.New(name = 'xmin', dtype = float, initial = 0, ro = True)
        self.settings.New(name = 'xmax', dtype = float, initial = 630, ro = True)
        
        self.settings.New(name = 'ymin', dtype = float, initial = 0, ro = True)
        self.settings.New(name = 'ymax', dtype = float, initial = 575, ro = True)
        self.settings.New(name = 'max_step', dtype = float, initial = 100, ro = False)
        
        self.settings.New(name = 'port', dtype = str, initial = 'COM3', ro = True)
        
        self.add_operation('left',self.manual_left)
        self.add_operation('right',self.manual_right)
        self.add_operation('up',self.manual_up)
        self.add_operation('down',self.manual_down)
        self.add_operation('reset',self.reset)
        self.add_operation('move_to',self.move_to)
        self.add_operation('zero',self.zero)
        self.add_operation('home',self.home)
        
    def connect(self):
        #connect to the camera device
        self._dev=TinyGDev(port = self.settings.port.value())
        time.sleep(1)
        self.update_cord()
                
    def reset(self):
        self.settings.x.update_value(0)
        self.settings.y.update_value(0)
        self._dev.reset()
        time.sleep(0.1)
        self.update_cord()
        self.write_location()
        
    def move_to(self):
        if self.settings.manual.value():
            self.update_cord()
            old_x = self.settings.x.value()
            old_y = self.settings.y.value()
            x = self.settings.move_to_x.value()
            y = self.settings.move_to_y.value()
            
            dx = x - old_x
            dy = y - old_y
            dd = np.sqrt(dx*dx + dy*dy)
            self.move_to_cartesian([x,y])
            time.sleep(0.2 + dd /150)
            self.update_cord()
            
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
        
    def move_to_cartesian(self,input):
        angle = self.settings.angle.value()
        output = rotate_cord(input,angle)
        self._dev.move_to(output[0],output[1])
        
    def move_cartesian_delta(self,dx,dy):
        self.update_cord()
        x = self.settings.x.value()
        y = self.settings.y.value()
        max_step = self.settings.max_step.value()
        
        dx = max(-max_step,dx)
        dx = min(max_step,dx)
        dy = max(-max_step,dy)
        dy = min(max_step,dy)
        new_x = max(x+dx,self.settings.xmin.value())
        new_x = min(new_x,self.settings.xmax.value())
        new_y = max(y+dy,self.settings.ymin.value())
        new_y = min(new_y,self.settings.ymax.value())
        self.move_to_cartesian([new_x,new_y])
        

        
    def update_cord(self):
        xm,ym = self._dev.read_pos()
        self.settings.xm.update_value(xm)
        self.settings.ym.update_value(ym)
        
        angle = self.settings.angle.value()
        new_cord = rotate_cord([xm,ym],-angle)
        self.settings.x.update_value(new_cord[0])
        self.settings.y.update_value(new_cord[1])
        
    def manual_left(self):
        if self.settings.manual.value():
            self.update_cord()
            x = self.settings.x.value()
            y = self.settings.y.value()
            new_x = x - self.settings.manual_mm.value()
            new_y = y

            self.move_to_cartesian([new_x,new_y])
            time.sleep(0.5)
            self.update_cord()
            
        
    def manual_right(self):
        if self.settings.manual.value():
            self.update_cord()
            x = self.settings.x.value()
            y = self.settings.y.value()
            new_x = x + self.settings.manual_mm.value()
            new_y = y

            self.move_to_cartesian([new_x,new_y])
            time.sleep(0.5)
            self.update_cord()
            
    def manual_up(self):
        if self.settings.manual.value():
            self.update_cord()
            x = self.settings.x.value()
            y = self.settings.y.value()
            new_x = x 
            new_y = y + self.settings.manual_mm.value()

            self.move_to_cartesian([new_x,new_y])
            time.sleep(0.5)
            self.update_cord()
        
    def manual_down(self):
        if self.settings.manual.value():
            self.update_cord()
            x = self.settings.x.value()
            y = self.settings.y.value()
            new_x = x 
            new_y = y - self.settings.manual_mm.value()

            self.move_to_cartesian([new_x,new_y])
            time.sleep(0.5)
            self.update_cord()
        
    def open_location_file(self):
        fname = self.settings.path.value()
        if os.path.isfile(fname):
            self.loc_file = h5py.File(fname,'r+')
            self.loc_dset = self.loc_file['/loc_data']
        else:
            self.loc_file = h5py.File(fname,'w')
            self.loc_dset = self.loc_file.create_dataset('loc_data',(2,),dtype ='longlong')
    
    def write_location(self):
        self.loc_dset[0] = self.settings.x.value()
        self.loc_dset[1] = self.settings.y.value()
        
    def read_location(self):
        self.settings.x.update_value(self.loc_dset[0])
        self.settings.y.update_value(self.loc_dset[1])
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