"""Export unique printable parts from the live V3 scene through Blender MCP.

STL coordinates are millimetres, individually centred with the lowest point
on Z=0. Export poses never alter the assembled, editable source objects.
"""
import bpy
import bmesh
import math
import json
from mathutils import Matrix, Vector

OUT='C:/Users/YX/Documents/云台检测/hardware/rid-handheld-rig-p1/v3/'
sc=bpy.data.scenes['RIG_P1_V3_Print']
bpy.context.window.scene=sc
depsgraph=bpy.context.evaluated_depsgraph_get()
def part_order(ob):
    return ob['part_id']
parts=sorted([o for o in sc.objects if o.type=='MESH' and 'part_id' in o
              and not o.get('instance_only')],key=part_order)
report={'units':'mm','z_min':0,'parts':[]}
for source in parts:
    me=bpy.data.meshes.new_from_object(source.evaluated_get(depsgraph),depsgraph=depsgraph)
    me.transform(source.matrix_world)
    if source.get('print_front_down'):
        me.transform(Matrix.Rotation(math.pi,4,'X'))
    lo=[min(v.co[k] for v in me.vertices) for k in range(3)]
    hi=[max(v.co[k] for v in me.vertices) for k in range(3)]
    me.transform(Matrix.Translation(Vector((-(lo[0]+hi[0])/2,-(lo[1]+hi[1])/2,-lo[2]))))
    bm=bmesh.new();bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bmesh.ops.triangulate(bm,faces=list(bm.faces))
    bad=sum(not e.is_manifold for e in bm.edges)
    volume=bm.calc_volume(signed=True)*1e6
    if bad or volume<=0:
        bm.free()
        raise RuntimeError('Refusing invalid STL export: '+source.name)
    bm.to_mesh(me);bm.free();me.update()
    temporary=bpy.data.objects.new('RIG3_EXPORT_temporary',me)
    sc.collection.objects.link(temporary)
    bpy.ops.object.select_all(action='DESELECT')
    temporary.select_set(True);bpy.context.view_layer.objects.active=temporary
    filename=source.name.removeprefix('RIG3_')+'.stl'
    bpy.ops.wm.stl_export(filepath=OUT+'stl/'+filename,
        export_selected_objects=True,global_scale=1000,use_scene_unit=False,
        forward_axis='Y',up_axis='Z',ascii_format=False,apply_modifiers=True,
        evaluation_mode='DAG_EVAL_VIEWPORT')
    report['parts'].append({'id':source['part_id'],'file':filename,
        'quantity':source.get('quantity',1),'triangles':len(me.polygons),
        'nonmanifold_edges':bad,'volume_cm3':round(volume,4),
        'bbox_mm':[round((hi[k]-lo[k])*1000,4) for k in range(3)],
        'front_down':bool(source.get('print_front_down'))})
    bpy.data.objects.remove(temporary,do_unlink=True);bpy.data.meshes.remove(me)
bpy.ops.object.select_all(action='DESELECT')
bpy.data.objects['RIG3_P01_front_shell'].select_set(True)
bpy.context.view_layer.objects.active=bpy.data.objects['RIG3_P01_front_shell']
sc['RIG3_export_report']=json.dumps(report)
print(json.dumps(report))
