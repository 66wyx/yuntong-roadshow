"""MCP audit of closed parts and actual positive-volume assembly clashes."""
import bpy
import bmesh
import json
from mathutils import Vector

sc=bpy.data.scenes['RIG_P1_V4_Print']
bpy.context.window.scene=sc
parts=[ob for ob in sc.objects if ob.type=='MESH' and 'part_id' in ob and not ob.get('instance_only')]
report={'units':'mm','parts':{},'clashes':[],'checked_pairs':0}

def measure(ob):
    bm=bmesh.new()
    bm.from_mesh(ob.data)
    seen=set()
    count=0
    for start in bm.verts:
        if start in seen: continue
        count+=1
        todo=[start]; seen.add(start)
        while todo:
            current=todo.pop()
            for item in current.link_edges:
                other=item.other_vert(current)
                if other not in seen:
                    seen.add(other); todo.append(other)
    result={'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),
            'components':count,'volume_cm3':round(bm.calc_volume(signed=True)*1e6,4),
            'bbox_mm':[round(v*1000,3) for v in ob.dimensions],
            'quantity':ob.get('quantity',1)}
    bm.free()
    return result

for ob in parts:
    report['parts'][ob.name]=measure(ob)

def bounds(ob):
    points=[ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return ([min(v[k] for v in points) for k in range(3)],
            [max(v[k] for v in points) for k in range(3)])

def broad(a,b):
    alo,ahi=bounds(a); blo,bhi=bounds(b)
    return all(min(ahi[k],bhi[k])-max(alo[k],blo[k])>1e-7 for k in range(3))

def overlap(a,b):
    ob=a.copy()
    ob.data=a.data.copy()
    sc.collection.objects.link(ob)
    ob.name='RIG4_AUDIT_temporary'
    mod=ob.modifiers.new('Interference measurement','BOOLEAN')
    mod.operation='INTERSECT'; mod.solver='EXACT'; mod.object=b
    bpy.context.view_layer.objects.active=ob
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bm=bmesh.new(); bm.from_mesh(ob.data)
    volume=abs(bm.calc_volume(signed=True))*1e9 if bm.faces else 0
    bm.free()
    data=ob.data
    bpy.data.objects.remove(ob,do_unlink=True)
    bpy.data.meshes.remove(data)
    return volume

def group(ob):
    if 'REF_lcd' in ob.name:return 'LCD'
    if 'REF_p4' in ob.name or 'REF_gpio' in ob.name:return 'P4'
    if 'REF_usb' in ob.name:return 'USB'
    return 'KEY'
assembly=[ob for ob in sc.objects if ob.type=='MESH' and
          ('part_id' in ob or ob.get('reference_only')) and
          not ob.get('fit_only') and 'REF_tact_plunger' not in ob.name]
for i,a in enumerate(assembly):
    for b in assembly[i+1:]:
        part_pair='part_id' in a or 'part_id' in b
        ga,gb=group(a),group(b)
        hardware_pair=not part_pair and ga!=gb and ga!='KEY' and gb!='KEY'
        if not part_pair and not hardware_pair:continue
        if hardware_pair and set((a.name,b.name))==set(('RIG4_REF_p4_usb_socket','RIG4_REF_usb_right_angle_plug')):continue
        if not broad(a,b):continue
        report['checked_pairs']+=1
        volume=overlap(a,b)
        if volume>.01:report['clashes'].append({'a':a.name,'b':b.name,'volume_mm3':round(volume,4)})
body=[ob for ob in assembly if 'part_id' in ob]
allpoints=[ob.matrix_world @ Vector(c) for ob in body for c in ob.bound_box]
report['physical_printed_thickness_mm']=round((max(v.z for v in allpoints)-min(v.z for v in allpoints))*1000,4)
report['under_28mm']=report['physical_printed_thickness_mm']<=28
report['all_parts_closed']=all(p['nonmanifold_edges']==0 and p['components']==1 and p['volume_cm3']>0 for p in report['parts'].values())
report['user_supplied_heights_mm']={'LCD':14,'P4':14.5}
report['fit_tested']=False
sc['RIG4_validation']=json.dumps(report)
print(json.dumps(report))
