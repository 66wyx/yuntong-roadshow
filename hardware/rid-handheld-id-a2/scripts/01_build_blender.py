"""ID-A2: continuous cubic-Bezier corners, CNC wrap shell, recessed printed inserts.
Execute as plain Python through Blender MCP. Helper dimensions are millimetres.
The two cubic segments per corner have zero endpoint curvature and a C2 midpoint.
This is an original iPhone-like curvature study, not recovered Apple CAD.
"""
import bpy
import math
from mathutils import Vector

BASE = 'C:/Users/YX/Documents/云台检测/hardware/rid-handheld-id-a2/'
P = 'RID_A2_'
existing = bpy.data.scenes.get('RID_ID_A2_Studio')
if existing and len(existing.objects):
    raise RuntimeError('A2 already exists. Modify named objects; do not overwrite it.')
scene = existing if existing else bpy.data.scenes.new('RID_ID_A2_Studio')
bpy.context.window.scene = scene
scene.unit_settings.system = next(i.identifier for i in scene.unit_settings.bl_rna.properties['system'].enum_items if i.identifier == 'METRIC')
scene.unit_settings.length_unit = 'MILLIMETERS'
scene.unit_settings.scale_length = 1
product = bpy.data.collections.new('ID-A2 | Product'); scene.collection.children.link(product)
studio = bpy.data.collections.new('ID-A2 | Studio'); scene.collection.children.link(studio)
construction = bpy.data.collections.new('ID-A2 | Construction'); scene.collection.children.link(construction)
root = bpy.data.objects.new(P+'Assembly', None); product.objects.link(root)
root['body_target_mm'] = '64 x 54 x 20; controls protrude separately'
root['status'] = 'Appearance review; PCB, battery, antenna, fit and manufacturing unvalidated'

def mat(name, color, metal=0, rough=.5, grain=0):
    m = bpy.data.materials.new(P+name); m.use_nodes = True
    p = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Metallic'].default_value = metal; p.inputs['Roughness'].default_value = rough
    m.diffuse_color = (*color, 1)
    if grain:
        coords = m.node_tree.nodes.new('ShaderNodeTexCoord')
        noise = m.node_tree.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 850
        noise.inputs['Detail'].default_value = 2
        m.node_tree.links.new(coords.outputs['Generated'], noise.inputs['Vector'])
        bump = m.node_tree.nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = .12; bump.inputs['Distance'].default_value = grain*.001
        m.node_tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
        m.node_tree.links.new(bump.outputs['Normal'], p.inputs['Normal'])
    return m

metal = mat('Natural_silver_anodized_CNC', (.57,.59,.60), .92, .29, .002)
edge = mat('Bright_satin_edge', (.68,.70,.72), .94, .2)
polymer = mat('Printed_warm_gray_insert', (.36,.365,.35), 0, .56, .006)
keymat = mat('Light_gray_keys', (.56,.57,.54), 0, .43, .003)
orange = mat('Orange_confirm', (.65,.10,.025), 0, .43, .003)
ink = mat('Charcoal_markings', (.023,.028,.026), 0, .6)
gasket = mat('Dark_shadow_gap', (.006,.009,.008), 0, .65)
glassmat = mat('AMOLED_black_glass', (.0015,.002,.0018), 0, .19)
gold = mat('Contact_gold', (.57,.34,.065), .8, .25)
fpcmat = mat('FPC_placement_proxy', (.16,.08,.022), .25, .48)

def mesh_obj(name, verts, faces, material, loc=(0,0,0), col=None):
    col = product if col is None else col
    me = bpy.data.meshes.new(P+name+'_mesh'); me.from_pydata(verts, [], faces); me.update()
    ob = bpy.data.objects.new(P+name, me); col.objects.link(ob)
    ob.location = tuple(v*.001 for v in loc)
    if col == product: ob.parent = root
    if material: me.materials.append(material)
    return ob

