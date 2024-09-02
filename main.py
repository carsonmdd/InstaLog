import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import csv
import os, sys
import json
from datetime import datetime
import serial

def resource_path(relative_path):
    '''Get absolute path to resource, works for dev and for PyInstaller'''
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath('.')

    return os.path.join(base_path, relative_path)

class SpeciesCounterGUI:

    def __init__(self):
        self.ask_save_folder()
        self.csv_name = None
        self.load_settings()

        self.create_root()

        self.style = ttk.Style(self.root)

        self.load_theme()

        self.create_general_frame()

        self.create_widgets_frame()
        self.create_csv_tools()

        self.create_tree_frame()
        self.create_treeview()
        self.config_hotkeys()

        self.root.mainloop()

    #####################
    # INTERFACE METHODS #
    #####################

    def ask_save_folder(self):
        home_directory = os.path.expanduser('~')
        desktop_path = os.path.join(home_directory, 'Desktop')
        self.directory = filedialog.askdirectory(initialdir=desktop_path, title='Select a directory')
        if not self.directory:
            sys.exit()

    def load_settings(self):
        filepath = resource_path('settings.json')

        with open(filepath) as file:
            data = json.load(file)
            self.baud_rate = data['baud_rate']
            self.hotkeys = data['hotkeys']

    def create_root(self):
        self.root = tk.Tk()
        self.root.title('Species Counter')
        self.root.geometry('1250x500')
        self.make_grid_resizable(self.root, 1, 1)

        self.root.focus_set()

    def load_theme(self):
        self.root.tk.call('source', resource_path('themes/forest-light.tcl'))
        self.style.theme_use('forest-light')

    def create_general_frame(self):
        self.frame = ttk.Frame(self.root)
        self.frame.grid(row=0, column=0, sticky='nsew')
        self.make_grid_resizable(self.frame, 1, 2)

    def create_widgets_frame(self):
        self.widgets_frame = ttk.Frame(self.frame)
        self.widgets_frame.grid(row=0, column=0, padx=20, pady=10, sticky='nsew')
        self.make_grid_resizable(self.widgets_frame, 1, 1)

    def create_csv_tools(self):
        self.csv_frame = ttk.LabelFrame(self.widgets_frame, text='CSV Tools', labelanchor='n')
        self.csv_frame.grid(row=0, column=0, pady=(10, 200), sticky='nsew')
        self.make_grid_resizable(self.csv_frame, 1, 1)

        self.csv_widgets_frame = ttk.Frame(self.csv_frame)
        self.csv_widgets_frame.grid(row=0, column=0, sticky='nsew')
        self.make_grid_resizable(self.csv_widgets_frame, 4, 1)

        self.create_button = ttk.Button(self.csv_widgets_frame, text='New CSV', command=self.reset_treeview)
        self.create_button.grid(row=0, column=0, padx=15, pady=15, sticky='nsew')

        self.load_button = ttk.Button(self.csv_widgets_frame, text='Load CSV', command=self.load_csv)
        self.load_button.grid(row=1, column=0, padx=15, pady=(0, 15), sticky='nsew')

        self.csv_tools_separator = ttk.Separator(self.csv_widgets_frame)
        self.csv_tools_separator.grid(row=2, column=0, padx=15, pady=(0, 15), sticky='ew')

        self.delete_button = ttk.Button(self.csv_widgets_frame, text='Delete last row', command=self.delete_last_row)
        self.delete_button.grid(row=3, column=0, padx=15, pady=(0, 15), sticky='nsew')

    def create_tree_frame(self):
        self.tree_frame = ttk.Frame(self.frame)
        self.tree_frame.grid(row=0, column=1, padx=(0, 20), pady=10, sticky='nsew')
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(1, weight=0)
        self.tree_frame.grid_columnconfigure(1, weight=0)
    
    def create_treeview(self):
        self.col_widths = {
            'Species': 200,
            'Count': 100,
            'Timestamp': 250,
            'Latitude': 150,
            'Longitude': 150
        }
        self.tree = ttk.Treeview(self.tree_frame, show='headings', columns=list(self.col_widths.keys()), height=15)
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

    def make_grid_resizable(self, element, rows, cols):
        for i in range(rows):
            element.grid_rowconfigure(i, weight=1)
        for i in range(cols):
            element.grid_columnconfigure(i, weight=1)

    def reset_treeview(self):
        for heading, width in self.col_widths.items():
            self.tree.heading(heading, text=heading, anchor='w')
            self.tree.column(heading, width=width, anchor='w')

        for item in self.tree.get_children():
            self.tree.delete(item)

    def load_csv(self):
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
        if self.tree.get_children():
            last_item = self.tree.get_children()[-1]
            self.tree.delete(last_item)

            self.save()
    
    def save(self):
        if not self.csv_name:
            date = datetime.today().strftime('%d%b%Y')
            self.csv_name = f'{date}_obs.csv'

        csv_path = os.path.join(self.directory, self.csv_name)
        with open(csv_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(self.tree['columns'])
            for row in self.tree.get_children():
                writer.writerow(self.tree.item(row)['values'])

    def config_hotkeys(self):
        self.last_key = ''
        self.digits = ''

        for key in self.hotkeys.keys():
            self.root.bind(f'<KeyPress-{key}>', self.key_pressed)

        for i in range(10):
            self.root.bind(f'<KeyPress-{i}>', self.number_key_pressed)

        self.root.bind('<Return>', self.add_row)

    def key_pressed(self, event):
        self.last_key = event.char

    def number_key_pressed(self, event):
        if self.last_key and not (self.digits == '' and event.char == '0'):
            self.digits += event.char

    def add_row(self, event):
        if self.last_key and self.digits:
            species = self.hotkeys[self.last_key]
            count = self.digits
            time = datetime.now().time().replace(microsecond=0)
            # latitude, longitude = self.get_coords()
            latitude = '38.8951'
            longitude = '-77.0364'

            row = [species, count, time, latitude, longitude]
            self.tree.insert("", tk.END, values=row)

            self.last_key = ''
            self.digits = ''

            self.tree.yview_moveto(1.0)
            self.save()
        
    def get_coords(self):
        return

if __name__ == '__main__':
    SpeciesCounterGUI()