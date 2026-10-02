#!/usr/bin/env python3
# Arterial — black / dark-grey / red-edge suite by splicer scorn (voidrane)
# One palette -> every asset. Run: python3 build.py   (writes ./dist)
import json, os, re, shutil
from pathlib import Path

HOME = Path.home()
ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
SHARE = DIST / "share"
CONF = DIST / "config"
NAME = "Arterial"
AUTHOR = "splicer scorn"

# ── palette ──────────────────────────────────────────────────────────────────
VOID   = "#000000"
PIT    = "#060606"
BASE   = "#0a0a0a"   # views / content
CHROME = "#121212"   # window chrome
PLATE  = "#1b1b1b"   # buttons / headers
RAISE  = "#242424"
LINE   = "#2e2e2e"
LINE2  = "#3a3a3a"
MUTE   = "#5e5858"
DIM    = "#857c7c"
TEXT   = "#bdb4b4"
BRIGHT = "#ece6e6"
BLOOD0 = "#1c0000"
BLOOD1 = "#3d0000"
BLOOD2 = "#5c0000"
BLOOD  = "#8b0000"
EDGE   = "#b30000"
HOT    = "#e01b1b"
FLARE  = "#ff4040"
NEG    = "#ff6a3d"   # errors: orange-red, distinct from the accent
NEU    = "#c9a227"
POS    = "#6fa36a"
LINK   = "#e05050"
VISIT  = "#9c5a6a"


def rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def csv(h):
    return ",".join(map(str, rgb(h)))


def write(path, text, mode=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    if mode:
        path.chmod(mode)


# ── 1. KDE color scheme ──────────────────────────────────────────────────────
def color_block(bg, alt, fg=TEXT, inactive=DIM, focus=EDGE, hover=HOT, active=BRIGHT):
    return {
        "BackgroundNormal": bg, "BackgroundAlternate": alt,
        "ForegroundNormal": fg, "ForegroundInactive": inactive, "ForegroundActive": active,
        "ForegroundLink": LINK, "ForegroundVisited": VISIT,
        "ForegroundNegative": NEG, "ForegroundNeutral": NEU, "ForegroundPositive": POS,
        "DecorationFocus": focus, "DecorationHover": hover,
    }


def colors_text():
    sections = {
        "Colors:Window": color_block(CHROME, PLATE),
        "Colors:View": color_block(BASE, "#0f0f0f"),
        "Colors:Button": color_block(PLATE, RAISE),
        "Colors:Header": color_block(CHROME, PLATE),
        "Colors:Header][Inactive": color_block(BASE, CHROME, fg=DIM, inactive=MUTE, focus=BLOOD2, hover=BLOOD),
        "Colors:Tooltip": color_block(PIT, CHROME),
        "Colors:Complementary": color_block(PIT, CHROME),
        "Colors:Selection": color_block("#780000", BLOOD2, fg="#ffffff", inactive="#d8caca", active="#ffffff"),
    }
    out = []
    out += ["[ColorEffects:Disabled]", "Color=40,36,36", "ColorAmount=0", "ColorEffect=0",
            "ContrastAmount=0.55", "ContrastEffect=1", "IntensityAmount=0.1", "IntensityEffect=2", ""]
    out += ["[ColorEffects:Inactive]", "ChangeSelectionColor=true", "Color=20,0,0", "ColorAmount=0.04",
            "ColorEffect=2", "ContrastAmount=0.15", "ContrastEffect=2", "Enable=true",
            "IntensityAmount=0", "IntensityEffect=0", ""]
    for name, block in sections.items():
        out.append(f"[{name}]")
        out += [f"{k}={csv(v)}" for k, v in sorted(block.items())]
        out.append("")
    out += ["[General]", f"ColorScheme={NAME}", f"Name={NAME}", "shadeSortColumn=true",
            f"AccentColor={csv(BLOOD)}", "", "[KDE]", "contrast=6", ""]
    out += ["[WM]", f"activeBackground={csv(PLATE)}", f"activeBlend={csv(EDGE)}",
            f"activeForeground={csv(BRIGHT)}", f"inactiveBackground={csv(BASE)}",
            f"inactiveBlend={csv(LINE)}", f"inactiveForeground={csv(MUTE)}", ""]
    return "\n".join(out)


# ── 2. Aurorae window decoration ─────────────────────────────────────────────
P = 14           # glow / shadow padding
B = 2            # side + bottom border (1px edge + 1px chrome)
TT, TH, TB = 3, 22, 3
T = TT + TH + TB  # 28 — title bar height
M = 20           # stretch-piece size

_gid = [0]


class Svg:
    def __init__(self):
        self.defs, self.body = [], []

    def grad_lin(self, x1, y1, x2, y2, stops):
        _gid[0] += 1
        gid = f"g{_gid[0]}"
        s = "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>' for o, c, a in stops)
        self.defs.append(f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" '
                         f'x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{s}</linearGradient>')
        return f"url(#{gid})"

    def grad_rad(self, cx, cy, r, stops):
        _gid[0] += 1
        gid = f"g{_gid[0]}"
        s = "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>' for o, c, a in stops)
        self.defs.append(f'<radialGradient id="{gid}" gradientUnits="userSpaceOnUse" '
                         f'cx="{cx}" cy="{cy}" r="{r}">{s}</radialGradient>')
        return f"url(#{gid})"

    def svg(self, w, h):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n'
                f'<defs>{"".join(self.defs)}</defs>\n' + "\n".join(self.body) + "\n</svg>\n")