def prism(name, pts, depth, loc, material, col=None):
    n = len(pts)
    verts = [(x*.001,y*.001,z*.001) for z in (-depth/2,depth/2) for x,y in pts]
    faces = [tuple(reversed(range(n))), tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh_obj(name, verts, faces, material, loc, col)

def bezier(p0,p1,p2,p3,t):
    u = 1-t
    return tuple(u*u*u*p0[k]+3*u*u*t*p1[k]+3*u*t*t*p2[k]+t*t*t*p3[k] for k in (0,1))

def continuous_points(w,h,L,steps=32):
    # Clockwise top-right from (0,0) to (L,-L); reverse whole outline to CCW.
    first = ((0,0),(.28*L,0),(.64*L,0),(.82*L,-.18*L))
    second = (first[3],(L,-.36*L),(L,-.72*L),(L,-L))
    c = [bezier(*first,j/steps) for j in range(steps)]
    c += [bezier(*second,j/steps) for j in range(steps+1)]
    tr = [(w/2-L+x,h/2+y) for x,y in c]
    br = [(x,-y) for x,y in reversed(tr)]
    bl = [(-x,-y) for x,y in tr]
    tl = [(-x,y) for x,y in reversed(tr)]
    return list(reversed(tr+br+bl+tl))

def crr(name,w,h,d,L,loc,material):
    o = prism(name,continuous_points(w,h,L),d,loc,material)
    o['corner_definition'] = 'Two cubic segments per corner; G2 at straight, C2 at diagonal'
    o['corner_extent_mm'] = L
    return o

def rr(name,w,h,d,r,loc,material,steps=24):
    pts=[]
    for cx,cy,start in ((w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)):
        for j in range(steps+1):
            a=math.radians(start+90*j/steps);pts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
    return prism(name,pts,d,loc,material)

def cylinder(name,r,d,loc,material,n=96):
    return prism(name,[(r*math.cos(i*2*math.pi/n),r*math.sin(i*2*math.pi/n)) for i in range(n)],d,loc,material)

def boolean(obj,tool,operation='DIFFERENCE'):
    kind=next(i.identifier for i in bpy.types.Modifier.bl_rna.properties['type'].enum_items if i.identifier=='BOOLEAN')
    mod=obj.modifiers.new('Machined or printed feature',kind)
    mod.operation=next(i.identifier for i in mod.bl_rna.properties['operation'].enum_items if i.identifier==operation)
    mod.solver=next(i.identifier for i in mod.bl_rna.properties['solver'].enum_items if i.identifier=='EXACT');mod.object=tool
    bpy.context.view_layer.objects.active=obj;obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=mod.name);obj.select_set(False)
    bpy.data.objects.remove(tool,do_unlink=True)

def bevel(obj,width=.15,segments=4):
    kind=next(i.identifier for i in bpy.types.Modifier.bl_rna.properties['type'].enum_items if i.identifier=='BEVEL')
    m=obj.modifiers.new('Soft machined edge',kind);m.width=width*.001;m.segments=segments
    m.limit_method=next(i.identifier for i in m.bl_rna.properties['limit_method'].enum_items if i.identifier=='ANGLE')
    m.harden_normals=True
    return m

def finish(obj):
    for p in obj.data.polygons:p.use_smooth=abs(p.normal.z)<.95
    kind=next(i.identifier for i in bpy.types.Modifier.bl_rna.properties['type'].enum_items if i.identifier=='WEIGHTED_NORMAL')
    m=obj.modifiers.new('Face weighted normals',kind);m.keep_sharp=True;m.weight=40

def line(name,points,r,material):
    types=[i.identifier for i in bpy.types.BlendDataCurves.bl_rna.functions['new'].parameters['type'].enum_items]
    curve=bpy.data.curves.new(P+name,types[types.index('CURVE')])
    curve.dimensions=next(i.identifier for i in curve.bl_rna.properties['dimensions'].enum_items if i.identifier=='3D')
    curve.bevel_depth=r*.001;curve.bevel_resolution=3;curve.use_fill_caps=True
    kind=next(i.identifier for i in bpy.types.Spline.bl_rna.properties['type'].enum_items if i.identifier=='POLY')
    sp=curve.splines.new(kind);sp.points.add(len(points)-1)
    for p,co in zip(sp.points,points):p.co=(*[v*.001 for v in co],1)
    ob=bpy.data.objects.new(P+name,curve);product.objects.link(ob);ob.parent=root;curve.materials.append(material)
    return ob

font_ui=bpy.data.fonts.load('C:/Windows/Fonts/msyh.ttc')
font_mono=bpy.data.fonts.load('C:/Windows/Fonts/consola.ttf')
def label(name,body,size,loc,material=ink,font=font_mono,rot=(0,0,0)):
    kind=next(i.identifier for i in bpy.types.BlendDataCurves.bl_rna.functions['new'].parameters['type'].enum_items if i.identifier=='FONT')
    c=bpy.data.curves.new(P+name,kind);c.body=body;c.font=font;c.size=size*.001
    c.align_x=next(i.identifier for i in c.bl_rna.properties['align_x'].enum_items if i.identifier=='CENTER')
    c.extrude=.000002;c.resolution_u=12
    o=bpy.data.objects.new(P+name,c);product.objects.link(o);o.parent=root
    o.location=tuple(v*.001 for v in loc);o.rotation_euler=rot;c.materials.append(material)
    return o

