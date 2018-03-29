'''
Created on Aug 9, 2017

@author: Lab Rat
'''
from math import sqrt
from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
from ScopeFoundry import h5_io
import pyqtgraph as pg
import numpy as np
import time
import os
from random import randint,random
from PyQt5.QtWidgets import QDoubleSpinBox, QCheckBox
            
class VOTABlockTrainingMeasure(Measurement):
    
    # this is the name of the measurement that ScopeFoundry uses 
    # when displaying your measurement and saving data related to it    
    name = "block_training"
    
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
        self.ui_filename = sibling_path(__file__, "block_training_plot.ui")
        
        #Load ui file and convert it to a live QWidget of the user interface
        self.ui = load_qt_ui_file(self.ui_filename)

        # Measurement Specific Settings
        # This setting allows the option to save data to an h5 data file during a run
        # All settings are automatically added to the Microscope user interface
        self.settings.New('save_h5', dtype=bool, initial=False)
        self.settings.New('train',dtype = bool, initial = False, ro = False)
        self.settings.New('block_number', dtype = int, initial = 10)
        self.settings.New('save_movie', dtype=bool, initial=False,ro=False)
        self.settings.New('movie_on', dtype=bool, initial=False,ro=True)
        self.settings.New('random',dtype=bool, initial=False, ro= False)
        self.settings.New('audio_on',dtype=bool,initial = False,ro = False)
        self.settings.New('lick_training',dtype=bool,initial=False)
        '''
        setting up experimental setting parameters for task
        '''
        exp_settings = []
        
        
        exp_settings.append(self.settings.New('block', dtype = int, initial = 5))
        exp_settings.append(self.settings.New('delay', dtype = int, initial = 2000, vmin = 500))
        exp_settings.append(self.settings.New('go', dtype = int, initial = 2500)) 
        exp_settings.append(self.settings.New('refract', dtype = int, initial = 2500, vmin = 500)) 
        exp_settings.append(self.settings.New('punish', dtype = int, initial = 3000)) 
        
        
        exp_settings.append(self.settings.New('channel1', dtype = int, initial = 6)) 
        exp_settings.append(self.settings.New('channel2', dtype = int, initial = 6)) 
        exp_settings.append(self.settings.New('level1', dtype = int, initial = 100, vmin = 0, vmax = 100))
        exp_settings.append(self.settings.New('level2', dtype = int, initial = 100, vmin = 0, vmax = 100))
        exp_settings.append(self.settings.New('Tpulse1', dtype = int, initial = 50))
        exp_settings.append(self.settings.New('Tpulse2', dtype = int, initial = 50))
        exp_settings.append(self.settings.New('interval1', dtype = int, initial = 100))
        exp_settings.append(self.settings.New('interval2', dtype = int, initial = 1000))
        
        

        self.exp_settings = exp_settings
        '''
        Setting up lqs for recording stats
        '''
        self.stat_settings = []
        self.stat_settings.append(self.settings.New('trial', dtype = int, initial = 0, ro = True))
        self.stat_settings.append(self.settings.New('success', dtype = int, initial = 0, ro = True))
        self.stat_settings.append(self.settings.New('failure', dtype = int, initial = 0, ro = True))
        self.stat_settings.append(self.settings.New('early', dtype = int, initial = 0, ro = True))
        self.stat_settings.append(self.settings.New('idle', dtype = int, initial = 0, ro = True))
        self.stat_settings.append(self.settings.New('success_percent', dtype = int, initial = 0, ro = True))
        self.stat_settings.append(self.settings.New('failure_percent', dtype = int, initial = 0, ro = True))
        self.stat_settings.append(self.settings.New('early_percent', dtype = int, initial = 0, ro = True))
        self.stat_settings.append(self.settings.New('idle_percent', dtype = int, initial = 0, ro = True))

        
        '''
        Setting up lqs for indicator lights
        '''
        self.state_ind = []
        self.reward_ind = []
        self.lick_ind = []
        
        self.state_ind.append(self.settings.New('delay_ind', dtype=bool, initial=False, ro = True))
        self.state_ind.append(self.settings.New('go_ind', dtype=bool, initial=False, ro = True))
        self.state_ind.append(self.settings.New('refract_ind', dtype=bool, initial=False, ro = True))
        self.state_ind.append(self.settings.New('punish_ind', dtype=bool, initial=False, ro = True))
        
        self.reward_ind.append(self.settings.New('left_reward_ind', dtype=bool, initial=False, ro = True))
        self.reward_ind.append(self.settings.New('right_reward_ind', dtype=bool, initial=False, ro = True))
        
        self.lick_ind.append(self.settings.New('left_lick_ind', dtype=bool, initial=False, ro = True))
        self.lick_ind.append(self.settings.New('right_lick_ind', dtype=bool, initial=False, ro = True))
        
        self.all_ind = self.state_ind + self.reward_ind + self.lick_ind

        
        #self.settings.New('sampling_period', dtype=float, unit='s', initial=0.005)
        
        # Create empty numpy array to serve as a buffer for the acquired data
        #self.buffer = np.zeros(10000, dtype=float)
        
        # Define how often to update display during a run
        self.display_update_period = 0.04 
        '''
        add reference to hardware
        '''
        # Convenient reference to the hardware used in the measurement
        _timerself.daq_ai = self.app.hardware['daq_ai']
        self.arduino_sol = self.app.hardware['arduino_sol']
        self.water=self.app.hardware['arduino_water']
        self.camera=self.app.hardware['thorcam']
        self.sound=self.app.hardware['sound']
        self.odometer = self.app.hardware['arduino_odometer']
        self.motor = self.app.hardware['arduino_motor']

    def setup_figure(self):
        """
        Runs once during App initialization, after setup()
        This is the place to make all graphical interface initializations,
        build plots, etc.
        """
        
        # connect ui widgets to measurement/hardware settings or functions
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        self.settings.train.connect_to_widget(self.ui.train_checkBox)
        self.settings.save_h5.connect_to_widget(self.ui.save_h5_checkBox)
        self.settings.save_movie.connect_to_widget(self.ui.save_movie_checkBox)
        self.settings.random.connect_to_widget(self.ui.random_checkBox)
        for exp_setting in self.exp_settings:
            exp_widget_name=exp_setting.name+'_doubleSpinBox'
            #print(exp_widget_name)
            exp_widget=self.ui.findChild(QDoubleSpinBox,exp_widget_name)
            exp_setting.connect_to_widget(exp_widget)
            
        for stat_setting in self.stat_settings:
            stat_widget_name=stat_setting.name+'_doubleSpinBox'
            #print(exp_widget_name)
            stat_widget=self.ui.findChild(QDoubleSpinBox,stat_widget_name)
            stat_setting.connect_to_widget(stat_widget)
            
        for ind in self.all_ind:
            ind_widget_name=ind.name+'_checkBox'
            ind_widget=self.ui.findChild(QCheckBox,ind_widget_name)
            ind.connect_to_widget(ind_widget)
            
        '''
        Setting light icons and colors for indicators
        '''
        self.ui.delay_ind_checkBox.setStyleSheet(
            'QCheckBox{color:orange;}QCheckBox::indicator:checked{image: url(./icons/c_o.png);}QCheckBox::indicator:unchecked{image: url(./icons/uc_o.png);}')
        self.ui.go_ind_checkBox.setStyleSheet(
            'QCheckBox{color:green;}QCheckBox::indicator:checked{image: url(./icons/c_g.png);}QCheckBox::indicator:unchecked{image: url(./icons/uc_g.png);}')
        self.ui.refract_ind_checkBox.setStyleSheet(
            'QCheckBox{color:yellow;}QCheckBox::indicator:checked{image: url(./icons/c_y.png);}QCheckBox::indicator:unchecked{image: url(./icons/uc_y.png);}')
        self.ui.punish_ind_checkBox.setStyleSheet(
            'QCheckBox{color:red;}QCheckBox::indicator:checked{image: url(./icons/c_r.png);}QCheckBox::indicator:unchecked{image: url(./icons/uc_r.png);}')
        
        self.ui.right_lick_ind_checkBox.setStyleSheet(
            'QCheckBox{color:green;}QCheckBox::indicator:checked{image: url(./icons/c_g.png);}QCheckBox::indicator:unchecked{image: url(./icons/uc_g.png);}')
        self.ui.left_lick_ind_checkBox.setStyleSheet(
            'QCheckBox{color:yellow;}QCheckBox::indicator:checked{image: url(./icons/c_y.png);}QCheckBox::indicator:unchecked{image: url(./icons/uc_y.png);}')
        
        self.ui.right_reward_ind_checkBox.setStyleSheet(
            'QCheckBox{color:green;}QCheckBox::indicator:checked{image: url(./icons/c_g.png);}QCheckBox::indicator:unchecked{image: url(./icons/uc_g.png);}')
        self.ui.left_reward_ind_checkBox.setStyleSheet(
            'QCheckBox{color:yellow;}QCheckBox::indicator:checked{image: url(./icons/c_y.png);}QCheckBox::indicator:unchecked{image: url(./icons/uc_y.png);}')
        
        '''
        Set up pyqtgraph graph_layout in the UI
        '''
        
        self.graph_layout=pg.GraphicsLayoutWidget()
        self.ui.plot_groupBox.layout().addWidget(self.graph_layout)
        
        self.aux_graph_layout=pg.GraphicsLayoutWidget()
        self.ui.aux_plot_groupBox.layout().addWidget(self.aux_graph_layout)
        
        self.camera_layout=pg.GraphicsLayoutWidget()
        self.ui.camera_groupBox.layout().addWidget(self.camera_layout)
        
        self.position_layout=pg.GraphicsLayoutWidget()
        self.ui.position_plot_groupBox.layout().addWidget(self.position_layout)
        # Create PlotItem object (a set of axes)  
     
        '''
        add plot
        '''
        self.plot1 = self.graph_layout.addPlot(row=1,col=1,title="Lick")
        self.plot2 = self.graph_layout.addPlot(row=2,col=1,title="breathing")
        self.plot3 = self.graph_layout.addPlot(row=3,col=1,title="odor")

        # Create PlotDataItem object ( a scatter plot on the axes )
        self.breathing_plot = self.plot2.plot([0])
        self.lick_plot_0 = self.plot1.plot([0])
        self.lick_plot_1 = self.plot1.plot([1])
        self.odor_plot = []
        for i in range(8):
            self.odor_plot.append(self.plot3.plot([i]))

        
        self.lick_plot_0.setPen('y')
        self.lick_plot_1.setPen('g')
        
        self.odor_plot[0].setPen('b')

        self.odor_plot[4].setPen('b')
        
        self.T=np.linspace(0,10,10000)
        self.k=0
        
        self.plot4 = self.aux_graph_layout.addPlot(title = 'Statistics')
        self.stat_plot = []
        for i in range(6):
            self.stat_plot.append(self.plot4.plot([i]))
        self.stat_plot[0].setPen('g')
        self.stat_plot[1].setPen('r')
        self.stat_plot[2].setPen('m')
        self.stat_plot[3].setPen('y')
        self.stat_plot[4].setPen('w')
        self.stat_plot[5].setPen('b')
        
        self.camera_view=pg.ViewBox()
        self.camera_layout.addItem(self.camera_view)
        self.camera_image=pg.ImageItem()
        self.camera_view.addItem(self.camera_image)
        
        self.position_plot = self.position_layout.addPlot(title='Position')
        self.position_map = self.position_plot.plot([0])
        self.pos_x = np.zeros((100,))
        self.pos_y = np.zeros((100,))
        self.position_map.setData(self.pos_x,self.pos_y)
        
    def update_display(self):
        """
        Displays (plots) the numpy array self.buffer. 
        This function runs repeatedly and automatically during the measurement run.
        its update frequency is defined by self.display_update_period
        """
        self.lick_plot_0.setData(self.k+self.T,self.buffer[:,1]) 
        self.lick_plot_1.setData(self.k+self.T,self.buffer[:,2]) 
        self.breathing_plot.setData(self.k+self.T,self.buffer[:,0]) 
        
        for i in range(8):
            self.odor_plot[i].setData(self.k + self.T, self.buffer[:,i+6])
        
        for i in range(4):
            self.stat_plot[i].setData(self.stat[0,0:self.ntrials+1],self.stat[5+i,0:self.ntrials+1])
            
        self.stat_plot[4].setData(self.side_stat[0,0:self.ntrials+1],self.side_stat[7,0:self.ntrials+1])
        self.stat_plot[5].setData(self.side_stat[0,0:self.ntrials+1],self.side_stat[8,0:self.ntrials+1])
       
        '''
        update position
        '''
        self.pos_x[0:-1] = self.pos_x[1:]
        self.pos_y[0:-1] = self.pos_x[1:]
        self.pos_x[-1] = self.odometer.settings.x.value()
        self.pos_y[-1] = self.odometer.settings.y.value()
        self.position_map.setData(self.pos_x,self.pos_y)
        
        if self.settings.movie_on.value():
            self.camera_image.setImage(self.camera.read())
            if self.settings.save_movie.value():
                self.camera.write()
    
        #print(self.buffer_h5.size)
    
    def run(self):
        """
        Runs when measurement is started. Runs in a separate thread from GUI.
        It should not update the graphical interface directly, and should only
        focus on data acquisition.
        """
        '''
        disable controls
        '''
        self.settings.save_h5.change_readonly(True)
        self.settings.save_movie.change_readonly(True)
        self.settings.train.change_readonly(True)
        
        self.ui.save_h5_checkBox.setEnabled(False)
        self.ui.save_movie_checkBox.setEnabled(False)
        self.ui.train_checkBox.setEnabled(False)
        
            
        if self.camera.connected.value():
            self.settings.movie_on.update_value(True)
        
        self.ntrials = 1
        num_of_chan=self.daq_ai.settings.num_of_chan.value()
        self.buffer = np.zeros((10000,num_of_chan+12), dtype=float)
        self.stat = np.zeros((9,2000), dtype = float)
        self.side_stat = np.zeros((11,2000), dtype = float)
        statrec = StatRec()
        siderec = SideRec()
        '''
        initialize position
        '''
        position = 0

        
        '''
        Decide whether to create HDF5 file or not
        '''
        # first, create a data file
        if self.settings['save_h5']:
            # if enabled will create an HDF5 file with the plotted data
            # first we create an H5 file (by default autosaved to app.settings['save_dir']
            # This stores all the hardware and app meta-data in the H5 file
            file_name_index=0
            file_name=os.path.join(self.app.settings.save_dir.value(),self.app.settings.sample.value())+'_'+str(file_name_index)+'.h5'
            while os.path.exists(file_name):
                file_name_index+=1
                file_name=os.path.join(self.app.settings.save_dir.value(),self.app.settings.sample.value())+'_'+str(file_name_index)+'.h5'
            
            self.h5file = h5_io.h5_base_file(app=self.app, measurement=self,fname = file_name)
            
            # create a measurement H5 group (folder) within self.h5file
            # This stores all the measurement meta-data in this group
            self.h5_group = h5_io.h5_create_measurement_group(measurement=self, h5group=self.h5file)
        

            # create an h5 dataset to store the data
            self.buffer_h5 = self.h5_group.create_dataset(name  = 'buffer', 
                                                          shape = self.buffer.shape,
                                                          dtype = self.buffer.dtype,
                                                          maxshape=(None,self.buffer.shape[1]))
            
            self.stat_h5 = self.h5_group.create_dataset(name  = 'stat', 
                                                          shape = self.stat.shape,
                                                          dtype = self.stat.dtype)
            self.side_stat_h5 = self.h5_group.create_dataset(name  = 'side_stat', 
                                                          shape = self.side_stat.shape,
                                                          dtype = self.side_stat.dtype)
        
        if self.settings.save_movie.value():
            file_name_index=0
            file_name=os.path.join(self.app.settings.save_dir.value(),self.app.settings.sample.value())+'_'+str(file_name_index)+'.avi'
            while os.path.exists(file_name):
                file_name_index+=1
                file_name=os.path.join(self.app.settings.save_dir.value(),self.app.settings.sample.value())+'_'+str(file_name_index)+'.avi'
            self.camera.settings.file_name.update_value(file_name)
            self.camera.open_file()
        # We use a try/finally block, so that if anything goes wrong during a measurement,
        # the finally block can clean things up, e.g. close the data file object.
        '''
        create odor generator and task object
        '''
        if self.settings.train.value():
            odorgen = OdorGen(T = self.settings.delay.value())
            task = TrainingTask(audio_on = self.settings.audio_on.value(), water_hw = self.water, odor_gen = odorgen,
                                sound_hw = self.sound,
                                motor_hw = self.motor,
                                stat_rec = statrec,
                                side_rec = siderec,
                                random_lq = self.settings.random,
                                state_lqs = self.state_ind,
                                reward_lqs = self.reward_ind,
                                block = self.settings.block.value(),
                                delay = self.settings.delay.value(),
                                go = self.settings.go.value(),
                                refract = self.settings.refract.value(),
                                punish = self.settings.punish.value(),
                                lick_training = self.settings.lick_training.value())
            task.set_stimuli(side = 1,
                             channel = self.settings.channel1.value(),
                             level = self.settings.level1.value(),
                             Tpulse = self.settings.Tpulse1.value(),
                             interval = self.settings.interval1.value())
            task.set_stimuli(side = 2,
                             channel = self.settings.channel2.value(),
                             level = self.settings.level2.value(),
                             Tpulse = self.settings.Tpulse2.value(),
                             interval = self.settings.interval2.value())
        '''
        start actual protocol
        '''
        try:
            '''
            initialize counter ticks
            '''
            i = 0 #counter tick for loading buffer
            j = 0 #counter tick for saving hdf5 file
            self.k=0 #number of seconds saved
            
           
            '''
            Start DAQ, Default at 1kHz
            '''
            self.daq_ai.start()
            
            # Will run forever until interrupt is called.
            '''
            Expand HDF5 buffer when necessary
            '''
            while not self.interrupt_measurement_called:
                i %= self.buffer.shape[0]
                if self.settings['save_h5']:
                    if j>(self.buffer_h5.shape[0]-1):
                        self.buffer_h5.resize((self.buffer_h5.shape[0]+self.buffer.shape[0],self.buffer.shape[1]))
                        self.k +=10
                

                '''
                Update Progress Bar
                '''
                self.settings['progress'] = i * 100./self.buffer.shape[0]
                
                '''
                Read DAQ sensor data(0:lick_left, 1:lick_right, 2:flowmeter)
                '''
                # Fills the buffer with sine wave readings from func_gen Hardware
                self.buffer[i,0:num_of_chan] = self.daq_ai.read_data()

                lick_0 = (self.buffer[i,1]<4)
                lick_1 = (self.buffer[i,2]<4)
                self.buffer[i,1]=lick_0 #convert lick sensor into 0(no lick) and 1(lick)
                self.buffer[i,2]=lick_1
                
                self.lick_ind[0].update_value(lick_0)
                self.lick_ind[1].update_value(lick_1)
                
                '''
                get a readout for lick
                '''
                if (lick_0 and lick_1):
                    lick = 3
                elif lick_0:
                    lick = 1
                elif lick_1:
                    lick = 2
                else:
                    lick = 0
                
                '''
                step through task
                '''
                if self.settings.train.value():
                    task.step(lick)
                    odor, odor_disp = odorgen.step()
                    self.buffer[i,(num_of_chan+2):(num_of_chan + 10)] = odor_disp
                    self.arduino_sol.load(odor)
                else:
                    self.arduino_sol.load([100,0,0,0,0,0,0,0])

                '''
                Read and save Position and Speed at 25Hz(default) (3:position 4:speed)
                '''
                if i%20 == 0:
                    self.odometer.read()
                    self.buffer[j:(j+20),num_of_chan+10] = self.odometer.settings.x.value()
                    self.buffer[j:(j+20),num_of_chan + 11] = self.odometer.settings.y.value()
                '''
                Read odor value from the odor generator, otherwise fill with clean air(default)
                '''
                    
                '''
                write odor value to valve
                '''
                self.arduino_sol.write()
                '''
                write odor value to display (7:clean air 8:odor1 9:odor2 10:odor3)
                '''
                    #to be implemented
                    
               
                '''
                Save hdf5 file
                '''
                if self.settings['save_h5']:
                    # if we are saving data to disk, copy data to H5 dataset
                    self.buffer_h5[j,:] = self.buffer[i,:]
                    # flush H5
                    self.h5file.flush()
            
                
                # wait between readings.
                # We will use our sampling_period settings to define time
                #time.sleep(self.settings['sampling_period'])
                
                i += 1
                j += 1
               
                '''
                update_statistics
                '''
                if not statrec.updated():
                    self.stat[:], self.ntrials = statrec.write()
                    for counter in range(9):
                        self.stat_settings[counter].update_value(self.stat[counter,self.ntrials])
                    if self.settings['save_h5']:
                        self.stat_h5[:] = self.stat[:]
                        
                if not siderec.updated():
                    self.side_stat[:] = siderec.write()
                    if self.settings['save_h5']:
                        self.side_stat_h5[:] = self.side_stat[:]
                        
                if self.interrupt_measurement_called:
                    # Listen for interrupt_measurement_called flag.
                    # This is critical to do, if you don't the measurement will
                    # never stop.
                    # The interrupt button is a polite request to the 
                    # Measurement thread. We must periodically check for
                    # an interrupt request
                    self.daq_ai.stop()
                    break

        finally:            
            if self.settings['save_h5']:
                # make sure to close the data file
                self.h5file.close()
            
            if self.camera.connected.value():
                self.settings.movie_on.update_value(False)
                time.sleep(0.1)
                if self.settings.save_movie.value():
                    self.camera.close_file()     
                
            self.settings.save_h5.change_readonly(False)
            self.settings.save_movie.change_readonly(False)
            self.settings.train.change_readonly(False)
            
            self.ui.save_h5_checkBox.setEnabled(True)
            self.ui.save_movie_checkBox.setEnabled(True)
            self.ui.train_checkBox.setEnabled(True)           
            
