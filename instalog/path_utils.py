import os
import sys

def internal_path(relative_path):
    '''Gets path for resource bundled in app file'''
    # If running as exe,
    if getattr(sys, 'frozen', False):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    # else running as script
    else:
        base_path = os.path.abspath('.')

    return os.path.join(base_path, relative_path)

def external_path(relative_path):
    '''Gets path for resource in same directory as app file on macOS'''
    # If running as exe,
    if getattr(sys, 'frozen', False):
        exe_path = os.path.abspath(sys.executable)
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(exe_path))))
    # else running as script
    else:
        base_path = os.path.abspath('.')

    return os.path.join(base_path, relative_path)