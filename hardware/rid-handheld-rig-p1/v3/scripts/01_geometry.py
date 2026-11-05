"""Run through Blender MCP. Millimetre inputs, metre scene, isolated V3 scene.

Hardware basis: photo-identified Waveshare ESP32-P4-WIFI6-M, 71.05 x 21,
and LCDWiki MSP2834. The latter drawing locates lens/VA/AA 6.40/9.14/9.30
below the PCB top. Geometry is a first physical fit prototype.
"""
import bpy
import bmesh
import math
import json
from mathutils import Vector, Matrix

OUT = 'C:/Users/YX/Documents/云台检测/hardware/rid-handheld-rig-p1/v3/'
P = 'RIG3_'
if bpy.data.scenes.get('RIG_P1_V3_Print'):
    raise RuntimeError('V3 exists. Inspect and edit its objects instead of overwriting it.')
sc = bpy.data.scenes.new('RIG_P1_V3_Print')
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
root['body_mm'] = '86 x 96 x 32'
root['status'] = 'First fit prototype; photo-identified narrow P4-WIFI6-M board'
root['hardware'] = 'MSP2834 + Waveshare ESP32-P4-WIFI6-M; no battery size supplied'
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

CASE_SCREWS=[(-39.0,-30),(-39.0,30),(39.8,-40),(39.8,40)]
LCD_HOLES=[(-33,40),(11,40),(-33,-36.08),(11,-36.08)]
TRAY_SCREWS=[(13.0,-22),(37.7,-22),(13.0,3),(37.7,3)]
KEY_SCREWS=[(21.2,-33),(38.0,-33),(21.2,30),(38.0,30)]

# Front shell: rear opening at z2.7, face at z32, 2.4 mm perimeter wall.
shell=part(mesh('P01_front_shell',corners(86,96,8.5),2.7,32,mat=mgray),'P01',flip=True)
boolean(shell,mesh('tool_cavity',corners(81.2,91.2,6.1),2.0,29.0))
boolean(shell,mesh('tool_insert_pocket',corners(58.2,88.6,4.8),30.5,33,-11,0))
boolean(shell,rect('tool_window',44.4,58.8,28.8,33,-11,4.9,.35))
boolean(shell,rect('tool_lens_recess',50.6,69.8,26.4,30.95,-11,2,.25))

for i,(x,y) in enumerate(CASE_SCREWS):
    boolean(shell,cyl('tool_case_boss',2.6,2.7,30.5,x,y), 'UNION')
    boolean(shell,cyl('tool_case_pilot',1.05,2.3,16.0,x,y))

for x,y in LCD_HOLES:
    boolean(shell,cyl('tool_lcd_boss',2.30,26.5,30.5,x,y),'UNION')
    boolean(shell,cyl('tool_lcd_pilot',1.05,26.0,30.1,x,y))

for x,y in KEY_SCREWS:
    boolean(shell,cyl('tool_key_boss',2.20,23.5,30.0,x,y),'UNION')
    boolean(shell,cyl('tool_key_pilot',.85,22.7,28.1,x,y))

# Front control apertures, with rear-retained caps.
KEYS=[('up',30,16.75,11.2,10.9),('down',30,5.25,11.2,10.9),
      ('confirm',30,-14,11.2,11.2),('mode',30,-25.5,8.4,4.2)]
for kind,x,y,w,h in KEYS:
    rad=5.4 if kind in ('up','down') else 5.6 if kind=='confirm' else .9
    if kind in ('up','down'):
        boolean(shell,mesh('tool_keyhole',half_rocker(w+.6,h+.6,kind=='up'),28.8,33.5,x,y))
    else:
        boolean(shell,rect('tool_keyhole',w+.6,h+.6,28.8,33.5,x,y,rad))
boolean(shell,rect('tool_power_aperture',12.6,8,20.0,24.2,30,47,1.0))
# USB port follows the photographed board, direct bottom cable access.
boolean(shell,rect('tool_usb',13.4,10.0,12.6,20.6,26,-47.0,1.0))
boolean(shell,rect('tool_board_edge_pocket',22,4.0,12.6,15.1,26,-45.2,.4))

bezel=part(mesh('P03_black_bezel',corners(57.6,88.0,4.5),30.65,31.85,-11,0,mblack),
           'P03',flip=True)
boolean(bezel,rect('tool_bezel_window',44.2,58.6,30.2,32.2,-11,4.9,.35))
boolean(bezel,rect('tool_bezel_lens_relief',50.6,69.8,30.4,30.95,-11,2,.25))