class StatRec(object):
    '''
    Record mouse performance such as correct v.s. incorrect response
    '''
    
    def __init__(self):
        self.buffer = np.zeros((9,2000))
        self.state_dict = {'success': 1, 'failure':2, 'early':3, 'idle':4}
        self.trial = 0
        self.up_to_date = True
    
    def increment(self,state_name):
        '''
        Called by task object, called whenever mice make a decision
        '''
        state = self.state_dict[state_name]
        self.up_to_date =False
        self.trial += 1
        i = self.trial
        self.buffer[:,i] = self.buffer[:,i - 1]
        self.buffer[0,i] = self.trial
        self.buffer[state,i] += 1
        self.buffer[5:9, i] = 100.0 * self.buffer[1:5,i] / self.trial
        
    def write(self):
        '''
        output to a buffer
        '''
        self.up_to_date = True
        return self.buffer, self.trial
    
    def updated(self):
        return self.up_to_date
    
class SideRec(object):
    '''
    Record mouse performcance on each side
    '''
    
    def __init__(self):
        self.buffer = np.zeros((11,2000))
        self.trial = 0
        self.up_to_date = True
    
    def increment(self,state_name,side):
        '''
        Called by task object, called whenever mice make a decision
        0: total trials
        1: side 0 trials
        2: side 1 trials
        3: side 0 success
        4: side 1 success
        5: side 0 failure
        6: side 1 failure
        7: side 0 success percentage
        8: side 1 success percentage
        9: side 0 failure percentage
        10: side 1 failure percentage
        '''
        self.up_to_date =False
        self.trial += 1
        i = self.trial
        self.buffer[:,i] = self.buffer[:,i - 1]
        self.buffer[0,i] = self.trial
        
        if state_name == 'success':
            state = 3
        elif state_name == 'failure':
            state = 5
        else:
            return #no side picked
        
        self.buffer[1+side,i] += 1
        self.buffer[state+side,i] += 1
        
        if self.buffer[1,i]>0:
            self.buffer[7, i] = 100.0 * self.buffer[3,i] / self.buffer[1,i]
            self.buffer[9, i] = 100.0 * self.buffer[5,i] / self.buffer[1,i]
        if self.buffer[2,i]>0:
            self.buffer[8, i] = 100.0 * self.buffer[4,i] / self.buffer[2,i]
            self.buffer[10, i] = 100.0 * self.buffer[6,i] / self.buffer[2,i]
        
    def write(self):
        '''
        output to a buffer
        '''
        self.up_to_date = True
        return self.buffer
    
    def updated(self):
        '''
        check to see if the last output was up to date
        '''
        return self.up_to_date

