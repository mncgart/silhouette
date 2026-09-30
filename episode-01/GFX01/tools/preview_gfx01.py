"""Animatic preview of GFX01 (same layout + timing as GFX01-build.jsx).

Not the final render — After Effects is. This only checks composition and pacing.
Usage: python3 preview_gfx01.py <out_dir> [--assets DIR] [--cairo Cairo.ttf]
Needs Pillow (with raqm for Arabic), numpy, ffmpeg.
"""
import argparse, math, os, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps, ImageChops

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("--assets", default=os.path.join(os.path.dirname(__file__), "..", "GFX01_assets"))
ap.add_argument("--cairo", default="Cairo.ttf")
ap.add_argument("--scale", type=float, default=0.5)
args = ap.parse_args()
os.makedirs(args.out, exist_ok=True)

K = args.scale
W, H, FPS, DUR = int(1920 * K), int(1080 * K), 30, 9.0
ZOOM = 2666.667
RED = (177, 29, 36)
INK = (23, 23, 23)
PAPER = (190, 190, 185)
PRINT = (244, 241, 233)
TITLE, YA, YB, KICK = "لجنة أميركا أولًا", "1940", "1941", "AMERICA FIRST COMMITTEE"
T = dict(flash1=3/30, flash2=7/30, shrink0=.40, shrink1=.95, panel0=.45, fg0=.55, bgf=1.40,
         title0=.75, title1=1.25, stars0=.95, yearA0=1.25, dash0=1.62, yearB0=1.72,
         ruler0=1.40, ruler1=2.10, kicker0=1.95, poster0=1.85, hold0=2.40, out0=8.15, out1=8.55)


def font(path, size, var=None):
    f = ImageFont.truetype(path, max(1, int(size)))
    if var:
        try: f.set_variation_by_name(var)
        except Exception: pass
    return f

AR = lambda s: font(args.cairo, s, "Black")
LAT = lambda s: font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", s)
SER = lambda s: font("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", s)

# ── easing ──
def bez(t, x1, y1, x2, y2):
    lo, hi = 0.0, 1.0
    for _ in range(30):
        m = (lo + hi) / 2
        x = 3*(1-m)**2*m*x1 + 3*(1-m)*m*m*x2 + m**3
        lo, hi = (m, hi) if x < t else (lo, m)
    m = (lo + hi) / 2
    return 3*(1-m)**2*m*y1 + 3*(1-m)*m*m*y2 + m**3

def ease(t, out_inf=.3, in_inf=.8):
    t = min(1, max(0, t))
    return bez(t, out_inf, 0, 1 - in_inf, 1)

def keys(t, ks):
    """ks: [(time, value, outInfluence, inInfluenceOfNext)] piecewise eased."""
    if t <= ks[0][0]: return ks[0][1]
    for i in range(len(ks) - 1):
        t0, v0 = ks[i][0], ks[i][1]
        t1, v1 = ks[i+1][0], ks[i+1][1]
        if t <= t1:
            u = ease((t - t0) / (t1 - t0), ks[i][2] if len(ks[i]) > 2 else .3, ks[i+1][3] if len(ks[i+1]) > 3 else .8)
            if isinstance(v0, tuple): return tuple(a + (b - a) * u for a, b in zip(v0, v1))
            return v0 + (v1 - v0) * u
    return ks[-1][1]

# ── assets / placeholders ──
def find(key):
    d = args.assets
    if os.path.isdir(d):
        for n in os.listdir(d):
            if n.lower().startswith(key.lower()) and n.lower().rsplit(".", 1)[-1] in ("jpg", "jpeg", "png", "tif", "tiff", "webp"):
                return Image.open(os.path.join(d, n)).convert("RGB")
    return None

rng = np.random.default_rng(3)
def placeholder(w, h, label, tone=(200, 200, 196), dark=(50, 50, 50)):
    y = np.linspace(0, 1, h)[:, None]; x = np.linspace(0, 1, w)[None, :]
    g = np.clip(0.55 * x + 0.45 * y + rng.normal(0, .06, (h, w)), 0, 1)
    arr = np.stack([dark[i] + (tone[i] - dark[i]) * (1 - g) for i in range(3)], -1).astype(np.uint8)
    im = Image.fromarray(arr)
    d = ImageDraw.Draw(im)
    f = LAT(w / 18)
    d.multiline_text((w / 2, h / 2), label, font=f, fill=(20, 20, 20), anchor="mm", align="center")
    return im

