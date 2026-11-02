"""Run as plain code through Blender MCP. All geometry is created in a new named scene.
Dimensions are metres in Blender; helpers accept millimetres. No external scene is cleared.
"""
import bpy
import math
from mathutils import Vector

BASE='C:/Users/YX/Documents/云台检测/hardware/rid-handheld-id-a1/'
PREFIX='RID_A1_'
existing=bpy.data.scenes.get('RID_ID_A1_Studio')
if existing and len(existing.objects):
    raise RuntimeError('ID scene already exists; edit its named objects rather than rebuilding over it.')
scene=existing if existing else bpy.data.scenes.new('RID_ID_A1_Studio')
bpy.context.window.scene=scene
scene.unit_settings.system=next(i.identifier for i in scene.unit_settings.bl_rna.properties['system'].enum_items if i.identifier=='METRIC')
# Dynamic enum verified from this Blender build's assignment diagnostic; RNA returns DEFAULT only.
scene.unit_settings.length_unit='MILLIMETERS'
scene.unit_settings.scale_length=1
assembly=bpy.data.collections.new('ID-A1 | Product');scene.collection.children.link(assembly)
studio=bpy.data.collections.new('ID-A1 | Studio');scene.collection.children.link(studio)
root=bpy.data.objects.new(PREFIX+'Assembly',None);assembly.objects.link(root)
root['design_status']='Appearance study. Hardware fit and RF are not validated.'
root['body_mm']='82 x 86 x 20'

def mat(name,color,metal=0,rough=.5,grain=0):
    m=bpy.data.materials.new(PREFIX+name);m.use_nodes=True
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    if grain:
        coords=m.node_tree.nodes.new('ShaderNodeTexCoord')
        n=m.node_tree.nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=780
        n.inputs['Detail'].default_value=2.0;n.inputs['Roughness'].default_value=.65
        m.node_tree.links.new(coords.outputs['Generated'],n.inputs['Vector'])
        bump=m.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.19
        bump.inputs['Distance'].default_value=grain*.001
        m.node_tree.links.new(n.outputs['Fac'],bump.inputs['Height']);m.node_tree.links.new(bump.outputs['Normal'],p.inputs['Normal'])
        ramp=m.node_tree.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position=.2;ramp.color_ramp.elements[0].color=(*[c*.88 for c in color],1)
        ramp.color_ramp.elements[1].position=.8;ramp.color_ramp.elements[1].color=(*[min(c*1.08,1) for c in color],1)
        m.node_tree.links.new(n.outputs['Fac'],ramp.inputs['Fac']);m.node_tree.links.new(ramp.outputs['Color'],p.inputs['Base Color'])
    return m

polymer=mat('Printed_polymer_fine_gray',(.315,.307,.285),0,.59,.009)
aluminum=mat('CNC_Al_gray_beadblast',(.33,.345,.337),.82,.34,.003)
chamfer=mat('CNC_edge_satin_bright',(.54,.55,.53),.88,.25)
gasket=mat('Charcoal_shadow_gasket',(.009,.012,.010),0,.69)
orange=mat('Orange_key_fine_matte',(.72,.185,.058),0,.46,.004)
orange_ink=mat('Orange_index_inlay',(.67,.14,.035),0,.5)
keymat=mat('Rocker_warm_light_gray',(.52,.51,.477),0,.48,.004)
ink=mat('Printed_charcoal_graphics',(.028,.033,.027),0,.64)
glassmat=mat('Black_smoked_cover_glass',(.002,.003,.0025),0,.19)
usbmetal=mat('USB_connector_shell',(.5,.53,.51),.88,.26)
gold=mat('Contact_gold',(.57,.34,.065),.8,.25)
internal=mat('Internal_RF_window_marker',(.08,.22,.16),0,.6)

def mesh_obj(name,verts,faces,material,loc=(0,0,0),collection=assembly):
    mesh=bpy.data.meshes.new(PREFIX+name+'_mesh');mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(PREFIX+name,mesh);collection.objects.link(obj)
    obj.location=tuple(v*.001 for v in loc)
    if collection==assembly:obj.parent=root
    if material:mesh.materials.append(material)
    return obj

