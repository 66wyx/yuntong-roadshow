"""RIG-P1 v2 parametric build (BODY / PANEL / WIN / MOD / Z dicts)

Run inside Blender 5.2 through Blender MCP. Output: ../generated
"""
from pathlib import Path
import bpy
import bmesh
import math
import json
import os
from mathutils import Vector, Matrix

MM = 0.001
P = 'RIG_V2_'
ROOT_OUT = str(Path(__file__).resolve().parents[1] / "generated")
os.makedirs(ROOT_OUT, exist_ok=True)

# ---------------------------------------------------------------------------
# spec
# ---------------------------------------------------------------------------
BODY = {'w': 82.0, 'h': 92.0, 'd': 37.0, 'corner': 9.2, 'wall': 2.6}
CAV = {'w': 76.8, 'h': 86.8, 'r': 4.0}
PANEL = {'w': 54.0, 'h': 74.0, 't': 2.8, 'cx': -10.0, 'cy': 4.0, 'reveal': 0.6, 'corner': 6.0}
WIN = {'w': 44.2, 'h': 58.65, 'cx': -10.0, 'cy': 7.2, 'r': 2.2}
COL = {'x0': 17.0, 'x1': 41.0, 'cx': 29.0}

# MSP2834 (vendor drawing)
MOD = {
    'pcb_w': 50.0, 'pcb_h': 86.0, 'pcb_t': 1.6,
    'lens_w': 50.0, 'lens_h': 69.2, 'lens_top_from_pcb_top': 3.0,
    'va_w': 43.6, 'va_h': 58.05, 'va_top_from_pcb_top': 6.2,
    'aa_w': 43.2, 'aa_h': 57.6, 'aa_top_from_pcb_top': 9.6,
    'stack': 4.3, 'header_h': 11.17, 'header_span': 33.02,
    'hole_dx': 44.0, 'hole_dy': 76.08, 'hole_d': 3.2,
}
# module centre in device coordinates: VA centre sits on the window centre
MOD_CX = WIN['cx']
MOD_CY = WIN['cy'] - (MOD['pcb_h'] / 2 - MOD['va_top_from_pcb_top'] - MOD['va_h'] / 2)
MOD_TOP = MOD_CY + MOD['pcb_h'] / 2
MOD_BOT = MOD_CY - MOD['pcb_h'] / 2

BOARD = {'w': 85.0, 'h': 56.5, 't': 1.6, 'hole_dx': 58.0, 'hole_dy': 49.0}

# Z stack, front face = +D, back face = 0
Z = {
    'front': BODY['d'],
    'panel_front': BODY['d'] - PANEL['reveal'],
    'panel_back': BODY['d'] - PANEL['reveal'] - PANEL['t'],
}
Z['lens_back'] = Z['panel_back'] - 1.0
Z['lcd_back'] = Z['lens_back'] - 0.5 - 2.3
Z['pcb_front'] = Z['lcd_back'] - 0.5
Z['pcb_back'] = Z['pcb_front'] - MOD['pcb_t']
Z['header_tip'] = Z['pcb_back'] - MOD['header_h']
Z['board_top'] = 15.2          # board flat side (faces the display)
Z['board_pcb'] = (Z['board_top'] - BOARD['t'], Z['board_top'])
Z['back_cover'] = 3.0

DECK_SCREWS = [(-37.2, -30.0), (37.2, -30.0), (-37.2, 30.0), (37.2, 30.0)]
BOARD_POSTS = [(-24.5, -29.0), (24.5, -29.0), (-24.5, 29.0), (24.5, 29.0)]

