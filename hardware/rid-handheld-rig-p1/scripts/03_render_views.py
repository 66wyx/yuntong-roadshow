"""RIG-P1 v2 view renders

Run inside Blender 5.2 through Blender MCP. Output: ../generated
"""
from pathlib import Path
import bpy
import math
import os

OUT = r'D:\ProgramData\deepseek\handle_rid\output\rig-p1-v2\renders'
os.makedirs(OUT, exist_ok=True)
sc = bpy.data.scenes['RIG_P1V2_Studio']
P = 'RIG_V2_'
root = bpy.data.objects[P + 'Assembly']
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGB'


def shot(cam, res, path):
    sc.camera = bpy.data.objects[cam]
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = os.path.join(OUT, path)
    bpy.ops.render.render(write_still=True)
    print('RENDERED', path)


sc.frame_set(1)
root.rotation_euler = (0, 0, 0)
shot(P + 'Camera_front', (1300, 1500), 'v2_front.png')
shot(P + 'Camera_hero', (1600, 1600), 'v2_hero.png')
shot(P + 'Camera_detail', (1500, 1500), 'v2_detail.png')

root.rotation_euler = (math.pi, 0, 0)
shot(P + 'Camera_hero', (1600, 1600), 'v2_back.png')
root.rotation_euler = (0, 0, 0)

sc.frame_set(60)
shot(P + 'Camera_exploded', (1800, 1500), 'v2_exploded.png')
sc.frame_set(1)
print('V2_RENDER_OK')