class OdorGen(object):
    '''
    Object generate a time series of odor
    '''
    
    def __init__(self,nchan = 8, T = 3000):
        self.tick = 0 # millisecond time counter
        self.nchan = nchan #number of channels
        self.T = T # size of the output time series
        self.odor_buffer = np.zeros((self.nchan,self.T))
        self.odor_buffer_disp = np.zeros((self.nchan,self.T))
        self.on = False
    
    def step(self):
        '''
        output the next odor level in the time series
        '''
        default_output = np.zeros((self.nchan,))
        default_output[0] = 100
        if self.on:
            if self.tick < self.T -1:
                self.tick += 1 
                return self.odor_buffer[:,self.tick].squeeze(),self.odor_buffer_disp[:,self.tick].squeeze()
            else:
                self.on = False
                self.odor_buffer[:] = 0
                return default_output,default_output
        else:
            return default_output,default_output
            
    
    def new_trial(self, channel = 4, level = 30, Tpulse = 50, interval = 2000):
        '''
        generate new time series
        called from a task
        '''
        self.tick = 0 #reset tick
        '''
        Exponential Process Generation
        '''
        base_intervals = np.random.exponential(scale = interval, size = (50,)) #pulses are exponentially distributed
        base_onsets = base_intervals.cumsum().astype(int)
        
        '''
        Spike generation
        '''
        full_length = int(base_intervals.sum()+2000)
        spike_trace = np.zeros((full_length,))
        spike_trace[base_onsets] = 1
        spike_trace = spike_trace[0:self.T]
        '''
        Covolution with a kernel for valve control
        '''
        y = np.ones((Tpulse,)) * level
        output_trace_disp = np.convolve(spike_trace,y)[0:self.T] 
        y[0:3] = 100
        y[3:5] = 90
        y[5:10] = 80
        output_trace = np.convolve(spike_trace,y)[0:self.T]
        output_trace =output_trace.clip(0,100) #amke sure output is with in range
        '''
        output to both solenoid valve buffer and display
        '''
        clean_trace = 100 - output_trace_disp
        clean_trace = clean_trace.clip(0,100)
        self.odor_buffer[0,:] = clean_trace
        self.odor_buffer[channel,:] = output_trace
        self.odor_buffer_disp[channel,:] = output_trace_disp
        self.on = True
        