# One load-bearing aluminum shell: continuous wall and integrated front lip.
shell=crr('CNC_wrap_shell',64,54,20,9.2,(0,0,0),metal)
boolean(shell,crr('cut_internal_cavity',60.4,50.4,20.4,7.4,(0,0,-1.5),None))
boolean(shell,crr('cut_front_opening',58.2,48.2,3.2,6.3,(0,0,9.4),None))
port=rr('cut_USB_C',11.4,4.8,6,2.1,(0,-26,0),None);port.rotation_euler.x=math.pi/2;boolean(shell,port)
port=rr('cut_power',9.3,3.1,5,1.2,(17.5,26.3,3.5),None);port.rotation_euler.x=math.pi/2;boolean(shell,port)
shell.data.materials.append(edge)
b=bevel(shell,.25,5);b.affect=next(i.identifier for i in b.bl_rna.properties['affect'].enum_items if i.identifier=='EDGES');b.material=1
finish(shell)
shell['material_process']='CNC aluminum shell, natural silver anodized, fine beadblast; bright edge'
shell['front_rim_nominal_mm']=2.9
shell['rear_opening']='Printed rear cover is inset inside the aluminum perimeter'

# Recessed printed face, retained by a narrow flange below the metal lip.
face=crr('Printed_front_insert',57.7,47.7,1.5,6.05,(0,0,8.9),polymer)
boolean(face,crr('printed_retaining_flange',59.8,49.8,.5,7.1,(0,0,8.15),polymer),'UNION')
boolean(face,rr('cut_glass_upper',36.9,36.9,4,1.75,(-8.8,.15,8.8),None))
boolean(face,rr('cut_glass_lower_seat',38.9,39.6,1.6,1.8,(-8.8,0,8.35),None))
boolean(face,rr('cut_rocker',11.1,18.6,4,5.5,(21.8,5.4,8.8),None))
boolean(face,cylinder('cut_confirm',5.61,4,(21.8,-11,8.8),None))
boolean(face,rr('cut_M',8,3.8,4,1.1,(21.8,-20.2,8.8),None))
for y in (16.6,-23):
    boolean(face,rr('cut_divider',16.2,.23,.25,.08,(21.6,y,9.64),None))
bevel(face,.065,3);finish(face)
face['front_surface_z_mm']=9.65
face['recess_below_metal_mm']=.35
face['production_note']='Minimum thin glass-locating lip requires process-specific fit review'

rear=crr('Printed_rear_insert',60,50,1.5,7.2,(0,0,-8.95),polymer)
for x in (-25,25):
    for y in (-20,20):
        boolean(rear,cylinder('cut_screw',.95,3,(x,y,-8.8),None))
        boolean(rear,cylinder('cut_screw_recess',1.65,.6,(x,y,-9.6),None))
for y in (-12,-14.2,-16.4):
    boolean(rear,rr('cut_rear_grip',32,.42,.35,.2,(0,y,-9.68),None))
bevel(rear,.12,4);finish(rear)
rear['inset_from_shell_back_mm']=.3

# AM200Q460460FLS1 geometry follows the QSPI drawing, not the MIPI variant.
back=rr('Display_assembly_back_envelope',37.88,39.08,.98,1.4,(-8.8,0,8.11),gasket)
back['note']='Combined non-glass layers envelope; not a detailed layer stack'
lower=rr('Display_lower_CG_38p5x39p2',38.5,39.2,.50,1.6,(-8.8,0,8.85),glassmat)
upper=rr('Display_upper_CG_36p5',36.5,36.5,.80,1.5,(-8.8,.15,9.50),glassmat)
for o in (back,lower,upper):bevel(o,.045,3);finish(o);o['display']='AM200Q460460FLS1 / QSPI'
lower['overall_assembly_nominal_mm']='38.50 x 39.20 x 2.28 (table); drawing thickness 2.26 +/- 0.20'
upper['AA_mm']='35.88 x 35.88; 460 x 460 px'
for variant in ('height','radar'):
    im=bpy.data.images.load(BASE+'assets/screen-'+variant+'-460.png',check_existing=True);im.pack()
    m=mat('Screen_'+variant,(.01,.01,.01),0,.24)
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Emission Strength'].default_value=1.0;p.inputs['Specular IOR Level'].default_value=.06;p.inputs['Coat Weight'].default_value=.02
    tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im
    m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);m.node_tree.links.new(tex.outputs['Color'],p.inputs['Emission Color'])
    panel=rr('Screen_'+variant,35.88,35.88,.012,.9,(-8.8,.15,9.912),m)
    uv=panel.data.uv_layers.new(name='Native_square_UV')
    for poly in panel.data.polygons:
        for i in poly.loop_indices:
            co=panel.data.vertices[panel.data.loops[i].vertex_index].co
            uv.data[i].uv=(co.x/.03588+.5,co.y/.03588+.5)
    panel.hide_render=variant!='height';panel.hide_set(variant!='height')
    panel['data_status']='DEMO artwork; height and direction are not measured'

