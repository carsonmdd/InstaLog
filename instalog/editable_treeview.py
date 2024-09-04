import tkinter as tk
from tkinter import ttk

class EditableTreeview(ttk.Treeview):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.entry = None

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

        self.entry.bind('<FocusOut>', self.on_focus_out)
        self.entry.bind('<Return>', self.on_enter)
        self.bind('<MouseWheel>', self.on_scroll)
        self.bind('<Shift-MouseWheel>', self.on_scroll)
        self.x_scrollbar.bind('<B1-Motion>', self.on_scroll)
        self.y_scrollbar.bind('<B1-Motion>', self.on_scroll)

        self.entry.place(x=cell_box[0],
                    y=cell_box[1],
                    w=cell_box[2],
                    h=cell_box[3])

    def on_scroll(self, event):
        if self.entry.winfo_exists():
            self.entry.destroy()

    def disable_root_binds(self):
        root = self.master.master.master
        for seq in root.binds.keys():
            root.unbind(seq)

    def on_focus_out(self, event):
        event.widget.destroy()

    def on_enter(self, event):
        new_text = event.widget.get()

        selected_iid = event.widget.selected_iid
        col_index = event.widget.col_index

        new_values = self.item(selected_iid).get('values')
        new_values[col_index] = new_text
        self.item(selected_iid, values=new_values)

        event.widget.destroy()
        self.restore_root_binds()

    def restore_root_binds(self):
        root = self.master.master.master
        for seq, func in root.binds.items():
            root.bind(seq, func)