def cover(im, w, h):
    return ImageOps.fit(im, (int(w), int(h)), Image.LANCZOS)

def bw(im, contrast=1.2):
    g = ImageOps.grayscale(im)
    g = Image.eval(g, lambda v: max(0, min(255, int((v - 128) * contrast + 124))))
    return g.convert("RGB")

random.seed(7)
def torn(x0, y0, x1, y1, sides, amp, step):
    v = []
    j = lambda: random.uniform(-amp, amp) * (2.2 if random.random() < .12 else 1)
    x = x0
    if "t" in sides:
        while x < x1: v.append((x, y0 + j())); x += random.uniform(step * .5, step * 1.4)
    else: v.append((x0, y0))
    y = y0
    if "r" in sides:
        while y < y1: v.append((x1 + j(), y)); y += random.uniform(step * .5, step * 1.4)
    else: v.append((x1, y0))
    x = x1
    if "b" in sides:
        while x > x0: v.append((x, y1 + j())); x -= random.uniform(step * .5, step * 1.4)
    else: v.append((x1, y1))
    y = y1
    if "l" in sides:
        while y > y0: v.append((x0 + j(), y)); y -= random.uniform(step * .5, step * 1.4)
    else: v.append((x0, y1))
    return v

S = lambda v: v * K  # design px → preview px

# ── pre-rendered layers (full-frame RGBA at preview scale, design coords) ──
def layer(): return Image.new("RGBA", (W, H), (0, 0, 0, 0))

def build_bg():
    bw_, bh = int(W * 1.2), int(H * 1.2)
    im = Image.new("RGB", (bw_, bh), PAPER)
    d = ImageDraw.Draw(im)
    random.seed(21)
    ox, oy = (bw_ - W) / 2, (bh - H) / 2
    scraps = [(-60, -40, 760, 700), (620, -80, 1380, 560), (1220, -60, 2360, 620), (-80, 560, 900, 1420), (780, 480, 1640, 1420), (1500, 560, 2380, 1420)]
    heads = ["AMERICA FIRST", "LINDBERGH SPEAKS", "KEEP OUT OF WAR", "RALLY TONIGHT", "NEUTRALITY", "THE NATION DEBATES"]
    for i, (a, b, c, e) in enumerate(scraps):
        a, b, c, e = a - 190, b - 140, c - 190, e - 140
        tone = int(random.uniform(.70, .82) * 255)
        pts = [(S(x) + ox, S(y) + oy) for x, y in torn(a, b, c, e, "lrtb", 7, 16)]
        sh = Image.new("L", im.size, 0); ImageDraw.Draw(sh).polygon([(x + 2, y + 2) for x, y in pts], fill=90)
        im.paste((60, 60, 60), (0, 0), sh.filter(ImageFilter.GaussianBlur(4)))
        d.polygon(pts, fill=(tone, tone, tone - 3))
        d.text((S(a + 24) + ox, S(b + 40) + oy), heads[i], font=SER(S(random.uniform(70, 110))), fill=(tone - 55,) * 3)
        for ci in range(int((c - a) / 200)):
            x = S(a + 20 + ci * 200) + ox
            for ly in range(int(b + 170), int(e - 20), 16):
                if random.random() < .06: continue
                d.line([(x, S(ly) + oy), (x + S(random.uniform(150, 180)), S(ly) + oy)], fill=(tone - 70,) * 3, width=max(1, int(S(7))))
    n = rng.normal(0, 14, (bh, bw_, 1))
    arr = np.clip(np.asarray(im).astype(float) + n, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)

def build_panel(crowd):
    im = layer(); d = ImageDraw.Draw(im)
    random.seed(33)
    dk = [(S(x), S(y)) for x, y in torn(1440, -60, 1990, 300, "lb", 9, 18)]
    pv = [(S(x), S(y)) for x, y in torn(1110, -60, 1990, 1140, "l", 12, 20)]
    sh = Image.new("L", (W, H), 0); ImageDraw.Draw(sh).polygon([(x - 4, y + 3) for x, y in pv], fill=140)
    im.paste((0, 0, 0, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(6)))
    d.polygon(dk, fill=(26, 26, 26, 255))
    red = Image.new("RGB", (W, H), RED)
    c = cover(bw(crowd, 1.35), S(900), S(1180))
    full = Image.new("RGB", (W, H), (255, 255, 255)); full.paste(c, (int(S(1110)), int(S(-60))))
    red = ImageChops.multiply(red, Image.blend(Image.new("RGB", (W, H), (255, 255, 255)), full, .85))
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).polygon(pv, fill=255)
    im.paste(red, (0, 0), m)
    d.line(pv + [pv[0]], fill=(242, 240, 230, 210), width=max(1, int(S(5))))
    return im

