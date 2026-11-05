"""A1 visual language, functional engravings and isolated render studio."""
import bpy
import bmesh
import math
import json
from mathutils import Vector

P='RIG4_'
sc=bpy.data.scenes['RIG_P1_V4_Print']
bpy.context.window.scene=sc
prod=bpy.data.collections[P+'Product']
studio=bpy.data.collections[P+'Studio']
root=bpy.data.objects[P+'Assembly']
if bpy.data.objects.get(P+'Screen_demo'):
    raise RuntimeError('Details already exist; inspect instead of duplicating')

def mat(name,rgb,rough=.6):
    m=bpy.data.materials.new(P+name)
    m.use_nodes=True
    node=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    node.inputs['Base Color'].default_value=(*rgb,1)
    node.inputs['Roughness'].default_value=rough
    m.diffuse_color=(*rgb,1)
    return m

ink=mat('Detail_ink',(.015,.023,.018))
lightink=mat('Gray_on_black',(.23,.27,.24))
orange=mat('Detail_orange',(.75,.18,.05))

def poly(name,pts,z0,z1,material=None):
    n=len(pts)
    me=bpy.data.meshes.new(P+name)
    verts=[(x*.001,y*.001,z*.001) for z in (z0,z1) for x,y in pts]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    me.from_pydata(verts,[],faces);me.update()
    ob=bpy.data.objects.new(P+name,me)
    prod.objects.link(ob); ob.parent=root
    if material:me.materials.append(material)
    ob['visual_detail']=True
    return ob

def stroke(name,a,b,width,z0,z1,material=None):
    length=math.dist(a,b)
    dx=-(b[1]-a[1])*width/(2*length)
    dy=(b[0]-a[0])*width/(2*length)
    return poly(name,[(a[0]+dx,a[1]+dy),(a[0]-dx,a[1]-dy),
                     (b[0]-dx,b[1]-dy),(b[0]+dx,b[1]+dy)],z0,z1,material)

def cut(ob,tool):
    m=ob.modifiers.new('Engraving','BOOLEAN')
    m.operation='DIFFERENCE';m.solver='EXACT';m.object=tool
    bpy.context.view_layer.objects.active=ob
    bpy.ops.object.modifier_apply(modifier=m.name)
    data=tool.data;bpy.data.objects.remove(tool,do_unlink=True)
    bpy.data.meshes.remove(data)

engravings=[('P05_key_up',[(28,16),(30,18),(32,16)]),
            ('P06_key_down',[(28,6),(30,4),(32,6)]),
            ('P07_key_confirm',[(27.8,-14),(29.3,-15.5),(32.4,-12.2)])]
for target,points in engravings:
    for a,b in zip(points[:-1],points[1:]):
        cut(bpy.data.objects[P+target],stroke('tool_mark',a,b,.55,27.35,28))
        stroke('Engraved_ink',a,b,.52,27.36,27.37,ink)

# A1 restrained horizontal breaks on the right column.
for yy in (30.8,-33.5):
    cut(bpy.data.objects[P+'P01_front_shell'],
        stroke('tool_groove',(20.3,yy),(39.5,yy),.35,26.73,27.15))

for ob in [o for o in sc.objects if o.type=='MESH' and 'part_id' in o and not o.get('instance_only')]:
    if ob['part_id'] not in ('P03','P05','P06','P07','P08','P09'):continue
    original=ob.data.copy()
    m=ob.modifiers.new('Small tactile edge radius','BEVEL')
    m.width=.08*.001;m.segments=2;m.limit_method='ANGLE'
    bpy.context.view_layer.objects.active=ob
    bpy.ops.object.modifier_apply(modifier=m.name)
    bm=bmesh.new();bm.from_mesh(ob.data)
    bad=any(not e.is_manifold for e in bm.edges)
    bm.free()
    if bad:ob.data=original
    ob['edge_radius_mm']=0 if bad else .08

def text(name,body,x,y,z,size,material=ink):
    cu=bpy.data.curves.new(P+name,'FONT')
    cu.body=body;cu.align_x='CENTER';cu.size=size*.001
    ob=bpy.data.objects.new(P+name,cu)
    prod.objects.link(ob);ob.parent=root
    ob.location=(x*.001,y*.001,z*.001)
    cu.materials.append(material)
    ob['visual_detail']=True
    return ob

text('Mode_letter','M',30,-26.25,27.715,2.1)
text('Model','RID / P1',30,26.8,27.015,1.6)
text('Insert_mark','TEST  240 x 320',-11,-39.7,26.865,1.6,lightink)
# Reuse the original A1 Chinese brand mesh with its verified glyphs.
for source_name,width,x,y in [('RID_A1_Brand_Yuntong',8.0,30,-38.0),
                              ('RID_A1_Brand_AIRSPACE',7.1,30,-41.5)]:
    source=bpy.data.objects[source_name]
    world=[source.matrix_world @ v.co for v in source.data.vertices]
    lo=[min(v[k] for v in world) for k in range(3)]
    hi=[max(v[k] for v in world) for k in range(3)]
    centre=Vector([(lo[k]+hi[k])/2 for k in range(3)])
    factor=width*.001/(hi[0]-lo[0])
    verts=[tuple((v-centre)*factor+Vector((x*.001,y*.001,.027015))) for v in world]
    me=bpy.data.meshes.new(P+'Brand_mesh')
    me.from_pydata(verts,[],[tuple(f.vertices) for f in source.data.polygons]);me.update()
    ob=bpy.data.objects.new(P+source_name,me)
    prod.objects.link(ob);ob.parent=root;me.materials.append(ink)
    ob['visual_detail']=True

