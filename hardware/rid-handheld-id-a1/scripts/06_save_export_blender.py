"""Finalize the local Blender ID package; convert lettering/marks to portable geometry."""
import bpy
import bmesh
import json
from mathutils import Vector
BASE='C:/Users/YX/Documents/云台检测/hardware/rid-handheld-id-a1/'
scene=bpy.data.scenes['RID_ID_A1_Studio'];bpy.context.window.scene=scene
assert not bpy.app.is_job_running('RENDER')
scene.frame_set(1)
scene.camera=bpy.data.objects['RID_A1_Camera_hero'];scene.render.resolution_x=1600;scene.render.resolution_y=1400
scene.render.filepath=BASE+'renders/02-hero-cnc.png'
bpy.data.objects['RID_A1_Studio_ground'].hide_render=False
for name in ('RID_A1_Back_key','RID_A1_Back_fill'):bpy.data.objects[name].hide_render=True
for v in ('height','radar','reference'):
    obj=bpy.data.objects['RID_A1_Screen_'+v];obj.hide_render=v!='height';obj.hide_set(v!='height')
for name in ('Brand_Yuntong','Brand_AIRSPACE'):
    obj=bpy.data.objects['RID_A1_'+name];obj.hide_render=False;obj.hide_set(False)
obj=bpy.data.objects['RID_A1_Reference_wordmark'];obj.hide_render=True;obj.hide_set(True)
product=bpy.data.collections['ID-A1 | Product']
target=next(i.identifier for i in bpy.ops.object.convert.get_rna_type().properties['target'].enum_items if i.identifier=='MESH')
converted=0
for obj in list(product.objects):
    if obj.type not in ('FONT','CURVE'):continue
    hidden=obj.hide_get();render_hidden=obj.hide_render
    obj.hide_set(False)
    for selected in list(bpy.context.selected_objects):selected.select_set(False)
    obj.select_set(True);bpy.context.view_layer.objects.active=obj
    bpy.ops.object.convert(target=target)
    obj=bpy.context.view_layer.objects.active;obj.select_set(False)
    obj.hide_set(hidden);obj.hide_render=render_hidden;converted+=1

dg=bpy.context.evaluated_depsgraph_get()
checks=[]
for name in ('CNC_midframe','Printed_front_cover','Printed_rear_cover','Rocker_upper','Rocker_lower','Orange_confirm_key','M_key_flush','Top_power_button','Front_black_glass'):
    obj=bpy.data.objects['RID_A1_'+name];ev=obj.evaluated_get(dg);mesh=ev.to_mesh();bm=bmesh.new();bm.from_mesh(mesh)
    checks.append({'name':name,'vertices':len(bm.verts),'faces':len(bm.faces),'non_manifold_edges':sum(not e.is_manifold for e in bm.edges),'volume_mm3':round(bm.calc_volume(signed=False)*1e9,3),'dimensions_mm':[round(v*1000,3) for v in obj.dimensions]})
    bm.free();ev.to_mesh_clear()
visible=[o for o in product.objects if o.type=='MESH' and not o.hide_render and not o.hide_get()]
points=[o.matrix_world@Vector(v) for o in visible for v in o.bound_box]
bounds=[[min(p[i] for p in points)*1000 for i in range(3)],[max(p[i] for p in points)*1000 for i in range(3)]]
report={'revision':'ID-A1','blender':bpy.app.version_string,'body_target_mm':[82,86,20],
        'visible_assembly_bounds_mm':bounds,'geometry_checks':checks,
        'markings_are_portable_meshes':all(o.type not in ('FONT','CURVE') for o in product.objects),'visible_export_meshes':len(visible),
        'images':[{'name':im.name,'packed':im.packed_file is not None,'size':list(im.size)} for im in bpy.data.images if im.name.startswith(('screen-','reference-'))],
        'scope':'visual geometry only; not CNC toolpath, print fit or RF verification'}
scene['validation_json']=json.dumps(report,ensure_ascii=False)
print('ID_REPORT_JSON '+json.dumps(report,ensure_ascii=False))

for selected in list(bpy.context.selected_objects):selected.select_set(False)
for obj in product.objects:
    if not obj.hide_render and not obj.hide_get():obj.select_set(True)
# This operator's dynamic enum reports an empty list in the connected Blender build.
try:
    bpy.ops.export_scene.gltf(filepath=BASE+'blender/yuntong-rid-id-a1.glb',export_format='GLB',use_selection=True,use_active_scene=True,export_apply=True,export_animations=False,export_cameras=False,export_lights=False)
except TypeError as error:
    print('GLTF_ARGUMENT_DIAGNOSTIC',str(error))
    raise
for selected in list(bpy.context.selected_objects):selected.select_set(False)
root=bpy.data.objects['RID_A1_Assembly'];root.select_set(True);bpy.context.view_layer.objects.active=root
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        space=area.spaces.active
        space.region_3d.view_perspective='CAMERA';space.overlay.show_overlays=False
        choices=[i.identifier for i in space.shading.bl_rna.properties['type'].enum_items]
        space.shading.type=choices[choices.index('MATERIAL')]
        space.shading.use_scene_lights=True;space.shading.use_scene_world=True
bpy.ops.wm.save_as_mainfile(filepath=BASE+'blender/yuntong-rid-id-a1.blend',compress=False)
print('PACKAGE_SAVED')
