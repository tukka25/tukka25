"""Shared helpers for the profile SVG generators.

SVGs embedded in a GitHub README are rendered as <img>, so they cannot load
external fonts or run JS. Fonts are therefore subset to the characters actually
used and inlined as base64 WOFF2, and all motion is CSS keyframes or SMIL.
"""
import base64
import io
import pathlib

from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS = ROOT / "scripts" / "fonts"
ASSETS = ROOT / "assets"

# Anthropic brand palette (Dark, Light, grays; Orange, Blue, Green accents) plus
# a few warm in-betweens, shared by every asset so the profile reads as one system.
C = {
    "dark": "#141413",
    "surface": "#1f1e1d",
    "raised": "#262624",
    "line": "#3a3835",
    "light": "#faf9f5",
    "cloud": "#e8e6dc",
    "soft": "#c2c0b6",
    "mid": "#b0aea5",
    "muted": "#87867f",
    "orange": "#d97757",
    "clay": "#c15f3c",
    "kraft": "#d4a27f",
    "manilla": "#ebdbbc",
    "blue": "#6a9bcc",
    "green": "#788c5d",
}

# Families are renamed in @font-face: Lora is an OFL Reserved Font Name.
DISPLAY = ("Lora.ttf", "HeroSerif")
LABEL = ("Poppins-SemiBold.ttf", "LabelSans")
MONO = ("JetBrainsMono.ttf", "TermMono")
MONO_ADVANCE = 0.6  # JetBrains Mono advance width, in em


def font_face(font, weight, text):
    """Return an @font-face rule embedding `font` at `weight`, subset to `text`."""
    filename, family = font
    tt = TTFont(FONTS / filename)
    if "fvar" in tt:
        tt = instantiateVariableFont(tt, {"wght": weight})
    opts = Options()
    opts.layout_features = ["kern"]
    opts.hinting = False
    opts.desubroutinize = True
    sub = Subsetter(options=opts)
    sub.populate(text="".join(sorted(set(text))) + " ")
    sub.subset(tt)
    tt.flavor = "woff2"
    buf = io.BytesIO()
    tt.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return (
        f"@font-face{{font-family:'{family}';font-weight:{weight};"
        f"src:url(data:font/woff2;base64,{b64}) format('woff2');}}"
    )


def text_width(font, text, size, spacing=0, weight=600):
    """Rendered width of `text` in `font`, from its advance widths."""
    tt = TTFont(FONTS / font[0])
    if "fvar" in tt:
        tt = instantiateVariableFont(tt, {"wght": weight})
    cmap, hmtx, upm = tt.getBestCmap(), tt["hmtx"], tt["head"].unitsPerEm
    adv = sum(hmtx[cmap[ord(ch)]][0] for ch in text)
    return adv * size / upm + spacing * (len(text) - 1)


def missing_glyphs(font, text):
    cmap = TTFont(FONTS / font[0]).getBestCmap()
    return sorted({ch for ch in text if ord(ch) not in cmap and not ch.isspace()})


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def pct(t, total):
    """Seconds -> keyframe percentage string."""
    return f"{max(0.0, min(100.0, 100.0 * t / total)):.3f}%"


def write(name, svg):
    ASSETS.mkdir(exist_ok=True)
    path = ASSETS / name
    path.write_text(svg, encoding="utf-8")
    print(f"  {name:<24} {len(svg.encode()) / 1024:7.1f} KB")
    return path


def scanlines(w, h, rx, opacity=0.14):
    """CRT scanline overlay plus a slow bright sweep bar."""
    return f"""
  <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">
    <rect width="4" height="2" fill="#000"/>
  </pattern>
  <linearGradient id="sweep" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#fff" stop-opacity="0"/>
    <stop offset=".5" stop-color="#fff" stop-opacity=".06"/>
    <stop offset="1" stop-color="#fff" stop-opacity="0"/>
  </linearGradient>
  <g pointer-events="none">
    <rect width="{w}" height="{h}" rx="{rx}" fill="url(#scan)" opacity="{opacity}"/>
    <rect class="sweep" y="-120" width="{w}" height="120" fill="url(#sweep)"/>
  </g>"""


def scan_css(h):
    return (
        ".sweep{animation:sweep 7s linear infinite}"
        f"@keyframes sweep{{from{{transform:translateY(0)}}to{{transform:translateY({h + 240}px)}}}}"
    )