def rr(name,w,h,d,r,loc,material,steps=24):
    pts=[]
    for cx,cy,start in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
        for j in range(steps+1):
            a=math.radians(start+90*j/steps);pts.append(((cx+r*math.cos(a))*.001,(cy+r*math.sin(a))*.001))
    n=len(pts);verts=[(x,y,z*.001) for z in (-d/2,d/2) for x,y in pts]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    return mesh_obj(name,verts,faces,material,loc)

def cylinder(name,r,d,loc,material,n=128):
    pts=[(r*.001*math.cos(i*2*math.pi/n),r*.001*math.sin(i*2*math.pi/n)) for i in range(n)]
    verts=[(x,y,z*.001) for z in (-d/2,d/2) for x,y in pts]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    return mesh_obj(name,verts,faces,material,loc)

def bevel(obj,width=.15,segments=4,apply=False):
    kind=next(i.identifier for i in bpy.types.Modifier.bl_rna.properties['type'].enum_items if i.identifier=='BEVEL')
    m=obj.modifiers.new('Precision edge radius',kind);m.width=width*.001;m.segments=segments
    m.limit_method=next(i.identifier for i in m.bl_rna.properties['limit_method'].enum_items if i.identifier=='ANGLE')
    m.harden_normals=True
    if apply:
        bpy.context.view_layer.objects.active=obj;obj.select_set(True);bpy.ops.object.modifier_apply(modifier=m.name);obj.select_set(False)
    return m

def cut(obj,cutter):
    kind=next(i.identifier for i in bpy.types.Modifier.bl_rna.properties['type'].enum_items if i.identifier=='BOOLEAN')
    mod=obj.modifiers.new('Machined opening',kind)
    mod.operation=next(i.identifier for i in mod.bl_rna.properties['operation'].enum_items if i.identifier=='DIFFERENCE')
    mod.solver=next(i.identifier for i in mod.bl_rna.properties['solver'].enum_items if i.identifier=='EXACT');mod.object=cutter
    bpy.context.view_layer.objects.active=obj;obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=mod.name);obj.select_set(False)
    bpy.data.objects.remove(cutter,do_unlink=True)

def finish(obj):
    for p in obj.data.polygons:p.use_smooth=abs(p.normal.z)<.95
    kinds=[i.identifier for i in bpy.types.Modifier.bl_rna.properties['type'].enum_items]
    if 'WEIGHTED_NORMAL' in kinds:
        m=obj.modifiers.new('Face-weighted normals',kinds[kinds.index('WEIGHTED_NORMAL')]);m.keep_sharp=True;m.weight=40

def line_obj(name,points,r,material):
    types=[i.identifier for i in bpy.types.BlendDataCurves.bl_rna.functions['new'].parameters['type'].enum_items]
    curve=bpy.data.curves.new(PREFIX+name,types[types.index('CURVE')])
    curve.dimensions=next(i.identifier for i in curve.bl_rna.properties['dimensions'].enum_items if i.identifier=='3D')
    curve.resolution_u=12;curve.bevel_depth=r*.001;curve.bevel_resolution=4;curve.use_fill_caps=True
    types=[i.identifier for i in bpy.types.Spline.bl_rna.properties['type'].enum_items]
    sp=curve.splines.new(types[types.index('POLY')]);sp.points.add(len(points)-1)
    for p,co in zip(sp.points,points):p.co=(*[v*.001 for v in co],1)
    obj=bpy.data.objects.new(PREFIX+name,curve);assembly.objects.link(obj);obj.parent=root;curve.materials.append(material)
    return obj

# Three separately modeled structural parts: polymer front, CNC ring, polymer back.
mid=rr('CNC_midframe',81.8,85.8,12,5.9,(0,0,0),aluminum)
cut(mid,rr('cut_mid_cavity',77,81,15,3.5,(0,0,0),None))
port=rr('cut_USB_C',11.4,4.8,7,2.1,(0,-42,0),None);port.rotation_euler.x=math.pi/2;cut(mid,port)
power=rr('cut_top_power',11.6,3.2,6,1.1,(30,42,3.5),None);power.rotation_euler.x=math.pi/2;cut(mid,power)
bevel(mid,.24,4);finish(mid);mid['manufacturing']='CNC aluminum midframe; tooling not released'

