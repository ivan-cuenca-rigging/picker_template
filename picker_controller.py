import os
import importlib
from maya import OpenMayaUI
from shiboken2 import wrapInstance
from PySide2 import QtCore, QtWidgets, QtUiTools, QtGui
from functools import partial
import picker_model
importlib.reload(picker_model)


# VARIABLES

window_name = 'Picker'

picker_folder = os.path.dirname(__file__)
ui_path_value = r'{}\picker_view.ui'.format(picker_folder)


class Picker(QtWidgets.QWidget):
    def __init__(self, ui_path, scale_factor, parent=None):
        super(Picker, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.Window)

        self.ui_path = ui_path
        self.width_default = 750
        self.height_default = 675

        # Load the UI from path
        self.ui_widget = self.loadUiWidget(ui_path_value, parent)

        self.load_images()

        # Drag and drop functionality
        self.tab_widget = self.findChild(QtWidgets.QTabWidget, 'tab_window')
        self.rubber_band = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)

        self.drag_selection = None
        self.origin = None
        self.source_geo = None
        self.alt_point = None
        self.delta = None
        self.widget_styles_dict = dict()
        for widget in self.ui_widget.findChildren(QtWidgets.QPushButton):
            if widget.objectName().endswith('_ctr'):
                widget_style = widget.styleSheet()
                self.widget_styles_dict[widget] = widget_style

        # Scale the whole window
        self.setMinimumSize(self.width_default * scale_factor, self.height_default * scale_factor)
        self.setMaximumSize(self.width_default * scale_factor, self.height_default * scale_factor)
        for child_widget in self.ui_widget.findChildren(QtWidgets.QWidget):
            child_widget.setGeometry(child_widget.x() * scale_factor, child_widget.y() * scale_factor,
                                     child_widget.width() * scale_factor, child_widget.height() * scale_factor)
        self.ui_widget.setFixedSize(self.ui_widget.size() * scale_factor)

        ###################
        # Connect buttons #
        ###################

        # Set namespace
        namespace_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'namespace_pushButton')[0]
        self.namespace_le = self.ui_widget.findChildren(QtWidgets.QLineEdit, 'namespace_lineEdit')[0]
        namespace_pb.clicked.connect(partial(picker_model.set_namespace, self.namespace_le))

        # Pose
        bind_pose_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'bindPose_pushButton')[0]
        bind_pose_pb.clicked.connect(partial(picker_model.bind_pose, self.namespace_le))

        flip_pose_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'flipPose_pushButton')[0]
        flip_pose_pb.clicked.connect(picker_model.flip_pose)

        bind_pose_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'mirrorPose_pushButton')[0]
        bind_pose_pb.clicked.connect(picker_model.mirror_pose)

        # Visibilities
        vis_controls_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'visControls_pushButton')[0]
        vis_controls_pb.clicked.connect(partial(picker_model.vis_controls, self.namespace_le))

        vis_geometries_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'visGeometries_pushButton')[0]
        vis_geometries_pb.clicked.connect(partial(picker_model.vis_geometries, self.namespace_le))

        # Selections
        select_all_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'selectAll_pushButton')[0]
        select_all_pb.clicked.connect(partial(picker_model.select_all_controls, self.namespace_le))

        select_body_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'selectBody_pushButton')[0]
        select_body_pb.clicked.connect(partial(picker_model.select_body_controls, self.namespace_le))

        select_face_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'selectFace_pushButton')[0]
        select_face_pb.clicked.connect(partial(picker_model.select_face_controls, self.namespace_le))

        # Keys
        key_all_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'keyAll_pushButton')[0]
        key_all_pb.clicked.connect(partial(picker_model.key_all_controls, self.namespace_le))

        key_body_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'keyBody_pushButton')[0]
        key_body_pb.clicked.connect(partial(picker_model.key_body_controls, self.namespace_le))

        key_face_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'keyFace_pushButton')[0]
        key_face_pb.clicked.connect(partial(picker_model.key_face_controls, self.namespace_le))

        # Controls
        for widget in self.ui_widget.findChildren(QtWidgets.QPushButton):
            if widget.objectName().endswith('_ctr'):
                widget.clicked.connect(partial(picker_model.select_control, widget.objectName(), self.namespace_le))
                widget.setToolTip(widget.objectName())

        # Snap
        arm_snap_l_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'armSnap_l_pushButton')[0]
        arm_snap_l_pb.clicked.connect(partial(picker_model.snap_fk_ik, 'arm', 'l', self.namespace_le))

        arm_snap_r_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'armSnap_r_pushButton')[0]
        arm_snap_r_pb.clicked.connect(partial(picker_model.snap_fk_ik, 'arm', 'r', self.namespace_le))

        leg_snap_l_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'legSnap_l_pushButton')[0]
        leg_snap_l_pb.clicked.connect(partial(picker_model.snap_fk_ik, 'leg', 'l', self.namespace_le))

        leg_snap_r_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'legSnap_r_pushButton')[0]
        leg_snap_r_pb.clicked.connect(partial(picker_model.snap_fk_ik, 'leg', 'r', self.namespace_le))

        # load the UI
        self.show()

    def loadUiWidget(self, ui_file_name, parent=None):
        loader = QtUiTools.QUiLoader()
        ui_file = QtCore.QFile(ui_file_name)
        ui_file.open(QtCore.QFile.ReadOnly)
        ui = loader.load(ui_file, parent)
        ui_file.close()

        ui.setParent(self)

        return ui

    def load_images(self):
        images_folder = r'{}/images'.format(os.path.dirname(self.ui_path))
        image_list = [f for f in os.listdir(images_folder) if f.endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        for i, image_file in enumerate(image_list):
            label_name = "{}_label".format(image_file.split('.')[0])
            label = self.ui_widget.findChild(QtWidgets.QLabel, label_name)
            if label:
                pixmap = QtGui.QPixmap(os.path.join(images_folder, image_file))
                label.setPixmap(pixmap)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.origin = event.pos()
            self.drag_selection = QtCore.QRect(self.origin, QtCore.QSize())
            self.rubber_band.setGeometry(self.drag_selection)
            self.rubber_band.show()

    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Alt:
            if self.delta is not None:
                self.origin += self.delta
                self.source_geo = None
                self.alt_point = None
                self.delta = None

    def mouseMoveEvent(self, event):
        if event.modifiers() == QtCore.Qt.AltModifier:
            if self.alt_point is None:
                self.source_geo = self.rubber_band.geometry()
                self.alt_point = event.pos()
            self.delta = event.pos() - self.alt_point
            new_geo = QtCore.QRect(self.source_geo)
            new_geo.moveTopLeft(self.source_geo.topLeft() + self.delta)
            self.rubber_band.setGeometry(new_geo)
        else:
            self.drag_selection = QtCore.QRect(self.origin, event.pos()).normalized()
            self.rubber_band.setGeometry(self.drag_selection)

        rubber_ban_pos = self.rubber_band.mapToGlobal(self.rubber_band.rect().topLeft())
        rubber_ban_rect = QtCore.QRect(rubber_ban_pos, self.rubber_band.rect().size())
        for widget, widget_style in self.widget_styles_dict.items():
            widget_pos = widget.mapToGlobal(widget.rect().topLeft())
            widget_rect = QtCore.QRect(widget_pos, widget.rect().size())
            if rubber_ban_rect.intersects(widget_rect):
                widget.setStyleSheet('color: black; background-color: white;')
            else:
                widget.setStyleSheet(widget_style)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.rubber_band.hide()
            tab_index = self.ui_widget.findChildren(QtWidgets.QTabWidget, 'picker_tab')[0].currentIndex()

            control_list = list()

            rubber_ban_pos = self.rubber_band.mapToGlobal(self.rubber_band.rect().topLeft())
            rubber_ban_rect = QtCore.QRect(rubber_ban_pos, self.rubber_band.rect().size())
            for widget, widget_style in self.widget_styles_dict.items():
                widget_pos = widget.mapToGlobal(widget.rect().topLeft())
                widget_rect = QtCore.QRect(widget_pos, widget.rect().size())
                if rubber_ban_rect.intersects(widget_rect):
                    parent_tab = widget
                    while parent_tab.objectName() != 'body_tab' and parent_tab.objectName() != 'face_tab':
                        parent_tab = parent_tab.parentWidget()
                    widget.setStyleSheet(widget_style)

                    if parent_tab.objectName() == 'body_tab' and tab_index == 0:
                        control_list.append(widget.objectName())
                    if parent_tab.objectName() == 'face_tab' and tab_index == 1:
                        control_list.append(widget.objectName())

            picker_model.select_control_list(control_list, self.namespace_le)


def openWindow(scale_factor):
    internal_window_name = 'pickerWindow'
    if QtWidgets.QApplication.instance():
        for win in (QtWidgets.QApplication.allWindows()):
            if internal_window_name in win.objectName():
                win.destroy()
    maya_main_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
    maya_main_window = wrapInstance(int(maya_main_window_ptr), QtWidgets.QWidget)
    Picker.window = Picker(ui_path=ui_path_value, scale_factor=scale_factor, parent=maya_main_window)
    Picker.window.setObjectName(internal_window_name)
    Picker.window.setWindowTitle(window_name)
    Picker.window.show()