def build_fg(crowd):
    im = layer(); random.seed(51)
    pv = [(S(x), S(y)) for x, y in torn(-60, 880, 760, 1140, "tr", 14, 22)]
    c = bw(crowd, 1.3); c = Image.eval(cover(c, S(1000), S(560)), lambda v: int(v * .55))
    full = Image.new("RGB", (W, H)); full.paste(c, (int(S(-100)), int(S(620))))
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).polygon(pv, fill=255)
    im.paste(full, (0, 0), m)
    return im

def make_print(src, w, h, b, look):
    img = cover(src, S(w), S(h))
    if look == "bw": img = bw(img, 1.22)
    p = Image.new("RGB", (int(S(w + 2 * b)), int(S(h + 2 * b))), PRINT)
    p.paste(img, (int(S(b)), int(S(b))))
    return p.convert("RGBA")

platform = find("GFX01_Lindbergh_AFC_Platform") or placeholder(1600, 1200, "LINDBERGH — PLATFORM\nGFX01_Lindbergh_AFC_Platform")
poster = find("GFX01_AFC_Poster") or placeholder(900, 1200, "AFC POSTER", tone=(236, 150, 90), dark=(150, 60, 30))
crowd = find("GFX01_Lindbergh_Crowd") or placeholder(1920, 1080, "CROWD")

BG = build_bg()
PANEL = build_panel(crowd)
FG = build_fg(crowd).filter(ImageFilter.GaussianBlur(S(12)))
HERO = make_print(platform, 1000, 740, 26, "bw")
POSTER = make_print(poster, 340, 460, 14, "color")

# title glyph image
tf = AR(S(108))
tb = tf.getbbox(TITLE, direction="rtl", language="ar")
TITLE_IM = Image.new("RGBA", (tb[2] - tb[0] + 4, tb[3] - tb[1] + 4), (0, 0, 0, 0))
ImageDraw.Draw(TITLE_IM).text((-tb[0] + 2, -tb[1] + 2), TITLE, font=tf, fill=RED + (255,), direction="rtl", language="ar")

YF = AR(S(200))
YEAR_RIGHT, YEAR_Y = 940, 452

def year_layout():
    chars = list(YA + "-" + YB)
    ws = [S(200) * .42 if c == "-" else YF.getbbox(c)[2] - YF.getbbox(c)[0] + S(4) for c in chars]
    tot = sum(ws); k = min(1, S(790) / tot)
    x = S(YEAR_RIGHT) - tot * k; out = []
    for c, w in zip(chars, ws):
        out.append((c, x + w * k / 2, k)); x += w * k
    return out
YL = year_layout()

def paste_scaled(dst, im, cx, cy, s, rot=0, alpha=1.0, blur=0):
    if s <= 0.001 or alpha <= 0: return
    w, h = max(1, int(im.width * s)), max(1, int(im.height * s))
    t = im.resize((w, h), Image.BILINEAR)
    if rot: t = t.rotate(rot, Image.BILINEAR, expand=True)
    if blur > 0.3: t = t.filter(ImageFilter.GaussianBlur(blur))
    if alpha < 1:
        a = t.getchannel("A").point(lambda v: int(v * alpha)); t.putalpha(a)
    dst.alpha_composite(t, (int(cx - t.width / 2), int(cy - t.height / 2))) if (cx - t.width / 2 > -1e5) else None

def safe_comp(dst, t, x, y):
    x, y = int(x), int(y)
    box = (max(0, x), max(0, y), min(W, x + t.width), min(H, y + t.height))
    if box[0] >= box[2] or box[1] >= box[3]: return
    crop = t.crop((box[0] - x, box[1] - y, box[2] - x, box[3] - y))
    dst.alpha_composite(crop, (box[0], box[1]))