def R(x, y, w, h, fill, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"{extra}/>'


def deco_svg():
    s = Svg()
    variants = {
        # prefix: (edge, inner-edge row, title top, title bottom, separator, side chrome, glow colour, glow alpha)
        "decoration":          (EDGE, BLOOD1, "#1d1d1d", "#101010", "#2a0000", CHROME, EDGE, 0.42),
        "decoration-inactive": (LINE2, "#161616", "#151515", "#0d0d0d", "#1c1c1c", "#0e0e0e", VOID, 0.55),
    }
    W = P + B + M + B + P
    H = P + T + M + B + P
    for vi, (prefix, (edge, inner, ttop, tbot, sep, side, gcol, ga)) in enumerate(variants.items()):
        oy = vi * (H + 10)
        g = [(0, gcol, ga), (0.35, gcol, round(ga * 0.38, 3)), (1, gcol, 0)]

        def title_col(x, y, w):
            fill = s.grad_lin(0, y + 2, 0, y + T - 1, [(0, ttop, 1), (1, tbot, 1)])
            return [R(x, y, w, 1, edge), R(x, y + 1, w, 1, inner), R(x, y + 2, w, T - 3, fill),
                    R(x, y + T - 1, w, 1, sep)]

        x0, x1, x2, x3 = 0, P + B, P + B + M, W
        y0, y1, y2 = oy, oy + P + T, oy + P + T + M
        parts = {}
        # top-left
        e = [R(x0, y0, P, P, s.grad_rad(P, y0 + P, P, g)),
             R(P, y0, B, P, s.grad_lin(0, y0 + P, 0, y0, g)),
             R(x0, y0 + P, P, T, s.grad_lin(P, 0, 0, 0, g)),
             R(P, y0 + P, 1, T, edge)] + title_col(P + 1, y0 + P, 1)
        parts["topleft"] = e
        parts["top"] = [R(x1, y0, M, P, s.grad_lin(0, y0 + P, 0, y0, g))] + title_col(x1, y0 + P, M)
        e = [R(x2 + B, y0, P, P, s.grad_rad(x2 + B, y0 + P, P, g)),
             R(x2, y0, B, P, s.grad_lin(0, y0 + P, 0, y0, g)),
             R(x2 + B, y0 + P, P, T, s.grad_lin(x2 + B, 0, x3, 0, g)),
             R(x2 + 1, y0 + P, 1, T, edge)] + title_col(x2, y0 + P, 1)
        parts["topright"] = e
        parts["left"] = [R(x0, y1, P, M, s.grad_lin(P, 0, 0, 0, g)), R(P, y1, 1, M, edge), R(P + 1, y1, 1, M, side)]
        parts["center"] = [R(x1, y1, M, M, side)]
        parts["right"] = [R(x2, y1, 1, M, side), R(x2 + 1, y1, 1, M, edge),
                          R(x2 + B, y1, P, M, s.grad_lin(x2 + B, 0, x3, 0, g))]
        parts["bottomleft"] = [R(x0, y2, P, B, s.grad_lin(P, 0, 0, 0, g)),
                               R(x0, y2 + B, P, P, s.grad_rad(P, y2 + B, P, g)),
                               R(P, y2 + B, B, P, s.grad_lin(0, y2 + B, 0, y2 + B + P, g)),
                               R(P, y2, 1, B, edge), R(P + 1, y2, 1, 1, side), R(P + 1, y2 + 1, 1, 1, edge)]
        parts["bottom"] = [R(x1, y2, M, 1, side), R(x1, y2 + 1, M, 1, edge),
                           R(x1, y2 + B, M, P, s.grad_lin(0, y2 + B, 0, y2 + B + P, g))]
        parts["bottomright"] = [R(x2, y2, 1, 1, side), R(x2, y2 + 1, 1, 1, edge), R(x2 + 1, y2, 1, B, edge),
                                R(x2 + B, y2, P, B, s.grad_lin(x2 + B, 0, x3, 0, g)),
                                R(x2 + B, y2 + B, P, P, s.grad_rad(x2 + B, y2 + B, P, g)),
                                R(x2, y2 + B, B, P, s.grad_lin(0, y2 + B, 0, y2 + B + P, g))]
        for k, els in parts.items():
            s.body.append(f'<g id="{prefix}-{k}">' + "".join(els) + "</g>")
    # maximized title strips (only the centre element is drawn when maximized)
    oy = 2 * (H + 10)
    for i, (prefix, top, ttop, tbot, sep) in enumerate([
            ("decoration-maximized", BLOOD, "#1d1d1d", "#101010", "#2a0000"),
            ("decoration-maximized-inactive", "#222222", "#151515", "#0d0d0d", "#1c1c1c")]):
        x = i * (M + 10)
        fill = s.grad_lin(0, oy + 1, 0, oy + T - 1, [(0, ttop, 1), (1, tbot, 1)])
        s.body.append(f'<g id="{prefix}-center">' + R(x, oy, M, 1, top) + R(x, oy + 1, M, T - 2, fill)
                      + R(x, oy + T - 1, M, 1, sep) + "</g>")
        # FrameSvgItem flattens a stretched centre to one colour; tiling keeps the strip intact.
        s.body.append(f'<rect id="{prefix}-hint-tile-center" x="{x}" y="{oy + T + 4}" width="2" height="2" '
                      'fill="#00ff00" opacity=".01"/>')
    return s.svg(W + 40, 3 * (H + 10))


BW, BH = 26, 22


def glyph(kind, color):
    sw = 'stroke="%s" stroke-width="1.4" fill="none" stroke-linecap="square"' % color
    c = lambda d: f'<path d="{d}" {sw}/>'
    if kind == "close":
        return c("M9 6.5 L17 14.5 M17 6.5 L9 14.5") + f'<rect x="12.3" y="9.8" width="1.4" height="1.4" fill="{color}"/>'
    if kind == "maximize":  # reticle
        return c("M8.5 9 V6.5 H11 M15 6.5 H17.5 V9 M17.5 13 V15.5 H15 M11 15.5 H8.5 V13") + \
            f'<rect x="12.3" y="10.3" width="1.4" height="1.4" fill="{color}"/>'
    if kind == "restore":
        return c("M10 10 V8 H12 M14 8 H16 V10 M16 12 V14 H14 M12 14 H10 V12") + \
            f'<rect x="11.8" y="9.8" width="2.4" height="2.4" fill="{color}"/>'
    if kind == "minimize":
        return c("M8.5 14.5 H17.5") + f'<rect x="12" y="11" width="2" height="1.4" fill="{color}"/>'
    if kind == "alldesktops":
        return c("M13 6.5 L17.5 11 L13 15.5 L8.5 11 Z")
    if kind == "keepabove":
        return c("M9 13.5 L13 9.5 L17 13.5")
    if kind == "keepbelow":
        return c("M9 8.5 L13 12.5 L17 8.5")
    raise ValueError(kind)


def button_svg(kind):
    is_close = kind == "close"
    states = {
        "active": (None, HOT if is_close else "#958c8c"),
        "hover": ((BLOOD if is_close else "#260000", EDGE), "#ffffff" if is_close else BRIGHT),
        "pressed": ((BLOOD2 if not is_close else "#5c0000", HOT), "#ffffff"),
        "inactive": (None, "#4d4747"),
        "hover-inactive": ((BLOOD if is_close else "#260000", EDGE), "#ffffff" if is_close else BRIGHT),
        "pressed-inactive": ((BLOOD2, HOT), "#ffffff"),
        "deactivated": (None, "#2b2828"),
        "deactivated-inactive": (None, "#222020"),
    }
    out = []
    for i, (st, (bg, fg)) in enumerate(states.items()):
        x = i * (BW + 4)
        inner = R(0, 0, BW, BH, "#000000", ' fill-opacity="0"')
        if bg:
            inner += R(0, 0, BW, BH, bg[0]) + R(0, BH - 1, BW, 1, bg[1])
        inner += glyph(kind, fg)
        out.append(f'<g id="{st}-center" transform="translate({x},0)">{inner}</g>')
    w = len(states) * (BW + 4)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{BH}" viewBox="0 0 {w} {BH}">\n'
            + "\n".join(out) + "\n</svg>\n")


