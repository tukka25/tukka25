"""Neon section titles and the synthwave footer."""
import random

import hero
from svgkit import C, DISPLAY, MONO, display_width, esc, font_face, scan_css, scanlines, write

SECTIONS = [
    ("whoami", "WHOAMI"),
    ("stack", "TECH STACK"),
    ("maze", "ENTER THE MAZE"),
    ("builds", "FEATURED BUILDS"),
    ("stats", "TELEMETRY"),
    ("city", "CONTRIBUTION CITY"),
    ("snake", "THE SNAKE IS HUNGRY"),
]

TW, TH, SIZE, SPACING = 900, 64, 24, 6


def title(index, slug, label):
    tag = f"0x{index:02X}"
    text_w = display_width(label, SIZE, SPACING)
    tag_w = len(tag) * 13 * 0.6 + 12
    total = tag_w + text_w
    x0 = TW / 2 - total / 2
    inner_l, inner_r = x0 - 22, x0 + total + 22
    y = 33
    css = f"""
{font_face(DISPLAY, 900, label)}
{font_face(MONO, 600, tag)}
.d{{font-family:'HeroDisplay','Orbitron','Arial Black',sans-serif;font-weight:900;font-size:{SIZE}px;letter-spacing:{SPACING}px}}
.m{{font-family:'TermMono','JetBrains Mono',ui-monospace,monospace;font-weight:600;font-size:13px}}
.flick{{animation:flick 7s steps(1,end) infinite;animation-delay:-{index * 1.3:.1f}s}}
@keyframes flick{{0%,90%,100%{{opacity:1}}91%{{opacity:.3}}92%{{opacity:1}}94%{{opacity:.55}}95%{{opacity:1}}}}
.run{{stroke-dasharray:46 1400;animation:run 3.2s linear infinite}}
@keyframes run{{from{{stroke-dashoffset:46}}to{{stroke-dashoffset:-460}}}}
"""
    return write(
        f"title-{slug}.svg",
        f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {TW} {TH}" width="{TW}" height="{TH}" role="img" aria-label="{esc(label.title())}">
<title>{esc(label.title())}</title>
<style>{css}</style>
<defs>
  <linearGradient id="tg" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{C["magenta"]}"/>
    <stop offset="1" stop-color="{C["violet"]}"/>
  </linearGradient>
  <linearGradient id="ll" gradientUnits="userSpaceOnUse" x1="{inner_l:.1f}" y1="0" x2="20" y2="0">
    <stop offset="0" stop-color="{C["magenta"]}"/>
    <stop offset="1" stop-color="{C["magenta"]}" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="lr" gradientUnits="userSpaceOnUse" x1="{inner_r:.1f}" y1="0" x2="{TW - 20}" y2="0">
    <stop offset="0" stop-color="{C["violet"]}"/>
    <stop offset="1" stop-color="{C["violet"]}" stop-opacity="0"/>
  </linearGradient>
  <filter id="glow" x="-10%" y="-60%" width="120%" height="220%">
    <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>
<line x1="{inner_l:.1f}" y1="{y}" x2="20" y2="{y}" stroke="url(#ll)" stroke-width="2"/>
<line x1="{inner_r:.1f}" y1="{y}" x2="{TW - 20}" y2="{y}" stroke="url(#lr)" stroke-width="2"/>
<line class="run" x1="{inner_l:.1f}" y1="{y}" x2="20" y2="{y}" stroke="{C["cyan"]}" stroke-width="3" stroke-linecap="round"/>
<line class="run" x1="{inner_r:.1f}" y1="{y}" x2="{TW - 20}" y2="{y}" stroke="{C["cyan"]}" stroke-width="3" stroke-linecap="round"/>
<rect x="{inner_l - 4:.1f}" y="{y - 4}" width="8" height="8" transform="rotate(45 {inner_l:.1f} {y})" fill="{C["magenta"]}"/>
<rect x="{inner_r - 4:.1f}" y="{y - 4}" width="8" height="8" transform="rotate(45 {inner_r:.1f} {y})" fill="{C["violet"]}"/>
<g class="flick" filter="url(#glow)">
  <text class="m" x="{x0:.1f}" y="{y + 5}" fill="{C["violet"]}">{tag}</text>
  <text class="d" x="{x0 + tag_w:.1f}" y="{y + 9}" fill="url(#tg)">{esc(label)}</text>
</g>
</svg>
""",
    )


def footer():
    W, H, RX, HORIZON = 1200, 170, 22, 100
    rng = random.Random(42)
    text = "SEE YOU IN THE NEXT COMMIT"
    size = 30
    tw = display_width(text, size, 4)
    grid_lines, grid_css = hero.grid(w=W, h=H, horizon=HORIZON, k_scale=55.0, spread=110)
    stars = "".join(
        f'<circle class="tw" cx="{rng.uniform(10, W - 10):.0f}" cy="{rng.uniform(8, HORIZON - 12):.0f}" r="{rng.choice([0.7, 1, 1.3])}" '
        f'fill="{C["text"]}" style="animation-delay:-{rng.uniform(0, 4):.1f}s"/>'
        for _ in range(45)
    )
    hud_l, hud_r = "❯ exit 0", "github.com/tukka25"
    css = f"""
{font_face(DISPLAY, 900, text)}
{font_face(MONO, 500, hud_l + hud_r)}
.d{{font-family:'HeroDisplay','Orbitron','Arial Black',sans-serif;font-weight:900}}
.m{{font-family:'TermMono','JetBrains Mono',ui-monospace,monospace;font-weight:500;font-size:13px;letter-spacing:2px;fill:{C["dim"]}}}
.tw{{animation:tw 4s ease-in-out infinite}}
@keyframes tw{{0%,100%{{opacity:.15}}50%{{opacity:1}}}}
{grid_css}
{scan_css(H)}
"""
    return write(
        "footer.svg",
        f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="See you in the next commit">
<title>See you in the next commit</title>
<style>{css}</style>
<defs>
  <clipPath id="frame"><rect width="{W}" height="{H}" rx="{RX}"/></clipPath>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#05010f"/>
    <stop offset=".6" stop-color="#2a0748"/>
    <stop offset="1" stop-color="#8a1270"/>
  </linearGradient>
  <linearGradient id="floor" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#2a0748"/>
    <stop offset="1" stop-color="{C["night"]}"/>
  </linearGradient>
  <linearGradient id="fadeG" gradientUnits="userSpaceOnUse" x1="0" y1="{HORIZON}" x2="0" y2="{H}">
    <stop offset="0" stop-color="#fff" stop-opacity="0"/>
    <stop offset=".5" stop-color="#fff" stop-opacity=".9"/>
    <stop offset="1" stop-color="#fff"/>
  </linearGradient>
  <mask id="gridFade"><rect y="{HORIZON}" width="{W}" height="{H - HORIZON}" fill="url(#fadeG)"/></mask>
  <linearGradient id="chrome" gradientUnits="userSpaceOnUse" x1="0" y1="{62 - size * 0.75:.0f}" x2="0" y2="62">
    <stop offset="0" stop-color="#dffcff"/>
    <stop offset=".46" stop-color="#ffffff"/>
    <stop offset=".54" stop-color="#ff9be6"/>
    <stop offset="1" stop-color="{C["magenta"]}"/>
  </linearGradient>
  <linearGradient id="edge" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{C["cyan"]}"/>
    <stop offset=".5" stop-color="{C["violet"]}"/>
    <stop offset="1" stop-color="{C["magenta"]}"/>
  </linearGradient>
  <filter id="neon" x="-10%" y="-60%" width="120%" height="220%">
    <feGaussianBlur in="SourceAlpha" stdDeviation="6" result="b"/>
    <feFlood flood-color="{C["magenta"]}" flood-opacity=".8"/>
    <feComposite in2="b" operator="in" result="g"/>
    <feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="soft"><feGaussianBlur stdDeviation="2.4"/></filter>
</defs>
<g clip-path="url(#frame)">
  <rect width="{W}" height="{HORIZON}" fill="url(#sky)"/>
  {stars}
  <rect y="{HORIZON}" width="{W}" height="{H - HORIZON}" fill="url(#floor)"/>
  <g mask="url(#gridFade)" stroke="{C["magenta"]}" stroke-width="1.5">
    <g filter="url(#soft)" opacity=".8">{grid_lines}</g>
    <g>{grid_lines}</g>
  </g>
  <line x1="0" y1="{HORIZON}" x2="{W}" y2="{HORIZON}" stroke="{C["magenta"]}" stroke-width="2.5" filter="url(#soft)"/>
  <line x1="0" y1="{HORIZON}" x2="{W}" y2="{HORIZON}" stroke="#ffd0f5" stroke-width="1"/>
  <text class="d" x="{W / 2}" y="62" text-anchor="middle" font-size="{size}" letter-spacing="4" fill="url(#chrome)" filter="url(#neon)">{text}</text>
  <text class="m" x="28" y="{H - 20}">{esc(hud_l)}</text>
  <text class="m" x="{W - 28}" y="{H - 20}" text-anchor="end">{hud_r}</text>
  {scanlines(W, H, RX, 0.08)}
</g>
<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="{RX}" fill="none" stroke="url(#edge)" stroke-width="1.5"/>
</svg>
""",
    ), tw


def build():
    for i, (slug, label) in enumerate(SECTIONS, start=1):
        title(i, slug, label)
    footer()


if __name__ == "__main__":
    build()
