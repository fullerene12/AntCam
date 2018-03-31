'''
Created on Mar 26, 2018

@author: Hao Wu
'''
from ScopeFoundry import Measurement
from ScopeFoundry.measurement import MeasurementQThread
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import pyqtgraph as pg
import numpy as np
from scipy import ndimage
import time
import PySpin
from qtpy import QtCore
from qtpy.QtCore import QObject
import os
import queue

def rebin(a, shape):
    sh = shape[0],a.shape[0]//shape[0],shape[1],a.shape[1]//shape[1]
    return a.reshape(sh).mean(-1).mean(1)

class SubMeasurementQThread(MeasurementQThread):

    def __init__(self, run_func, parent=None):
        super(MeasurementQThread, self).__init__(parent)
        self.run_func = run_func
        self.interrupted = False
  
    def run(self):
        while not self.interrupted:
            self.run_func()
            if self.interrupted:
                break
            
    @QtCore.Slot()
    def interrupt(self):
        self.interrupted = True
    
class MovementThread(SubMeasurementQThread):
    x = 0
    y = 0

    @QtCore.Slot()
    def read_position(self,position):
        try:
            self.x = position[0]
            self.y = position[1]
        except Exception as ex:
            print('Error: %s' % ex)
            
class AntWatchMeasure(Measurement):
    
    # this is the name of the measurement that ScopeFoundry uses 
    # when displaying your measurement and saving data related to it    
    name = "ant_watch"
    interrupt_subthread = QtCore.Signal(())
    
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
        self.settings.New('save_video', dtype = bool, initial = False)
        self.settings.New('sampling_period', dtype=float, unit='s', initial=0.1)
        self.settings.New('writing_flag',dtype=bool,initial = False, ro= False)
        
        # Define how often to update display during a run
        self.display_update_period = 0.01
        
        # Convenient reference to the hardware used in the measurement
        self.track_cam = self.app.hardware['track_cam']
        self.wide_cam = self.app.hardware['wide_cam']
        self.recorder = self.app.hardware['recorder']
        
        #setup experiment condition
        self.track_cam.settings.frame_rate.update_value(30)
        self.wide_cam.settings.frame_rate.update_value(30)
        self.track_cam.read_from_hardware()
        self.wide_cam.read_from_hardware()
        
        self.track_output_queue = queue.Queue(1000)
        self.track_disp_queue = queue.Queue(1000)
        self.wide_disp_queue = queue.Queue(1000)

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
        if not hasattr(self,'wide_disp_queue'):
            return None
        elif self.wide_disp_queue.empty():
            return None
        else:
            try:
                wide_disp_image = self.wide_disp_queue.get()
                if type(wide_disp_image) == np.ndarray:
                    if wide_disp_image.shape == (self.wide_cam.settings.height.value(),self.wide_cam.settings.width.value()):
                        self.wide_cam_image.setImage(wide_disp_image)
            except Exception as ex:
                print("Error: %s" % ex)
                
        if not hasattr(self,'track_disp_queue'):
            return None
        elif self.track_disp_queue.empty():
            return None
        else:
            try:
                track_disp_image = self.track_disp_queue.get()
                if type(track_disp_image) == np.ndarray:
                    if track_disp_image.shape == (self.track_cam.settings.height.value(),self.track_cam.settings.width.value()):
                        self.track_cam_image.setImage(track_disp_image)
            except Exception as ex:
                print("Error: %s" % ex)
           
    
    def pre_run(self):
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
        if self.settings.save_video.value():
            save_dir = self.app.settings.save_dir.value()
            data_path = os.path.join(save_dir,self.app.settings.sample.value())
            try:
                os.makedirs(data_path)
            except OSError:
                print('directory already exist, writing to existing directory')
            
            self.recorder.settings.path.update_value(data_path)
        
            frame_rate = self.wide_cam.settings.frame_rate.value()
            self.recorder.create_file('track_mov',frame_rate)
            self.recorder.create_file('wide_mov',frame_rate)
            self.track_queue = queue.Queue(1000)
            self.wide_queue = queue.Queue(1000)
            
            self.rec_thread = SubMeasurementQThread(self.record_frame)
            self.interrupt_subthread.connect(self.rec_thread.interrupt)
            
        
        
        try:
            
            i = 0
            self.track_cam.config_event(self.track_repeat)
            self.wide_cam.config_event(self.wide_repeat)

            self.track_cam.start()
            self.wide_cam.start()
            # Will run forever until interrupt is called.
            while not self.interrupt_measurement_called:
                    
                    # wait between readings.
                    # We will use our sampling_period settings to define time
                comp_buffer = self.track_output_queue.get()
                if type(comp_buffer) == np.ndarray:
                    height = self.track_cam.settings.height.value()
                    width = self.track_cam.settings.width.value()
                    if comp_buffer.shape == (height,width):
                        binning = 8
                        binned_height = height / binning
                        binned_width = width /binning
                        binned_buffer = rebin(comp_buffer,(binned_height,binned_width))

            
                if self.interrupt_measurement_called:
                    # Listen for interrupt_measurement_called flag.
                    # This is critical to do, if you don't the measurement will
                    # never stop.
                    # The interrupt button is a polite request to the 
                    # Measurement thread. We must periodically check for
                    # an interrupt request
                    self.interrupt_subthread.emit()
                    break

        finally:
            
            self.track_cam.stop()
            self.wide_cam.stop()
            self.track_cam.remove_event()
            self.wide_cam.remove_event()

            if self.settings.save_video.value():
                self.rec_thread.terminate()
                del self.rec_thread
                self.recorder.close()

                del self.track_queue
                del self.wide_queue
                
            del self.track_disp_queue
            del self.wide_disp_queue
            del self.track_output_queue
            
        def post_run(self):
            pass
            
    def track_repeat(self):
        try:
            track_output_data = self.track_cam.read_output_data()
            track_disp_data =np.copy(track_output_data)
            self.track_disp_queue.put(track_disp_data)
            self.track_output_queue.put(track_output_data)
        except TypeError as ex:
            print("Error: %s" % ex)
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
        except ValueError as ex:
            print("Error: %s" % ex)
        except Exception as ex:
            print("Error: %s" % ex)
            
    def wide_repeat(self):
        try:
            wide_disp_data = self.wide_cam.read_output_data()
            self.wide_disp_queue.put(wide_disp_data)
#             if self.settings.save_video.value():
#                 track_image = self.track_cam.get_record_image()
#                 wide_image = self.wide_cam.get_record_image()
#                 self.track_queue.put(track_image)
#                 self.wide_queue.put(wide_image)
            pass
        except TypeError as ex:
            print("Error: %s" % ex)
        except PySpin.SpinnakerException as ex:
            print("Error: %s" % ex)
        except ValueError as ex:
            print("Error: %s" % ex)
          
    def record_frame(self):
        if self.settings.save_video.value():
            self.recorder.save_frame('track_mov',self.track_queue.get())
            self.recorder.save_frame('wide_mov',self.wide_queue.get())
#                
                

#             if self.settings['save_h5']:
#                 # make sure to close the data file
#                 self.h5file.close()