"""Animated terminal: neofetch with a spinning donut.c torus, ls, make, idle prompt.

The whole session is one loop of length TOTAL: lines pop in via per-line CSS
keyframes, typed text grows through SMIL-animated <textPath> paths (glyphs past
the end of a path are not drawn), and the donut flips through pre-rendered
ASCII frames.
"""
import math

from svgkit import C, MONO, MONO_ADVANCE, esc, font_face, pct, scan_css, scanlines, write

W, RX = 900, 14
FS, LH = 16, 25
CW = FS * MONO_ADVANCE
LEFT = 26
BAR = 38
TYPE_DT = 0.075

DONUT_FS, DONUT_LH, DONUT_COLS, DONUT_ROWS, DONUT_FRAMES, DONUT_PERIOD = 12.5, 13.6, 42, 19, 48, 4.0

INFO = [
    [("tukka25", "orange"), ("@", "muted"), ("github", "blue")],
    [("─" * 22, "line")],
    [("Name    ", "orange"), ("Abdalrahman Tukka", "cloud")],
    [("Role    ", "orange"), ("Software Developer", "cloud")],
    [("School  ", "orange"), ("42 Network · ALX SE", "cloud")],
    [("Stack   ", "orange"), ("C · C++ · Python · TS · Kotlin · Swift", "cloud")],
    [("Focus   ", "orange"), ("systems · AI agents · MCP tools", "cloud")],
    [("Shell   ", "orange"), ("minishell ", "cloud"), ("(hand-rolled, in C)", "muted")],
    [("Uptime  ", "orange"), ("shipping code since 2018", "cloud")],
]
PALETTE = [C["dark"], C["clay"], C["orange"], C["kraft"], C["manilla"], C["green"], C["blue"], C["light"]]

PROJECTS = [
    ["cub3d/", "42_minishell/", "ft_webserve/", "ft_traceroute/"],
    ["ft_ping/", "Philos/", "inception/", "IRIS-APP/"],
    ["Graps-MCP/", "Tukkagrind/", "push_swap/", "so_long/"],
]
BAR_LEN = 30


def donut_frames():
    """a1k0n's donut.c, looped: A turns 2pi and B turns pi; the torus is symmetric under the remainder."""
    chars = ".,-~:;=!*#$@"
    aspect = DONUT_LH / (DONUT_FS * MONO_ADVANCE)  # a character cell is taller than wide
    raw = []
    for f in range(DONUT_FRAMES):
        a, b = 2 * math.pi * f / DONUT_FRAMES, math.pi * f / DONUT_FRAMES
        e, g, m, n = math.sin(a), math.cos(a), math.cos(b), math.sin(b)
        pts = []
        j = 0.0
        while j < 2 * math.pi:
            d, fj = math.cos(j), math.sin(j)
            h = d + 2
            i = 0.0
            while i < 2 * math.pi:
                c, l = math.sin(i), math.cos(i)
                big_d = 1 / (c * h * e + fj * g + 5)
                t = c * h * g - fj * e
                x, y = big_d * (l * h * m - t * n), big_d * (l * h * n + t * m)
                lum = 8 * ((fj * e - c * d * g) * m - c * d * e - fj * g - l * d * n)
                pts.append((x, y, big_d, lum))
                i += 0.025
            j += 0.08
        raw.append(pts)
    ext = max(max(abs(x) for x, _, _, _ in pts) for pts in raw)
    kx = (DONUT_COLS / 2 - 1) / ext
    ky = kx / aspect
    frames = []
    for pts in raw:
        out = [[" "] * DONUT_COLS for _ in range(DONUT_ROWS)]
        zbuf = [[0.0] * DONUT_COLS for _ in range(DONUT_ROWS)]
        for x, y, ooz, lum in pts:
            xp, yp = int(DONUT_COLS / 2 + kx * x), int(DONUT_ROWS / 2 + ky * y)
            if 0 <= xp < DONUT_COLS and 0 <= yp < DONUT_ROWS and ooz > zbuf[yp][xp]:
                zbuf[yp][xp] = ooz
                out[yp][xp] = chars[max(0, min(11, int(lum)))]
        frames.append(["".join(r).rstrip() for r in out])
    return frames


def spans(parts):
    return "".join(f'<tspan fill="{C[col]}">{esc(txt)}</tspan>' for txt, col in parts)


