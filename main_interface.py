'''
Created on Mar 26, 2018

@author: Hao Wu
'''

from ScopeFoundry import BaseMicroscopeApp

class AntCamApp(BaseMicroscopeApp):

    # this is the name of the microscope that ScopeFoundry uses 
    # when storing data
    name = 'ant_cam'
    
    # You must define a setup function that adds all the 
    #capablities of the microscope and sets default settings
    def setup(self):
        
        #Add App wide settings
        
        #Add hardware components
        print("Adding Hardware Components")
        from AntCamHW.camera.camera_hw import CameraHW
        track_cam = CameraHW(self)
        track_cam.settings.camera_id.update_value(1)
        track_cam.name = 'track_cam'
        wide_cam = CameraHW(self)
        wide_cam.settings.camera_id.update_value(0)
        wide_cam.name = 'wide_cam'
        self.add_hardware(track_cam)
        self.add_hardware(wide_cam)
        
        from AntCamHW.daq_timer.daq_timer_hw import DAQTimerHW
        #self.add_hardware(DAQTimerHW(self))

        #Add measurement components
        print("Create Measurement objects")
        from AntCamMS.ant_watch import AntWatchMeasure
        self.add_measurement(AntWatchMeasure(self))
        # Connect to custom gui
        
        # load side panel UI
        
        # show ui
        self.ui.show()
        self.ui.activateWindow()
    

if __name__ == '__main__':
    import sys
    
    app = AntCamApp(sys.argv)
    
    app.hardware['track_cam'].connected.update_value(True)
    app.hardware['wide_cam'].connected.update_value(True)
    #app.hardware['daq_timer'].connected.update_value(True)
    
    sys.exit(app.exec_())
    
    