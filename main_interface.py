"Create Measurement objects"'''
Created on Mar 26, 2018

@author: Hao Wu
'''
from ScopeFoundry import BaseMicroscopeApp
from qtpy import QtGui, QtWidgets

class AntCamApp(BaseMicroscopeApp):

    # this is the name of the microscope that ScopeFoundry uses 
    # when storing data
    name = 'ant_cam'
    
    # You must define a setup function that adds all the 
    #capablities of the microscope and sets default settings
    def setup(self):
        #start splash screen
        splash_pix = QtGui.QPixmap('splash.png')
        splash = QtWidgets.QSplashScreen(splash_pix)
        splash.show()
        splash.setEnabled(False)
        
        #Add App wide settings
        
        #Add hardware components
        splash.showMessage("Adding Hardware Components...")
        print("Adding Hardware Components")
        from AntCamHW.flircam.flircam_hw import FLIRCamHW
        splash.showMessage("Adding Tracking Camera...")
        track_cam = FLIRCamHW(self)
        track_cam.settings.camera_sn.update_value('16130612')
        splash.showMessage("Adding Side Camera...")
        track_cam.name = 'track_cam'
        wide_cam = FLIRCamHW(self)
        wide_cam.settings.camera_sn.update_value('15188107')
        wide_cam.name = 'wide_cam'
        self.add_hardware(track_cam)
        self.add_hardware(wide_cam)
        
        from AntCamHW.flircam.flirrec_hw import FLIRRecHW
        self.add_hardware(FLIRRecHW(self))
        
        from AntCamHW.daqmotor.daqmotor_hw import DAQMotorHW
        self.add_hardware(DAQMotorHW(self))
        
        #self.add_hardware(DAQTimerHW(self))

        #Add measurement components
        splash.showMessage("Create Measurement objects...")
        print("Create Measurement objects")
        from AntCamMS.ant_watch import AntWatchMeasure
        self.add_measurement(AntWatchMeasure(self))
        # Connect to custom gui
        
        # load side panel UI
        
        # show ui
        splash.finish(self.ui)
        self.ui.show()
        self.ui.activateWindow()
    

if __name__ == '__main__':
    import sys
    import ctypes

    myappid = 'MurthyLab.PyLab.AntCam.v1.0.0' # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = AntCamApp(sys.argv)
    
    app.ui.setWindowIcon(QtGui.QIcon('ant_icon.ico'))
    app.hardware['track_cam'].connected.update_value(True)
    #app.hardware['wide_cam'].connected.update_value(True)
    app.hardware['flirrec'].connected.update_value(True)
    app.hardware['daqmotor'].connected.update_value(True)
    #app.hardware['daq_timer'].connected.update_value(True)
    
    sys.exit(app.exec_())
    
    