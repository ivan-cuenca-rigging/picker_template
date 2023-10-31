import os
import sys
import importlib
from maya import OpenMayaUI, cmds
from shiboken2 import wrapInstance
from PySide2 import QtCore, QtWidgets, QtUiTools, QtGui
from functools import partial


char_name = 'Hulk'


class Picker(QtWidgets.QWidget):
    def __init__(self, scale_factor):
        maya_main_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
        maya_main_window = wrapInstance(int(maya_main_window_ptr), QtWidgets.QWidget)
        super(Picker, self).__init__(maya_main_window)

        self.setWindowTitle('{} Picker'.format(char_name))
        self.setObjectName('{}PickerWindow'.format(char_name))
        self.ui_path_value = r'{}\picker.ui'.format(os.path.dirname(__file__))

        self.width_default = 750
        self.height_default = 675
        self.setWindowFlags(QtCore.Qt.Window)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Load the UI from path
        self.ui_widget = self.loadUiWidget(self.ui_path_value, maya_main_window)
        self.load_icon()
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
        # Pose
        bind_pose_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'bindPose_pushButton')[0]
        bind_pose_pb.clicked.connect(self.bind_pose)

        flip_pose_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'flipPose_pushButton')[0]
        flip_pose_pb.clicked.connect(self.flip_pose)

        mirror_pose_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'mirrorPose_pushButton')[0]
        mirror_pose_pb.clicked.connect(self.mirror_pose)

        # Visibilities
        vis_controls_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'visControls_pushButton')[0]
        vis_controls_pb.clicked.connect(self.vis_controls)

        vis_geometries_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'visGeometries_pushButton')[0]
        vis_geometries_pb.clicked.connect(self.vis_geometries)

        # Selections
        select_all_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'selectAll_pushButton')[0]
        select_all_pb.clicked.connect(self.select_all_controls)

        select_body_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'selectBody_pushButton')[0]
        select_body_pb.clicked.connect(self.select_body_controls)

        select_face_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'selectFace_pushButton')[0]
        select_face_pb.clicked.connect(self.select_face_controls)

        # Keys
        key_all_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'keyAll_pushButton')[0]
        key_all_pb.clicked.connect(self.key_all_controls)

        key_body_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'keyBody_pushButton')[0]
        key_body_pb.clicked.connect(self.key_body_controls)

        key_face_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'keyFace_pushButton')[0]
        key_face_pb.clicked.connect(self.key_face_controls)

        # Controls
        for widget in self.ui_widget.findChildren(QtWidgets.QPushButton):
            if widget.objectName().endswith('_ctr'):
                widget.clicked.connect(partial(self.select_control, widget.objectName()))
                widget.setToolTip(widget.objectName())

        # Snap
        arm_snap_l_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'armSnap_l_pushButton')[0]
        arm_snap_l_pb.clicked.connect(partial(self.snap_fk_ik, 'arm', 'l'))

        arm_snap_r_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'armSnap_r_pushButton')[0]
        arm_snap_r_pb.clicked.connect(partial(self.snap_fk_ik, 'arm', 'r'))

        leg_snap_l_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'legSnap_l_pushButton')[0]
        leg_snap_l_pb.clicked.connect(partial(self.snap_fk_ik, 'leg', 'l'))

        leg_snap_r_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'legSnap_r_pushButton')[0]
        leg_snap_r_pb.clicked.connect(partial(self.snap_fk_ik, 'leg', 'r'))
        
        # Set namespace
        namespace_pb = self.ui_widget.findChildren(QtWidgets.QPushButton, 'namespace_pushButton')[0]
        self.namespace_le = self.ui_widget.findChildren(QtWidgets.QLineEdit, 'namespace_lineEdit')[0]
        namespace_pb.clicked.connect(self.set_namespace)

    def loadUiWidget(self, ui_file_name, parent=None):
        loader = QtUiTools.QUiLoader()
        ui_file = QtCore.QFile(ui_file_name)
        ui_file.open(QtCore.QFile.ReadOnly)
        ui = loader.load(ui_file, parent)
        ui_file.close()

        ui.setParent(self)

        return ui

    def set_namespace(self):
        selection = cmds.ls(selection=True)
        namespace = None
        if len(selection) >= 1:
            selection = selection[0]
            if ':' in selection:
                namespace = '{}:'.format(':'.join(selection.split(':')[:-1]))
            else:
                namespace = ''
        else:
            namespace = ''

        self.namespace_le.setText(namespace)

    def get_namespace(self):
        return self.namespace_le.text()

    @staticmethod
    def get_modifier():
        """
        Get modifiers
        """
        mod = cmds.getModifiers()
        mod_value = None
        if (mod & 1) > 0:
            mod_value = 'shift'
        if (mod & 4) > 0:
            mod_value = 'control'
        if (mod & 8) > 0:
            mod_value = 'alt'
        return mod_value

    def bind_pose(self):
        """
        Set the rig to the bind/skin pose
        """
        cmds.undoInfo(openChunk=True)
        try:
            namespace = self.get_namespace()

            modules_grp = '{}modules_c_grp'.format(namespace)

            control_list = [x for x in cmds.listRelatives(modules_grp, allDescendents=True)
                            if x.endswith('_ctr')]

            skin_pose_attr = 'skinPoseData'

            for ctr in control_list:
                user_attrs = cmds.listAttr(ctr, userDefined=True)
                if user_attrs:
                    for user_attr in cmds.listAttr(ctr, userDefined=True):
                        try:
                            user_attr_dv = cmds.attributeQuery(user_attr, node=ctr, listDefault=True)[0]
                            cmds.setAttr('{}.{}'.format(ctr, user_attr), user_attr_dv)
                        except:
                            pass

                for attr in 'trs':
                    for axis in 'xyz':
                        attr_value = 1 if attr == 's' else 0
                        try:
                            cmds.setAttr('{}.{}{}'.format(ctr, attr, axis), attr_value)
                        except:
                            pass

                if cmds.attributeQuery(skin_pose_attr, node=ctr, exists=True):
                    skin_pose_data = cmds.getAttr('{}.{}'.format(ctr, skin_pose_attr))
                    skin_pose_data = skin_pose_data.split('[')[-1].split(']')[0].split(',')
                    skin_pose_data = [float(x) for x in skin_pose_data]

                    cmds.xform(ctr, objectSpace=True, matrix=skin_pose_data)
        finally:
            cmds.undoInfo(closeChunk=True)

    @staticmethod
    def flip_pose():
        """
        Flip the pose for the controls selected
        """
        cmds.undoInfo(openChunk=True)
        try:
            for ctr in cmds.ls(selection=True):
                side = '_{}_'.format(ctr.split('_')[-2])
                opposite_side = '_l_' if side == '_r_' else '_r_'
                if side == '_c_':
                    ctr_translate = cmds.xform(ctr, query=True, objectSpace=True, translation=True)
                    ctr_rotate = cmds.xform(ctr, query=True, objectSpace=True, rotation=True)

                    cmds.xform(ctr, objectSpace=True, rotation=(ctr_rotate[0], -ctr_rotate[1], -ctr_rotate[2]))
                    cmds.xform(ctr, objectSpace=True, translation=(-ctr_translate[0], ctr_translate[1], ctr_translate[2]))

                else:
                    ctr_xform = cmds.xform(ctr, query=True, objectSpace=True, matrix=True)
                    ctr_opposite_xform = cmds.xform(ctr.replace(side, opposite_side), query=True, objectSpace=True,
                                                    matrix=True)

                    cmds.xform(ctr.replace(side, opposite_side), objectSpace=True, matrix=ctr_xform)
                    cmds.xform(ctr, objectSpace=True, matrix=ctr_opposite_xform)

                user_attrs = cmds.listAttr(ctr, userDefined=True)
                if user_attrs:
                    for user_attr in cmds.listAttr(ctr, userDefined=True):
                        try:
                            attr_value = cmds.getAttr('{}.{}'.format(ctr, user_attr))
                            attr_opposite_value = cmds.getAttr(
                                '{}.{}'.format(ctr.replace(side, opposite_side), user_attr))

                            cmds.setAttr('{}.{}'.format(ctr.replace(side, opposite_side), user_attr), attr_value)
                            cmds.setAttr('{}.{}'.format(ctr, user_attr), attr_opposite_value)
                        except:
                            pass
        finally:
            cmds.undoInfo(closeChunk=True)

    @staticmethod
    def mirror_pose():
        """
        Mirror the pose for the controls selected
        """
        cmds.undoInfo(openChunk=True)
        try:
            for ctr in cmds.ls(selection=True):
                side = '_{}_'.format(ctr.split('_')[-2])
                opposite_side = '_l_' if side == '_r_' else '_r_'

                if side != '_c_':
                    ctr_xform = cmds.xform(ctr, query=True, objectSpace=True, matrix=True)
                    cmds.xform(ctr.replace(side, opposite_side), objectSpace=True, matrix=ctr_xform)

                    user_attrs = cmds.listAttr(ctr, userDefined=True)
                    if user_attrs:
                        for user_attr in cmds.listAttr(ctr, userDefined=True):
                            try:
                                attr_value = cmds.getAttr('{}.{}'.format(ctr, user_attr))
                                cmds.setAttr('{}.{}'.format(ctr.replace(side, opposite_side), user_attr), attr_value)
                            except:
                                pass
        finally:
            cmds.undoInfo(closeChunk=True)

    def snap_fk_ik(self, limb='arm', side='l'):
        """
        Snap fk ik
        :param limb: str , arm or leg
        :param side: str, "l" or "r"
        """
        cmds.undoInfo(openChunk=True)
        try:
            namespace = self.get_namespace()

            end_name = 'hand' if limb == 'arm' else 'foot'

            snap_info = {'start': {'fk_control': '{}up{}Fk_{}_ctr'.format(namespace, limb.capitalize(), side),
                                   'ik_control': None,
                                   'fk_snap': '{}up{}_{}_jnt'.format(namespace, limb.capitalize(), side),
                                   'ik_snap': None,
                                   'snap_xform': None
                                   },
                         'mid': {'fk_control': '{}low{}Fk_{}_ctr'.format(namespace, limb.capitalize(), side),
                                 'ik_control': '{}{}PoleVector_{}_ctr'.format(namespace, limb, side),
                                 'fk_snap': '{}low{}_{}_jnt'.format(namespace, limb.capitalize(), side),
                                 'ik_snap': '{}{}PoleVector_{}_snap'.format(namespace, limb, side),
                                 'snap_xform': None
                                 },
                         'end': {'fk_control': '{}{}{}Fk_{}_ctr'.format(namespace, end_name, limb.capitalize(), side),
                                 'ik_control': '{}{}{}Ik_{}_ctr'.format(namespace, end_name, limb.capitalize(), side),
                                 'fk_snap': '{}{}{}_{}_skn'.format(namespace, end_name, limb.capitalize(), side),
                                 'ik_snap': '{}{}{}_{}_skn'.format(namespace, end_name, limb.capitalize(), side),
                                 'snap_xform': None
                                 }
                         }

            settings_control = '{}{}Settings_{}_ctr'.format(namespace, limb, side)

            state = cmds.getAttr('{}{}.fkIk'.format(namespace, settings_control))  # 0 == Fk; 1 == Ik

            snap_value = 'ik_snap' if state == 0 else 'fk_snap'
            control_value = 'ik_control' if state == 0 else 'fk_control'

            for key, values in snap_info.items():
                if snap_info[key][control_value]:
                    snap_info[key]['snap_xform'] = cmds.xform(snap_info[key][snap_value],
                                                              query=True, worldSpace=True, matrix=True)

            new_state = 1 if state == 0 else 0
            cmds.setAttr('{}.fkIk'.format(settings_control), new_state)

            for key, values in snap_info.items():
                if snap_info[key][control_value]:
                    cmds.xform(snap_info[key][control_value], worldSpace=True, matrix=snap_info[key]['snap_xform'])
        finally:
            cmds.undoInfo(closeChunk=True)

    def select_control(self, control_name):
        """
        Select the control with the namespace given
        :param control_name: str
        """
        cmds.undoInfo(openChunk=True)
        try:
            namespace = self.get_namespace()

            control_name = '{}{}'.format(namespace, control_name)

            if self.get_modifier() == 'shift':
                cmds.select(control_name, add=True)
            elif self.get_modifier() == 'control':
                cmds.select(control_name, deselect=True)
            else:
                cmds.select(control_name)
        finally:
            cmds.undoInfo(closeChunk=True)
    def select_control_list(self, control_list):
        """
        Select the control with the namespace given
        :param control_list: list
        """
        cmds.undoInfo(openChunk=True)
        try:
            namespace = self.get_namespace()
            control_list = ['{}{}'.format(namespace, control_name) for control_name in control_list]

            if self.get_modifier() == 'shift':
                cmds.select(control_list, add=True)
            elif self.get_modifier() == 'control':
                cmds.select(control_list, deselect=True)
            else:
                cmds.select(control_list)
        finally:
            cmds.undoInfo(closeChunk=True)
    def select_all_controls(self):
        """
        Select all the controls in the scene with the namespace given
        """
        cmds.undoInfo(openChunk=True)
        try:
            namespace = self.get_namespace()
            modules_grp = '{}modules_c_grp'.format(namespace)

            cmds.select([x for x in cmds.listRelatives(modules_grp, allDescendents=True)
                         if x.endswith('_ctr')])
        finally:
            cmds.undoInfo(closeChunk=True)

    def select_body_controls(self):
        """
        Select body the controls in the scene with the namespace given
        """
        cmds.undoInfo(openChunk=True)
        try:
            namespace = self.get_namespace()

            modules_grp = '{}bodyModules_c_grp'.format(namespace)

            cmds.select([x for x in cmds.listRelatives(modules_grp, allDescendents=True)
                         if x.endswith('_ctr')])
        finally:
            cmds.undoInfo(closeChunk=True)

    def select_face_controls(self):
        """
        Select face the controls in the scene with the namespace given
        """
        cmds.undoInfo(openChunk=True)
        try:
            namespace = self.get_namespace()

            modules_grp = '{}faceModules_c_grp'.format(namespace)

            cmds.select([x for x in cmds.listRelatives(modules_grp, allDescendents=True)
                         if x.endswith('_ctr')])
        finally:
            cmds.undoInfo(closeChunk=True)

    def key_all_controls(self):
        """
        Key all the controls in the scene with the namespace given
        """
        cmds.undoInfo(openChunk=True)
        try:
            namespace = self.get_namespace()

            modules_grp = '{}modules_c_grp'.format(namespace)

            cmds.setKeyframe([x for x in cmds.listRelatives(modules_grp, allDescendents=True)
                              if x.endswith('_ctr')])
        finally:
            cmds.undoInfo(closeChunk=True)

    def key_body_controls(self):
        """
        Key body the controls in the scene with the namespace given
        """
        cmds.undoInfo(openChunk=True)
        try:
            namespace = self.get_namespace()

            modules_grp = '{}bodyModules_c_grp'.format(namespace)

            cmds.setKeyframe([x for x in cmds.listRelatives(modules_grp, allDescendents=True)
                              if x.endswith('_ctr')])
        finally:
            cmds.undoInfo(closeChunk=True)

    def key_face_controls(self):
        """
        Key face the controls in the scene with the namespace given
        """
        cmds.undoInfo(openChunk=True)
        try:
            namespace = self.get_namespace()

            modules_grp = '{}faceModules_c_grp'.format(namespace)

            cmds.setKeyframe([x for x in cmds.listRelatives(modules_grp, allDescendents=True)
                              if x.endswith('_ctr')])
        finally:
            cmds.undoInfo(closeChunk=True)

    def vis_controls(self):
        """
        switch on/off controls visibilities
        """
        cmds.undoInfo(openChunk=True)
        try:
            namespace = self.get_namespace()

            vis_controls_value = 0 if cmds.getAttr('{}general_c_ctr.visControls'.format(namespace)) else 1
            cmds.setAttr('{}general_c_ctr.visControls'.format(namespace), vis_controls_value)
        finally:
            cmds.undoInfo(closeChunk=True)

    def vis_geometries(self):
        """
        switch on/off controls visibilities
        """
        cmds.undoInfo(openChunk=True)
        try:
            namespace = self.get_namespace()

            vis_controls_value = 0 if cmds.getAttr('{}general_c_ctr.visGeometries'.format(namespace)) else 1
            cmds.setAttr('{}general_c_ctr.visGeometries'.format(namespace), vis_controls_value)
        finally:
            cmds.undoInfo(closeChunk=True)

    # Load images from the picker folder if not the backgrounds does not work
    def load_images(self):
        images_folder = r'{}/images'.format(os.path.dirname(__file__))
        image_list = [f for f in os.listdir(images_folder) if f.endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        for i, image_file in enumerate(image_list):
            label_name = "{}_label".format(image_file.split('.')[0])
            label = self.ui_widget.findChild(QtWidgets.QLabel, label_name)
            if label:
                pixmap = QtGui.QPixmap(os.path.join(images_folder, image_file))
                label.setPixmap(pixmap)

    def load_icon(self):
        icon_path = r'{}/images/hiddenStrings.png'.format(os.path.dirname(__file__))
        icon = QtGui.QIcon(icon_path)
        QtWidgets.QApplication.setWindowIcon(icon)
    
    # DRAG AND DROP METHODS
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

            self.select_control_list(control_list)


def openWindow(scale_factor):
    main_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
    maya_main_window = wrapInstance(int(main_window_ptr), QtWidgets.QWidget)
    all_maya_windows = maya_main_window.findChildren(QtWidgets.QWidget)

    picker_window = [x for x in all_maya_windows if
                     isinstance(x, QtWidgets.QWidget) and x.objectName() == '{}PickerWindow'.format(char_name)]
    if picker_window:
        picker_window[0].close()

    picker_window = Picker(scale_factor)
    picker_window.show()
