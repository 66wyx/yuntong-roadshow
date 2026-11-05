"""RIG-P1 v2 STL + GLB export with a watertight audit

Run inside Blender 5.2 through Blender MCP. Output: ../generated
"""
from pathlib import Path
import bpy
import bmesh
import json
import math
import os
import struct
from mathutils import Vector

OUT = str(Path(__file__).resolve().parents[1] / "generated")
STL = os.path.join(OUT, 'stl')
os.makedirs(STL, exist_ok=True)
sc = bpy.data.scenes['RIG_P1V2_Studio']
P = 'RIG_V2_'
bpy.context.window.scene = sc
sc.frame_set(1)
root = bpy.data.objects[P + 'Assembly']
root.rotation_euler = (0, 0, 0)

PARTS = {
    P + 'F01_Front_panel': ('RIG-P1v2-F01_front_panel.stl', True),
    P + 'F02_Body': ('RIG-P1v2-F02_body.stl', True),
    P + 'F03_Back_cover': ('RIG-P1v2-F03_back_cover.stl', False),
    P + 'F04_Rocker_seat': ('RIG-P1v2-F04_rocker_seat.stl', False),
    P + 'F05_Rocker_up': ('RIG-P1v2-F05_rocker_up.stl', False),
    P + 'F05_Rocker_down': ('RIG-P1v2-F06_rocker_down.stl', False),
    P + 'F06_Confirm_key': ('RIG-P1v2-F07_confirm_key.stl', False),
    P + 'F07_M_key': ('RIG-P1v2-F08_m_key.stl', False),
    P + 'F08_Power_key': ('RIG-P1v2-F09_power_key.stl', False),
}


def write_stl(ob, path, flip):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    # weld coincident vertices left by stacked booleans, then recalc normals
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.00002)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.calc_loop_triangles()
    mw = ob.matrix_world
    pts = [mw @ v.co for v in me.vertices]
    if flip:
        zref = max(p.z for p in pts)
        verts = [(p.x*1000.0, -p.y*1000.0, (-p.z + zref)*1000.0) for p in pts]
    else:
        zref = min(p.z for p in pts)
        verts = [(p.x*1000.0, p.y*1000.0, (p.z - zref)*1000.0) for p in pts]
    tris = [tuple(t.vertices) for t in me.loop_triangles]
    with open(path, 'wb') as fh:
        fh.write(('RIG-P1 v2 ' + ob.name + ' mm').encode('ascii', 'ignore').ljust(80)[:80])
        fh.write(struct.pack('<I', len(tris)))
        for a, b, c in tris:
            va, vb, vc = verts[a], verts[b], verts[c]
            ux, uy, uz = vb[0]-va[0], vb[1]-va[1], vb[2]-va[2]
            wx, wy, wz = vc[0]-va[0], vc[1]-va[1], vc[2]-va[2]
            nx, ny, nz = uy*wz-uz*wy, uz*wx-ux*wz, ux*wy-uy*wx
            ln = math.sqrt(nx*nx+ny*ny+nz*nz) or 1.0
            fh.write(struct.pack('<3f', nx/ln, ny/ln, nz/ln))
            for v in (va, vb, vc):
                fh.write(struct.pack('<3f', *v))
            fh.write(struct.pack('<H', 0))
    bm = bmesh.new()
    bm.from_mesh(me)
    nm = sum(1 for e in bm.edges if not e.is_manifold)
    bm.free()
    ev.to_mesh_clear()
    lo = [min(v[i] for v in verts) for i in range(3)]
    hi = [max(v[i] for v in verts) for i in range(3)]
    print('STL', os.path.basename(path), len(tris), 'tris,', nm, 'non-manifold, size',
          [round(hi[i]-lo[i], 2) for i in range(3)])
    return nm


audit = {}
# the cosmetic bevel on the body breaks watertightness where it meets boolean
# seams, so it is switched off for the print export only
body = bpy.data.objects[P + 'F02_Body']
disabled = []
for mod in body.modifiers:
    if mod.type == 'BEVEL':
        disabled.append((mod, mod.show_render))
        mod.show_render = False
for name, (fn, flip) in PARTS.items():
    audit[fn] = write_stl(bpy.data.objects[name], os.path.join(STL, fn), flip)
for mod, state in disabled:
    mod.show_render = state
print('AUDIT', audit)

for ob in bpy.context.view_layer.objects:
    ob.select_set(False)
for ob in bpy.data.collections['RIG-V2 | Product'].objects:
    ob.select_set(True)
lc = None


def find(lc_, name):
    if lc_.name == name:
        return lc_
    for c in lc_.children:
        r = find(c, name)
        if r:
            return r
    return None


lc = find(bpy.context.view_layer.layer_collection, 'RIG-V2 | Product')
bpy.context.view_layer.active_layer_collection = lc
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'rig-p1-v2.glb'), export_format='GLB',
                          use_active_scene=True, use_active_collection=True,
                          use_active_collection_with_nested=True, export_apply=True,
                          export_yup=True, export_animations=False)
print('GLB', os.path.getsize(os.path.join(OUT, 'rig-p1-v2.glb')))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'rig-p1-v2.blend'))
print('V2_EXPORT_OK')
