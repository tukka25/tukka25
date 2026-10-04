"""Hero banner: ember sun, rolling grid, glitching serif name, typing roles."""
import random

from svgkit import C, DISPLAY, MONO, MONO_ADVANCE, esc, font_face, scan_css, scanlines, text_width, write

W, H, RX = 1200, 420, 22
HORIZON = 300
SUN_R = 150
NAME = "Abdalrahman Tukka"
NAME_SIZE = 68
NAME_BASE = 112
ROLES = [
    "Software Developer",
    "C/C++ systems, forged at 42",
    "building AI agents & MCP tools",
    "raycasting walls since cub3d",
    "hackathon regular",
]
ROLE_SIZE = 21
TYPE_DT, DELETE_DT, HOLD, GAP = 0.065, 0.028, 1.9, 0.35

HUD = {
    "tl": "~/tukka25",
    "tr": "ONLINE",
    "bl": "SYS  C / C++ / PY / TS / KT / SWIFT",
    "br": "EST. 2018",
}


def stars(rng, n=90):
    out = []
    for _ in range(n):
        x, y = rng.uniform(8, W - 8), rng.uniform(8, HORIZON - 70)
        r = rng.choice([0.6, 0.8, 1.0, 1.2, 1.6])
        dur, delay = rng.uniform(2.2, 5.5), rng.uniform(0, 5)
        col = rng.choice([C["light"], C["light"], C["mid"], C["kraft"]])
        out.append(
            f'<circle class="tw" cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="{col}" '
            f'style="animation-duration:{dur:.1f}s;animation-delay:-{delay:.1f}s"/>'
        )
    return "\n    ".join(out)


def ridge(rng, x0, x1, base, peak, rough):
    """Midpoint-displacement mountain silhouette as a closed polygon."""
    pts = {x0: base - rng.uniform(5, 15), x1: base - rng.uniform(5, 15)}

    def split(a, b, amp):
        if b - a < 14:
            return
        m = (a + b) // 2
        pts[m] = max(base - peak, min(base - 2, (pts[a] + pts[b]) / 2 + rng.uniform(-amp, amp)))
        split(a, m, amp * rough)
        split(m, b, amp * rough)

    split(x0, x1, peak)
    line = " ".join(f"{x},{pts[x]:.0f}" for x in sorted(pts))
    return f"{x0},{base} {line} {x1},{base}"


def sun_stripes(cy):
    """Conveyor of horizontal cut-outs: each stripe grows into the next one's slot."""
    n, top, bottom = 7, cy - SUN_R * 0.62, HORIZON + 2
    slots = [(top + (bottom - top) * (k / n) ** 0.85, 1.0 + 9.0 * k / n) for k in range(n + 1)]
    out = []
    for k in range(n):
        (y0, h0), (y1, h1) = slots[k], slots[k + 1]
        out.append(
            f'<rect x="{600 - SUN_R}" width="{2 * SUN_R}" fill="url(#skyU)">'
            f'<animate attributeName="y" values="{y0:.1f};{y1:.1f}" dur="2.6s" repeatCount="indefinite"/>'
            f'<animate attributeName="height" values="{h0:.1f};{h1:.1f}" dur="2.6s" repeatCount="indefinite"/>'
            "</rect>"
        )
    return "\n      ".join(out)


def grid(w=W, h=H, horizon=HORIZON, k_scale=118.0, spread=125):
    cx = w / 2
    verticals = "".join(
        f'<line x1="{cx}" y1="{horizon}" x2="{cx + k * spread}" y2="{h + 60}"/>' for k in range(-13, 14)
    )
    # Each horizontal line rides the same perspective curve (offset = K / depth);
    # staggering them evenly in time spaces them evenly in depth.
    stops, z_far, z_near = 12, 26.0, 0.75
    frames = []
    for i in range(stops + 1):
        u = i / stops
        z = z_far - (z_far - z_near) * u
        frames.append(f"{100 * u:.1f}%{{transform:translateY({k_scale / z:.1f}px)}}")
    n, period = 10, 2.4
    horizontals = "".join(
        f'<line class="hl" x1="0" x2="{w}" y1="{horizon}" y2="{horizon}" '
        f'style="animation-delay:-{period * i / n:.2f}s"/>'
        for i in range(n)
    )
    css = f"@keyframes hl{{{''.join(frames)}}}.hl{{animation:hl {period}s linear infinite}}"
    return verticals + horizontals, css


