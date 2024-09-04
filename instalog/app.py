from .path_utils import internal_path, external_path
from .editable_treeview import EditableTreeview
from .action import Action

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import csv
import os, sys
import json

from datetime import datetime
import time

import serial
import serial.tools.list_ports
import threading

class InstaLogApp:

    def __init__(self):
        self.load_settings()
        self.get_gps_port()
        self.coords = (0.0, 0.0)
        self.read_error_displayed = False
        self.ask_save_folder()
        self.csv_name = None
        self.undo_stack = []

        self.create_root()
        self.style = ttk.Style(self.root)
        self.load_theme()

        self.create_general_frame()

        self.create_widgets_frame()
        self.create_csv_tools()
        self.create_error_panel()

        self.create_tree_frame()
        self.create_treeview()
        self.config_hotkeys()

        self.init_gps_thread()

    def run(self):
        self.root.mainloop()

    #####################
    # INTERFACE METHODS #
    #####################

    def create_root(self):
        '''Creates and configures the root'''
        self.root = tk.Tk()
        self.root.title('Species Counter')
        self.root.geometry('1250x500')
        self.root.binds = {}
        self.make_grid_resizable(self.root, 1, 1)

        self.root.focus_set()

    def load_theme(self):
        '''Loads and applies the theme for GUI appearance'''
        self.root.tk.call('source', internal_path('themes/forest-light.tcl'))
        self.style.theme_use('forest-light')

    def create_general_frame(self):
        '''Creates and configures general frame'''
        self.frame = ttk.Frame(self.root)
        self.frame.grid(row=0, column=0, sticky='nsew')
        self.make_grid_resizable(self.frame, 1, 2)

    def create_widgets_frame(self):
        '''Creates and configures frame for widgets'''
        self.widgets_frame = ttk.Frame(self.frame)
        self.widgets_frame.grid(row=0, column=0, padx=20, pady=10, sticky='nsew')
        self.make_grid_resizable(self.widgets_frame, 2, 1)

    def create_csv_tools(self):
        '''Creates CSV widgets'''
        self.csv_frame = ttk.LabelFrame(self.widgets_frame, text='CSV Tools', labelanchor='n')
        self.csv_frame.grid(row=0, column=0, pady=(10, 100), sticky='nsew')
        self.make_grid_resizable(self.csv_frame, 1, 1)

        self.csv_widgets_frame = ttk.Frame(self.csv_frame)
        self.csv_widgets_frame.grid(row=0, column=0, sticky='nsew')
        self.make_grid_resizable(self.csv_widgets_frame, 5, 1)

        self.create_button = ttk.Button(self.csv_widgets_frame, text='New CSV', command=self.reset_treeview)
        self.create_button.grid(row=0, column=0, padx=15, pady=15, sticky='nsew')

        self.load_button = ttk.Button(self.csv_widgets_frame, text='Load CSV', command=self.load_csv)
        self.load_button.grid(row=1, column=0, padx=15, pady=(0, 15), sticky='nsew')

        self.csv_tools_separator = ttk.Separator(self.csv_widgets_frame)
        self.csv_tools_separator.grid(row=2, column=0, padx=15, pady=(0, 15), sticky='ew')

        self.delete_button = ttk.Button(self.csv_widgets_frame, text='Delete last row', command=self.delete_last_row)
        self.delete_button.grid(row=3, column=0, padx=15, pady=(0, 15), sticky='nsew')

        self.undo_button = ttk.Button(self.csv_widgets_frame, text='Undo', command=self.undo)
        self.undo_button.grid(row=4, column=0, padx=15, pady=(0, 15), sticky='nsew')

    def create_error_panel(self):
        '''Creates error panel with "Clear" button'''
        self.error_labelframe = ttk.LabelFrame(self.widgets_frame, text='Error Log', labelanchor='n')
        self.error_labelframe.grid(row=1, column=0, pady=(0, 10), sticky='nsew')
        self.make_grid_resizable(self.error_labelframe, 1, 1)

        self.error_frame = ttk.Frame(self.error_labelframe)
        self.error_frame.grid(row=0, column=0, sticky='nsew')
        self.make_grid_resizable(self.error_frame, 1, 1)

        self.error_label = ttk.Label(self.error_frame,
                                     borderwidth=5,
                                     font=('TkDefaultFont', 16, 'bold'), 
                                     anchor='center')
        self.error_label.grid(row=0, column=0)

    def show_error(self, message):
        '''Displays an error in the error panel'''
        self.error_label.config(text=message, background='red')

    def clear_errors(self):
        '''Clears the errors in the error panel'''
        self.error_label.config(text='', background='white')
        self.read_error_displayed = False

    def create_tree_frame(self):
        '''Creates and configures the tree frame'''
        self.tree_frame = ttk.Frame(self.frame)
        self.tree_frame.grid(row=0, column=1, padx=(0, 20), pady=10, sticky='nsew')
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(1, weight=0)
        self.tree_frame.grid_columnconfigure(1, weight=0)
    
    def create_treeview(self):
        '''Creates and configures the treeview for displaying the CSV'''
        self.col_widths = {
            'Species': 200,
            'Count': 100,
            'Timestamp': 250,
            'Latitude': 150,
            'Longitude': 150
        }
        self.tree = EditableTreeview(self.tree_frame, show='headings', columns=list(self.col_widths.keys()), height=15)
        self.tree.grid(row=0, column=0, sticky='nsew')

        self.tree_xscroll = ttk.Scrollbar(self.tree_frame, orient='horizontal', command=self.tree.xview)
        self.tree_xscroll.grid(row=1, column=0, sticky='ew')
        self.tree_yscroll = ttk.Scrollbar(self.tree_frame, orient='vertical', command=self.tree.yview)
        self.tree_yscroll.grid(row=0, column=1, sticky='ns')

        self.tree.configure(xscrollcommand=self.tree_xscroll.set, yscrollcommand=self.tree_yscroll.set)

        self.reset_treeview()

    #####################
    # MECHANICS METHODS #
    #####################

    def ask_save_folder(self):
        '''Prompts the user to select a directory for output files'''
        home_directory = os.path.expanduser('~')
        desktop_path = os.path.join(home_directory, 'Desktop')
        self.directory = filedialog.askdirectory(initialdir=desktop_path, title='Select a directory')
        if not self.directory:
            sys.exit()

    def load_settings(self):
        '''Reads in settings from a file'''
        filepath = external_path('settings.json')

        try:
            with open(filepath) as file:
                data = json.load(file)
                self.baud_rate = data['baud_rate']
                self.hotkeys = data['hotkeys']
        except Exception as e:
            messagebox.showerror('Error', f'Error opening settings file: {e}')
            sys.exit()

    def get_gps_port(self):
        '''
        - Finds the GPS port by connecting to all ports and looking for specific
        NMEA sentences
        - Once valid sentences are found, collects the valid NMEA sentence types 
        and saves the port.
        '''
        self.sentence_types = [None, None, None]
        self.port = None

        ports = serial.tools.list_ports.comports()
        gps_sentences = ['$GPGGA', '$GPRMC', '$GPGLL']
        for port in ports:
            try:
                with serial.Serial(port.device, baudrate=self.baud_rate, timeout=1) as ser:
                    start_time = time.time()
                    while time.time() - start_time < 5:
                        data = ser.readline()
                        for i in range(len(gps_sentences)):
                            sentence_bytes = gps_sentences[i].encode('utf-8')
                            if sentence_bytes in data:
                                sentence_str = gps_sentences[i]
                                if sentence_str not in self.sentence_types:
                                    self.sentence_types[i] = sentence_str
                                    self.port = port.device
                        if self.sentence_types == gps_sentences:
                            return
            except Exception as e:
                messagebox.showerror('Error', f'Error accessing port {port.device}: {e}')
                sys.exit()

        if not self.port:
            messagebox.showerror('Error', f'Could not find a connected GPS')
            sys.exit()

    def init_gps_thread(self):
        '''Starts thread for consistenly reading coordinates in the background'''
        self.gps_thread = threading.Thread(target=self.read_coords)
        self.gps_thread.daemon = True
        self.gps_thread.start()

    def read_coords(self):
        '''Retrieves coordinates every 3 seconds'''
        while True:
            self.coords = self.get_coords()
            time.sleep(3)

    def make_grid_resizable(self, element, rows, cols):
        '''Makes an grid element's rows and columns resizable'''
        for i in range(rows):
            element.grid_rowconfigure(i, weight=1)
        for i in range(cols):
            element.grid_columnconfigure(i, weight=1)

    def reset_treeview(self):
        '''Clears the entries in the current treeview'''
        for heading, width in self.col_widths.items():
            self.tree.heading(heading, text=heading, anchor='w')
            self.tree.column(heading, width=width, anchor='w')

        for item in self.tree.get_children():
            self.tree.delete(item)

    def load_csv(self):
        '''
        - Prompts the user to select a CSV file
        - If provided, fills the treeview with the entries from the CSV
        '''
        self.reset_treeview()

        filepath = filedialog.askopenfilename(filetypes=[('CSV files', '*.csv')])
        if filepath:
            with open(filepath) as file:
                csvFile = csv.reader(file)
                headers = next(csvFile)
                if headers == list(self.col_widths.keys()):
                    for heading, width in self.col_widths.items():
                        self.tree.heading(heading, text=heading, anchor='w')
                        self.tree.column(heading, width=width, anchor='w')
                else:
                    self.tree['columns'] = headers
                    for header in headers:
                        self.tree.heading(header, text=header, anchor='w')
                        self.tree.column(header, width=200, anchor='w')

                for row in csvFile:
                    self.tree.insert("", tk.END, values=row)

        self.root.focus_set()
        
    def delete_last_row(self):
        '''Deletes the contents of the last row in the treeview'''
        if self.tree.get_children():
            last_item = self.tree.get_children()[-1]
            data = self.tree.item(last_item).get('values')
            self.tree.delete(last_item)

            self.save()

            self.undo_stack.append(Action('delete row', self.undo_delete_last_row, data))

    def undo_delete_last_row(self, data):
        self.tree.insert("", tk.END, values=data)
        self.tree.yview_moveto(1.0)
        self.save()

    def undo(self):
        if self.undo_stack:
            last_action = self.undo_stack.pop()
            last_action.undo()
    
    def save(self):
        '''Writes the contents of the treeview to the output csv'''
        if not self.csv_name:
            date = datetime.today().strftime('%d%b%Y')
            self.csv_name = f'{date}_obs.csv'

        csv_path = os.path.join(self.directory, self.csv_name)
        with open(csv_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(self.tree['columns'])
            for row in self.tree.get_children():
                writer.writerow(self.tree.item(row).get('values'))

    def config_hotkeys(self):
        '''Creates the keybinds for the provided keys'''
        self.last_key = ''
        self.digits = ''

        for key in self.hotkeys.keys():
            seq = f'<KeyPress-{key}>'
            self.root.bind(seq, self.key_pressed)
            self.root.binds[seq] = self.key_pressed

        for i in range(10):
            seq = f'<KeyPress-{i}>'
            self.root.bind(seq, self.number_key_pressed)
            self.root.binds[seq] = self.number_key_pressed

        self.root.bind('<Return>', self.add_row)
        self.root.binds['<Return>'] = self.add_row

    def key_pressed(self, event):
        '''Updates the last key pressed when a hotkey letter is pressed'''
        self.last_key = event.char

    def number_key_pressed(self, event):
        '''
        Appends the number pressed to the recorded digits and
        prevents leading zeros from being appended
        '''
        if self.last_key and not (self.digits == '' and event.char == '0'):
            self.digits += event.char

    def add_row(self, event):
        '''Retrieves the necessary data, adds a row to the treeview, and updates the CSV'''
        if self.last_key and self.digits:
            species = self.hotkeys[self.last_key]
            count = self.digits
            time = datetime.now().time().replace(microsecond=0)
            latitude, longitude = self.coords

            row = [species, count, time, latitude, longitude]
            self.tree.insert("", tk.END, values=row)

            self.last_key = ''
            self.digits = ''

            self.tree.yview_moveto(1.0)
            self.save()

            self.undo_stack.append(Action('add row', self.undo_add_row))

    def undo_add_row(self, data):
        if self.tree.get_children():
            last_item = self.tree.get_children()[-1]
            self.tree.delete(last_item)

            self.save()
        
    def get_coords(self) -> tuple[float]:
        '''
        - Attempts to read and return coordinates from the GPS
        - Upon failure, displays an error message in the GUI and returns
        the last recorded coordinates instead
        '''
        lat, lon = 0.0, 0.0

        start_time = time.time()
        with serial.Serial(port=self.port, baudrate=self.baud_rate, timeout=1) as ser:
            # Read for right sentence with valid data for 5 seconds
            while time.time() - start_time < 5:
                num_types = sum(element != None for element in self.sentence_types)
                line = ser.readline().decode('utf-8', errors='replace')
                if line.startswith(self.sentence_types[0]):
                    # $GPGGA,123519.00,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47
                    parts = line.split(',')
                    if parts[6] == '1' or parts[6] == '2':
                        lat, lon = self.ddm2dd(((parts[2], parts[3]), (parts[4], parts[5])))
                        self.coords = lat, lon
                        self.clear_errors()
                    break
                elif num_types >= 2 and line.startswith(self.sentence_types[1]):
                    # $GPRMC,123519.00,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A
                    parts = line.split(',')
                    if parts[2] == 'A':
                        lat, lon = self.ddm2dd(((parts[3], parts[4]), (parts[5], parts[6])))
                        self.coords = lat, lon
                        self.clear_errors()
                    break
                elif num_types == 3 and line.startswith(self.sentence_types[2]):
                    # $GPGLL,3519.2341,N,12050.9613,W,013604,A,A*54
                    parts = line.split(',')
                    if parts[6] == 'A':
                        lat, lon = self.ddm2dd(((parts[1], parts[2]), (parts[3], parts[4])))
                        self.coords = lat, lon
                        self.clear_errors()
                    break

        if (lat, lon) == (0.0, 0.0) and not self.read_error_displayed:
            self.show_error('Can\'t read from GPS')
            self.read_error_displayed = True

        return self.coords

    def ddm2dd(self, coordinates: tuple[tuple[str]]) -> tuple[float]:
        '''
        - Converts coordinates from degrees and decimal minutes to decimal degrees
        - Example input: (('3519.2344', 'N'), ('12059.9621', 'W'))
        '''
        ddm_lat, ddm_lon = coordinates
        lat_degrees = float(ddm_lat[0][:2])
        lat_mins = float(ddm_lat[0][2:])
        lon_degrees = float(ddm_lon[0][:3])
        lon_mins = float(ddm_lon[0][3:])

        lat = lat_degrees + (lat_mins / 60)
        lon = lon_degrees + (lon_mins / 60)

        lat = lat if ddm_lat[1] == 'N' else -lat
        lon = lon if ddm_lon[1] == 'E' else -lon

        return round(lat, 6), round(lon, 6)