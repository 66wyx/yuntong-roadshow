"""Independent OpenCascade CAD. Install build123d==0.9.1; run from any cwd.

Nominal package envelopes and fit prototypes, not manufacturing release.
Never opens or changes an existing user's CAD document.
"""
from pathlib import Path
from itertools import combinations
import json
import build123d as b
import vtk

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'mechanical' / 'generated'
OUT.mkdir(parents=True, exist_ok=True)
cfg = json.loads((ROOT / 'design.json').read_text(encoding='utf-8'))
W, H, D = [cfg['case'][k] for k in ('width', 'height', 'depth')]
wall, split, roof = [cfg['case'][k] for k in ('wall', 'split_z', 'front_roof_bottom')]
pieces = []


def box(cx, cy, w, h, z0, z1, r=0):
    sketch = b.RectangleRounded(w, h, r) if r else b.Rectangle(w, h)
    return b.Pos(cx, cy, z0) * b.extrude(sketch, amount=z1-z0)


def cyl(x, y, r, z0, z1):
    return b.Pos(x, y, z0) * b.Cylinder(r, z1-z0, align=(b.Align.CENTER, b.Align.CENTER, b.Align.MIN))


def record(name, shape, color, group, printable=False):
    if not shape.is_valid() or len(shape.solids()) != 1 or shape.volume <= 0:
        raise ValueError('Invalid solid: '+name)
    shape = shape.solids()[0]
    shape.label = name
    shape.color = b.Color(*[c/255 for c in color])
    bb = shape.bounding_box()
    pieces.append(dict(name=name, shape=shape, color=color, group=group, printable=printable,
                       volume_mm3=round(shape.volume, 5),
                       bounds=[list(bb.min), list(bb.max)]))
    return shape


back = box(W/2,H/2,W,H,0,split,8) - box(W/2,H/2,W-2*wall,H-2*wall,wall,split+.2,8-wall)
front = box(W/2,H/2,W,H,split,D,8) - box(W/2,H/2,W-2*wall,H-2*wall,split-.2,roof,8-wall)
for x,y in cfg['case']['screw_centers']:
    back = (back + cyl(x,y,2.8,wall-.05,9.4)) - cyl(x,y,1.2,-.2,9.6)
    front = (front + cyl(x,y,2.8,11,roof+.05)) - cyl(x,y,.8,10.8,20)

display = cfg['display']; cx,cy = display['center_xy']; cw,ch,ct = display['cover_size']
front -= box(cx,cy,cw+.6,ch+.6,20.15,D+.3,3)
aw,ah = display['aperture_size']
front -= box(cx,cy,aw,ah,roof-.2,D+.3,1)
front -= box(67,44.5,13.6,22.4,roof-.2,D+.3,6.7)
front -= cyl(67,25.5,6.5,roof-.2,D+.3)
front -= box(67,12.5,13.6,7.1,roof-.2,D+.3,1.5)
usb = cfg['usb']; ux=usb['center_x']; uz=usb['center_z']; uw,uh=usb['opening_size']
front -= box(ux,(wall+.1)/2,uw,wall+.7,uz-uh/2,uz+uh/2)
front -= box(66.5,H-wall/2,13.2,wall+1,14.7,17.9)
record('Front_shell',front,(156,154,146),'Housing',True)
record('Rear_shell',back,(143,144,137),'Housing',True)

cradle = box(cx,cy,49,66.4,16.4,18.4,2)
cradle -= box(cx,cy,40,57,16.2,18.6,.7)
cradle -= box(cx,cy,43,60.4,17,18.6,.3)
cradle -= box(cx,8,16,8,16.2,18.6,.4)  # FPC passage; fold still requires supplier review.
for x,y in cfg['case']['screw_centers']:
    cradle -= cyl(x,y,3.1,16.1,18.7)
record('Display_cradle',cradle,(80,86,80),'Housing',True)
record('Black_cover_glass_envelope',box(cx,cy,cw,ch,20.2,21,3),(24,30,26),'Display')
dw,dh,dt = display['body_size']
record('LCD_body_'+display['part'],box(cx,cy,dw,dh,17.2,17.2+dt),(83,91,87),'Display')
vw,vh = display['active_size']
record('LCD_active_area_reference',box(cx,cy,vw,vh,21.01,21.03),(24,51,43),'Reference')
pcb = cfg['pcb']; px,py=pcb['center_xy']; pw,ph,pt=pcb['size']; pz=pcb['bottom_z']
board = box(px,py,pw,ph,pz,pz+pt,3)
for x,y in cfg['case']['screw_centers']: board -= cyl(x,y,1.2,pz-.2,pz+pt+.2)
record('PCB_outline_4_layer_unrouted',board,(42,91,69),'PCB')
bat=cfg['battery']; bx,by=bat['center_xy']; bw,bh,bt=bat['envelope_size']; bz=bat['bottom_z']
record('Battery_maximum_envelope_unconfirmed',box(bx,by,bw,bh,bz,bz+bt,2),(157,165,156),'Battery')
colors={'radio':(132,139,135),'gnss':(129,143,132),'sensor':(48,55,49),
        'antenna':(205,198,158),'reserved_area':(133,97,56)}
for p in cfg['parts']:
    x,y=p['center_xy']; w,h,t=p['size']; z=p['bottom_z']
    record(p['ref']+'_'+p['part'],box(x,y,w,h,z,z+t,.25),colors[p['kind']],
           'Reserved' if p['kind']=='reserved_area' else 'Components')

