"""The figures. Each function returns one finished SVG string for one theme.

Every figure is a loop of a fixed length, and t = 0 is its rest pose, so a
paused figure (reduced motion) still reads. Its read-out, bottom right,
keeps time with the drawing: watch for a few seconds and it tells you, in a
handful of characters, what you are looking at.

Most figures place things with u/v rather than world x/y. At the 45° camera
u runs straight across the screen and v straight into it, so a row along u
lines up horizontally and nothing in it overlaps its neighbours.
"""
import json
import math
import os

from iso import (
    Cam, Fig, Track, E_HOUSE, E_GLIDE, E_OUT, E_IN, E_LIN, box, circ, clamp, emit, emit_matrix,
    emit_switch, emit_translate, hull, lerp, level, open_, poly, prism, r2, ring_at, rings, rrect,
    run, seg,
)

HERE = os.path.dirname(os.path.abspath(__file__))
LOGOS = json.load(open(os.path.join(HERE, "logos.json")))
SQ = math.sqrt(0.5)


def W(u, v):
    """World x/y for a screen-aligned u (across) and v (into the screen)."""
    return ((u + v) * SQ, (v - u) * SQ)


def P(C, u, v, z=0.0):
    x, y = W(u, v)
    return C.P(x, y, z)


def solid_uv(f, C, u, v, hw, hd, z0, z1, r=4.0, b=1.4, cls="sil", sid=None, crease=True):
    """A rounded box centred on (u, v); hw/hd are its half extents along world x/y."""
    x, y = W(u, v)
    ring, inner = rings(x - hw, y - hd, x + hw, y + hd, r, b)
    sil, cr = prism(C, ring, inner if crease else None, z0, z1)
    i = f' id="{sid}"' if sid else ""
    out = f'<path d="{sil}" class="{cls}"{i}/>'
    if cr:
        out += f'<path d="{cr}" class="nf cr"/>'
    return out


def cyl_uv(f, C, u, v, R, z0, z1, cls="sil", sid=None, n=28):
    x, y = W(u, v)
    sil, cr = prism(C, circ(R, n, x, y), circ(R - 1.3, n, x, y), z0, z1)
    i = f' id="{sid}"' if sid else ""
    return f'<path d="{sil}" class="{cls}"{i}/><path d="{cr}" class="nf cr"/>'


def led(f, C, u, v, z, lid=None, cls="sigf", r=1.7):
    p = P(C, u, v, z)
    i = f' id="{lid}"' if lid else ""
    return f'<circle cx="{r2(p[0])}" cy="{r2(p[1])}" r="{r}" class="{cls}"{i}/>'


def dot(p, cls="dotm", r=1.15, did=None):
    i = f' id="{did}"' if did else ""
    return f'<circle cx="{r2(p[0])}" cy="{r2(p[1])}" r="{r}" class="{cls}"{i}/>'


def wrap(f, inner, move=None, show=None, fade=0.3, tol=0.1, hidden_at_rest=False):
    """Nest the animations a part needs, one per element, so they never fight:
    an outer group moves, an inner group fades."""
    out = inner
    if show is not None:
        gid = f.uid("o")
        emit_switch(f, gid, "opacity", show, "1", "0", fade)
        op = ' opacity="0"' if hidden_at_rest else ""
        out = f'<g id="{gid}"{op}>{out}</g>'
    if move is not None:
        gid = f.uid("v")
        emit_translate(f, gid, move, tol)
        out = f'<g id="{gid}">{out}</g>'
    return out


def hop(a, b, h):
    """A point on a hop from a to b (screen offsets), h px high at its peak."""
    def at(u):
        return (lerp(a[0], b[0], u), lerp(a[1], b[1], u) - h * 4 * u * (1 - u))
    return at


def path_at(pts, u):
    """The point a fraction u of the way along a polyline."""
    segs = [(a, b, math.hypot(b[0] - a[0], b[1] - a[1])) for a, b in zip(pts, pts[1:])]
    d = clamp(u, 0, 1) * sum(s[2] for s in segs)
    for i, (a, b, L) in enumerate(segs):
        if d <= L or i == len(segs) - 1:
            k = clamp(d / L, 0, 1) if L else 0
            return (lerp(a[0], b[0], k), lerp(a[1], b[1], k))
        d -= L
    return pts[-1]


def packet(f, pts, windows, r=2.0, cls="sigf"):
    """A green signal that runs along pts (screen) inside each window (t0, t1)."""
    x0, y0 = pts[0]

    def pos(t):
        for (t0, t1) in windows:
            if t0 <= t <= t1:
                p = path_at(pts, E_GLIDE((t - t0) / (t1 - t0)))
                return (p[0] - x0, p[1] - y0)
        return (0.0, 0.0)
    show = [(t0 - 0.12, t1 - 0.05) for (t0, t1) in windows]
    inner = f'<circle cx="{r2(x0)}" cy="{r2(y0)}" r="{r}" class="{cls}"/>'
    return wrap(f, inner, move=pos, show=show, fade=0.12, hidden_at_rest=True)


def legend(f, x, y, rows, widths, active, head=None, step=18, foot=None):
    """A small table beside a wide figure. rows: [cells]; active: per row a list
    of (t0, t1) windows in which the row is lit, in step with the drawing."""
    out = ""
    yy = y
    rule_w = sum(widths) - 10
    if head:
        cx = x
        for k, cell in enumerate(head):
            out += f.label_text(cx, yy, cell, "lab dim")
            cx += widths[k]
        out += f'<path d="M{x} {yy + 8}H{x + rule_w}" class="nf lo"/>'
        yy += 8 + step
    for i, cells in enumerate(list(rows) + ([foot[0]] if foot else [])):
        is_foot = foot and i == len(rows)
        if is_foot:
            out += f'<path d="M{x} {yy - step + 6}H{x + rule_w}" class="nf lo"/>'
            yy += 4
        cx = x
        gid = f.uid("r")
        inner = ""
        for k, cell in enumerate(cells):
            inner += f.label_text(cx, yy, cell, "lab")
            cx += widths[k]
        out += f'<g id="{gid}" class="row">{inner}</g>'
        wins = foot[1] if is_foot else (active[i] if active else None)
        if wins:
            emit_switch(f, gid, "fill", wins, f.t["hi"], f.t["text"], 0.3)
        yy += step
    return out


# ================================================================= stack


