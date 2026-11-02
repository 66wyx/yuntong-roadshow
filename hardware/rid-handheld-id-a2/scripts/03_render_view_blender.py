"""Change VIEW for a named render preset; execute as plain code through MCP."""
import bpy
VIEW='hero'
P='RID_A2_'
BASE='C:/Users/YX/Documents/云台检测/hardware/rid-handheld-id-a2/'
scene=bpy.data.scenes['RID_ID_A2_Studio'];bpy.context.window.scene=scene
assert not bpy.app.is_job_running('RENDER'),'Wait for current render'
presets={
    'hero':('hero',1600,1300,'01-hero-metal-wrap.png','height',1),
    'front':('front',1500,1350,'02-front-height.png','height',1),
    'radar':('front',1500,1350,'03-front-radar.png','radar',1),
    'corner':('corner',1450,1300,'04-continuous-corner.png','height',1),
    'controls':('controls',1150,1450,'05-controls.png','height',1),
    'usb':('USB',1500,900,'06-usb-c.png','height',1),
    'rear':('rear',1450,1300,'07-inset-rear.png','height',1),
    'exploded':('exploded',1450,1600,'08-exploded.png','height',60),
    'side':('side',1600,1100,'09-continuous-shell.png','height',1),
}
cam,w,h,file,variant,frame=presets[VIEW]
scene.camera=bpy.data.objects[P+'Camera_'+cam]
scene.render.resolution_x=w;scene.render.resolution_y=h;scene.frame_set(frame)
bpy.data.objects[P+'Studio_ground'].hide_render=VIEW in ('rear','exploded')
for name in ('Back_key','Back_fill'):bpy.data.objects[P+name].hide_render=VIEW!='rear'
for name in ('height','radar'):
    ob=bpy.data.objects[P+'Screen_'+name];ob.hide_render=name!=variant;ob.hide_set(name!=variant)
scene.render.filepath=BASE+'renders/'+file
bpy.ops.render.render(write_still=True)
print('A2_RENDER_COMPLETE',VIEW,scene.render.filepath)
