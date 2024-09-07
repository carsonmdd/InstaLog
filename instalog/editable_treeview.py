import tkinter as tk
from tkinter import ttk

class EditableTreeview(ttk.Treeview):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.entry = None
        self.num_observers = 2

        self.bind('<Double-1>', self.on_double_click)

    def on_double_click(self, event):
        '''Creates an entry if user clicked on a cell'''
        region = self.identify_region(event.x, event.y)
        if region != 'cell':
            return
        
        self.create_entry(event)
        
    def create_entry(self, event):
        '''Creates an entry for the user to edit a selected cell'''
        col_index = int(self.identify_column(event.x)[1:]) - 1
        selected_iid = self.focus()
        cell_box = self.bbox(selected_iid, col_index)

        selected_text = self.item(selected_iid).get('values')[col_index]
    
        self.entry = ttk.Entry(self)

        # Set these attributes for later use when "Enter" is pressed
        self.entry.selected_iid = selected_iid
        self.entry.col_index = col_index

        # Inserting original text from cell into entry
        self.entry.insert(0, selected_text)
        self.entry.select_range(0, tk.END)
        self.entry.focus()

        # "Return" updates the cell's text
        # Leaving the entry or scrolling destroys the entry
        self.entry.bind('<FocusOut>', self.destroy_entry)
        self.entry.bind('<Return>', self.on_enter)
        self.bind('<MouseWheel>', self.destroy_entry)
        self.bind('<Shift-MouseWheel>', self.destroy_entry)
        self.x_scrollbar.bind('<B1-Motion>', self.destroy_entry)
        self.y_scrollbar.bind('<B1-Motion>', self.destroy_entry)

        self.entry.place(x=cell_box[0],
                    y=cell_box[1],
                    w=cell_box[2],
                    h=cell_box[3])

    def destroy_entry(self, event):
        '''Destroys entry if it exists'''
        if self.entry.winfo_exists():
            self.entry.destroy()

    def on_enter(self, event):
        '''Updates corresponding treeview cell(s) with entry text'''
        new_text = self.entry.get()

        selected_iid = self.entry.selected_iid
        col_index = self.entry.col_index

        new_values = self.item(selected_iid).get('values')
        new_values[col_index] = new_text
        self.item(selected_iid, values=new_values)

        # If num of observers changed,
        #   updates all num of observers for every row below this row as well
        if col_index == 3:
            self.num_observers = new_text
            self.update_obs_below(selected_iid)

        self.entry.destroy()

    def update_obs_below(self, start_iid):
        '''Updates all rows below start_iid with start_iid's number of observers'''
        items = self.get_children()

        start_index = items.index(start_iid) + 1
        new_obs = self.item(start_iid).get('values')[3]
        for item in items[start_index:]:
            new_values = self.item(item).get('values')
            new_values[3] = new_obs
            self.item(item, values=new_values)