'''
Created on Apr 5, 2018

@author: Hao Wu
'''
import numpy as np

def rotate_cord(input_cord, angle = 45):
    '''
    rotate the input (x,y) by angle(degrees)
    
    input_cord: (x,y)
    angle: rotation angle in degrees
    '''
    theta = np.radians(angle)
    c, s = np.cos(theta), np.sin(theta)
    R = np.matrix([[c, -s], [s, c]])
    new_cord = np.array(np.matmul(R,input_cord)).squeeze()
    return new_cord
    
def wall_find(image,axis = 0, threshold = 100):
    '''
    find an 
    '''
    pass

if __name__ == '__main__':
    print(rotate_cord([0,1],angle = 45))