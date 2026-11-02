"""Generate original screen artwork for the Blender ID study; reference images remain untouched."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math, shutil
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets';OUT.mkdir(parents=True,exist_ok=True)
(ROOT/'renders').mkdir(exist_ok=True)
(ROOT/'blender').mkdir(exist_ok=True)
for name,src in [('reference-design.png','codex-clipboard-f8ee8dc9-37af-4dfc-89de-7f3fbf997c61.png'),('reference-rid-layout.png','codex-clipboard-0b1dd0ca-9470-4f2a-925f-5594ad0ca03c.png')]:
    shutil.copyfile(Path(r'C:/Users/YX/AppData/Local/Temp')/src,OUT/name)
W,H=840,1200
WHITE='#d7d6c9';DIM='#8c9485';ORANGE='#d57443';GRID='#37483d';BG='#030504'
def font(size,mono=False,bold=False):
    path='consolab.ttf' if mono and bold else 'consola.ttf' if mono else 'msyhbd.ttc' if bold else 'msyh.ttc'
    return ImageFont.truetype('C:/Windows/Fonts/'+path,size)
def txt(d,xy,s,size,fill=WHITE,anchor='la',mono=False,bold=False):d.text(xy,s,font=font(size,mono,bold),fill=fill,anchor=anchor)
def dot_sun(d,x,y):
    for yy in range(-4,5):
        for xx in range(-4,5):
            if xx*xx+yy*yy<=18:
                px=x+xx*8;py=y+yy*8
                d.ellipse((px-2.2,py-2.2,px+2.2,py+2.2),fill=WHITE)
    for a in range(0,360,45):
        xx=x+69*math.cos(math.radians(a));yy=y+69*math.sin(math.radians(a))
        for dx,dy in [(0,0),(-3,0),(3,0),(0,-3),(0,3)]:d.ellipse((xx+dx-1,yy+dy-1,xx+dx+1,yy+dy+1),fill=WHITE)
def dot_type(d,xy,s,size,fill=WHITE,spacing=4):
    f=font(size,True,True);bb=f.getbbox(s);mask=Image.new('L',(bb[2]+10,bb[3]-bb[1]+10));md=ImageDraw.Draw(mask)
    md.text((5,5-bb[1]),s,font=f,fill=255)
    xx=xy[0]-mask.width/2;yy=xy[1]-mask.height/2
    for y in range(0,mask.height,spacing):
        for x in range(0,mask.width,spacing):
            if mask.getpixel((x,y))>100:d.ellipse((xx+x,yy+y,xx+x+spacing*.62,yy+y+spacing*.62),fill=fill)

im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
dot_sun(d,420,169)
dot_type(d,(378,501),'FAIR',47,spacing=2);dot_type(d,(493,501),'30°',44,ORANGE,2)
dot_type(d,(420,607),'01:00',135,spacing=3)
dot_type(d,(420,706),'SAT. 18 MAY',39,spacing=2)
d.rounded_rectangle((207,1067,633,1133),radius=33,outline='#926b50',width=2)
dot_type(d,(324,1100),'press',29,spacing=2)
d.line([(385,1101),(392,1108),(404,1089)],fill=WHITE,width=3)
dot_type(d,(493,1100),'to start',29,spacing=2)
im.save(OUT/'screen-reference.png')

for mode in ('height','radar'):
    im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
    txt(d,(47,63),'云瞳 · RID',32);txt(d,(792,66),'DEMO  82%',25,anchor='ra',mono=True)
    txt(d,(47,139),'高度示意' if mode=='height' else '雷达俯视',35)
    txt(d,(792,143),'自动 · 03 目标',25,DIM,'ra')
    if mode=='height':
        txt(d,(63,214),'仰角约 20°',28,DIM)
        cx,cy=420,600
        for rx,ry in [(280,97),(173,59),(86,30)]:d.ellipse((cx-rx,cy-ry,cx+rx,cy+ry),outline=GRID,width=3)
        d.line((cx-280,cy,cx+280,cy),fill=GRID,width=2);d.line((cx,290,cx,712),fill=GRID,width=2)
        txt(d,(447,288),'高度',24,DIM)
        x,y=475,533;top=386
        d.line((cx,cy,x,y),fill=DIM,width=4);d.line((x,y,x,top),fill=ORANGE,width=4)
        d.ellipse((cx-9,cy-9,cx+9,cy+9),fill=WHITE)
        d.ellipse((x-12,y-12,x+12,y+12),outline=ORANGE,width=3)
        d.ellipse((x-13,top-13,x+13,top+13),fill=ORANGE)
        txt(d,(x,340),'UAV-01 · +62 m',30,anchor='ma',mono=True)
        txt(d,(55,757),'机头朝上',24,DIM);txt(d,(790,757),'纵向 ×2 示意',24,DIM,'ra')
    else:
        cx,cy=420,457;R=246
        for r in (82,164,246):d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=GRID,width=3)
        d.line((cx-R,cy,cx+R,cy),fill=GRID,width=2);d.line((cx,cy-R,cx,cy+R),fill=GRID,width=2)
        txt(d,(cx,cy-R-28),'N',22,DIM,'mm',True)
        r=R*168/250;x=cx+r*math.sin(math.radians(17));y=cy-r*math.cos(math.radians(17))
        d.line((cx,cy,x,y),fill=ORANGE,width=3);d.ellipse((x-10,y-10,x+10,y+10),fill=ORANGE)
        txt(d,(x+19,y-24),'01',26,ORANGE,mono=True)
        for x,y in [(295,477),(569,584)]:d.ellipse((x-7,y-7,x+7,y+7),fill=DIM)
        d.polygon([(cx,cy-14),(cx-10,cy+12),(cx+10,cy+12)],fill=WHITE)
        txt(d,(55,757),'机头朝上',24,DIM);txt(d,(790,757),'范围 250 m',24,DIM,'ra')
    d.line((48,806,792,806),fill='#27382e',width=2)
    txt(d,(49,849),'UAV-01',38,mono=True);txt(d,(792,855),'已选定',27,ORANGE,'ra')
    d.line([(672,873),(680,881),(695,858)],fill=ORANGE,width=3)
    txt(d,(49,923),'水平距离',26,DIM);txt(d,(451,923),'相对高度≈',26,DIM)
    txt(d,(49,981),'168 m',72,mono=True);txt(d,(451,981),'+62 m',72,mono=True)
    d.line((49,1094,792,1094),fill='#27382e',width=2)
    txt(d,(49,1125),'广播估算 · 0.8 s · 右前方 17°',24,DIM)
    im.save(OUT/f'screen-{mode}.png')
print('Created 3 screen artworks and copied 2 untouched reference images.')
