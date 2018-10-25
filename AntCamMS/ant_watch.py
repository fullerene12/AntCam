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
from .helper_funcs import find_centroid, PIDController

class SubMeasurementQThread(MeasurementQThread):
    '''
    Sub-Thread for different loops in measurement
    '''

    def __init__(self, run_func, parent=None):
        '''
        run_func: user-defined function to run in the loop
        parent = parent thread, usually None
        '''
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
        self.settings.New('save_video', dtype = bool, initial = False)
        self.settings.New('track_ant',dtype = bool, initial = False)
        self.settings.New('pixel_size', dtype = float, initial = 0.05547850208, ro = True)
        self.settings.New('binning', dtype = int, initial = 16, ro = True)
        self.settings.New('threshold', dtype = int, initial = 85, ro = False)
        self.settings.New('proportional', dtype = float, initial = 0.12, ro = False)
        self.settings.New('integral', dtype = float, initial = 0, ro = False)
        self.settings.New('derivative', dtype = float, initial = 0.05, ro = False)
        
        # x and y is for transmitting signal
        self.settings.New('x',dtype = float, initial = 32, ro = True, vmin = 0, vmax = 63.5)
        self.settings.New('y',dtype = float, initial = 32, ro = True, vmin = 0, vmax = 63.5)
        
        # Define how often to update display during a run
        self.display_update_period = 0.01
        
        
        # Convenient reference to the hardware used in the measurement
        self.track_cam = self.app.hardware['track_cam']
        self.wide_cam = self.app.hardware['wide_cam']
        self.recorder = self.app.hardware['flirrec']
        self.daqmotor = self.app.hardware['daqmotor']
        
        #setup experiment condition
        self.track_cam.settings.frame_rate.update_value(50)
        self.track_cam.read_from_hardware()

    def setup_figure(self):
        """
        Runs once during App initialization, after setup()
        This is the place to make all graphical interface initializations,
        build plots, etc.
        """
        # connect ui widgets to measurement/hardware settings or functions
        self.settings.save_video.connect_to_widget(self.ui.save_video_checkBox)
        self.settings.track_ant.connect_to_widget(self.ui.track_ant_checkBox)
        
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        self.ui.up_pushButton.clicked.connect(self.daqmotor.operations['up'])
        self.ui.down_pushButton.clicked.connect(self.daqmotor.operations['down'])
        self.ui.left_pushButton.clicked.connect(self.daqmotor.operations['left'])
        self.ui.right_pushButton.clicked.connect(self.daqmotor.operations['right'])
        self.daqmotor.settings.manual.connect_to_widget(self.ui.manual_checkBox)
        self.daqmotor.settings.manual_steps.connect_to_widget(self.ui.manual_steps_doubleSpinBox)
        
        self.daqmotor.settings.x.connect_to_widget(self.ui.x_doubleSpinBox)
        self.daqmotor.settings.y.connect_to_widget(self.ui.y_doubleSpinBox)
        self.daqmotor.settings.move_to_x.connect_to_widget(self.ui.move_to_x_doubleSpinBox)
        self.daqmotor.settings.move_to_y.connect_to_widget(self.ui.move_to_y_doubleSpinBox)
        self.ui.move_to_pushButton.clicked.connect(self.daqmotor.operations['move_to'])
        self.ui.zero_pushButton.clicked.connect(self.daqmotor.operations['zero'])
        self.ui.home_pushButton.clicked.connect(self.daqmotor.operations['home'])
        
        # Set up pyqtgraph graph_layout in the UI
        self.wide_cam_layout=pg.GraphicsLayoutWidget()
        self.track_cam_layout=pg.GraphicsLayoutWidget()
        self.tracker_layout=pg.GraphicsLayoutWidget()
        self.ui.wide_cam_groupBox.layout().addWidget(self.wide_cam_layout)
        self.ui.track_cam_groupBox.layout().addWidget(self.track_cam_layout)
        self.ui.tracker_groupBox.layout().addWidget(self.tracker_layout)
        
        '''
        Clean up this at some point
        '''
        #create camera image graphs
        self.wide_cam_view=pg.ViewBox()
        self.track_cam_view=pg.ViewBox()
        self.wide_cam_layout.addItem(self.track_cam_view)
        self.wide_cam_image=pg.ImageItem()
        self.track_cam_image=pg.ImageItem()
        self.track_cam_view.addItem(self.track_cam_image)
        self.track_histogram = pg.HistogramLUTItem(self.track_cam_image)
        self.wide_cam_layout.addItem(self.track_histogram)
        self.track_histogram.setLevels(0,200)
        
        #self.track_cam_view=pg.ViewBox()
        #self.track_cam_layout.addItem(self.track_cam_view)
        #self.track_cam_image=pg.ImageItem()
        #self.track_cam_view.addItem(self.track_cam_image)
        
        self.tracker_view=pg.ViewBox()
        self.tracker_layout.addItem(self.tracker_view)
        self.tracker_image=pg.ImageItem()
        self.tracker_view.addItem(self.tracker_image)
        
        # initiate tracker buffer
        self.tracker_data = np.zeros((64,64),dtype = np.uint8)
        
        #counter used for reducing refresh rate
        self.wide_disp_counter = 0
        self.track_disp_counter = 0
        
    def update_display(self):
        """
        Displays (plots) the numpy array self.buffer. 
        This function runs repeatedly and automatically during the measurement run.
        its update frequency is defined by self.display_update_period
        """
        
        # check availability of display queue of the wide camera