def put(dst, im, cx, cy, s, rot=0, alpha=1.0, blur=0, shadow=0):
    if s <= 0.001 or alpha <= 0.001: return
    w, h = max(1, int(im.width * s)), max(1, int(im.height * s))
    t = im.resize((w, h), Image.BILINEAR)
    if rot: t = t.rotate(rot, Image.BICUBIC, expand=True)
    if blur > 0.3: t = t.filter(ImageFilter.GaussianBlur(blur))
    if alpha < 1: t.putalpha(t.getchannel("A").point(lambda v: int(v * alpha)))
    if shadow > 0:
        sh = Image.new("RGBA", t.size, (0, 0, 0, 0)); sh.putalpha(t.getchannel("A").point(lambda v: int(v * shadow)))
        sh = sh.filter(ImageFilter.GaussianBlur(S(14)))
        safe_comp(dst, sh, cx - t.width / 2 + S(6), cy - t.height / 2 + S(9))
    safe_comp(dst, t, cx - t.width / 2, cy - t.height / 2)

def cam(t):
    # camera x, y, distance offset (matches the jsx keys)
    return keys(t, [(0, (30, 10, -60), .33), (T["hold0"], (8, 0, 40), .4, .6), (DUR, (-22, -6, 150), .33, .4)])

def proj(t, z):
    cx, cy, push = cam(t)
    dist = ZOOM - push + z
    f = ZOOM / dist
    return f, cx, cy

def view(dst, lay, t, z, extra=1.0, dx=0, dy=0):
    """place a full-frame design layer at depth z (layer pre-compensated so it matches at z)"""
    f, cx, cy = proj(t, z)
    s = f * (ZOOM + z) / ZOOM * extra
    put(dst, lay, W / 2 + S(dx - cx) * f, H / 2 + S(dy - cy) * f, s)

grain_bank = [Image.fromarray(np.clip(rng.normal(128, 18, (H, W)), 0, 255).astype(np.uint8)) for _ in range(6)]

