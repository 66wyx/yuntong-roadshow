"""Pack ID-A2, retain editable Bezier construction, export active A2 product only."""
import bpy
import bmesh
import json
from mathutils import Vector

P='RID_A2_'
BASE='C:/Users/YX/Documents/云台检测/hardware/rid-handheld-id-a2/'
scene=bpy.data.scenes['RID_ID_A2_Studio'];bpy.context.window.scene=scene
assert not bpy.app.is_job_running('RENDER')
scene.frame_set(1)
scene.camera=bpy.data.objects[P+'Camera_hero']
scene.render.resolution_x=1600;scene.render.resolution_y=1300
scene.render.filepath=BASE+'renders/01-hero-metal-wrap.png'
bpy.data.objects[P+'Studio_ground'].hide_render=False
for name in ('Back_key','Back_fill'):bpy.data.objects[P+name].hide_render=True
for name in ('height','radar'):
    o=bpy.data.objects[P+'Screen_'+name];o.hide_render=name!='height';o.hide_set(name!='height')
product=bpy.data.collections['ID-A2 | Product']
for name in ('reference-original.png','reference-rid.png','reference-metal-wrap.png'):
    im=bpy.data.images.load(BASE+'assets/'+name,check_existing=True);im.use_fake_user=True;im.pack()
kind=next(i.identifier for i in bpy.ops.object.convert.get_rna_type().properties['target'].enum_items if i.identifier=='MESH')
for o in list(product.objects):
    if o.type not in ('FONT','CURVE'):continue
    hidden=o.hide_get();render_hidden=o.hide_render;o.hide_set(False)
    for selected in list(bpy.context.selected_objects):selected.select_set(False)
    o.select_set(True);bpy.context.view_layer.objects.active=o
    bpy.ops.object.convert(target=kind)
    o=bpy.context.view_layer.objects.active;o.select_set(False);o.hide_set(hidden);o.hide_render=render_hidden

dg=bpy.context.evaluated_depsgraph_get();checks=[]
names=('CNC_wrap_shell','Printed_front_insert','Printed_rear_insert','Display_lower_CG_38p5x39p2','Display_upper_CG_36p5','Rocker_upper','Rocker_lower','Orange_confirm_key','M_key','Top_power_button','USB_C_metal_shell')
for name in names:
    o=bpy.data.objects[P+name];ev=o.evaluated_get(dg);me=ev.to_mesh();bm=bmesh.new();bm.from_mesh(me)
    checks.append({'name':name,'vertices':len(bm.verts),'faces':len(bm.faces),
                   'non_manifold_edges':sum(not e.is_manifold for e in bm.edges),
                   'signed_volume_mm3':round(bm.calc_volume(signed=True)*1e9,5),
                   'dimensions_mm':[round(v*1000,4) for v in o.dimensions]})
    bm.free();ev.to_mesh_clear()

# Verify the editable cubic handles, not only the design text.
curve=bpy.data.objects[P+'Cubic_corner_control_path'].data
b0,b1,b2=curve.splines[0].bezier_points
first=[Vector(p) for p in (b0.co,b0.handle_right,b1.handle_left,b1.co)]
second=[Vector(p) for p in (b1.co,b1.handle_right,b2.handle_left,b2.co)]
def deriv(p,t):
    return 3*((1-t)**2*(p[1]-p[0])+2*(1-t)*t*(p[2]-p[1])+t*t*(p[3]-p[2]))
def dderiv(p,t):
    return 6*((1-t)*(p[2]-2*p[1]+p[0])+t*(p[3]-2*p[2]+p[1]))
def curvature(p,t):
    d=deriv(p,t);dd=dderiv(p,t)
    return d.cross(dd).length/(d.length**3)/1000
corner={'curve':'two cubic Beziers per quadrant',
        'extent_mm':9.2,'first_control_points_mm':[[round(v*1000,6) for v in p] for p in first],
        'second_control_points_mm':[[round(v*1000,6) for v in p] for p in second],
        'start_curvature_per_mm':curvature(first,0),'end_curvature_per_mm':curvature(second,1),
        'join_position_error_mm':(first[3]-second[0]).length*1000,
        'join_first_derivative_error_mm':(deriv(first,1)-deriv(second,0)).length*1000,
        'join_second_derivative_error_mm':(dderiv(first,1)-dderiv(second,0)).length*1000,
        'note':'G2 at straight sides; C2 at diagonal join. Original parameters, not Apple CAD.'}
visible=[o for o in product.objects if o.type=='MESH' and not o.hide_render and not o.hide_get()]
pts=[o.matrix_world@Vector(v) for o in visible for v in o.bound_box]
report={'revision':'ID-A2','blender':bpy.app.version_string,'body_target_mm':[64,54,20],
        'front_aluminum_rim_mm':2.9,'printed_face_recess_mm':.35,
        'screen_model':'AM200Q460460FLS1','screen_active_area_mm':[35.88,35.88],
        'screen_native_pixels':[460,460],'geometry_checks':checks,'corner_validation':corner,
        'visible_assembly_bounds_mm':[[round(min(p[i] for p in pts)*1000,4) for i in range(3)],[round(max(p[i] for p in pts)*1000,4) for i in range(3)]],
        'portable_markings':all(o.type not in ('FONT','CURVE') for o in product.objects),
        'exact_corner_control_curve_retained':bpy.data.objects[P+'Cubic_corner_control_path'].type=='CURVE',
        'visible_export_meshes':len(visible),
        'images':[{'name':im.name,'packed':im.packed_file is not None,'size':list(im.size)} for im in bpy.data.images if im.name.startswith(('screen-','reference-'))],
        'scope':'Appearance geometry validation only; no physical fit, CNC tooling, charging or RF validation'}
scene['validation_json']=json.dumps(report,ensure_ascii=False)
print('ID_REPORT_JSON '+json.dumps(report,ensure_ascii=False))
assert all(v['non_manifold_edges']==0 and v['signed_volume_mm3']>0 for v in checks),'Structural mesh check failed'
assert corner['join_first_derivative_error_mm']<.0001 and corner['join_second_derivative_error_mm']<.0001,'Cubic join check failed'

for o in list(bpy.context.selected_objects):o.select_set(False)
for o in product.objects:
    if not o.hide_render and not o.hide_get():o.select_set(True)
try:
    bpy.ops.export_scene.gltf(filepath=BASE+'blender/yuntong-rid-id-a2.glb',export_format='GLB',use_selection=True,use_active_scene=True,export_apply=True,export_animations=False,export_cameras=False,export_lights=False)
except TypeError as error:
    print('GLTF_ARGUMENT_DIAGNOSTIC',str(error));raise
for o in list(bpy.context.selected_objects):o.select_set(False)
root=bpy.data.objects[P+'Assembly'];root.select_set(True);bpy.context.view_layer.objects.active=root
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        s=area.spaces.active;s.region_3d.view_perspective='CAMERA';s.overlay.show_overlays=False
        s.shading.type=next(i.identifier for i in s.shading.bl_rna.properties['type'].enum_items if i.identifier=='MATERIAL')
        s.shading.use_scene_lights=True;s.shading.use_scene_world=True
bpy.ops.wm.save_as_mainfile(filepath=BASE+'blender/yuntong-rid-id-a2.blend',compress=False)
print('A2_PACKAGE_SAVED')