#         if not hasattr(self,'wide_disp_queue'):
#             pass
#         elif self.wide_disp_queue.empty():
#             pass
#         else:
#             try:
#                 wide_disp_image = self.wide_disp_queue.get()
#                 
#                 self.wide_disp_counter += 1
#                 self.wide_disp_counter %= 2
#                 if self.wide_disp_counter == 0:
#                     if type(wide_disp_image) == np.ndarray:
#                         if wide_disp_image.shape == (self.wide_cam.settings.height.value(),self.wide_cam.settings.width.value()):
#                             try:
#                                 self.wide_cam_image.setImage(wide_disp_image)
#                             except Exception as ex:
#                                 print('Error: %s' % ex)
#             except Exception as ex:
#                 print("Error: %s" % ex)
        
        # check availability of display queue of the track camera         
        if not hasattr(self,'track_disp_queue'):
            pass
        elif self.track_disp_queue.empty():
            pass
        else:
            try:
                track_disp_image = self.track_disp_queue.get()
                self.track_disp_counter += 1
                self.track_disp_counter %= 4
                if self.track_disp_counter == 0:
                    if type(track_disp_image) == np.ndarray:
                        if track_disp_image.shape == (self.track_cam.settings.height.value(),self.track_cam.settings.width.value()):
                            try:
                                self.track_cam_image.setImage(track_disp_image)
                            except Exception as ex:
                                print('Error: %s' % ex)
                                
                    x = int(self.settings.x.value())
                    y = int(self.settings.y.value())
                    self.tracker_data[:] = 0
                    self.tracker_data[x,y] = 1
                    self.tracker_image.setImage(np.copy(self.tracker_data))
            except Exception as ex:
                print("Error: %s" % ex)

    def run(self):
        """
        Runs when measurement is started. Runs in a separate thread from GUI.
        It should not update the graphical interface directly, and should only
        focus on data acquisition.
        """
        self.buffer = np.zeros((60000,2))
        self.track_cam._dev.set_buffer_count(500)
        
        
            # if enabled will create an HDF5 file with the plotted data
            # first we create an H5 file (by default autosaved to app.settings['save_dir']
            # This stores all the hardware and app meta-data in the H5 file

        if self.settings.save_video.value():
            save_dir = self.app.settings.save_dir.value()
            data_path = os.path.join(save_dir,self.app.settings.sample.value())
            try:
                os.makedirs(data_path)
            except OSError:
                print('directory already exist, writing to existing directory')

            frame_rate = self.track_cam.settings.frame_rate.value()
            self.recorder.settings.path.update_value(data_path)
            
            self.recorder.create_file('track_mov',frame_rate)
            
            #save h5
            file_name_index=0
            file_name=os.path.join(self.recorder.settings.path.value(),'trail_'+str(file_name_index)+'.h5')
            while os.path.exists(file_name):
                file_name_index+=1
                file_name=os.path.join(self.recorder.settings.path.value(),'trail_'+str(file_name_index)+'.h5')
        
            self.h5file = h5_io.h5_base_file(app=self.app, measurement=self,fname = file_name)
            
            # create a measurement H5 group (folder) within self.h5file
            # This stores all the measurement meta-data in this group
            self.h5_group = h5_io.h5_create_measurement_group(measurement=self, h5group=self.h5file)
        

            # create an h5 dataset to store the data
            self.buffer_h5 = self.h5_group.create_dataset(name  = 'buffer', 
                                                          shape = self.buffer.shape,
                                                          dtype = self.buffer.dtype)
            
            
        

#             self.recorder.create_file('wide_mov',frame_rate)
        
        self.track_disp_queue = queue.Queue(1000)