def roles_typing(x0, y):
    cw = ROLE_SIZE * MONO_ADVANCE
    windows, t = [], 0.4
    for role in ROLES:
        n = len(role)
        windows.append((t, role))
        t += n * TYPE_DT + HOLD + n * DELETE_DT + GAP
    total = t

    paths, texts, cursor = [], [], [(0.0, 0)]
    for i, (s, role) in enumerate(windows):
        n = len(role)
        ev = [(0.0, 0)]
        ev += [(s + k * TYPE_DT, k) for k in range(1, n + 1)]
        d0 = s + n * TYPE_DT + HOLD
        ev += [(d0 + (k - 1) * DELETE_DT, n - k) for k in range(1, n + 1)]
        cursor += ev[1:]
        key_times = ";".join(f"{e[0] / total:.5f}" for e in ev)
        values = ";".join(f"M{x0:.1f} {y} h{e[1] * cw:.1f}" for e in ev)
        paths.append(
            f'<path id="r{i}" d="M{x0:.1f} {y} h0">'
            f'<animate attributeName="d" dur="{total:.2f}s" repeatCount="indefinite" calcMode="discrete" '
            f'keyTimes="{key_times}" values="{values}"/></path>'
        )
        texts.append(f'<text class="mono role"><textPath xlink:href="#r{i}" href="#r{i}">{esc(role)}</textPath></text>')

    cursor.sort()
    key_times = ";".join(f"{t / total:.5f}" for t, _ in cursor)
    values = ";".join(f"{x0 + n * cw + 2:.1f}" for _, n in cursor)
    caret = (
        f'<rect class="caret" x="{x0 + 2:.1f}" y="{y - ROLE_SIZE * 0.78:.1f}" width="{cw * 0.55:.1f}" '
        f'height="{ROLE_SIZE * 0.95:.1f}" fill="{C["orange"]}">'
        f'<animate attributeName="x" dur="{total:.2f}s" repeatCount="indefinite" calcMode="discrete" '
        f'keyTimes="{key_times}" values="{values}"/></rect>'
    )
    return "".join(paths), "".join(texts) + caret


