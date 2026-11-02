"""Create a review board, exact cubic SVG, verify files and zip this ID package."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import ast
import hashlib
import json
import struct
import sys
import zipfile
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parents[1]

def font(n,bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/'+('msyhbd.ttc' if bold else 'msyh.ttc'),n)

board=Image.new('RGB',(1900,1470),'#eeeee8')
d=ImageDraw.Draw(board)
d.text((65,38),'云瞳 RID  /  ID-A2',font=font(48,True),fill='#222a27')
d.text((65,111),'连续曲率四角  ·  包覆正面的铝壳  ·  AM200Q460460FLS1',font=font(25),fill='#606a63')
d.rectangle((65,165,1835,168),fill='#cb6d41')

def panel(x,y,w,h,file,title,caption):
    d.rounded_rectangle((x,y,x+w,y+h),radius=14,fill='#fafaf6')
    d.text((x+22,y+18),title,font=font(28,True),fill='#27332c')
    im=Image.open(ROOT/'renders'/file).convert('RGB')
    im.thumbnail((w-42,h-122),Image.Resampling.LANCZOS)
    board.paste(im,(x+(w-im.width)//2,y+66+(h-122-im.height)//2))
    d.text((x+22,y+h-42),caption,font=font(20),fill='#616d64')

panel(65,195,870,570,'02-front-height.png','01 / 正面比例','64 × 54 × 20 mm 目标包络；面板下沉 0.35 mm')
panel(965,195,870,570,'04-continuous-corner.png','02 / 连续曲线与金属围边','每角两段三次贝塞尔；铝壳外沿与内框平顺过渡')
panel(65,790,870,570,'06-usb-c.png','03 / Type-C 与一体侧壁','充电 / 数据接口外形；电路和插头空间待实物核对')
panel(965,790,870,570,'07-inset-rear.png','04 / 后盖内嵌','后盖嵌在铝壁以内，侧面取消上下包夹的层次')
d.text((65,1403),'外观评审模型 · UI 为 DEMO · 内部装配、射频与制造公差尚未冻结',font=font(23),fill='#677268')
board.save(ROOT/'renders/10-design-board.png')

def contour(w,h,L):
    return ' '.join([
        f'M {L} 0 H {w-L}',
        f'C {w-.72*L} 0 {w-.36*L} 0 {w-.18*L} {.18*L}',
        f'C {w} {.36*L} {w} {.72*L} {w} {L}',
        f'V {h-L}',
        f'C {w} {h-.72*L} {w} {h-.36*L} {w-.18*L} {h-.18*L}',
        f'C {w-.36*L} {h} {w-.72*L} {h} {w-L} {h}',
        f'H {L}',
        f'C {.72*L} {h} {.36*L} {h} {.18*L} {h-.18*L}',
        f'C 0 {h-.36*L} 0 {h-.72*L} 0 {h-L}',
        f'V {L}',
        f'C 0 {.72*L} 0 {.36*L} {.18*L} {.18*L}',
        f'C {.36*L} 0 {.72*L} 0 {L} 0 Z',
    ])

svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="180mm" height="106mm" viewBox="0 0 180 106">
<title>云瞳 RID ID-A2 三次贝塞尔轮廓参考</title>
<desc>Millimetres. Original G2-to-line and C2-between-cubics construction. Appearance reference only, not manufacturing CAD.</desc>
<rect width="180" height="106" fill="#f5f5ef"/>
<g font-family="Microsoft YaHei, sans-serif" fill="#27342c">
<text x="10" y="10" font-size="4" font-weight="bold">ID-A2 / 连续曲率四角</text>
<text x="10" y="16" font-size="2">64 × 54 × 20 mm 目标尺寸 · 单位 mm · 外观轮廓参考，非加工图</text>
<g transform="translate(13,26)" stroke-linejoin="round">
<path d="{contour(64,54,9.2)}" fill="#bcc2c1" stroke="#34403b" stroke-width=".3"/>
<path transform="translate(2.9,2.9)" d="{contour(58.2,48.2,6.3)}" fill="#303b35"/>
<path transform="translate(3.15,3.15)" d="{contour(57.7,47.7,6.05)}" fill="#e0e0d7"/>
<rect x="3.95" y="7.4" width="38.5" height="39.2" rx="1.6" fill="none" stroke="#97a398" stroke-width=".16" stroke-dasharray=".6 .6"/>
<rect x="4.95" y="8.6" width="36.5" height="36.5" rx="1.5" fill="#101a16"/>
<rect x="5.26" y="8.91" width="35.88" height="35.88" rx=".9" fill="none" stroke="#87a88f" stroke-width=".18"/>
<text x="23.2" y="25" font-size="2.7" fill="#e7eadd" text-anchor="middle">460 × 460</text>
<text x="23.2" y="30" font-size="2.1" fill="#99ac9f" text-anchor="middle">AA 35.88 × 35.88</text>
<rect x="48.6" y="12.65" width="10.4" height="17.9" rx="5.2" fill="#f3f1e9" stroke="#59665d" stroke-width=".2"/>
<path d="M48.6 21.6 H59" stroke="#59665d" stroke-width=".18"/>
<circle cx="53.8" cy="38" r="5.25" fill="#d87542" stroke="#6b422f" stroke-width=".2"/>
<rect x="50.05" y="45.55" width="7.5" height="3.3" rx=".85" fill="#f3f1e9" stroke="#59665d" stroke-width=".18"/>
</g>
<g stroke="#78847b" stroke-width=".2" fill="none">
<path d="M13 23 V20 M77 23 V20 M13 21.5 H77 M10 26 H7 M10 80 H7 M8.5 26 V80"/>
<path d="M13 21.5 l1 -.5 m-1 .5 l1 .5 M77 21.5 l-1 -.5 m1 .5 l-1 .5"/>
</g>
<text x="45" y="20" text-anchor="middle" font-size="2">64</text>
<text x="6.5" y="54" text-anchor="middle" font-size="2">54</text>
<text x="91" y="26" font-size="2.7" font-weight="bold">每角两段三次曲线</text>
<g transform="translate(98,34)">
<path d="M-5 0 H0 M28 28 V33" stroke="#53675b" stroke-width=".35" fill="none"/>
<path d="M0 0 C7.84 0 17.92 0 22.96 5.04 C28 10.08 28 20.16 28 28" stroke="#cf6c3d" stroke-width=".65" fill="none"/>
<path d="M0 0 L7.84 0 L17.92 0 L22.96 5.04 L28 10.08 L28 20.16 L28 28" stroke="#92a297" stroke-width=".18" stroke-dasharray=".7 .6" fill="none"/>
<g fill="#506d5a"><circle cx="0" cy="0" r=".55"/><circle cx="7.84" cy="0" r=".55"/><circle cx="17.92" cy="0" r=".55"/><circle cx="22.96" cy="5.04" r=".65"/><circle cx="28" cy="10.08" r=".55"/><circle cx="28" cy="20.16" r=".55"/><circle cx="28" cy="28" r=".55"/></g>
<text x="-.8" y="-2.5" font-size="1.8">G2 → 直边</text>
<text x="27" y="4.5" font-size="1.8">C2 连接</text>
<text x="32" y="28.5" font-size="1.8">G2 → 直边</text>
</g>
<text x="91" y="74" font-size="2">外轮廓 L = 9.2；前内框 L = 6.3</text>
<text x="91" y="79" font-size="2">L 是角部过渡长度，不是圆弧半径。</text>
<text x="91" y="84" font-size="2">机身、内框、面板使用同一曲线构造。</text>
<text x="13" y="91" font-size="2">铝壳正面直边约 2.9；打印前面板下沉 0.35；打印后盖下沉约 0.30。</text>
<text x="13" y="98" font-size="1.8" fill="#7a857b">自主构造的 iPhone 风格曲率参数；屏幕玻璃遵循供应商资料。2026-10-30</text>
</g></svg>'''
svgpath=ROOT/'references/id-a2-bezier-contours.svg'
svgpath.write_text(svg,encoding='utf-8');ET.parse(svgpath)

brief={
    'revision':'ID-A2','date':'2026-10-30','status':'appearance review, not manufacturing release',
    'body_mm':[64,54,20],'construction':'CNC wrap shell with recessed printed face and rear',
    'front_metal_width_mm':2.9,'front_recess_mm':.35,'rear_recess_mm':.30,
    'corner':{'segments_per_corner':2,'degree':3,'outer_extent_mm':9.2,'line_connection':'G2','internal_connection':'C2','source':'original parameters inspired by requested iPhone-like appearance'},
    'display':{'model':'AM200Q460460FLS1','interface':'QSPI','pixels':[460,460],'active_mm':[35.88,35.88],'envelope_mm':[38.5,39.2,2.28]},
    'ui':'native-resolution DEMO radar / height; not a live receiver',
    'charging':'USB-C mechanical feature only; circuit implementation not included',
}
(ROOT/'id-brief.json').write_text(json.dumps(brief,ensure_ascii=False,indent=2),encoding='utf-8')

for path in (ROOT/'scripts').glob('*.py'):
    ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
for path in (ROOT/'renders').glob('*.png'):
    with Image.open(path) as im:im.verify()
blend=ROOT/'blender/yuntong-rid-id-a2.blend'
assert blend.read_bytes()[:7]==b'BLENDER'
glb=ROOT/'blender/yuntong-rid-id-a2.glb'
data=glb.read_bytes()
magic,version,length=struct.unpack('<4sII',data[:12]);assert magic==b'glTF' and version==2 and length==len(data)
chunk_len,chunk_type=struct.unpack('<II',data[12:20]);assert chunk_type==0x4E4F534A
g=json.loads(data[20:20+chunk_len]);assert len(g['scenes'])==1
names=[n.get('name','') for n in g['nodes']]
assert names and all(name.startswith('RID_A2_') for name in names)
assert all('uri' not in im for im in g.get('images',[]))
report=json.loads((ROOT/'geometry-review.json').read_text(encoding='utf-8'))
assert all(v['non_manifold_edges']==0 and v['signed_volume_mm3']>0 for v in report['geometry_checks'])
review={'blend_header':'BLENDER','glb_version':version,'glb_scenes':len(g['scenes']),
        'glb_meshes':len(g['meshes']),'glb_nodes':len(names),'all_nodes_A2':True,'embedded_images':len(g.get('images',[])),
        'render_files':len(list((ROOT/'renders').glob('*.png'))),'source_scripts_parse':True,
        'main_solids_checked':len(report['geometry_checks']),'scope':'file integrity and appearance geometry; no hardware validation'}
(ROOT/'file-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')

files=[p for p in ROOT.rglob('*') if p.is_file() and p.name not in ('artifact-manifest.json',) and p.suffix not in ('.blend1','.pyc') and '__pycache__' not in p.parts]
manifest={'revision':'ID-A2','date':'2026-10-30','files':[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)]}
(ROOT/'artifact-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
archive=ROOT.parents[1]/'output/yuntong-rid-id-a2-blender-review-2026-10-30.zip'
archive.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(files+[ROOT/'artifact-manifest.json']):z.write(p,Path(ROOT.name)/p.relative_to(ROOT))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    count=len(z.namelist())
print(json.dumps({'review':review,'zip':str(archive),'zip_files':count,'zip_bytes':archive.stat().st_size},ensure_ascii=False,indent=2))