# ---------------------------------------------------------------------------
# teardown + scene
# ---------------------------------------------------------------------------
for sc in [s for s in bpy.data.scenes if s.name == 'RIG_P1V2_Studio']:
    for ob in list(sc.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.scenes.remove(sc)
for ob in [o for o in bpy.data.objects if o.name.startswith(P)]:
    bpy.data.objects.remove(ob, do_unlink=True)
for c in [c for c in bpy.data.collections if c.name.startswith('RIG-V2')]:
    bpy.data.collections.remove(c)
for m in [m for m in bpy.data.materials if m.name.startswith(P)]:
    bpy.data.materials.remove(m)
for me in [m for m in bpy.data.meshes if m.name.startswith(P) or m.name == 'v2_ground']:
    bpy.data.meshes.remove(me)
for cu in [c for c in bpy.data.curves if c.name.startswith(P)]:
    bpy.data.curves.remove(cu)
for w in [w for w in bpy.data.worlds if w.name == 'RIG_V2_world']:
    bpy.data.worlds.remove(w)

scene = bpy.data.scenes.new('RIG_P1V2_Studio')
bpy.context.window.scene = scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'MILLIMETERS'
scene.unit_settings.scale_length = 1.0

product = bpy.data.collections.new('RIG-V2 | Product')
studio = bpy.data.collections.new('RIG-V2 | Studio')
construction = bpy.data.collections.new('RIG-V2 | Construction')
for c in (product, studio, construction):
    scene.collection.children.link(c)
root = bpy.data.objects.new(P + 'Assembly', None)
product.objects.link(root)
root['layout'] = 'ID-A1 format: 82 x 92 body, left black glass, right control column'
root['hardware'] = 'ESP32-P4-WIFI6-DEV-KIT + LCDWiki MSP2834 (vendor drawing 2023-06-02)'

# ---------------------------------------------------------------------------
# materials
# ---------------------------------------------------------------------------
def mat(name, color, metal=0.0, rough=0.5, grain=0.0):
    m = bpy.data.materials.new(P + name)
    m.use_nodes = True
    p = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Metallic'].default_value = metal
    p.inputs['Roughness'].default_value = rough
    m.diffuse_color = (*color, 1)
    if grain:
        tc = m.node_tree.nodes.new('ShaderNodeTexCoord')
        noise = m.node_tree.nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 180
        noise.inputs['Detail'].default_value = 2.0
        m.node_tree.links.new(tc.outputs['Generated'], noise.inputs['Vector'])
        bump = m.node_tree.nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = 0.10
        bump.inputs['Distance'].default_value = grain * MM
        m.node_tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
        m.node_tree.links.new(bump.outputs['Normal'], p.inputs['Normal'])
    return m


M = {
    'body': mat('Body_warm_gray', (0.262, 0.256, 0.238), 0.0, 0.62, 0.006),
    'glass': mat('Front_glass_black', (0.0045, 0.0055, 0.005), 0.0, 0.19),
    'back': mat('Back_cover_gray', (0.245, 0.240, 0.224), 0.0, 0.66, 0.006),
    'key': mat('Key_light_gray', (0.360, 0.352, 0.330), 0.0, 0.55, 0.004),
    'seat': mat('Key_dark_seat', (0.030, 0.032, 0.030), 0.0, 0.70),
    'orange': mat('Orange_key', (0.680, 0.150, 0.033), 0.0, 0.46, 0.003),
    'ink': mat('Marking_ink', (0.020, 0.024, 0.022), 0.0, 0.62),
    'pcb': mat('Dev_board_PCB_blue', (0.030, 0.080, 0.190), 0.15, 0.55),
    'pcb_dark': mat('Module_PCB_dark', (0.035, 0.038, 0.036), 0.10, 0.55),
    'metal': mat('USB_shell_steel', (0.42, 0.43, 0.44), 0.90, 0.34),
    'chip': mat('Chip_epoxy_black', (0.017, 0.018, 0.017), 0.0, 0.50),
    'gold': mat('Contact_gold', (0.57, 0.34, 0.065), 0.85, 0.28),
    'screen': mat('Screen_demo', (0.010, 0.030, 0.026), 0.0, 0.30),
}

# ---------------------------------------------------------------------------
# geometry helpers
# ---------------------------------------------------------------------------
def bezier(p0, p1, p2, p3, t):
    u = 1 - t
    return (u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0],
            u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1])


def g2_points(w, h, L, steps=30):
    first = ((0, 0), (.28*L, 0), (.64*L, 0), (.82*L, -.18*L))
    second = (first[3], (L, -.36*L), (L, -.72*L), (L, -L))
    c = [bezier(*first, j/steps) for j in range(steps)]
    c += [bezier(*second, j/steps) for j in range(steps + 1)]
    tr = [(w/2 - L + x, h/2 + y) for x, y in c]
    br = [(x, -y) for x, y in reversed(tr)]
    bl = [(-x, -y) for x, y in tr]
    tl = [(-x, y) for x, y in reversed(tr)]
    return list(reversed(tr + br + bl + tl))


def rr_points(w, h, r, steps=18):
    pts = []
    for cx, cy, start in ((w/2-r, h/2-r, 0), (-w/2+r, h/2-r, 90),
                          (-w/2+r, -h/2+r, 180), (w/2-r, -h/2+r, 270)):
        for j in range(steps + 1):
            a = math.radians(start + 90*j/steps)
            pts.append((cx + r*math.cos(a), cy + r*math.sin(a)))
    return pts


def circle_points(r, n=48):
    return [(r*math.cos(i*2*math.pi/n), r*math.sin(i*2*math.pi/n)) for i in range(n)]


def capsule_points(w, h, steps=12):
    """Rounded rectangle with the end radius = w/2 (A1 rocker outline)."""
    r = w / 2.0
    pts = []
    for cx, cy, start in ((0, h/2 - r, 0), (0, -h/2 + r, 180)):
        for j in range(steps + 1):
            a = math.radians(start + 180*j/steps)
            pts.append((cx + r*math.cos(a), cy + r*math.sin(a)))
    return pts


