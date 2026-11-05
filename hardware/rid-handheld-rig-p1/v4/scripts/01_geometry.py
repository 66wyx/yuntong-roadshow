"""Run through Blender MCP. Millimetre inputs, metre scene, isolated V4 scene.

Hardware basis: photo-identified Waveshare ESP32-P4-WIFI6-M, 71.05 x 21,
and LCDWiki MSP2834. The latter drawing locates lens/VA/AA 6.40/9.14/9.30
below the PCB top. Geometry is a first physical fit prototype.
"""
import bpy
import bmesh
import math
import json
from mathutils import Vector, Matrix

OUT = 'C:/Users/YX/Documents/云台检测/hardware/rid-handheld-rig-p1/v4/'
P = 'RIG4_'
if bpy.data.scenes.get('RIG_P1_V4_Print'):
    raise RuntimeError('V4 exists. Inspect and edit its objects instead of overwriting it.')
sc = bpy.data.scenes.new('RIG_P1_V4_Print')
bpy.context.window.scene = sc
sc.unit_settings.system = 'METRIC'
sc.unit_settings.scale_length = 1.0
prod = bpy.data.collections.new(P + 'Product')
refs = bpy.data.collections.new(P + 'Hardware_envelopes')
studio = bpy.data.collections.new(P + 'Studio')
for collection in (prod, refs, studio):
    sc.collection.children.link(collection)
root = bpy.data.objects.new(P+'Assembly', None)
prod.objects.link(root)
root['body_mm'] = '86 x 96 x 27; key-inclusive 27.7'
root['status'] = 'First fit prototype; photo-identified narrow P4-WIFI6-M board'
root['hardware'] = 'User heights: LCD 14.0, P4 14.5 mm; soldered wiring; central USB extension'
PARTS = []
REFS = []
MM = .001

def material(name, rgb, rough=.55, metallic=0):
    m = bpy.data.materials.new(P+name)
    m.use_nodes = True
    node = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    node.inputs['Base Color'].default_value = (*rgb, 1)
    node.inputs['Roughness'].default_value = rough
    node.inputs['Metallic'].default_value = metallic
    m.diffuse_color = (*rgb,1)
    return m

mgray = material('Warm_gray_PETG',(.39,.39,.36),.58)
mback = material('Rear_warm_gray',(.31,.32,.30),.63)
mblack = material('Black_front_insert',(.008,.011,.009),.34)
mkey = material('Keys',(.56,.56,.52),.5)
morange = material('Orange_confirm',(.77,.19,.055),.5)
mink = material('Ink',(.018,.025,.021),.57)
mpcb = material('PCB',(.018,.09,.055),.58)
mgold = material('Pins',(.55,.36,.09),.4,.7)
mmetal = material('Connector',(.38,.41,.40),.3,.8)
mlcd = material('LCD_envelope',(.018,.021,.020),.5)

def mesh(name, pts, z0,z1, x=0,y=0, mat=None,col=None):
    n=len(pts)
    verts=[((a+x)*MM,(b+y)*MM,z*MM) for z in (z0,z1) for a,b in pts]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    me=bpy.data.meshes.new(P+name+'_mesh')
    me.from_pydata(verts,[],faces)
    me.update()
    ob=bpy.data.objects.new(P+name,me)
    (col or prod).objects.link(ob)
    if mat: me.materials.append(mat)
    ob.parent=root if col != studio else None
    return ob

def bez(a,b,c,d,t):
    u=1-t
    return (u*u*u*a[0]+3*u*u*t*b[0]+3*u*t*t*c[0]+t*t*t*d[0],
            u*u*u*a[1]+3*u*u*t*b[1]+3*u*t*t*c[1]+t*t*t*d[1])

def corners(w,h,L,n=20):
    a=((0,0),(.28*L,0),(.64*L,0),(.82*L,-.18*L))
    b=(a[3],(L,-.36*L),(L,-.72*L),(L,-L))
    q=[bez(*a,j/n) for j in range(n)] + [bez(*b,j/n) for j in range(n+1)]
    tr=[(w/2-L+x,h/2+y) for x,y in q]
    return list(reversed(tr+[(x,-y) for x,y in reversed(tr)] +
                         [(-x,-y) for x,y in tr]+[(-x,y) for x,y in reversed(tr)]))

