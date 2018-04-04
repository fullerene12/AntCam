'''
Created on Mar 29, 2018

@author: Hao Wu

Adapted from FLIR PySpin Example ImageEvents
'''
import PySpin

class ImageEventHandler(PySpin.ImageEvent):
    """
    This class defines the properties, parameters, and the event itself. Take a
    moment to notice what parts of the class are mandatory, and what have been
    added for demonstration purposes. First, any class used to define image events
    must inherit from ImageEvent. Second, the method signature of OnImageEvent()
    must also be consistent. Everything else - including the constructor,
    destructor, properties, body of OnImageEvent(), and other functions -
    is particular to the example.
    """

    def __init__(self, cam):
        """
        Constructor. Retrieves serial number of given camera and sets image counter to 0.

        :param cam: Camera device object
        :type cam: CameraHW
        :rtype: None
        """
        super(ImageEventHandler, self).__init__()
        
        self.cam = cam
        
        # Initialize image counter to 0

    def OnImageEvent(self, image):
        """
        This method defines an image event. In it, the image that triggered the
        event is converted and saved before incrementing the count. Please see
        Acquisition example for more in-depth comments on the acquisition
        of images.

        :param image: Image from event.
        :type image: ImagePtr
        :rtype: None
        """
        # update all buffers in the camera
        status = True
        #status = True
        #print(status)

        if status:
            #image_converted = PySpin.Image.Create(image)
            image_converted = image.Convert(PySpin.PixelFormat_Mono8)
            
            if self.cam.recording:
                image_recorded = PySpin.Image.Create(image)
                self.cam.write_record_frame(image_recorded)
            
            try:
                self.cam.write(image_converted)
            except Exception as ex:
                print('In callback, Error as %s' % ex)
            
            image.Release()

            del image
        else:
            print('status is %i' % status)
        
if __name__ == '__main__':
    pass