def half_capsule_points(w, h, up=True, steps=14):
    """Half of the A1 rocker: a semicircular end plus a flat split face."""
    r = w / 2.0
    pts = []
    if up:
        base = h - r
        for j in range(steps + 1):
            a = math.radians(180 - 180.0*j/steps)
            pts.append((r*math.cos(a), base + r*math.sin(a)))
        pts.append((r, 0.0))
        pts.append((-r, 0.0))
    else:
        base = -(h - r)
        for j in range(steps + 1):
            a = math.radians(180 + 180.0*j/steps)
            pts.append((r*math.cos(a), base + r*math.sin(a)))
        pts.append((r, 0.0))
        pts.append((-r, 0.0))
    return pts


def _mesh(name, verts, faces, material, col):
    me = bpy.data.meshes.new(name + '_mesh')
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    if material:
        me.materials.append(material)
    return ob


def prism(name, pts, z0, z1, material, cx=0.0, cy=0.0, col=None):
    col = col or product
    n = len(pts)
    verts = [(cx*MM + x*MM, cy*MM + y*MM, z*MM) for z in (z0, z1) for x, y in pts]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2*n))]
    faces += [(i, (i+1) % n, (i+1) % n + n, i + n) for i in range(n)]
    return _mesh(name, verts, faces, material, col)


def block(name, x0, x1, y0, y1, z0, z1, material=None, col=None):
    return prism(name, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1, material, 0, 0,
                 col or construction)


def cylinder(name, r, z0, z1, x, y, material=None, n=48, col=None):
    return prism(name, circle_points(r, n), z0, z1, material, x, y, col or construction)


def boolean(obj, tool, op='DIFFERENCE'):
    mod = obj.modifiers.new('cut', 'BOOLEAN')
    mod.operation = op
    mod.solver = 'EXACT'
    mod.object = tool
    bpy.context.view_layer.objects.active = obj
    for o in bpy.context.selected_objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.select_set(False)
    bpy.data.objects.remove(tool, do_unlink=True)


def bevel(obj, width=0.3, segments=3, angle=34.0):
    m = obj.modifiers.new('soft edge', 'BEVEL')
    m.width = width * MM
    m.segments = segments
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(angle)
    m.harden_normals = True
    m.miter_outer = 'MITER_ARC'
    return m


def shade(obj):
    for p in obj.data.polygons:
        p.use_smooth = abs(p.normal.z) < 0.92
    m = obj.modifiers.new('weighted normals', 'WEIGHTED_NORMAL')
    m.keep_sharp = True
    m.weight = 40


def text_label(name, body, size_mm, loc, material, font_path=r'C:\Windows\Fonts\msyh.ttc',
               rotation=(0, 0, 0), extrude=0.35):
    c = bpy.data.curves.new(P + name, 'FONT')
    c.body = body
    c.font = bpy.data.fonts.load(font_path)
    c.size = size_mm * MM
    c.align_x = 'CENTER'
    c.align_y = 'CENTER'
    c.extrude = extrude * MM
    c.resolution_u = 10
    ob = bpy.data.objects.new(P + name, c)
    product.objects.link(ob)
    ob.parent = root
    ob.location = (loc[0]*MM, loc[1]*MM, loc[2]*MM)
    ob.rotation_euler = rotation
    c.materials.append(material)
    return ob


# ---------------------------------------------------------------------------
# reference hardware
# ---------------------------------------------------------------------------
lens_top = MOD_TOP - MOD['lens_top_from_pcb_top']
block(P + 'REF_mod_pcb', MOD_CX - 25, MOD_CX + 25, MOD_BOT, MOD_TOP, Z['pcb_back'], Z['pcb_front'],
      M['pcb_dark'], product)
block(P + 'REF_mod_lcd', MOD_CX - 25, MOD_CX + 25, lens_top - 69.2, lens_top,
      Z['pcb_front'], Z['lens_back'], M['pcb_dark'], product)
block(P + 'REF_mod_lens', MOD_CX - 25, MOD_CX + 25, lens_top - 69.2, lens_top,
      Z['lens_back'], Z['panel_back'], M['pcb_dark'], product)
va_top = MOD_TOP - MOD['va_top_from_pcb_top']
block(P + 'REF_mod_va', MOD_CX - MOD['va_w']/2, MOD_CX + MOD['va_w']/2, va_top - MOD['va_h'], va_top,
      Z['panel_back'] - 0.06, Z['panel_back'] - 0.02, M['screen'], product)
for i in range(14):
    hx = MOD_CX - MOD['header_span']/2 + i*2.54
    cylinder(P + 'REF_mod_pin_%02d' % i, 0.32, Z['header_tip'], Z['pcb_back'], hx,
             MOD_BOT + 2.2, M['gold'], 12, product)


def board_pt(xl, yl):
    return (-yl, xl)


block(P + 'REF_board_pcb', -28.25, 28.25, -42.5, 42.5, Z['board_pcb'][0], Z['board_pcb'][1],
      M['pcb'], product)


