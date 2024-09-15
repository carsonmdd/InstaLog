from .path_utils import external_path
from tkinter import filedialog, messagebox
import os, sys
import json
import threading

from .shapefile_gen import ShapefileGenerator
from .gps_manager import GpsManager
from .gui_manager import GuiManager

class InstaLogApp:
    def __init__(self):
        self.settings = self.load_settings()
        self.ask_save_folder()

        self.gps = GpsManager(self.settings.get('baud_rate'),
                              self.gps_callback,
                              self.output_dir)
        self.shapefile_gen = ShapefileGenerator(self.output_dir,
                                                self.shapefile_gen_callback)
        self.gui = GuiManager(self.settings.get('shortcuts'),
                              self.gui_callback,
                              self.output_dir,
                              self.init_port_thread)

        self.gui.protocol('WM_DELETE_WINDOW', lambda: (self.shapefile_gen.generate(), self.gui.destroy()))
                                                                                              
    def run(self):
        '''Run application'''
        self.gui.run()

    def load_settings(self):
        '''Reads in settings from a file'''
        data = {}
        filepath = external_path('settings.json')
        try:
            with open(filepath) as file:
                data = json.load(file)
        except Exception as e:
            messagebox.showerror('Error', f'Error opening settings file: {e}')
            sys.exit()

        if not data.get('baud_rate'):
            messagebox.showerror('Error', 'No baud_rate found in settings')
            sys.exit()
        elif not data.get('shortcuts'):
            messagebox.showerror('Error', 'No shortcuts found in settings')
            sys.exit()
        else:
            return data

    def init_port_thread(self):
        '''Initialize thread to find gps port in the background'''
        # daemon=True ensures thread terminates when mainloop terminates
        port_thread = threading.Thread(target=self.load, daemon=True)
        port_thread.start()

    def load(self):
        '''Starts searching for gps and stops loading when finished'''
        res = self.gps.find_gps_port()
        self.gui.stop_loading(res)

    def ask_save_folder(self):
        '''Prompts the user to select a directory for output files'''
        home_directory = os.path.expanduser('~')
        desktop_path = os.path.join(home_directory, 'Desktop')
        self.output_dir = filedialog.askdirectory(initialdir=desktop_path, title='Select a directory')
        if not self.output_dir:
            sys.exit()

    def gui_callback(self, req, data=None):
        '''Callback function for GUI manager requests'''
        if req == 'get coords':
            return self.gps.get_coords()
        elif req == 'set create output':
            # Note we only need to tell gps because shapefile_gen will get a
            # value that is not "None" when requesting the obs csv path
            self.gps.set_create_output(True)
        elif req == 'continue data':
            # Tell other managers whether we're continuing old project based on data['status']
            self.gps.continue_data(data)
            self.shapefile_gen.continue_data(data)
        elif req == 'save work before new':
            self.gps.save()
            self.shapefile_gen.generate()
        elif req == 'set coords':
            self.gps.set_coords(data['coords'])
        else:
            return None
    
    def gps_callback(self, req):
        '''Callback function for GPS manager requests'''
        if req == 'clear errors':
            self.gui.clear_errors()
        elif req == 'has read error':
            return self.gui.has_read_error()
        elif req == 'show read error':
            self.gui.show_error('Can\'t read from GPS')
        else:
            return None
        
    def shapefile_gen_callback(self, req):
        '''Callback function for shapefile generator requests'''
        if req == 'get obs csv path':
            return self.gui.get_obs_csv_path()
        elif req == 'get track df':
            return self.gps.get_track_df()
        else:
            return None