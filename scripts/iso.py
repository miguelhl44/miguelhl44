"""The drawing kernel every figure on the page shares.

An orthographic 2:1 camera, rounded solids drawn as one bright silhouette
and one dim crease, and plates filled with the ground colour and painted
back to front, so a nearer solid simply covers a farther one. The projection
and solid maths are adapted from an MIT-licensed isometric drawing library;
see scripts/NOTICE.

A README has no JavaScript, so every figure plays a loop: the motion is CSS
keyframes inside the SVG, which GitHub animates when the file is loaded
through <img>. Because the projection is linear, moving a part in the world
is a plain translate on screen, so most of the motion is translates, stroke
colour and dash offsets.

The rules every figure keeps:
  * the stroke is the only highlight, and one thing is bright at a time;
  * rest is a composition, never a flat grid;
  * no words inside the drawing; names go to the read-out in the corner;
  * one green signal (the Holmgaard "skov" accent) marks what is live: a
    packet, a ready node, a running agent. Nothing else is coloured.
"""
import base64
import io
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TTF = os.path.join(HERE, "fonts", "JetBrainsMono-Regular.ttf")

# ---------------------------------------------------------------- palette

THEMES = {
    "dark": dict(
        bg="#0d1117", card="#0a0d12", border="#1f242c",
        plate="#0a0d12", hi="#e6edf3", edge="#6e7681", mid="#3a414b", lo="#21262d",
        text="#8b949e", faint="#484f58", sig="#46d394", sig_lo="#1d4d38",
    ),
    "light": dict(
        bg="#ffffff", card="#fbfbfa", border="#e4e6e2",
        plate="#fbfbfa", hi="#1f2328", edge="#8c959f", mid="#c4c9ce", lo="#e3e6e8",
        text="#59636e", faint="#a5adb5", sig="#12805c", sig_lo="#bfe3d3",
    ),
}

HOUSE = "cubic-bezier(.32,.72,0,1)"     # a discrete change: long ease-out
GLIDE = "cubic-bezier(.65,0,.35,1)"     # travel between two rests
SNAP = "cubic-bezier(.2,.9,.3,1.25)"    # a small overshoot, for things landing
LINEAR = "linear"

# ---------------------------------------------------------------- maths

def r2(n):
    v = round(n * 100) / 100
    return ("%g" % v) if abs(v) < 1e6 else str(v)


def clamp(v, a, b):
    return max(a, min(b, v))


def lerp(a, b, t):
    return a + (b - a) * t


def poly(pts):
    return "M" + "L".join(f"{r2(p[0])} {r2(p[1])}" for p in pts) + "Z"


def open_(pts):
    return "" if len(pts) < 2 else "M" + "L".join(f"{r2(p[0])} {r2(p[1])}" for p in pts)


def seg(a, b):
    return f"M{r2(a[0])} {r2(a[1])}L{r2(b[0])} {r2(b[1])}"


class Cam:
    """An orthographic camera: azimuth in degrees, k = sin(elevation), scale S."""

    def __init__(self, az=45, k=0.5, S=1.0):
        self.az = math.radians(az)
        self.k = k
        self.S = S
        self.ox = 0.0
        self.oy = 0.0

    def P(self, x, y, z=0.0):
        c, s, zf = math.cos(self.az), math.sin(self.az), math.sqrt(1 - self.k * self.k)
        X, Y = x * c - y * s, x * s + y * c
        return (self.ox + self.S * X, self.oy + self.S * (Y * self.k - z * zf))

    def d(self, dx, dy, dz=0.0):
        """A world displacement as a screen displacement: what a translate needs."""
        a, b = self.P(0, 0, 0), self.P(dx, dy, dz)
        return (b[0] - a[0], b[1] - a[1])

    def fit(self, pts, cx, cy):
        self.ox = self.oy = 0
        q = [self.P(*p) for p in pts]
        xs, ys = [p[0] for p in q], [p[1] for p in q]
        self.ox = cx - (min(xs) + max(xs)) / 2
        self.oy = cy - (min(ys) + max(ys)) / 2

    def autoscale(self, pts, w, h, cx, cy):
        """The largest scale whose box of pts fits w x h, centred on (cx, cy)."""
        self.S = 1
        self.ox = self.oy = 0
        q = [self.P(*p) for p in pts]
        xs, ys = [p[0] for p in q], [p[1] for p in q]
        self.S = min(w / (max(xs) - min(xs)), h / (max(ys) - min(ys)))
        self.fit(pts, cx, cy)
        return self

    def front(self, q):
        s, c = math.sin(self.az), math.cos(self.az)
        return q[2] * s + q[3] * c >= -1e-6


