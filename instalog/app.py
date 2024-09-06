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

        self.gps = GpsManager(self.settings['baud_rate'],
                              self.gps_callback)
        self.shapefile_gen = ShapefileGenerator(self.output_dir,
                                                self.shapefile_gen_callback)
        self.gui = GuiManager(self.settings['shortcuts'],
                              self.gui_callback,
                              self.output_dir,
                              self.init_port_thread)
        
        self.gui.protocol('WM_DELETE_WINDOW', self.shapefile_gen.generate)

    def run(self):
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

        return data

    def init_port_thread(self):
        port_thread = threading.Thread(target=self.start_loading, daemon=True)
        port_thread.start()

    def start_loading(self):
        res = self.gps.find_gps_port()
        self.gui.stop_loading(res)

    def ask_save_folder(self):
        '''Prompts the user to select a directory for output files'''
        home_directory = os.path.expanduser('~')
        desktop_path = os.path.join(home_directory, 'Desktop')
        self.output_dir = filedialog.askdirectory(initialdir=desktop_path, title='Select a directory')
        if not self.output_dir:
            sys.exit()

    def gui_callback(self, req):
        if req == 'get coords':
            return self.gps.get_coords()
        else:
            return None
    
    def gps_callback(self, req):
        if req == 'clear errors':
            self.gui.clear_errors()
        elif req == 'has read error':
            self.gui.get_read_error_status()
        elif req == 'show read error':
            self.gui.show_error('Can\'t read from GPS')
        else:
            return None
        
    def shapefile_gen_callback(self, req):
        if req == 'get csv path':
            return self.gui.get_csv_path()
        elif req == 'get track df':
            return self.gps.get_track_df()
        elif req == 'destroy':
            self.gui.destroy()
        else:
            return None