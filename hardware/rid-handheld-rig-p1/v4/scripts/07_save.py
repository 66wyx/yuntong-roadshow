"""Portable preview and editable Blender file; preserve older scenes."""
import bpy
OUT='C:/Users/YX/Documents/云台检测/hardware/rid-handheld-rig-p1/v4/'
sc=bpy.data.scenes['RIG_P1_V4_Print'];bpy.context.window.scene=sc
root=bpy.data.objects['RIG4_Assembly']
sc['constraints']='User: all wires soldered, LCD total 14 mm, P4 total 14.5 mm, central panel USB-C, overall thickness <=28 mm'
sc['nominal_body_thickness_mm']=27
sc['nominal_key_inclusive_thickness_mm']=27.7
sc['physical_assembly_tested']=False
sc['pending_measurement']='USB extension boot cross-section, elbow plug envelope, exact board height distribution and wire routing'
for material in bpy.data.materials:
    if material.name.startswith('RIG4_Display_demo_texture') and material.use_nodes:
        for node in material.node_tree.nodes:
            if node.type=='TEX_IMAGE' and node.image:node.image.pack()
bpy.ops.object.select_all(action='DESELECT')
root.select_set(True)
for ob in sc.objects:
    if ob.parent==root and not ob.get('fit_only') and ob.type in ('MESH','FONT','CURVE'):
        ob.hide_set(False);ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT+'blender/yuntong-rig-p1-v4.glb',
    export_format='GLB',use_selection=True,use_active_scene=True,export_apply=True,
    export_animations=False,export_cameras=False,export_lights=False,export_extras=True)
bpy.ops.object.select_all(action='DESELECT')
bpy.data.objects['RIG4_P01_front_shell'].select_set(True)
bpy.context.view_layer.objects.active=bpy.data.objects['RIG4_P01_front_shell']
sc.camera=bpy.data.objects['RIG4_Camera_Hero']
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=OUT+'blender/yuntong-rig-p1-v4.blend',compress=True)
print('V4 saved: editable blend and GLB preview; assembled scene active')