front=rr('Printed_front_cover',82,86,3.75,6,(0,0,8.125),polymer)
bevel(front,.48,6,True)
cut(front,rr('cut_front_cavity',78,82,3.3,4,(0,0,6.8),None))
cut(front,rr('cut_glass_seat',56.95,81.15,1.0,3.25,(-10,0,9.85),None))
cut(front,rr('cut_display_through',55.9,80.1,4.3,2.8,(-10,0,8.1),None))
cut(front,rr('cut_rocker',11.65,22.85,4.5,5.7,(30,7.5,8.4),None))
cut(front,cylinder('cut_confirm',5.84,4.6,(30,-13.4,8.4),None))
cut(front,rr('cut_M_key',8.5,4.3,4.4,1.15,(30,-23.5,8.4),None))
for y in (26.9,-27.2):
    cut(front,rr('cut_face_divider',24,.28,.36,.09,(30,y,9.98),None))
bevel(front,.075,3);finish(front);front['manufacturing']='3D printed polymer with fine matte finish'

rear=rr('Printed_rear_cover',82,86,3.75,6,(0,0,-8.125),polymer)
bevel(rear,.65,7,True)
cut(rear,rr('cut_rear_cavity',78,82,3.4,4,(0,0,-6.6),None))
for x in (-35.5,35.5):
    for y in (-37.5,37.5):
        cut(rear,cylinder('cut_rear_screw',1.15,5,(x,y,-8),None,64))
        cut(rear,cylinder('cut_head_recess',2.1,1.3,(x,y,-9.75),None,64))
for y in (-22,-19.7,-17.4):
    cut(rear,rr('cut_rear_grip',44,.6,.5,.28,(0,y,-10.05),None))
bevel(rear,.07,3);finish(rear);rear['manufacturing']='3D printed polymer; concealed recessed fasteners'

# Dark interfaces are visible shadow gaps, not excessive decorative bands.
for z,label in [(6.12,'front'),(-6.12,'rear')]:
    seam=rr(label+'_interface_seal',81.15,85.15,.22,5.65,(0,0,z),gasket)
    cut(seam,rr('cut_seal',77.5,81.5,.8,3.85,(0,0,z),None));finish(seam)
for z,label in [(5.81,'upper'),(-5.81,'lower')]:
    rim=rr('CNC_'+label+'_edge',81.78,85.78,.16,5.89,(0,0,z),chamfer)
    cut(rim,rr('cut_rim',81.25,85.25,.8,5.62,(0,0,z),None));bevel(rim,.045,2);finish(rim)

rim=rr('Glass_perimeter_gasket',56.85,81.05,.55,3.2,(-10,0,9.57),gasket)
cut(rim,rr('cut_glass_gasket',56.38,80.58,1.1,2.99,(-10,0,9.57),None))
glass=rr('Front_black_glass',56.4,80.6,.8,3,(-10,0,9.85),glassmat);bevel(glass,.16,5);finish(glass)
for variant in ('height','radar','reference'):
    im=bpy.data.images.load(BASE+'assets/screen-'+variant+'.png',check_existing=True)
    im.pack()
    m=bpy.data.materials.new(PREFIX+'Screen_'+variant);m.use_nodes=True
    p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Roughness'].default_value=.24
    p.inputs['Coat Weight'].default_value=.22;p.inputs['Coat Roughness'].default_value=.2
    p.inputs['Emission Strength'].default_value=.45
    tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im
    m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);m.node_tree.links.new(tex.outputs['Color'],p.inputs['Emission Color'])
    panel=rr('Screen_'+variant,56.07,80.27,.012,2.86,(-10,0,10.257),m)
    uv=panel.data.uv_layers.new(name='Screen_UV')
    for face in panel.data.polygons:
        for idx in face.loop_indices:
            co=panel.data.vertices[panel.data.loops[idx].vertex_index].co
            uv.data[idx].uv=(co.x/.05607+.5,co.y/.08027+.5)
    panel.hide_render=variant!='height';panel.hide_set(variant!='height')
    panel['artwork']='Reference artwork study' if variant=='reference' else 'RID UI DEMO, not live measurements'

