// GFX01-build.jsx — الحلقة الأولى / GFX 01: لجنة أميركا أولًا ← 1940–1941
// After Effects 2024+ (tested target: AE 2026). File > Scripts > Run Script File…
// Keyframes only (no expressions). Re-running rebuilds everything (idempotent).
//
// Assets: put them in a folder named "GFX01_assets" next to this script
// (any of jpg/png/tif/psd). Names (prefix match, case-insensitive):
//   GFX01_AFC_Poster               ملصق لجنة أميركا أولًا
//   GFX01_Lindbergh_AFC_Platform   ليندبرغ وقادة اللجنة على المنصة
//   GFX01_Lindbergh_Crowd          حشد خارج خطاب ليندبرغ
//   GFX01_Newspaper_Texture        (optional) scanned newspaper page for the background
// Missing files are replaced by labelled placeholders so the layout still works.

(function () {

// ───────────────────────────── CONFIG ─────────────────────────────
var CFG = {
    PREFIX:   "GFX01",
    TITLE:    "لجنة أميركا أولًا",
    YEAR_A:   "1940",
    YEAR_B:   "1941",
    KICKER:   "AMERICA FIRST COMMITTEE",
    W: 1920, H: 1080, FPS: 30, DUR: 9,
    // first installed font wins (PostScript names)
    FONTS_AR:  ["Cairo-Black", "Cairo-ExtraBold", "Cairo-Bold", "Almarai-ExtraBold", "Tajawal-Black", "NotoSansArabic-Bold", "ArialMT"],
    FONTS_NUM: ["Cairo-Black", "Montserrat-Black", "Montserrat-ExtraBold", "Arial-BoldMT"],
    FONTS_LAT: ["Montserrat-SemiBold", "Montserrat-Bold", "Arial-BoldMT"],
    FONTS_NEWS:["TimesNewRomanPSMT", "Georgia", "ArialMT"],
    FONTS_HEAD:["TimesNewRomanPS-BoldMT", "Georgia-Bold", "Arial-BoldMT"],
    RED:      [0.694, 0.114, 0.141],   // #B11D24
    INK:      [0.090, 0.090, 0.090],
    PAPER:    [0.745, 0.745, 0.725],
    PRINT:    [0.955, 0.945, 0.915],   // photo border
    ZOOM:     2666.6667
};

var ASSETS = {
    poster:   { key: "GFX01_AFC_Poster",             w: 900,  h: 1200, label: "AFC POSTER" },
    platform: { key: "GFX01_Lindbergh_AFC_Platform", w: 1600, h: 1200, label: "LINDBERGH — PLATFORM" },
    crowd:    { key: "GFX01_Lindbergh_Crowd",        w: 1920, h: 1080, label: "CROWD" },
    news:     { key: "GFX01_Newspaper_Texture",      w: 2200, h: 1300, label: "", optional: true }
};

// ───────────────────────────── HELPERS ─────────────────────────────
var LOG = [];
function log(s) { LOG.push(s); }
var F = 1 / CFG.FPS;
function fr(n) { return n * F; }

var seed = 7;
function rnd() { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; }
function rr(a, b) { return a + (b - a) * rnd(); }

function tr(l)  { return l.property("ADBE Transform Group"); }
function P(l)   { return tr(l).property("ADBE Position"); }
function S(l)   { return tr(l).property("ADBE Scale"); }
function O(l)   { return tr(l).property("ADBE Opacity"); }
function R(l)   { return tr(l).property("ADBE Rotate Z"); }
function A(l)   { return tr(l).property("ADBE Anchor Point"); }

function dimsOf(p) {
    var t = p.propertyValueType;
    if (t === PropertyValueType.TwoD) return 2;
    if (t === PropertyValueType.ThreeD) return 3;
    return 1;
}
function isSpatial(p) {
    var t = p.propertyValueType;
    return t === PropertyValueType.TwoD_SPATIAL || t === PropertyValueType.ThreeD_SPATIAL;
}

// keys: [[t, value, inInfluence, outInfluence, hold]]
function addKeys(p, keys) {
    var i;
    for (i = 0; i < keys.length; i++) p.setValueAtTime(keys[i][0], keys[i][1]);
    if (p.propertyValueType === PropertyValueType.CUSTOM_VALUE || p.propertyValueType === PropertyValueType.NO_VALUE) return;
    for (i = 0; i < keys.length; i++) {
        var k = p.nearestKeyIndex(keys[i][0]);
        var n = dimsOf(p), inA = [], outA = [], d;
        var ei = keys[i][2] !== undefined ? keys[i][2] : 70;
        var eo = keys[i][3] !== undefined ? keys[i][3] : 30;
        for (d = 0; d < n; d++) { inA.push(new KeyframeEase(0, Math.max(0.1, ei))); outA.push(new KeyframeEase(0, Math.max(0.1, eo))); }
        try { p.setTemporalEaseAtKey(k, inA, outA); } catch (e) {}
        if (isSpatial(p)) {
            try {
                var z = (p.value.length === 3) ? [0, 0, 0] : [0, 0];
                p.setSpatialAutoBezierAtKey(k, false);
                p.setSpatialTangentsAtKey(k, z, z);
            } catch (e2) {}
        }
        if (keys[i][4]) p.setInterpolationTypeAtKey(k, p.keyInInterpolationType(k), KeyframeInterpolationType.HOLD);
    }
}
function holdKeys(p, list) { // [[t, v]] all HOLD
    var k2 = [];
    for (var i = 0; i < list.length; i++) k2.push([list[i][0], list[i][1], 50, 50, true]);
    addKeys(p, k2);
}
function clearKeys(p) { while (p.numKeys > 0) p.removeKey(1); }

function fxAdd(l, match, name) {
    var par = l.property("ADBE Effect Parade");
    var e = par.addProperty(match);
    if (name) e.name = name;
    return par.property(par.numProperties);
}
function setPct(p, pct) {
    var v = pct;
    try { if (p.hasMax && p.maxValue > 100.5) v = pct * p.maxValue / 100; } catch (e) {}
    p.setValue(v);
}
function tryProp(e, names, v) {
    for (var i = 0; i < names.length; i++) {
        try { var p = e.property(names[i]); if (p) { p.setValue(v); return p; } } catch (x) {}
    }
    return null;
}

function blurFx(l, v) {
    var e = fxAdd(l, "ADBE Gaussian Blur 2", "Blur");
    e.property(1).setValue(v);
    try { e.property(3).setValue(1); } catch (x) {}
    return e;
}
function blurKeys(l, keys) { // [[t,v,in,out]]
    var e = blurFx(l, keys[0][1]);
    addKeys(e.property(1), keys);
    return e;
}
function shadow(l, dist, soft, pct, dir) {
    var e = fxAdd(l, "ADBE Drop Shadow", "Shadow");
    e.property(1).setValue([0, 0, 0]);
    setPct(e.property(2), pct);
    e.property(3).setValue(dir !== undefined ? dir : 150);
    e.property(4).setValue(dist);
    e.property(5).setValue(soft);
    return e;
}
function grayscale(l, contrast, bright) {
    var t = fxAdd(l, "ADBE Tint", "B&W");
    t.property(3).setValue(100);
    var b = fxAdd(l, "ADBE Brightness & Contrast 2", "Contrast");
    b.property(1).setValue(bright || 0);
    b.property(2).setValue(contrast || 20);
}
function duotone(l, dark, light) {
    var t = fxAdd(l, "ADBE Tint", "Duotone");
    t.property(1).setValue(dark);
    t.property(2).setValue(light);
    t.property(3).setValue(100);
}

function pickFont(list) {
    for (var i = 0; i < list.length; i++) {
        try {
            if (app.fonts && app.fonts.getFontsByPostScriptName) {
                var r = app.fonts.getFontsByPostScriptName(list[i]);
                if (r && r.length) return list[i];
            } else return list[0];
        } catch (e) { return list[0]; }
    }
    return list[list.length - 1];
}

function textLayer(comp, str, font, size, color, just, rtl) {
    var l = comp.layers.addText(str);
    var sp = l.property("ADBE Text Properties").property("ADBE Text Document");
    var td = sp.value;
    try { td.resetCharStyle(); td.resetParagraphStyle(); } catch (e) {}
    td.text = str;
    td.font = font;
    td.fontSize = size;
    td.applyFill = true;
    td.fillColor = color;
    td.applyStroke = false;
    td.tracking = 0;
    td.justification = just;
    if (rtl) {
        try { td.composerEngine = ComposerEngine.UNIVERSAL_TYPE_ENGINE; } catch (e1) {}
        try { td.direction = ParagraphDirection.DIRECTION_RIGHT_TO_LEFT; } catch (e2) {}
    }
    sp.setValue(td);
    return l;
}
function boxText(comp, str, font, size, leading, color, w, h) {
    var l = comp.layers.addBoxText([w, h], str);
    var sp = l.property("ADBE Text Properties").property("ADBE Text Document");
    var td = sp.value;
    td.font = font; td.fontSize = size; td.fillColor = color; td.applyFill = true; td.applyStroke = false;
    try { td.autoLeading = false; td.leading = leading; } catch (e) {}
    td.justification = ParagraphJustification.FULL_JUSTIFY_LASTLINE_LEFT;
    sp.setValue(td);
    return l;
}
// anchor to a side of the text bounds, keep it at (x,y)
function pinText(l, side, x, y) {
    var r = l.sourceRectAtTime(0, false);
    var ax = side === "right" ? r.left + r.width : (side === "left" ? r.left : r.left + r.width / 2);
    A(l).setValue([ax, r.top + r.height / 2]);
    P(l).setValue([x, y]);
    return r;
}

// ── shapes (path coordinates == comp coordinates: A = P = [0,0]) ──
function shapeLayer(comp, name) {
    var l = comp.layers.addShape();
    l.name = name;
    A(l).setValue([0, 0]);
    P(l).setValue([0, 0]);
    return l;
}
function contents(l) { return l.property("ADBE Root Vectors Group"); }
function addGroup(l, name) {
    var g = contents(l).addProperty("ADBE Vector Group");
    g.name = name;
    return contents(l).property(name);
}
function vecs(g) { return g.property("ADBE Vectors Group"); }
function addPath(g, verts, closed, inT, outT) {
    var v = vecs(g);
    v.addProperty("ADBE Vector Shape - Group");
    var p = v.property(v.numProperties);
    var s = new Shape();
    s.vertices = verts;
    if (inT) s.inTangents = inT;
    if (outT) s.outTangents = outT;
    s.closed = closed;
    p.property("ADBE Vector Shape").setValue(s);
    return p;
}
function addFill(g, col) {
    vecs(g).addProperty("ADBE Vector Graphic - Fill");
    var f = vecs(g).property(vecs(g).numProperties);
    f.property("ADBE Vector Fill Color").setValue(col);
    return f;
}
function addStroke(g, col, w) {
    vecs(g).addProperty("ADBE Vector Graphic - Stroke");
    var s = vecs(g).property(vecs(g).numProperties);
    s.property("ADBE Vector Stroke Color").setValue(col);
    s.property("ADBE Vector Stroke Width").setValue(w);
    try { s.property("ADBE Vector Stroke Line Cap").setValue(2); } catch (e) {}
    return s;
}
function addTrim(g, sequential) {
    vecs(g).addProperty("ADBE Vector Filter - Trim");
    var t = vecs(g).property(vecs(g).numProperties);
    if (sequential) try { t.property("ADBE Vector Trim Type").setValue(2); } catch (e) {}
    return t;
}
function rectVerts(x0, y0, x1, y1) { return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]; }

// torn rectangle: jagged on the requested sides {l,r,t,b}
function tornVerts(x0, y0, x1, y1, sides, amp, step) {
    var v = [], x, y;
    function jag() { var j = rr(-amp, amp); if (rnd() < 0.12) j *= 2.2; return j; }
    // top: left → right
    if (sides.t) { for (x = x0; x < x1; x += rr(step * 0.5, step * 1.4)) v.push([x, y0 + jag()]); }
    else v.push([x0, y0]);
    // right: top → bottom
    if (sides.r) { for (y = y0; y < y1; y += rr(step * 0.5, step * 1.4)) v.push([x1 + jag(), y]); }
    else v.push([x1, y0]);
    // bottom: right → left
    if (sides.b) { for (x = x1; x > x0; x -= rr(step * 0.5, step * 1.4)) v.push([x, y1 + jag()]); }
    else v.push([x1, y1]);
    // left: bottom → top
    if (sides.l) { for (y = y1; y > y0; y -= rr(step * 0.5, step * 1.4)) v.push([x0 + jag(), y]); }
    else v.push([x0, y1]);
    return v;
}
function ellipseVerts(cx, cy, rx, ry) {
    var k = 0.5523;
    return {
        v: [[cx, cy - ry], [cx + rx, cy], [cx, cy + ry], [cx - rx, cy]],
        i: [[-rx * k, 0], [0, -ry * k], [rx * k, 0], [0, ry * k]],
        o: [[rx * k, 0], [0, ry * k], [-rx * k, 0], [0, -ry * k]]
    };
}
function pivot(l, x, y) { // shape layers: move anchor & position together
    A(l).setValue([x, y]);
    P(l).setValue([x, y]);
}

// sampled sine float (baked)
function floatKeys(p, base, ax, ay, fx, fy, ph, t0, t1, step) {
    var keys = [], t;
    for (t = t0; t <= t1 + 0.0001; t += step) {
        var env = Math.min(1, (t - t0) / 0.8);
        var dx = ax * env * Math.sin(2 * Math.PI * fx * t + ph);
        var dy = ay * env * Math.sin(2 * Math.PI * fy * t + ph * 1.7);
        if (base.length === 3) keys.push([t, [base[0] + dx, base[1] + dy, base[2]], 33, 33]);
        else if (base.length === 2) keys.push([t, [base[0] + dx, base[1] + dy], 33, 33]);
        else keys.push([t, base + dx, 33, 33]);
    }
    addKeys(p, keys);
    for (var i = 1; i <= p.numKeys; i++) {
        if (p.keyTime(i) >= t0 - 0.0001) {
            try { p.setInterpolationTypeAtKey(i, KeyframeInterpolationType.BEZIER, KeyframeInterpolationType.BEZIER); p.setTemporalAutoBezierAtKey(i, true); p.setTemporalContinuousAtKey(i, true); } catch (e) {}
        }
    }
}

// ───────────────────────────── ASSETS ─────────────────────────────
function scriptFolder() {
    try { return File($.fileName).parent; } catch (e) { return Folder.desktop; }
}
var ASSET_DIR = new Folder(scriptFolder().fsName + "/GFX01_assets");
if (!ASSET_DIR.exists) {
    var pick = Folder.selectDialog("GFX01: اختار فولدر الأصول (GFX01_assets) — أو Cancel للـ placeholders");
    if (pick) ASSET_DIR = pick;
}
function findAsset(key) {
    if (!ASSET_DIR || !ASSET_DIR.exists) return null;
    var files = ASSET_DIR.getFiles(), k = key.toLowerCase();
    for (var i = 0; i < files.length; i++) {
        if (!(files[i] instanceof File)) continue;
        var n = decodeURI(files[i].name).toLowerCase();
        if (n.indexOf(k) === 0 && /\.(jpe?g|png|tiff?|psd|webp|bmp)$/i.test(n)) return files[i];
    }
    return null;
}

// ───────────────────────────── PROJECT SETUP ─────────────────────────────
app.beginUndoGroup("GFX01 build");
if (!app.project) app.newProject();
var proj = app.project;

// remove previous build (folder + everything inside)
for (var ri = proj.numItems; ri >= 1; ri--) {
    var it = proj.item(ri);
    if (it instanceof FolderItem && it.name === CFG.PREFIX + "_Lindbergh_AFC") it.remove();
}
var ROOT = proj.items.addFolder(CFG.PREFIX + "_Lindbergh_AFC");
var PRE  = proj.items.addFolder(CFG.PREFIX + "_precomps");  PRE.parentFolder = ROOT;
var FOOT = proj.items.addFolder(CFG.PREFIX + "_footage");   FOOT.parentFolder = ROOT;

function newComp(name, w, h, dur) {
    var c = proj.items.addComp(name, Math.round(w), Math.round(h), 1, dur || CFG.DUR, CFG.FPS);
    c.parentFolder = PRE;
    c.motionBlur = true;
    c.shutterAngle = 180;
    return c;
}

var FONT_AR   = pickFont(CFG.FONTS_AR);
var FONT_NUM  = pickFont(CFG.FONTS_NUM);
var FONT_LAT  = pickFont(CFG.FONTS_LAT);
var FONT_NEWS = pickFont(CFG.FONTS_NEWS);
var FONT_HEAD = pickFont(CFG.FONTS_HEAD);
log("fonts: " + [FONT_AR, FONT_NUM, FONT_LAT, FONT_NEWS, FONT_HEAD].join(" | "));

function placeholder(a) {
    var c = newComp(CFG.PREFIX + "_PH_" + a.key, a.w, a.h);
    var s = c.layers.addSolid([0.5, 0.5, 0.5], "ph", a.w, a.h, 1);
    var g = fxAdd(s, "ADBE Ramp");
    g.property(1).setValue([a.w * 0.2, 0]);
    g.property(2).setValue([0.78, 0.78, 0.76]);
    g.property(3).setValue([a.w * 0.8, a.h]);
    g.property(4).setValue([0.22, 0.22, 0.22]);
    var n = c.layers.addSolid([0.5, 0.5, 0.5], "grit", a.w, a.h, 1);
    fxAdd(n, "ADBE Fractal Noise");
    n.blendingMode = BlendingMode.OVERLAY;
    O(n).setValue(55);
    if (a.label) {
        var t = textLayer(c, a.label + "\n" + a.key, FONT_LAT, Math.round(a.w / 22), [0.1, 0.1, 0.1], ParagraphJustification.CENTER_JUSTIFY, false);
        pinText(t, "center", a.w / 2, a.h / 2);
        O(t).setValue(70);
    }
    return c;
}
function source(id) {
    var a = ASSETS[id];
    var f = findAsset(a.key);
    if (f) {
        var io = new ImportOptions(f);
        try { io.importAs = ImportAsType.FOOTAGE; } catch (e) {}
        var item = proj.importFile(io);
        item.parentFolder = FOOT;
        log("asset " + a.key + " → " + decodeURI(f.name) + " (" + item.width + "x" + item.height + ")");
        return item;
    }
    log("asset " + a.key + " → MISSING" + (a.optional ? " (optional)" : ", placeholder"));
    return a.optional ? null : placeholder(a);
}

// cover-fit a source into a w×h comp, optional slow push (Ken Burns)
function fitComp(name, src, w, h, kb) {
    var c = newComp(name, w, h);
    var l = c.layers.add(src);
    var s = Math.max(w / src.width, h / src.height) * 100;
    P(l).setValue([w / 2, h / 2]);
    if (kb) addKeys(S(l), [[0, [s * 1.1, s * 1.1], 33, 20], [CFG.DUR, [s, s], 60, 33]]);
    else S(l).setValue([s, s]);
    return { comp: c, layer: l };
}
// photo print: image inside a paper border
function makePrint(name, src, w, h, b, look) {
    var inner = fitComp(name + "_img", src, w, h, true);
    if (look === "bw") grayscale(inner.layer, 22, -4);
    var c = newComp(name, w + 2 * b, h + 2 * b);
    var paper = c.layers.addSolid(CFG.PRINT, "paper", w + 2 * b, h + 2 * b, 1);
    var il = c.layers.add(inner.comp);
    P(il).setValue([w / 2 + b, h / 2 + b]);
    // thin inner line like a real print
    var edge = shapeLayer(c, "print edge");
    var g = addGroup(edge, "edge");
    addPath(g, rectVerts(b, b, b + w, b + h), true);
    addStroke(g, [0, 0, 0], 1.5);
    O(edge).setValue(35);
    return c;
}

// ───────────────────────────── SOURCES ─────────────────────────────
var SRC_POSTER   = source("poster");
var SRC_PLATFORM = source("platform");
var SRC_CROWD    = source("crowd");
var SRC_NEWS     = source("news");

// ───────────────────────────── 1. NEWSPAPER BACKGROUND ─────────────────────────────
var BGW = 2300, BGH = 1360;
var bgComp = newComp(CFG.PREFIX + "_BG_newspaper", BGW, BGH);
(function buildBG(c) {
    c.layers.addSolid(CFG.PAPER, "paper base", BGW, BGH, 1);
    if (SRC_NEWS) {
        var n = c.layers.add(SRC_NEWS);
        var s = Math.max(BGW / SRC_NEWS.width, BGH / SRC_NEWS.height) * 100;
        S(n).setValue([s, s]); P(n).setValue([BGW / 2, BGH / 2]);
        grayscale(n, 10, 0);
        n.blendingMode = BlendingMode.MULTIPLY;
        O(n).setValue(85);
    } else {
        var words = "America First Committee rally draws thousands as Lindbergh warns against war in Europe. Speakers urge the nation to stay out of foreign conflicts and keep America neutral. The committee, founded in 1940, grew to more than eight hundred thousand members across the country. Critics called the movement isolationist while supporters said it defended democracy at home. ";
        var body = ""; for (var k = 0; k < 10; k++) body += words;
        var heads = ["AMERICA FIRST", "LINDBERGH SPEAKS", "KEEP OUT OF WAR", "RALLY TONIGHT", "NEUTRALITY", "THE NATION DEBATES"];
        seed = 21;
        // paper scraps (slightly different tones), each with columns + a headline
        var scraps = [[-60, -40, 760, 700], [620, -80, 1380, 560], [1220, -60, 2360, 620], [-80, 560, 900, 1420], [780, 480, 1640, 1420], [1500, 560, 2380, 1420]];
        for (var si = 0; si < scraps.length; si++) {
            var r = scraps[si];
            var tone = rr(0.70, 0.82);
            var sl = shapeLayer(c, "scrap " + (si + 1));
            var g = addGroup(sl, "scrap");
            addPath(g, tornVerts(r[0], r[1], r[2], r[3], { l: 1, r: 1, t: 1, b: 1 }, 7, 16), true);
            addFill(g, [tone, tone, tone * 0.985]);
            pivot(sl, (r[0] + r[2]) / 2, (r[1] + r[3]) / 2);
            R(sl).setValue(rr(-2.5, 2.5));
            shadow(sl, 3, 10, 35);
            var cols = Math.floor((r[2] - r[0]) / 200);
            for (var ci = 0; ci < cols; ci++) {
                var tl = boxText(c, body, FONT_NEWS, 13, 15.5, [0.16, 0.16, 0.16], 180, r[3] - r[1] - 190);
                pinText(tl, "left", r[0] + 20 + ci * 200, (r[1] + r[3]) / 2 + 70);
                R(tl).setValue(R(sl).value);
                O(tl).setValue(rr(28, 48));
            }
            var hl = textLayer(c, heads[si % heads.length], FONT_HEAD, Math.round(rr(70, 110)), [0.12, 0.12, 0.12], ParagraphJustification.LEFT_JUSTIFY, false);
            pinText(hl, "left", r[0] + 24, r[1] + 80);
            R(hl).setValue(R(sl).value);
            O(hl).setValue(rr(16, 28));
        }
    }
    // grunge / uneven ink
    var gr = c.layers.addSolid([0.5, 0.5, 0.5], "grunge", BGW, BGH, 1);
    var fn = fxAdd(gr, "ADBE Fractal Noise", "grunge");
    tryProp(fn, ["Contrast"], 160);
    tryProp(fn, ["Brightness"], -10);
    try { fn.property("Transform").property("Uniform Scaling").setValue(1); fn.property("Transform").property("Scale").setValue(900); } catch (e) {}
    gr.blendingMode = BlendingMode.OVERLAY;
    O(gr).setValue(45);
    var dust = c.layers.addSolid([0.5, 0.5, 0.5], "speckle", BGW, BGH, 1);
    var fn2 = fxAdd(dust, "ADBE Fractal Noise", "speckle");
    tryProp(fn2, ["Contrast"], 420);
    tryProp(fn2, ["Brightness"], -120);
    try { fn2.property("Transform").property("Scale").setValue(18); } catch (e) {}
    dust.blendingMode = BlendingMode.MULTIPLY;
    O(dust).setValue(30);
})(bgComp);

// ───────────────────────────── 2. RED TORN PANEL + CROWD ─────────────────────────────
var panelComp = newComp(CFG.PREFIX + "_PANEL_red_crowd", CFG.W, CFG.H);
(function buildPanel(c) {
    seed = 33;
    // dark scrap top-right (behind)
    var dk = shapeLayer(c, "dark scrap");
    var gd = addGroup(dk, "dark");
    addPath(gd, tornVerts(1440, -60, 1990, 300, { l: 1, b: 1 }, 9, 18), true);
    addFill(gd, [0.10, 0.10, 0.10]);
    shadow(dk, 4, 14, 45);
    // red panel
    var red = shapeLayer(c, "red panel");
    var gr = addGroup(red, "red");
    var pv = tornVerts(1110, -60, 1990, 1140, { l: 1 }, 12, 20);
    addPath(gr, pv, true);
    addFill(gr, CFG.RED);
    shadow(red, 5, 16, 55);
    // paper fibre edge (white stroke only on the torn side feel)
    var fib = shapeLayer(c, "torn fibre");
    var gf = addGroup(fib, "fibre");
    addPath(gf, pv, true);
    addStroke(gf, [0.95, 0.94, 0.9], 5);
    O(fib).setValue(80);
    fib.moveBefore(red);
    // crowd inside the red panel (duotone, multiply), matted by a fill copy
    var matte = shapeLayer(c, "panel matte");
    var gm = addGroup(matte, "m");
    addPath(gm, pv, true);
    addFill(gm, [1, 1, 1]);
    var crowd = c.layers.add(SRC_CROWD);
    var s = Math.max(900 / SRC_CROWD.width, 1180 / SRC_CROWD.height) * 100;
    P(crowd).setValue([1560, 540]);
    addKeys(S(crowd), [[0, [s * 1.12, s * 1.12], 33, 20], [CFG.DUR, [s * 1.02, s * 1.02], 60, 33]]);
    grayscale(crowd, 35, 0);
    crowd.blendingMode = BlendingMode.MULTIPLY;
    O(crowd).setValue(85);
    crowd.moveBefore(red);
    matte.moveBefore(crowd);
    crowd.setTrackMatte(matte, TrackMatteType.ALPHA);
    matte.enabled = false;
    fib.moveToBeginning();
})(panelComp);

// ───────────────────────────── 3. FOREGROUND CROWD (blurred, depth) ─────────────────────────────
var fgComp = newComp(CFG.PREFIX + "_FG_crowd", CFG.W, CFG.H);
(function buildFG(c) {
    seed = 51;
    var m = shapeLayer(c, "fg matte");
    var g = addGroup(m, "m");
    addPath(g, tornVerts(-60, 880, 760, 1140, { t: 1, r: 1 }, 14, 22), true);
    addFill(g, [1, 1, 1]);
    var l = c.layers.add(SRC_CROWD);
    var s = Math.max(900 / SRC_CROWD.width, 520 / SRC_CROWD.height) * 100 * 1.25;
    S(l).setValue([s, s]);
    P(l).setValue([380, 900]);
    grayscale(l, 30, -28);
    m.moveBefore(l);
    l.setTrackMatte(m, TrackMatteType.ALPHA);
    m.enabled = false;
})(fgComp);

// ───────────────────────────── 4. YEAR DIGITS (rolling) ─────────────────────────────
var T = { // master timing (seconds)
    flash1: fr(3), flash2: fr(7),
    shrink0: 0.40, shrink1: 0.95,
    panel0: 0.45, fg0: 0.55, bgFocus1: 1.40,
    title0: 0.75, title1: 1.25, stars0: 0.95,
    yearA0: 1.25, dash0: 1.62, yearB0: 1.72,
    ruler0: 1.40, ruler1: 2.10, kicker0: 1.95,
    poster0: 1.85,
    hold0: 2.40,
    out0: 8.15, out1: 8.55
};

var yearComp = newComp(CFG.PREFIX + "_YEAR_digits", CFG.W, CFG.H);
var YEAR_RIGHT = 940, YEAR_Y = 452, YEAR_MAXW = 790;
(function buildYear(c) {
    var chars = (CFG.YEAR_A + "-" + CFG.YEAR_B).split("");
    var size = 200, trackPx = 4;
    // measure widths
    var widths = [], layers = [], i;
    for (i = 0; i < chars.length; i++) {
        if (chars[i] === "-") { widths.push(size * 0.42); layers.push(null); continue; }
        var l = textLayer(c, chars[i], FONT_NUM, size, CFG.INK, ParagraphJustification.CENTER_JUSTIFY, false);
        l.name = "digit " + (i + 1) + " (" + chars[i] + ")";
        var r = l.sourceRectAtTime(0, false);
        widths.push(r.width + trackPx);
        A(l).setValue([r.left + r.width / 2, r.top + r.height / 2]);
        layers.push(l);
    }
    var total = 0; for (i = 0; i < widths.length; i++) total += widths[i];
    var k = Math.min(1, YEAR_MAXW / total);
    var x = YEAR_RIGHT - total * k;
    var dashIdx = CFG.YEAR_A.length;
    for (i = 0; i < chars.length; i++) {
        var cx = x + widths[i] * k / 2;
        x += widths[i] * k;
        if (!layers[i]) {
            // dash: grows from its left end
            var d = shapeLayer(c, "dash");
            var g = addGroup(d, "dash");
            var dw = widths[i] * k * 0.78, dh = size * k * 0.12;
            addPath(g, rectVerts(cx - dw / 2, YEAR_Y - dh / 2, cx + dw / 2, YEAR_Y + dh / 2), true);
            addFill(g, CFG.RED);
            pivot(d, cx - dw / 2, YEAR_Y);
            addKeys(S(d), [[T.dash0, [0, 100], 70, 30], [T.dash0 + 0.25, [108, 100], 55, 55], [T.dash0 + 0.36, [100, 100], 85, 30]]);
            continue;
        }
        var lay = layers[i];
        P(lay).setValue([cx, YEAR_Y]);
        var sc = 100 * k;
        var partB = i > dashIdx;
        var local = partB ? i - dashIdx - 1 : i;
        var t0 = (partB ? T.yearB0 : T.yearA0) + local * fr(2);
        var finalCh = chars[i];
        var roll = local >= 2; // last two digits of each year roll like a counter
        if (roll) {
            // ghost roll through digits, then land
            var sp = lay.property("ADBE Text Properties").property("ADBE Text Document");
            var base = sp.value, steps = 6 + (local - 2) * 2, fd = parseInt(finalCh, 10), s;
            for (s = 0; s < steps; s++) {
                var td = sp.value;
                td.text = String((fd + steps - s) % 10);
                sp.setValueAtTime(t0 + s * fr(2), td);
            }
            var tdF = sp.value; tdF.text = finalCh;
            sp.setValueAtTime(t0 + steps * fr(2), tdF);
            var tLand = t0 + steps * fr(2);
            addKeys(O(lay), [[t0 - F, 0, 50, 50, true], [t0, 40, 50, 50, true], [tLand, 100, 50, 50]]);
            addKeys(S(lay), [[t0, [sc, sc]], [tLand, [sc * 1.12, sc * 1.12], 60, 20], [tLand + 0.22, [sc * 0.985, sc * 0.985], 55, 55], [tLand + 0.34, [sc, sc], 85, 30]]);
            blurKeys(lay, [[t0, 6, 50, 50, true], [tLand, 0, 50, 50]]);
        } else {
            addKeys(O(lay), [[t0, 0, 50, 30], [t0 + 0.18, 100, 70, 50]]);
            addKeys(S(lay), [[t0, [sc * 1.25, sc * 1.25], 50, 20], [t0 + 0.24, [sc * 0.98, sc * 0.98], 55, 55], [t0 + 0.34, [sc, sc], 85, 30]]);
            blurKeys(lay, [[t0, 14, 50, 20], [t0 + 0.22, 0, 80, 50]]);
        }
        lay.motionBlur = true;
    }
    log("year width " + Math.round(total * k) + " px (fit " + Math.round(k * 100) + "%)");
})(yearComp);

// ───────────────────────────── 5. TEXT BLOCK ─────────────────────────────
var textComp = newComp(CFG.PREFIX + "_TEXT_block", CFG.W, CFG.H);
(function buildText(c) {
    // --- year (black) + newspaper texture inside the digits (like the reference)
    var yl = c.layers.add(yearComp);
    yl.name = "YEAR";
    shadow(yl, 5, 12, 35);
    var ym = c.layers.add(yearComp);
    ym.name = "YEAR matte";
    var tex = c.layers.add(bgComp);
    tex.name = "YEAR texture";
    P(tex).setValue([CFG.W / 2 + 90, CFG.H / 2 - 40]);
    S(tex).setValue([62, 62]);
    grayscale(tex, 40, -35);
    tex.blendingMode = BlendingMode.SCREEN;
    O(tex).setValue(55);
    ym.moveBefore(tex);
    tex.setTrackMatte(ym, TrackMatteType.ALPHA);
    ym.enabled = false;

    // --- title (red, RTL), soft wipe right → left
    var title = textLayer(c, CFG.TITLE, FONT_AR, 108, CFG.RED, ParagraphJustification.RIGHT_JUSTIFY, true);
    title.name = "TITLE";
    var tr0 = pinText(title, "right", YEAR_RIGHT, 262);
    var tw = tr0.width + 120;
    var wipe = shapeLayer(c, "TITLE wipe matte");
    var wg = addGroup(wipe, "wipe");
    addPath(wg, rectVerts(YEAR_RIGHT + 60 - tw, 262 - 110, YEAR_RIGHT + 60, 262 + 110), true);
    addFill(wg, [1, 1, 1]);
    pivot(wipe, YEAR_RIGHT + 60, 262);
    addKeys(S(wipe), [[T.title0, [0, 100], 60, 25], [T.title1, [100, 100], 85, 40]]);
    blurFx(wipe, 28);
    wipe.moveBefore(title);
    title.setTrackMatte(wipe, TrackMatteType.ALPHA);
    wipe.enabled = false;
    // settle + blur
    addKeys(S(title), [[T.title0, [104, 104], 50, 20], [T.title1 + 0.15, [100, 100], 85, 30]]);
    blurKeys(title, [[T.title0, 12, 50, 20], [T.title1, 0, 85, 30]]);
    shadow(title, 3, 8, 25);

    // --- three red stars above the title (pop, stagger)
    for (var si = 0; si < 3; si++) {
        var st = shapeLayer(c, "star " + (si + 1));
        var sg = addGroup(st, "star");
        vecs(sg).addProperty("ADBE Vector Shape - Star");
        var star = vecs(sg).property(vecs(sg).numProperties);
        star.property("ADBE Vector Star Type").setValue(1);
        star.property("ADBE Vector Star Points").setValue(5);
        star.property("ADBE Vector Star Outer Radius").setValue(15);
        star.property("ADBE Vector Star Inner Radius").setValue(6.2);
        addFill(sg, CFG.RED);
        var sx = YEAR_RIGHT - 14 - si * 36, sy = 168;
        star.property("ADBE Vector Star Position").setValue([sx, sy]);
        pivot(st, sx, sy);
        var t = T.stars0 + si * fr(3);
        addKeys(S(st), [[t, [0, 0], 50, 20], [t + 0.2, [125, 125], 55, 55], [t + 0.32, [100, 100], 85, 30]]);
        addKeys(R(st), [[t, -40, 50, 20], [t + 0.32, 0, 85, 30]]);
    }

    // --- ruler ticks, drawn right → left (sequential trim)
    var ru = shapeLayer(c, "RULER ticks");
    var rg = addGroup(ru, "ticks");
    var n = 0, x;
    for (x = YEAR_RIGHT; x >= 170; x -= 24) {
        var tall = (n % 5 === 0);
        addPath(rg, [[x, 600 - (tall ? 12 : 6)], [x, 600 + (tall ? 12 : 6)]], false);
        n++;
    }
    var trim = addTrim(rg, true);   // trim above the stroke so the stroke is trimmed
    addStroke(rg, [0.13, 0.13, 0.13], 3);
    trim = vecs(rg).property("ADBE Vector Filter - Trim");
    addKeys(trim.property("ADBE Vector Trim End"), [[T.ruler0, 0, 60, 30], [T.ruler1, 100, 85, 40]]);
    // red cursor rides the draw
    var cur = shapeLayer(c, "RULER cursor");
    var cg = addGroup(cur, "cursor");
    addPath(cg, [[-8, -26], [8, -26], [0, -12]], true);
    addFill(cg, CFG.RED);
    addKeys(P(cur), [[T.ruler0, [YEAR_RIGHT, 600], 60, 30], [T.ruler1, [170 + 24 * 0.5, 600], 85, 40]]);
    addKeys(O(cur), [[T.ruler0, 0], [T.ruler0 + 0.1, 100]]);

    // --- small English kicker, tracking in
    var kk = textLayer(c, CFG.KICKER, FONT_LAT, 22, [0.14, 0.14, 0.14], ParagraphJustification.RIGHT_JUSTIFY, false);
    kk.name = "KICKER";
    pinText(kk, "right", YEAR_RIGHT, 648);
    var anims = kk.property("ADBE Text Properties").property("ADBE Text Animators");
    anims.addProperty("ADBE Text Animator");
    var an = anims.property(1);
    an.property("ADBE Text Selectors").addProperty("ADBE Text Selector");
    var props = an.property("ADBE Text Animator Properties");
    props.addProperty("ADBE Text Opacity");
    props = kk.property("ADBE Text Properties").property("ADBE Text Animators").property(1).property("ADBE Text Animator Properties");
    props.property("ADBE Text Opacity").setValue(0);
    props.addProperty("ADBE Text Tracking Amount");
    props = kk.property("ADBE Text Properties").property("ADBE Text Animators").property(1).property("ADBE Text Animator Properties");
    addKeys(props.property("ADBE Text Tracking Amount"), [[T.kicker0, 220, 50, 20], [T.kicker0 + 0.7, 0, 85, 30]]);
    var sel = kk.property("ADBE Text Properties").property("ADBE Text Animators").property(1).property("ADBE Text Selectors").property(1);
    addKeys(sel.property("ADBE Text Percent Start"), [[T.kicker0, 0, 50, 30], [T.kicker0 + 0.6, 100, 80, 40]]);
    O(kk).setValue(75);
})(textComp);

// ───────────────────────────── 6. PRINTS ─────────────────────────────
var heroPrint   = makePrint(CFG.PREFIX + "_PRINT_platform", SRC_PLATFORM, 1000, 740, 26, "bw");
var posterPrint = makePrint(CFG.PREFIX + "_PRINT_poster",   SRC_POSTER,   340,  460, 14, "color");

// ───────────────────────────── 7. MAIN COMP ─────────────────────────────
var main = proj.items.addComp(CFG.PREFIX + "_لجنة_أميركا_أولًا", CFG.W, CFG.H, 1, CFG.DUR, CFG.FPS);
main.parentFolder = ROOT;
main.motionBlur = true;
main.shutterAngle = 180;
main.bgColor = CFG.PAPER;

function z3(l, z, extra) {
    l.threeDLayer = true;
    var p = P(l).value;
    P(l).setValue([p[0], p[1], z]);
    var s = 100 * (CFG.ZOOM + z) / CFG.ZOOM * (extra || 1);
    S(l).setValue([s, s, s]);
    return s;
}

// background
var BG = main.layers.add(bgComp);
BG.name = "BG newspaper";
z3(BG, 700, 1.02);
var bgBlur = blurKeys(BG, [[0, 22, 50, 20], [T.bgFocus1, 1.5, 85, 30]]);
var bgBC = fxAdd(BG, "ADBE Brightness & Contrast 2", "exposure");
addKeys(bgBC.property(1), [[0, -35, 50, 20], [T.bgFocus1, 0, 85, 30]]);

// red panel
var PANEL = main.layers.add(panelComp);
PANEL.name = "PANEL red + crowd";
z3(PANEL, 260);
var pp = P(PANEL).value;
addKeys(P(PANEL), [[T.panel0, [pp[0] + 820, pp[1], pp[2]], 60, 22], [T.panel0 + 0.32, [pp[0] - 22, pp[1], pp[2]], 55, 55], [T.panel0 + 0.48, pp, 85, 30]]);
PANEL.motionBlur = true;

// text block
var TXT = main.layers.add(textComp);
TXT.name = "TEXT block";
z3(TXT, 60);

// hero print — starts full frame (negative flash), shrinks into the collage
var HERO = main.layers.add(heroPrint);
HERO.name = "HERO print — platform";
HERO.threeDLayer = true;
HERO.motionBlur = true;
var heroFinal = [1412, 590, 0], heroS = 78;
var fullS = Math.max(CFG.W / 1000, CFG.H / 740) * 100 * 1.06;
addKeys(P(HERO), [[0, [960, 540, 0], 50, 50], [T.shrink0, [960, 540, 0], 50, 22], [T.shrink1, heroFinal, 85, 30]]);
addKeys(S(HERO), [[0, [fullS * 1.04, fullS * 1.04, 100], 33, 33], [T.shrink0, [fullS, fullS, 100], 50, 22],
                  [T.shrink0 + (T.shrink1 - T.shrink0) * 0.62, [heroS * 0.965, heroS * 0.965, 100], 55, 55],
                  [T.shrink1 + 0.12, [heroS, heroS, 100], 85, 30]]);
addKeys(tr(HERO).property("ADBE Rotate Z"), [[T.shrink0, 0, 50, 22], [T.shrink1 + 0.1, -2.2, 85, 30]]);
var inv = fxAdd(HERO, "ADBE Invert", "negative flash");
holdKeys(inv.property(2), [[0, 100], [T.flash1, 0], [T.flash1 + fr(2), 100], [T.flash2, 0], [T.flash2 + fr(1), 100]]);
// short hand-held jolt with the flash (baked)
var jolt = [];
seed = 99;
for (var jf = 2; jf <= 10; jf++) jolt.push([fr(jf), [rr(-10, 10), rr(-7, 7)]]);
var hs = shadow(HERO, 10, 34, 0);
addKeys(hs.property(2), [[T.shrink0, 0], [T.shrink1, 60 * (hs.property(2).hasMax && hs.property(2).maxValue > 100.5 ? 2.55 : 1)]]);
var heroT = tr(HERO).property("ADBE Anchor Point"), ha = heroT.value;
var jk = [[fr(1), ha, 50, 50, true]];
for (var ji = 0; ji < jolt.length; ji++) jk.push([jolt[ji][0], [ha[0] + jolt[ji][1][0], ha[1] + jolt[ji][1][1], 0], 50, 50, true]);
jk.push([fr(11), ha, 50, 50]);
addKeys(heroT, jk);
// gentle float during hold
floatKeys(tr(HERO).property("ADBE Rotate Z"), -2.2, 0.35, 0, 0.11, 0, 0.6, T.hold0, T.out1, 0.5);

// poster print
var POSTER = main.layers.add(posterPrint);
POSTER.name = "POSTER print — AFC";
var posterPos = [1118, 272, -60];
POSTER.threeDLayer = true;
P(POSTER).setValue(posterPos);
var ps = 62 * (CFG.ZOOM - 60) / CFG.ZOOM;
addKeys(S(POSTER), [[T.poster0, [0, 0, 100], 50, 20], [T.poster0 + 0.26, [ps * 1.06, ps * 1.06, 100], 55, 55], [T.poster0 + 0.42, [ps, ps, 100], 85, 30]]);
addKeys(tr(POSTER).property("ADBE Rotate Z"), [[T.poster0, -16, 50, 20], [T.poster0 + 0.42, -6, 85, 30]]);
blurKeys(POSTER, [[T.poster0, 10, 50, 20], [T.poster0 + 0.25, 0, 85, 30]]);
shadow(POSTER, 8, 22, 55);
floatKeys(tr(POSTER).property("ADBE Rotate Z"), -6, 0.5, 0, 0.13, 0, 1.9, T.hold0, T.out1, 0.5);
POSTER.motionBlur = true;

// foreground crowd (closest to camera, blurred)
var FG = main.layers.add(fgComp);
FG.name = "FG crowd (depth)";
z3(FG, -480);
var fp = P(FG).value;
addKeys(P(FG), [[T.fg0, [fp[0] - 40, fp[1] + 240, fp[2]], 60, 22], [T.fg0 + 0.5, fp, 85, 30]]);
blurFx(FG, 12);
FG.motionBlur = true;

// ordering (top → bottom): FG, POSTER, HERO, TEXT, PANEL, BG
FG.moveToBeginning();
POSTER.moveAfter(FG);
HERO.moveAfter(POSTER);
TXT.moveAfter(HERO);
PANEL.moveAfter(TXT);
BG.moveToEnd();

// camera — slow push + drift (baked keys)
var cam = main.layers.addCamera("CAM", [CFG.W / 2, CFG.H / 2]);
cam.property("ADBE Camera Options Group").property("ADBE Camera Zoom").setValue(CFG.ZOOM);
var camP = tr(cam).property("ADBE Position");
var camI = tr(cam).property("ADBE Anchor Point"); // point of interest
addKeys(camP, [[0, [CFG.W / 2 + 30, CFG.H / 2 + 10, -CFG.ZOOM - 60], 33, 25], [T.hold0, [CFG.W / 2 + 8, CFG.H / 2, -CFG.ZOOM + 40], 60, 40], [CFG.DUR, [CFG.W / 2 - 22, CFG.H / 2 - 6, -CFG.ZOOM + 150], 40, 33]]);
addKeys(camI, [[0, [CFG.W / 2 + 30, CFG.H / 2 + 10, 0], 33, 25], [T.hold0, [CFG.W / 2 + 8, CFG.H / 2, 0], 60, 40], [CFG.DUR, [CFG.W / 2 - 22, CFG.H / 2 - 6, 0], 40, 33]]);
cam.moveToBeginning();

// outro — torn paper sheet wipes across
seed = 77;
var wipeBack = shapeLayer(main, "OUT torn sheet (back)");
var wb = addGroup(wipeBack, "sheet");
addPath(wb, tornVerts(-2700, -120, 0, 1200, { r: 1 }, 18, 26), true);
addFill(wb, [0.14, 0.14, 0.14]);
shadow(wipeBack, 8, 30, 50);
var wipeFront = shapeLayer(main, "OUT torn sheet");
var wf = addGroup(wipeFront, "sheet");
addPath(wf, tornVerts(-2700, -120, 0, 1200, { r: 1 }, 16, 22), true);
addFill(wf, CFG.PAPER);
var wfFib = addGroup(wipeFront, "fibre");
addPath(wfFib, tornVerts(-2700, -120, 6, 1200, { r: 1 }, 16, 22), true);
addStroke(wfFib, [0.95, 0.94, 0.9], 6);
shadow(wipeFront, 10, 34, 60);
addKeys(P(wipeBack),  [[T.out0 - fr(2), [0, 0], 60, 20], [T.out1 - fr(2), [CFG.W + 260, 0], 85, 30]]);
addKeys(P(wipeFront), [[T.out0 + fr(2), [0, 0], 60, 20], [T.out1 + fr(3), [CFG.W + 300, 0], 85, 30]]);
tr(wipeFront).property("ADBE Rotate Z").setValue(2.5);
tr(wipeBack).property("ADBE Rotate Z").setValue(-1.5);
wipeFront.motionBlur = wipeBack.motionBlur = true;
wipeFront.moveToBeginning();
wipeBack.moveAfter(wipeFront);

// finish: vignette + grain + flicker
var vig = main.layers.addSolid([0, 0, 0], "FINISH vignette", CFG.W, CFG.H, 1);
var m = vig.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");
var ev = ellipseVerts(CFG.W / 2, CFG.H / 2, CFG.W * 0.62, CFG.H * 0.72);
var es = new Shape(); es.vertices = ev.v; es.inTangents = ev.i; es.outTangents = ev.o; es.closed = true;
m.property("ADBE Mask Shape").setValue(es);
m.maskMode = MaskMode.SUBTRACT;
m.property("ADBE Mask Feather").setValue([520, 520]);
O(vig).setValue(48);

var fin = main.layers.addSolid([1, 1, 1], "FINISH grain + flicker", CFG.W, CFG.H, 1);
fin.adjustmentLayer = true;
var nz = fxAdd(fin, "ADBE Noise", "grain");
nz.property(1).setValue(6);
try { nz.property(2).setValue(0); } catch (e) {}
var fl = fxAdd(fin, "ADBE Brightness & Contrast 2", "flicker");
var flk = []; seed = 5;
for (var ft = 0; ft <= CFG.DUR; ft += fr(2)) flk.push([ft, rr(-3, 3), 50, 50, true]);
addKeys(fl.property(1), flk);
fin.moveToBeginning();
vig.moveAfter(fin);

// markers
function mark(t, s) { var mv = new MarkerValue(s); main.markerProperty.setValueAtTime(t, mv); }
mark(0, "GFX01 IN — negative flash");
mark(T.title0, "TITLE");
mark(T.yearA0, "DATES 1940–1941");
mark(T.hold0, "HOLD");
mark(T.out0, "OUT — torn wipe");

main.openInViewer();

// preview frames + log
var dir = new Folder(scriptFolder().fsName + "/previews");
if (!dir.exists) dir.create();
var times = [0.1, 0.6, 0.9, 1.2, 1.5, 1.9, 2.4, 5.0, 8.35];
for (var pi = 0; pi < times.length; pi++) {
    try { main.saveFrameToPng(times[pi], new File(dir.fsName + "/GFX01_" + ("000" + Math.round(times[pi] * CFG.FPS)).slice(-3) + ".png")); } catch (e) { log("preview " + times[pi] + ": " + e.toString()); break; }
}

// save as next version next to the script (never overwrite)
try {
    var v = 1, f;
    do { f = new File(scriptFolder().fsName + "/GFX01_Lindbergh_AFC-v" + (v < 10 ? "0" : "") + v + ".aep"); v++; } while (f.exists);
    proj.save(f);
    log("saved " + decodeURI(f.name));
} catch (e) { log("save: " + e.toString()); }

var lf = new File(scriptFolder().fsName + "/GFX01-log.txt");
lf.encoding = "UTF-8"; lf.open("w"); lf.write(LOG.join("\n")); lf.close();
app.endUndoGroup();

})();
