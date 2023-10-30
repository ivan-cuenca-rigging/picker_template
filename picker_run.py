import sys
import importlib


picker_folder = r''
if picker_folder not in sys.path:
    sys.path.append(picker_folder)

import picker_controller
importlib.reload(picker_controller)


picker_controller.openWindow(scale_factor=1)