def aurorae():
    d = SHARE / "aurorae/themes" / NAME
    write(d / "decoration.svg", deco_svg())
    for k in ("close", "maximize", "restore", "minimize", "alldesktops", "keepabove", "keepbelow"):
        write(d / f"{k}.svg", button_svg(k))
    a, i = csv(BRIGHT), csv(MUTE)
    write(d / f"{NAME}rc", f"""[General]
ActiveTextColor={a},255
InactiveTextColor={i},255
TitleAlignment=Left
TitleVerticalAlignment=Center
UseTextShadow=false
Shadow=true
Animation=0

[Layout]
BorderLeft={B}
BorderRight={B}
BorderBottom={B}
TitleEdgeTop={TT}
TitleEdgeBottom={TB}
TitleEdgeLeft=8
TitleEdgeRight=1
TitleBorderLeft=10
TitleBorderRight=10
TitleHeight={TH}
ButtonWidth={BW}
ButtonHeight={BH}
ButtonSpacing=1
ButtonMarginTop=0
ExplicitButtonSpacer=6
PaddingTop={P}
PaddingBottom={P}
PaddingLeft={P}
PaddingRight={P}
TitleEdgeTopMaximized={TT}
TitleEdgeBottomMaximized={TB}
TitleEdgeLeftMaximized=8
TitleEdgeRightMaximized=0
""")
    write(d / "metadata.desktop", f"""[Desktop Entry]
Name={NAME}
Comment=Black and dark-grey chrome cut with arterial red edges and a red focus glow
Type=Service
X-KDE-ServiceTypes=AuroraeTheme
X-KDE-Library=aurorae
X-KDE-PluginInfo-Author={AUTHOR}
X-KDE-PluginInfo-Name={NAME}
X-KDE-PluginInfo-Version=1.0.0
X-KDE-PluginInfo-License=GPLv3
""")


