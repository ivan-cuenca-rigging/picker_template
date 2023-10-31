import sys
import importlib


picker_folder = r'C:\Users\IvanCuenca\Documents\Ivan\3D\projects\2023\hulk\picker'
if picker_folder not in sys.path:
    sys.path.append(picker_folder)

import picker
importlib.reload(picker)


picker_controller.openWindow(scale_factor=1)
