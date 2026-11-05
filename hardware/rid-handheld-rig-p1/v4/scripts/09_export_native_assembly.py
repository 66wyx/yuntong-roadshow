"""Direct native CAD assembly export, without importing mesh/STL geometry.

Dependencies: cadquery==2.6.1 and cadquery-ocp==7.8.1.1.post1.
Millimetres. V4 mechanical parts retain their assembled positions.
"""
from pathlib import Path
import hashlib
import json
import re
import shutil
import time
import cadquery as cq

import native_shells
import native_controls
import native_board


def main():
    started=time.monotonic()
    root=Path(__file__).resolve().parents[1]
    step_dir=root/'step';step_dir.mkdir(exist_ok=True)
    cad_dir=root/'cad';cad_dir.mkdir(exist_ok=True)
    work=Path.home()/'.cache'/'yuntong-native-cad-export'
    work.mkdir(parents=True,exist_ok=True)
    print('Building native Bezier, circular, planar and fillet geometry',flush=True)
    parts=native_shells.build_parts()+native_controls.build_parts()+native_board.build_parts()
    assert len(parts)==14
    assembly=cq.Assembly(name='Yuntong_RIG_P1_V4_NATIVE_27p7mm')
    records=[]
    for name,shape in parts:
        assert shape.isValid() and len(shape.Solids())==1 and shape.Volume()>0,name
        rgb=(.91,.36,.09) if name.startswith('P07') else (.035,.045,.04) if name.startswith('P03') else (.60,.60,.56)
        assembly.add(shape,name=name,color=cq.Color(*rgb))
        records.append({'name':name,'solids':1,'faces':len(shape.Faces()),'volume_mm3':shape.Volume()})
    filename='yuntong-rig-p1-v4-native-assembly.stp'
    temporary=work/filename
    assembly.save(str(temporary),exportType='STEP',mode='default')
    # One quick exchange round-trip confirms the assembled file, not a mesh.
    imported=cq.importers.importStep(str(temporary)).val()
    bounds=imported.BoundingBox()
    assert len(imported.Solids())==14
    assert bounds.zlen<28.001
    text=temporary.read_text(encoding='utf-8')
    keywords=['CYLINDRICAL_SURFACE','CONICAL_SURFACE','TOROIDAL_SURFACE',
              'CIRCLE','B_SPLINE_CURVE_WITH_KNOTS','B_SPLINE_SURFACE_WITH_KNOTS',
              'SURFACE_OF_LINEAR_EXTRUSION','ADVANCED_FACE','FACETED_BREP',
              'TRIANGULATED_FACE_SET']
    counts={k:len(re.findall(r'\b'+k+r'\s*\(',text)) for k in keywords}
    assert counts['CYLINDRICAL_SURFACE']>0 and counts['CIRCLE']>0
    assert counts['B_SPLINE_CURVE_WITH_KNOTS']+counts['B_SPLINE_SURFACE_WITH_KNOTS']>0
    assert counts['FACETED_BREP']==0 and counts['TRIANGULATED_FACE_SET']==0
    destination=step_dir/filename
    shutil.copyfile(temporary,destination)
    brep_work=work/'yuntong-rig-p1-v4-native-assembly.brep'
    cq.Compound.makeCompound([shape for _,shape in parts]).exportBrep(str(brep_work))
    shutil.copyfile(brep_work,cad_dir/brep_work.name)
    report={'date':'2026-11-06','source':'Native CadQuery/OpenCascade construction from V4 dimensions',
            'mesh_or_stl_input':False,'units':'mm','part_count':len(parts),
            'assembly_file':'step/'+filename,'size_bytes':destination.stat().st_size,
            'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),
            'assembled_size_mm':[bounds.xlen,bounds.ylen,bounds.zlen],
            'step_entities':counts,'parts':records,'seconds':round(time.monotonic()-started,2)}
    (root/'validation/native-cad-export.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report),flush=True)


if __name__=='__main__':
    main()