def board_box(name, xl0, xl1, yl0, yl1, z0, z1, material):
    a = board_pt(xl0, yl0); b = board_pt(xl1, yl1)
    x0, x1 = sorted((a[0], b[0])); y0, y1 = sorted((a[1], b[1]))
    return block(P + name, x0, x1, y0, y1, z0, z1, material, product)


bt = Z['board_pcb'][0]
board_box('REF_board_rj45', 21.5, 42.5, 9.52, 28.25, bt - 13.5, bt, M['metal'])
board_box('REF_board_usb1', 25.5, 42.5, -8.48, 9.52, bt - 7.4, bt, M['metal'])
board_box('REF_board_usb2', 25.5, 42.5, -24.83, -8.48, bt - 7.4, bt, M['metal'])
board_box('REF_board_typec1', 22.5, 31.5, -28.25, -19.5, bt - 3.2, bt, M['metal'])
board_box('REF_board_typec2', 33.0, 42.0, -28.25, -19.5, bt - 3.2, bt, M['metal'])
board_box('REF_board_boot', 11.0, 17.0, -28.25, -23.0, bt - 4.2, bt, M['chip'])
board_box('REF_board_rst', 5.0, 10.4, -28.25, -23.0, bt - 4.2, bt, M['chip'])
board_box('REF_board_hdr', -26.0, 26.0, 22.9, 28.25, bt - 8.5, bt, M['chip'])
board_box('REF_board_p4', -8.0, 12.0, -6.0, 12.0, bt - 2.9, bt, M['chip'])

# ---------------------------------------------------------------------------
# F01 front glass
# ---------------------------------------------------------------------------
panel = prism(P + 'F01_Front_panel', g2_points(PANEL['w'], PANEL['h'], PANEL['corner'], 22),
              Z['panel_back'], Z['panel_front'], M['glass'], PANEL['cx'], PANEL['cy'])
boolean(panel, prism('cut_window', rr_points(WIN['w'], WIN['h'], WIN['r'], 22),
                     Z['panel_back'] - 1, Z['panel_front'] + 1, None, WIN['cx'], WIN['cy'],
                     construction))
bevel(panel, 0.4, 3, 40)
shade(panel)

# ---------------------------------------------------------------------------
# F02 body
# ---------------------------------------------------------------------------
body = prism(P + 'F02_Body', g2_points(BODY['w'], BODY['h'], BODY['corner'], 30),
             0, BODY['d'], M['body'])

# cavity open at the back
boolean(body, prism('cut_cavity', rr_points(CAV['w'], CAV['h'], CAV['r'], 20),
                    0 - 1, Z['panel_back'], None, 0, 0, construction))
# panel recess + front aperture with a 1.6 mm lip
boolean(body, prism('cut_panel_recess', rr_points(PANEL['w'] + 0.6, PANEL['h'] + 0.6,
                                                  PANEL['corner'] + 0.3, 20),
                    Z['panel_back'] - 0.05, Z['panel_front'], None, PANEL['cx'], PANEL['cy'], construction))
boolean(body, prism('cut_front_aperture', rr_points(PANEL['w'] - 3.0, PANEL['h'] - 3.0, 2.2, 20),
                    Z['panel_front'], BODY['d'] + 1, None, PANEL['cx'], PANEL['cy'], construction))

# ---- key wells on the control column --------------------------------------
KEY_ROCKER = {'w': 12.4, 'h': 24.0, 'cx': COL['cx'], 'cy': 20.0}
KEY_CONFIRM = {'d': 10.5, 'cx': COL['cx'], 'cy': -2.0}
KEY_M = {'w': 8.0, 'h': 3.6, 'r': 1.0, 'cx': COL['cx'], 'cy': -15.0}
PK = {'w': 12.0, 'h': 3.4, 'cx': 24.0, 'cy': BODY['h']/2 - 1.0}

# rocker opening (capsule) + seat pocket
boolean(body, prism('cut_rocker', capsule_points(KEY_ROCKER['w'], KEY_ROCKER['h']),
                    Z['panel_front'] - 0.1, BODY['d'] + 1, None,
                    KEY_ROCKER['cx'], KEY_ROCKER['cy'], construction))
boolean(body, prism('cut_rocker_seat', capsule_points(KEY_ROCKER['w'] + 2.0, KEY_ROCKER['h'] + 2.0),
                    Z['panel_front'] - 1.9, Z['panel_front'] - 0.6, None,
                    KEY_ROCKER['cx'], KEY_ROCKER['cy'], construction))
# confirm opening + seat
boolean(body, cylinder('cut_confirm', KEY_CONFIRM['d']/2, Z['panel_front'] - 0.1, BODY['d'] + 1,
                       KEY_CONFIRM['cx'], KEY_CONFIRM['cy'], None, 64))
boolean(body, cylinder('cut_confirm_seat', KEY_CONFIRM['d']/2 + 1.0, Z['panel_front'] - 1.9,
                       Z['panel_front'] - 0.6, KEY_CONFIRM['cx'], KEY_CONFIRM['cy'], None, 64))
