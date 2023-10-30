from maya import cmds
from PySide2.QtWidgets import QLineEdit


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


def set_namespace(line_edit):
    """
    Get and set the namespace of the node selected
    """
    selection = cmds.ls(selection=True)
    namespace = None
    if len(selection) >= 1:
        selection = selection[0]
        if ':' in selection:
            namespace = '{}:'.format(':'.join(selection.split(':')[:-1]))

    line_edit.setText(namespace)


def bind_pose(namespace_le=None):
    """
    Set the rig to the bind/skin pose
    :param namespace_le: QLineEdit
    """

    modules_grp = 'modules_c_grp'

    control_list = list()
    if namespace_le:
        namespace = namespace_le.text()
        if namespace:
            control_list = [x for x in cmds.listRelatives('{}modules_grp'.format(namespace), allDescendents=True)
                            if x.endswith('_ctr')]
        else:
            control_list = [x for x in cmds.listRelatives(modules_grp, allDescendents=True) if x.endswith('_ctr')]

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


def flip_pose():
    """
    Flip the pose for the controls selected
    """
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
            ctr_opposite_xform = cmds.xform(ctr.replace(side, opposite_side), query=True, objectSpace=True, matrix=True)

            cmds.xform(ctr.replace(side, opposite_side), objectSpace=True, matrix=ctr_xform)
            cmds.xform(ctr, objectSpace=True, matrix=ctr_opposite_xform)

            user_attrs = cmds.listAttr(ctr, userDefined=True)
            if user_attrs:
                for user_attr in cmds.listAttr(ctr, userDefined=True):
                    try:
                        attr_value = cmds.getAttr('{}.{}'.format(ctr, user_attr))
                        attr_opposite_value = cmds.getAttr('{}.{}'.format(ctr.replace(side, opposite_side), user_attr))

                        cmds.setAttr('{}.{}'.format(ctr.replace(side, opposite_side), user_attr), attr_value)
                        cmds.setAttr('{}.{}'.format(ctr, user_attr), attr_opposite_value)
                    except:
                        pass


def mirror_pose():
    """
    Mirror the pose for the controls selected
    """
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


def snap_fk_ik(limb='arm', side='l', namespace_le=None):
    """
    Snap fk ik
    :param limb: str , arm or leg
    :param side: str, "l" or "r"
    :param namespace_le: QLineEdit
    """
    end_name = 'hand' if limb == 'arm' else 'foot'
    snap_info = {'start': {'fk_control': 'up{}Fk_{}_ctr'.format(limb.capitalize(), side),
                           'ik_control': None,
                           'fk_snap': 'up{}_{}_jnt'.format(limb.capitalize(), side),
                           'ik_snap': None,
                           'snap_xform': None
                           },
                 'mid': {'fk_control': 'low{}Fk_{}_ctr'.format(limb.capitalize(), side),
                         'ik_control': '{}PoleVector_{}_ctr'.format(limb, side),
                         'fk_snap': 'low{}_{}_jnt'.format(limb.capitalize(), side),
                         'ik_snap': '{}PoleVector_{}_snap'.format(limb, side),
                         'snap_xform': None
                         },
                 'end': {'fk_control': '{}{}Fk_{}_ctr'.format(end_name, limb.capitalize(), side),
                         'ik_control': '{}{}Ik_{}_ctr'.format(end_name, limb.capitalize(), side),
                         'fk_snap': '{}{}_{}_skn'.format(end_name, limb.capitalize(), side),
                         'ik_snap': '{}{}_{}_skn'.format(end_name, limb.capitalize(), side),
                         'snap_xform': None
                         }
                 }

    settings_control = '{}Settings_{}_ctr'.format(limb, side)

    if namespace_le:
        namespace = namespace_le.text()
        if namespace:
            settings_control = '{}{}'.format(namespace, settings_control)
            for key, values in snap_info.items():
                for sub_key, sub_value in values.items():
                    if snap_info[key][sub_key] is not None:
                        snap_info[key][sub_key] = '{}{}'.format(namespace, snap_info[key][sub_key])

    state = cmds.getAttr('{}.fkIk'.format(settings_control))  # 0 == Fk; 1 == Ik

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


def select_control(control_name, namespace_le=None):
    """
    Select the control with the namespace given
    :param control_name: str
    :param namespace_le: QLineEdit
    """
    if namespace_le:
        namespace = namespace_le.text()
        if namespace:
            control_name = '{}{}'.format(namespace, control_name)

    if get_modifier() == 'shift':
        cmds.select(control_name, add=True)
    elif get_modifier() == 'control':
        cmds.select(control_name, deselect=True)
    else:
        cmds.select(control_name)


def select_control_list(control_list, namespace_le=None):
    """
    Select the control with the namespace given
    :param control_list: list
    :param namespace_le: QLineEdit
    """
    if namespace_le:
        namespace = namespace_le.text()
        if namespace:
            control_list = ['{}{}'.format(namespace, control_name) for control_name in control_list]

    if get_modifier() == 'shift':
        cmds.select(control_list, add=True)
    elif get_modifier() == 'control':
        cmds.select(control_list, deselect=True)
    else:
        cmds.select(control_list)