def rounded(w,h,r,n=14):
    pts=[]
    for x,y,a in ((w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),
                  (-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)):
        for j in range(n+1):
            angle=math.radians(a+90*j/n)
            pt=(x+r*math.cos(angle),y+r*math.sin(angle))
            if not pts or math.dist(pt,pts[-1])>1e-6: pts.append(pt)
    if math.dist(pts[0],pts[-1])<1e-6: pts.pop()
    return pts

def half_rocker(w,h,upper=True,n=24):
    radius=w/2
    centre=h/2-radius
    pts=[(radius*math.cos(j*math.pi/n),centre+radius*math.sin(j*math.pi/n)) for j in range(n+1)]
    pts += [(-radius,-h/2),(radius,-h/2)]
    return pts if upper else list(reversed([(x,-y) for x,y in pts]))

def rect(name,w,h,z0,z1,x=0,y=0,r=.2,mat=None,col=None):
    return mesh(name,rounded(w,h,min(r,w/2,h/2)),z0,z1,x,y,mat,col)

def cyl(name,r,z0,z1,x,y,mat=None,col=None,n=48):
    return mesh(name,[(r*math.cos(j*2*math.pi/n),r*math.sin(j*2*math.pi/n)) for j in range(n)],
                z0,z1,x,y,mat,col)

def boolean(ob, tool, op='DIFFERENCE'):
    mod=ob.modifiers.new('Mechanical '+op,'BOOLEAN')
    mod.operation=op
    mod.solver='EXACT'
    mod.object=tool
    bpy.context.view_layer.objects.active=ob
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(tool,do_unlink=True)

def edge(ob,w=.13):
    mod=ob.modifiers.new('Edge break','BEVEL')
    mod.width=w*MM
    mod.segments=3
    mod.limit_method='ANGLE'
    # Cosmetic modifier remains unapplied until evaluated mesh audit.

def part(ob,part_id,qty=1,flip=False):
    ob['part_id']=part_id
    ob['quantity']=qty
    ob['print_front_down']=flip
    PARTS.append(ob)
    return ob

def ref(ob):
    REFS.append(ob)
    ob['reference_only']=True
    return ob


# Overall hard limit includes raised front keys.
FACE=27.0
CASE_SCREWS=[(-39,-30),(-39,30),(39.8,-40),(39.8,40)]
LCD_HOLES=[(-33,-40),(11,-40),(-33,36.08),(11,36.08)]
TRAY_SCREWS=[(13,-10),(37.7,-10),(13,15),(37.7,15)]
KEY_SCREWS=[(21.2,-33),(38,-33),(21.2,30),(38,30)]
KEYS=[('up',30,16.75,11.2,10.9),('down',30,5.25,11.2,10.9),
      ('confirm',30,-14,11.2,11.2),('mode',30,-25.5,8.4,4.2)]

def side_rect(name,w,h,y0,y1,x,z,r=.2,mat=None,col=None):
    ob=mesh(name,rounded(w,h,r),-y1,-y0,x,0,mat,col)
    ob.data.transform(Matrix.Translation(Vector((0,0,z*MM))) @ Matrix.Rotation(math.pi/2,4,'X'))
    return ob

def side_hole(name,r,y0,y1,x,z):
    ob=cyl(name,r,-y1,-y0,x,0)
    ob.data.transform(Matrix.Translation(Vector((0,0,z*MM))) @ Matrix.Rotation(math.pi/2,4,'X'))
    return ob

def cone_z(name,r0,r1,z0,z1,x=0,y=0):
    n=48
    verts=[((x+r*math.cos(j*math.tau/n))*MM,(y+r*math.sin(j*math.tau/n))*MM,z*MM)
           for r,z in ((r0,z0),(r1,z1)) for j in range(n)]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
    me=bpy.data.meshes.new(P+name);me.from_pydata(verts,[],faces);me.update()
    ob=bpy.data.objects.new(P+name,me);prod.objects.link(ob);ob.parent=root
    return ob

