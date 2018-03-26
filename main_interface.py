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

        #Add measurement components
        print("Create Measurement objects")

        # Connect to custom gui
        
        # load side panel UI
        
        # show ui
        self.ui.show()
        self.ui.activateWindow()
    

if __name__ == '__main__':
    import sys
    
    app = AntCamApp(sys.argv)
    sys.exit(app.exec_())