def rrect(u0, v0, u1, v1, r, n=4):
    """A rounded rectangle, sampled: (u, v, nu, nv) with the outward normal."""
    r = max(0, min(r, (u1 - u0) / 2, (v1 - v0) / 2))
    out = []
    for cu, cv, a0 in ((u1 - r, v1 - r, 0), (u0 + r, v1 - r, 90), (u0 + r, v0 + r, 180), (u1 - r, v0 + r, 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            ca, sa = math.cos(a), math.sin(a)
            out.append((cu + r * ca, cv + r * sa, ca, sa))
    return out


def circ(R, n=48, cx=0.0, cy=0.0):
    out = []
    for k in range(n):
        a = k / n * math.tau
        out.append((cx + R * math.cos(a), cy + R * math.sin(a), math.cos(a), math.sin(a)))
    return out


def hull(pts):
    pts = sorted(set((round(p[0], 3), round(p[1], 3)) for p in pts))
    if len(pts) < 3:
        return pts

    def x(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lo, up = [], []
    for p in pts:
        while len(lo) > 1 and x(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) > 1 and x(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def ring_at(C, ring, z):
    return [C.P(q[0], q[1], z) for q in ring]


def run(ring, keep):
    """The one cyclic run of samples that pass keep, in ring order."""
    n = len(ring)
    s = -1
    for i in range(n):
        if keep(ring[i]) and not keep(ring[(i - 1) % n]):
            s = i
            break
    if s < 0:
        return list(ring) if keep(ring[0]) else []
    out = []
    k = 0
    while k < n and keep(ring[(s + k) % n]):
        out.append(ring[(s + k) % n])
        k += 1
    return out


def rings(x0, y0, x1, y1, r, b):
    return rrect(x0, y0, x1, y1, r), rrect(x0 + b, y0 + b, x1 - b, y1 - b, max(0.3, r - b))


def prism(C, ring, inner, z0, z1):
    """A solid standing from z0 to z1: its silhouette, and the one crease on its lid."""
    sil = poly(hull(ring_at(C, ring, z1) + ring_at(C, ring, z0)))
    crease = open_(ring_at(C, run(inner, C.front), z1)) if inner else ""
    return sil, crease


def lid(C, ring, z):
    return poly(ring_at(C, ring, z))


def box(C, x0, y0, x1, y1, z0, z1, r=3.0, b=1.4):
    ring, inner = rings(x0, y0, x1, y1, r, b)
    return prism(C, ring, inner, z0, z1)


def affine_to_plane(C, ox, oy, z, ux, uy, vx, vy, scale=1.0):
    """An SVG matrix that lays a 2D drawing (x right, y down) on a world plane at height z.

    The drawing's x axis runs along world (ux, uy) and its y axis along (vx, vy).
    """
    o = C.P(ox, oy, z)
    a = C.P(ox + ux * scale, oy + uy * scale, z)
    b = C.P(ox + vx * scale, oy + vy * scale, z)
    return f"matrix({r2(a[0]-o[0])} {r2(a[1]-o[1])} {r2(b[0]-o[0])} {r2(b[1]-o[1])} {r2(o[0])} {r2(o[1])})"


def affine_upright(C, ox, oy, z, ux, uy, scale=1.0):
    """An SVG matrix for a drawing standing up on a vertical plane: x along (ux, uy), y down."""
    o = C.P(ox, oy, z)
    a = C.P(ox + ux * scale, oy + uy * scale, z)
    b = C.P(ox, oy, z - scale)
    return f"matrix({r2(a[0]-o[0])} {r2(a[1]-o[1])} {r2(b[0]-o[0])} {r2(b[1]-o[1])} {r2(o[0])} {r2(o[1])})"


def plen(pts):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))

# ---------------------------------------------------------------- font


_FONT_CACHE = {}


def font_face(text, family="HL"):
    """The mono face, subset to the glyphs this SVG uses and inlined.

    An SVG loaded through <img> fetches nothing, so a linked font would never
    arrive; a subset of a few dozen glyphs costs a few kilobytes.
    """
    from fontTools import subset
    from fontTools.ttLib import TTFont

    chars = "".join(sorted(set(text) | set(" ")))
    if chars in _FONT_CACHE:
        return _FONT_CACHE[chars]
    # no timestamp: the same text must give the same bytes, or every rebuild
    # rewrites every file
    font = TTFont(TTF, recalcTimestamp=False)
    opts = subset.Options()
    opts.flavor = "woff"
    opts.layout_features = []
    opts.name_IDs = []
    opts.hinting = False
    opts.desubroutinize = True
    s = subset.Subsetter(opts)
    s.populate(text=chars)
    s.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff"
    font.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    css = (f"@font-face{{font-family:{family};font-style:normal;font-weight:400;font-display:swap;"
           f"src:url(data:font/woff;base64,{b64}) format('woff')}}")
    _FONT_CACHE[chars] = css
    return css

# ---------------------------------------------------------------- the figure


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Fig:
    """One SVG: a card, the drawing on it, and the keyframes that move it.

    The drawing is appended back to front. Every animated element gets an id
    and one rule; `dur` is the loop, and every keyframe list closes on its
    opening value so the loop has no seam.
    """

    def __init__(self, w, h, theme="dark", dur=12.0, label="figure"):
        self.w, self.h = w, h
        self.t = THEMES[theme]
        self.theme = theme
        self.dur = dur
        self.label = label
        self.body = []
        self.css = []
        self.text = ""
        self.n = 0

    # -- ids and keyframes

    def uid(self, p="e"):
        self.n += 1
        return f"{p}{self.n}"

    def keyframes(self, el_id, prop, stops, ease=HOUSE, dur=None, extra=""):
        """stops: [(seconds, value)]. Each segment eases into the next stop."""
        dur = dur or self.dur
        stops = sorted(stops, key=lambda s: s[0])
        if stops[0][0] > 0:
            stops = [(0, stops[-1][1] if stops[-1][0] >= dur else stops[0][1])] + stops
        if stops[-1][0] < dur:
            stops = stops + [(dur, stops[0][1])]
        name = "k" + el_id
        frames = []
        for i, (t, v) in enumerate(stops):
            pct = clamp(t / dur * 100, 0, 100)
            e = stops[i][2] if len(stops[i]) > 2 else ease
            frames.append(f"{pct:.3f}%{{{prop}:{v};animation-timing-function:{e}}}")
        self.css.append(f"@keyframes {name}{{{''.join(frames)}}}")
        self.css.append(f"#{el_id}{{animation:{name} {dur}s infinite both{extra}}}")

    def move(self, el_id, stops, ease=HOUSE, dur=None):
        """stops: [(seconds, (dx, dy))] in screen units."""
        self.keyframes(el_id, "transform",
                       [(s[0], f"translate({r2(s[1][0])}px,{r2(s[1][1])}px)") + tuple(s[2:]) for s in stops],
                       ease, dur)

    def raw(self, s):
        self.body.append(s)

    def css_rule(self, s):
        self.css.append(s)

    # -- drawing primitives (all strings, so groups can nest)

    def path(self, d, cls="", extra=""):
        c = f' class="{cls}"' if cls else ""
        return f'<path d="{d}"{c}{extra}/>'

    def solid(self, sil, crease, hi=False, cls=""):
        k = "sil hi" if hi else "sil"
        out = self.path(sil, f"{k} {cls}".strip())
        if crease:
            out += self.path(crease, "nf cr")
        return out

    def g(self, inner, gid=None, cls="", extra=""):
        i = f' id="{gid}"' if gid else ""
        c = f' class="{cls}"' if cls else ""
        return f"<g{i}{c}{extra}>{inner}</g>"

    def label_text(self, x, y, s, cls="lab", anchor="start", extra=""):
        self.text += s
        a = f' text-anchor="{anchor}"' if anchor != "start" else ""
        return f'<text x="{r2(x)}" y="{r2(y)}" class="{cls}"{a}{extra}>{esc(s)}</text>'

    def cycle_text(self, x, y, items, cls="lab", anchor="start"):
        """A read-out that changes on cue: items = [(start_s, end_s, text)]."""
        out = []
        for (t0, t1, txt) in items:
            # the read-out showing at the seam is fully in at t = 0 and the
            # last one is fully out by then, so a paused figure still reads
            if t0 == 0:
                t0 = -0.18
            if abs(t1 - self.dur) < 1e-6:
                t1 = self.dur - 0.18
            tid = self.uid("t")
            out.append(self.label_text(x, y, txt, cls, anchor, f' id="{tid}" opacity="0"'))
            emit_switch(self, tid, "opacity", [(t0, t1 - 0.18)], "1", "0", 0.18)
        return "".join(out)

    # -- the card

    def frame(self, fig_no, title, caption, readout_items=None, readout=None, inset=0.5):
        """The card every figure sits on: number top-left, title top-right,
        caption bottom-left, read-out bottom-right."""
        w, h = self.w, self.h
        p = 14
        s = (f'<rect x="{inset}" y="{inset}" width="{w-2*inset}" height="{h-2*inset}" rx="10" class="card"/>')
        s += self.label_text(p + 2, p + 12, fig_no, "lab")
        s += self.label_text(w - p - 2, p + 12, title, "lab", "end")
        s += self.label_text(p + 2, h - p - 4, caption, "lab")
        if readout_items:
            s += self.cycle_text(w - p - 2, h - p - 4, readout_items, "lab ro", "end")
        elif readout:
            s += self.label_text(w - p - 2, h - p - 4, readout, "lab ro", "end")
        self.body.insert(0, s)

    # -- out

    def svg(self):
        t = self.t
        style = [
            font_face(self.text + "0123456789"),
            f".card{{fill:{t['card']};stroke:{t['border']};stroke-width:1}}",
            f"path,ellipse,polygon,circle.p{{fill:{t['plate']};stroke:{t['mid']};stroke-width:.9;"
            "vector-effect:non-scaling-stroke;stroke-linejoin:round;stroke-linecap:round}",
            ".nf{fill:none!important}",
            ".fo{stroke:none!important}",
            f".sil{{stroke:{t['edge']}}}",
            f".hi{{stroke:{t['hi']}}}",
            f".lo{{stroke:{t['lo']}}}",
            f".cr{{stroke:{t['mid']}}}",
            ".dash{stroke-dasharray:1 3}",
            f".sig{{stroke:{t['sig']}}}",
            f".sigf{{fill:{t['sig']}!important;stroke:none}}",
            f".dot{{fill:{t['hi']};stroke:none}}",
            f".dotm{{fill:{t['edge']};stroke:none}}",
            f".dotl{{fill:{t['lo']};stroke:none}}",
            f".mark{{fill:{t['edge']};stroke:none}}",
            f".markhi{{fill:{t['hi']};stroke:none}}",
            f"text{{font-family:HL,ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;fill:{t['text']}}}",
            ".lab{font-size:9.5px;letter-spacing:.06em}",
            f".ro{{fill:{t['hi']}}}",
            f".dim{{fill:{t['faint']}}}",
            f".row{{fill:{t['text']}}}.row text{{fill:inherit}}",
            "@media (prefers-reduced-motion:reduce){*{animation-play-state:paused!important}}",
        ] + self.css
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{esc(self.label)}">'
                f'<title>{esc(self.label)}</title>'
                f"<style>{''.join(style)}</style>{''.join(self.body)}</svg>")

# ---------------------------------------------------------------- timelines
#
# CSS can only ease between keyframes, and some motion here is not a
# straight line between two poses: a card turning on its hinge, a ripple
# whose parts set off at different times. So the motion is simulated
# instead: each part owns scalar tracks driven by tweens, the track is
# sampled at 60 fps over one loop, and the samples are thinned with
# Ramer-Douglas-Peucker until linear keyframes stay within a fraction of a
# pixel of the real curve. Smooth motion, short files.


def bezier(x1, y1, x2, y2):
    def bx(t):
        return 3 * (1 - t) ** 2 * t * x1 + 3 * (1 - t) * t * t * x2 + t ** 3

    def by(t):
        return 3 * (1 - t) ** 2 * t * y1 + 3 * (1 - t) * t * t * y2 + t ** 3

    def f(x):
        if x <= 0:
            return 0.0
        if x >= 1:
            return 1.0
        lo, hi = 0.0, 1.0
        for _ in range(40):
            m = (lo + hi) / 2
            if bx(m) < x:
                lo = m
            else:
                hi = m
        return by((lo + hi) / 2)
    return f


E_HOUSE = bezier(.32, .72, 0, 1)
E_GLIDE = bezier(.65, 0, .35, 1)
E_OUT = bezier(.16, 1, .3, 1)
E_IN = bezier(.5, 0, .75, 0)
E_LIN = lambda x: clamp(x, 0, 1)


def spring(x, k=100.0, c=18.0):
    """A damped spring (k 100, c 18, m 1) from 0 to 1, as a function of seconds."""
    if x <= 0:
        return 0.0
    w0 = math.sqrt(k)
    z = c / (2 * w0)
    if z < 1:
        wd = w0 * math.sqrt(1 - z * z)
        return 1 - math.exp(-z * w0 * x) * (math.cos(wd * x) + z * w0 / wd * math.sin(wd * x))
    return 1 - math.exp(-w0 * x) * (1 + w0 * x)


class Track:
    """A value over one loop, moved by tweens. Add tweens in time order."""

    def __init__(self, rest):
        self.rest = rest
        self.segs = []          # (t0, v0, v1, dur, ease)

    def at(self, t):
        v = self.rest
        for (t0, v0, v1, d, e) in self.segs:
            if t < t0:
                break
            u = (t - t0) / d if d > 0 else 1
            v = v1 if u >= 1 else v0 + (v1 - v0) * e(u)
        return v

    def to(self, t, target, dur=0.7, ease=E_HOUSE):
        v0 = self.at(t)
        self.segs.append((t, v0, target, dur, ease))
        self.segs.sort(key=lambda s: s[0])
        return self


def _rdp(pts, tol, dist):
    if len(pts) < 3:
        return pts
    keep = [0, len(pts) - 1]
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        worst, wi = -1, -1
        for i in range(a + 1, b):
            d = dist(pts[i], pts[a], pts[b])
            if d > worst:
                worst, wi = d, i
        if worst > tol:
            keep.append(wi)
            stack += [(a, wi), (wi, b)]
    return [pts[i] for i in sorted(keep)]


def sample(fn, dur, fps=60, tol=0.12):
    """fn(t) -> tuple of floats (screen units). Returns thinned [(t, vals)]."""
    n = int(dur * fps)
    pts = [(i / fps if i < n else dur, tuple(fn(i / fps if i < n else dur))) for i in range(n + 1)]

    def dist(p, a, b):
        ta, tb = a[0], b[0]
        u = (p[0] - ta) / (tb - ta) if tb > ta else 0
        return max(abs(pv - (av + (bv - av) * u)) for pv, av, bv in zip(p[1], a[1], b[1]))
    return _rdp(pts, tol, dist)


def emit(fig, el_id, prop, fn, fmt, tol=0.12, fps=60):
    """Animate el_id's prop along fn(t); fmt(vals) -> the CSS value."""
    a, b = fn(0.0), fn(fig.dur)
    if max(abs(x - y) for x, y in zip(a, b)) > max(tol * 4, 0.5):
        print(f"    seam: #{el_id} {prop} jumps {a} -> {b}")
    pts = sample(fn, fig.dur, fps, tol)
    if all(p[1] == pts[0][1] for p in pts):
        return False
    frames = "".join(f"{p[0] / fig.dur * 100:.3f}%{{{prop}:{fmt(p[1])}}}" for p in pts)
    name = "k" + el_id
    fig.css.append(f"@keyframes {name}{{{frames}}}")
    fig.css.append(f"#{el_id}{{animation:{name} {fig.dur}s linear infinite both}}")
    return True


def emit_translate(fig, el_id, fn, tol=0.1):
    """fn(t) -> (dx, dy)."""
    return emit(fig, el_id, "transform", fn, lambda v: f"translate({r2(v[0])}px,{r2(v[1])}px)", tol)


def emit_matrix(fig, el_id, fn, tol=0.25, extent=24.0):
    """fn(t) -> (a, b, c, d, e, f). The linear part is weighed by the drawing's
    extent, so tol is the most any point of it may stray, in px."""
    def scaled(t):
        a, b, c, d, e, f_ = fn(t)
        return (a * extent, b * extent, c * extent, d * extent, e, f_)
    return emit(fig, el_id, "transform", scaled,
                lambda v: "matrix(" + ",".join(r2(x) if i > 3 else f"{x / extent:.3f}" for i, x in enumerate(v)) + ")", tol)


def level(t, windows, fade, dur):
    """0..1: how far "on" a part is at t, for windows [(t0, t1)] that may wrap the loop.
    It rises over `fade` from t0 and falls over `fade` from t1."""
    best = 0.0
    for (a, b) in windows:
        for off in (-dur, 0.0, dur):
            x = t + off
            if x < a or x > b + fade:
                continue
            v = min(1.0, (x - a) / fade) if x < a + fade else (1.0 if x <= b else 1 - (x - b) / fade)
            best = max(best, v)
    return best


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def emit_switch(fig, el_id, prop, windows, on, off, fade=0.25):
    """A property that is `on` inside the windows and `off` outside, faded at the edges.
    on/off are colours ('#rrggbb') or numbers (as strings)."""
    if not windows:
        return
    if on.startswith("#"):
        a, b = _rgb(off), _rgb(on)
        fn = lambda t: tuple(lerp(a[i], b[i], level(t, windows, fade, fig.dur)) for i in range(3))
        fmt = lambda v: "rgb(%d,%d,%d)" % tuple(round(x) for x in v)
        return emit(fig, el_id, prop, fn, fmt, tol=1.5, fps=30)
    a, b = float(off), float(on)
    fn = lambda t: (lerp(a, b, level(t, windows, fade, fig.dur)),)
    return emit(fig, el_id, prop, fn, lambda v: r2(v[0]), tol=0.01, fps=30)