# ── 3. Plasma desktop style ──────────────────────────────────────────────────
def frame_svg(fill, center, edge, bracket, margin=6, C=8, Mi=16):
    """9-slice frame: 1px edge, bright L-brackets in the fixed-size corners."""
    W = C + Mi + C
    o = []
    pieces = {
        "topleft": (0, 0, C, C), "top": (C, 0, Mi, C), "topright": (C + Mi, 0, C, C),
        "left": (0, C, C, Mi), "center": (C, C, Mi, Mi), "right": (C + Mi, C, C, Mi),
        "bottomleft": (0, C + Mi, C, C), "bottom": (C, C + Mi, Mi, C), "bottomright": (C + Mi, C + Mi, C, C),
    }
    for k, (x, y, w, h) in pieces.items():
        els = [R(x, y, w, h, center if k == "center" else fill)]
        if k != "center":
            if "top" in k:
                els.append(R(x, 0, w, 1, edge))
            if "bottom" in k:
                els.append(R(x, W - 1, w, 1, edge))
            if "left" in k:
                els.append(R(0, y, 1, h, edge))
            if "right" in k:
                els.append(R(W - 1, y, 1, h, edge))
        if bracket and k in ("topleft", "topright", "bottomleft", "bottomright"):
            L = 6
            bx = 0 if "left" in k else W - L
            by = 0 if "top" in k else W - 2
            vx = 0 if "left" in k else W - 2
            vy = 0 if "top" in k else W - L
            els += [R(bx, by, L, 2, bracket), R(vx, vy, 2, L, bracket)]
        o.append(f'<g id="{k}">' + "".join(els) + "</g>")
    hint = ' fill="#00ff00" opacity=".01"'
    o += [f'<rect id="hint-stretch-borders" x="{W/2-1}" y="{W/2-1}" width="2" height="2"{hint}/>',
          f'<rect id="hint-top-margin" x="{C+2}" y="1" width="2" height="{margin}"{hint}/>',
          f'<rect id="hint-bottom-margin" x="{C+2}" y="{W-1-margin}" width="2" height="{margin}"{hint}/>',
          f'<rect id="hint-left-margin" x="1" y="{C+2}" width="{margin}" height="2"{hint}/>',
          f'<rect id="hint-right-margin" x="{W-1-margin}" y="{C+2}" width="{margin}" height="2"{hint}/>']
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{W}" viewBox="0 0 {W} {W}">\n'
            + "\n".join(o) + "\n</svg>\n")


def plasma_style():
    d = SHARE / "plasma/desktoptheme" / NAME
    files = {
        "widgets/background.svg": frame_svg("#0d0d0d", "#0d0d0d", BLOOD, HOT),
        "dialogs/background.svg": frame_svg("#0f0f0f", "#0f0f0f", EDGE, HOT),
        "widgets/panel-background.svg": frame_svg("#0b0b0b", "#0b0b0b", EDGE, None, margin=2),
        "widgets/tooltip.svg": frame_svg(PIT, PIT, BLOOD, EDGE, margin=5),
    }
    for sub in ("", "translucent/", "opaque/", "solid/"):
        for rel, txt in files.items():
            write(d / (sub + rel), txt)
    write(d / "colors", colors_text())
    write(d / "plasmarc", "[ContrastEffect]\nenabled=false\n\n[AdaptiveTransparency]\nenabled=false\n")
    write(d / "metadata.json", json.dumps({
        "KPlugin": {"Authors": [{"Name": AUTHOR}], "Category": "Plasma Theme",
                    "Description": "Black and dark-grey Plasma style with arterial red edges",
                    "EnabledByDefault": True, "Id": NAME, "License": "GPL-3.0-or-later",
                    "Name": NAME, "Version": "1.0.0"},
        "X-Plasma-API": "6.0"}, indent=2) + "\n")


# ── 4. Kvantum (recolour of splicer scorn's Org-XIII-Void widget map) ────────
KV_SRC = HOME / ".config/Kvantum/Org-XIII-Void"
KV_MAP = {
    "#6f5b91": BLOOD, "#a98ad6": HOT, "#11131d": BASE, "#090a10": CHROME, "#191c29": PLATE,
    "#332a47": "#4a0a0a", "#39f": "#c40000", "#e7e5ff": TEXT, "#85839c": DIM,
}


def to_grey(h):
    r, g, b = rgb(h)
    y = round(0.299 * r + 0.587 * g + 0.114 * b)
    return "#%02x%02x%02x" % (y, max(0, y - 3), max(0, y - 3))


