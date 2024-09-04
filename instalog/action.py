class Action:
    def __init__(self, type, undo_function, data=None):
        self.type = type
        self.undo_function = undo_function
        self.data = data
    
    def undo(self):
        self.undo_function(self.data)