class Session:
    """Accumulates timed elements; times are resolved to keyframes once TOTAL is known."""

    def __init__(self):
        self.t = 0.6
        self.y = BAR + 36
        self.items = []  # (appear_time, svg)
        self.paths = []  # (id, x, y, [(time, nchars)])
        self.cursor = [(0.0, LEFT, self.y)]

    def prompt(self, cmd):
        y = self.y
        self.items.append((self.t, f'<text class="t" x="{LEFT}" y="{y}">{spans([("❯", "orange"), (" ~ ", "blue")])}</text>'))
        x0 = LEFT + 4 * CW
        self.cursor.append((self.t, x0, y))
        start = self.t + 0.4
        steps = [(start + k * TYPE_DT, k) for k in range(1, len(cmd) + 1)]
        self.cursor += [(t, x0 + n * CW, y) for t, n in steps]
        self.typed(cmd, x0, y, steps, "light")
        self.t = steps[-1][0] + 0.35
        self.y += LH
        self.cursor.append((self.t, LEFT, self.y))

    def typed(self, text, x0, y, steps, col):
        pid = f"p{len(self.paths)}"
        self.paths.append((pid, x0, y, [(0.0, 0)] + steps))
        self.items.append((0.0, f'<text class="t" style="fill:{C[col]}"><textPath xlink:href="#{pid}" href="#{pid}">{esc(text)}</textPath></text>'))

    def line(self, svg, dt=0.05, advance=LH):
        self.items.append((self.t, svg))
        self.t += dt
        self.y += advance
        self.cursor.append((self.t, LEFT, self.y))

    def pause(self, dt):
        self.t += dt


