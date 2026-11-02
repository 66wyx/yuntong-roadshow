"""Native 460 px screen artwork and untouched user references for ID-A2."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math
import shutil

ROOT = Path(__file__).resolve().parents[1]
for folder in ('assets', 'renders', 'blender', 'references'):
    (ROOT / folder).mkdir(parents=True, exist_ok=True)
refs = {
    'reference-original.png': 'codex-clipboard-f8ee8dc9-37af-4dfc-89de-7f3fbf997c61.png',
    'reference-rid.png': 'codex-clipboard-0b1dd0ca-9470-4f2a-925f-5594ad0ca03c.png',
    'reference-metal-wrap.png': 'codex-clipboard-1697f58b-8a9b-44cb-b6aa-3bd9f8c5edd4.png',
}
for dest, src in refs.items():
    shutil.copyfile(Path('C:/Users/YX/AppData/Local/Temp') / src, ROOT / 'assets' / dest)

BG = '#030605'
WHITE = '#e0e4d8'
MUTED = '#9aa99c'
GRID = '#34483c'
ORANGE = '#ef7943'

def font(size, mono=False, bold=False):
    name = ('consolab.ttf' if bold else 'consola.ttf') if mono else ('msyhbd.ttc' if bold else 'msyh.ttc')
    return ImageFont.truetype('C:/Windows/Fonts/' + name, size)

def text(d, xy, s, size=20, fill=WHITE, anchor='lt', mono=False, bold=False):
    d.text(xy, s, font=font(size, mono, bold), fill=fill, anchor=anchor)

for mode in ('height', 'radar'):
    im = Image.new('RGB', (460, 460), BG)
    d = ImageDraw.Draw(im)
    text(d, (20, 18), '云瞳', 24, bold=True)
    text(d, (108, 22), 'RID', 19, MUTED, mono=True)
    d.rounded_rectangle((277, 16, 346, 42), 5, outline=GRID, width=1)
    text(d, (311, 29), 'DEMO', 17, ORANGE, 'mm', True)
    text(d, (437, 21), '82%', 20, WHITE, 'rt', True)
    d.line((20, 54, 440, 54), fill=GRID, width=1)
    text(d, (20, 67), '高度示意' if mode == 'height' else '雷达俯视', 22)
    text(d, (440, 70), '03 目标', 18, MUTED, 'rt')
    if mode == 'height':
        cx, cy = 218, 258
        for rx, ry in ((154, 49), (98, 31), (46, 15)):
            d.ellipse((cx-rx, cy-ry, cx+rx, cy+ry), outline=GRID, width=2)
        d.line((64, cy, 372, cy), fill=GRID, width=1)
        d.line((cx, 126, cx, 307), fill=GRID, width=1)
        x, y, top = 257, 240, 162
        d.line((cx, cy, x, y), fill=MUTED, width=3)
        d.line((x, y, x, top), fill=ORANGE, width=3)
        d.ellipse((x-6, y-6, x+6, y+6), outline=ORANGE, width=2)
        d.ellipse((x-7, top-7, x+7, top+7), fill=ORANGE)
        d.ellipse((cx-5, cy-5, cx+5, cy+5), fill=WHITE)
        text(d, (x, 131), 'UAV-01', 20, ORANGE, 'mm', True)
        text(d, (20, 294), '仰角约 20°', 18, MUTED)
        text(d, (440, 294), '高度 ×2', 18, MUTED, 'rt')
    else:
        cx, cy, radius = 230, 206, 102
        for r in (34, 68, 102):
            d.ellipse((cx-r, cy-r, cx+r, cy+r), outline=GRID, width=2)
        d.line((cx-radius, cy, cx+radius, cy), fill=GRID, width=1)
        d.line((cx, cy-radius, cx, cy+radius), fill=GRID, width=1)
        r = radius * 168 / 250
        x = cx + r * math.sin(math.radians(17))
        y = cy - r * math.cos(math.radians(17))
        d.line((cx, cy, x, y), fill=ORANGE, width=2)
        d.ellipse((x-6, y-6, x+6, y+6), fill=ORANGE)
        text(d, (x+12, y-13), '01', 21, ORANGE, mono=True)
        for x, y in ((177, 220), (286, 262)):
            d.ellipse((x-4, y-4, x+4, y+4), fill=MUTED)
        d.polygon(((cx, cy-9), (cx-7, cy+7), (cx+7, cy+7)), fill=WHITE)
        text(d, (20, 294), '机头朝上', 18, MUTED)
        text(d, (440, 294), '250 m', 19, MUTED, 'rt', True)
    d.line((20, 326, 440, 326), fill=GRID, width=1)
    text(d, (20, 340), '水平距离', 18, MUTED)
    text(d, (246, 340), '相对高度≈', 18, MUTED)
    text(d, (20, 369), '168', 43, mono=True)
    text(d, (102, 389), 'm', 22, MUTED, mono=True)
    text(d, (245, 369), '+62', 43, mono=True)
    text(d, (326, 389), 'm', 22, MUTED, mono=True)
    text(d, (20, 427), 'UAV-01', 18, ORANGE, mono=True)
    text(d, (440, 427), '0.8 s  /  右前 17°', 17, MUTED, 'rt')
    im.save(ROOT / 'assets' / f'screen-{mode}-460.png')
print('Artwork: 460 x 460 px; two DEMO modes; three original reference files copied.')