# Rocker silhouette: one capsule, two flat meeting edges, not two oval buttons.
well=rr('Rocker_dark_seat',11.55,22.75,.9,5.7,(30,7.5,9.55),gasket);bevel(well,.15,4)
def rocker_cap(name,cy,down=False):
    w,h=11,10.875;r=w/2;ay=h/2-r
    pts=[(-r,-h/2),(r,-h/2)]+[(r*math.cos(math.pi*j/64),ay+r*math.sin(math.pi*j/64)) for j in range(65)]
    if down:pts=[(-x,-y) for x,y in pts]
    n=len(pts);verts=[(x*.001,y*.001,z*.001) for z in (-.65,.65) for x,y in pts]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    obj=mesh_obj(name,verts,faces,keymat,(30,cy,10.64));bevel(obj,.22,5);finish(obj)
    return obj
rocker_cap('Rocker_upper',13.1125)
rocker_cap('Rocker_lower',1.8875,True)
line_obj('Up_chevron_inlay',[(28.75,12.7,11.29),(30,14.05,11.29),(31.25,12.7,11.29)],.20,ink)
line_obj('Down_chevron_inlay',[(28.75,2.45,11.29),(30,1.1,11.29),(31.25,2.45,11.29)],.20,ink)
well=cylinder('Confirm_dark_seat',5.76,.6,(30,-13.4,10.05),gasket);bevel(well,.15,4);finish(well)
key=cylinder('Orange_confirm_key',5.5,1.35,(30,-13.4,10.69),orange);bevel(key,.23,6);finish(key)
line_obj('Confirm_tick_inlay',[(28.35,-13.6,11.37),(29.6,-15.05,11.37),(32,-11.1,11.37)],.22,ink)
for rradius,label in [(5.06,'outer'),(4.77,'inner')]:
    pts=[(30+rradius*math.cos(i*2*math.pi/192),-13.4+rradius*math.sin(i*2*math.pi/192),11.365) for i in range(193)]
    line_obj('Confirm_'+label+'_score',pts,.026,ink)
for i in range(80):
    a=i*math.pi*2/80
    pts=[(30+r*math.cos(a),-13.4+r*math.sin(a),11.37) for r in (4.96,5.13)]
    line_obj('Confirm_radial_tick_'+str(i).zfill(2),pts,.025,ink)
well=rr('M_key_shadow',8.35,4.15,.55,1.1,(30,-23.5,9.85),gasket)
key=rr('M_key_flush',8,3.8,.7,1,(30,-23.5,10.12),polymer);bevel(key,.13,4);finish(key)

# Original seven-cell checker motif, including its single orange square.
for row,xs in enumerate([(-3,-1,1,3),(-2,0,2)]):
    for j,dx in enumerate(xs):
        tile=rr('Checker_'+str(row)+'_'+str(j),.94,.94,.022,.025,(30+dx,38.9-row*1.05,10.025),orange_ink if row==1 and j==0 else ink)

font_ui=bpy.data.fonts.load('C:/Windows/Fonts/msyh.ttc')
font_jp=bpy.data.fonts.load('C:/Windows/Fonts/YuGothB.ttc')
font_mono=bpy.data.fonts.load('C:/Windows/Fonts/consola.ttf')
def label(name,body,size,loc,material,font,rot=(0,0,0)):
    types=[i.identifier for i in bpy.types.BlendDataCurves.bl_rna.functions['new'].parameters['type'].enum_items]
    curve=bpy.data.curves.new(PREFIX+name,types[types.index('FONT')]);curve.body=body;curve.font=font
    curve.size=size*.001;curve.align_x=next(i.identifier for i in curve.bl_rna.properties['align_x'].enum_items if i.identifier=='CENTER')
    curve.extrude=.002*.001;curve.resolution_u=12
    ob=bpy.data.objects.new(PREFIX+name,curve);assembly.objects.link(ob);ob.parent=root;ob.location=tuple(v*.001 for v in loc);ob.rotation_euler=rot;curve.materials.append(material)
    return ob