# M opening + seat
boolean(body, prism('cut_m', rr_points(KEY_M['w'], KEY_M['h'], KEY_M['r'], 8),
                    Z['panel_front'] - 0.1, BODY['d'] + 1, None, KEY_M['cx'], KEY_M['cy'], construction))
boolean(body, prism('cut_m_seat', rr_points(KEY_M['w'] + 1.6, KEY_M['h'] + 1.6, 1.4, 8),
                    Z['panel_front'] - 1.5, Z['panel_front'] - 0.6, None,
                    KEY_M['cx'], KEY_M['cy'], construction))
# power key slot on the top edge
boolean(body, block('cut_power', PK['cx'] - PK['w']/2, PK['cx'] + PK['w']/2,
                    BODY['h']/2 - 4.0, BODY['h']/2 + 1, BODY['d'] - 16.0, BODY['d'] - 12.6))

# switch pockets on the inside of the front wall (3 x 6x6 tact switches)
# Key wells are open through the front wall; a 6x6 tact switch is glued on the
# inner face around each opening, so no printed switch pocket is needed.

# ---- port openings --------------------------------------------------------
# top edge: RJ45 + 2x USB-A (the board sits 42.5 mm up, openings face +Y)
boolean(body, block('cut_rj45', -29.0, -8.8, 40.0, BODY['h']/2 + 1, 0.6, 14.6))
boolean(body, block('cut_usb_a', -8.6, 25.6, 41.2, BODY['h']/2 + 1, 0.6, 15.0))
# right edge: Type-C pair and BOOT / RST
boolean(body, block('cut_typec', 25.0, BODY['w']/2 + 1, 20.0, 44.2, 0.6, 4.2))
boolean(body, block('cut_buttons', 25.0, BODY['w']/2 + 1, 2.0, 19.0, 0.6, 5.0))

bevel(body, 0.5, 3, 34)
shade(body)

# ---------------------------------------------------------------------------
# F03 back cover (carries the board on four 15.2 mm posts)
# ---------------------------------------------------------------------------
back = prism(P + 'F03_Back_cover', g2_points(BODY['w'], BODY['h'], BODY['corner'], 30),
             0, Z['back_cover'], M['back'])
boolean(back, prism('cut_back_cavity', rr_points(CAV['w'] - 0.4, CAV['h'] - 0.4, CAV['r'], 18),
                    Z['back_cover'] - 1, Z['back_cover'] + 0.1, None, 0, 0, construction))
for i, (bx, by) in enumerate(BOARD_POSTS):
    boolean(back, cylinder(P + '_post_%d' % i, 3.0, Z['back_cover'] - 0.1, Z['board_top'],
                           bx, by, M['back']), 'UNION')
    boolean(back, cylinder('cut_post_pilot_%d' % i, 1.05, Z['back_cover'] - 1.0, Z['board_top'] - 2.6,
                           bx, by, None, 20))
for i, (bx, by) in enumerate(DECK_SCREWS):
    boolean(back, cylinder('cut_back_screw_%d' % i, 1.7, -1, Z['back_cover'] + 1, bx, by, None, 24))
    boolean(back, cylinder('cut_back_cb_%d' % i, 3.3, -0.01, 1.4, bx, by, None, 24))
bevel(back, 0.4, 3, 40)
shade(back)

# ---- seat for the back cover: the body stops at z = 3, the cover fills 0..3
boolean(body, prism('cut_back_seat', g2_points(BODY['w'] + 0.2, BODY['h'] + 0.2, BODY['corner'], 30),
                    -1.0, Z['back_cover'], None, 0, 0, construction))

# ---- back-cover flanges: the module fills the cavity, so the screws live in
# ---- 5 mm thick shelves on the left and right walls (z 0..3)
for sx in (-1, 1):
    x0, x1 = (36.0, 39.6) if sx > 0 else (-39.6, -36.0)
    boolean(body, block(P + '_flange_%d' % sx, x0, x1, -38.0, 38.0, Z['back_cover'], 10.5,
                        M['body'], product), 'UNION')
for i, (bx, by) in enumerate(DECK_SCREWS):
    boolean(body, cylinder('cut_back_pilot_%d' % i, 1.2, Z['back_cover'] - 0.2, 9.8, bx, by, None, 20))

# ---------------------------------------------------------------------------
# keys
# ---------------------------------------------------------------------------
# rocker: one seat + two caps
prism(P + 'F04_Rocker_seat', capsule_points(KEY_ROCKER['w'] + 1.8, KEY_ROCKER['h'] + 1.8),
      Z['panel_front'] - 1.9, Z['panel_front'] - 0.7, M['seat'],
      KEY_ROCKER['cx'], KEY_ROCKER['cy'])