# Folded flex placement proxy, deliberately labeled rather than treated as routing CAD.
fpc=rr('Display_folded_FPC_proxy',30,10,.22,.4,(-8.8,-13,7.44),fpcmat)
fpc['status']='Illustrative folded-flex keep-out. Supplier fold radius and component heights pending.'
fpc=rr('Display_FPC_tail_proxy',4,22,.16,.3,(-8.8,1,7.4),fpcmat)
fpc['status']='Placement proxy, not production flex geometry'

# Original control vocabulary, proportioned for the new square screen.
seat=rr('Rocker_dark_seat',10.95,18.45,.5,5.4,(21.8,5.4,9.3),gasket);bevel(seat,.10,3)
def rocker(name,cy,down=False):
    w,h=10.4,8.8;r=w/2;ay=h/2-r
    pts=[(-r,-h/2),(r,-h/2)]+[(r*math.cos(math.pi*j/64),ay+r*math.sin(math.pi*j/64)) for j in range(65)]
    if down:pts=[(-x,-y) for x,y in pts]
    o=prism(name,pts,1.4,(21.8,cy,10.08),keymat);bevel(o,.23,5);finish(o)
rocker('Rocker_upper',9.95)
rocker('Rocker_lower',.85,True)
line('Up_chevron',[(20.5,9.6,10.79),(21.8,10.9,10.79),(23.1,9.6,10.79)],.17,ink)
line('Down_chevron',[(20.5,1.25,10.79),(21.8,-.05,10.79),(23.1,1.25,10.79)],.17,ink)
seat=cylinder('Confirm_dark_seat',5.5,.45,(21.8,-11,9.5),gasket);bevel(seat,.10,3)
key=cylinder('Orange_confirm_key',5.25,1.45,(21.8,-11,10.12),orange);bevel(key,.23,5);finish(key)
line('Confirm_check',[(20.25,-11.2,10.852),(21.35,-12.55,10.852),(23.7,-8.95,10.852)],.18,ink)
for radius,name in ((4.83,'outer'),(4.55,'inner')):
    line('Confirm_'+name+'_score',[(21.8+radius*math.cos(i*2*math.pi/192),-11+radius*math.sin(i*2*math.pi/192),10.849) for i in range(193)],.023,ink)
for i in range(80):
    a=i*math.pi*2/80
    line('Confirm_radial_tick_'+str(i).zfill(2),[(21.8+r*math.cos(a),-11+r*math.sin(a),10.851) for r in (4.73,4.91)],.022,ink)
seat=rr('M_dark_seat',7.85,3.65,.4,1,(21.8,-20.2,9.35),gasket)
key=rr('M_key',7.5,3.3,.7,.85,(21.8,-20.2,9.75),keymat);bevel(key,.12,3);finish(key)
label('M_legend','M',1.65,(21.8,-20.76,10.105))
for row,xs in enumerate(((-2.4,-.8,.8,2.4),(-1.6,0,1.6))):
    for j,dx in enumerate(xs):
        rr('Checker_'+str(row)+'_'+str(j),.85,.85,.02,.025,(21.8+dx,21.7-row*.96,9.665),orange if row==1 and j==0 else ink)
label('AIRSPACE','A I R S P A C E',.67,(21.8,18.8,9.67))
label('Yuntong_on_metal','云瞳',1.9,(21.8,-25.6,10.014),font=font_ui)