label('M_legend','M',1.7,(30,-24.08,10.48),ink,font_mono)
label('Brand_Yuntong','云瞳',2.65,(30,-37.85,10.035),ink,font_ui)
label('Brand_AIRSPACE','A I R S P A C E',.72,(30,-39.5,10.035),ink,font_mono)
refbrand=label('Reference_wordmark','マスター',2.5,(30,-38.1,10.038),ink,font_jp)
refbrand.hide_render=True;refbrand.hide_set(True)

# USB-C: recessed frame, actual hollow shell, central tongue, individual contact accents.
usb=rr('USB_C_metal_shell',9.0,3.3,4.8,1.55,(0,-41.55,0),usbmetal)
cut(usb,rr('cut_USB_inner',8.24,2.58,5.5,1.22,(0,-41.55,0),None))
usb.rotation_euler.x=math.pi/2;bevel(usb,.075,3);finish(usb)
tongue=rr('USB_C_tongue',6.25,.67,2.25,.2,(0,-42.0,0),gasket);tongue.rotation_euler.x=math.pi/2;bevel(tongue,.07,3)
for i in range(12):
    for sign in (-1,1):
        c=rr('USB_contact_'+str(i)+'_'+str(sign),.18,.03,1.1,.01,((i-5.5)*.43,-42.5,sign*.35),gold)
        c.rotation_euler.x=math.pi/2
label('USB_C_mark','USB-C  /  5V',.95,(0,-42.915,3.5),ink,font_mono,(math.pi/2,0,0))
pk=rr('Top_power_button',10.65,2.65,2.3,1.1,(30,43.25,3.5),keymat);pk.rotation_euler.x=math.pi/2;bevel(pk,.22,5);finish(pk)
label('Rear_brand','Y U N T O N G',2.0,(0,14,-10.025),ink,font_mono,(math.pi,0,0))
label('Rear_model','RID  /  ID-A1',1.15,(0,10.8,-10.025),ink,font_mono,(math.pi,0,0))
label('Rear_material','POLYMER  /  CNC ALUMINUM  /  POLYMER',.75,(0,-30,-10.025),ink,font_mono,(math.pi,0,0))
for x in (-35.5,35.5):
    for y in (-37.5,37.5):
        screw=cylinder('Rear_recessed_screw_'+str(x)+'_'+str(y),1.65,.75,(x,y,-9.16),aluminum,96);bevel(screw,.10,3);finish(screw)
        # Six-lobed dark recess drawn as a shallow filled 3D mesh.
        pts=[]
        for i in range(60):
            a=math.pi*2*i/60;r=.67+.12*math.cos(6*a);pts.append((x+r*math.cos(a),y+r*math.sin(a),-9.545))
        mesh_obj('Screw_drive_'+str(x)+'_'+str(y),[tuple(v*.001 for v in p) for p in pts],[tuple(reversed(range(60)))],ink)

# Non-rendering RF reserve indicators belong above/below the metal band.
for name,w,h,loc in [('GNSS_polymer_window',17,17,(29,29,7.2)),('BLE_rear_window',35,10,(-13,28,-7.5)),('WiFi24_rear_window',35,10,(-13,-28,-7.5))]:
    o=rr(name,w,h,.2,1,loc,internal);o.hide_render=True;o.hide_set(True)
    o['note']='Only a placement intention; RF clearance and antenna engineering not established'

for obj in assembly.objects:
    if obj!=root:obj['id_revision']='ID-A1'
scene['reference_policy']='Front detail fidelity from supplied reference; rear, side and internal structure are proposed design.'
scene['rf_policy']='Metal midframe supersedes A0 wall antenna positions. Polymer window regions require RF validation.'
print('BUILD_OK',len(assembly.objects),'objects; original scene retained.')
print('STRUCTURAL_PARTS',[(o.name,tuple(round(v*1000,3) for v in o.dimensions)) for o in (mid,front,rear)])
