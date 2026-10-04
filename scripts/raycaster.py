"""cub3d.svg: a Wolfenstein-style raycaster rendered into a looping SVG.

Rays are cast per column with DDA (as in cub3d); consecutive columns that hit the
same wall plane are merged into one exact trapezoid, so each frame is a handful
of vector faces instead of hundreds of strips. The map has 4-fold rotational
symmetry and the camera walks a rounded square, so one quarter of the loop is
rendered and replayed while the minimap dot travels the full square.
"""
import math

from svgkit import C, MONO, esc, font_face, scan_css, scanlines, write

W, H, RX = 960, 440, 18
N = 18
RAYS = 320
FOV_PLANE = math.tan(math.radians(35))
FOCAL = W / (2 * FOV_PLANE)
NEAR, FAR = 0.3, 13.0
FRAMES, PERIOD = 96, 8.0  # one quarter of the loop
SIDE, TURN_R = 9.0, 1.5  # straight run and corner radius of the camera path
QUARTER = SIDE + TURN_R * math.pi / 2

ALCOVES = {5, 8, 9, 12}
WINDOWS = {7, 10}


def build_map():
    base = {(0, c) for c in range(N)}
    base |= {(1, c) for c in range(N) if c not in ALCOVES}
    base |= {(4, c) for c in range(4, 14) if c not in WINDOWS}
    base |= {(6, 6), (8, 8), (8, 9), (9, 8), (9, 9)}
    walls = set()
    for cell in base:
        for _ in range(4):
            walls.add(cell)
            cell = (cell[1], N - 1 - cell[0])
    return walls


WALLS = build_map()


def solid(row, col):
    return (row, col) in WALLS


def camera(s):
    """Pose at arc length s along one quarter of the loop."""
    if s < SIDE:
        x, y, heading = 4.5 + s, 3.0, 0.0
    else:
        a = -math.pi / 2 + (s - SIDE) / TURN_R
        x, y, heading = 13.5 + TURN_R * math.cos(a), 4.5 + TURN_R * math.sin(a), a + math.pi / 2
    u = s / QUARTER
    heading += 0.07 * math.sin(2 * math.pi * u)
    eye = 0.5 + 0.012 * math.sin(2 * math.pi * 6 * u)
    return x, y, heading, eye


def cast(px, py, rx, ry):
    """DDA. Returns (key, depth) where key identifies the wall plane hit."""
    mx, my = int(px), int(py)
    ddx = abs(1 / rx) if rx else 1e30
    ddy = abs(1 / ry) if ry else 1e30
    sx, sy = (1 if rx > 0 else -1), (1 if ry > 0 else -1)
    dx = (mx + 1 - px) * ddx if rx > 0 else (px - mx) * ddx
    dy = (my + 1 - py) * ddy if ry > 0 else (py - my) * ddy
    while True:
        if dx < dy:
            dx += ddx
            mx += sx
            side = 0
        else:
            dy += ddy
            my += sy
            side = 1
        if solid(my, mx):
            if side == 0:
                return (0, mx if sx > 0 else mx + 1, sx), dx - ddx
            return (1, my if sy > 0 else my + 1, sy), dy - ddy