def build():
    rng = random.Random(25)
    name_w = text_width(DISPLAY, NAME, NAME_SIZE, 1)
    name_top = NAME_BASE - NAME_SIZE * 0.74

    cw = ROLE_SIZE * MONO_ADVANCE
    max_role = max(len(r) for r in ROLES)
    pill_w = 22 * 2 + cw * (2 + max_role + 1)
    pill_x, pill_y, pill_h = 600 - pill_w / 2, 136, 40
    text_x, text_y = pill_x + 22 + 2 * cw, pill_y + 27
    role_paths, role_texts = roles_typing(text_x, text_y)

    # Glitch slices of the name; each band jumps on its own beat.
    band_edges = [name_top - 8, name_top + 13, name_top + 27, name_top + 40, NAME_BASE + 16]
    bands_def = "".join(
        f'<clipPath id="b{i}"><rect x="0" y="{a:.1f}" width="{W}" height="{b - a:.1f}"/></clipPath>'
        for i, (a, b) in enumerate(zip(band_edges, band_edges[1:]))
    )
    bands = "".join(
        f'<g clip-path="url(#b{i})"><use xlink:href="#name" href="#name" class="g{i}" fill="url(#chrome)"/></g>'
        for i in range(len(band_edges) - 1)
    )
    jumps = [(-16, 9, 6), (12, -7, -4), (-6, 14, 3), (9, -12, -7)]
    glitch_css = "".join(
        f"@keyframes g{i}{{0%,84%,100%{{transform:none}}85%{{transform:translateX({a}px)}}"
        f"86.5%{{transform:translateX({b}px)}}88%{{transform:none}}93%{{transform:translateX({c}px)}}94%{{transform:none}}}}"
        f".g{i}{{animation:g{i} 5.5s steps(1,end) infinite}}"
        for i, (a, b, c) in enumerate(jumps)
    )

    grid_lines, grid_css = grid()
    sun_cy = HORIZON - 12

    hud_text = "".join(HUD.values()) + "●❯" + "".join(ROLES)
    css = f"""
{font_face(DISPLAY, 600, NAME)}
{font_face(MONO, 500, hud_text)}
.disp{{font-family:'HeroSerif','Lora',Georgia,serif;font-weight:600}}
.mono{{font-family:'TermMono','JetBrains Mono',ui-monospace,Menlo,Consolas,monospace;font-weight:500}}
.role{{font-size:{ROLE_SIZE}px;fill:{C["cloud"]}}}
.hud{{font-size:13px;fill:{C["muted"]};letter-spacing:2px}}
.tw{{animation:tw 4s ease-in-out infinite}}
@keyframes tw{{0%,100%{{opacity:.15}}50%{{opacity:1}}}}
.caret{{animation:blink 1s steps(1,end) infinite}}
@keyframes blink{{0%{{opacity:1}}50%{{opacity:0}}}}
.live{{animation:blink 1.6s steps(1,end) infinite}}
.glow{{animation:pulse 4s ease-in-out infinite}}
@keyframes pulse{{0%,100%{{opacity:.45}}50%{{opacity:.75}}}}
.gm{{animation:gm 5.5s steps(1,end) infinite}}
@keyframes gm{{0%,100%{{transform:translate(-3px,0)}}40%{{transform:translate(-2px,1px)}}85%{{transform:translate(-11px,2px)}}88%{{transform:translate(-3px,0)}}}}
.gc{{animation:gc 5.5s steps(1,end) infinite}}
@keyframes gc{{0%,100%{{transform:translate(3px,0)}}40%{{transform:translate(2px,-1px)}}85%{{transform:translate(12px,-2px)}}88%{{transform:translate(3px,0)}}}}
.shoot{{animation:shoot 9s ease-in infinite;opacity:0}}
@keyframes shoot{{0%,70%{{transform:translate(0,0);opacity:0}}71%{{opacity:1}}80%{{transform:translate(-340px,150px);opacity:0}}100%{{opacity:0}}}}
{grid_css}
{glitch_css}
{scan_css(H)}
"""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Abdalrahman Tukka, software developer">
<title>Abdalrahman Tukka, software developer</title>
<style>{css}</style>
<defs>
  <clipPath id="frame"><rect width="{W}" height="{H}" rx="{RX}"/></clipPath>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{C["dark"]}"/>
    <stop offset=".45" stop-color="#1c1a18"/>
    <stop offset=".78" stop-color="#2e231e"/>
    <stop offset="1" stop-color="#5c3628"/>
  </linearGradient>
  <linearGradient id="skyU" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="{HORIZON}">
    <stop offset="0" stop-color="{C["dark"]}"/>
    <stop offset=".45" stop-color="#1c1a18"/>
    <stop offset=".78" stop-color="#2e231e"/>
    <stop offset="1" stop-color="#5c3628"/>
  </linearGradient>
  <linearGradient id="sunFill" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{C["manilla"]}"/>
    <stop offset=".42" stop-color="#e9a582"/>
    <stop offset=".75" stop-color="{C["orange"]}"/>
    <stop offset="1" stop-color="{C["clay"]}"/>
  </linearGradient>
  <radialGradient id="sunHalo">
    <stop offset=".35" stop-color="{C["orange"]}" stop-opacity=".4"/>
    <stop offset="1" stop-color="{C["orange"]}" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="floor" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#2b211c"/>
    <stop offset="1" stop-color="{C["dark"]}"/>
  </linearGradient>
  <linearGradient id="fadeG" x1="0" y1="{HORIZON}" x2="0" y2="{H}" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="#fff" stop-opacity="0"/>
    <stop offset=".35" stop-color="#fff" stop-opacity=".9"/>
    <stop offset="1" stop-color="#fff"/>
  </linearGradient>
  <mask id="gridFade"><rect y="{HORIZON}" width="{W}" height="{H - HORIZON}" fill="url(#fadeG)"/></mask>
  <linearGradient id="chrome" gradientUnits="userSpaceOnUse" x1="0" y1="{name_top:.0f}" x2="0" y2="{NAME_BASE}">
    <stop offset="0" stop-color="{C["light"]}"/>
    <stop offset=".5" stop-color="{C["light"]}"/>
    <stop offset=".62" stop-color="{C["manilla"]}"/>
    <stop offset="1" stop-color="{C["kraft"]}"/>
  </linearGradient>
  <linearGradient id="edge" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{C["orange"]}"/>
    <stop offset=".5" stop-color="{C["kraft"]}"/>
    <stop offset="1" stop-color="{C["blue"]}"/>
  </linearGradient>
  <filter id="neon" x="-10%" y="-40%" width="120%" height="180%">
    <feGaussianBlur in="SourceAlpha" stdDeviation="9" result="b"/>
    <feFlood flood-color="{C["orange"]}" flood-opacity=".45"/>
    <feComposite in2="b" operator="in" result="g"/>
    <feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="soft"><feGaussianBlur stdDeviation="2.4"/></filter>
  <clipPath id="sunClip"><circle cx="600" cy="{sun_cy}" r="{SUN_R}"/></clipPath>
  <text id="name" class="disp" x="600" y="{NAME_BASE}" text-anchor="middle" font-size="{NAME_SIZE}" letter-spacing="1">{NAME}</text>
  {bands_def}
  {role_paths}
