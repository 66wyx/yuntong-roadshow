"""Arrange the actual Blender renders into portable review sheets; no synthetic renders."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
import json, struct
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'renders'
BG='#131815';FG='#e2e4da';DIM='#a9b6aa';ACCENT='#dd8154'
def font(n,bold=False):return ImageFont.truetype('C:/Windows/Fonts/'+('msyhbd.ttc' if bold else 'msyh.ttc'),n)
def place(canvas,name,box):
    im=Image.open(OUT/name).convert('RGB');x,y,w,h=box
    im=ImageOps.contain(im,(w,h),Image.Resampling.LANCZOS)
    canvas.paste(im,(x+(w-im.width)//2,y+(h-im.height)//2))

canvas=Image.new('RGB',(2200,1740),BG);draw=ImageDraw.Draw(canvas)
draw.text((56,35),'云瞳 RID · ID-A1',font=font(48,True),fill=FG)
draw.text((56,102),'CNC 铝合金中框  /  3D 打印前后盖  /  外观细节评审',font=font(27),fill=DIM)
panels=[('04-controls-detail.png','01  长形分体键 · 确认键同心细圈与边缘刻纹',(55,218,1020,620)),
        ('05-usbc-detail.png','02  内凹 Type-C · 金属中框与装配缝',(1125,218,1020,620)),
        ('06-rear.png','03  打印后盖 · 内凹螺钉与防滑槽',(55,988,1020,620)),
        ('07-exploded.png','04  前盖 / 中框 / 后盖独立成件',(1125,988,1020,620))]
for name,title,box in panels:
    draw.text((box[0],box[1]-54),title,font=font(25),fill=FG)
    place(canvas,name,box)
draw.text((56,1677),'外观模型与演示 UI；接口、装配公差及天线布局需后续工程验证。',font=font(23),fill=DIM)
canvas.save(OUT/'09-detail-board.png',optimize=True)

canvas=Image.new('RGB',(1760,1260),BG);draw=ImageDraw.Draw(canvas)
draw.text((54,33),'同一外壳 · 两种界面表达',font=font(43,True),fill=FG)
draw.text((54,104),'参考图风格对照',font=font(26),fill=DIM)
draw.text((922,104),'云瞳 RID 高度界面',font=font(26),fill=DIM)
place(canvas,'03-reference-study.png',(40,154,820,930))
place(canvas,'01-front-rid.png',(900,154,820,930))
draw.text((54,1126),'保留黑橙棋盘标记、分缝、胶囊按键、橙色细纹键与底部字标位置。',font=font(26),fill=FG)
draw.text((54,1182),'参考版的天气、计时与日文标记仅用于外观对照；产品版保留 M 键和 RID 演示状态。',font=font(22),fill=DIM)
canvas.save(OUT/'10-reference-and-rid.png',optimize=True)

report=json.loads((ROOT/'geometry-review.json').read_text(encoding='utf-8'))
assert all(x['non_manifold_edges']==0 and x['volume_mm3']>0 for x in report['geometry_checks'])
assert all(im['packed'] for im in report['images'])
blend=ROOT/'blender/yuntong-rid-id-a1.blend'
assert blend.read_bytes()[:7]==b'BLENDER'
data=(ROOT/'blender/yuntong-rid-id-a1.glb').read_bytes()
magic,ver,size=struct.unpack_from('<4sII',data)
assert magic==b'glTF' and ver==2 and size==len(data)
n,kind=struct.unpack_from('<I4s',data,12);assert kind==b'JSON'
gltf=json.loads(data[20:20+n]);assert len(gltf['meshes'])==report['visible_export_meshes']
pngs=[]
for path in sorted(OUT.glob('*.png')):
    with Image.open(path) as im:
        im.verify()
    with Image.open(path) as im:pngs.append({'file':path.name,'size':list(im.size)})
result={'structural_and_control_meshes_checked':len(report['geometry_checks']),'mesh_checks_passed':True,
        'glb_mesh_count':len(gltf['meshes']),'glb_embedded_images':len(gltf.get('images',[])),
        'blend_file_header':'valid','renders':pngs,'scope':'ID visual package; not machining, print-fit, hardware or RF verification'}
(ROOT/'file-review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
