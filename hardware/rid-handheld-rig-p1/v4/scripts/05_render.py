"""Five actual Blender renders. Restore the assembled scene after every view."""
import bpy
import math
from mathutils import Vector

OUT='C:/Users/YX/Documents/云台检测/hardware/rid-handheld-rig-p1/v4/'
sc=bpy.data.scenes['RIG_P1_V4_Print']
bpy.context.window.scene=sc
root=bpy.data.objects['RIG4_Assembly']
sc.render.resolution_percentage=100
for name,power in [('Key',.5184),('Fill',.3456),('Rim',.4608)]:
    bpy.data.objects['RIG4_'+name].data.energy=power
background=next(n for n in sc.world.node_tree.nodes if n.type=='BACKGROUND')
background.inputs['Strength'].default_value=.18

def render(name,camera):
    sc.camera=bpy.data.objects['RIG4_Camera_'+camera]
    sc.render.filepath=OUT+'renders/'+name+'.png'
    bpy.ops.render.render(write_still=True)

render('01-hero','Hero')
render('02-front','Front')
render('06-usb-detail','USB')
render('07-side','Side')
try:
    root.rotation_euler.x=math.pi;root.location.z=.027
    render('03-rear','Hero')
    bpy.data.objects['RIG4_P02_rear_cover'].hide_render=True
    render('04-inside','Hero')
finally:
    root.rotation_euler.x=0;root.location.z=0
    bpy.data.objects['RIG4_P02_rear_cover'].hide_render=False

saved=[]
try:
    for ob in list(sc.objects):
        if ob.parent!=root or ob.get('fit_only'):continue
        saved.append((ob,ob.location.copy()))
        name=ob.name
        if name=='RIG4_P02_rear_cover':dz=0
        elif name=='RIG4_P10_board_cradle':dz=.010
        elif name=='RIG4_P11_board_keeper' or ob.get('instance_only'):dz=.025
        elif name=='RIG4_P03_black_bezel' or 'Insert_mark' in name:dz=.100
        elif name in ('RIG4_P05_key_up','RIG4_P06_key_down','RIG4_P07_key_confirm',
                       'RIG4_P08_key_mode','RIG4_P09_top_key') or 'Engraved_ink' in name or 'Mode_letter' in name:dz=.095
        elif name=='RIG4_P04_key_carrier' or 'REF_tact' in name:dz=.043
        elif 'REF_lcd' in name or 'REF_header' in name or 'Screen_demo' in name:dz=.032
        elif ob.get('reference_only'):dz=.017
        else:dz=.075
        ob.location.z+=dz
    render('05-exploded','Exploded')
finally:
    for ob,location in saved:ob.location=location
    sc.camera=bpy.data.objects['RIG4_Camera_Hero']
    sc.render.filepath=OUT+'renders/01-hero.png'
print('Rendered hero, front, rear, inside and exploded; assembled transforms restored')