def select_all_controls(namespace_le=None):
    """
    Select all the controls in the scene with the namespace given
    :param namespace_le: QLineEdit
    """
    modules_grp = 'modules_c_grp'

    if namespace_le:
        namespace = namespace_le.text()
        if namespace:
            cmds.select([x for x in cmds.listRelatives('{}{}'.format(namespace, modules_grp), allDescendents=True)
                         if x.endswith('_ctr')])
        else:
            cmds.select([x for x in cmds.listRelatives(modules_grp, allDescendents=True) if x.endswith('_ctr')])


def select_body_controls(namespace_le=None):
    """
    Select body the controls in the scene with the namespace given
    :param namespace_le: QLineEdit
    """
    modules_grp = 'bodyModules_c_grp'

    if namespace_le:
        namespace = namespace_le.text()
        if namespace:
            cmds.select([x for x in cmds.listRelatives('{}{}'.format(namespace, modules_grp), allDescendents=True)
                         if x.endswith('_ctr')])
        else:
            cmds.select([x for x in cmds.listRelatives(modules_grp, allDescendents=True) if x.endswith('_ctr')])


def select_face_controls(namespace_le=None):
    """
    Select face the controls in the scene with the namespace given
    :param namespace_le: QLineEdit
    """
    modules_grp = 'faceModules_c_grp'
    if namespace_le:
        namespace = namespace_le.text()
        if namespace:
            cmds.select([x for x in cmds.listRelatives('{}{}'.format(namespace, modules_grp), allDescendents=True)
                         if x.endswith('_ctr')])
        else:
            cmds.select([x for x in cmds.listRelatives(modules_grp, allDescendents=True) if x.endswith('_ctr')])


def key_all_controls(namespace_le=None):
    """
    Key all the controls in the scene with the namespace given
    :param namespace_le: QLineEdit
    """
    modules_grp = 'modules_c_grp'

    if namespace_le:
        namespace = namespace_le.text()
        if namespace:
            cmds.setKeyframe([x for x in cmds.listRelatives('{}{}'.format(namespace, modules_grp), allDescendents=True)
                              if x.endswith('_ctr')])
        else:
            cmds.setKeyframe([x for x in cmds.listRelatives(modules_grp, allDescendents=True) if x.endswith('_ctr')])


def key_body_controls(namespace_le=None):
    """
    Key body the controls in the scene with the namespace given
    :param namespace_le: QLineEdit
    """
    modules_grp = 'bodyModules_c_grp'
    if namespace_le:
        namespace = namespace_le.text()
        if namespace:
            cmds.setKeyframe([x for x in cmds.listRelatives('{}{}'.format(namespace, modules_grp), allDescendents=True)
                              if x.endswith('_ctr')])
        else:
            cmds.setKeyframe([x for x in cmds.listRelatives(modules_grp, allDescendents=True) if x.endswith('_ctr')])


def key_face_controls(namespace_le=None):
    """
    Key face the controls in the scene with the namespace given
    :param namespace_le: QLineEdit
    """
    modules_grp = 'faceModules_c_grp'

    if namespace_le:
        namespace = namespace_le.text()
        if namespace:
            cmds.setKeyframe([x for x in cmds.listRelatives('{}{}'.format(namespace, modules_grp), allDescendents=True)
                              if x.endswith('_ctr')])
        else:
            cmds.setKeyframe([x for x in cmds.listRelatives(modules_grp, allDescendents=True) if x.endswith('_ctr')])


def vis_controls(namespace_le=None):
    """
    switch on/off controls visibilities
    :param namespace_le: QLineEdit
    """
    if namespace_le:
        namespace = namespace_le.text()
        if namespace:
            vis_controls_value = 0 if cmds.getAttr('{}general_c_ctr.visControls'.format(namespace)) else 1
            cmds.setAttr('{}general_c_ctr.visControls'.format(namespace), vis_controls_value)
        else:
            vis_controls_value = 0 if cmds.getAttr('general_c_ctr.visControls') else 1
            print(vis_controls_value)
            cmds.setAttr('general_c_ctr.visControls', vis_controls_value)


def vis_geometries(namespace_le=None):
    """
    switch on/off controls visibilities
    :param namespace_le: QLineEdit
    """
    if namespace_le:
        namespace = namespace_le.text()
        if namespace:
            vis_controls_value = 0 if cmds.getAttr('{}general_c_ctr.visGeometries'.format(namespace)) else 1
            cmds.setAttr('{}general_c_ctr.visGeometries'.format(namespace), vis_controls_value)
        else:
            vis_controls_value = 0 if cmds.getAttr('general_c_ctr.visGeometries') else 1
            cmds.setAttr('general_c_ctr.visGeometries', vis_controls_value)