def stack(theme, tools, jobs, cols=4, fig_no="Fig 1.6", title="STACK", caption="RIGHT TOOL, RIGHT JOB"):
    """The tools, as a tray of tiles, beside a table of jobs. Each tile carries
    a card with the tool's mark, hinged at its near edge. One at a time a card
    stands up and turns to face the reader, the cards around it lift a little,
    staggered outwards, and the job it does lights in the table.

    tools: [(simple-icons slug, read-out role, job row)] in the order the
    cards stand; jobs: [(job, tools)] for the table."""
    n = len(tools)
    rows = math.ceil(n / cols)
    T, G, TH, RB, LOGO, UP = 46, 9, 6, 7, 30, 90
    W_, H_ = cols * T + (cols - 1) * G, rows * T + (rows - 1) * G
    step = 2.0
    f = Fig(820, 320, theme, dur=step * n, label="the tools, one card standing at a time, and the job each one does")
    C = Cam(45, 0.5, 1)
    CARD = LOGO + 8
    C.autoscale([(-RB, -RB, -5), (W_ + RB, H_ + RB, -5), (W_ + RB, -RB, -5), (-RB, H_ + RB, -5),
                 (0, 0, TH + CARD), (W_, 0, TH + CARD), (0, H_, TH + CARD)], 400, 228, 250, 170)

    tr, ti = rings(-RB, -RB, W_ + RB, H_ + RB, 8, 2.2)
    f.raw(f.solid(*prism(C, tr, ti, -5, 0)))

    s = LOGO / 24
    PAD = 4 / s
    SIDE = (24 + 2 * PAD) * s

    def hinge(cx, cy, th):
        t = math.radians(th)
        c, nn = math.cos(t), math.sin(t)
        y = (math.pi / 4) * (th / 90)
        e1 = (math.cos(y), -math.sin(y))
        fw = (math.sin(y), math.cos(y))
        hx = cx + fw[0] * (SIDE / 2) * c
        hy = cy + fw[1] * (SIDE / 2) * c

        def W3(u, v):
            a = (u - 12) * s
            d = (24 + PAD - v) * s
            return C.P(hx + e1[0] * a - fw[0] * d * c, hy + e1[1] * a - fw[1] * d * c, TH + 0.4 + d * nn)
        o, a, b = W3(0, 0), W3(1, 0), W3(0, 1)
        return (a[0] - o[0], a[1] - o[1], b[0] - o[0], b[1] - o[1], o[0], o[1])

    k3 = 3
    card = (f"M{-PAD + k3} {-PAD}H{24 + PAD - k3}Q{24 + PAD} {-PAD} {24 + PAD} {-PAD + k3}"
            f"V{24 + PAD - k3}Q{24 + PAD} {24 + PAD} {24 + PAD - k3} {24 + PAD}H{-PAD + k3}"
            f"Q{-PAD} {24 + PAD} {-PAD} {24 + PAD - k3}V{-PAD + k3}Q{-PAD} {-PAD} {-PAD + k3} {-PAD}Z")

    # The cards stand in the order given, but placed so that each one hops
    # across the tray from the last rather than reading it like a list.
    order = sorted(range(n), key=lambda k: ((k * 5) % n))
    tiles = [None] * n
    for j, (slug, role, job) in enumerate(tools):
        k = order[j]
        tiles[k] = dict(slug=slug, role=role, job=job, c=k % cols, r=k // cols, k=k, j=j)
    rest_lift = lambda d, reach=1.9: max(3.0, 34 * max(0.0, 1 - d / reach))

    # Each card's turn starts LEAD seconds before its slot, so the first card
    # is already standing at t = 0: the still frame (and the paused one, under
    # reduced motion) shows the first tool with its read-out.
    LEAD = 1.0
    first = tiles[order[0]]
    tracks = {}
    for t in tiles:
        d = math.hypot(t["c"] - first["c"], t["r"] - first["r"])
        tracks[t["k"]] = Track(UP if t is first else rest_lift(d))
    windows = {k: [] for k in range(n)}
    for j in list(range(1, n)) + [0]:
        a = tiles[order[j]]
        t0 = j * step - LEAD if j else n * step - LEAD
        for t in tiles:
            d = math.hypot(t["c"] - a["c"], t["r"] - a["r"])
            tracks[t["k"]].to(t0 + d * 0.06, UP if t is a else rest_lift(d), 0.75 if t is a else 0.6, E_HOUSE)
        windows[a["k"]].append((j * step - LEAD, (j + 1) * step - LEAD - 0.25))

    for t in sorted(tiles, key=lambda t: t["c"] + t["r"]):
        x0, y0 = t["c"] * (T + G), t["r"] * (T + G)
        ring, inner = rings(x0, y0, x0 + T, y0 + T, 5, 1.4)
        f.raw(f.solid(*prism(C, ring, inner, 0, TH)))
        cx, cy = x0 + T / 2, y0 + T / 2
        gid, cid, mid = f.uid("g"), f.uid("c"), f.uid("m")
        tr_ = tracks[t["k"]]
        m0 = hinge(cx, cy, tr_.at(0))
        f.raw(f'<g id="{gid}" transform="matrix({",".join(r2(v) for v in m0)})">'
              f'<path id="{cid}" d="{card}" class="sil"/>'
              f'<path id="{mid}" d="{LOGOS[t["slug"]]["d"]}" class="mark"/></g>')
        emit_matrix(f, gid, lambda tt, tr_=tr_, cx=cx, cy=cy: hinge(cx, cy, tr_.at(tt)), tol=0.3, extent=24 + 2 * PAD)
        emit_switch(f, cid, "stroke", windows[t["k"]], f.t["hi"], f.t["edge"])
        emit_switch(f, mid, "fill", windows[t["k"]], f.t["hi"], f.t["edge"])

    # the table: a job lights while one of its tools is standing
    lit = [[] for _ in jobs]
    for t in tiles:
        lit[t["job"]] += windows[t["k"]]
    f.raw(legend(f, 508, 98, [list(jb) for jb in jobs], [140, 154], lit, head=["job", "tool"]))

    items = []
    for j in range(n):
        tl = tiles[order[j]]
        name = LOGOS[tl["slug"]].get("short") or LOGOS[tl["slug"]]["title"].lower()
        items.append((j * step - LEAD, (j + 1) * step - LEAD, f"{name} · {tl['role']}"))
    f.frame(fig_no, title, caption, items)
    return f.svg()


# ================================================================= homelab

HOSTS = [
    # name, ram, threads, what it runs, (half x, half y, height), (guest kind, count)
    ("pve", "32 GB", "12", "lxc services", (24, 24, 22), ("lxc", 5), "gitea · gotify · ci runner"),
    ("dell", "64 GB", "12", "project vms", (31, 31, 30), ("vm", 3), "vm1–3 · hermes agent"),
    ("m920q", "32 GB", "6", "kubernetes", (18, 18, 11), ("talos", 4), "devops vm + 3 talos vms"),
]


def homelab(theme, fig_no="Fig 01", title="HOMELAB", caption="PROXMOX VE · ONE CLUSTER, THREE NODES",
            hosts=HOSTS, total=("128 GB", "30")):
    """Three machines in a row. One at a time a host's guests rise out of it,
    exploded, and its row in the table lights: LXC services on pve, project
    VMs on dell, and on the small m920q a control VM under the three Talos
    VMs that are the Kubernetes cluster. A tailnet runs under all three."""
    dur = 15.0
    f = Fig(820, 320, theme, dur=dur, label="three proxmox nodes and the guests each one runs")
    C = Cam(45, 0.5, 1.0)
    PITCH = 118
    us = [-PITCH, 0, PITCH]
    C.autoscale([W(-PITCH, 0) + (0,), W(-PITCH - 34, 0) + (0,), W(PITCH + 34, 0) + (0,),
                 W(0, 50) + (0,), W(0, -34) + (0,), W(0, 0) + (122,)], 470, 236, 268, 160)
    focus = [(1.0, 4.6), (4.6, 8.2), (8.2, 11.8)]
    every = (11.8, 14.4)

    # the tailnet: a dashed run on the floor in front, a drop to each host
    route = [P(C, u, 52, 0) for u in us]
    f.raw(f'<path d="{open_(route)}" class="nf dash"/>')
    for u in us:
        f.raw(f'<path d="{seg(P(C, u, 52, 0), P(C, u, 26, 0))}" class="nf dash"/>')

    for k, ((name, ram, thr, what, (hw, hd, h), (kind, count), _), u) in enumerate(zip(hosts, us)):
        sid = f.uid("s")
        body = solid_uv(f, C, u, 0, hw, hd, 0, h, 5, 1.6, sid=sid)
        # a vent line and a status led on the face toward the reader
        x, y = W(u, 0)
        a, b = C.P(x + hw, y - hd * 0.55, h * 0.55), C.P(x + hw, y + hd * 0.1, h * 0.55)
        body += f'<path d="{seg(a, b)}" class="nf lo"/>'
        q = C.P(x + hw * 0.55, y + hd, h * 0.55)
        body += f'<circle cx="{r2(q[0])}" cy="{r2(q[1])}" r="1.7" class="sigf"/>'
        f.raw(body)
        emit_switch(f, sid, "stroke", [focus[k]], f.t["hi"], f.t["edge"], 0.3)

        # guests stacked on the lid; at focus they explode upward
        tr = Track(0.0)
        tr.to(focus[k][0], 1.0, 0.9).to(focus[k][1] - 0.6, 0.0, 0.8)
        tr.to(every[0] + 0.12 * k, 0.4, 0.9).to(every[1] - 0.2, 0.0, 0.8)
        if kind == "lxc":
            tray = solid_uv(f, C, u, 0, hw - 3, hd - 3, h + 2, h + 5, 4, 1.2)
            cells = [(-8.5, -8.5), (8.5, -8.5), (0, 0), (-8.5, 8.5), (8.5, 8.5)][:count]
            for (dx, dy) in sorted(cells, key=lambda c: c[0] + c[1]):
                tray += _cube(C, x + dx, y + dy, h + 5, 4.4, 8.5)
            f.raw(wrap(f, tray, move=lambda t, tr=tr: C.d(0, 0, tr.at(t) * 30)))
        else:
            th = 5.0 if kind == "vm" else 3.6
            inset = 4.5 if kind == "vm" else 3.0
            for j in range(count):
                z0 = h + 2 + j * (th + 1.6)
                slab = solid_uv(f, C, u, 0, hw - inset, hd - inset, z0, z0 + th, 4, 1.2)
                if kind == "talos" and j > 0:
                    # the talos vms carry a dot code on the lid: three of them are the cluster
                    for qd in range(3):
                        slab += dot(C.P(x - 4 + qd * 4, y + 4 - qd * 4, z0 + th), "dotm", 0.95)
                gap = 13 if kind == "vm" else 11
                f.raw(wrap(f, slab, move=lambda t, tr=tr, j=j, gap=gap: C.d(0, 0, tr.at(t) * (j + 1) * gap), tol=0.08))

    # signals along the tailnet when the cluster is seen whole
    for i in range(2):
        f.raw(packet(f, [route[i], route[i + 1]],
                     [(every[0] + 0.4 + 0.9 * i, every[0] + 1.2 + 0.9 * i), (focus[i][1] - 1.2, focus[i][1] - 0.3)], 1.9))

    rows = [[h[0], h[1], h[2], h[3]] for h in hosts]
    f.raw(legend(f, 548, 116, rows, [60, 58, 38, 100], [[focus[i]] for i in range(3)],
                 head=["node", "ram", "thr", "runs"],
                 foot=(["total", total[0], total[1], "on tailscale"], [every])))
    items = [(0, focus[0][0], "3 nodes · 128 GB · 30 threads")]
    for k, h in enumerate(hosts):
        items.append((focus[k][0], focus[k][1], h[6]))
    items.append((every[0], dur, "one tailnet, one cluster"))
    f.frame(fig_no, title, caption, items)
    return f.svg()


def _cube(C, x, y, z, hw, h):
    ring, inner = rings(x - hw, y - hw, x + hw, y + hw, 1.8, 0.9)
    sil, cr = prism(C, ring, inner, z, z + h)
    return f'<path d="{sil}" class="sil"/><path d="{cr}" class="nf cr"/>'


def rings_uv(u0, v0, u1, v1, r, b):
    """A rounded footprint laid along u/v instead of world x/y, with its crease ring."""
    def conv(ring):
        out = []
        for (u, v, nu, nv) in ring:
            x, y = W(u, v)
            out.append((x, y, (nu + nv) * SQ, (nv - nu) * SQ))
        return out
    return conv(rrect(u0, v0, u1, v1, r)), conv(rrect(u0 + b, v0 + b, u1 - b, v1 - b, max(0.3, r - b)))


def plank_uv(C, u0, v0, u1, v1, z0, z1, r=3.0, b=1.2, cls="sil", sid=None):
    ring, inner = rings_uv(u0, v0, u1, v1, r, b)
    sil, cr = prism(C, ring, inner, z0, z1)
    i = f' id="{sid}"' if sid else ""
    return f'<path d="{sil}" class="{cls}"{i}/><path d="{cr}" class="nf cr"/>'


# ================================================================= cluster


def cluster(theme, fig_no="Fig 02", title="CLUSTER", caption="TALOS LINUX · ARGO CD"):
    """Git, one control plane, two workers. A push lands in the repo, Argo CD on
    the control plane notices and reconciles, and the workers' pods are
    replaced one at a time until the cluster matches git again."""
    dur = 13.0
    f = Fig(400, 320, theme, dur=dur, label="argo cd syncing a talos kubernetes cluster from git")
    C = Cam(45, 0.5, 1.0)
    REPO, CP, WK = (-112, -24), (2, -30), [(-46, 32), (50, 32)]
    C.autoscale([W(REPO[0] - 16, REPO[1]) + (0,), W(WK[1][0] + 34, WK[1][1]) + (0,),
                 W(WK[0][0], WK[0][1] + 34) + (0,), W(CP[0], CP[1] - 30) + (0,), W(CP[0], CP[1]) + (78,)],
                336, 220, 200, 166)

    t_push, t_pkt, t_sync, t_roll, per = 1.2, 1.6, 2.6, 3.4, 0.92
    t_done = t_roll + 6 * per + 0.2

    # floor links: repo -> cp -> each worker
    repo_out, cp_in = P(C, REPO[0] + 14, REPO[1], 0), P(C, CP[0] - 26, CP[1], 0)
    f.raw(f'<path d="{seg(repo_out, cp_in)}" class="nf dash"/>')
    links = []
    for (u, v) in WK:
        a = P(C, CP[0] + (u - CP[0]) * 0.36, CP[1] + 21, 0)
        b = P(C, u, v - 26, 0)
        f.raw(f'<path d="{seg(a, b)}" class="nf dash"/>')
        links.append((a, b))

    # the repo: a low block with three commits on its lid
    rid = f.uid("s")
    repo = solid_uv(f, C, *REPO, 13, 13, 0, 9, 4, 1.3, sid=rid)
    x, y = W(*REPO)
    for k in range(3):
        repo += dot(C.P(x - 5 + k * 5, y + 5 - k * 5, 9), "dotm", 1.1)
    f.raw(repo)
    emit_switch(f, rid, "stroke", [(t_push, t_sync)], f.t["hi"], f.t["edge"])

    # control plane, with argo's reconcile ring on its lid
    cid = f.uid("s")
    HC = 30
    cpm = solid_uv(f, C, *CP, 20, 20, 0, HC, 5, 1.6, sid=cid)
    x, y = W(*CP)
    ring = [C.P(x + 10 * math.cos(a), y + 10 * math.sin(a), HC) for a in [i / 40 * math.tau for i in range(40)]]
    cpm += f'<path d="{poly(ring)}" class="nf dash"/>'
    q = C.P(x + 20, y + 20 * 0.5, HC * 0.5)
    cpm += f'<circle cx="{r2(q[0])}" cy="{r2(q[1])}" r="1.7" class="sigf"/>'
    f.raw(cpm)
    emit_switch(f, cid, "stroke", [(t_sync, t_done)], f.t["hi"], f.t["edge"])
    # the orbiting reconcile dot
    o0 = C.P(x + 10, y, HC)

    def orbit(t):
        if t < t_sync or t > t_done:
            return (0.0, 0.0)
        a = (t - t_sync) * 2.2
        p = C.P(x + 10 * math.cos(a), y + 10 * math.sin(a), HC)
        return (p[0] - o0[0], p[1] - o0[1])
    f.raw(wrap(f, f'<circle cx="{r2(o0[0])}" cy="{r2(o0[1])}" r="2" class="sigf"/>', move=orbit,
               show=[(t_sync, t_done)], fade=0.2, hidden_at_rest=True, tol=0.15))

    # workers and their pods
    HW = 17
    slots = [(-7, -7), (7, -7), (-7, 7), (7, 7)]
    order = []
    for w, (u, v) in enumerate(WK):
        f.raw(solid_uv(f, C, u, v, 22, 22, 0, HW, 5, 1.6))
        x, y = W(u, v)
        q = C.P(x + 22, y + 22 * 0.5, HW * 0.5)
        f.raw(f'<circle cx="{r2(q[0])}" cy="{r2(q[1])}" r="1.7" class="sigf"/>')
        filled = [0, 1, 3] if w == 0 else [0, 2, 3]
        for s in sorted(filled, key=lambda s: slots[s][0] + slots[s][1]):
            order.append((w, s, x + slots[s][0], y + slots[s][1]))
    # replace in an order that alternates workers
    seq = sorted(order, key=lambda p: (order.index(p) % 3, p[0]))
    pkts = []
    for (w, s, px, py) in order:
        k = seq.index((w, s, px, py))
        t0 = t_roll + k * per + 0.35
        tr = Track(0.0).to(t0, 22, 0.32, E_IN).to(t0 + 0.32, -26, 0.001, E_LIN).to(t0 + 0.34, 0.0, 0.5, E_OUT)
        pid = f.uid("s")
        ring_, inner = rings(px - 4.4, py - 4.4, px + 4.4, py + 4.4, 1.8, 0.9)
        sil, cr = prism(C, ring_, inner, HW, HW + 9)
        pod = f'<path d="{sil}" class="sil" id="{pid}"/><path d="{cr}" class="nf cr"/>'
        emit_switch(f, pid, "stroke", [(t0 + 0.34, t0 + 1.1)], f.t["hi"], f.t["edge"], 0.2)
        f.raw(wrap(f, pod, move=lambda t, tr=tr: C.d(0, 0, tr.at(t)),
                   show=[(-1, t0 + 0.12), (t0 + 0.36, dur + 1)], fade=0.18, tol=0.1))
        pkts.append((w, t_roll + k * per - 0.05, t_roll + k * per + 0.4))

    f.raw(packet(f, [repo_out, cp_in], [(t_pkt, t_pkt + 0.9)]))
    for w in range(2):
        f.raw(packet(f, list(links[w]), [(a, b) for (ww, a, b) in pkts if ww == w], 1.8))

    items = [(0, t_push, "1 control plane · 2 workers"), (t_push, t_sync, "git push · k8s/apps"),
             (t_sync, t_roll, "argo cd · out of sync")]
    for k in range(6):
        items.append((t_roll + k * per, t_roll + (k + 1) * per, f"rolling · pod {k + 1}/6"))
    items.append((t_roll + 6 * per, dur, "synced · healthy"))
    f.frame(fig_no, title, caption, items)
    return f.svg()


# ================================================================= previews


def previews(theme, fig_no="Fig 03", title="PREVIEWS", caption="ONE ENVIRONMENT PER BRANCH"):
    """A commit graph above a preview environment. A branch forks off main and
    an ApplicationSet gives it its own WordPress and database; a new commit on
    the branch is pulled into the preview; the branch merges and its preview
    is torn down. Then the history settles for the next one."""
    dur = 14.0
    f = Fig(400, 320, theme, dur=dur, label="a branch gets its own preview environment until it merges")
    C = Cam(45, 0.5, 1.0)
    MV = -46          # main's v
    BV = 14           # the branch's v
    C.autoscale([W(-128, MV - 10) + (0,), W(128, MV + 10) + (0,), W(-40, 118) + (0,), W(40, 118) + (0,),
                 W(0, MV) + (34,)], 330, 214, 200, 166)

    t_fork, t_c1, t_env, t_blocks, t_c2, t_pull, t_merge, t_down, t_reset = 1.0, 1.7, 2.4, 3.0, 5.4, 5.8, 7.8, 9.0, 11.4
    # main: a plank with commits
    f.raw(plank_uv(C, -128, MV - 7, 128, MV + 7, -3, 0, 4, 1.2))
    main_c = [-104, -74, -44]
    FORK = -44
    MERGE = 62
    for u in main_c:
        f.raw(cyl_uv(f, C, u, MV, 6, 0, 5, n=24))

    # the branch path, drawn in: down from the fork, along, and later back up to main
    p_fork = [P(C, FORK, MV + 6, 0), P(C, FORK + 26, BV, 0), P(C, MERGE - 30, BV, 0)]
    p_merge = [P(C, MERGE - 30, BV, 0), P(C, MERGE, MV + 6, 0)]

    def drawn(pts, t0, t1, gone0, gone1):
        L = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))
        did = f.uid("d")
        f.css_rule(f"#{did}{{stroke-dasharray:{r2(L)} {r2(L + 2)}}}")
        emit(f, did, "stroke-dashoffset",
             lambda t: (L if t > gone1 + 0.05 else L * (1 - E_GLIDE(clamp((t - t0) / (t1 - t0), 0, 1))),),
             lambda v: r2(v[0]) + "px", tol=0.4, fps=40)
        return wrap(f, f'<path id="{did}" d="{open_(pts)}" class="nf sil"/>', show=[(t0 - 0.05, gone0)], fade=gone1 - gone0)
    f.raw(drawn(p_fork, t_fork, t_c1, t_reset, t_reset + 0.6))
    f.raw(drawn(p_merge, t_merge, t_merge + 0.6, t_reset, t_reset + 0.6))

    # branch commits pop up on the path
    def pop(u, v, t_in, cls_win=None):
        cid_ = f.uid("s")
        body = cyl_uv(f, C, u, v, 5.5, 0, 5, sid=cid_, n=24)
        if cls_win:
            emit_switch(f, cid_, "stroke", cls_win, f.t["hi"], f.t["edge"], 0.25)
        tr = Track(9.0).to(t_in, 0.0, 0.5, E_OUT).to(t_reset + 0.8, 9.0, 0.01, E_LIN)
        return wrap(f, body, move=lambda t, tr=tr: C.d(0, 0, tr.at(t)), show=[(t_in, t_reset)], fade=0.3,
                    hidden_at_rest=True)
    c1u, c2u = FORK + 44, MERGE - 30
    f.raw(pop(c1u, BV, t_c1, [(t_c1, t_c2)]))
    f.raw(pop(c2u, BV, t_c2, [(t_c2, t_merge)]))
    f.raw(pop(MERGE, MV, t_merge + 0.5, [(t_merge + 0.5, t_down + 1.0)]))

    # the preview: a namespace plate, a wordpress block and a database cylinder
    EU, EV = 6, 88
    plate = solid_uv(f, C, EU, EV, 30, 30, 0, 3.5, 6, 1.6)
    lp = P(C, EU + 30 * SQ * 0.9, EV + 30 * SQ * 1.1, 1.8)
    plate += f'<circle cx="{r2(lp[0])}" cy="{r2(lp[1])}" r="1.6" class="sigf"/>'
    ptr = Track(-14.0).to(t_env, 0.0, 0.6, E_OUT).to(t_down + 0.5, -14.0, 0.6, E_IN)
    f.raw(wrap(f, plate, move=lambda t: C.d(0, 0, ptr.at(t)), show=[(t_env, t_down + 0.7)], fade=0.4,
               hidden_at_rest=True))
    wx, wy = W(EU, EV)
    wid = f.uid("s")
    wp = solid_uv(f, C, EU - 9, EV - 9, 9, 9, 3.5, 21, 3, 1.2, sid=wid)
    db = cyl_uv(f, C, EU + 11, EV + 11, 7.5, 3.5, 15)
    # wordpress bumps when the new commit is pulled in
    wtr = Track(26.0).to(t_blocks, 0.0, 0.55, E_OUT).to(t_pull + 0.8, 5.0, 0.25, E_OUT).to(t_pull + 1.05, 0.0, 0.4, E_HOUSE)
    wtr.to(t_down, 22.0, 0.5, E_IN).to(t_reset, 26.0, 0.01, E_LIN)
    dtr = Track(26.0).to(t_blocks + 0.18, 0.0, 0.55, E_OUT).to(t_down + 0.12, 22.0, 0.5, E_IN).to(t_reset, 26.0, 0.01, E_LIN)
    emit_switch(f, wid, "stroke", [(t_pull + 0.8, t_pull + 1.7)], f.t["hi"], f.t["edge"], 0.2)
    f.raw(wrap(f, db, move=lambda t: C.d(0, 0, dtr.at(t)), show=[(t_blocks + 0.05, t_down + 0.3)], fade=0.3,
               hidden_at_rest=True))
    f.raw(wrap(f, wp, move=lambda t: C.d(0, 0, wtr.at(t)), show=[(t_blocks - 0.1, t_down + 0.3)], fade=0.3,
               hidden_at_rest=True))

    # the pull: a signal from the new commit down to the preview
    f.raw(packet(f, [P(C, c2u, BV + 6, 0), P(C, EU - 9, EV - 20, 0)], [(t_pull, t_pull + 0.8)]))

    items = [(0, t_fork, "main · deployed"), (t_fork, t_env, "branch · feat/hero"),
             (t_env, t_c2, "applicationset → preview"), (t_c2, t_merge - 0.2, "push · pulled within 60 s"),
             (t_merge - 0.2, t_down, "merge → main"), (t_down, t_reset + 0.4, "preview · torn down"),
             (t_reset + 0.4, dur, "main · deployed")]
    f.frame(fig_no, title, caption, items)
    return f.svg()


