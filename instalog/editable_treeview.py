import tkinter as tk
from tkinter import ttk

class EditableTreeview(ttk.Treeview):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.entry = None
        self.num_observers = 0

        self.bind('<Double-1>', self.on_double_click)

    def on_double_click(self, event):
        self.disable_root_binds()

        region = self.identify_region(event.x, event.y)
        if region != 'cell':
            return
        
        self.create_entry(event)
        
    def create_entry(self, event):
        col_index = int(self.identify_column(event.x)[1:]) - 1
        selected_iid = self.focus()
        cell_box = self.bbox(selected_iid, col_index)

        selected_text = self.item(selected_iid).get('values')[col_index]
    
        self.entry = ttk.Entry(self)

        self.entry.selected_iid = selected_iid
        self.entry.col_index = col_index

        self.entry.insert(0, selected_text)
        self.entry.select_range(0, tk.END)
        self.entry.focus()

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
        if self.entry.winfo_exists():
            self.entry.destroy()

    def disable_root_binds(self):
        root = self.master.master.master
        for seq in root.binds.keys():
            root.unbind(seq)

    def on_enter(self, event):
        new_text = self.entry.get()

        selected_iid = self.entry.selected_iid
        col_index = self.entry.col_index

        new_values = self.item(selected_iid).get('values')
        new_values[col_index] = new_text
        self.item(selected_iid, values=new_values)

        if col_index == 3:
            self.num_observers = new_text
            self.update_obs_below(selected_iid)

        self.entry.destroy()
        self.restore_root_binds()

    def update_obs_below(self, start_iid):
        items = self.get_children()

        start_index = items.index(start_iid) + 1
        new_obs = self.item(start_iid).get('values')[3]
        for item in items[start_index:]:
            new_values = self.item(item).get('values')
            new_values[3] = new_obs
            self.item(item, values=new_values)

    def restore_root_binds(self):
        root = self.master.master.master
        for seq, func in root.binds.items():
            root.bind(seq, func)