# Face and LCD move forward by -5 mm; original straight pin heights retained.
shell=part(mesh('P01_front_shell',corners(86,96,8.5),2.7,FACE,mat=mgray),'P01',flip=True)
boolean(shell,mesh('tool_cavity',corners(81.2,91.2,6.1),2.0,24.0))
boolean(shell,mesh('tool_bezel_pocket',corners(58.2,88.6,4.8),25.5,28,-11,0))
boolean(shell,rect('tool_window',44.4,58.8,23.8,28,-11,-4.9,.35))
boolean(shell,rect('tool_lens_recess',50.6,69.8,21.4,25.95,-11,-2,.25))
for x,y in CASE_SCREWS:
    boolean(shell,cyl('tool_case_boss',2.6,2.7,25.5,x,y),'UNION')
    boolean(shell,cyl('tool_case_pilot',1.05,2.3,16,x,y))
for x,y in LCD_HOLES:
    boolean(shell,cyl('tool_lcd_boss',2.30,21.5,25.5,x,y),'UNION')
    boolean(shell,cyl('tool_lcd_pilot',1.05,21.0,25.1,x,y))
for x,y in KEY_SCREWS:
    boolean(shell,cyl('tool_key_boss',2.2,18.8,25,x,y),'UNION')
    boolean(shell,cyl('tool_key_pilot',.85,18.0,23.8,x,y))
for kind,x,y,w,h in KEYS:
    if kind in ('up','down'):
        boolean(shell,mesh('tool_key',half_rocker(w+.6,h+.6,kind=='up'),23.8,28.5,x,y))
    else:
        boolean(shell,rect('tool_key',w+.6,h+.6,23.8,28.5,x,y,5.6 if kind=='confirm' else .9))
boolean(shell,rect('tool_power_slot',12.6,8,15.0,19.2,30,47,1.0))
# Central USB port, both width-centred and centred through the 27 mm body.
boolean(shell,side_rect('tool_usb_slot',10.2,4.8,-49,-44.9,0,13.5,2.0))
for x in (-8,8):
    boolean(shell,side_hole('tool_usb_M2',1.1,-48.5,-44.8,x,13.5))
    # 90 degree countersink for flush M2 flat-head mounting screws.
    tool=cone_z('tool_usb_countersink',1.1,2.2,46.9,48.1,x,0)
    tool.data.transform(Matrix.Translation(Vector((0,0,.0135))) @ Matrix.Rotation(math.pi/2,4,'X'))
    boolean(shell,tool)

bezel=part(mesh('P03_black_bezel',corners(57.6,88,4.5),25.65,26.85,-11,0,mblack),'P03',flip=True)
boolean(bezel,rect('tool_window',44.2,58.6,25.2,27.2,-11,-4.9,.35))
boolean(bezel,rect('tool_lens_relief',50.6,69.8,25.4,25.95,-11,-2,.25))
back=part(mesh('P02_rear_cover',corners(86,96,8.5),0,2.4,mat=mback),'P02')
lip=mesh('tool_register',corners(80.6,90.6,5.8),2.2,3.9)
boolean(lip,mesh('tool_lip_inside',corners(78.6,88.6,4.8),2,4.1))
for x,y in CASE_SCREWS:boolean(lip,cyl('tool_boss_relief',2.95,1.9,4.2,x,y))
boolean(back,lip,'UNION')
for x,y in CASE_SCREWS:
    boolean(back,cyl('tool_case_clearance',1.45,-.3,4.1,x,y))
    boolean(back,cyl('tool_head',2.65,-.2,1.6,x,y))
for x,y in TRAY_SCREWS:
    boolean(back,cyl('tool_tray_mount',2.6,2.1,4,x,y),'UNION')
    boolean(back,cyl('tool_pilot',1.05,1.15,4.2,x,y))
for y in (-15,-10,-5,0,5,10):
    boolean(back,rect('tool_vent',25,1.25,-.2,2.8,-16,y,.6))

# A thinner carrier preserves the full 14.5 mm board envelope below the keys.
carrier=part(rect('P04_key_carrier',21.2,79,17.6,18.8,29.8,4.5,1.3,mback),'P04')
boolean(carrier,rect('tool_corner_relief',3,6,14,22,40,43,.2))
for x,y in CASE_SCREWS:boolean(carrier,cyl('tool_boss_clearance',2.95,14,23,x,y))
for kind,x,y,w,h in KEYS:
    rim=rect('tool_tact_rim',7.8,7.8,18.6,19.9,x,y,.6)
    boolean(rim,rect('tool_tact_socket',6.4,6.4,18.4,20.2,x,y,.35))
    boolean(carrier,rim,'UNION')
    for dx in (-2.5,2.5):
        for dy in (-2.25,2.25):boolean(carrier,cyl('tool_pin',.65,17.2,20.1,x+dx,y+dy,n=24))
