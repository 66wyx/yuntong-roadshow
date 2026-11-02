"""Run after 01 via Blender MCP. Set up lighting, cameras and reversible exploded animation."""
import bpy
import math
from mathutils import Vector
scene=bpy.data.scenes['RID_ID_A1_Studio'];bpy.context.window.scene=scene
collection=bpy.data.collections['ID-A1 | Studio'];product=bpy.data.collections['ID-A1 | Product']
root=bpy.data.objects['RID_A1_Assembly']
scene.render.engine='BLENDER_EEVEE'
if hasattr(scene,'eevee'):
    if hasattr(scene.eevee,'taa_render_samples'):scene.eevee.taa_render_samples=64
    if hasattr(scene.eevee,'use_raytracing'):scene.eevee.use_raytracing=True
scene.render.resolution_percentage=100
scene.render.image_settings.file_format=next(i.identifier for i in scene.render.image_settings.bl_rna.properties['file_format'].enum_items if i.identifier=='PNG')
scene.render.film_transparent=False
transforms=[i.identifier for i in scene.view_settings.bl_rna.properties['view_transform'].enum_items]
print('VIEW_TRANSFORMS',transforms)
if 'AgX' in transforms:scene.view_settings.view_transform='AgX'
scene.view_settings.exposure=-.5
world=bpy.data.worlds.new('RID_A1_Studio_world');world.use_nodes=True;scene.world=world
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND')
bg.inputs['Color'].default_value=(.045,.05,.048,1);bg.inputs['Strength'].default_value=.3
mat=bpy.data.materials.new('RID_A1_Studio_charcoal');mat.use_nodes=True
p=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
p.inputs['Base Color'].default_value=(.015,.018,.016,1);p.inputs['Roughness'].default_value=.88
mesh=bpy.data.meshes.new('RID_A1_Ground_mesh');mesh.from_pydata([(-2,-2,-.0106),(2,-2,-.0106),(2,2,-.0106),(-2,2,-.0106)],[],[(0,1,2,3)])
ground=bpy.data.objects.new('RID_A1_Studio_ground',mesh);collection.objects.link(ground);mesh.materials.append(mat)

def area(name,position,target,power,size,ratio,color):
    types=[i.identifier for i in bpy.types.Light.bl_rna.properties['type'].enum_items]
    data=bpy.data.lights.new('RID_A1_'+name,types[types.index('AREA')]);data.energy=power;data.color=color
    shape=next(i.identifier for i in data.bl_rna.properties['shape'].enum_items if i.identifier=='RECTANGLE')
    data.shape=shape;data.size=size;data.size_y=size*ratio
    obj=bpy.data.objects.new(data.name,data);collection.objects.link(obj);obj.location=position
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    return obj
area('Softbox_key',(-.135,.13,.24),(0,0,0),7.5,.19,1.5,(1,.965,.91))
area('Softbox_edge',(.15,.035,.16),(0,0,.005),4,.08,2.2,(.91,.96,1))
area('Softbox_low',(-.025,-.16,.095),(0,0,0),2.6,.12,.45,(1,.9,.79))
area('Long_glass_reflector',(-.12,.18,.28),(-.015,0,.01),2,.045,5,(1,1,1))

def camera(name,location,target,ortho):
    data=bpy.data.cameras.new('RID_A1_'+name);data.type=next(i.identifier for i in data.bl_rna.properties['type'].enum_items if i.identifier=='ORTHO')
    data.ortho_scale=ortho;data.clip_start=.001;data.clip_end=20
    ob=bpy.data.objects.new(data.name,data);collection.objects.link(ob);ob.location=location
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();return ob
front=camera('Camera_front',(0,0,.3),(0,0,0),.113)
camera('Camera_hero',(.09,-.13,.26),(0,0,.001),.128)
camera('Camera_back',(.07,.12,-.23),(0,0,-.002),.126)
camera('Camera_USB',(0,-.16,.067),(0,-.035,0),.060)
camera('Camera_controls',(.065,-.025,.24),(.028,-.004,.010),.054)
camera('Camera_exploded',(.10,-.13,.24),(0,0,.006),.166)

front_group=bpy.data.objects.new('RID_A1_FRONT_GROUP',None);product.objects.link(front_group);front_group.parent=root
rear_group=bpy.data.objects.new('RID_A1_REAR_GROUP',None);product.objects.link(rear_group);rear_group.parent=root
front_prefixes=('Printed_front','front_interface','Glass_','Front_black','Screen_','Rocker_','Up_','Down_','Orange_','Confirm_','M_','Checker_','Brand_','Reference_')
rear_prefixes=('Printed_rear','rear_interface','Rear_','Screw_drive_')
for obj in list(product.objects):
    suffix=obj.name.replace('RID_A1_','',1)
    if suffix.startswith(front_prefixes):obj.parent=front_group
    elif suffix.startswith(rear_prefixes):obj.parent=rear_group
for obj,z in [(front_group,.033),(rear_group,-.026)]:
    obj.location=(0,0,0);obj.keyframe_insert(data_path='location',frame=1)
    obj.location=(0,0,z);obj.keyframe_insert(data_path='location',frame=60)
scene.frame_start=1;scene.frame_end=60;scene.frame_set(1)
scene.camera=front;scene.render.resolution_x=1100;scene.render.resolution_y=1250
for area_ui in bpy.context.screen.areas:
    if area_ui.type=='VIEW_3D':
        area_ui.spaces.active.region_3d.view_perspective='CAMERA'
        area_ui.spaces.active.overlay.show_overlays=False
print('STUDIO_READY',scene.camera.name,'frame',scene.frame_current)
print('LIGHTS',[(o.name,o.data.energy) for o in collection.objects if o.type=='LIGHT'])