class TrainingTask(object):
    '''
    task object control the state of the task, and also generate each task
    '''
    
    def __init__(self, audio_on, water_hw, odor_gen, sound_hw, motor_hw, stat_rec, 
                 side_rec, random_lq, state_lqs, reward_lqs, block = 3, delay = 2000, go = 5000, refract = 2000, punish = 5000, lick_training = False):
        '''
        tick is for measuring time
        '''
        self.tick = 0
        '''
        the correct side
        '''
        self.side = 1
        self.trial = 0
        self.block = block
        
        self.audio_on = audio_on
        self.water = water_hw
        self.odor_gen = odor_gen
        self.sound = sound_hw
        self.motor = motor_hw
        self.stat_rec = stat_rec
        self.side_rec = side_rec
        self.random_lq = random_lq
        self.state_lqs = state_lqs
        self.reward_lqs = reward_lqs
        self.lick_training = lick_training
        
        self.water_available = False
        self.duration = [delay,go,refract,punish]
        self.channel = [0,0]
        self.level = [0,0]
        self.Tpulse = [100,100]
        self.interval = [500,500]
        
        self.state_dict = {'delay':0,'go':1,'refract':2,'punish':3}
        self.state = 2
    
    def step(self,lick = 0):
        self.tick += 1
        if self.state == self.state_dict['delay']:
            self.delay_step(lick)
        elif self.state == self.state_dict['go']:
            self.go_step(lick)
        elif self.state == self.state_dict['refract']:
            self.refract_step(lick)
        elif self.state == self.state_dict['punish']:
            self.punish_step(lick)
    
    def set_state(self,state_name):
        self.tick = 0
        self.state = self.state_dict[state_name]
        for state_lq in self.state_lqs:
            state_lq.update_value(False)
        self.state_lqs[self.state].update_value(True)
        '''
        if beginning a new trial, check to see if switching side is needed
        '''
        if self.state == self.state_dict['delay']:
            '''
            switch side for if the number of trials reach the block number
            '''
            if self.random_lq.value():
                self.side = np.random.randint(1,3)
            else:
                if self.trial >= self.block:
                    self.side = 3 - self.side
                    self.trial = 0
                
            side = self.side - 1
            for reward_lq in self.reward_lqs:
                reward_lq.update_value(False)
            self.reward_lqs[side].update_value(True)
            
            '''
            delivery odor if not in lick training, otherwise do not deliver
            '''
            if not self.lick_training:
                self.odor_gen.new_trial(self.channel[side],self.level[side],self.Tpulse[side],self.interval[side])
                
        
    def set_stimuli(self,side = 1, channel = 4, level = 30, Tpulse = 50, interval = 2000):
        side = side - 1
        self.channel[side] = channel
        self.level[side] = level
        self.Tpulse[side] = Tpulse
        self.interval[side] = interval
        
    def delay_step(self, lick = 0):
        if self.audio_on:
            if lick > 0:
                self.tick = 0
                self.stat_rec.increment('early')
                self.side_rec.increment('early',self.side - 1)
                self.sound.wrong()
                self.set_state('punish')
            else:
                pass
        
        my_state = self.state_dict['delay']
        if self.tick > self.duration[my_state]:
            self.tick = 0
            self.water_available = True
            if self.audio_on:
                self.sound.start()
            else:
                self.motor.settings.lick_position.update_value(True)
            self.set_state('go')
            
            
    def go_step(self,lick = 0): 
        
        if self.lick_training:
            if lick > 0 and lick<3:
                if self.water_available:
                    self.water.give_water(lick - 1)
                    self.water_available = False
                    if self.audio_on:
                        self.sound.correct()
                    self.stat_rec.increment('success')
                    self.side_rec.increment('success',self.side - 1)
                    self.set_state('refract')
        else:
            if lick == self.side:
                if self.water_available:
                    self.water.give_water(self.side - 1)
                    self.water_available = False
                    if self.audio_on:
                        self.sound.correct()
                    self.stat_rec.increment('success')
                    self.side_rec.increment('success',self.side - 1)
                    if not self.random_lq.value():
                        self.trial += 1
                    self.set_state('refract')
                    
            if lick > 0 and lick != self.side:
                if self.audio_on:
                    self.sound.wrong()
                else:
                    self.motor.settings.lick_position.update_value(False)
                self.set_state('punish')
                self.stat_rec.increment('failure')
                self.side_rec.increment('failure',self.side - 1)
                
        my_state = self.state_dict['go']
        if self.tick > self.duration[my_state]:
            self.set_state('refract')
            self.stat_rec.increment('idle')
            self.side_rec.increment('idle',self.side - 1)
            
    def refract_step(self, lick = 0):
        if self.lick_training:
            my_state = self.state_dict['refract']
            if self.tick > self.duration[my_state]:
                self.set_state('delay')
                if not self.audio_on:
                    self.motor.settings.lick_position.update_value(False)
        else:
            if lick == self.side:
                self.set_state('refract')
            
            if self.audio_on:
                if lick > 0 and lick != self.side:
                    self.sound.wrong()
                    self.set_state('punish')
                    
            my_state = self.state_dict['refract']
            if self.tick > self.duration[my_state]:
                self.set_state('delay')
                if not self.audio_on:
                    self.motor.settings.lick_position.update_value(False)
        
    def punish_step(self, lick = 0):
        if lick > 0:
            self.set_state('punish')
            
        my_state = self.state_dict['punish']
        if self.tick > self.duration[my_state]:
            self.set_state('delay')