for x,y in KEY_SCREWS:boolean(carrier,cyl('tool_M2',1.1,17.2,20.1,x,y))
# Top switch is outside the main PCB end and remains reachable from the rear.
boolean(carrier,rect('tool_power_backstop',9,1.7,14.1,21.5,30,40.3,.4),'UNION')
for x in (26.4,33.6):
    boolean(carrier,rect('tool_power_side',1.2,4.5,14.1,21.5,x,42.2,.3),'UNION')
for i,(kind,x,y,w,h) in enumerate(KEYS):
    capw=w-.1;caph=h-.1
    rad=min(capw,caph)/2 if kind in ('up','down','confirm') else .8
    if kind in ('up','down'):
        ob=mesh('P%02d_key_%s'%(5+i,kind),half_rocker(capw,caph,kind=='up'),23.7,27.7,x,y,mkey)
    else:
        ob=rect('P%02d_key_%s'%(5+i,kind),capw,caph,23.7,27.7,x,y,rad,morange if kind=='confirm' else mkey)
    extra=.4 if kind in ('up','down') else 1.4
    boolean(ob,rect('tool_flange',capw+1.8,caph+extra,23.3,23.85,x,y,min(rad+.4,3)),'UNION')
    boolean(ob,cyl('tool_stem',1.4,23.2,24.1,x,y),'UNION')
    part(ob,'P%02d'%(5+i),flip=True)
power=rect('P09_top_key',12,3.1,15.6,18.6,30,47.25,1.1,mkey)
boolean(power,rect('tool_top_flange',14,.8,15.1,19.1,30,45.1,.3),'UNION')
boolean(power,rect('tool_top_stem',2,1.4,16.2,18,30,45.3,.3),'UNION')
part(power,'P09')

# Board shifted 12 mm upward in XY, leaving room for its internal right-angle USB plug.
tray=part(rect('P10_board_cradle',28.6,45,4,5.2,26.1,-1.5,1,mback),'P10')
for x,y in TRAY_SCREWS:
    boolean(tray,cyl('tool_ear',2.6,4,5.2,x,y),'UNION')
    boolean(tray,cyl('tool_tray_hole',1.35,3.7,5.7,x,y))
for y in (-18,12):
    for x in (14,37.8):
        boolean(tray,rect('tool_support',5 if x==14 else 4.6,10,5.0,9.3,x,y,.5),'UNION')
        sx,sw,hx=(13.65,3.3,14) if x==14 else (38.4,3.4,38)
        boolean(tray,rect('tool_hard_stop',sw,10,9.1,13.85,sx,y,.35),'UNION')
        boolean(tray,cyl('tool_pilot',.85,6.3,14.1,hx,y))
for x in (17.11,34.89):
    boolean(tray,rect('tool_bare_pin_channel',1.6,52,3.5,12.5,x,-7.8,.2))
keeper=part(rect('P11_board_keeper',4.4,10,13.85,15.05,14,-18,.4,mkey),'P11',4,True)
boolean(keeper,cyl('tool_M2',1.1,13.5,15.4,14,-18))
for x,y in ((14,12),(38,-18),(38,12)):
    ob=keeper.copy();ob.data=keeper.data;ob.name=P+'keeper_instance'
    ob.location=Vector(((x-14)*MM,(y+18)*MM,0));ob['instance_only']=True;prod.objects.link(ob)

coupon=part(rect('P12_fit_coupon',38,18,0,3,mat=mback),'P12')
for j,d in enumerate((2,2.1,2.2,2.3)):boolean(coupon,cyl('tool_pilot',d/2,-.2,3.4,-13+j*8.5,0))
coupon['fit_only']=True;coupon.location.x=.075;coupon.hide_render=True;coupon.hide_set(True)
usbtest=part(rect('P13_usb_fit_coupon',30,12,0,2.4,r=1,mat=mback),'P13')
boolean(usbtest,rect('tool_usb',10.2,4.8,-.3,2.7,r=2))
for x in (-8,8):
    boolean(usbtest,cyl('tool_M2',1.1,-.3,2.7,x,0))
    boolean(usbtest,cone_z('tool_countersink',2.2,1.1,-.1,1.1,x,0))