for key in cfg['keys']:
    x,y=key['center_xy']; w,h,t=key['size']; top=key['top_z']
    if key['shape']=='circle':
        cap=cyl(x,y,w/2,20.2,top); flange=cyl(x,y,w/2+.7,18.75,19.15)
    else:
        if key['shape'].startswith('half_capsule'):
            r=w/2; sign=1 if key['id']=='up' else -1
            arc_y=y+sign*(h/2-r)
            stem_y=y-sign*r/2
            cap=(cyl(x,arc_y,r,20.2,top)+box(x,stem_y,w,h-r,20.2,top)) & box(x,y,w,h,20.1,top+.1)
        else:
            cap=box(x,y,w,h,20.2,top,1.1)
        flange=box(x,y,w+1.4,h,18.75,19.15,1)
    cap = cap + cyl(x,y,1.4,15.55,20.25) + flange
    record('Key_'+key['id'],cap,(230,116,58) if key['id']=='confirm' else (191,188,178),'Keys',True)
    record('Switch_envelope_'+key['id'],box(x,y,6,6,11,15.3,.1),(69,73,68),'Switches')
pk=cfg['power_key']; x,y,z=pk['center']; w,h,t=pk['size']
record('Power_key_visual_envelope',box(x,y,w,h,z-t/2,z+t/2),(132,137,126),'Reference')
for a in cfg['radio_fpc_envelopes']:
    x,y,z=a['center']; length,width,th=a['length'],a['width'],a['thickness']
    w,h=(length,th) if a['plane']=='top_wall' else (th,length)
    record(a['ref']+'_FPC_envelope',box(x,y,w,h,z-width/2,z+width/2),(73,87,72),'Antenna')
fpc=cfg['display_fpc_reserve']; x,y=fpc['center_xy']; w,h,t=fpc['size']; z=fpc['bottom_z']
record('LCD_FPC_fold_space_reserved',box(x,y,w,h,z,z+t),(189,128,47),'Reserved')

# Reference/reserved volumes intentionally depict non-parts. Omit from physical collision audit.
collisions=[]
physical=[p for p in pieces if p['group'] not in ('Reference','Reserved')]
for a,c in combinations(physical,2):
    # bounding boxes are a fast rejection before exact BRep intersection.
    if any(a['bounds'][1][i] <= c['bounds'][0][i]+.001 or c['bounds'][1][i] <= a['bounds'][0][i]+.001 for i in range(3)):
        continue
    common=a['shape'].intersect(c['shape'])
    volume=sum(s.volume for s in common.solids()) if common else 0
    if volume > .001: collisions.append(dict(parts=[a['name'],c['name']],volume_mm3=round(volume,5)))

assembly=b.Compound(label='RID_EVT1_A0_REVIEW',children=[p['shape'] for p in pieces])
if not b.export_step(assembly,OUT/'rid-handheld-evt1-a0.step'): raise RuntimeError('STEP export failed')
if not b.export_gltf(assembly,OUT/'rid-handheld-evt1-a0.glb',binary=True,linear_deflection=.08,angular_deflection=.15):
    raise RuntimeError('GLB export failed')
for p in pieces:
    if not p['printable']: continue
    shape=p['shape']
    if p['name']=='Front_shell' or p['name'].startswith('Key_'): shape=b.Rot(180,0,0)*shape
    bb=shape.bounding_box(); shape=b.Pos(-bb.min.X,-bb.min.Y,-bb.min.Z)*shape
    stl_path=OUT/(p['name'].lower()+'_fit_prototype.stl')
    if not b.export_stl(shape,stl_path,tolerance=.05,angular_tolerance=.15):
        raise RuntimeError('STL export failed '+p['name'])
    # OCCT face meshes can differ at shared edges after binary float conversion.
    # Canonicalize vertices within 0.0001 mm, far below the 0.05 mm tessellation tolerance.
    reader=vtk.vtkSTLReader();reader.SetFileName(str(stl_path));reader.Update()
    clean=vtk.vtkCleanPolyData();clean.SetInputConnection(reader.GetOutputPort())
    clean.SetToleranceIsAbsolute(True);clean.SetAbsoluteTolerance(.0001);clean.Update()
    mesh=vtk.vtkPolyData();mesh.DeepCopy(clean.GetOutput())
    writer=vtk.vtkSTLWriter();writer.SetFileName(str(stl_path));writer.SetFileTypeToBinary();writer.SetInputData(mesh)
    if not writer.Write(): raise RuntimeError('Canonical STL write failed '+p['name'])

checks=dict(revision=cfg['revision'],units='mm',all_solids_valid=True,
    battery_to_pcb_nominal_gap_mm=round(pz-bz-bt,3),
    module_to_display_nominal_gap_mm=round(17.2-max(p['bottom_z']+p['size'][2] for p in cfg['parts'] if p['kind']=='radio'),3),
    gnss_patch_to_front_roof_nominal_gap_mm=round(roof-next(p['bottom_z']+p['size'][2] for p in cfg['parts'] if p['ref']=='ANT_GNSS'),3),
    physical_envelope_intersections=collisions,stl_vertex_weld_tolerance_mm=.0001,
    collision_scope='nominal modeled rigid parts only; excludes reference and reserved volumes; no wires, flex bend, connectors, tolerances or antenna field',
    note='Not a manufacturing release. Switch travel, screw lengths, mounts, gasket/adhesive and RF require engineering review.',
    part_count=len(pieces),solids=[{k:v for k,v in p.items() if k not in ('shape','color')} for p in pieces])
(OUT/'cad-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in checks.items() if k!='solids'},ensure_ascii=False))
if collisions: raise RuntimeError('Nominal assembly intersections found; see cad-checks.json')
