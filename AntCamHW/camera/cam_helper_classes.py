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

    def __init__(self, cam, run_func):
        """
        Constructor. Retrieves serial number of given camera and sets image counter to 0.

        :param cam: Camera device object
        :type cam: CameraHW
        :rtype: None
        """
        super(ImageEventHandler, self).__init__()
        
        self.cam = cam
        self.run_func = run_func
        
        # Initialize image counter to 0
        self._image_count = 0

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
        self.cam.buffer = image
        self.cam.update_output_buffer()
        self.cam.update_record_buffer()
        
        #run user_defined functions
        self.run_func()
        self._image_count += 1
        
    def get_image_count(self):
        """
        Getter for image count.

        :return: Number of images saved.
        :rtype: int
        """
        return self._image_count
        
if __name__ == '__main__':
    pass