# ================================================================= agents


def agents(theme, fig_no="Fig 04", title="AGENTS", caption="ISOLATED BY DESIGN"):
    """An agent in a cage, a gate, an app. The agent lives on its own VM and
    reaches the app only through an MCP server whose lid carries the tool
    allowlist: twenty-four tools, twenty-two lit. Reads go through; a publish
    stops at the gate and comes back."""
    dur = 14.0
    f = Fig(400, 320, theme, dur=dur, label="an ai agent on its own vm, reaching an app only through an mcp allowlist")
    C = Cam(45, 0.5, 1.0)
    SB, GT, AP = -108, 0, 108
    C.autoscale([W(SB - 36, 0) + (0,), W(AP + 36, 0) + (0,), W(0, 30) + (0,), W(0, -30) + (0,),
                 W(SB, 0) + (46,)], 340, 200, 200, 172)

    req = [(3.0, True), (5.5, True), (8.0, False)]
    GH, AH = 26, 20
    # the floor run between the three
    sb_r, gt_l, gt_r, ap_l = P(C, SB + 26 * 1.414, 0, 0), P(C, GT - 18 * 1.414, 0, 0), P(C, GT + 18 * 1.414, 0, 0), P(C, AP - 24 * 1.414, 0, 0)
    f.raw(f'<path d="{seg(sb_r, gt_l)}" class="nf dash"/><path d="{seg(gt_r, ap_l)}" class="nf dash"/>')

    # the sandbox: a plate and a dashed cage around the agent
    x, y = W(SB, 0)
    HB, CG, TOP = 4, 21, 44
    f.raw(solid_uv(f, C, SB, 0, 26, 26, 0, HB, 6, 1.6))
    corners = {"back": (x - CG, y - CG), "left": (x - CG, y + CG), "right": (x + CG, y - CG), "front": (x + CG, y + CG)}
    for k in ("back", "left", "right"):
        cx, cy = corners[k]
        f.raw(f'<path d="{seg(C.P(cx, cy, HB), C.P(cx, cy, TOP))}" class="nf dash"/>')
    # the agent wanders inside
    spots = [(0, 0), (-9, 6), (7, -8), (8, 7), (0, 0)]
    times = [0, 1.4, 4.6, 7.2, 10.5, dur]
    tx, ty = Track(0.0), Track(0.0)
    for k in range(1, len(spots)):
        tx.to(times[k], spots[k][0], 1.0, E_GLIDE)
        ty.to(times[k], spots[k][1], 1.0, E_GLIDE)
    aid = f.uid("s")
    agent = _cube(C, x, y, HB, 6.5, 13).replace('class="sil"', f'class="sil" id="{aid}"', 1)
    f.raw(wrap(f, agent, move=lambda t: C.d(tx.at(t), ty.at(t), 0), tol=0.08))
    emit_switch(f, aid, "stroke", [(-0.4, 1.6), (10.2, dur + 0.2)], f.t["hi"], f.t["edge"], 0.3)
    cx, cy = corners["front"]
    f.raw(f'<path d="{seg(C.P(cx, cy, HB), C.P(cx, cy, TOP))}" class="nf dash"/>')
    top = rrect(x - CG, y - CG, x + CG, y + CG, 3)
    f.raw(f'<path d="{poly(ring_at(C, top, TOP))}" class="nf dash"/>')

    # the gate: an mcp server, its allowlist laid out on the lid
    gx, gy = W(GT, 0)
    gid = f.uid("s")
    f.raw(solid_uv(f, C, GT, 0, 18, 18, 0, GH, 5, 1.6, sid=gid))
    emit_switch(f, gid, "stroke", [(1.6, 3.0), (8.7, 9.5)], f.t["hi"], f.t["edge"], 0.25)
    cells = [(i, j) for j in range(4) for i in range(6)]
    denied = {(5, 3), (4, 3)}
    used = {0: (1, 0), 1: (3, 1), 2: (5, 3)}
    for (i, j) in cells:
        p = C.P(gx - 12.5 + i * 5, gy - 7.5 + j * 5, GH)
        cls = "dotl" if (i, j) in denied else "dotm"
        did = f.uid("d")
        f.raw(dot(p, cls, 1.15, did))
        for k, (i2, j2) in used.items():
            if (i, j) == (i2, j2):
                t_hit = req[k][0] + 0.7
                emit_switch(f, did, "fill", [(t_hit, t_hit + 0.5)],
                            f.t["sig"] if req[k][1] else f.t["hi"], f.t["lo"] if cls == "dotl" else f.t["edge"], 0.15)

    # the app
    ax, ay = W(AP, 0)
    pid = f.uid("s")
    app = solid_uv(f, C, AP, 0, 24, 24, 0, AH, 5, 1.6, sid=pid)
    q = C.P(ax + 24 * 0.55, ay + 24, AH * 0.5)
    app += f'<circle cx="{r2(q[0])}" cy="{r2(q[1])}" r="1.7" class="sigf"/>'
    a, b = C.P(ax + 24, ay - 24 * 0.55, AH * 0.55), C.P(ax + 24, ay + 24 * 0.1, AH * 0.55)
    app += f'<path d="{seg(a, b)}" class="nf lo"/>'
    f.raw(app)
    emit_switch(f, pid, "stroke", [(t + 1.75, t + 2.3) for (t, ok) in req if ok], f.t["hi"], f.t["edge"], 0.2)

    # the requests
    for (t, ok) in req:
        f.raw(packet(f, [sb_r, gt_l], [(t, t + 0.7)], 2.1))
        if ok:
            f.raw(packet(f, [gt_r, ap_l], [(t + 1.0, t + 1.75)], 2.1))
        else:
            f.raw(packet(f, [gt_l, sb_r], [(t + 1.0, t + 1.8)], 2.1, "dot"))

    items = [(0, 1.6, "hermes · own vm"), (1.6, 3.0, "mcp · 22 of 24 tools"),
             (3.0, 5.5, "read · allowed"), (5.5, 8.0, "analyze · allowed"),
             (8.0, 10.2, "publish · denied"), (10.2, dur, "read-only · no keys")]
    f.frame(fig_no, title, caption, items)
    return f.svg()


