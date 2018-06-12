'''
Created on Mar 31, 2018

@author: AntMan
'''
import numpy as np
from scipy import ndimage

def rebin(a, shape):
    sh = shape[0],a.shape[0]//shape[0],shape[1],a.shape[1]//shape[1]
    return a.reshape(sh).mean(-1).mean(1)

def find_centroid(image, threshold = 120, low_pass = True, binning = 8):
    '''
    take a 2d array and find centroid of said array
    
    image: input image array
    threshold: under
    mode: 'low' or 'high', lock on to feature lower or higher than threshold
    binning: pixel binning number to improve speed
    '''
    h = image.shape[0]
    w = image.shape[1]
    
    if h % binning == 0 and w % binning == 0:
        hb = h // binning
        wb = w // binning
        try:
            imageb = rebin(image,(hb,wb))
        except Exception as ex:
            print('Error: %s' % ex)
            return (h/(binning*2),w/(binning*2))
                
        
        if low_pass:
            imagef = imageb < threshold
        else:
            imagef = imageb > threshold
        
        if imagef.max()>0:
            try:
                cms = ndimage.center_of_mass(imagef.astype(np.float))
                return cms
            except Exception as ex:
                print('Error: %s' % ex)
                return (h/(binning*2),w/(binning*2))
        else:
            #print('Could not identify any feature with the threshold settings, returning (h/2,w/2)')
            return (h/(binning*2),w/(binning*2))
        
    else:
        print('Height or width is not divisible by binning, returning (h/2,w/2)')
        return (h/(binning*2),w/(binning*2))
    
class PIDController(object):
    '''
    PID controller object, takes in an error signal (float) and output a feedback
    '''
    
    def __init__(self, p = 1, i = 0, d = 0, msize = 5):
        '''
        initialize the controller
        
        p: proportional factor (float)
        i: integral factor (float)
        d: derivative factor (float)
        msize: the size of memory used for integration (int)
        '''
        self.p = p
        self.i = i
        self.d = d
        self.msize = msize
        self.memory = np.zeros((self.msize,))
        self.last_error = 0
        self.first_trial = True
        
    def memorize_error(self,error):
        '''
        take in a new error and put it into internal memory
        '''
        self.memory[0:-1] = self.memory[1:]
        self.memory[-1] = error
    
    def diff_error(self,error):
        '''
        differentiate the error signal to find the derivative
        '''
        return error - self.last_error
    
    def feedback(self,error):
        '''
        take an error and give a PID feedback
        '''
        output = 0
        output += self.p * error
        if not self.i == 0:
            self.memorize_error(error)
            output += self.i * self.memory.sum()
        if not self.d == 0:
            if self.first_trial:
                self.first_trial = False
            else:
                deriv = self.diff_error(error)
                output += self.d * deriv
            self.last_error = error
        return output