usb=rr('USB_C_metal_shell',9,3.3,4.8,1.55,(0,-24.0,0),edge)
boolean(usb,rr('cut_USB_inner',8.24,2.58,5.5,1.22,(0,-24.0,0),None))
usb.rotation_euler.x=math.pi/2;bevel(usb,.075,3);finish(usb)
tongue=rr('USB_C_tongue',6.25,.67,2.25,.2,(0,-24.6,0),gasket);tongue.rotation_euler.x=math.pi/2;bevel(tongue,.07,3)
for i in range(12):
    for sign in (-1,1):
        c=rr('USB_contact_'+str(i)+'_'+str(sign),.18,.03,1.1,.01,((i-5.5)*.43,-25.25,sign*.35),gold);c.rotation_euler.x=math.pi/2
label('USB_C_legend','USB-C  /  5V',.85,(0,-27.012,4),rot=(math.pi/2,0,0))
pk=rr('Top_power_button',8.6,2.6,1.9,1.1,(17.5,26.7,3.5),keymat);pk.rotation_euler.x=math.pi/2;bevel(pk,.18,4);finish(pk)
label('Power_symbol','I',.95,(17.5,27.665,3.15),rot=(-math.pi/2,0,0))

label('Rear_brand','Y U N T O N G',1.8,(0,9,-9.708),rot=(0,math.pi,0))
label('Rear_model','RID  /  ID-A2',1.05,(0,5.8,-9.708),rot=(0,math.pi,0))
label('Rear_note','CNC SHELL  /  PRINTED INSERT',.62,(0,-21,-9.708),rot=(0,math.pi,0))
for x in (-25,25):
    for y in (-20,20):
        screw=cylinder('Rear_screw_'+str(x)+'_'+str(y),1.36,.4,(x,y,-9.38),metal,64);bevel(screw,.07,3);finish(screw)
        pts=[]
        for i in range(60):
            a=2*math.pi*i/60;r=.5+.09*math.cos(6*a);pts.append((x+r*math.cos(a),y+r*math.sin(a),-9.585))
        mesh_obj('Rear_screw_drive_'+str(x)+'_'+str(y),[tuple(v*.001 for v in p) for p in pts],[tuple(reversed(range(60)))],ink)

# Exact Bezier handles preserved in a hidden construction curve for editability.
kind=next(i.identifier for i in bpy.types.BlendDataCurves.bl_rna.functions['new'].parameters['type'].enum_items if i.identifier=='CURVE')
c=bpy.data.curves.new(P+'Cubic_corner_control_path',kind)
c.dimensions=next(i.identifier for i in c.bl_rna.properties['dimensions'].enum_items if i.identifier=='2D')
sp=c.splines.new(next(i.identifier for i in bpy.types.Spline.bl_rna.properties['type'].enum_items if i.identifier=='BEZIER'));sp.bezier_points.add(2)
L=9.2
nodes=[((0,0),(0,0),(.28*L,0)),((.82*L,-.18*L),(.64*L,0),(L,-.36*L)),((L,-L),(L,-.72*L),(L,-L))]
for bp,(co,hl,hr) in zip(sp.bezier_points,nodes):
    free=next(i.identifier for i in bp.bl_rna.properties['handle_left_type'].enum_items if i.identifier=='FREE')
    bp.handle_left_type=free;bp.handle_right_type=free
    bp.co=(co[0]*.001,co[1]*.001,0);bp.handle_left=(hl[0]*.001,hl[1]*.001,0);bp.handle_right=(hr[0]*.001,hr[1]*.001,0)
ob=bpy.data.objects.new(P+'Cubic_corner_control_path',c);construction.objects.link(ob)
ob.location=((32-L)*.001,.027,.01);ob.hide_render=True;ob.hide_set(True)
ob['note']='Exact editable two-segment cubic; body mesh is a sampled visual realization'

for name in ('reference-original.png','reference-rid.png','reference-metal-wrap.png'):
    im=bpy.data.images.load(BASE+'assets/'+name,check_existing=True);im.use_fake_user=True;im.pack()
scene['screen_source']='references/AM200Q460460FLS1.pdf; table p3, dimension drawing p4'
scene['design_scope']='64 x 54 x 20 mm ID target. Not a manufacturing or RF release.'
scene['corner_spec']='Original G2-to-line, C2-between-cubics construction. No official Apple dimensions claimed.'
scene['antenna_note']='Printed face and back are potential RF windows; antenna placement and aluminum interaction unvalidated.'
print('A2_BUILD_OK',len(product.objects),'objects. Previous A1 scene retained.')
