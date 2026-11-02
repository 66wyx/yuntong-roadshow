"""Optional CAD preview: build123d, VTK and Pillow; run render_screens.cjs first."""
from pathlib import Path
import vtk
from PIL import Image, ImageDraw, ImageFont
import build_cad as cad

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical/generated'


def actor(shape,color,offset):
    vertices,triangles=shape.tessellate(.08,.15)
    points=vtk.vtkPoints()
    for v in vertices: points.InsertNextPoint(v.X,v.Y,v.Z)
    cells=vtk.vtkCellArray()
    for tri in triangles:
        cells.InsertNextCell(3)
        for i in tri: cells.InsertCellPoint(i)
    mesh=vtk.vtkPolyData();mesh.SetPoints(points);mesh.SetPolys(cells)
    normals=vtk.vtkPolyDataNormals();normals.SetInputData(mesh);normals.SplittingOn();normals.SetFeatureAngle(40)
    mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(normals.GetOutputPort())
    a=vtk.vtkActor();a.SetMapper(mapper);a.SetPosition(0,0,offset)
    p=a.GetProperty();p.SetColor(*[c/255 for c in color]);p.SetAmbient(.28);p.SetDiffuse(.72);p.SetSpecular(.15);p.SetSpecularPower(22)
    return a


def screen_texture(renderer,z):
    reader=vtk.vtkPNGReader();reader.SetFileName(str(ROOT/'interface/height-demo.png'));reader.Update()
    texture=vtk.vtkTexture();texture.SetInputConnection(reader.GetOutputPort());texture.InterpolateOn()
    cx,cy=cad.cfg['display']['center_xy'];w,h=cad.cfg['display']['active_size']
    plane=vtk.vtkPlaneSource();plane.SetOrigin(cx-w/2,cy-h/2,z);plane.SetPoint1(cx+w/2,cy-h/2,z);plane.SetPoint2(cx-w/2,cy+h/2,z)
    mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(plane.GetOutputPort())
    a=vtk.vtkActor();a.SetMapper(mapper);a.SetTexture(texture);a.GetProperty().LightingOff();renderer.AddActor(a)


def symbol(renderer,points,z,color=(.16,.23,.17)):
    pp=vtk.vtkPoints()
    for x,y in points:pp.InsertNextPoint(x,y,z)
    lines=vtk.vtkCellArray();lines.InsertNextCell(len(points))
    for i in range(len(points)):lines.InsertCellPoint(i)
    data=vtk.vtkPolyData();data.SetPoints(pp);data.SetLines(lines)
    mapper=vtk.vtkPolyDataMapper();mapper.SetInputData(data)
    a=vtk.vtkActor();a.SetMapper(mapper);a.GetProperty().SetColor(*color);a.GetProperty().SetLineWidth(3);a.GetProperty().LightingOff();renderer.AddActor(a)


def render(exploded=False):
    ren=vtk.vtkRenderer();ren.SetBackground(.94,.945,.915)
    offsets={'Front_shell':32,'Rear_shell':-15,'Display_cradle':17,'Black_cover_glass_envelope':42,
             'LCD_body_DT024ETFT-IPS':25,'Battery_maximum_envelope_unconfirmed':-8}
    for p in cad.pieces:
        if p['group'] in ('Reference','Reserved'): continue
        off=(32 if p['group']=='Keys' else offsets.get(p['name'],0)) if exploded else 0
        ren.AddActor(actor(p['shape'],p['color'],off))
    # Power cap is only an envelope, not a printable switch design.
    p=next(p for p in cad.pieces if p['name']=='Power_key_visual_envelope')
    ren.AddActor(actor(p['shape'],p['color'],32 if exploded else 0))
    screen_texture(ren,21.05+(42 if exploded else 0))
    z=22.03+(32 if exploded else 0)
    symbol(ren,[(65.3,49.0),(67,50.6),(68.7,49.0)],z)
    symbol(ren,[(65.3,40),(67,38.4),(68.7,40)],z)
    symbol(ren,[(64.7,25.5),(66.3,23.4),(69.5,28)],z)
    symbol(ren,[(65,10.7),(65,14.3),(67,11.5),(69,14.3),(69,10.7)],z)
    camera=ren.GetActiveCamera();camera.ParallelProjectionOn();camera.SetViewUp(0,1,0)
    if exploded:camera.SetPosition(155,-170,220);camera.SetFocalPoint(41,38,23);camera.SetParallelScale(74)
    else:camera.SetPosition(138,-100,250);camera.SetFocalPoint(41,38,11);camera.SetParallelScale(55)
    window=vtk.vtkRenderWindow();window.SetOffScreenRendering(1);window.SetSize(900,820);window.AddRenderer(ren);window.SetMultiSamples(8);window.Render()
    capture=vtk.vtkWindowToImageFilter();capture.SetInput(window);capture.Update()
    output=OUT/('exploded-view.png' if exploded else 'assembly-view.png')
    writer=vtk.vtkPNGWriter();writer.SetFileName(str(output));writer.SetInputConnection(capture.GetOutputPort());writer.Write();window.Finalize()
    return Image.open(output).convert('RGB')


front=render();exploded=render(True)
canvas=Image.new('RGB',(1800,960),'#f0f1e9');canvas.paste(front,(0,72));canvas.paste(exploded,(900,72))
draw=ImageDraw.Draw(canvas)
fontfile=Path('C:/Windows/Fonts/msyh.ttc')
large=ImageFont.truetype(str(fontfile),28);small=ImageFont.truetype(str(fontfile),19)
draw.text((42,22),'云瞳 RID · EVT1-A0 结构评审',font=large,fill='#1d3826')
draw.text((941,26),'分解示意 · 不同部件沿 Z 轴移开',font=small,fill='#38543e')
draw.text((42,894),'机身 82 × 76 × 21 mm；含按键目标 82 × 78 × 22 mm。',font=small,fill='#294731')
draw.text((42,928),'名义包络模型；屏幕为演示图。FPC、电池公差、连接器、天线载板及装配需实物核查。',font=small,fill='#7c572e')
canvas.save(OUT/'engineering-preview.png')
print('CAD previews generated.')