# ================================================================= services


def services(theme, fig_no="Fig 1.5", title="SERVICES", caption="GO · ONE BINARY, ONE JOB"):
    """Go is what the infrastructure is written in. A build at the back ships
    one static binary to each service in turn: the old one lifts off, the new
    one hops across and lands, and the service is up again with nothing to
    install. Then the services talk."""
    dur = 12.0
    f = Fig(400, 320, theme, dur=dur, label="go services: a build ships one static binary to each service, then they talk")
    C = Cam(45, 0.5, 1.0)
    BU, BV = 0, -60
    SU, SV = [-88, 0, 88], 18
    HW, H = 19, 16
    C.autoscale([W(-88 - 30, SV) + (0,), W(88 + 30, SV) + (0,), W(0, SV + 30) + (0,), W(BU, BV - 20) + (0,),
                 W(BU, BV) + (52,)], 340, 210, 200, 168)
    swaps = [1.8 + 1.4 * k for k in range(3)]

    # the floor run between the services
    corners = [(P(C, u - HW * 1.414, SV, 0), P(C, u + HW * 1.414, SV, 0)) for u in SU]
    for k in range(2):
        f.raw(f'<path d="{seg(corners[k][1], corners[k + 1][0])}" class="nf dash"/>')

    # the build: a low block with a dot code, bright while it ships
    bid = f.uid("s")
    bx, by = W(BU, BV)
    build = solid_uv(f, C, BU, BV, 14, 14, 0, 10, 4, 1.3, sid=bid)
    for q in range(3):
        build += dot(C.P(bx - 5 + q * 5, by + 5 - q * 5, 10), "dotm", 1.1)
    f.raw(build)
    emit_switch(f, bid, "stroke", [(1.3, swaps[-1] + 0.9)], f.t["hi"], f.t["edge"])

    def slab(u, z, sid=None):
        x, y = W(u, SV)
        ring, inner = rings(x - 12, y - 12, x + 12, y + 12, 3, 1.1)
        sil, cr = prism(C, ring, inner, z, z + 3.5)
        i = f' id="{sid}"' if sid else ""
        return f'<path d="{sil}" class="sil"{i}/><path d="{cr}" class="nf cr"/>'

    for k, u in enumerate(SU):
        x, y = W(u, SV)
        body = solid_uv(f, C, u, SV, HW, HW, 0, H, 5, 1.6)
        a, b = C.P(x + HW, y - HW * 0.55, H * 0.5), C.P(x + HW, y + HW * 0.1, H * 0.5)
        body += f'<path d="{seg(a, b)}" class="nf lo"/>'
        q = C.P(x + HW * 0.55, y + HW, H * 0.5)
        lid_ = f.uid("l")
        body += f'<circle id="{lid_}" cx="{r2(q[0])}" cy="{r2(q[1])}" r="1.7" class="sigf"/>'
        f.raw(body)
        t = swaps[k]
        emit_switch(f, lid_, "fill", [(t, t + 0.9)], f.t["lo"], f.t["sig"], 0.15)
        # the binary it runs now: lifts off and fades when the new one ships
        old = Track(0.0).to(t, 12.0, 0.45, E_IN).to(dur - 0.05, 0.0, 0.01, E_LIN)
        f.raw(wrap(f, slab(u, H), move=lambda tt, old=old: C.d(0, 0, old.at(tt)), show=[(-1.0, t)], fade=0.45))

    # the new binaries, in flight from the build to each service
    for k, u in enumerate(SU):
        t = swaps[k]
        start = P(C, BU, BV, 10)
        end = P(C, u, SV, H)
        a0 = (start[0] - end[0], start[1] - end[1])
        arc = hop(a0, (0.0, 0.0), 46)

        def pos(tt, t=t, arc=arc, a0=a0):
            if tt < t:
                return (0.0, 0.0)      # hidden: parked on its lid until it ships
            if tt < t + 0.25:
                return a0
            if tt < t + 1.0:
                return arc(E_GLIDE((tt - t - 0.25) / 0.75))
            return (0.0, 0.0)
        sid = f.uid("s")
        f.raw(wrap(f, slab(u, H, sid), move=pos, show=[(t + 0.15, dur - 0.02)], fade=0.15, hidden_at_rest=True))
        emit_switch(f, sid, "stroke", [(t + 0.25, t + 1.5)], f.t["hi"], f.t["edge"], 0.25)

    # traffic between the services once they are up, and a little before
    bursts = [0.2, 6.4, 7.6, 8.8, 10.0]
    for k in range(2):
        f.raw(packet(f, [corners[k][1], corners[k + 1][0]], [(b + 0.35 * k, b + 0.35 * k + 0.7) for b in bursts], 1.9))

    items = [(0, 1.3, "go · services running"), (1.3, 2.8, "go build · one static binary"),
             (2.8, 6.2, "deploy · nothing to install"), (6.2, 9.0, "service → service"),
             (9.0, dur, "one binary, one job")]
    f.frame(fig_no, title, caption, items)
    return f.svg()


