import bpy
import math
from mathutils import Vector
sc=bpy.data.scenes['RIG_P1_V4_Print']
root=bpy.data.objects['RIG4_Assembly']
studio=bpy.data.collections['RIG4_Studio']
prod=bpy.data.collections['RIG4_Product']
for name,pos,target,scale in [('USB',(.065,-.17,.075),(0,-.044,.0135),.055),('Side',(.2,0,.0135),(0,0,.0135),.112)]:
    data=bpy.data.cameras.new('RIG4_'+name);data.type='ORTHO';data.ortho_scale=scale;data.lens=100;data.clip_start=.001
    ob=bpy.data.objects.new('RIG4_Camera_'+name,data);studio.objects.link(ob);ob.location=pos
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
curve=bpy.data.curves.new('RIG4_USB_route_guide','CURVE');curve.dimensions='3D';curve.bevel_depth=.00065;curve.bevel_resolution=3
spline=curve.splines.new('BEZIER')
points=[(0,-.0146,.0135),(0,-.006,.0135),(.002,0,.010),(.0085,-.002,.007),(.0085,-.028,.007),(.010,-.040,.009),(.022,-.041,.012),(.026,-.041,.0135)]
spline.bezier_points.add(len(points)-1)
for point,position in zip(spline.bezier_points,points):point.co=position;point.handle_left_type='AUTO';point.handle_right_type='AUTO'
wire=bpy.data.objects.new('RIG4_USB_routing_guide',curve);prod.objects.link(wire);wire.parent=root;wire['visual_detail']=True;wire['routing_preview_only']=True
mat=next(m for m in bpy.data.objects['RIG4_REF_usb_boot_30mm'].data.materials if m)
curve.materials.append(mat)
metal=next(m for m in bpy.data.objects['RIG4_REF_usb_front_metal'].data.materials if m)
for x in (-.008,.008):
    bpy.ops.mesh.primitive_cone_add(vertices=48,radius1=.001,radius2=.002,depth=.0011,rotation=(math.pi/2,0,0),location=(x,-.04745,.0135))
    ob=bpy.context.object;ob.name='RIG4_USB_M2_head';ob.parent=root;ob['visual_detail']=True
    for collection in list(ob.users_collection):collection.objects.unlink(ob)
    prod.objects.link(ob);ob.data.materials.append(metal)
sc.camera=bpy.data.objects['RIG4_Camera_Hero'];sc.render.resolution_percentage=60
bpy.ops.render.render(write_still=True)
print('Added central USB detail cameras and routing guide; hero preview rendered')
