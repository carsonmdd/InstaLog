import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from .path_utils import internal_path
from .editable_treeview import EditableTreeview
from .action import Action
from .path_utils import new_path
from collections import deque
from datetime import datetime
import csv
import os

class GuiManager(tk.Tk):
    def __init__(self, shortcuts, callback, output_dir, init_port_thread):
        super().__init__()

        self.shortcuts = shortcuts
        self.callback = callback
        self.output_dir = output_dir
        self.init_port_thread = init_port_thread

        self.title('InstaLog')
        self.style = ttk.Style(self)
        self.make_grid_resizable(self, 1, 1)
        self.bind('<Map>', lambda event, w=self: self.center_window(w)) # Centering root immediately upon opening
        self.undo_stack = deque(maxlen=20)
        self.read_error_displayed = False
        self.obs_csv_path = None
        self.saved = False

        self.load_theme()
        self.create_general_frame()
        self.create_widgets_frame()
        self.create_csv_tools()
        self.create_entry_viewer()
        self.create_error_panel()
        self.create_tree_frame()
        self.create_treeview()

    def run(self):
        '''Runs the GUI'''
        self.withdraw() # Hide root while loading
        self.create_loading_screen()
        self.init_port_thread()

        self.mainloop()

    def center_window(self, window):
        '''Centers given window on screen (slightly higher than middle)'''
        window.update_idletasks() # Ensures window is fully loaded before getting its dimensions

        width = window.winfo_reqwidth()
        height = window.winfo_reqheight()
        x = int(window.winfo_screenwidth() * 0.5) - (width // 2)
        y = int(window.winfo_screenheight() * 0.4) - (height // 2)

        window.geometry(f'{width}x{height}+{x}+{y}')

        window.unbind('<Map>') # Ensures window only centers upon creation

    def has_read_error(self):
        '''Returns whether a read error is displayed'''
        return self.read_error_displayed
    
    def get_obs_csv_path(self):
        '''Returns path to CSV'''
        return self.obs_csv_path
    
    def create_loading_screen(self):
        '''Creates loading screen and its features'''
        self.loading_screen = tk.Toplevel()
        self.loading_screen.overrideredirect(True)
        self.loading_label = ttk.Label(self.loading_screen,
                                 text='Searching for GPS port...',
                                 font=('TkDefaultFont', 18, 'bold'), 
                                 anchor='center')
        self.loading_label.pack(padx=30, pady=30)
        self.loading_screen.resizable(False, False)

        # Centering loading screen immediately upon opening
        self.loading_screen.bind('<Map>', lambda event, w=self.loading_screen: self.center_window(w))
    
    def stop_loading(self, res):
        '''Destroys loading screen and processes result of finding gps port'''
        self.loading_screen.destroy()
        
        # If the result string isn't empty, there was an error
        if res:
            messagebox.showerror('Error', res)
            self.quit()
        # Else no error, so show the root
        else:
            self.deiconify()

    ##################
    # LAYOUT METHODS #
    ##################

    def load_theme(self):
        '''Loads and applies the theme for GUI appearance'''
        self.tk.call('source', internal_path('themes/forest-light.tcl'))
        self.style.theme_use('forest-light')

    def create_general_frame(self):
        '''Creates and configures general frame'''
        self.frame = ttk.Frame(self)
        self.frame.grid(row=0, column=0, sticky='nsew')
        self.make_grid_resizable(self.frame, 1, 2)

    def create_widgets_frame(self):
        '''Creates and configures frame for widgets'''
        self.widgets_frame = ttk.Frame(self.frame)
        self.widgets_frame.grid(row=0, column=0, padx=20, pady=10, sticky='nsew')
        self.make_grid_resizable(self.widgets_frame, 3, 1)

    def create_csv_tools(self):
        '''Creates CSV widgets'''
        self.csv_frame = ttk.LabelFrame(self.widgets_frame, text='CSV Tools', labelanchor='n')
        self.csv_frame.grid(row=0, column=0, pady=10, sticky='nsew')
        self.make_grid_resizable(self.csv_frame, 1, 1)

        self.csv_widgets_frame = ttk.Frame(self.csv_frame)
        self.csv_widgets_frame.grid(row=0, column=0, sticky='nsew')
        self.make_grid_resizable(self.csv_widgets_frame, 5, 1)

        self.create_button = ttk.Button(self.csv_widgets_frame, text='New CSV', command=self.new_csv)
        self.create_button.grid(row=0, column=0, padx=15, pady=15, sticky='nsew')

        self.load_button = ttk.Button(self.csv_widgets_frame, text='Load CSV', command=self.load_csv)
        self.load_button.grid(row=1, column=0, padx=15, pady=(0, 15), sticky='nsew')

        self.csv_tools_separator = ttk.Separator(self.csv_widgets_frame)
        self.csv_tools_separator.grid(row=2, column=0, padx=15, pady=(0, 15), sticky='ew')

        self.delete_button = ttk.Button(self.csv_widgets_frame, text='Delete last row', command=self.delete_last_row)
        self.delete_button.grid(row=3, column=0, padx=15, pady=(0, 15), sticky='nsew')

        self.undo_button = ttk.Button(self.csv_widgets_frame, text='Undo', command=self.undo)
        self.undo_button.grid(row=4, column=0, padx=15, pady=(0, 15), sticky='nsew')

    def create_entry_viewer(self):
        '''Creates entry viewer'''
        self.viewer_labelframe = ttk.LabelFrame(self.widgets_frame, text='Entry Viewer', labelanchor='n')
        self.viewer_labelframe.grid(row=1, column=0, pady=(0, 100), sticky='nsew')
        self.make_grid_resizable(self.viewer_labelframe, 1, 1)

        self.viewer_frame = ttk.Frame(self.viewer_labelframe)
        self.viewer_frame.grid(row=0, column=0, sticky='nsew')
        self.make_grid_resizable(self.viewer_frame, 1, 1)

        self.viewer = tk.Entry(self.viewer_frame, font=('TkDefaultFont', 16, 'bold'))
        self.viewer.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        self.viewer.bind('<Return>', self.on_return)
        self.viewer.focus_set() # Sets focus in entry when main GUI is opened

    def create_error_panel(self):
        '''Creates error panel'''
        self.error_labelframe = ttk.LabelFrame(self.widgets_frame, text='Error Log', labelanchor='n')
        self.error_labelframe.grid(row=2, column=0, pady=(0, 10), sticky='nsew')
        self.make_grid_resizable(self.error_labelframe, 1, 1)

        self.error_frame = ttk.Frame(self.error_labelframe)
        self.error_frame.grid(row=0, column=0, sticky='nsew')
        self.make_grid_resizable(self.error_frame, 1, 1)

        self.error_label = ttk.Label(self.error_frame,
                                     borderwidth=5,
                                     font=('TkDefaultFont', 16, 'bold'), 
                                     anchor='center')
        self.error_label.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

    def show_error(self, message):
        '''Displays an error in the error panel'''
        self.error_label.config(text=message, background='red')
        self.read_error_displayed = True

    def clear_errors(self):
        '''Clears the errors in the error panel'''
        self.error_label.config(text='', background='white')
        self.read_error_displayed = False

    def create_tree_frame(self):
        '''Creates and configures the treeview frame'''
        self.tree_frame = ttk.Frame(self.frame)
        self.tree_frame.grid(row=0, column=1, padx=(0, 20), pady=10, sticky='nsew')

        # Custom grid configs to account for scrollbars
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(1, weight=0)
    
    def create_treeview(self):
        '''Creates and configures the treeview for displaying the CSV'''
        self.col_widths = {
            'Species': 250,
            'Count': 75,
            'Time': 150,
            'Obs': 75,
            'Comment': 200,
            'Latitude': 150,
            'Longitude': 150
        }
        self.tree = EditableTreeview(self.tree_frame,
                                     self.save,
                                     show='headings',
                                     columns=list(self.col_widths.keys()),
                                     height=20)
        self.tree.grid(row=0, column=0, sticky='nsew')

        self.tree_yscroll = ttk.Scrollbar(self.tree_frame, orient='vertical', command=self.tree.yview)
        self.tree_yscroll.grid(row=0, column=1, sticky='ns')
    
        # Set scrollbar attributes for EditableTreeview class
        self.tree.y_scrollbar = self.tree_yscroll

        self.tree.configure(yscrollcommand=self.tree_yscroll.set)

        for heading, width in self.col_widths.items():
            self.tree.heading(heading, text=heading, anchor='w')
            self.tree.column(heading, width=width, anchor='w')

        self.reset_treeview()

    #####################
    # MECHANICS METHODS #
    #####################

    def make_grid_resizable(self, element, rows, cols):
        '''Makes a grid element's rows and columns resizable with equal weights'''
        for i in range(rows):
            element.grid_rowconfigure(i, weight=1)
        for i in range(cols):
            element.grid_columnconfigure(i, weight=1)

    def reset_treeview(self):
        '''Clears the entries in the current treeview'''
        for item in self.tree.get_children():
            self.tree.delete(item)

    def new_csv(self):
        '''
        - Saves all work before resetting
        - Resets treeview and relevant attributes
        '''
        # Want to save everything before making new CSV
        if self.obs_csv_path:
            self.save()
            self.callback('save work before new')

        self.reset_treeview()
        self.obs_csv_path = None
        self.saved = False
        data = {
            'status': False
        }
        self.callback('continue data', data)

    def load_csv(self):
        '''
        - Prompts the user to select a CSV file
        - If provided, fills the treeview with the entries from the CSV
        '''
        filepath = filedialog.askopenfilename(filetypes=[('CSV files', '*.csv')])
        if filepath:
            if not self.loaded_csv_valid(filepath):
                messagebox.showerror('Error', 'Invalid filename')
                return
            self.reset_treeview()
            with open(filepath) as file:
                csvFile = csv.reader(file)
                headers = next(csvFile)
                if headers != list(self.col_widths.keys()):
                    messagebox.showerror('Error', 'CSV headers do not match')
                    return
                else:
                    for row in csvFile:
                        self.tree.insert("", tk.END, values=row)

                self.obs_csv_path = filepath

                filename = os.path.basename(filepath)
                root, ext = os.path.splitext(filename)
                # Ex: root = 07Sep2024_obs
                # Ex: root = 07Sep2024_obs_1
                parts = root.split('_')
                date = parts[0]
                counter = '0' if len(parts) == 2 else parts[2]
                data = {
                    'status': True,
                    'date': date,
                    'counter': counter
                }
                self.save()
                self.callback('continue data', data)

    def loaded_csv_valid(self, filepath) -> bool:
        filename = os.path.basename(filepath)
        name, ext = os.path.splitext(filename)

        parts = name.split('_')
        if len(parts) == 2:
            if len(parts[0]) != 9 or parts[1] != 'obs':
                return False
        elif len(parts) == 3:
            if len(parts[0]) != 9 or parts[1] != 'obs' or not parts[2].isdigit():
                return False
        else:
            return False
        
        return True

    def delete_last_row(self):
        '''Deletes the contents of the last row in the treeview'''
        if self.tree.get_children():
            last_item = self.tree.get_children()[-1]
            data = self.tree.item(last_item).get('values')
            self.tree.delete(last_item)

            self.save()

            self.undo_stack.append(Action('delete row', self.undo_delete_last_row, data))

    def undo_delete_last_row(self, data):
        '''Inserts deleted data back into treeview without adding an Action to the undo stack'''
        self.tree.insert("", tk.END, values=data)
        self.tree.yview_moveto(1.0)
        self.save()

    def undo(self):
        '''Calls undo function for most recent Action'''
        if self.undo_stack:
            last_action = self.undo_stack.pop()
            last_action.undo()

    def on_return(self, event):
        '''Updates treeview with parsed entry text and clears entry'''
        text = self.viewer.get()
        self.species, self.count = self.parse_text(text)    
        self.add_row()
        self.viewer.delete(0, tk.END)

    def parse_text(self, text: str) -> tuple[str]:
        '''Parses text for entry cell and returns species name and count'''
        species, count = '', ''
        for i in range(len(text)):
            if text[i].isdigit():
                species = text[:i].strip()
                count = self.only_digits(text[i:])
                break
        
        # If text could not be broken up...
        if species == '':
            species = text.strip()
            count = '0'

        # .upper because all shortcuts are uppercase
        if species.upper() in self.shortcuts:
            species = self.shortcuts[species.upper()]

        return species, count

    def save(self):
        '''Writes the contents of the treeview to the obs csv'''
        # Creates a new CSV path if it does not exist
        if not self.obs_csv_path:
            date = datetime.today().strftime('%d%b%Y')
            csv_name = f'{date}_obs'
            self.obs_csv_path = os.path.join(self.output_dir, csv_name + '.csv')
            if os.path.exists(self.obs_csv_path):
                self.obs_csv_path = new_path(self.obs_csv_path)
        
        with open(self.obs_csv_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(self.tree['columns'])
            for child in self.tree.get_children():
                row = self.tree.item(child).get('values')
                writer.writerow(row)

        if not self.saved:
            # Tells other managers to create output if current doc has been saved
            self.callback('set create output', True)
            self.saved = True
    
    def only_digits(self, s):
        return ''.join([char for char in s if char.isdigit()])
    
    def add_row(self):
        '''Retrieves the necessary data, adds a row to the treeview, and updates the CSV'''
        species = self.species
        count = self.count
        time = datetime.now().time().replace(microsecond=0)
        obs = self.tree.num_observers
        comment = ''
        latitude, longitude = self.callback('get coords')

        row = [species, count, time, obs, comment, latitude, longitude]
        self.tree.insert("", tk.END, values=row)

        self.tree.yview_moveto(1.0) # Scrolls treeview down if necessary
        self.save()

        self.undo_stack.append(Action('add row', self.undo_add_row))

    def undo_add_row(self, data):
        '''Removes last row without adding an Action to the undo stack'''
        if self.tree.get_children():
            last_item = self.tree.get_children()[-1]
            self.tree.delete(last_item)

            self.save()