cap_h = (KEY_ROCKER['h'] - 1.2) / 2
for name, up in (('F05_Rocker_up', True), ('F05_Rocker_down', False)):
    if up:
        base_y = KEY_ROCKER['cy'] + 0.6
    else:
        base_y = KEY_ROCKER['cy'] - 0.6
    cap = prism(P + name, half_capsule_points(KEY_ROCKER['w'] - 0.3, cap_h, up),
                Z['panel_front'] - 1.4, Z['panel_front'] + 1.5, M['key'],
                KEY_ROCKER['cx'], base_y)
    tip = 2.1 if up else -2.1
    tri = [(KEY_ROCKER['cx'] - 2.4, base_y + (cap_h - 3.1) * (1 if up else -1)),
           (KEY_ROCKER['cx'] + 2.4, base_y + (cap_h - 3.1) * (1 if up else -1)),
           (KEY_ROCKER['cx'], base_y + (cap_h - 3.1 + 1.7) * (1 if up else -1))]
    prism(P + name + '_chevron', tri, Z['panel_front'] + 1.5, Z['panel_front'] + 1.56, M['ink'])
    bevel(cap, 0.4, 3, 45)
    shade(cap)

# confirm key
conf = cylinder(P + 'F06_Confirm_key', KEY_CONFIRM['d']/2, Z['panel_front'] - 1.4,
                Z['panel_front'] + 0.9, KEY_CONFIRM['cx'], KEY_CONFIRM['cy'], M['orange'], 64,
                product)
bevel(conf, 0.5, 3, 45)
shade(conf)
# tick mark
tick = [(KEY_CONFIRM['cx'] - 2.6, KEY_CONFIRM['cy'] + 0.2), (KEY_CONFIRM['cx'] - 0.7, KEY_CONFIRM['cy'] - 1.7),
        (KEY_CONFIRM['cx'] + 2.8, KEY_CONFIRM['cy'] + 2.0)]
for idx, (a, b) in enumerate(((tick[0], tick[1]), (tick[1], tick[2]))):
    dx, dy = b[0]-a[0], b[1]-a[1]
    ln = math.hypot(dx, dy)
    nx, ny = -dy/ln*0.32, dx/ln*0.32
    quad = [(a[0]-nx, a[1]-ny), (b[0]-nx, b[1]-ny), (b[0]+nx, b[1]+ny), (a[0]+nx, a[1]+ny)]
    prism(P + 'F06_tick_%d' % idx, quad, Z['panel_front'] + 1.6, Z['panel_front'] + 1.65, M['ink'])

# M key
mkey = prism(P + 'F07_M_key', rr_points(KEY_M['w'], KEY_M['h'], KEY_M['r'], 8),
             Z['panel_front'] - 1.2, Z['panel_front'] + 0.2, M['key'], KEY_M['cx'], KEY_M['cy'])
bevel(mkey, 0.25, 2, 45)
shade(mkey)

# power key on the top edge
pkey = block(P + 'F08_Power_key', PK['cx'] - PK['w']/2, PK['cx'] + PK['w']/2,
             BODY['h']/2 - 3.4, BODY['h']/2 + 0.4, BODY['d'] - 15.8, BODY['d'] - 12.8, M['key'], product)
bevel(pkey, 0.3, 2, 40)
shade(pkey)

# ---------------------------------------------------------------------------
# marks
# ---------------------------------------------------------------------------
text_label('mark_wordmark', '浜戠灣', 4.6, (-12.0, -38.6, BODY['d'] + 0.12), M['ink'])
text_label('mark_airspace', 'AIRSPACE', 1.5, (-12.0, -41.9, BODY['d'] + 0.12), M['ink'],
           font_path=r'C:\Windows\Fonts\consola.ttf')
text_label('mark_model', 'RID  P1', 1.5, (12.0, -41.9, BODY['d'] + 0.12), M['ink'],
           font_path=r'C:\Windows\Fonts\consola.ttf')
text_label('mark_power', 'PWR', 1.2, (COL['cx'], 34.6, BODY['d'] + 0.12), M['ink'],
           font_path=r'C:\Windows\Fonts\consola.ttf')
text_label('mark_m_legend', 'M', 2.0, (KEY_M['cx'], KEY_M['cy'], Z['panel_front'] + 0.25), M['ink'],
           font_path=r'C:\Windows\Fonts\consola.ttf')

sq, gap = 1.3, 0.42
for row in range(2):
    for col in range(4):
        x0 = 24.0 + col*(sq + gap)
        y0 = 39.4 + row*(sq + gap)
        material = M['orange'] if (row == 1 and col == 0) else M['ink']
        block(P + 'mark_checker_%d_%d' % (row, col), x0, x0 + sq, y0, y0 + sq,
              BODY['d'] - 0.1, BODY['d'] + 0.22, material, product)

text_label('mark_back_brand', '浜戠灣 路 RID', 4.0, (0, 30.0, -0.12), M['ink'],
           rotation=(0, math.pi, 0))