usbtest['fit_only']=True;usbtest.location.x=.110;usbtest.hide_render=True;usbtest.hide_set(True)

# LCD is rotated 180 degrees in-plane: connector at TOP clears central bottom USB boot.
lcd=ref(rect('REF_lcd_pcb',50,86,19.9,21.5,-11,0,.25,mpcb,refs))
for x,y in LCD_HOLES:boolean(lcd,cyl('tool_lcd_hole',1.6,19.5,21.9,x,y))
ref(rect('REF_lcd_stack',50,69.2,21.5,25.8,-11,-2,.2,mlcd,refs))
ref(rect('REF_lcd_header_housing',35.1,2.6,17.2,19.9,-11,41,.2,mlcd,refs))
for j in range(14):
    ref(rect('REF_lcd_pin',.65,.65,11.8,17.3,-27.51+j*2.54,41,.05,mgold,refs))
# Exact supplied total-height extremes: 25.8-11.8=14.0, 17.2-2.7=14.5.
ref(rect('REF_p4_pcb',21,71.05,12,13.6,26,1,.5,mpcb,refs))
ref(rect('REF_p4_chip',10.5,10.5,13.6,17.2,26,-3,.3,mlcd,refs))
ref(rect('REF_p4_c6_shield',12,14,13.6,16.3,26,22,.3,mmetal,refs))
ref(rect('REF_p4_antenna',18,8,13.6,14.2,26,32.2,.3,mlcd,refs))
ref(rect('REF_p4_usb_socket',9.1,7.3,13.6,16.8,26,-32.7,.8,mmetal,refs))
for x in (17.11,34.89):
    ref(rect('REF_gpio_housing',2.54,50.8,9.46,12,x,-7.8,.2,mlcd,refs))
    for j in range(20):ref(rect('REF_gpio_pin',.65,.65,2.7,9.46,x,-31.93+2.54*j,.04,mgold,refs))
ref(rect('REF_usb_right_angle_plug',10,9,10.8,16.8,26,-40.3,1,mlcd,refs))
ref(side_rect('REF_usb_panel_pcb',20,6.7,-45.6,-44.6,0,13.5,.15,mpcb,refs))
for x in (-8,8):boolean(bpy.data.objects[P+'REF_usb_panel_pcb'],side_hole('tool_hole',1.1,-46,-44,x,13.5))
ref(rect('REF_usb_boot_neck',11,6,9,18,0,-41.6,.5,mlcd,refs))
ref(rect('REF_usb_boot_30mm',14,24,9,18,0,-26.6,1,mlcd,refs))
for x in (-8,8):
    ref(side_rect('REF_usb_nut_keepout',4.6,4.6,-44.6,-42.6,x,13.5,.5,mmetal,refs))
socket=ref(side_rect('REF_usb_front_metal',9.4,3.6,-47.9,-40.5,0,13.5,1.6,mmetal,refs))
boolean(socket,side_rect('tool_socket_inside',7.9,2.3,-48.2,-41.3,0,13.5,.9))
for kind,x,y,w,h in KEYS:
    ref(rect('REF_tact_'+kind,6,6,18.8,22.3,x,y,.3,mlcd,refs))
    ref(cyl('REF_tact_plunger',1.6,22.3,23,x,y,mkey,refs))
root['max_physical_thickness_mm']=27.7
root['lcd_total_height_mm']=14.0
root['p4_total_height_mm']=14.5
root['usb_panel_dimensions_mm']='20 x 6.7; screw pitch 16; holes >=2; boot length 30 reserved'
root['wiring']='All hand-soldered. No Dupont female connector keepout.'
print(json.dumps({'scene':sc.name,'parts':len(PARTS),'body_mm':[86,96,27],
 'key_inclusive_thickness_mm':27.7,'lcd_total_height_mm':14,
 'p4_total_height_mm':14.5,'usb_center_xz_mm':[0,13.5],
 'lcd_connector':'TOP, rotate UI 180 degrees','pcb_y':1},ensure_ascii=False))
