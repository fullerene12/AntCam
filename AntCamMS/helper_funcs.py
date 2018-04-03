'''
Created on Mar 31, 2018

@author: AntMan
'''
import numpy as np
from scipy import ndimage

def rebin(a, shape):
    sh = shape[0],a.shape[0]//shape[0],shape[1],a.shape[1]//shape[1]
    return a.reshape(sh).mean(-1).mean(1)

def find_centroid(image, threshold = 100, low_pass = True, binning = 8):
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
                cms = ndimage.center_of_mass(imagef)
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
    


if __name__ == '__main__':
    pass