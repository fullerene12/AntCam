'''
Created on Jun 7, 2018
@author: Hao Wu
'''
import numpy as np
import serial
import time
import re

class TinyGDev(object):
    '''
    classdocs
    '''

    def __init__(self, port='COM3'):
        '''
        Constructor
        '''
        self.port=port
        self.ser=serial.Serial(self.port,
                               baudrate = 230400,
                               bytesize=serial.EIGHTBITS,
                               parity = serial.PARITY_NONE,
                               stopbits = serial.STOPBITS_ONE,
                               rtscts = True)
        
        #self.open()
        
    def move_to(self,x,y):
        output = bytes('$QF\n','utf-8')
        self.ser.write(output)
        output = bytes('g0x%.1fy%.1f\n'%(x,y),'utf-8')
        self.ser.write(output)
        
    def read_posx(self):
        self.ser.flushInput()
        output = bytes('$posx\n','utf-8')
        self.ser.write(output)
        xstr = self.ser.readline().decode('utf-8')
        xlst = re.findall(r"[-+]?\d*\.\d+|\d+",xstr)
        x = float(xlst[0])
        return x
    
    def read_posy(self):
        self.ser.flushInput()
        output = bytes('$posy\n','utf-8')
        self.ser.write(output)
        ystr = self.ser.readline().decode('utf-8')
        ylst = re.findall(r"[-+]?\d*\.\d+|\d+",ystr)
        y = float(ylst[0])
        return y
    
    def read_pos(self):
        return self.read_posx(),self.read_posy()
        
    def offsetx(self,xoff):
        self.ser.flushOutput()
        output  = bytes('$g54x=%.3f\n'%xoff,'ascii')
        self.ser.write(output)
        time.sleep(0.1)
        self.ser.flushInput()
        

    def offsety(self,yoff):
        self.ser.flushOutput()
        output  = bytes('$g54y=%.3f\n'%yoff,'ascii')
        self.ser.write(output)
        time.sleep(0.1)
        self.ser.flushInput()

        
    def reset(self):
        self.offsetx(0.0)
        self.offsety(0.0)
        x,y = self.read_pos()
        time.sleep(0.1)
        self.offsetx(x)
        self.offsety(y)
        
    def forward(self):
        output=bytes('f','utf-8')
        self.ser.write(output)
        
    def backward(self):
        output=bytes('b','utf-8')
        self.ser.write(output)
        
    def close(self):
        self.ser.close()


if __name__ == '__main__':
    motor = TinyGDev()
    motor.move_to(0,50)
    motor.close()