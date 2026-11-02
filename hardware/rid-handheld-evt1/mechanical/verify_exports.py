"""Reopen STEP, check exported STL boundary/nonmanifold edges and GLB container."""
from pathlib import Path
import json
import struct
import build123d as b
import vtk

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'mechanical/generated'
cad=json.loads((OUT/'cad-checks.json').read_text(encoding='utf-8'))
step=b.import_step(OUT/'rid-handheld-evt1-a0.step')
assert len(step.solids())==cad['part_count']
assert all(s.is_valid() and s.volume>0 for s in step.solids())
stls=[]
for path in sorted(OUT.glob('*_fit_prototype.stl')):
    reader=vtk.vtkSTLReader();reader.SetFileName(str(path));reader.Update()
    edges=vtk.vtkFeatureEdges();edges.SetInputConnection(reader.GetOutputPort())
    edges.BoundaryEdgesOn();edges.NonManifoldEdgesOn();edges.FeatureEdgesOff();edges.ManifoldEdgesOff();edges.Update()
    assert reader.GetOutput().GetNumberOfCells()>0
    assert edges.GetOutput().GetNumberOfCells()==0,path.name+' is not a closed manifold mesh'
    stls.append(dict(file=path.name,triangles=reader.GetOutput().GetNumberOfCells(),boundary_or_nonmanifold_edges=0))
assert len(stls)==7
data=(OUT/'rid-handheld-evt1-a0.glb').read_bytes()
magic,version,total=struct.unpack_from('<4sII',data)
assert magic==b'glTF' and version==2 and total==len(data)
size,kind=struct.unpack_from('<I4s',data,12)
assert kind==b'JSON'
gltf=json.loads(data[20:20+size]);assert len(gltf.get('meshes',[]))==cad['part_count']
report=dict(step_roundtrip_solid_count=len(step.solids()),step_valid_solids=True,stl_count=len(stls),
            stl_mesh_checks=stls,glb_version=version,glb_mesh_count=len(gltf['meshes']),
            note='Geometry/file checks only. STL dimensions use millimetres. No physical fit verification.')
(ROOT/'validation/export-checks.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