# ================================================================= pipeline


def pipeline(theme, rows, readouts, foot=None, fig_no="Fig 2.1", title="METHOD",
             caption="HOW AN IDEA BECOMES A SYSTEM", label="an idea moving through research, build, test and scale"):
    """A belt that steps one crate at a time past four stations: a dish that
    listens for a signal, a gate that picks one approach out of many, a gate
    that scans what was built, and an exit into a grid of slots where it is
    put to work. One crate is bright; the table and the read-out follow it.
    rows: four [number, stage, what] rows; readouts: four short lines."""
    N, STEP_MOVE, STEP_HOLD = 8, 0.75, 0.85
    PER = STEP_MOVE + STEP_HOLD
    dur = N * PER
    f = Fig(820, 320, theme, dur=dur, label=label)
    C = Cam(45, 0.5, 1.0)
    PITCH, BW, CH, CW = 34.0, 15.0, 12.0, 8.0
    L = (N - 1) * PITCH
    G1, G2 = 2, 5                         # the slots under each gate
    C.autoscale([(-30, -BW - 30, 0), (L + 40, BW + 8, 0), (-30, BW + 8, 0), (L + 40, -BW - 8, 0),
                 (G1 * PITCH, 0, 46), (-14, -BW - 26, 52)], 470, 226, 272, 166)

    def progress(t):
        """Slots advanced by time t: steps of glide, then a hold."""
        k = int(t // PER)
        fr = (t - k * PER) / STEP_MOVE
        return k + (E_GLIDE(fr) if fr < 1 else 1.0)

    # the belt: a long plank, and rollers at each end
    ring, inner = rings(-22, -BW, L + 22, BW, 6, 1.6)
    f.raw(f.solid(*prism(C, ring, inner, -5, 0)))
    for k in range(N):
        a, b = C.P(k * PITCH + PITCH / 2, -BW + 1.5, 0), C.P(k * PITCH + PITCH / 2, BW - 1.5, 0)
        f.raw(f'<path d="{seg(a, b)}" class="nf lo"/>')

    # the dish, behind the start of the belt, watching
    f.raw(_dish(f, C, -10, -BW - 26, 0))

    def gate_back(g):
        x = g * PITCH
        return _post(C, x, -BW - 5, 44)

    def gate_front(g, kind):
        x = g * PITCH
        out = _post(C, x, BW + 5, 44)
        ring, inner = rings(x - 3, -BW - 8, x + 3, BW + 8, 2.4, 1.0)
        sil, cr = prism(C, ring, inner, 40, 46)
        out += f'<path d="{sil}" class="sil"/><path d="{cr}" class="nf cr"/>'
        return out

    f.raw(gate_back(G1) + gate_back(G2))

    # crates
    crate_win = {}
    for i in range(N):
        def slot(t, i=i):
            return (i + progress(t)) % N

        def pos(t, i=i):
            s = slot(t)
            if s > N - 1:              # leaving the end: lift away
                u = s - (N - 1)
                return C.d((N - 1) * PITCH + u * PITCH * 0.5, 0, 16 * E_OUT(u))
            if s < 0.0001 or (progress(t) % 1 == 1.0 and s % N == 0):
                pass
            return C.d(s * PITCH, 0, 0)

        # visibility: hidden while it leaves the end and until it has dropped onto slot 0
        def drop(t, i=i):
            s = slot(t)
            if s > N - 1:
                u = s - (N - 1)
                return C.d((N - 1) * PITCH + u * PITCH * 0.5, 0, 16 * E_OUT(u))
            if s == 0 or s < 1e-9:
                # resting at slot 0: it fell in at the start of this hold
                th = (t % PER) - STEP_MOVE
                z = 18 * (1 - E_OUT(clamp(th / 0.5, 0, 1))) if th >= 0 else 0.0
                return C.d(0, 0, z)
            return C.d(s * PITCH, 0, 0)

        # the times this crate reaches each slot (start of the hold there)
        def reach(slot_no, i=i):
            return ((slot_no - i - 1) % N) * PER + STEP_MOVE

        # marks: a dot code after the route gate, a bar after the render gate
        t_route = reach(G1) + 0.35
        t_render = reach(G2) + 0.35
        t_leave = reach(N - 1) + STEP_HOLD - 0.05
        t_in = reach(0)
        if t_leave < t_in:
            t_leave += dur
        if t_route < t_in:
            t_route += dur
        if t_render < t_in:
            t_render += dur
        bright = i == 0
        sid = f.uid("s")
        ring, inner = rings(-CW, -CW, CW, CW, 2.6, 1.1)
        sil, cr = prism(C, ring, inner, 0, CH)
        body = f'<path d="{sil}" class="sil{" hi" if bright else ""}" id="{sid}"/><path d="{cr}" class="nf cr"/>'
        codes = [(i * 3) % 4 + 1]
        dots = ""
        for q in range(codes[0]):
            p = C.P(-4.5 + q * 3, 3, CH)
            dots += dot(p, "dotm" if not bright else "dot", 0.95)
        mid = C.P(CW, -CW * 0.5, CH * 0.5), C.P(CW, CW * 0.5, CH * 0.5)
        bar = f'<path d="{seg(*mid)}" class="nf sil"/>'
        body += wrap(f, dots, show=[(t_route, t_leave)], fade=0.25, hidden_at_rest=level(0, [(t_route, t_leave)], 0.25, dur) < 0.5)
        body += wrap(f, bar, show=[(t_render, t_leave)], fade=0.25, hidden_at_rest=level(0, [(t_render, t_leave)], 0.25, dur) < 0.5)
        f.raw(wrap(f, body, move=drop, show=[(t_in, t_leave)], fade=0.3, tol=0.1,
                   hidden_at_rest=level(0, [(t_in, t_leave)], 0.3, dur) < 0.5))
        if bright:
            crate_win = dict(route=t_route, render=t_render, leave=t_leave, t_in=t_in)

    f.raw(gate_front(G1, "route") + gate_front(G2, "render"))

    # the first gate's selector: fourteen ticks along its bar, a signal that jumps between them
    x1 = G1 * PITCH
    ticks = [C.P(x1 + 3, -BW - 6 + (2 * BW + 12) * (k + 0.5) / 14, 46) for k in range(14)]
    for p in ticks:
        f.raw(dot(p, "dotl", 0.8))
    choices = [((i * 3) % 4 * 3 + i) % 14 for i in range(N)]
    sel0 = ticks[choices[0]]

    def sel(t):
        k = int(t // PER)
        th = (t - k * PER) - STEP_MOVE
        c = choices[(k - 1) % N] if th < 0.3 else choices[k % N]
        p = ticks[c]
        return (p[0] - sel0[0], p[1] - sel0[1])
    f.raw(wrap(f, f'<circle cx="{r2(sel0[0])}" cy="{r2(sel0[1])}" r="1.6" class="sigf"/>', move=sel, tol=0.2))

    # the second gate's scan: a plane that sweeps down through the crate in each hold
    x2 = G2 * PITCH
    scan_ring = rrect(x2 - 2, -BW - 4, x2 + 2, BW + 4, 1.5)
    scan = f'<path d="{poly(ring_at(C, scan_ring, 38))}" class="nf sig"/>'
    holds = [(k * PER + STEP_MOVE + 0.05, k * PER + STEP_MOVE + 0.75) for k in range(N)]

    def sweep(t):
        for (a, b) in holds:
            if a <= t <= b:
                return C.d(0, 0, -36 * E_GLIDE((t - a) / (b - a)))
        return (0.0, 0.0)
    f.raw(wrap(f, scan, move=sweep, show=[(a, b - 0.1) for a, b in holds], fade=0.1, hidden_at_rest=True, tol=0.15))

    # the exit: a grid of slots, one lighting as each crate is put to work
    cal = (L + 30, BW + 26)
    cring, cinner = rings(cal[0] - 16, cal[1] - 11, cal[0] + 16, cal[1] + 11, 4, 1.3)
    f.raw(f.solid(*prism(C, cring, cinner, 0, 3)))
    cells = [(cal[0] - 12 + c * 4, cal[1] - 6 + r * 6) for r in range(3) for c in range(7)]
    for k, (cx, cy) in enumerate(cells):
        did = f.uid("d")
        f.raw(dot(C.P(cx, cy, 3), "dotl", 1.0, did))
        posts = [i for i in range(N) if (i * 5) % len(cells) == k]
        wins = [(((N - 1 - i) % N) * PER + STEP_MOVE + STEP_HOLD, ((N - 1 - i) % N) * PER + STEP_MOVE + STEP_HOLD + 1.2) for i in posts]
        if wins:
            emit_switch(f, did, "fill", wins, f.t["sig"], f.t["lo"], 0.2)

    cw = crate_win
    marks = [cw["t_in"] - 0.1, cw["route"] - 0.35, cw["render"] - 0.35, cw["leave"] - STEP_HOLD, cw["t_in"] - 0.1 + dur]
    marks = [marks[0]] + [m if m >= marks[0] else m + dur for m in marks[1:]]
    stages = [[(marks[k], marks[k + 1])] for k in range(4)]
    f.raw(legend(f, 548, 116, rows, [30, 70, 150], stages, head=["#", "stage", "what"],
                 foot=(["", foot], None) if foot else None))
    items = [(w[0][0], w[0][1], txt) for w, txt in zip(stages, readouts)]
    f.frame(fig_no, title, caption, items)
    return f.svg()


def _post(C, x, y, h):
    ring, inner = rings(x - 2.6, y - 2.6, x + 2.6, y + 2.6, 1.6, 0.8)
    sil, cr = prism(C, ring, inner, 0, h)
    return f'<path d="{sil}" class="sil"/>'


def _dish(f, C, x, y, z):
    """A parabolic dish on a mast behind the start of the belt, turned up and
    away toward what it watches."""
    def norm(v):
        m = math.sqrt(sum(c * c for c in v))
        return tuple(c / m for c in v)

    def cross(a, b):
        return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
    n = norm((-0.55, 0.45, 0.72))          # where it points: up, back along the belt, a little toward us
    e1 = norm(cross(n, (0, 0, 1)))
    e2 = cross(n, e1)
    R, depth, cz = 15.0, 6.0, 34.0
    c = (x, y, cz)

    def circle(scale, back, k=48):
        pts = []
        for i in range(k):
            a = i / k * math.tau
            pts.append(C.P(*(c[j] + scale * R * (math.cos(a) * e1[j] + math.sin(a) * e2[j]) - n[j] * back for j in range(3))))
        return pts
    rim, bowl = circle(1.0, 0.0), circle(0.5, depth)
    hub = tuple(c[j] - n[j] * depth for j in range(3))
    out = _post(C, x, y, hub[2] - 1.5)
    out += f'<path d="{poly(hull(rim + bowl))}" class="sil"/>'
    out += f'<path d="{poly(rim)}" class="nf cr"/>'
    foc = tuple(c[j] + n[j] * 12 for j in range(3))
    for a in (0.25, 0.58, 0.92):
        q = tuple(c[j] + R * (math.cos(a * math.tau) * e1[j] + math.sin(a * math.tau) * e2[j]) for j in range(3))
        out += f'<path d="{seg(C.P(*q), C.P(*foc))}" class="nf cr"/>'
    p = C.P(*foc)
    out += f'<circle cx="{r2(p[0])}" cy="{r2(p[1])}" r="1.8" class="sigf"/>'
    return out


# ================================================================= hero


def portrait_card(theme, portrait_svg, fig_no="Fig 0.1", title="OPERATOR", caption="ASCII · ONE PHOTO, 72 COLUMNS",
                  readout="mikkel"):
    """The ASCII portrait exactly as make_portrait.py draws it, row-by-row
    reveal and green cursor included, set on a card so it sits beside the
    spec card. Only its ink is fixed to one theme, so it follows the reader's
    GitHub theme instead of their OS."""
    import re
    f = Fig(400, 480, theme, dur=10.0, label="ascii portrait of mikkel")
    head, body = portrait_svg.split(">", 1)
    body = body.rsplit("</svg>", 1)[0]
    vb = re.search(r'viewBox="([^"]+)"', head).group(1)
    vw, vh = [float(v) for v in vb.split()[2:]]
    ink = "#c9d1d9" if theme == "dark" else "#30363d"
    body = re.sub(r"\.i\{fill:[^}]*\}\.c\{fill:([^}]*)\}@media\(prefers-color-scheme:dark\)\{\.i\{fill:[^}]*\}\}",
                  lambda m: f".i{{fill:{ink}}}.c{{fill:{m.group(1)}}}", body)
    # its clip ids would collide with ids of this card
    body = re.sub(r'id="r(\d+)"', r'id="pr\1"', body).replace("url(#r", "url(#pr")
    font = re.search(r'font-family="([^"]+)"', head).group(1)
    # the card's own text rule must not reach the portrait: it is drawn in
    # its own embedded face, whose ramp was measured glyph by glyph
    f.css_rule(f".pt text{{font-family:{font}}}")
    top, bottom = 38, 40
    hgt = 480 - top - bottom
    w = vw * hgt / vh
    f.raw(f'<svg class="pt" x="{r2((400 - w) / 2)}" y="{top}" width="{r2(w)}" height="{r2(hgt)}" viewBox="{vb}" '
          f'font-family="{font}" font-size="8.0">{body}</svg>')
    f.frame(fig_no, title, caption, readout=readout)
    return f.svg()


def id_card(theme, name, tagline, facts, fig_no="Fig 0.2", title="SPEC", caption="RESEARCH · BUILD · SCALE"):
    """Who, in a few lines, over a small phosphor display that plays the
    studio's method: a scan (research), bricks laid row by row (build), bars
    that climb (scale). The lines read in once; the display loops."""
    dur = 9.6
    f = Fig(400, 480, theme, dur=dur, label=f"{name}: {tagline}")
    x0 = 30
    out = f'<text x="{x0}" y="96" class="name">{name}</text>'
    f.text += name
    out += f.label_text(x0 + 2, 120, tagline, "lab tag")
    kw = max(len(k) for k, _ in facts)
    y = 168
    for i, (k, v) in enumerate(facts):
        line = f.label_text(x0 + 2, y, k, "lab tag") + f.label_text(x0 + 2 + (kw + 2) * 6.3, y, v, "lab val")
        out += f'<g class="rv" style="animation-delay:{0.25 + 0.1 * i:.2f}s">{line}</g>'
        y += 22
    f.raw(out)
    f.css_rule(f".name{{font-size:40px;letter-spacing:-.01em;fill:{f.t['hi']}}}")
    f.css_rule(f".tag{{fill:{f.t['edge']}}}.val{{fill:{f.t['hi']};opacity:.82}}")
    f.css_rule("@keyframes rv{from{opacity:0;transform:translate(-6px,0)}to{opacity:1;transform:none}}"
               ".rv{opacity:0;animation:rv .7s cubic-bezier(.32,.72,0,1) forwards}"
               "@media (prefers-reduced-motion:reduce){.rv{animation:none!important;opacity:1}}")

    # the display: an upright panel on a small stand
    C = Cam(45, 0.5, 1.0)
    C.autoscale([W(-70, 0) + (8,), W(70, 0) + (56,), W(0, 18) + (0,), W(0, -18) + (0,)], 270, 118, 200, 368)
    f.raw(plank_uv(C, -24, -15, 24, 15, 0, 4, 4, 1.2))
    f.raw(plank_uv(C, -5, -3, 5, 3, 4, 10, 2, 0.8))
    f.raw(plank_uv(C, -70, -8, 70, 8, 10, 56, 5, 1.4))
    cols, rows = 18, 6
    us = [-58 + c * (116 / (cols - 1)) for c in range(cols)]
    zs = [16 + r * (34 / (rows - 1)) for r in range(rows)]
    hts = [1 + round(5 * (c / (cols - 1)) ** 1.5) for c in range(cols)]
    for c in range(cols):
        for r in range(rows):
            p = P(C, us[c], 8.2, zs[r])
            wins = []
            # research: a column sweeps across, twice
            for sweep in range(2):
                t = 0.3 + sweep * 1.4 + c * (1.25 / cols)
                wins.append((t, t + 0.12))
            # build: bricks laid from the bottom row up
            t = 3.4 + (r * cols + c) * (2.3 / (cols * rows))
            wins.append((t, 6.2))
            # scale: bars climb, left to right
            if r < hts[c]:
                wins.append((6.5 + c * 0.07 + r * 0.06, 9.2))
            did = f.uid("d")
            f.raw(dot(p, "dotl", 1.35, did))
            emit_switch(f, did, "fill", wins, f.t["hi"], f.t["lo"], 0.12)
    f.frame(fig_no, title, caption, [(0, 3.2, "research."), (3.2, 6.4, "build."), (6.4, dur, "scale.")])
    return f.svg()