# Back with register lip, screw countersinks, board-cradle bosses and ventilation.
back=part(mesh('P02_rear_cover',corners(86,96,8.5),0,2.4,mat=mback),'P02')
lip=mesh('tool_register',corners(80.6,90.6,5.8),2.2,3.9)
boolean(lip,mesh('tool_lip_inside',corners(78.6,88.6,4.8),2.0,4.1))
for x,y in CASE_SCREWS:
    boolean(lip,cyl('tool_lip_boss_relief',2.95,1.9,4.2,x,y))
boolean(back,lip,'UNION')
for x,y in CASE_SCREWS:
    boolean(back,cyl('tool_case_clearance',1.45,-.3,4.1,x,y))
    # Counterbore for a low-head M2.5 screw, accessible from the rear.
    boolean(back,cyl('tool_case_counterbore',2.65,-.2,1.1,x,y))
for x,y in TRAY_SCREWS:
    boolean(back,cyl('tool_tray_mount',2.6,2.1,4.0,x,y),'UNION')
    boolean(back,cyl('tool_tray_pilot',1.05,1.15,4.2,x,y))
for y in (-15,-10,-5,0,5,10):
    boolean(back,rect('tool_vent',25,1.25,-.2,2.8,-16,y,.6))
for y in (-39.5,-33.5):
    boolean(back,cyl('tool_service',1.7,-.2,2.8,21.5,y))

# Four front switch pockets, plate fastened to dedicated face posts.
carrier=part(rect('P04_key_carrier',21.2,79.0,21.9,23.5,29.8,4.5,1.3,mback),'P04')
boolean(carrier,rect('tool_cavity_corner_relief',3,6,19,27,40,43,.2))
for x,y in CASE_SCREWS:
    boolean(carrier,cyl('tool_case_boss_clearance',2.95,19,27,x,y))
for kind,x,y,w,h in KEYS:
    # Locating rim around a 6x6 tact body. Body rests on the plate at z23.5.
    rim=rect('tool_tact_rim',7.8,7.8,23.3,24.6,x,y,.6)
    boolean(rim,rect('tool_tact_socket',6.4,6.4,23.0,24.9,x,y,.35))
    boolean(carrier,rim,'UNION')
    for dx in (-2.5,2.5):
        for dy in (-2.25,2.25):
            boolean(carrier,cyl('tool_wire_or_pin',.65,21.5,24.8,x+dx,y+dy,n=24))
for x,y in KEY_SCREWS:
    boolean(carrier,cyl('tool_carrier_clearance',1.1,21.5,24.8,x,y))
# Power tact cradle, oriented toward the top edge.
boolean(carrier,rect('tool_power_backstop',9,1.7,19.1,26.5,30,40.3,.4),'UNION')
for x in (26.4,33.6):
    boolean(carrier,rect('tool_power_side',1.2,4.5,19.1,26.5,x,42.2,.3),'UNION')

for i,(kind,x,y,w,h) in enumerate(KEYS):
    capw=w-.10; caph=h-.10
    rad=min(capw,caph)/2 if kind in ('up','down','confirm') else .8
    if kind in ('up','down'):
        ob=mesh('P%02d_key_%s'%(5+i,kind),half_rocker(capw,caph,kind=='up'),28.7,32.7,x,y,mkey)
    else:
        ob=rect('P%02d_key_%s'%(5+i,kind),capw,caph,28.7,32.7,x,y,rad,morange if kind=='confirm' else mkey)
    flange_extra=.4 if kind in ('up','down') else 1.4
    boolean(ob,rect('tool_key_flange',capw+1.8,caph+flange_extra,28.3,28.85,x,y,min(rad+.4,3)),'UNION')
    boolean(ob,cyl('tool_key_stem',1.4,27.9,29.1,x,y),'UNION')
    part(ob,'P%02d'%(5+i),flip=True)

# Top cap, retained by an internal flange and driving the fifth tact.
power=rect('P09_top_key',12,3.1,20.6,23.6,30,47.25,1.1,mkey)
boolean(power,rect('tool_power_flange',14.0,.8,20.1,24.1,30,45.1,.3),'UNION')
boolean(power,rect('tool_power_stem',2,1.4,21.2,23.0,30,45.3,.3),'UNION')
part(power,'P09')

# Slender WIFI6-M cradle. Board is held at edge lands without relying on holes.
tray=part(rect('P10_board_cradle',28.6,45.0,4.0,5.6,26.1,-13.5,1.0,mback),'P10')
for x,y in TRAY_SCREWS:
    # Ears tie the custom cradle into the back cover.
    boolean(tray,cyl('tool_tray_ear',2.6,4.0,5.6,x,y),'UNION')
    boolean(tray,cyl('tool_tray_clearance',1.35,3.7,6.0,x,y))
