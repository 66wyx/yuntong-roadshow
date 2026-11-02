"""Final CMF/render settings, verified against the connected Blender 5.2 build."""
import bpy
scene=bpy.data.scenes['RID_ID_A1_Studio'];bpy.context.window.scene=scene
power={'RID_A1_Softbox_key':.60375,'RID_A1_Softbox_edge':.322,'RID_A1_Softbox_low':.2093,'RID_A1_Long_glass_reflector':.161}
for name,value in power.items():bpy.data.objects[name].data.energy=value
scene.view_settings.exposure=-.1
next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND').inputs['Strength'].default_value=.08
for name in ('height','radar','reference'):
    mat=bpy.data.materials['RID_A1_Screen_'+name]
    p=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    p.inputs['Emission Strength'].default_value=1.0
    p.inputs['Specular IOR Level'].default_value=.065
    p.inputs['Coat Weight'].default_value=.02
    texture=next(n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE')
    texture.image.reload();texture.image.pack()
for obj in bpy.data.collections['ID-A1 | Product'].objects:
    if obj.name.startswith('RID_A1_USB_C_metal_shell'):obj.location.y=-.0404
    elif obj.name.startswith('RID_A1_USB_C_tongue'):obj.location.y=-.04085
    elif obj.name.startswith('RID_A1_USB_contact_'):obj.location.y=-.04135
brand=bpy.data.objects['RID_A1_Brand_Yuntong']
if brand.type=='FONT':brand.data.size=.0033
m=bpy.data.materials['RID_A1_Orange_key_fine_matte']
p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(.64,.10,.025,1)
ramp=next(n for n in m.node_tree.nodes if n.type=='VALTORGB')
for element,mul in zip(ramp.color_ramp.elements,(.88,1.08)):element.color=(.64*mul,.10*mul,.025*mul,1)
p=next(n for n in bpy.data.materials['RID_A1_Orange_index_inlay'].node_tree.nodes if n.type=='BSDF_PRINCIPLED')
p.inputs['Base Color'].default_value=(.60,.075,.017,1)
cycles_addon=bpy.context.preferences.addons.get('cycles')
cycles_preferences=cycles_addon.preferences
try:
    cycles_preferences.compute_device_type='OPTIX'
    cycles_preferences.get_devices()
    for device in cycles_preferences.devices:device.use=device.type=='OPTIX'
except TypeError as e:
    print('GPU_ENUM',str(e))
try:scene.render.engine='CYCLES'
except TypeError as e:print('RENDER_ENGINES',str(e))
scene.cycles.device=next(i.identifier for i in scene.cycles.bl_rna.properties['device'].enum_items if i.identifier=='GPU')
scene.cycles.samples=96;scene.cycles.use_denoising=True;scene.cycles.adaptive_threshold=.012
scene.cycles.max_bounces=8
scene.render.resolution_x=1100;scene.render.resolution_y=1250
scene.camera=bpy.data.objects['RID_A1_Camera_front'];scene.frame_set(1)
scene.render.filepath='C:/Users/YX/Documents/云台检测/hardware/rid-handheld-id-a1/renders/01-front-rid.png'
print('FINAL_CMF_READY',scene.render.engine,scene.cycles.device)