#         self.wide_disp_queue = queue.Queue(1000)
        self.motor_queue = queue.Queue(1000)
        self.comp_thread = SubMeasurementQThread(self.camera_action)
        self.motor_thread = SubMeasurementQThread(self.motor_action)
        
        self.interrupt_subthread.connect(self.comp_thread.interrupt)
        self.interrupt_subthread.connect(self.motor_thread.interrupt)
        
        self.pid = PIDController(p = self.settings.proportional.value(),
                             i = self.settings.integral.value(),
                             d = self.settings.derivative.value())
        self.midpoint = (self.track_cam.settings.height.value()//self.settings.binning.value())//2
        self.pix_size = self.settings.pixel_size.value() * self.settings.binning.value()

        try:
            self.track_i = 0
            self.i = 0
#             self.wide_i = 0
            
            self.track_flag = False
            
            self.track_cam.start()
#             self.wide_cam.start()
            self.comp_thread.start()
            self.motor_thread.start()
            
            # Will run forever until interrupt is called.
            while not self.interrupt_measurement_called:
                #wait for 0.1ms
                time.sleep(0.5)
        
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
#             self.wide_cam.stop()
            if self.settings.save_video.value():
                self.recorder.close()
            
            del self.motor_thread           
            del self.comp_thread
            del self.motor_queue
            del self.track_disp_queue
            if self.settings.save_video.value():
                self.recorder.close()
                self.h5file.close()
#             del self.wide_disp_queue

    def camera_action(self):
        '''
        format the image properly, and find centroid on the track cam
        '''
        try:
            self.i += 1
            self.track_i += 1
            self.track_i %= 6
            track_image = self.track_cam.read()
            
            if self.track_flag:
                if self.settings.save_video.value():
                    self.recorder.save_frame('track_mov',track_image)
                    self.buffer[self.i,0] = self.daqmotor.settings.x.value()
                    self.buffer[self.i,1] = self.daqmotor.settings.y.value()
                    self.buffer_h5[self.i,:] = self.buffer[self.i,:]
                    self.h5file.flush()
                if self.track_i % 2 == 0:
                    time.sleep(0.001)
                    track_data = self.track_cam._dev.to_numpy(track_image)
                    track_disp_data = np.copy(track_data)
                    self.track_disp_queue.put(np.fliplr(track_disp_data.transpose()))
                    try:
                        cms = find_centroid(image = track_data, 
                                            threshold = self.settings.threshold.value(), 
                                            binning = self.settings.binning.value())
                        tracker_size = self.track_cam.settings.height.value()//self.settings.binning.value()
                        self.settings.x.update_value(cms[1])
                        self.settings.y.update_value(tracker_size - cms[0])
                        if self.settings.track_ant.value():
                            self.motor_queue.put((cms[1],tracker_size - cms[0]))
                    except Exception as ex:
                        print('CMS Error : %s' % ex)
            else:
                if self.track_i == 0:
                    track_data = self.track_cam._dev.to_numpy(track_image)
                    if not self.settings.track_ant.value():
                        track_disp_data = np.copy(track_data)
                        self.track_disp_queue.put(np.fliplr(track_disp_data.transpose()))
                    if track_data.min()< self.settings.threshold.value():
                        self.track_flag = True
            
                
        except Exception as ex:
            print('Error : %s' % ex)
            
#         try:
#             self.wide_i += 1
#             self.wide_i %= 5
#             wide_image= self.wide_cam.read()
#             
#             if self.track_flag:
#                 if self.settings.save_video.value():
#                     self.recorder.save_frame('wide_mov',wide_image)
#                 if self.wide_i == 0:
#                     time.sleep(0.001)
#                     wide_data = self.wide_cam._dev.to_numpy(wide_image)
#                     self.wide_disp_queue.put(wide_data)
#         except Exception as ex:
#             print('Error : %s' % ex)
            
            
    def motor_action(self):
        if self.settings.track_ant.value():
            cords = self.motor_queue.get()
            error_x = (cords[0] - self.midpoint) * self.pix_size
            error_y = (cords[1] - self.midpoint) * self.pix_size
            x_fb = self.pid.feedback(error_x)
            y_fb = self.pid.feedback(error_y)
            new_x = self.daqmotor.settings.x.value() + x_fb
            new_y = self.daqmotor.settings.y.value() + y_fb
            if new_x < self.daqmotor.settings.bound_x.value():
                self.daqmotor.settings.move_to_x.update_value(self.daqmotor.settings.bound_x.value()+2)
            elif new_x > self.daqmotor.settings.move_to_x.vmax:
                self.daqmotor.settings.move_to_x.update_value(self.daqmotor.settings.move_to_x.vmax-2)
            else:
                self.daqmotor.settings.move_to_x.update_value(new_x)
            if new_y < self.daqmotor.settings.bound_y.value():
                self.daqmotor.settings.move_to_y.update_value(self.daqmotor.settings.bound_y.value()+2)
            elif new_y > self.daqmotor.settings.move_to_y.vmax:
                self.daqmotor.settings.move_to_y.update_value(self.daqmotor.settings.move_to_y.vmax-2)
            else:
                self.daqmotor.settings.move_to_y.update_value(new_y)
            self.daqmotor.move_to_auto()
        else:
            time.sleep(0.2)
                