for row,col in ((0,0),(0,2),(0,4),(1,1),(1,2),(1,3),(1,4)):
    x=24.7+col*1.85;y=37.9-row*1.85
    poly('Checker',[(x,y),(x+1.15,y),(x+1.15,y+1.15),(x,y+1.15)],
         27.01,27.02,orange if (row,col)==(1,1) else ink)

screenmat=bpy.data.materials.new(P+'Display_demo_texture')
screenmat.use_nodes=True
nodes=screenmat.node_tree.nodes
nodes.clear()
output=nodes.new('ShaderNodeOutputMaterial')
emit=nodes.new('ShaderNodeEmission');emit.inputs['Strength'].default_value=.65
texture=nodes.new('ShaderNodeTexImage')
texture.image=bpy.data.images.load('C:/Users/YX/Documents/云台检测/hardware/rid-handheld-id-a1/assets/screen-height.png',check_existing=True)
screenmat.node_tree.links.new(texture.outputs['Color'],emit.inputs['Color'])
screenmat.node_tree.links.new(emit.outputs[0],output.inputs['Surface'])
me=bpy.data.meshes.new(P+'Screen_quad')
me.from_pydata([(-.0326,-.0337,.02581),(.0106,-.0337,.02581),
                (.0106,.0239,.02581),(-.0326,.0239,.02581)],[],[(0,1,2,3)])
me.update()
layer=me.uv_layers.new()
for item,uv in zip(layer.data,[(0,0),(1,0),(1,1),(0,1)]):item.uv=uv
screen=bpy.data.objects.new(P+'Screen_demo',me)
prod.objects.link(screen);screen.parent=root;me.materials.append(screenmat)
screen['visual_detail']=True
screen['demo_only']=True

world=bpy.data.worlds.new(P+'Studio_world');world.use_nodes=True
sc.world=world
background=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND')
background.inputs['Color'].default_value=(.16,.17,.16,1)
background.inputs['Strength'].default_value=.18

floor_mat=mat('Studio_ground',(.115,.12,.11),.75)
me=bpy.data.meshes.new(P+'Ground')
me.from_pydata([(-2,-2,-.001),(2,-2,-.001),(2,2,-.001),(-2,2,-.001)],[],[(0,1,2,3)])
floor=bpy.data.objects.new(P+'Ground',me);studio.objects.link(floor);me.materials.append(floor_mat)

def aim(ob,target):
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()

for name,pos,power,size in [('Key',(-.13,-.10,.24),9,.24),
                            ('Fill',(.18,.06,.20),6,.22),
                            ('Rim',(-.08,.16,.20),8,.17)]:
    data=bpy.data.lights.new(P+name,'AREA')
    data.energy=power*.0576;data.shape='DISK';data.size=size
    ob=bpy.data.objects.new(P+name,data);studio.objects.link(ob);ob.location=pos
    aim(ob,(0,0,.02))

for name,pos,target,scale in [('Hero',(.14,-.19,.25),(0,0,.015),.158),
                              ('Front',(0,0,.35),(0,0,.016),.112),
                              ('Rear',(-.12,-.16,-.22),(0,0,.016),.158),
                              ('Exploded',(.20,-.24,.24),(0,0,.060),.215)]:
    data=bpy.data.cameras.new(P+name)
    data.type='ORTHO';data.ortho_scale=scale;data.lens=100
    data.clip_start=.001;data.clip_end=10
    ob=bpy.data.objects.new(P+'Camera_'+name,data)
    studio.objects.link(ob);ob.location=pos;aim(ob,target)
sc.camera=bpy.data.objects[P+'Camera_Hero']
try:sc.render.engine='BLENDER_EEVEE'
except TypeError:pass
sc.render.resolution_x=1600;sc.render.resolution_y=1600;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG'
sc.render.film_transparent=False
if 'AgX' in [item.identifier for item in sc.view_settings.bl_rna.properties['view_transform'].enum_items]:
    sc.view_settings.view_transform='AgX'
sc.view_settings.exposure=0
sc.render.filepath='C:/Users/YX/Documents/云台检测/hardware/rid-handheld-rig-p1/v4/renders/01-hero.png'
# Boolean cutters can introduce empty material slots. Keep each mechanical
# part monochrome so its actual assigned material also covers newly cut faces.
for ob in sc.objects:
    if ob.type!='MESH':continue
    if 'part_id' in ob or ob.get('reference_only'):
        valid=[m for m in ob.data.materials if m is not None]
        if valid:
            ob.data.materials.clear();ob.data.materials.append(valid[0])
            for face in ob.data.polygons:face.material_index=0
    if 'part_id' in ob or ob.get('visual_detail'):
        for m in ob.data.materials:
            if m is None or not m.use_nodes:continue
            for n in m.node_tree.nodes:
                if n.type=='BSDF_PRINCIPLED':
                    n.inputs['Specular IOR Level'].default_value=.08
                    if ob.name=='RIG4_P03_black_bezel':n.inputs['Roughness'].default_value=.65
print(json.dumps({'scene':sc.name,'camera':sc.camera.name,'parts':13,'board':'photo WIFI6-M','display_demo':'A1 texture on actual 43.2 x 57.6 AA'},ensure_ascii=False))
