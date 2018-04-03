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
from .helper_funcs import find_centroid

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
        self.settings.New('x',dtype = float, initial = 32, ro = True, vmin = 0, vmax = 63.5)
        self.settings.New('y',dtype = float, initial = 32, ro = True, vmin = 0, vmax = 63.5)
        
        # Define how often to update display during a run
        self.display_update_period = 0.01
        
        # Convenient reference to the hardware used in the measurement
        self.track_cam = self.app.hardware['track_cam']
        self.wide_cam = self.app.hardware['wide_cam']
        self.recorder = self.app.hardware['recorder']
        
        #setup experiment condition
        self.track_cam.settings.frame_rate.update_value(25)
        self.wide_cam.settings.frame_rate.update_value(25)
        self.track_cam.read_from_hardware()
        self.wide_cam.read_from_hardware()

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
        self.tracker_layout=pg.GraphicsLayoutWidget()
        self.ui.wide_cam_groupBox.layout().addWidget(self.wide_cam_layout)
        self.ui.track_cam_groupBox.layout().addWidget(self.track_cam_layout)
        self.ui.tracker_groupBox.layout().addWidget(self.tracker_layout)
        
        #create camera image graphs
        self.wide_cam_view=pg.ViewBox()
        self.wide_cam_layout.addItem(self.wide_cam_view)
        self.wide_cam_image=pg.ImageItem()
        self.wide_cam_view.addItem(self.wide_cam_image)
        
        self.track_cam_view=pg.ViewBox()
        self.track_cam_layout.addItem(self.track_cam_view)
        self.track_cam_image=pg.ImageItem()
        self.track_cam_view.addItem(self.track_cam_image)
        
        self.tracker_view=pg.ViewBox()
        self.tracker_layout.addItem(self.tracker_view)
        self.tracker_image=pg.ImageItem()
        self.tracker_view.addItem(self.tracker_image)
        
        self.tracker_data = np.zeros((64,64),dtype = np.uint8)
        
    def update_display(self):
        """
        Displays (plots) the numpy array self.buffer. 
        This function runs repeatedly and automatically during the measurement run.
        its update frequency is defined by self.display_update_period
        """
        x = int(self.settings.x.value())
        y = int(self.settings.y.value())
        self.tracker_data[:] = 0
        self.tracker_data[x,y] = 1
        self.tracker_image.setImage(np.fliplr(np.copy(self.tracker_data).transpose()))
        
        if self.wide_cam.empty():
            pass
        else:
            try:
                wide_disp_data = self.wide_cam.read()
                wide_disp_image = self.wide_cam.to_numpy(wide_disp_data)
                if type(wide_disp_image) == np.ndarray:
                    if wide_disp_image.shape == (self.wide_cam.settings.height.value(),self.wide_cam.settings.width.value()):
                        try:
                            self.wide_cam_image.setImage(np.copy(wide_disp_image))
                        except Exception as ex:
                            print('Error: %s' % ex)
            except Exception as ex:
                print("Error: %s" % ex)
                 
        if not hasattr(self,'track_disp_queue'):
            pass
        elif self.track_disp_queue.empty():
            pass
        else:
            try:
                track_disp_image = self.track_disp_queue.get()
                if type(track_disp_image) == np.ndarray:
                    if track_disp_image.shape == (self.track_cam.settings.height.value(),self.track_cam.settings.width.value()):
                        try:
                            self.track_cam_image.setImage(np.copy(track_disp_image))
                        except Exception as ex:
                            print('Error: %s' % ex)
            except Exception as ex:
                print("Error: %s" % ex)

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
            self.track_cam._dev.recording = True
            self.wide_cam._dev.recording = True
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
            
            self.rec_thread = SubMeasurementQThread(self.record_frame)
            self.interrupt_subthread.connect(self.rec_thread.interrupt)
        
        
        
        self.track_output_queue = queue.Queue(1000)
        self.track_disp_queue = queue.Queue(1000)
        self.wide_disp_queue = queue.Queue(1000)
        self.comp_thread = SubMeasurementQThread(self.compute_location)
        self.interrupt_subthread.connect(self.comp_thread.interrupt)

        try:
            threshold = 100
            self.i = 0
            self.track_cam.config_event(self.track_repeat)
            self.wide_cam.config_event(self.wide_repeat)
            
            if self.settings.save_video.value():
                self.rec_thread.start()
            self.comp_thread.start()
            self.track_cam.start()
            self.wide_cam.start()
            # Will run forever until interrupt is called.
            while not self.interrupt_measurement_called:
                #i += 1
#                 track_disp_data = self.track_cam._dev.data_q.get()
#                 wide_disp_data = self.wide_cam._dev.data_q.get()
                #print(self.track_cam._dev.data_q.qsize())
                time.sleep(0.5)
                    
                    # wait between readings.
                    # We will use our sampling_period settings to define time
                
#                 #track_disp_data =np.copy(track_output_data)
#                 self.track_disp_queue.put(track_disp_data)
#                 
                
#                 self.wide_disp_queue.put(wide_disp_data)
# #             self.track_output_queue.put(track_output_data)
#                 comp_buffer = self.track_output_queue.get()
#                 
#                 
#                 if type(comp_buffer) == np.ndarray:
#                     height = self.track_cam.settings.height.value()
#                     width = self.track_cam.settings.width.value()
#                     
#                     if comp_buffer.shape == (height,width):
#                         i += 1
#                         time1 = time.clock()
#                         try:
#                             cms = find_centroid(image = comp_buffer, threshold = 100, binning = 16)
#                         except Exception as ex:
#                             print('Error: %s' % ex)
#                             cms = (512,512)
#                         time2 = time.clock()
#                         
#                         if i%3600 == 0:
#                             print((time2 - time1) * 1000, cms)

            
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
                self.track_cam._dev.recording = False
                self.wide_cam._dev.recording = False
            
            self.comp_thread.terminate()
            del self.comp_thread
            del self.track_disp_queue
            del self.wide_disp_queue
            del self.track_output_queue
            
            
    def track_repeat(self):
        pass
            
    def wide_repeat(self):
        pass
          
    def record_frame(self):
        if self.settings.save_video.value():
            self.recorder.save_frame('track_mov',self.track_cam._dev.read_record_frame())
            self.recorder.save_frame('wide_mov',self.wide_cam._dev.read_record_frame())
            
    def compute_location(self):
        '''
        format the image properly, and find centroid on the track cam
        '''
        try:
            track_disp_data = self.track_cam.read()
            track_disp_image = self.track_cam.to_numpy(track_disp_data)
            track_comp_image = np.copy(track_disp_image)
            self.track_disp_queue.put(np.fliplr(track_disp_image.transpose()))
            try:
                self.i += 1
                cms = find_centroid(image = track_comp_image, threshold = 100, binning = 16)
                self.settings.x.update_value(cms[0])
                self.settings.y.update_value(cms[1])
            except Exception as ex:
                print('CMS Error : %s' % ex)
        except Exception as ex:
            print('Error : %s' % ex)
                

#             if self.settings['save_h5']:
#                 # make sure to close the data file
#                 self.h5file.close()