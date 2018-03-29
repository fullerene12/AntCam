'''
Created on Mar 26, 2018

@author: Hao Wu
'''
from math import sqrt
from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import pyqtgraph as pg
import numpy as np
import time
import cv2
from qtpy.QtCore import QThread, QTimer, QTimerEvent

class AntWatchMeasure(Measurement):
    
    # this is the name of the measurement that ScopeFoundry uses 
    # when displaying your measurement and saving data related to it    
    name = "ant_watch"
    
    def setup(self):
        """
        Runs once during App initialization.
        This is the place to load a user interface file,
        define settings, and set up data structures. 
        """
        
        # Define ui file to be used as a graphical interface
        # This file can be edited graphically with Qt Creator
        # sibling_path function allows python to find a file in the same folder
        # as this python module
        self.ui_filename = sibling_path(__file__, "ant_watch_plot.ui")
        
        #Load ui file and convert it to a live QWidget of the user interface
        self.ui = load_qt_ui_file(self.ui_filename)

        # Measurement Specific Settings
        # This setting allows the option to save data to an h5 data file during a run
        # All settings are automatically added to the Microscope user interface
        self.settings.New('save_h5', dtype=bool, initial=True)
        self.settings.New('sampling_period', dtype=float, unit='s', initial=0.1)
        self.settings.New('writing_flag',dtype=bool,initial = False, ro= False)
        
        # Create empty numpy array to serve as a buffer for the acquired data
        self.track_buffer = np.zeros((1200,1920),dtype=np.uint8)
        self.wide_buffer = np.zeros((2048,2048), dtype=np.uint8)
        self.track_disp_buffer = np.zeros((1200,1920),dtype=np.uint8)
        self.wide_disp_buffer = np.zeros((2048,2048), dtype=np.uint8)
        
        # Define how often to update display during a run
        self.display_update_period = 0.02
        
        # Convenient reference to the hardware used in the measurement
        self.track_cam = self.app.hardware['track_cam']
        self.wide_cam = self.app.hardware['wide_cam']


    def setup_figure(self):
        """
        Runs once during App initialization, after setup()
        This is the place to make all graphical interface initializations,
        build plots, etc.
        """
        
        # connect ui widgets to measurement/hardware settings or functions
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        
        # Set up pyqtgraph graph_layout in the UI
        self.wide_cam_layout=pg.GraphicsLayoutWidget()
        self.track_cam_layout=pg.GraphicsLayoutWidget()
        self.ui.wide_cam_groupBox.layout().addWidget(self.wide_cam_layout)
        self.ui.track_cam_groupBox.layout().addWidget(self.track_cam_layout)

        #create camera image graphs
        self.wide_cam_view=pg.ViewBox()
        self.wide_cam_layout.addItem(self.wide_cam_view)
        self.wide_cam_image=pg.ImageItem()
        self.wide_cam_view.addItem(self.wide_cam_image)
        
        self.track_cam_view=pg.ViewBox()
        self.track_cam_layout.addItem(self.track_cam_view)
        self.track_cam_image=pg.ImageItem()
        self.track_cam_view.addItem(self.track_cam_image)
        
    def update_display(self):
        """
        Displays (plots) the numpy array self.buffer. 
        This function runs repeatedly and automatically during the measurement run.
        its update frequency is defined by self.display_update_period
        """
        try:
            self.track_disp_buffer[:] = self.track_cam.read_disp()
            self.wide_disp_buffer[:] = self.wide_cam.read_disp()
            self.track_cam_image.setImage(self.track_disp_buffer)
            self.wide_cam_image.setImage(self.wide_disp_buffer)

            pass
        except TypeError:
            pass

    
    def run(self):
        """
        Runs when measurement is started. Runs in a separate thread from GUI.
        It should not update the graphical interface directly, and should only
        focus on data acquisition.
        """
#         # first, create a data file
#         if self.settings['save_h5']:
#             # if enabled will create an HDF5 file with the plotted data
#             # first we create an H5 file (by default autosaved to app.settings['save_dir']
#             # This stores all the hardware and app meta-data in the H5 file
#             self.h5file = h5_io.h5_base_file(app=self.app, measurement=self)
#             
#             # create a measurement H5 group (folder) within self.h5file
#             # This stores all the measurement meta-data in this group
#             self.h5_group = h5_io.h5_create_measurement_group(measurement=self, h5group=self.h5file)
#             
#             # create an h5 dataset to store the data
#             self.buffer_h5 = self.h5_group.create_dataset(name  = 'buffer', 
#                                                           shape = self.buffer.shape,
#                                                           dtype = self.buffer.dtype)
        
        # We use a try/finally block, so that if anything goes wrong during a measurement,
        # the finally block can clean things up, e.g. close the data file object.
        try:
            
            self.track_cam.start()
            self.wide_cam.start()
            # Will run forever until interrupt is called.
            
            
            self.track_cam_frame = True
            #self.i = 0
            self.last_time = time.time()
            self.time_diff = 0.0
            self.this_time = time.time()
            self.acq_thread.setPriority(QThread.TimeCriticalPriority)
            self.start_time = time.clock()
            while not self.interrupt_measurement_called:
                current_time = time.clock() - self.start_time
                current_time_convert = int((current_time-int(current_time))*10000)
                if current_time_convert % 200 == 1:
                    self.repeat()

                # wait between readings.
                # We will use our sampling_period settings to define time
                #time.sleep(self.settings['sampling_period'])
                
                if self.interrupt_measurement_called:
                    # Listen for interrupt_measurement_called flag.
                    # This is critical to do, if you don't the measurement will
                    # never stop.
                    # The interrupt button is a polite request to the 
                    # Measurement thread. We must periodically check for
                    # an interrupt request
                    break

        finally:      
            time.sleep(0.1)
            self.track_cam.stop()
            self.wide_cam.stop()
            
    def repeat(self):
        time1 = time.time()
        self.track_buffer[:] = self.track_cam.read()
        self.wide_buffer[:] = self.wide_cam.read()
        
        time2 = time.time()  
                

        print(time2-time1,end ='\r')

#                
                
def rebin(a, shape):
    sh = shape[0],a.shape[0]//shape[0],shape[1],a.shape[1]//shape[1]
    return a.reshape(sh).mean(-1).mean(1)
#             if self.settings['save_h5']:
#                 # make sure to close the data file
#                 self.h5file.close()