def mix(a, b, t):
    pa = [int(a[i : i + 2], 16) for i in (1, 3, 5)]
    pb = [int(b[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{min(255, round((x + (y - x) * t) / 4) * 4):02x}" for x, y in zip(pa, pb))


class Frame:
    def __init__(self, s, colors):
        self.px, self.py, heading, self.eye = camera(s)
        self.dx, self.dy = math.cos(heading), math.sin(heading)
        self.plx, self.ply = -self.dy * FOV_PLANE, self.dx * FOV_PLANE
        self.colors = colors

    def ray(self, sx):
        cam = 2 * sx / W - 1
        return self.dx + self.plx * cam, self.dy + self.ply * cam

    def project(self, wx, wy, z):
        rx, ry = wx - self.px, wy - self.py
        depth = rx * self.dx + ry * self.dy
        lateral = (rx * self.plx + ry * self.ply) / FOV_PLANE
        return W / 2 + FOCAL * lateral / depth, H / 2 - FOCAL * (z - self.eye) / depth, depth

    def plane_depth(self, key, sx, fallback):
        rx, ry = self.ray(sx)
        axis, c, _ = key
        t = (c - self.px) / rx if axis == 0 and rx else (c - self.py) / ry if axis == 1 and ry else -1
        return t if 0 < t < 60 else fallback

    def wall_y(self, t):
        return H / 2 - FOCAL * (1 - self.eye) / t, H / 2 + FOCAL * self.eye / t

    def corners(self, key, a, b):
        """World corner points of the face run on `key` between plane coords a..b."""
        axis, c, step = key
        lo, hi = sorted((a, b))
        wall_line, free_line = (c, c - 1) if step > 0 else (c - 1, c)

        def face(k):
            if axis == 0:
                return solid(k, wall_line) and not solid(k, free_line)
            return solid(wall_line, k) and not solid(free_line, k)

        out = []
        for k in range(math.floor(lo - 0.02), math.ceil(hi + 0.02) + 1):
            if lo - 0.02 <= k <= hi + 0.02 and face(k - 1) != face(k):
                out.append((c, k) if axis == 0 else (k, c))
        return out

    def walls(self):
        hits = [cast(self.px, self.py, *self.ray((i + 0.5) * W / RAYS)) for i in range(RAYS)]
        groups, start = [], 0
        for i in range(1, RAYS + 1):
            if i == RAYS or hits[i][0] != hits[start][0]:
                groups.append((start, i - 1))
                start = i
        faces, edges, seams, strips = [], {0: [], 1: [], 2: []}, [], []
        for a, b in groups:
            key = hits[a][0]
            xl, xr = a * W / RAYS, (b + 1) * W / RAYS
            tl = self.plane_depth(key, xl, hits[a][1])
            tr = self.plane_depth(key, xr, hits[b][1])
            (tl_top, tl_bot), (tr_top, tr_bot) = self.wall_y(tl), self.wall_y(tr)
            depth = (tl + tr) / 2

            axis, c, step = key
            nx, ny = (-step, 0) if axis == 0 else (0, -step)
            rx, ry = self.ray((xl + xr) / 2)
            norm = math.hypot(rx, ry)
            facing = abs(nx * rx + ny * ry) / norm
            fog = min(1.0, max(0.0, (depth - 0.8) / (FAR - 2)))
            col = mix(mix("#150630", "#3d147c", 0.25 + 0.75 * facing), "#140430", fog)
            cls = self.colors.setdefault(col, f"c{len(self.colors)}")
            faces.append(
                f'<path class="{cls}" d="M{xl:.0f} {tl_top:.0f}L{xr:.0f} {tr_top:.0f}L{xr:.0f} {tr_bot:.0f}L{xl:.0f} {tl_bot:.0f}Z"/>'
            )

            bucket = 0 if depth < 3.5 else 1 if depth < 7 else 2
            edges[bucket].append(f"M{xl:.0f} {tl_top:.0f}L{xr:.0f} {tr_top:.0f}M{xl:.0f} {tl_bot:.0f}L{xr:.0f} {tr_bot:.0f}")
            rxl, ryl = self.ray(xl)
            rxr, ryr = self.ray(xr)
            if axis == 0:
                wa, wb = self.py + tl * ryl, self.py + tr * ryr
            else:
                wa, wb = self.px + tl * rxl, self.px + tr * rxr
            sl, sr = H / 2 - FOCAL * (0.8 - self.eye) / tl, H / 2 - FOCAL * (0.8 - self.eye) / tr
            strips.append(f"M{xl:.0f} {sl:.0f}L{xr:.0f} {sr:.0f}")
            corners = self.corners(key, wa, wb)
            for k in range(math.ceil(min(wa, wb) + 0.05), math.floor(max(wa, wb) - 0.05) + 1):
                p = (c, k) if axis == 0 else (k, c)
                if p in corners:
                    continue
                sx, top, d = self.project(*p, 1.0)
                if d > NEAR:
                    seams.append(f"M{sx:.0f} {top:.0f}V{self.project(*p, 0.0)[1]:.0f}")
            for wx, wy in corners:
                sx, top, d = self.project(wx, wy, 1.0)
                if d > NEAR and xl - 2 <= sx <= xr + 2:
                    _, bot, _ = self.project(wx, wy, 0.0)
                    edges[bucket].append(f"M{sx:.0f} {top:.0f}V{bot:.0f}")
        return "".join(faces), {k: "".join(v) for k, v in edges.items()}, "".join(seams), "".join(strips)

    def grid(self):
        floor, ceil = [], []
        for k in range(N + 1):
            for a, b in (((k, 0), (k, N)), ((0, k), (N, k))):
                seg = self.clip(a, b)
                if not seg:
                    continue
                (ax, ay), (bx, by) = seg
                for z, out in ((0.0, floor), (1.0, ceil)):
                    x1, y1, _ = self.project(ax, ay, z)
                    x2, y2, _ = self.project(bx, by, z)
                    out.append(f"M{x1:.0f} {y1:.0f}L{x2:.0f} {y2:.0f}")
        return "".join(floor), "".join(ceil)

    def clip(self, a, b):
        da = (a[0] - self.px) * self.dx + (a[1] - self.py) * self.dy
        db = (b[0] - self.px) * self.dx + (b[1] - self.py) * self.dy
        t0, t1 = 0.0, 1.0
        for bound, sign in ((NEAR, 1), (FAR, -1)):
            fa, fb = sign * (da - bound), sign * (db - bound)
            if fa < 0 and fb < 0:
                return None
            if fa < 0:
                t0 = max(t0, fa / (fa - fb))
            elif fb < 0:
                t1 = min(t1, fa / (fa - fb))
        if t0 >= t1:
            return None
        lerp = lambda t: (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        return lerp(t0), lerp(t1)


def minimap(x0, y0, cell):
    walls = "".join(f"M{x0 + c * cell} {y0 + r * cell}h{cell}v{cell}h-{cell}z" for r, c in sorted(WALLS))
    s = lambda v: v * cell
    loop = (
        f"M{x0 + s(4.5)} {y0 + s(3)}H{x0 + s(13.5)}A{s(1.5)} {s(1.5)} 0 0 1 {x0 + s(15)} {y0 + s(4.5)}"
        f"V{y0 + s(13.5)}A{s(1.5)} {s(1.5)} 0 0 1 {x0 + s(13.5)} {y0 + s(15)}"
        f"H{x0 + s(4.5)}A{s(1.5)} {s(1.5)} 0 0 1 {x0 + s(3)} {y0 + s(13.5)}"
        f"V{y0 + s(4.5)}A{s(1.5)} {s(1.5)} 0 0 1 {x0 + s(4.5)} {y0 + s(3)}Z"
    )
    size = N * cell
    return f"""
  <g>
    <rect x="{x0 - 8}" y="{y0 - 8}" width="{size + 16}" height="{size + 16}" rx="8" fill="{C["night"]}" fill-opacity=".82" stroke="{C["violet"]}" stroke-opacity=".7"/>
    <path d="{walls}" fill="#3a1470" stroke="{C["violet"]}" stroke-width=".4"/>
    <path d="{loop}" fill="none" stroke="{C["cyan"]}" stroke-opacity=".25" stroke-dasharray="2 3"/>
    <g>
      <path d="M0 0L{cell * 3.4:.1f} {-cell * 2.3:.1f}A{cell * 4:.1f} {cell * 4:.1f} 0 0 1 {cell * 3.4:.1f} {cell * 2.3:.1f}Z" fill="{C["cyan"]}" fill-opacity=".28"/>
      <circle r="{cell * 0.55:.1f}" fill="{C["magenta"]}"/>
      <animateMotion dur="{4 * PERIOD}s" repeatCount="indefinite" rotate="auto" path="{loop}"/>
    </g>
  </g>"""


def build():
    colors = {}
    grid_frames, wall_frames = [], []
    for i in range(FRAMES):
        fr = Frame(QUARTER * i / FRAMES, colors)
        floor, ceil = fr.grid()
        faces, edges, seams, strips = fr.walls()
        cls = f"f f{i}"
        grid_frames.append(f'<g class="{cls}"><path class="fl" d="{floor}"/><path class="cl" d="{ceil}"/></g>')
        wall_frames.append(
            f'<g class="{cls}">{faces}<path class="sm" d="{seams}"/><path class="ls" d="{strips}"/><path class="e0" d="{edges[0]}"/><path class="e1" d="{edges[1]}"/><path class="e2" d="{edges[2]}"/></g>'
        )

    step = 100 / FRAMES
    delays = "".join(f".f{i}{{animation-delay:-{(FRAMES - i) % FRAMES * PERIOD / FRAMES:.4f}s}}" for i in range(FRAMES))
    fills = "".join(f".{cls}{{fill:{col}}}" for col, cls in colors.items())
    hud = {
        "tl": "CUB3D.SVG  //  RAYCASTING IN PURE SVG",
        "bl": f"RAYS {RAYS}   FPS {FRAMES // PERIOD:.0f}   JS 0",
        "br": "FLOOR 42   SCORE 0x2A",
    }
    mm_cell = 6
    css = f"""
{font_face(MONO, 600, "".join(hud.values()) + "0123456789")}
.hud{{font-family:'TermMono','JetBrains Mono',ui-monospace,Menlo,monospace;font-weight:600;font-size:13px;letter-spacing:2px;fill:{C["lavender"]}}}
.f{{visibility:hidden;animation:fr {PERIOD}s steps(1,end) infinite}}
@keyframes fr{{0%{{visibility:visible}}{step:.4f}%,100%{{visibility:hidden}}}}
{delays}
{fills}
.fl{{fill:none;stroke:{C["magenta"]};stroke-width:1.3}}
.cl{{fill:none;stroke:{C["violet"]};stroke-width:1;stroke-opacity:.55}}
.sm{{fill:none;stroke:{C["violet"]};stroke-width:1;stroke-opacity:.5}}
.ls{{fill:none;stroke:{C["cyan"]};stroke-width:1.2;stroke-opacity:.35}}
.e0,.e1,.e2{{fill:none;stroke:url(#edgeV);stroke-linecap:round}}
.e0{{stroke-width:2.2}}.e1{{stroke-width:1.6;stroke-opacity:.7}}.e2{{stroke-width:1.1;stroke-opacity:.4}}
.blink{{animation:blink 1.4s steps(1,end) infinite}}
@keyframes blink{{0%{{opacity:1}}50%{{opacity:.15}}}}
{scan_css(H)}
"""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="A raycaster walking through a neon maze, rendered as an animated SVG">
<title>cub3d.svg: a raycaster in pure SVG</title>
<style>{css}</style>
<defs>
  <clipPath id="frame"><rect width="{W}" height="{H}" rx="{RX}"/></clipPath>
  <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#05010f"/>
    <stop offset=".5" stop-color="#1e0640"/>
    <stop offset="1" stop-color="#0b0221"/>
  </linearGradient>
  <linearGradient id="edgeV" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="{H}">
    <stop offset="0" stop-color="{C["cyan"]}"/>
    <stop offset=".5" stop-color="{C["violet"]}"/>
    <stop offset="1" stop-color="{C["magenta"]}"/>
  </linearGradient>
  <linearGradient id="fogG" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="0" y2="{H}">
    <stop offset="0" stop-color="#fff"/>
    <stop offset=".42" stop-color="#fff" stop-opacity=".15"/>
    <stop offset=".5" stop-color="#fff" stop-opacity="0"/>
    <stop offset=".58" stop-color="#fff" stop-opacity=".15"/>
    <stop offset="1" stop-color="#fff"/>
  </linearGradient>
  <mask id="fog"><rect width="{W}" height="{H}" fill="url(#fogG)"/></mask>
  <radialGradient id="vig" cx=".5" cy=".5" r=".7">
    <stop offset=".55" stop-color="#000" stop-opacity="0"/>
    <stop offset="1" stop-color="#000" stop-opacity=".6"/>
  </radialGradient>
  <linearGradient id="edge" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{C["cyan"]}"/>
    <stop offset=".5" stop-color="{C["violet"]}"/>
    <stop offset="1" stop-color="{C["magenta"]}"/>
  </linearGradient>
  <filter id="soft"><feGaussianBlur stdDeviation="1.8"/></filter>
</defs>
<g clip-path="url(#frame)">
  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  <line x1="0" y1="{H / 2}" x2="{W}" y2="{H / 2}" stroke="{C["magenta"]}" stroke-width="3" opacity=".6" filter="url(#soft)"/>
  <g mask="url(#fog)">{"".join(grid_frames)}</g>
  <g>{"".join(wall_frames)}</g>
  <rect width="{W}" height="{H}" fill="url(#vig)"/>
  <g stroke="{C["cyan"]}" stroke-opacity=".55" stroke-width="1.5">
    <line x1="{W / 2 - 9}" y1="{H / 2}" x2="{W / 2 - 3}" y2="{H / 2}"/><line x1="{W / 2 + 3}" y1="{H / 2}" x2="{W / 2 + 9}" y2="{H / 2}"/>
    <line x1="{W / 2}" y1="{H / 2 - 9}" x2="{W / 2}" y2="{H / 2 - 3}"/><line x1="{W / 2}" y1="{H / 2 + 3}" x2="{W / 2}" y2="{H / 2 + 9}"/>
  </g>
  {minimap(W - N * mm_cell - 26, 26, mm_cell)}
  <circle class="blink" cx="30" cy="31" r="4.5" fill="{C["magenta"]}"/>
  <text class="hud" x="44" y="36">{esc(hud["tl"])}</text>
  <text class="hud" x="24" y="{H - 22}">{esc(hud["bl"])}</text>
  <text class="hud" x="{W - 24}" y="{H - 22}" text-anchor="end">{esc(hud["br"])}</text>
  {scanlines(W, H, RX, 0.12)}
</g>
<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="{RX}" fill="none" stroke="url(#edge)" stroke-width="1.5"/>
</svg>
"""
    return write("raycaster.svg", svg)


if __name__ == "__main__":
    build()
