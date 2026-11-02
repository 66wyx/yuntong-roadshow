"""Run via Blender MCP after stages 01-04. Change VIEW to a named preset below."""
import bpy
VIEW='front'
BASE='C:/Users/YX/Documents/云台检测/hardware/rid-handheld-id-a1/'
scene=bpy.data.scenes['RID_ID_A1_Studio'];bpy.context.window.scene=scene
assert not bpy.app.is_job_running('RENDER'),'Current render must finish before another view'
presets={
 'front':('front',1100,1250,'01-front-rid.png','height',1),
 'hero':('hero',1600,1400,'02-hero-cnc.png','height',1),
 'reference':('front',1100,1250,'03-reference-study.png','reference',1),
 'controls':('controls',1100,1300,'04-controls-detail.png','height',1),
 'usb':('USB',1600,850,'05-usbc-detail.png','height',1),
 'rear':('back',1400,1250,'06-rear.png','height',1),
 'exploded':('exploded',1400,1550,'07-exploded.png','height',60),
 'radar':('front',1100,1250,'08-front-radar.png','radar',1)
}
camera,w,h,file,variant,frame=presets[VIEW]
scene.camera=bpy.data.objects['RID_A1_Camera_'+camera]
scene.render.resolution_x=w;scene.render.resolution_y=h;scene.frame_set(frame)
bpy.data.objects['RID_A1_Studio_ground'].hide_render=VIEW in ('rear','exploded')
for name in ('RID_A1_Back_key','RID_A1_Back_fill'):bpy.data.objects[name].hide_render=VIEW!='rear'
for v in ('height','radar','reference'):
    obj=bpy.data.objects['RID_A1_Screen_'+v];obj.hide_render=v!=variant;obj.hide_set(v!=variant)
for name in ('Brand_Yuntong','Brand_AIRSPACE'):
    obj=bpy.data.objects['RID_A1_'+name];obj.hide_render=variant=='reference';obj.hide_set(variant=='reference')
obj=bpy.data.objects['RID_A1_Reference_wordmark'];obj.hide_render=variant!='reference';obj.hide_set(variant!='reference')
scene.render.filepath=BASE+'renders/'+file
bpy.ops.render.render(write_still=True)
print('RENDER_COMPLETE',VIEW,scene.render.filepath)