</defs>

<g clip-path="url(#frame)">
  <rect width="{W}" height="{HORIZON}" fill="url(#sky)"/>
  <g>
    {stars(rng)}
  </g>
  <g class="shoot"><line x1="1010" y1="40" x2="1075" y2="12" stroke="url(#edge)" stroke-width="2" stroke-linecap="round"/></g>

  <circle class="glow" cx="600" cy="{sun_cy}" r="{SUN_R * 1.9}" fill="url(#sunHalo)"/>
  <circle cx="600" cy="{sun_cy}" r="{SUN_R}" fill="url(#sunFill)"/>
  <g clip-path="url(#sunClip)">
      {sun_stripes(sun_cy)}
  </g>

  <polygon points="{ridge(rng, -10, 520, HORIZON, 95, 0.55)}" fill="#24211e" stroke="{C["mid"]}" stroke-opacity=".3" stroke-width="1.2"/>
  <polygon points="{ridge(rng, 690, 1210, HORIZON, 105, 0.55)}" fill="#24211e" stroke="{C["mid"]}" stroke-opacity=".3" stroke-width="1.2"/>
  <polygon points="{ridge(rng, -10, 380, HORIZON, 55, 0.6)}" fill="#181715" stroke="{C["orange"]}" stroke-opacity=".55" stroke-width="1.2"/>
  <polygon points="{ridge(rng, 840, 1210, HORIZON, 60, 0.6)}" fill="#181715" stroke="{C["orange"]}" stroke-opacity=".55" stroke-width="1.2"/>

  <rect y="{HORIZON}" width="{W}" height="{H - HORIZON}" fill="url(#floor)"/>
  <g mask="url(#gridFade)" stroke="{C["orange"]}" stroke-width="1.4">
    <g filter="url(#soft)" opacity=".45">{grid_lines}</g>
    <g>{grid_lines}</g>
  </g>
  <line x1="0" y1="{HORIZON}" x2="{W}" y2="{HORIZON}" stroke="{C["orange"]}" stroke-width="2.5" filter="url(#soft)"/>
  <line x1="0" y1="{HORIZON}" x2="{W}" y2="{HORIZON}" stroke="#f2cdb9" stroke-width="1"/>

  <use xlink:href="#name" href="#name" class="gm" fill="{C["orange"]}" opacity=".75"/>
  <use xlink:href="#name" href="#name" class="gc" fill="{C["blue"]}" opacity=".75"/>
  <g filter="url(#neon)">{bands}</g>

  <rect x="{pill_x:.1f}" y="{pill_y}" width="{pill_w:.1f}" height="{pill_h}" rx="{pill_h / 2}" fill="{C["dark"]}" fill-opacity=".94" stroke="url(#edge)" stroke-width="1.4"/>
  <text class="mono" x="{pill_x + 22:.1f}" y="{text_y}" font-size="{ROLE_SIZE}" fill="{C["orange"]}">❯</text>
  {role_texts}

  <text class="mono hud" x="28" y="36">{HUD["tl"]}</text>
  <g text-anchor="end"><text class="mono hud" x="{W - 28}" y="36">{HUD["tr"]}</text></g>
  <circle class="live" cx="{W - 28 - 13 * 0.6 * len(HUD["tr"]) - 2 * len(HUD["tr"]) - 14}" cy="31.5" r="4.5" fill="{C["green"]}"/>
  <text class="mono hud" x="28" y="{H - 22}">{HUD["bl"]}</text>
  <g text-anchor="end"><text class="mono hud" x="{W - 28}" y="{H - 22}">{HUD["br"]}</text></g>
  {scanlines(W, H, RX, 0.05)}
</g>
<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="{RX}" fill="none" stroke="url(#edge)" stroke-width="1.5"/>
</svg>
"""
    assert name_w < W - 160, f"name too wide: {name_w:.0f}px"
    return write("hero.svg", svg)


if __name__ == "__main__":
    build()
