"""Additional review details and reference assets; run once after the build and studio stages."""
import bpy
import math
from mathutils import Vector
scene=bpy.data.scenes['RID_ID_A1_Studio'];bpy.context.window.scene=scene
assert not bpy.app.is_job_running('RENDER'),'Wait for current render before changing scene'
product=bpy.data.collections['ID-A1 | Product'];studio=bpy.data.collections['ID-A1 | Studio']
root=bpy.data.objects['RID_A1_Assembly']
for name in ('Rear_brand','Rear_model','Rear_material'):
    obj=bpy.data.objects['RID_A1_'+name];obj.rotation_euler=(0,math.pi,0)
bpy.data.objects['RID_A1_Rear_brand'].data.size=.0024
ink=bpy.data.materials['RID_A1_Printed_charcoal_graphics']

def curve(name,points):
    types=[i.identifier for i in bpy.types.BlendDataCurves.bl_rna.functions['new'].parameters['type'].enum_items]
    data=bpy.data.curves.new('RID_A1_'+name,types[types.index('CURVE')]);data.dimensions='3D'
    data.bevel_depth=.000055;data.bevel_resolution=3;data.use_fill_caps=True
    types=[i.identifier for i in bpy.types.Spline.bl_rna.properties['type'].enum_items]
    sp=data.splines.new(types[types.index('POLY')]);sp.points.add(len(points)-1)
    for p,co in zip(sp.points,points):p.co=(*co,1)
    ob=bpy.data.objects.new(data.name,data);product.objects.link(ob);ob.parent=root;data.materials.append(ink)
curve('Power_symbol_arc',[(.03+.00057*math.sin(math.radians(a)),.044406,.0035+.00057*math.cos(math.radians(a))) for a in range(42,319,4)])
curve('Power_symbol_stem',[(.03,.044406,.00355),(.03,.044406,.00425)])

def backlight(name,loc,power,size):
    types=[i.identifier for i in bpy.types.Light.bl_rna.properties['type'].enum_items]
    data=bpy.data.lights.new(name,types[types.index('AREA')]);data.energy=power;data.size=size
    ob=bpy.data.objects.new(name,data);studio.objects.link(ob);ob.location=loc
    ob.rotation_euler=(Vector((0,0,0))-ob.location).to_track_quat('-Z','Y').to_euler();ob.hide_render=True
backlight('RID_A1_Back_key',(-.13,.10,-.20),.55,.17)
backlight('RID_A1_Back_fill',(.12,-.08,-.14),.24,.13)

refs=bpy.data.collections.new('ID-A1 | Supplied references');scene.collection.children.link(refs)
for i,name in enumerate(('reference-design.png','reference-rid-layout.png')):
    im=bpy.data.images.load('C:/Users/YX/Documents/云台检测/hardware/rid-handheld-id-a1/assets/'+name,check_existing=True);im.pack()
    ob=bpy.data.objects.new('RID_REF_'+str(i+1),None);refs.objects.link(ob)
    choices=[e.identifier for e in ob.bl_rna.properties['empty_display_type'].enum_items]
    ob.empty_display_type=choices[choices.index('IMAGE')];ob.data=im;ob.empty_display_size=.13
    ob.location=(-.14-i*.13,0,0);ob.hide_render=True;ob.hide_set(True)

scene['readme']='ID-A1: CNC aluminum midframe and printed front/rear covers. Frame 1 assembled; frame 60 exploded. Screen_height/radar/reference are visual-only variants. Supplied references are packed. Rear and sides are proposed designs. Not manufacturing CAD.'
print('DETAILS_ADDED',len(product.objects),'product objects')
