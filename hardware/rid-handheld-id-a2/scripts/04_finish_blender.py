"""Camera composition and silver side reflections; run before the final renders."""
import bpy
from mathutils import Vector, Matrix
P='RID_A2_'
scene=bpy.data.scenes['RID_ID_A2_Studio'];bpy.context.window.scene=scene
col=bpy.data.collections['ID-A2 | Studio']

def look_y_up(o, target):
    direction=(Vector(target)-o.location).normalized()
    right=direction.cross(Vector((0,1,0))).normalized()
    up=right.cross(direction).normalized()
    o.rotation_euler=Matrix((right,up,-direction)).transposed().to_euler()

for name,target,scale in [('hero',(0,0,0),.094),('controls',(.0215,0,.010),.049),('side',(0,0,0),.098),('corner',(-.023,.018,.007),.034)]:
    o=bpy.data.objects[P+'Camera_'+name];look_y_up(o,target);o.data.ortho_scale=scale

kind=next(i.identifier for i in bpy.types.Light.bl_rna.properties['type'].enum_items if i.identifier=='AREA')
d=bpy.data.lights.new(P+'Silver_side_reflection',kind);d.energy=.115
d.shape=next(i.identifier for i in d.bl_rna.properties['shape'].enum_items if i.identifier=='RECTANGLE')
d.size=.10;d.size_y=.14;d.color=(.96,.98,1)
o=bpy.data.objects.new(d.name,d);col.objects.link(o);o.location=(.13,-.14,.025)
o.rotation_euler=(Vector((0,0,0))-o.location).to_track_quat('-Z','Y').to_euler()

for name in ('Top_power_button','Power_symbol'):bpy.data.objects[P+name].location.x=.0175
scene.camera=bpy.data.objects[P+'Camera_hero']
print('A2_FINISH_READY')