for y in (-30.0,0.0):
    for x in (14.0,37.8):
        width=5.0 if x==14.0 else 4.6
        boolean(tray,rect('tool_cradle_pillar',width,10,5.4,10.3,x,y,.5),'UNION')
        # The narrower upper step avoids the GPIO housing and supports the
        # keeper at its screw, so tightening cannot bow it across an air gap.
        step_x,step_w,screw_x=(13.65,3.3,14.0) if x==14.0 else (38.4,3.4,38.0)
        boolean(tray,rect('tool_keeper_step',step_w,10,10.1,14.85,step_x,y,.35),'UNION')
        boolean(tray,cyl('tool_keeper_pilot',.85,6.3,15.0,screw_x,y))
for x in (17.11,34.89):
    boolean(tray,rect('tool_header_channel',1.6,52,3.5,13.5,x,-19.8,.2))
keeper=part(rect('P11_board_keeper',4.4,10,14.85,16.25,14,-30,.4,mkey),'P11',4,True)
boolean(keeper,cyl('tool_keeper_hole',1.1,14.5,16.5,14.0,-30))
# Render-only instances of the same four keepers.
for x,y in ((14,0),(38.0,-30),(38.0,0)):
    cp=keeper.copy(); cp.data=keeper.data
    cp.name=P+'keeper_instance'
    cp.location=Vector(((x-14)*MM,(y+30)*MM,0))
    cp['instance_only']=True
    prod.objects.link(cp)

# Fit coupon with pilot-hole ladder and the screen-PCB support land.
coupon=part(rect('P12_fit_coupon',38,18,0,3,mat=mback),'P12')
for j,d in enumerate((2.0,2.1,2.2,2.3)):
    boolean(coupon,cyl('tool_coupon_pilot',d/2,-.2,3.4,-13+j*8.5,0))
coupon.location=Vector((.075,0,0))
coupon.hide_render=True
coupon.hide_set(True)

# Actual hardware reference envelopes, with no print selection tags.
lcdpcb=ref(rect('REF_lcd_pcb',50,86,24.9,26.5,-11,0,.25,mpcb,refs))
for x,y in LCD_HOLES:
    boolean(lcdpcb,cyl('tool_lcd_hole',1.6,24.5,26.9,x,y))
ref(rect('REF_lcd_stack',50,69.2,26.5,30.8,-11,2,.2,mlcd,refs))
ref(rect('REF_header_housing',35.1,2.6,22.2,24.9,-11,-41,.2,mlcd,refs))
for j in range(14):
    ref(rect('REF_lcd_pin',.65,.65,16.52,22.3,-27.51+j*2.54,-41,.05,mgold,refs))
ref(rect('REF_lcd_dupont_keepout',36,8,7.52,16.5,-11,-41,1,mlcd,refs))
board=ref(rect('REF_p4_pcb',21,71.05,13,14.6,26,-11,.5,mpcb,refs))
ref(rect('REF_p4_chip',10.5,10.5,14.6,16.6,26,-15,.3,mlcd,refs))
ref(rect('REF_p4_c6_shield',12,14,14.6,17.3,26,10,.3,mmetal,refs))
ref(rect('REF_p4_antenna',18,8,14.6,15.2,26,20.2,.3,mlcd,refs))
ref(rect('REF_usb_socket',9.1,7.3,14.6,17.8,26,-44.7,.8,mmetal,refs))
for x in (17.11,34.89):
    ref(rect('REF_gpio_housing',2.54,50.8,10.46,13,x,-19.8,.2,mlcd,refs))
    for j in range(20):
        ref(rect('REF_gpio_pin',.65,.65,4.46,10.46,x,-43.93+2.54*j,.04,mgold,refs))

# Preview-only tact references positioned in the four seats.
for kind,x,y,w,h in KEYS:
    ref(rect('REF_tact_'+kind,6,6,23.5,27.0,x,y,.3,mlcd,refs))
    ref(cyl('REF_tact_plunger',1.6,27,27.7,x,y,mkey,refs))

print(json.dumps({'scene':sc.name,'parts':[ob.name for ob in PARTS],
                  'body_mm':[86,96,32],'board':'WIFI6-M 71.05 x 21',
                  'screen_pcb':[-11,0],'lcd_holes':LCD_HOLES,
                  'screen_AA_centre':[-11,4.9], 'screen_front_z':30.8,
                  'header_end_z':16.52,'dupont_keepout_end_z':7.52},ensure_ascii=False))