def kv_recolor(text):
    def sub(m):
        h = m.group(0).lower()
        if h in KV_MAP:
            return KV_MAP[h]
        if h in ("#000", "#fff", "#000000", "#ffffff"):
            return h
        if h in ("#f04a50",):
            return NEG
        if len(h) in (4, 7):
            return to_grey(h)
        return h
    return re.sub(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b", sub, text)


def kvantum():
    d = CONF / "Kvantum" / NAME
    write(d / f"{NAME}.svg", kv_recolor((KV_SRC / "Org-XIII-Void.svg").read_text()))
    kv = (KV_SRC / "Org-XIII-Void.kvconfig").read_text()
    kv = re.sub(r"^author=.*$", f"author={AUTHOR}; engine map adapted from KvArcDark by Tsu Jan", kv, flags=re.M)
    kv = re.sub(r"^comment=.*$", "comment=Arterial — black/dark-grey surfaces, red edges", kv, flags=re.M)
    kv = kv.replace("progressbar_thickness=3font", "progressbar_thickness=3")
    kv = kv_recolor(kv)
    gc = f"""[GeneralColors]
window.color={CHROME}
base.color={BASE}
alt.base.color=#0f0f0f
button.color={PLATE}
light.color={LINE}
mid.light.color={PLATE}
dark.color=black
mid.color=#0e0e0e
highlight.color={BLOOD}
inactive.highlight.color={BLOOD2}
text.color={TEXT}
window.text.color={TEXT}
button.text.color={TEXT}
disabled.text.color={MUTE}
tooltip.text.color={TEXT}
highlight.text.color=white
link.color={LINK}
link.visited.color={VISIT}
progress.indicator.text.color=white

"""
    kv = re.sub(r"\[GeneralColors\].*?(?=^\[)", gc, kv, flags=re.S | re.M)
    write(d / f"{NAME}.kvconfig", kv)
    for f in ("LICENSE", "UPSTREAM-LICENSE-KVANTUM"):
        shutil.copy(KV_SRC / f, d / f)
    write(d / "NOTICE", "Widget map adapted from KvArcDark by Tsu Jan (Kvantum project) via splicer scorn's "
          "Org XIII — The Void, recoloured for Arterial. Distributed under GPL-3.0-or-later.\n")


# ── 5. KWin effects (scripted shader effects on the Burn-My-Windows harness) ─
BMW = HOME / ".local/share/kwin/effects/kwin6_effect_tv_glitch/contents/shaders"
MARK = "// The content from common.glsl is automatically prepended to each shader effect."


def bmw_prefix(fname):
    t = (BMW / fname).read_text()
    i = t.index(MARK) + len(MARK)
    return t[:i] + "\n// Arterial shader by splicer scorn — GPL-3.0-or-later.\n\n"


SOLID = """
float solidAt(vec2 c) {
  if (c.x < 0.0 || c.y < 0.0 || c.x > 1.0 || c.y > 1.0) {
    return 0.0;
  }
  return step(0.85, getInputColor(c).a);
}

// 1 on the outermost uEdgeWidth pixels of the opaque window body, 0 elsewhere.
float outlineAt(vec2 uv, vec2 px) {
  vec2 o  = uEdgeWidth * px;
  float c = solidAt(uv);
  float n = min(min(solidAt(uv + vec2(o.x, 0.0)), solidAt(uv - vec2(o.x, 0.0))),
                min(solidAt(uv + vec2(0.0, o.y)), solidAt(uv - vec2(0.0, o.y))));
  return c * (1.0 - n);
}
"""

INCISION = """
uniform vec4 uColor;
uniform float uSeed;
uniform float uEdgeWidth;
uniform float uTear;
""" + SOLID + """
// Open: two red tracers run the window's perimeter, then the body is cut open from a
// horizontal incision whose ragged lips tear sideways and drain from red to true colour.
// Close: the same, reversed.
void main() {
  float p = uForOpening ? uProgress : 1.0 - uProgress;
  vec2 uv = iTexCoord.st;
  vec2 px = 1.0 / uSize;

  float body    = solidAt(uv);
  float outline = outlineAt(uv, px);
  float ang     = fract(atan(uv.y - 0.5, uv.x - 0.5) / 6.2831853 + 0.625);
  float trace   = step(fract(ang * 2.0), easeOutQuad(clamp(p / 0.4, 0.0, 1.0)));
  outline *= trace * (1.0 - smoothstep(0.75, 1.0, p));

  float pb     = clamp((p - 0.18) / 0.72, 0.0, 1.0);
  float open   = easeOutQuad(pb);
  float live   = step(0.001, pb);
  float column = floor(uv.x * uSize.x / 18.0);
  float jag    = (hash12(vec2(column, uSeed * 97.0)) - 0.5) * 0.12 * (1.0 - open);
  float r      = open * 0.5 + jag * live;
  float d      = abs(uv.y - 0.5);
  float reveal = step(d, r) * live;
  float seam   = exp(-abs(d - r) * uSize.y / 2.5) * live * (1.0 - smoothstep(0.85, 1.0, pb));

  float band  = floor(uv.y * uSize.y / 5.0);
  float tick  = floor(uProgress * uDuration * 24.0);
  float shift = hash12(vec2(band, tick + uSeed * 53.0)) - 0.5;
  shift *= uTear * 0.08 * pow(1.0 - open, 2.0) * step(0.7, hash12(vec2(band * 1.7, tick)));
  vec2 sc  = uv + vec2(shift, 0.0);
  vec4 src = (sc.x < 0.0 || sc.x > 1.0) ? vec4(0.0) : getInputColor(sc);

  float lum   = dot(src.rgb, vec3(0.299, 0.587, 0.114));
  vec3 tint   = mix(src.rgb, uColor.rgb * (0.25 + 1.4 * lum), 0.75 * (1.0 - open));
  vec4 color  = vec4(tint, src.a * reveal);
  float glow  = clamp(outline + seam * body * 0.9, 0.0, 1.0);
  vec3 hot    = mix(uColor.rgb, vec3(1.0, 0.85, 0.85), seam * 0.35);
  setOutputColor(alphaOver(color, vec4(hot, glow)));
}
"""

PULSE = """
uniform vec4 uColor;
uniform float uEdgeWidth;
""" + SOLID + """
// Focus: the window's edge flashes arterial red and bleeds a short way inward, then fades.
void main() {
  vec2 uv  = iTexCoord.st;
  vec2 px  = 1.0 / uSize;
  vec4 src = getInputColor(uv);

  float body    = solidAt(uv);
  float outline = outlineAt(uv, px);
  vec2 dpx      = min(uv, 1.0 - uv) * uSize;
  float inner   = exp(-min(dpx.x, dpx.y) / 10.0) * body;
  float k       = (1.0 - uProgress) * (1.0 - uProgress);

  float glow = clamp((outline + 0.35 * inner) * k, 0.0, 1.0);
  setOutputColor(alphaOver(src, vec4(uColor.rgb, glow)));
}
"""

JS_HELPERS = r"""
function readRGBA(key, fallback) {
  const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})?([a-f\d]{2})?$/i.exec(
    String(effect.readConfig(key, fallback)));
  if (!m) {
    return [0.7, 0.0, 0.0, 1.0];
  }
  const c = m.slice(1).filter(x => x !== undefined).map(x => parseInt(x, 16) / 255);
  return c.length == 3 ? [c[0], c[1], c[2], 1.0] : [c[1], c[2], c[3], c[0]];
}

const blacklist = [
  'ksmserver ksmserver', 'ksmserver-logout-greeter ksmserver-logout-greeter',
  'ksplashqml ksplashqml'
];

// Window filter adapted from Burn-My-Windows (Simon Schneegans, Vlad Zahorodnii,
// Martin Flöser), GPL-3.0-or-later.
function shouldAnimate(window) {
  if (window.windowClass == 'plasmashell plasmashell' ||
      window.windowClass == 'plasmashell org.kde.plasmashell') {
    return window.hasDecoration;
  }
  if (!window.hasDecoration && window.onAllDesktops) {
    return false;
  }
  if (blacklist.indexOf(window.windowClass) != -1) {
    return false;
  }
  if (window.hasDecoration) {
    return true;
  }
  if (window.popupWindow || window.lockScreen || window.outline || !window.managed) {
    return false;
  }
  return window.normalWindow || window.dialog;
}

function forceRoles(window, on) {
  window.setData(Effect.WindowForceBackgroundContrastRole, on ? true : null);
  window.setData(Effect.WindowForceBlurRole, on ? true : null);
}
"""

INCISION_JS = """// SPDX-FileCopyrightText: splicer scorn; harness after Burn-My-Windows by Simon Schneegans,
// Vlad Zahorodnii and Martin Flöser
// SPDX-License-Identifier: GPL-3.0-or-later

'use strict';
""" + JS_HELPERS + r"""
class ArterialIncision {
  constructor() {
    effect.configChanged.connect(this.loadConfig.bind(this));
    effect.animationEnded.connect(window => forceRoles(window, false));
    effects.windowAdded.connect(this.onAdded.bind(this));
    effects.windowClosed.connect(this.onClosed.bind(this));
    effects.windowDataChanged.connect(this.onDataChanged.bind(this));
    this.shader = effect.addFragmentShader(Effect.MapTexture, 'arterial-incision.frag');
    this.loadConfig();
  }

  loadConfig() {
    this.duration = animationTime(effect.readConfig('Duration', 900));
    effect.setUniform(this.shader, 'uDuration', this.duration * 0.001);
    effect.setUniform(this.shader, 'uEdgeWidth', effect.readConfig('EdgeWidth', 2.0));
    effect.setUniform(this.shader, 'uTear', effect.readConfig('Tear', 1.0));
    effect.setUniform(this.shader, 'uColor', readRGBA('Color', '#e01b1b'));
  }

  run(window, opening) {
    forceRoles(window, true);
    effect.setUniform(this.shader, 'uForOpening', opening ? 1.0 : 0.0);
    effect.setUniform(this.shader, 'uIsFullscreen', window.fullScreen ? 1.0 : 0.0);
    effect.setUniform(this.shader, 'uSeed', Math.random());
    return animate({
      window: window,
      curve: QEasingCurve.Linear,
      duration: this.duration,
      animations: [{
        type: Effect.ShaderUniform,
        fragmentShader: this.shader,
        uniform: 'uProgress',
        from: 0.0,
        to: 1.0
      }]
    });
  }

  onAdded(window) {
    window.arterialBorn = Date.now();
    if (effects.hasActiveFullScreenEffect || !shouldAnimate(window) || !window.visible) {
      return;
    }
    if (effect.isGrabbed(window, Effect.WindowAddedGrabRole)) {
      return;
    }
    window.arterialIn = this.run(window, true);
  }

  onClosed(window) {
    if (effects.hasActiveFullScreenEffect || !shouldAnimate(window)) {
      return;
    }
    if (!window.visible || window.skipsCloseAnimation) {
      return;
    }
    if (effect.isGrabbed(window, Effect.WindowClosedGrabRole)) {
      return;
    }
    if (window.arterialIn) {
      cancel(window.arterialIn);
      delete window.arterialIn;
    }
    window.arterialOut = this.run(window, false);
  }

  onDataChanged(window, role) {
    const key = role == Effect.WindowAddedGrabRole ? 'arterialIn' :
                role == Effect.WindowClosedGrabRole ? 'arterialOut' : null;
    if (key && window[key] && effect.isGrabbed(window, role)) {
      cancel(window[key]);
      delete window[key];
      forceRoles(window, false);
    }
  }
}

new ArterialIncision();
"""

PULSE_JS = """// SPDX-FileCopyrightText: splicer scorn
// SPDX-License-Identifier: GPL-3.0-or-later

'use strict';
""" + JS_HELPERS + r"""
class ArterialPulse {
  constructor() {
    effect.configChanged.connect(this.loadConfig.bind(this));
    effect.animationEnded.connect(this.onEnded.bind(this));
    effects.windowAdded.connect(window => { window.arterialBorn = Date.now(); });
    effects.windowActivated.connect(this.onActivated.bind(this));
    this.shader = effect.addFragmentShader(Effect.MapTexture, 'arterial-pulse.frag');
    this.loadConfig();
  }

  loadConfig() {
    this.duration = animationTime(effect.readConfig('Duration', 600));
    effect.setUniform(this.shader, 'uEdgeWidth', effect.readConfig('EdgeWidth', 2.0));
    effect.setUniform(this.shader, 'uColor', readRGBA('Color', '#e01b1b'));
  }

  onActivated(window) {
    if (!window || effects.hasActiveFullScreenEffect || !shouldAnimate(window)) {
      return;
    }
    if (!window.visible || window.minimized || window.fullScreen) {
      return;
    }
    // A freshly opened window is already being cut open by the incision effect.
    if (window.arterialBorn && Date.now() - window.arterialBorn < 1200) {
      return;
    }
    if (window.arterialPulse) {
      cancel(window.arterialPulse);
      delete window.arterialPulse;
    }
    forceRoles(window, true);
    effect.setUniform(this.shader, 'uForOpening', 1.0);
    effect.setUniform(this.shader, 'uIsFullscreen', 0.0);
    window.arterialPulse = animate({
      window: window,
      curve: QEasingCurve.OutQuad,
      duration: this.duration,
      animations: [{
        type: Effect.ShaderUniform,
        fragmentShader: this.shader,
        uniform: 'uProgress',
        from: 0.0,
        to: 1.0
      }]
    });
  }

  onEnded(window) {
    forceRoles(window, false);
    delete window.arterialPulse;
  }
}

new ArterialPulse();
"""


def kcfg(entries):
    rows = "\n".join(f'    <entry name="{n}" type="{t}">\n      <default>{v}</default>\n    </entry>'
                     for n, t, v in entries)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<kcfg xmlns="http://www.kde.org/standards/kcfg/1.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="http://www.kde.org/standards/kcfg/1.0 http://www.kde.org/standards/kcfg/1.0/kcfg.xsd">
  <kcfgfile name="" />
  <group name="">
{rows}
  </group>
</kcfg>
"""


def config_ui(entries):
    rows = []
    for i, (n, t, v) in enumerate(entries):
        rows.append(f"""   <item row="{i}" column="0"><widget class="QLabel" name="l{i}"><property name="text"><string>{n}</string></property></widget></item>""")
        if t == "Color":
            w = f'<widget class="KColorButton" name="kcfg_{n}"/>'
        elif t == "Double":
            w = (f'<widget class="QDoubleSpinBox" name="kcfg_{n}"><property name="maximum"><double>8</double></property>'
                 f'<property name="singleStep"><double>0.5</double></property></widget>')
        else:
            w = (f'<widget class="QSpinBox" name="kcfg_{n}"><property name="maximum"><number>3000</number></property>'
                 f'<property name="singleStep"><number>20</number></property></widget>')
        rows.append(f'   <item row="{i}" column="1">{w}</item>')
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>ArterialConfigForm</class>
 <widget class="QWidget" name="ArterialConfigForm">
  <layout class="QGridLayout" name="grid">
{chr(10).join(rows)}
  </layout>
 </widget>
 <customwidgets>
  <customwidget><class>KColorButton</class><extends>QPushButton</extends><header>kcolorbutton.h</header></customwidget>
 </customwidgets>
</ui>
"""


def effect_pkg(eid, name, desc, js, frag_name, frag, entries, exclusive):
    d = SHARE / "kwin/effects" / eid
    meta = {
        "KPackageStructure": "KWin/Effect",
        "KPlugin": {"Name": name, "Description": desc, "Category": "Window Open/Close Animation"
                    if exclusive else "Focus", "Authors": [{"Name": AUTHOR}], "Id": eid,
                    "License": "GPLv3", "Version": "1.0", "EnabledByDefault": False},
        "X-KDE-ConfigModule": "kcm_kwin4_genericscripted",
        "X-KDE-Ordering": "60",
        "X-KDE-PluginKeyword": eid,
        "X-Plasma-API": "javascript",
        "X-Plasma-MainScript": "code/main.js",
    }
    if exclusive:
        meta["X-KWin-Exclusive-Category"] = "toplevel-open-close-animation"
    write(d / "metadata.json", json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    write(d / "contents/code/main.js", js)
    write(d / "contents/config/main.xml", kcfg(entries))
    write(d / "contents/ui/config.ui", config_ui(entries))
    write(d / f"contents/shaders/{frag_name}.frag", bmw_prefix("tv-glitch.frag") + frag)
    write(d / f"contents/shaders/{frag_name}_core.frag", bmw_prefix("tv-glitch_core.frag") + frag)


def effects():
    effect_pkg("arterial_incision", "Arterial Incision",
               "Red tracers outline the window, then it is cut open along a ragged incision",
               INCISION_JS, "arterial-incision", INCISION,
               [("Duration", "UInt", 900), ("EdgeWidth", "Double", 2), ("Tear", "Double", 1),
                ("Color", "Color", HOT.upper())], True)
    effect_pkg("arterial_pulse", "Arterial Pulse",
               "The focused window's edge flashes arterial red and bleeds inward",
               PULSE_JS, "arterial-pulse", PULSE,
               [("Duration", "UInt", 600), ("EdgeWidth", "Double", 2), ("Color", "Color", HOT.upper())], False)


# ── 6. terminals ─────────────────────────────────────────────────────────────
TERM = {
    "background": "#050505", "foreground": TEXT,
    0: VOID, 8: "#2b2626", 1: BLOOD, 9: "#d41a1a", 2: "#5d6b5a", 10: "#7f927b",
    3: "#8a6d3b", 11: NEU, 4: "#4a4f5c", 12: "#6f7686", 5: "#6b2a3a", 13: "#a8455e",
    6: "#5a6a6a", 14: "#889a9a", 7: "#9e9494", 15: BRIGHT,
}


def terminals():
    k = [f"# {NAME} — kitty palette (splicer scorn)", f"background {TERM['background']}",
         f"foreground {TERM['foreground']}", f"selection_background {BLOOD2}", "selection_foreground #ffffff",
         f"cursor {HOT}", "cursor_text_color #000000", f"url_color {LINK}",
         f"active_border_color {EDGE}", f"inactive_border_color {LINE}", f"bell_border_color {FLARE}",
         "window_border_width 1px", "draw_minimal_borders yes",
         "tab_bar_style separator", 'tab_separator "  "', f"active_tab_background {BLOOD1}",
         f"active_tab_foreground {BRIGHT}", f"inactive_tab_background {PIT}",
         f"inactive_tab_foreground {MUTE}", f"tab_bar_background {VOID}", f"mark1_background {BLOOD}"]
    k += [f"color{i} {TERM[i]}" for i in range(16)]
    write(CONF / "kitty/arterial.conf", "\n".join(k) + "\n")

    names = {0: "Color0", 1: "Color1", 2: "Color2", 3: "Color3", 4: "Color4", 5: "Color5", 6: "Color6", 7: "Color7"}
    out = []
    for sect, h in (("Background", TERM["background"]), ("BackgroundIntense", "#0d0d0d"),
                    ("BackgroundFaint", TERM["background"]), ("Foreground", TEXT),
                    ("ForegroundIntense", BRIGHT), ("ForegroundFaint", DIM)):
        out += [f"[{sect}]", f"Color={csv(h)}", ""]
    for i, n in names.items():
        out += [f"[{n}]", f"Color={csv(TERM[i])}", "", f"[{n}Intense]", f"Color={csv(TERM[i + 8])}", "",
                f"[{n}Faint]", f"Color={csv(TERM[i])}", ""]
    out += ["[General]", "Anchor=0.5,0.5", "Blur=true", "ColorRandomization=false",
            f"Description={NAME}", "FillStyle=Tile", "Opacity=0.9", "Wallpaper=", "WallpaperFlipType=NoFlip",
            "WallpaperOpacity=1", ""]
    write(SHARE / "konsole" / f"{NAME}.colorscheme", "\n".join(out))


def mako():
    write(CONF / "mako/config", f"""# {NAME} — mako notifications (splicer scorn)
background-color={BASE}f0
text-color={TEXT}
border-color={EDGE}
border-size=1
border-radius=0
padding=8
progress-color=over {BLOOD2}

[urgency=low]
border-color={BLOOD1}

[urgency=critical]
border-color={FLARE}
text-color={BRIGHT}
""")


if __name__ == "__main__":
    if DIST.exists():
        shutil.rmtree(DIST)
    write(SHARE / "color-schemes" / f"{NAME}.colors", colors_text())
    aurorae()
    plasma_style()
    kvantum()
    effects()
    terminals()
    mako()
    n = sum(1 for _ in DIST.rglob("*") if _.is_file())
    print(f"built {n} files into {DIST}")