text_label('mark_back_model', 'RIG-P1  P4/C6 BENCH', 2.0, (0, 24.0, -0.12), M['ink'],
           font_path=r'C:\Windows\Fonts\consola.ttf', rotation=(0, math.pi, 0))

# ---------------------------------------------------------------------------
# screen mock
# ---------------------------------------------------------------------------
ui_path = r'C:\Users\YX\Documents\浜戝彴妫€娴媆hardware\rid-handheld-id-a1\assets\screen-radar.png'
if os.path.exists(ui_path):
    img = bpy.data.images.load(ui_path)
    img.colorspace_settings.name = 'sRGB'
    smat = bpy.data.materials.new(P + 'Screen_UI')
    smat.use_nodes = True
    nt = smat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    em = nt.nodes.new('ShaderNodeEmission')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = img
    tex.extension = 'EXTEND'
    nt.links.new(tex.outputs['Color'], em.inputs['Color'])
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    em.inputs['Strength'].default_value = 1.15
    hw, hh = WIN['w']/2, WIN['h']/2
    zz = Z['panel_back'] + 0.02
    verts = [((WIN['cx']-hw)*MM, (WIN['cy']-hh)*MM, zz*MM), ((WIN['cx']+hw)*MM, (WIN['cy']-hh)*MM, zz*MM),
             ((WIN['cx']+hw)*MM, (WIN['cy']+hh)*MM, zz*MM), ((WIN['cx']-hw)*MM, (WIN['cy']+hh)*MM, zz*MM)]
    me = bpy.data.meshes.new(P + 'Screen_UI_mesh')
    me.from_pydata(verts, [], [(0, 1, 2, 3)])
    uvl = me.uv_layers.new(name='UVMap')
    for i, co in enumerate([(0.006, 0.0), (0.994, 0.0), (0.994, 1.0), (0.006, 1.0)]):
        uvl.data[i].uv = co
    me.materials.append(smat)
    so = bpy.data.objects.new(P + 'Screen_UI', me)
    product.objects.link(so)
    so.parent = root

# ---------------------------------------------------------------------------
# studio
# ---------------------------------------------------------------------------
scene.render.engine = 'BLENDER_EEVEE'
if hasattr(scene, 'eevee'):
    if hasattr(scene.eevee, 'taa_render_samples'):
        scene.eevee.taa_render_samples = 64
    if hasattr(scene.eevee, 'use_raytracing'):
        scene.eevee.use_raytracing = True
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'
scene.view_settings.exposure = -0.45

world = bpy.data.worlds.new('RIG_V2_world')
world.use_nodes = True
scene.world = world
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0.042, 0.046, 0.044, 1)
bg.inputs['Strength'].default_value = 0.32

gmat = mat('Studio_charcoal', (0.014, 0.017, 0.015), 0, 0.9)
me = bpy.data.meshes.new('v2_ground')
gg, gz = 3.0, -0.0009
me.from_pydata([(-gg, -gg, gz), (gg, -gg, gz), (gg, gg, gz), (-gg, gg, gz)], [], [(0, 1, 2, 3)])
ground = bpy.data.objects.new(P + 'Studio_ground', me)
studio.objects.link(ground)
me.materials.append(gmat)


def area(name, position, target, power, size, ratio, color):
    data = bpy.data.lights.new(P + name, 'AREA')
    data.energy = power
    data.color = color
    data.shape = 'RECTANGLE'
    data.size = size
    data.size_y = size*ratio
    ob = bpy.data.objects.new(P + name, data)
    studio.objects.link(ob)
    ob.location = position
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat('-Z', 'Y').to_euler()
    return ob


area('softbox_key', (-0.17, 0.17, 0.30), (0, 0, 0.02), 3.0, 0.24, 1.5, (1, 0.965, 0.91))
area('softbox_edge', (0.20, 0.05, 0.21), (0, 0, 0.015), 1.5, 0.09, 2.2, (0.91, 0.96, 1))
area('softbox_low', (-0.03, -0.21, 0.12), (0, 0, 0.01), 1.0, 0.15, 0.45, (1, 0.90, 0.79))
area('glass_reflector', (-0.15, 0.22, 0.34), (-0.015, 0, 0.02), 1.0, 0.05, 5, (1, 1, 1))
area('rim_back', (0.06, 0.10, -0.34), (0, 0, 0), 6.0, 0.30, 0.8, (0.95, 0.97, 1.0))


def camera(name, location, target, ortho=None, lens=90):
    data = bpy.data.cameras.new(P + name)
    if ortho:
        data.type = 'ORTHO'
        data.ortho_scale = ortho
    else:
        data.type = 'PERSP'
        data.lens = lens
    data.clip_start = 0.001
    data.clip_end = 20
    ob = bpy.data.objects.new(P + name, data)
    studio.objects.link(ob)
    ob.location = location
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat('-Z', 'Y').to_euler()
    return ob


