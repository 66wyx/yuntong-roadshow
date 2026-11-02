"""Generate review drawings and board header from design.json + gpio.csv. Stdlib only."""
from pathlib import Path
import csv
import html
import json

ROOT = Path(__file__).resolve().parents[1]
cfg = json.loads((ROOT/'design.json').read_text(encoding='utf-8'))
MECH=ROOT/'mechanical'/'generated'; UI=ROOT/'interface'; ELEC=ROOT/'electrical'
for folder in (MECH,UI,ELEC): folder.mkdir(parents=True,exist_ok=True)


def svg(w,h,body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<style>text{{font-family:'Microsoft YaHei','Segoe UI',sans-serif}}.dim{{fill:#47564d;font-size:13px}}.small{{fill:#59685e;font-size:12px}}</style>
{body}</svg>'''


def text(x,y,s,size=14,fill='#e9eee6',anchor='start',extra=''):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" {extra}>{html.escape(str(s))}</text>'


def rect(x,y,w,h,fill,stroke='none',r=0,extra=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" {extra}/>'


def line(x1,y1,x2,y2,stroke='#426052',extra=''):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" {extra}/>'


def screen(mode):
    p=[rect(0,0,240,320,'#101813'),text(10,20,'云瞳 · RID',12),text(230,20,'演示 · 82%',11,anchor='end'),
       text(10,43,'雷达俯视' if mode=='radar' else '高度示意',13),text(230,43,'自动 · 3 目标',10,'#a1b4a3','end')]
    if mode=='radar':
        for r in (24,48,70): p.append(f'<circle cx="120" cy="126" r="{r}" fill="none" stroke="#375443"/>')
        p += [line(50,126,190,126),line(120,56,120,196),text(120,66,'N',9,'#b1c7b2','middle'),
              '<path d="M120 119 L115 132 L125 132 Z" fill="#dce9df"/>',
              line(120,126,140,86,'#e7783f'),'<circle cx="140" cy="86" r="5" fill="#ed8045"/>',
              '<circle cx="83" cy="119" r="3" fill="#819c85"/><circle cx="157" cy="161" r="3" fill="#819c85"/>',
              text(147,79,'01',10,'#ed8045'),text(10,211,'机头朝上',10,'#a1b4a3'),text(230,211,'范围 250 m',10,'#a1b4a3','end')]
    else:
        p += [text(18,65,'仰角约 20°',11,'#a1b4a3'),
              '<ellipse cx="120" cy="162" rx="88" ry="29" fill="none" stroke="#375443"/>',
              '<ellipse cx="120" cy="162" rx="44" ry="15" fill="none" stroke="#375443"/>',
              line(32,162,208,162),line(120,72,120,193),text(128,79,'高度',10,'#a1b4a3'),
              line(120,162,139,142,'#c4dac9'),line(139,142,139,101,'#ed8045','stroke-width="2"'),
              '<circle cx="120" cy="162" r="3.5" fill="#e1eee3"/><circle cx="139" cy="142" r="4.5" fill="none" stroke="#ed8045"/><circle cx="139" cy="101" r="5.5" fill="#ed8045"/>',
              text(139,90,'UAV-01 · +62 m',11,anchor='middle'),text(10,211,'机头朝上',10,'#a1b4a3'),text(230,211,'纵向 ×2 示意',10,'#a1b4a3','end')]
    p += [text(10,233,'UAV-01',15),text(230,233,'✓ 选定目标',11,'#ed8045','end'),
          text(10,256,'水平距离',10,'#a1b4a3'),text(126,256,'相对高度≈',10,'#a1b4a3'),
          text(10,282,'168 m',25),text(126,282,'+62 m',25),
          line(10,292,230,292),text(10,309,'广播估算 · 0.8 s · 右前方 17°',10,'#a1b4a3')]
    return svg(240,320,''.join(p))


for mode in ('radar','height'): (UI/f'{mode}-demo.svg').write_text(screen(mode),encoding='utf-8')

# Front control drawing, body millimetres scaled uniformly. Text remains screen-aligned.
W,H=cfg['case']['width'],cfg['case']['height']; scale=6.5; ox,oy=80,90
def sx(x): return ox+x*scale
def sy(y): return oy+(H-y)*scale
def mr(cx,cy,w,h,fill,stroke='none',r=0,extra=''):
    return rect(sx(cx-w/2),sy(cy+h/2),w*scale,h*scale,fill,stroke,r*scale,extra)
p=[rect(0,0,1080,760,'#f5f5ef'),text(52,38,'云瞳 RID · EVT1-A0 正面控制图',24,'#172d21'),text(52,63,'单位 mm · 名义尺寸 · 装配评审稿',13,'#536556'),
   mr(W/2,H/2,W,H,'#a5a59b','#5b665b',8)]
d=cfg['display'];cx,cy=d['center_xy'];cw,ch,ct=d['cover_size'];aw,ah=d['active_size']
p += [mr(cx,cy,cw,ch,'#101813','#283c2e',3)]
ui=screen('height').split('>',1)[1].rsplit('</svg>',1)[0]
p += [f'<svg x="{sx(cx-aw/2)}" y="{sy(cy+ah/2)}" width="{aw*scale}" height="{ah*scale}" viewBox="0 0 240 320">{ui}</svg>']
for k in cfg['keys']:
    x,y=k['center_xy'];w,h,t=k['size'];fill='#ed8045' if k['id']=='confirm' else '#c8c6b9'
    if k['shape']=='circle':p.append(f'<circle cx="{sx(x)}" cy="{sy(y)}" r="{w*scale/2}" fill="{fill}" stroke="#5c6357"/>')
    elif k['shape'].startswith('half_capsule'):
        sign=1 if k['id']=='up' else -1
        arc_y=sy(y+sign*(h/2-w/2));flat_y=sy(y-sign*h/2);left=sx(x-w/2);right=sx(x+w/2);rr=w*scale/2
        path=f'M {left} {flat_y} L {right} {flat_y} L {right} {arc_y} A {rr} {rr} 0 0 {0 if sign==1 else 1} {left} {arc_y} Z'
        p.append(f'<path d="{path}" fill="{fill}" stroke="#5c6357"/>')
    else:p.append(mr(x,y,w,h,fill,'#5c6357',1.1))
    p.append(text(sx(x),sy(y)+6,{'up':'▲','down':'▼','confirm':'✓','mode':'M'}[k['id']],21,'#354638','middle'))
p += [mr(66.5,76.3,12,3.4,'#949b8a','#5c6357',.7),mr(67,70.2,3.1,.7,'#ed8045'),text(sx(67),sy(67.5),'AIRSPACE',9,'#354638','middle'),text(sx(67),sy(3.6),'云瞳',12,'#354638','middle')]
p += [line(sx(0),sy(0)+30,sx(W),sy(0)+30,'#52685a'),line(sx(0),sy(0)+22,sx(0),sy(0)+38),line(sx(W),sy(0)+22,sx(W),sy(0)+38),text(sx(W/2),sy(0)+50,'82.0',15,'#304a36','middle'),
      line(ox-30,sy(0),ox-30,sy(H)),line(ox-38,sy(0),ox-22,sy(0)),line(ox-38,sy(H),ox-22,sy(H)),text(ox-40,sy(H/2),'76.0',15,'#304a36','end')]
notes=['机身：82 × 76 × 21','含按键目标：82 × 78 × 22','黑色盖板：52 × 67 × 0.8','LCD 模组：42.52 × 59.86 × 2.40','有效区：36.72 × 48.96','主板包络：74 × 68 × 1.6','上/下键：12.4 × 10.4','确认键：Ø12.4；M 键：13 × 6.5','底部 USB-C 开口：10 × 4.2','顶部电源键；内部下载测试点']
for i,n in enumerate(notes):p.append(text(655,123+i*34,n,14,'#243e2c'))
p += [text(52,660,'结构说明：两片式壳体、独立屏幕托架、可更换按键；当前不含挂绳孔、密封、卡扣和紧固件。',13,'#4c6051'),
      text(52,687,'屏幕 FPC 折弯、电池最大外形、GNSS 载板/天线净空和按键行程确认后，才能冻结 PCB 与壳体。',13,'#4c6051'),
      text(52,715,'图中数值为演示数据；不能作为实际接收、定位或测高结果。',13,'#9d582e')]
(MECH/'front-dimensions.svg').write_text(svg(1080,760,''.join(p)),encoding='utf-8')

# Placement view is package envelopes, not a footprint or copper layout.
ox,oy,scale=90,95,8
palette={'radio':'#c5d0c8','gnss':'#a8bfaf','sensor':'#e5e0b7','antenna':'#e0ca8e','reserved_area':'#ecd4b2'}
p=[rect(0,0,1080,810,'#f5f5ef'),text(45,38,'器件包络与主板位置 · 前视',23,'#172d21'),text(45,64,'坐标原点为机身左下角；此图不包含电气焊盘、走线或射频净空。',13,'#536556'),
   mr(W/2,H/2,W,H,'none','#7b897c',8),mr(41,38,74,68,'#dce8db','#3d6547',3)]
for part in cfg['parts']:
    x,y=part['center_xy'];w,h,t=part['size'];p.append(mr(x,y,w,h,palette[part['kind']],'#59705c',.3))
    p.append(text(sx(x),sy(y)+4,part['ref'],10,'#203d29','middle'))
for x,y in cfg['case']['screw_centers']:p.append(f'<circle cx="{sx(x)}" cy="{sy(y)}" r="{1.2*scale}" fill="#f5f5ef" stroke="#51664f"/>')
for k in cfg['keys']:
    x,y=k['center_xy'];p.append(mr(x,y,6,6,'#aaa996','#5c6357',.2));p.append(text(sx(x),sy(y)+4,k['id'],9,'#203d29','middle'))
for i,(name,desc) in enumerate([('U1','S3：UI / BLE / 汇聚'),('U2','C5：2.4 GHz'),('U3','C5：5.8 GHz'),('U4','MAX-M10S GNSS'),('U5','BMI270 IMU'),('U6','BMM350 地磁'),('ANT_GNSS','15 × 15 × 4 陶瓷贴片'),('PWR_AREA','电源区预留，尚非实际布局')]):
    p.append(text(790,120+i*38,f'{name}  {desc}',12,'#28442e'))
p += [text(45,758,'四角安装孔 Ø2.4；电池位于 PCB 背面；屏幕排线折回区另见 STEP。封装焊盘、测试点及元件外围待原理图完成后布局。',12,'#526652')]
(MECH/'component-placement.svg').write_text(svg(1150,810,''.join(p)),encoding='utf-8')

# Stack chart: Z is millimetres measured from rear exterior.
p=[rect(0,0,1100,700,'#f5f5ef'),text(50,38,'厚度分配与结构堆叠 · Z 轴',23,'#172d21'),text(50,64,'不同 X/Y 位置的高度包络并列显示，不能理解为全部元件上下堆在同一处。',13,'#536556')]
layers=[('后壳底',0,1.8,'#aaa99c'),('电池最大包络',2.3,8.8,'#b7c8b8'),('四层 PCB',9.4,11,'#427756'),('S3 / C5 射频模组',11,14.3,'#8e9e90'),('屏幕排线折回预留',14.4,17.08,'#d7b36f'),('LCD 模组',17.2,19.6,'#687b6d'),('黑色盖板',20.2,21,'#273b2c'),('右上 GNSS 陶瓷贴片',14.4,18.4,'#dbc48d'),('壳体正面顶层',19.2,21,'#aaa99c'),('实体键帽/柱整体',15.55,22,'#e28c56')]
base=118; unit=29
for z in range(23):p += [line(base+unit*z,90,base+unit*z,540,'#d9ded2'),text(base+unit*z,565,z,11,'#4c6250','middle')]
for i,(name,z0,z1,color) in enumerate(layers):
    yy=100+i*42;p += [rect(base+unit*z0,yy,unit*(z1-z0),25,color,r=2),text(800,yy+18,f'{name}  {z0:g}–{z1:g}',13,'#2b4530')]
p += [text(50,610,'名义间隙：电池至 PCB 0.6；射频模组至 LCD 2.9；GNSS 贴片至前壳内顶 0.8。',14,'#294b32'),text(50,640,'尚未覆盖：电池鼓胀与供应商最大公差、GNSS 载板、胶层、排线弯曲半径、线束和开关行程。',13,'#84552d')]
(MECH/'stack-dimensions.svg').write_text(svg(1100,700,''.join(p)),encoding='utf-8')

pins=list(csv.DictReader((ELEC/'gpio.csv').open(encoding='utf-8')))
nums=[int(row['s3_gpio']) for row in pins]
assert len(nums)==len(set(nums)), 'Duplicate GPIO assignment'
assert not set(nums)&{0,3,35,36,37,45,46}, 'Strap / octal-memory GPIO in assignment'
assert set(nums)<=set(range(22))|set(range(35,49)), 'Not a module GPIO'
header='// Generated by tools/generate_design.py from electrical/gpio.csv. Review before enabling board I/O.\n#pragma once\nnamespace evt1 {\n'
header+=''.join(f'inline constexpr int {row["signal"]} = {row["s3_gpio"]};\n' for row in pins)+'}\n'
(ROOT/'firmware/s3/main/board_pins.hpp').write_text(header,encoding='utf-8')
print(json.dumps({'drawings':5,'gpio_assignments':len(pins),'unique_gpio':True,'no_strap_or_octal_memory_pins':True}))
