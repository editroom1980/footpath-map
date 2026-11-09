# ホーム画面のアイコン（v268「藍の町」）を描く。
# 使い方：python3 tools/アイコンを描く.py <出力フォルダ>  → 案A_1024.png（採用）・案B・案C（不採用の比べ）ができる。
# 4つの大きさ（1024・512・192・180）は 案A_1024.png を LANCZOS で縮めて、icon-1024/512/192.png・apple-touch-icon.png にする。
# 色はアプリの新しいデザインと同じ（藍 #2E78AE・白 #F7EEDC・朱 #E9603B・淡い水色 #C4DCEE）。
import math, sys
from PIL import Image, ImageDraw, ImageFilter
OUT = sys.argv[1]
AI, AIDK, SHIRO, SHU, YAM, MIZU = '#2E78AE', '#215B87', '#F7EEDC', '#E9603B', '#E8A83A', '#C4DCEE'
S = 2048  # 2倍で描いて 1024 に縮める
def hexa(h, a=255): h = h.lstrip('#'); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4)) + (a,)
def bez(p, n=600):
    pts = []
    for seg in p:
        (x0,y0),(x1,y1),(x2,y2),(x3,y3) = seg
        for i in range(n):
            t = i / n; u = 1 - t
            pts.append((u**3*x0+3*u*u*t*x1+3*u*t*t*x2+t**3*x3, u**3*y0+3*u*u*t*y1+3*u*t*t*y2+t**3*y3))
    pts.append(p[-1][3]); return pts
def even(pts, step):
    out = [pts[0]]; acc = 0
    for a, b in zip(pts, pts[1:]):
        d = math.dist(a, b); acc += d
        if acc >= step: out.append(b); acc = 0
    return out
# 道順（下から上へ曲がる S 字）。1024 基準の座標を 2 倍
R = [((330,1060),(250,860),(700,820),(650,640)), ((650,640),(600,470),(330,540),(380,380)), ((380,380),(420,250),(600,300),(600,300))]
R = [tuple((x*2, y*2) for x, y in s) for s in R]
route = bez(R)
route = [p for p in route if math.dist(p, R[-1][3]) > 236 + 40 + 70 or p[1] > 1100]   # 札の手前で点線を止める（点が札に半分隠れないように）
def dots(d, pts, step, rh, rd, halo, col):
    for x, y in even(pts, step):
        if halo: d.ellipse((x-rh, y-rh, x+rh, y+rh), fill=hexa(halo))
    for x, y in even(pts, step):
        d.ellipse((x-rd, y-rd, x+rd, y+rd), fill=hexa(col))
def flag(d, cx, cy, sz, col):   # 札の中の旗（アプリの札と同じ形。24 の箱）
    k = sz / 24; ox, oy = cx - 10.77*k, cy - 13.1*k   # 旗の外枠（横 4.8〜17・縦 4〜22.2）の中心を丸の中心に
    d.line((ox+6*k, oy+21*k, ox+6*k, oy+4*k), fill=hexa(col), width=max(2, int(2.4*k)))
    d.ellipse((ox+6*k-1.2*k, oy+21*k-1.2*k, ox+6*k+1.2*k, oy+21*k+1.2*k), fill=hexa(col))
    d.polygon([(ox+6*k, oy+4*k), (ox+17*k, oy+4*k), (ox+14.5*k, oy+8*k), (ox+17*k, oy+12*k), (ox+6*k, oy+12*k)], fill=hexa(col))
def fuda(d, cx, cy, r, ring, ringw, col, shadow_img=None):
    d.ellipse((cx-r-ringw*0.8, cy-r-ringw*0.8, cx+r+ringw*0.8, cy+r+ringw*0.8), fill=hexa(SHIRO))
    d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=hexa(ring))
    d.ellipse((cx-r+ringw, cy-r+ringw, cx+r-ringw, cy+r-ringw), fill=hexa(SHIRO))
    flag(d, cx, cy, r*1.15, col)
def shadow(img, cx, cy, r, a=90):
    sh = Image.new('RGBA', img.size, (0,0,0,0)); ImageDraw.Draw(sh).ellipse((cx-r, cy-r+16, cx+r, cy+r+16), fill=(10,30,50,a))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(22)))
END = R[-1][3]

def town(d, line, river, alpha_road=70):   # 町の地図を抽象化（道の格子・川）
    import random; random.seed(7)
    # 川（左上から右下へ）
    rv = bez([((-100,700),(500,600),(900,1500),(2200,1300))])
    for x, y in rv[::2]: d.ellipse((x-70, y-70, x+70, y+70), fill=hexa(river))
    # 道（少し傾けた格子）
    ang = math.radians(-14); ca, sa = math.cos(ang), math.sin(ang)
    for i in range(-3, 7):
        o = i * 430 + random.randint(-90, 90)
        w = 30 if i in (1, 4) else 12
        a = (o*ca - (-400)*sa, o*sa + (-400)*ca); b = (o*ca - 2600*sa, o*sa + 2600*ca)
        d.line((a, b), fill=hexa(line, alpha_road if w < 20 else alpha_road + 60), width=w)
        a = ((-400)*ca - o*sa, (-400)*sa + o*ca); b = (2600*ca - o*sa, 2600*sa + o*ca)
        d.line((a, b), fill=hexa(line, alpha_road if w < 20 else alpha_road + 60), width=w)

def make(kind):
    img = Image.new('RGBA', (S, S), hexa(AI if kind != 'B' else SHIRO))
    lay = Image.new('RGBA', (S, S), (0,0,0,0)); d = ImageDraw.Draw(lay)
    if kind == 'A':
        town(d, SHIRO, MIZU, 46)
        img.alpha_composite(lay); lay = Image.new('RGBA', (S, S), (0,0,0,0)); d = ImageDraw.Draw(lay)
        dots(d, route, 118, 52, 34, SHIRO, SHU)
        img.alpha_composite(lay); shadow(img, *END, 250)
        d = ImageDraw.Draw(img); fuda(d, END[0], END[1], 236, AI, 40, AI)
    if kind == 'B':
        # 等高線（白の地に薄い茶の輪）
        for k in range(9):
            r = 260 + k * 150
            d.ellipse((1500 - r*1.15, 300 - r*0.8, 1500 + r*1.15, 300 + r*0.8), outline=hexa('#E6D6B4'), width=8)
        img.alpha_composite(lay); lay = Image.new('RGBA', (S, S), (0,0,0,0)); d = ImageDraw.Draw(lay)
        dots(d, route, 118, 0, 36, None, SHU)
        img.alpha_composite(lay); shadow(img, *END, 250, 60)
        d = ImageDraw.Draw(img); fuda(d, END[0], END[1], 236, AI, 40, AI)
    if kind == 'C':
        # 藍の地に白の点線（今のアイコンの組み方のまま）。ゴールの札は朱の縁
        top = Image.new('RGBA', (S, S), hexa(AIDK)); m = Image.linear_gradient('L').resize((S, S))
        img = Image.composite(img, top, m.point(lambda v: 255 - int(v * 0.55)))
        d = ImageDraw.Draw(img)
        for x, y in even(route, 118):
            d.ellipse((x-38, y-38, x+38, y+38), fill=hexa(SHIRO))
        shadow(img, *END, 250, 110)
        d = ImageDraw.Draw(img); fuda(d, END[0], END[1], 236, SHU, 40, AI)
    return img.convert('RGB').resize((1024, 1024), Image.LANCZOS)

for k in 'ABC': make(k).save(f'{OUT}/案{k}_1024.png')