cam_front = camera('Camera_front', (0, 0, 0.40), (0, 0, 0), ortho=0.135)
cam_hero = camera('Camera_hero', (0.115, -0.150, 0.26), (0, 0, 0.004), lens=95)
cam_back = camera('Camera_back', (0.10, 0.140, -0.24), (0, 0, -0.004), lens=95)
cam_detail = camera('Camera_detail', (0.055, -0.105, 0.16), (0.018, -0.012, 0.020), lens=115)
cam_ex = camera('Camera_exploded', (0.30, -0.24, 0.16), (0, 0, 0.004), lens=80)

scene.camera = cam_hero
scene.render.resolution_x = 1600
scene.render.resolution_y = 1600

# ---------------------------------------------------------------------------
# explosion
# ---------------------------------------------------------------------------
for ob in list(product.objects):
    if ob.parent is None and ob is not root:
        ob.parent = root

g_front = bpy.data.objects.new(P + 'FRONT_GROUP', None)
g_back = bpy.data.objects.new(P + 'BACK_GROUP', None)
for g in (g_front, g_back):
    product.objects.link(g)
    g.parent = root

for n in [P + 'F01_Front_panel', P + 'Screen_UI']:
    ob = bpy.data.objects.get(n)
    if ob:
        ob.parent = g_front
for n in [P + 'F03_Back_cover']:
    bpy.data.objects[n].parent = g_back
for ob in product.objects:
    if ob.name.startswith(P + 'REF_board'):
        ob.parent = g_back

for g, dz in ((g_front, 0.030), (g_back, -0.040)):
    g.location = (0, 0, 0)
    g.keyframe_insert(data_path='location', frame=1)
    g.location = (0, 0, dz)
    g.keyframe_insert(data_path='location', frame=60)
scene.frame_start = 1
scene.frame_end = 60
scene.frame_set(1)

# ---------------------------------------------------------------------------
# checks + save
# ---------------------------------------------------------------------------
def stats(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(me)
    vol = abs(bm.calc_volume(signed=False))
    bm.free()
    ev.to_mesh_clear()
    bb = [Vector(c) for c in ob.bound_box]
    xs = [v.x for v in bb]; ys = [v.y for v in bb]; zs = [v.z for v in bb]
    return {'volume_cm3': round(vol*1e9/1000, 2),
            'bbox_mm': [round((max(xs)-min(xs))*1000, 2), round((max(ys)-min(ys))*1000, 2),
                        round((max(zs)-min(zs))*1000, 2)]}


parts = [P + 'F01_Front_panel', P + 'F02_Body', P + 'F03_Back_cover', P + 'F04_Rocker_seat',
         P + 'F05_Rocker_up', P + 'F05_Rocker_down', P + 'F06_Confirm_key', P + 'F07_M_key',
         P + 'F08_Power_key']
report = {'revision': 'RIG-P1V2-A0', 'units': 'mm', 'parts': {}, 'checks': {}}
for n in parts:
    report['parts'][n] = stats(bpy.data.objects[n])

report['checks'] = {
    'layout': 'ID-A1: 82 x 92, left glass 54 x 74, right column 24 wide',
    'z_stack': {k: (round(v, 2) if isinstance(v, (int, float)) else [round(x, 2) for x in v])
                for k, v in Z.items()},
    'module_position': {'cx': round(MOD_CX, 2), 'cy': round(MOD_CY, 2),
                        'pcb_top': round(MOD_TOP, 2), 'pcb_bottom': round(MOD_BOT, 2),
                        'lens_top': round(lens_top, 2), 'va_top': round(va_top, 2)},
    'clearances': {
        'header_tip_to_board_flat_side': round(Z['header_tip'] - Z['board_top'], 2),
        'board_lowest_component_to_back_face': round(Z['board_pcb'][0] - 13.5, 2),
        'module_side_gap': round((CAV['w'] - MOD['pcb_w'])/2, 2),
        'panel_to_recess': 0.30,
        'glass_to_body_left_edge': round(PANEL['cx'] - PANEL['w']/2 + BODY['w']/2, 2),
        'column_width': round(COL['x1'] - COL['x0'], 2),
    },
    'open_items': [
        'Keys need three 6x6x5 tact switches glued into the printed pockets and four jumper wires to the 2x20 header.',
        'The 14P header is 11.17 tall; trimming it to 8 mm would take the body from 37 to 34 mm.',
        'RJ45 / USB-A / Type-C envelope heights are vendor-table values.',
    ],
}
with open(os.path.join(ROOT_OUT, 'rig-p1-v2-checks.json'), 'w', encoding='utf-8') as fh:
    json.dump(report, fh, ensure_ascii=False, indent=2)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT_OUT, 'rig-p1-v2.blend'))
print('RIG_V2_BUILD_OK')
print(json.dumps(report['checks'], ensure_ascii=False))
print(json.dumps(report['parts'], ensure_ascii=False))