def build():
    s = Session()

    s.prompt("neofetch")
    top = s.y - 16
    frames = donut_frames()
    donut = []
    for i, rows in enumerate(frames):
        body = "".join(
            f'<text x="{LEFT}" y="{top + 10 + r * DONUT_LH:.1f}" xml:space="preserve">{esc(row)}</text>'
            for r, row in enumerate(rows)
            if row
        )
        donut.append(f'<g class="df" style="animation-delay:-{(DONUT_FRAMES - i) % DONUT_FRAMES * DONUT_PERIOD / DONUT_FRAMES:.3f}s">{body}</g>')
    s.items.append((s.t, f'<g class="donut" fill="url(#donutG)">{"".join(donut)}</g>'))
    info_x = LEFT + DONUT_COLS * DONUT_FS * MONO_ADVANCE + 26
    for i, parts in enumerate(INFO):
        s.items.append((s.t + 0.05 * i, f'<text class="t" x="{info_x:.1f}" y="{top + 16 + i * 26}">{spans(parts)}</text>'))
    blocks = "".join(
        f'<rect x="{info_x + i * 28:.1f}" y="{top + 16 + len(INFO) * 26 - 8}" width="26" height="14" rx="2" fill="{col}"/>'
        for i, col in enumerate(PALETTE)
    )
    s.items.append((s.t + 0.05 * len(INFO), f"<g>{blocks}</g>"))
    s.t += 0.05 * len(INFO) + 0.9
    s.y = top + max(DONUT_ROWS * DONUT_LH, (len(INFO) + 1) * 26) + 30
    s.cursor.append((s.t, LEFT, s.y))

    s.prompt("ls ~/projects")
    for row in PROJECTS:
        cells = "".join(f'<tspan x="{LEFT + c * 19 * CW:.1f}">{esc(name)}</tspan>' for c, name in enumerate(row))
        s.line(f'<text class="t dir" y="{s.y}">{cells}</text>', dt=0.07)
    s.pause(0.8)
    s.y += 8

    s.prompt("make it_happen")
    y = s.y
    label = "building "
    s.line(f'<text class="t" x="{LEFT}" y="{y}">{spans([("▸ ", "orange"), (label, "muted"), ("[", "muted")])}</text>', dt=0.25, advance=0)
    x0 = LEFT + (2 + len(label) + 1) * CW
    steps = [(s.t + k * 0.045, k) for k in range(1, BAR_LEN + 1)]
    s.typed("█" * BAR_LEN, x0, y, steps, "orange")
    s.cursor += [(t, x0 + n * CW, y) for t, n in steps]
    s.t = steps[-1][0] + 0.15
    s.line(f'<text class="t" x="{x0 + BAR_LEN * CW:.1f}" y="{y}">{spans([("] ", "muted"), ("100%", "green"), ("  ● shipped", "green")])}</text>', dt=0.9)
    s.y += 8

    idle_y = s.y
    s.items.append((s.t, f'<text class="t" x="{LEFT}" y="{idle_y}">{spans([("❯", "orange"), (" ~ ", "blue")])}</text>'))
    s.cursor.append((s.t, LEFT + 4 * CW, idle_y))
    hold, fade = 5.0, 0.6
    total = s.t + hold + fade
    H = idle_y + 34

    # --- assemble -----------------------------------------------------------------
    css, body = [], []
    for i, (t, svg) in enumerate(s.items):
        if t <= 0:
            body.append(svg)
            continue
        css.append(f"@keyframes a{i}{{0%,{pct(t - 0.01, total)}{{opacity:0}}{pct(t, total)},100%{{opacity:1}}}}.a{i}{{animation:a{i} {total:.2f}s linear infinite}}")
        body.append(f'<g class="a{i}" opacity="0">{svg}</g>')

    path_defs = []
    for pid, x0, y, ev in s.paths:
        kt = ";".join(f"{t / total:.5f}" for t, _ in ev)
        vals = ";".join(f"M{x0:.1f} {y} h{n * CW:.1f}" for _, n in ev)
        path_defs.append(
            f'<path id="{pid}" d="M{x0:.1f} {y} h0"><animate attributeName="d" dur="{total:.2f}s" '
            f'repeatCount="indefinite" calcMode="discrete" keyTimes="{kt}" values="{vals}"/></path>'
        )

    # SMIL rejects the whole animation on duplicate keyTimes; keep the last event per instant.
    cur = sorted({round(t, 4): (t, x, y) for t, x, y in sorted(s.cursor, key=lambda e: e[0])}.values())
    kt = ";".join(f"{t / total:.5f}" for t, _, _ in cur)
    cx = ";".join(f"{x + 1:.1f}" for _, x, _ in cur)
    cy = ";".join(f"{y - 15}" for _, _, y in cur)
    cursor = (
        f'<rect class="cur" width="{CW - 1:.1f}" height="19" fill="{C["cloud"]}" opacity=".8">'
        f'<animate attributeName="x" dur="{total:.2f}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{kt}" values="{cx}"/>'
        f'<animate attributeName="y" dur="{total:.2f}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{kt}" values="{cy}"/></rect>'
    )

    title = f"tukka@42 : ~ — zsh — {W // 10}x{H // 20}"
    text_used = "".join(body) + title + "❯~█▸●─·"
    donut_step = 100 / DONUT_FRAMES
    style = f"""
{font_face(MONO, 500, text_used)}
text{{font-family:'TermMono','JetBrains Mono',ui-monospace,Menlo,Consolas,monospace;font-weight:500}}
.t{{font-size:{FS}px;fill:{C["cloud"]}}}
.dir{{fill:{C["blue"]}}}
.title{{font-size:13px;fill:{C["muted"]};letter-spacing:1px}}
.donut text{{font-size:{DONUT_FS}px}}
.df{{visibility:hidden;animation:df {DONUT_PERIOD}s steps(1,end) infinite}}
@keyframes df{{0%{{visibility:visible}}{donut_step:.3f}%,100%{{visibility:hidden}}}}
.cur{{animation:blink 1.05s steps(1,end) infinite}}
@keyframes blink{{0%{{opacity:.9}}50%{{opacity:0}}}}
.screen{{animation:screen {total:.2f}s linear infinite}}
@keyframes screen{{0%,{pct(total - fade, total)}{{opacity:1}}100%{{opacity:0}}}}
{"".join(css)}
{scan_css(H)}
"""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" xml:space="preserve" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Terminal session: neofetch, ls ~/projects, make it_happen">
<title>tukka@42 terminal</title>
<style>{style}</style>
<defs>
  <clipPath id="win"><rect width="{W}" height="{H}" rx="{RX}"/></clipPath>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{C["surface"]}"/>
    <stop offset="1" stop-color="{C["dark"]}"/>
  </linearGradient>
  <linearGradient id="edge" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{C["orange"]}"/>
    <stop offset=".5" stop-color="{C["kraft"]}"/>
    <stop offset="1" stop-color="{C["blue"]}"/>
  </linearGradient>
  <linearGradient id="donutG" gradientUnits="userSpaceOnUse" x1="{LEFT}" y1="{BAR + 40}" x2="{LEFT + 320}" y2="{BAR + 300}">
    <stop offset="0" stop-color="{C["manilla"]}"/>
    <stop offset=".5" stop-color="{C["orange"]}"/>
    <stop offset="1" stop-color="{C["clay"]}"/>
  </linearGradient>
  <radialGradient id="vignette" cx=".5" cy=".5" r=".75">
    <stop offset=".6" stop-color="#000" stop-opacity="0"/>
    <stop offset="1" stop-color="#000" stop-opacity=".45"/>
  </radialGradient>
  <filter id="bloom" x="-5%" y="-5%" width="110%" height="110%">
    <feGaussianBlur stdDeviation="1.1" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  {"".join(path_defs)}
</defs>
<g clip-path="url(#win)">
  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  <rect width="{W}" height="{BAR}" fill="{C["raised"]}"/>
  <line x1="0" y1="{BAR}" x2="{W}" y2="{BAR}" stroke="{C["line"]}"/>
  <circle cx="22" cy="{BAR / 2}" r="6.5" fill="{C["orange"]}"/>
  <circle cx="44" cy="{BAR / 2}" r="6.5" fill="{C["kraft"]}"/>
  <circle cx="66" cy="{BAR / 2}" r="6.5" fill="{C["green"]}"/>
  <text class="title" x="{W / 2}" y="{BAR / 2 + 4.5}" text-anchor="middle">{title}</text>
  <g class="screen" filter="url(#bloom)">
    {"".join(body)}
    {cursor}
  </g>
  <rect width="{W}" height="{H}" fill="url(#vignette)"/>
  {scanlines(W, H, RX, 0.05)}
</g>
<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="{RX}" fill="none" stroke="url(#edge)" stroke-width="1.5"/>
</svg>
"""
    return write("terminal.svg", svg)


if __name__ == "__main__":
    build()
