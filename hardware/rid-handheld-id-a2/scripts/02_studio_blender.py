"""Studio, square-screen presets and reversible assembly separation for ID-A2."""
import bpy
import math
from mathutils import Vector

P='RID_A2_'
scene=bpy.data.scenes['RID_ID_A2_Studio'];bpy.context.window.scene=scene
col=bpy.data.collections['ID-A2 | Studio'];product=bpy.data.collections['ID-A2 | Product']
root=bpy.data.objects[P+'Assembly']
world=bpy.data.worlds.new(P+'Studio_world');world.use_nodes=True;scene.world=world
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND')
bg.inputs['Color'].default_value=(.045,.05,.048,1);bg.inputs['Strength'].default_value=.09
m=bpy.data.materials.new(P+'Studio_charcoal');m.use_nodes=True
p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
p.inputs['Base Color'].default_value=(.015,.018,.016,1);p.inputs['Roughness'].default_value=.88
me=bpy.data.meshes.new(P+'Ground_mesh');me.from_pydata([(-2,-2,-.01035),(2,-2,-.01035),(2,2,-.01035),(-2,2,-.01035)],[],[(0,1,2,3)])
ground=bpy.data.objects.new(P+'Studio_ground',me);col.objects.link(ground);me.materials.append(m)

def area(name,pos,target,power,size,ratio,color):
    kind=next(i.identifier for i in bpy.types.Light.bl_rna.properties['type'].enum_items if i.identifier=='AREA')
    d=bpy.data.lights.new(P+name,kind);d.energy=power;d.color=color
    d.shape=next(i.identifier for i in d.bl_rna.properties['shape'].enum_items if i.identifier=='RECTANGLE')
    d.size=size;d.size_y=size*ratio
    o=bpy.data.objects.new(d.name,d);col.objects.link(o);o.location=pos
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    return o
area('Key',(-.135,.13,.24),(0,0,0),.68,.19,1.5,(1,.975,.94))
area('Edge',(.15,.035,.16),(0,0,.005),.40,.08,2.2,(.93,.97,1))
area('Low',(-.025,-.16,.095),(0,0,0),.255,.12,.45,(1,.96,.90))
area('Long_reflector',(-.12,.18,.28),(-.01,0,.01),.19,.045,5,(1,1,1))
for name,pos,power,size in [('Back_key',(-.10,.04,-.18),.52,.15),('Back_fill',(.08,-.06,-.14),.26,.10)]:
    o=area(name,pos,(0,0,-.006),power,size,1.5,(1,.98,.95));o.hide_render=True

def camera(name,pos,target,ortho):
    d=bpy.data.cameras.new(P+'Camera_'+name)
    d.type=next(i.identifier for i in d.bl_rna.properties['type'].enum_items if i.identifier=='ORTHO')
    d.ortho_scale=ortho;d.clip_start=.001;d.clip_end=20
    o=bpy.data.objects.new(d.name,d);col.objects.link(o);o.location=pos
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    return o
camera('front',(0,0,.3),(0,0,0),.082)
camera('hero',(.080,-.10,.23),(0,0,0),.091)
camera('corner',(-.075,.065,.17),(-.023,.018,.007),.034)
camera('controls',(.065,-.025,.24),(.0215,0,.010),.047)
camera('USB',(0,-.16,.063),(0,-.022,0),.045)
camera('rear',(.07,.12,-.23),(0,0,-.002),.086)
camera('exploded',(.1,-.12,.24),(0,0,.008),.139)
camera('side',(.11,-.13,.063),(0,0,0),.091)

front=bpy.data.objects.new(P+'FRONT_GROUP',None);product.objects.link(front);front.parent=root
display=bpy.data.objects.new(P+'DISPLAY_GROUP',None);product.objects.link(display);display.parent=root
rear=bpy.data.objects.new(P+'REAR_GROUP',None);product.objects.link(rear);rear.parent=root
front_prefixes=('Printed_front','Rocker_','Up_','Down_','Orange_','Confirm_','M_','Checker_','AIRSPACE')
for o in list(product.objects):
    suffix=o.name.replace(P,'',1)
    if suffix.startswith(front_prefixes):o.parent=front
    elif suffix.startswith(('Display_','Screen_')):o.parent=display
    elif suffix.startswith(('Printed_rear','Rear_')):o.parent=rear
for o,z in ((front,.020),(display,.035),(rear,-.022)):
    o.location=(0,0,0);o.keyframe_insert(data_path='location',frame=1)
    o.location=(0,0,z);o.keyframe_insert(data_path='location',frame=60)
scene.frame_start=1;scene.frame_end=60;scene.frame_set(1)

addon=bpy.context.preferences.addons.get('cycles')
prefs=addon.preferences
try:
    prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='OPTIX'
except TypeError as e:print('GPU_ENUM',str(e))
try:scene.render.engine='CYCLES'
except TypeError as e:print('RENDER_ENUM',str(e));raise
scene.cycles.device=next(i.identifier for i in scene.cycles.bl_rna.properties['device'].enum_items if i.identifier=='GPU')
scene.cycles.samples=96;scene.cycles.use_denoising=True;scene.cycles.adaptive_threshold=.012;scene.cycles.max_bounces=8
scene.render.resolution_percentage=100
scene.render.image_settings.file_format=next(i.identifier for i in scene.render.image_settings.bl_rna.properties['file_format'].enum_items if i.identifier=='PNG')
scene.render.film_transparent=False;scene.view_settings.exposure=-.1
scene.camera=bpy.data.objects[P+'Camera_hero'];scene.render.resolution_x=1600;scene.render.resolution_y=1300
for a in bpy.context.screen.areas:
    if a.type=='VIEW_3D':
        a.spaces.active.region_3d.view_perspective='CAMERA';a.spaces.active.overlay.show_overlays=False
print('A2_STUDIO_READY',scene.render.engine,scene.cycles.device)