def frame(t):
    im = Image.new("RGBA", (W, H), PAPER + (255,))
    # BG
    blur = keys(t, [(0, 22, .2), (T["bgf"], 1.5, .3, .85)])
    bgl = BG.convert("RGBA").filter(ImageFilter.GaussianBlur(S(blur)))
    dark = keys(t, [(0, .62, .2), (T["bgf"], 1.0, .3, .85)])
    bgl = Image.eval(bgl.convert("RGB"), lambda v: int(v * dark)).convert("RGBA")
    f, cx, cy = proj(t, 700)
    put(im, bgl, W / 2 - S(cx) * f, H / 2 - S(cy) * f, f * (ZOOM + 700) / ZOOM * 1.02)
    # PANEL
    px = keys(t, [(T["panel0"], 820, .22), (T["panel0"] + .32, -22, .55, .55), (T["panel0"] + .48, 0, .3, .85)])
    view(im, PANEL, t, 260, dx=px)
    # TEXT block (z 60)
    txt = layer()
    # year digits
    dash_i = len(YA)
    for i, (c, x, k) in enumerate(YL):
        if c == "-":
            sx = keys(t, [(T["dash0"], 0, .3), (T["dash0"] + .25, 1.08, .55, .7), (T["dash0"] + .36, 1.0, .3, .85)])
            dw, dh = S(200) * .42 * k * .78, S(200) * k * .12
            if sx > 0:
                ImageDraw.Draw(txt).rectangle([x - dw / 2, S(YEAR_Y) - dh / 2, x - dw / 2 + dw * sx, S(YEAR_Y) + dh / 2], fill=RED)
            continue
        partB = i > dash_i; local = i - dash_i - 1 if partB else i
        t0 = (T["yearB0"] if partB else T["yearA0"]) + local * 2 / 30
        if t < t0 - 1 / 30: continue
        if local >= 2:
            steps = 6 + (local - 2) * 2; tl = t0 + steps * 2 / 30
            ch = c if t >= tl else str((int(c) + steps - int((t - t0) * 15)) % 10)
            a = 1.0 if t >= tl else .4
            sc = keys(t, [(t0, 1.0), (tl, 1.12, .2, .6), (tl + .22, .985, .55, .55), (tl + .34, 1, .3, .85)])
            bl = 0 if t >= tl else S(6)
        else:
            ch = c
            a = keys(t, [(t0, 0, .3), (t0 + .18, 1, .5, .7)])
            sc = keys(t, [(t0, 1.25, .2), (t0 + .24, .98, .55, .55), (t0 + .34, 1, .3, .85)])
            bl = keys(t, [(t0, S(14), .2), (t0 + .22, 0, .5, .8)])
        bb = YF.getbbox(ch)
        g = Image.new("RGBA", (bb[2] - bb[0] + 8, bb[3] - bb[1] + 8), (0, 0, 0, 0))
        ImageDraw.Draw(g).text((-bb[0] + 4, -bb[1] + 4), ch, font=YF, fill=INK + (255,))
        put(txt, g, x, S(YEAR_Y), sc * k, alpha=a, blur=bl, shadow=.3)
    # title wipe (right → left) + settle
    u = keys(t, [(T["title0"], 0, .25), (T["title1"], 1, .4, .85)])
    if u > 0:
        ti = TITLE_IM.copy()
        m = Image.new("L", ti.size, 0)
        wx = ti.width * (1 - u) - S(40)
        ImageDraw.Draw(m).rectangle([wx, 0, ti.width, ti.height], fill=255)
        m = m.filter(ImageFilter.GaussianBlur(S(14)))
        ti.putalpha(ImageChops.multiply(ti.getchannel("A"), m))
        sc = keys(t, [(T["title0"], 1.04, .2), (T["title1"] + .15, 1.0, .3, .85)])
        bl = keys(t, [(T["title0"], S(12), .2), (T["title1"], 0, .3, .85)])
        put(txt, ti, S(YEAR_RIGHT) - ti.width * sc / 2, S(262), sc, blur=bl, shadow=.25)
    # stars
    d = ImageDraw.Draw(txt)
    for si in range(3):
        ts = T["stars0"] + si * 3 / 30
        sc = keys(t, [(ts, 0, .2), (ts + .2, 1.25, .55, .55), (ts + .32, 1, .3, .85)])
        if sc <= 0: continue
        cx0, cy0, ro, ri = S(YEAR_RIGHT - 14 - si * 36), S(168), S(15) * sc, S(6.2) * sc
        pts = [(cx0 + (ro if j % 2 == 0 else ri) * math.sin(j * math.pi / 5), cy0 - (ro if j % 2 == 0 else ri) * math.cos(j * math.pi / 5)) for j in range(10)]
        d.polygon(pts, fill=RED)
    # ruler
    xs = list(range(YEAR_RIGHT, 169, -24))
    e = keys(t, [(T["ruler0"], 0, .3), (T["ruler1"], 1, .4, .85)])
    nshow = int(e * len(xs) + .001)
    for n_, x in enumerate(xs[:nshow]):
        hh = 12 if n_ % 5 == 0 else 6
        d.line([(S(x), S(600 - hh)), (S(x), S(600 + hh))], fill=(33, 33, 33), width=max(1, int(S(3))))
    if e > 0:
        cxr = S(YEAR_RIGHT + (170 + 12 - YEAR_RIGHT) * e)
        d.polygon([(cxr - S(8), S(574)), (cxr + S(8), S(574)), (cxr, S(588))], fill=RED)
    # kicker
    kt = keys(t, [(T["kicker0"], 0, .3), (T["kicker0"] + .6, 1, .4, .8)])
    if kt > 0:
        kf = LAT(S(22)); trk = keys(t, [(T["kicker0"], S(9), .2), (T["kicker0"] + .7, S(2.5), .3, .85)])
        x = S(YEAR_RIGHT); chars = list(KICK)[::-1]
        for j, ch in enumerate(chars):
            cw = kf.getlength(ch)
            if (len(chars) - 1 - j) / len(chars) < kt:
                d.text((x - cw, S(648)), ch, font=kf, fill=(36, 36, 36, 200), anchor="lm")
            x -= cw + trk
    view(im, txt, t, 60)
    # HERO print
    f, cx, cy = proj(t, 0)
    fullS = max(1920 / 1000, 1080 / 740) * 1.06
    s = keys(t, [(0, fullS * 1.04, .33), (T["shrink0"], fullS, .22, .33), (T["shrink0"] + .34, .78 * .965, .55, .55), (T["shrink1"] + .12, .78, .3, .85)])
    pos = keys(t, [(0, (960, 540)), (T["shrink0"], (960, 540), .22), (T["shrink1"], (1412, 590), .3, .85)])
    rot = keys(t, [(T["shrink0"], 0, .22), (T["shrink1"] + .1, -2.2, .3, .85)])
    if t > T["hold0"]: rot += .35 * min(1, (t - T["hold0"]) / .8) * math.sin(2 * math.pi * .11 * t + .6)
    jx = jy = 0
    fr_ = int(t * 30)
    if 2 <= fr_ <= 10:
        random.seed(99 + fr_); jx, jy = random.uniform(-10, 10) * s, random.uniform(-7, 7) * s
    h = HERO
    if T["flash1"] <= t < T["flash1"] + 2 / 30 or T["flash2"] <= t < T["flash2"] + 1 / 30:
        h = ImageOps.invert(HERO.convert("RGB")).convert("RGBA")
    shade = keys(t, [(T["shrink0"], 0), (T["shrink1"], .6)])
    put(im, h, W / 2 + (S(pos[0] + jx) - W / 2 - S(cx)) * f, H / 2 + (S(pos[1] + jy) - H / 2 - S(cy)) * f, s * f, rot=-rot, shadow=shade)
    # POSTER
    f, cx, cy = proj(t, -60)
    ps = .62 * (ZOOM - 60) / ZOOM
    sc = keys(t, [(T["poster0"], 0, .2), (T["poster0"] + .26, ps * 1.06, .55, .55), (T["poster0"] + .42, ps, .3, .85)])
    rot = keys(t, [(T["poster0"], -16, .2), (T["poster0"] + .42, -6, .3, .85)])
    if t > T["hold0"]: rot += .5 * min(1, (t - T["hold0"]) / .8) * math.sin(2 * math.pi * .13 * t + 1.9)
    bl = keys(t, [(T["poster0"], S(10), .2), (T["poster0"] + .25, 0, .3, .85)])
    put(im, POSTER, W / 2 + (S(1118) - W / 2 - S(cx)) * f, H / 2 + (S(272) - H / 2 - S(cy)) * f, sc * f, rot=-rot, blur=bl, shadow=.55)
    # FG
    fy = keys(t, [(T["fg0"], (-40, 240), .22), (T["fg0"] + .5, (0, 0), .3, .85)])
    view(im, FG, t, -480, dx=fy[0], dy=fy[1])
    # OUT wipe
    for off, col, rot in ((-2, (36, 36, 36), -1.5), (2, PAPER, 2.5)):
        x = keys(t, [(T["out0"] + off / 30, 0, .2), (T["out1"] + (off + 1) / 30, 1920 + 280, .3, .85)])
        if x > 0:
            random.seed(77 + off)
            pts = [(S(px + x), S(py)) for px, py in torn(-2700, -120, 0, 1200, "r", 17, 24)]
            ImageDraw.Draw(im).polygon(pts, fill=col + (255,))
    # vignette + grain + flicker
    rgb = im.convert("RGB")
    rgb = ImageChops.multiply(rgb, VIG)
    g = grain_bank[int(t * 15) % len(grain_bank)]
    rgb = ImageChops.overlay(rgb, Image.merge("RGB", (g, g, g)))
    random.seed(int(t * 15) + 5)
    fl = 1 + random.uniform(-.012, .012)
    return Image.eval(rgb, lambda v: min(255, int(v * fl)))

yy, xx = np.mgrid[0:H, 0:W]
r = np.sqrt(((xx - W / 2) / (W * .62)) ** 2 + ((yy - H / 2) / (H * .72)) ** 2)
v = 1 - .48 * np.clip((r - .55) / .6, 0, 1)
VIG = Image.fromarray((np.stack([v] * 3, -1) * 255).astype(np.uint8))

n = int(DUR * FPS)
fdir = os.path.join(args.out, "frames"); os.makedirs(fdir, exist_ok=True)
for i in range(n):
    frame(i / FPS).save(os.path.join(fdir, f"f{i:04d}.png"))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(fdir, "f%04d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", os.path.join(args.out, "GFX01_preview.mp4")], check=True)
sel = [3, 18, 27, 36, 45, 57, 72, 150, 250]
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(args.out, "GFX01_preview.mp4"), "-vf",
                "select='" + "+".join(f"eq(n\\,{s})" for s in sel) + "',scale=640:-1,tile=3x3", "-frames:v", "1", "-vsync", "0",
                os.path.join(args.out, "GFX01_contact.png")], check=True)
print("done")
