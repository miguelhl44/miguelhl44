#!/usr/bin/env python3
"""Draw the three hand-written graphics at the top of the README.

    python3 scripts/make_profile.py

Standard library only. Unlike generate_stats.py these are not fed by an API,
they are fed by the CONFIG block below — so this runs when you change what it
says about you, not on a schedule.

  boot.svg    a boot console that plays as the page opens
  whoami.svg  a terminal window that types out who you are
  infra.svg   the homelab as a topology, with traffic still moving on it
              after the diagram has finished drawing

Motion is SMIL for the same reason as everywhere else here: GitHub strips
<script> from READMEs, but an SVG loaded through <img> animates fine.

Two rules keep this honest. Nothing on the page is a fake measurement — no
invented CPU percentages, no "1,247 workflows" — because a number that looks
live and isn't is worse than no number. And the guest count under the node is
derived from SERVICES rather than typed in, so the label cannot drift from the
tiles actually drawn next to it.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# ==================================================================
# CONFIG — this is the part to edit. Everything below just draws it.
# ==================================================================

USER = "miguelhl44"
HOST = "homelab"

# The identity card. Keys are padded to the longest one automatically.
FACTS = [
    ("role", "bootstrapper · marketing + it"),
    ("studying", "business economics & it"),
    ("building", "automations, sites, small sharp tools"),
    ("homelab", "proxmox ve · zfs · docker"),
    ("location", "denmark"),
]

# The boot console. Each line is (label, is_final_target).
BOOT = [
    ("mounting /dev/curiosity", False),
    ("loading business-economics + it", False),
    ("starting marketing-ops.service", False),
    ("starting bootstrapper.target", False),
    ("bringing up proxmox-ve", False),
    ("starting n8n automation runner", False),
    ("mounting zfs pool + backups", False),
    ("reached target ship-something-today", True),
]

# The topology. EDIT ME: these are plausible homelab defaults, not a scan of
# your rack — swap them for what you actually run. The node's guest count is
# computed from SERVICES, so adding a tile updates the label with it.
EDGE = ("internet", "opnsense · firewall")
NODE = ("pve-01", "proxmox ve")
SERVICES = [
    ("n8n", "automation"),
    ("docker", "runtime"),
    ("nginx", "reverse proxy"),
    ("postgres", "data"),
    ("grafana", "dashboards"),
    ("uptime-kuma", "monitoring"),
    ("wireguard", "vpn"),
    ("adguard", "dns"),
]
STORAGE = ("zfs pool", "snapshots + offsite backup")

# The stack, as a funnel: every tool lands in the lane it actually runs in,
# and both lanes sit on the one machine. "vm" and "ct" are the only valid
# lanes — a tool tagged anything else would silently vanish, so they are
# checked at build time rather than quietly dropped.
WORKSTATION = "vscode"          # what the ssh session is opened from
TOOLS = [
    ("go", "vm"),
    ("python", "vm"),
    ("typescript", "vm"),
    ("terraform", "vm"),
    ("git", "vm"),
    ("n8n", "ct"),
    ("mcp servers", "ct"),
    ("docker", "ct"),
    ("postgres", "ct"),
    ("nginx", "ct"),
]
LANES = [
    ("vm", "VM", "dev", "own kernel · full isolation"),
    ("ct", "CT", "services", "lxc · shared kernel"),
]

# Buttons under the topology. Each is its own file because a link has to wrap
# the whole image: an SVG loaded through <img> is a picture, not a document,
# so <a> inside it never fires and one big diagram can only ever have one
# destination. The key doubles as the anchor it jumps to in the README.
NAV = [
    ("guests", "vm / ct split"),
    ("storage", "storage & backups"),
    ("access", "network & access"),
    ("why", "why self-host"),
]

# The two reader tracks. (anchor, title, subtitle, accent class)
TRACKS = [
    ("projects", "how i run work", "kanban · version control · shipping",
     "acc"),
    ("building", "how i build it", "proxmox · go · terraform · mcp", "warn"),
]

# EDIT ME: the board is illustrative — put real work items here.
BOARD = [
    ("backlog", ["landing page copy", "invoice automation"]),
    ("doing", ["n8n → crm sync"]),
    ("review", ["pve backup job"]),
    ("done", ["dns migration", "lxc tf module"]),
]
CARD_IN_FLIGHT = "weekly report bot"

GIT_MAIN = "main"
GIT_BRANCH = "feat/backup-job"

# ==================================================================

WIDTH = 620
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
CW = 0.6                      # monospace advance width, em

LIGHT = dict(ink="#1f2328", mut="#59636e", fnt="#818b98", lin="#d1d9e0",
             acc="#1a7f37", warn="#bc4c00", pane="#f6f8fa", chip="#eaeef2")
DARK = dict(ink="#f0f6fc", mut="#9198a1", fnt="#6e7681", lin="#3d444d",
            acc="#3fb950", warn="#db6d28", pane="#161b22", chip="#21262d")


# ---------------------------------------------------------------- helpers

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def palette(t):
    return (f".ink{{fill:{t['ink']}}}.mut{{fill:{t['mut']}}}"
            f".fnt{{fill:{t['fnt']}}}.acc{{fill:{t['acc']}}}"
            f".warn{{fill:{t['warn']}}}.pane{{fill:{t['pane']}}}"
            f".chip{{fill:{t['chip']}}}"
            f".ls{{stroke:{t['lin']}}}.as{{stroke:{t['acc']}}}")


def svg_open(w, h, extra=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" '
            f'height="{h}" viewBox="0 0 {w} {h}" font-family="{MONO}">'
            f"<style>{palette(LIGHT)}{extra}"
            f"@media(prefers-color-scheme:dark){{{palette(DARK)}}}</style>")


def text(x, y, body, size=12, cls="mut", anchor=None, weight=None,
         spacing=None, preserve=False):
    a = f' text-anchor="{anchor}"' if anchor else ""
    a += f' font-weight="{weight}"' if weight else ""
    a += f' letter-spacing="{spacing}"' if spacing else ""
    a += ' xml:space="preserve"' if preserve else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" '
            f'font-size="{size}"{a}>{body}</text>')


def fade(begin, dur=0.32):
    return (f'<animate attributeName="opacity" from="0" to="1" '
            f'begin="{begin:.2f}s" dur="{dur:.2f}s" fill="freeze"/>')


def appear(body, begin, dur=0.32):
    return f'<g opacity="0">{fade(begin, dur)}{body}</g>'


def slide_in(body, begin, dx=-8, dur=0.34):
    """Fade plus a short travel — reads as arriving rather than blinking on."""
    return (f'<g opacity="0" transform="translate({dx},0)">{fade(begin, dur)}'
            f'<animateTransform attributeName="transform" type="translate" '
            f'from="{dx} 0" to="0 0" begin="{begin:.2f}s" dur="{dur:.2f}s" '
            f'fill="freeze" calcMode="spline" keySplines="0.2 0.8 0.2 1"/>'
            f"{body}</g>")


def typed(uid, x, y, size, spans, begin, cps=30, weight=None):
    """Types a line one character at a time, cursor riding the caret.

    The reveal is a discrete-step clip rather than a smooth one so characters
    land whole instead of being sliced down the middle mid-glyph.
    """
    full = "".join(t for t, _ in spans)
    n = max(len(full), 1)
    cw = size * CW
    dur = n / cps
    stops = [i * cw for i in range(n + 1)]
    values = ";".join(f"{v:.1f}" for v in stops)
    keys = ";".join(f"{i / n:.4f}" for i in range(n + 1))
    end = begin + dur
    w_attr = f' font-weight="{weight}"' if weight else ""
    tspans = "".join(f'<tspan class="{c}">{esc(t)}</tspan>' for t, c in spans)
    xs = ";".join(f"{x + v:.1f}" for v in stops)
    body = (
        f'<clipPath id="{uid}"><rect x="{x:.1f}" y="{y - size * 1.05:.1f}" '
        f'width="0" height="{size * 1.45:.1f}">'
        f'<animate attributeName="width" calcMode="discrete" values="{values}" '
        f'keyTimes="{keys}" begin="{begin:.2f}s" dur="{dur:.2f}s" '
        f'fill="freeze"/></rect></clipPath>'
        f'<g clip-path="url(#{uid})"><text x="{x:.1f}" y="{y:.1f}" '
        f'font-size="{size}"{w_attr} xml:space="preserve">{tspans}</text></g>'
        f'<rect x="{x:.1f}" y="{y - size * 0.8:.1f}" width="{cw * 0.9:.1f}" '
        f'height="{size:.1f}" class="acc" opacity="0">'
        f'<set attributeName="opacity" to="0.7" begin="{begin:.2f}s"/>'
        f'<animate attributeName="x" calcMode="discrete" values="{xs}" '
        f'keyTimes="{keys}" begin="{begin:.2f}s" dur="{dur:.2f}s" '
        f'fill="freeze"/>'
        f'<set attributeName="opacity" to="0" begin="{end:.2f}s"/></rect>')
    return body, end


def caret(x, y, size, begin):
    return (f'<rect x="{x:.1f}" y="{y - size * 0.8:.1f}" '
            f'width="{size * CW * 0.9:.1f}" height="{size:.1f}" class="acc" '
            f'opacity="0"><animate attributeName="opacity" '
            f'calcMode="discrete" values="1;0" keyTimes="0;0.5" dur="1.06s" '
            f'begin="{begin:.2f}s" repeatCount="indefinite"/></rect>')


def panel(x, y, w, h, cls="pane", r=8, stroke="ls", sw=1):
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'rx="{r}" class="{cls} {stroke}" stroke-width="{sw}"/>')


# ---------------------------------------------------------------- boot.svg

def draw_boot():
    """A boot console: phosphor flash, then services reporting in."""
    FS, LH, PAD = 12.5, 19.0, 4.0
    COLS = 74                       # line width in characters
    STATUS = "[  OK  ]"
    lead_in, step = 0.45, 0.17

    lines = [("", f"{USER} — cold boot", None)]
    t = 0.118
    for label, final in BOOT:
        lines.append((f"[ {t:.3f} ] ", label, "final" if final else "ok"))
        t += 0.137

    height = PAD * 2 + (len(lines) + 2.6) * LH
    out = [svg_open(WIDTH, height)]

    # power-on: a hairline at the centre that opens to full height and fades
    out.append(
        f'<rect x="0" y="{height / 2:.1f}" width="{WIDTH}" height="2" '
        f'class="acc" opacity="0.55">'
        f'<animate attributeName="y" from="{height / 2:.1f}" to="0" '
        f'begin="0s" dur="0.30s" fill="freeze"/>'
        f'<animate attributeName="height" from="2" to="{height:.1f}" '
        f'begin="0s" dur="0.30s" fill="freeze"/>'
        f'<animate attributeName="opacity" from="0.55" to="0" begin="0s" '
        f'dur="0.42s" fill="freeze"/></rect>')

    for i, (stamp, label, kind) in enumerate(lines):
        y = PAD + LH * (i + 1)
        begin = lead_in + i * step
        if kind is None:
            out.append(slide_in(
                text(0, y, f'<tspan class="fnt">{esc(stamp)}</tspan>'
                           f'<tspan class="ink">{esc(label)}</tspan>',
                     FS, "ink", preserve=True, weight="600"), begin))
            continue

        # leader dots pad to a fixed character column, so the status lines up
        # no matter how wide the viewer's monospace actually is
        room = COLS - len(stamp) - len(STATUS) - 1
        dots = "." * max(room - len(label) - 1, 1)   # -1 keeps a gap
        body = (f'<tspan class="fnt">{esc(stamp)}</tspan>'
                f'<tspan class="ink">{esc(label)}</tspan>'
                f'<tspan class="fnt"> {dots}</tspan>')
        out.append(slide_in(text(0, y, body, FS, "mut", preserve=True), begin))

        sx = (COLS - len(STATUS)) * FS * CW
        cls = "warn" if kind == "final" else "acc"
        out.append(
            f'<g opacity="0" transform="translate({sx:.1f},{y:.1f})">'
            f'{fade(begin + 0.13, 0.16)}'
            f'<g transform="scale(1)">'
            f'<animateTransform attributeName="transform" type="scale" '
            f'values="0.86;1.06;1" keyTimes="0;0.65;1" '
            f'begin="{begin + 0.13:.2f}s" dur="0.24s" fill="freeze" '
            f'additive="sum"/>'
            f'{text(0, 0, esc(STATUS), FS, cls, weight="600", preserve=True)}'
            f"</g></g>")

    prompt = f"{USER}@{HOST}:~$ "
    py = PAD + LH * (len(lines) + 1.9)
    begin = lead_in + len(lines) * step + 0.15
    out.append(appear(text(0, py, esc(prompt), FS, "mut", preserve=True),
                      begin, 0.2))
    out.append(caret(len(prompt) * FS * CW, py, FS, begin + 0.2))
    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------- whoami.svg

def draw_whoami():
    """A terminal window whose contents type themselves in."""
    FS, LH = 13.0, 22.0
    BAR, PAD = 30.0, 16.0
    height = BAR + PAD * 2 + (len(FACTS) + 1) * LH + 6
    keyw = max(len(k) for k, _ in FACTS) + 2

    out = [svg_open(WIDTH, height)]
    out.append(panel(0.5, 0.5, WIDTH - 1, height - 1))
    out.append(f'<path d="M0.5 {BAR:.1f}H{WIDTH - 0.5:.1f}" class="ls" '
               f'stroke-width="1"/>')
    for i, colour in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        anim = fade(0.05 + i * 0.06, 0.2)
        out.append(f'<circle cx="{18 + i * 16}" cy="{BAR / 2:.1f}" r="5" '
                   f'fill="{colour}" opacity="0">{anim}</circle>')
    out.append(appear(text(WIDTH / 2, BAR / 2 + 4, esc(f"{USER}@{HOST}: ~"),
                           11.5, "fnt", anchor="middle"), 0.22, 0.25))

    x = PAD
    y = BAR + PAD + FS
    body, t = typed("w0", x, y, FS,
                    [("$ ", "fnt"), ("whoami --long", "ink")], 0.42, cps=24)
    out.append(body)

    for i, (key, value) in enumerate(FACTS):
        y += LH
        body, t = typed(f"w{i + 1}", x, y, FS,
                        [(key.ljust(keyw), "acc"), (value, "mut")],
                        t + 0.14, cps=56)
        out.append(body)

    out.append(caret(x, y + LH, FS, t + 0.2))
    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------- infra.svg

def flow(path, begin, dur=2.6, r=2.6):
    """A packet that keeps running the link after the diagram has settled."""
    return (f'<circle r="{r}" class="acc" opacity="0">'
            f'<animateMotion path="{path}" begin="{begin:.2f}s" '
            f'dur="{dur:.2f}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0;0.95;0.95;0" '
            f'keyTimes="0;0.12;0.85;1" begin="{begin:.2f}s" '
            f'dur="{dur:.2f}s" repeatCount="indefinite"/></circle>')


def link(x1, y1, x2, y2, begin, dur=0.4):
    """A connector that draws itself from one end to the other."""
    length = abs(x2 - x1) + abs(y2 - y1)
    return (f'<path d="M{x1:.1f} {y1:.1f}L{x2:.1f} {y2:.1f}" class="ls" '
            f'stroke-width="1.5" stroke-dasharray="{length:.1f}" '
            f'stroke-dashoffset="{length:.1f}">'
            f'<animate attributeName="stroke-dashoffset" '
            f'from="{length:.1f}" to="0" begin="{begin:.2f}s" '
            f'dur="{dur:.2f}s" fill="freeze"/></path>')


def draw_infra():
    mid = WIDTH / 2
    cols, gap, pad = 4, 10.0, 14.0
    rows = (len(SERVICES) + cols - 1) // cols

    y_net = 16.0                       # internet label baseline
    y_fw = 34.0                        # firewall box top
    fw_h = 34.0
    y_node = y_fw + fw_h + 26          # node panel top
    head_h = 40.0
    tile_h = 38.0
    inner = WIDTH - 2 * 16 - 2 * pad
    tile_w = (inner - gap * (cols - 1)) / cols
    grid_top = y_node + head_h
    node_h = head_h + rows * tile_h + (rows - 1) * gap + pad
    y_store = y_node + node_h + 26
    store_h = 34.0
    height = y_store + store_h + 14

    out = [svg_open(WIDTH, height)]

    # --- trunk links, drawn top to bottom, then packets on top of them
    out.append(link(mid, y_net + 6, mid, y_fw, 0.15))
    out.append(link(mid, y_fw + fw_h, mid, y_node, 0.45))
    out.append(link(mid, y_node + node_h, mid, y_store, 1.55))

    # --- internet
    out.append(appear(text(mid, y_net, "internet", 11, "fnt",
                           anchor="middle", spacing="1.2"), 0.05))

    # --- firewall
    fw_w = 190.0
    out.append(appear(
        panel(mid - fw_w / 2, y_fw, fw_w, fw_h, cls="chip")
        + text(mid, y_fw + 21, esc(EDGE[1]), 12, "ink", anchor="middle"),
        0.28))

    # --- proxmox node
    guests = f"{len(SERVICES)} guests"
    out.append(appear(
        f'<rect x="16.5" y="{y_node + 0.5:.1f}" width="{WIDTH - 33:.1f}" '
        f'height="{node_h - 1:.1f}" rx="10" class="pane" stroke="#e57000" '
        f'stroke-width="1.5" stroke-opacity="0.85"/>'
        + text(16 + pad, y_node + 25, esc(NODE[1]).upper(), 10, "warn",
               weight="600", spacing="1.4")
        + text(WIDTH - 16 - pad, y_node + 25,
               esc(f"{NODE[0]} · {guests} · {STORAGE[0]}"), 10.5, "fnt",
               anchor="end"),
        0.62))

    for i, (name, tag) in enumerate(SERVICES):
        r, c = divmod(i, cols)
        tx = 16 + pad + c * (tile_w + gap)
        ty = grid_top + r * (tile_h + gap)
        begin = 0.9 + i * 0.07
        led = (f'<circle cx="{tx + 11:.1f}" cy="{ty + 13:.1f}" r="3" '
               f'class="acc"><animate attributeName="opacity" '
               f'values="1;0.3;1" dur="{2.2 + (i % 4) * 0.45:.2f}s" '
               f'begin="{begin + 0.4:.2f}s" repeatCount="indefinite"/>'
               f"</circle>")
        out.append(slide_in(
            panel(tx, ty, tile_w, tile_h, cls="chip", r=6)
            + led
            + text(tx + 21, ty + 17, esc(name), 11.5, "ink")
            + text(tx + 21, ty + 29, esc(tag), 9, "fnt"),
            begin, dx=0, dur=0.3))

    # --- storage
    st_w = 260.0
    out.append(appear(
        panel(mid - st_w / 2, y_store, st_w, store_h, cls="chip")
        + text(mid, y_store + 15, esc(STORAGE[0]), 11.5, "ink",
               anchor="middle")
        + text(mid, y_store + 27, esc(STORAGE[1]), 9, "fnt", anchor="middle"),
        1.75))

    # --- traffic: starts once each link exists, then never stops
    out.append(flow(f"M{mid:.1f} {y_net + 6:.1f}L{mid:.1f} {y_fw:.1f}",
                    0.8, 2.2))
    out.append(flow(f"M{mid:.1f} {y_fw + fw_h:.1f}L{mid:.1f} {y_node:.1f}",
                    1.1, 2.2))
    out.append(flow(f"M{mid:.1f} {y_node + node_h:.1f}L{mid:.1f} "
                    f"{y_store:.1f}", 2.2, 3.0))
    out.append(flow(f"M{mid:.1f} {y_store:.1f}L{mid:.1f} "
                    f"{y_node + node_h:.1f}", 3.6, 3.0))

    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------- stack.svg

def chassis(x, y, w, h, begin):
    """The machine itself, drawn as a rack unit: ears, bays, vents, lamps.

    This is the base layer, so it assembles before anything that sits on it.
    """
    p = []
    p.append(f'<rect x="{x + 0.75:.1f}" y="{y + 0.75:.1f}" '
             f'width="{w - 1.5:.1f}" height="{h - 1.5:.1f}" rx="7" '
             f'class="pane" stroke="#e57000" stroke-width="1.5" '
             f'stroke-opacity="0.85"/>')

    # rack ears, with mounting holes — the detail that makes it read as 1U
    for ex in (x + 11, x + w - 11):
        p.append(f'<line x1="{ex:.1f}" y1="{y + 7:.1f}" x2="{ex:.1f}" '
                 f'y2="{y + h - 7:.1f}" class="ls" stroke-width="1"/>')
        for hy in (y + 15, y + h - 15):
            p.append(f'<circle cx="{ex:.1f}" cy="{hy:.1f}" r="2" '
                     f'class="lin ls" fill="none" stroke-width="1"/>')

    # drive bays; each lamp comes up a beat after the one to its left
    bx, bw, bg = x + 24, 26.0, 6.0
    for i in range(4):
        sx = bx + i * (bw + bg)
        p.append(f'<rect x="{sx:.1f}" y="{y + 12:.1f}" width="{bw:.1f}" '
                 f'height="{h - 24:.1f}" rx="3" class="chip ls" '
                 f'stroke-width="1"/>')
        p.append(f'<line x1="{sx + 6:.1f}" y1="{y + h - 19:.1f}" '
                 f'x2="{sx + bw - 6:.1f}" y2="{y + h - 19:.1f}" '
                 f'class="ls" stroke-width="1"/>')
        lamp = begin + 0.45 + i * 0.11
        p.append(f'<circle cx="{sx + 6:.1f}" cy="{y + 18:.1f}" r="2.2" '
                 f'class="acc" opacity="0">'
                 f'<set attributeName="opacity" to="1" '
                 f'begin="{lamp:.2f}s"/>'
                 f'<animate attributeName="opacity" values="1;0.35;1" '
                 f'dur="{2.4 + i * 0.5:.1f}s" begin="{lamp + 0.3:.2f}s" '
                 f'repeatCount="indefinite"/></circle>')

    # wordmark
    tx = bx + 4 * (bw + bg) + 10
    p.append(text(tx, y + 26, "PROXMOX VE", 12, "warn", weight="600",
                  spacing="1.3"))
    p.append(text(tx, y + 42, esc(f"{NODE[0]} · one machine, everything on it"),
                  9.5, "fnt"))

    # ventilation grille
    gx, gy = x + w - 128, y + 14
    dots = "".join(
        f'<circle cx="{gx + c * 7:.1f}" cy="{gy + r * 7:.1f}" r="1.4" '
        f'class="fnt" opacity="0.5"/>'
        for r in range(5) for c in range(9))
    p.append(dots)

    # status lamps
    for i, cls in enumerate(("acc", "acc", "warn")):
        p.append(f'<circle cx="{x + w - 30:.1f}" cy="{y + 16 + i * 12:.1f}" '
                 f'r="2.6" class="{cls}" opacity="0">'
                 f'<set attributeName="opacity" to="0.9" '
                 f'begin="{begin + 0.5 + i * 0.12:.2f}s"/>'
                 f'<animate attributeName="opacity" values="0.9;0.2;0.9" '
                 f'dur="{1.8 + i * 0.7:.1f}s" '
                 f'begin="{begin + 0.9 + i * 0.2:.2f}s" '
                 f'repeatCount="indefinite"/></circle>')

    return (f'<g opacity="0" transform="translate(0,14)">{fade(begin, 0.4)}'
            f'<animateTransform attributeName="transform" type="translate" '
            f'from="0 14" to="0 0" begin="{begin:.2f}s" dur="0.45s" '
            f'fill="freeze" calcMode="spline" keySplines="0.2 0.8 0.2 1"/>'
            + "".join(p) + "</g>")


def draw_stack():
    lanes = {key: (short, role, note) for key, short, role, note in LANES}
    unknown = sorted({lane for _, lane in TOOLS} - set(lanes))
    if unknown:
        raise SystemExit(f"TOOLS references unknown lane(s): {unknown}")

    ssh_x = 20.0
    ws_x, ws_w, ws_y, ws_h = 8.0, 168.0, 6.0, 44.0
    tools_y, chip_h, chip_gap = 60.0, 26.0, 8.0
    lane_h, srv_h = 46.0, 62.0

    cols = [(48.0, 272.0, "vm"), (336.0, 276.0, "ct")]
    lane_box = {"vm": (8.0, 292.0), "ct": (312.0, 300.0)}

    # Everything below the tool grid is derived from how tall that grid ends
    # up. Hardcoding these worked at two rows and silently overlapped at
    # three, so adding a tool must not be able to break the layout.
    rows_max = max((len([1 for _, lane in TOOLS if lane == key]) + 1) // 2
                   for _, _, key in cols)
    bar_y = tools_y + rows_max * (chip_h + chip_gap) - chip_gap + 10
    neck_y = bar_y + 18
    lane_y = neck_y + 6
    srv_y = lane_y + lane_h + 18
    height = srv_y + srv_h + 10
    out = [svg_open(WIDTH, height)]

    # --- base layer first: everything else is drawn as sitting on it
    out.append(chassis(8.0, srv_y, WIDTH - 16, srv_h, 0.05))

    # --- isolation lanes
    for key, (lx, lw) in lane_box.items():
        short, role, note = lanes[key]
        begin = 0.62 + (0.1 if key == "ct" else 0)
        body = (
            f'<rect x="{lx + 0.5:.1f}" y="{lane_y + 0.5:.1f}" '
            f'width="{lw - 1:.1f}" height="{lane_h - 1:.1f}" rx="8" '
            f'class="pane ls" stroke-width="1.2" stroke-dasharray="6 4"/>'
            + text(lx + 16, lane_y + 21, esc(short), 13, "ink", weight="600")
            + text(lx + 16 + len(short) * 13 * CW + 7, lane_y + 21,
                   esc("· " + role), 11.5, "mut")
            + text(lx + 16, lane_y + 35, esc(note), 9, "fnt"))
        out.append(slide_in(body, begin, dx=0))

        # the lane rests on the machine, and work keeps landing on it
        cx = lx + lw / 2
        out.append(link(cx, lane_y + lane_h, cx, srv_y, begin + 0.25, 0.3))
        out.append(flow(f"M{cx:.1f} {lane_y + lane_h:.1f}L{cx:.1f} "
                        f"{srv_y:.1f}", begin + 1.6, 2.8, r=2.3))

    # --- the funnel: a column of tools narrowing to a neck over its lane
    for ci, (cx0, cw, key) in enumerate(cols):
        picked = [name for name, lane in TOOLS if lane == key]
        chip_w = (cw - chip_gap) / 2
        rows = (len(picked) + 1) // 2
        for i, name in enumerate(picked):
            r, c = divmod(i, 2)
            x = cx0 + c * (chip_w + chip_gap)
            y = tools_y + r * (chip_h + chip_gap)
            begin = 1.02 + ci * 0.08 + i * 0.07
            out.append(slide_in(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{chip_w:.1f}" '
                f'height="{chip_h:.1f}" rx="6" class="chip ls" '
                f'stroke-width="1"/>'
                + text(x + chip_w / 2, y + 17, esc(name), 11.5, "ink",
                       anchor="middle"),
                begin, dx=0, dur=0.3))

        lx, lw = lane_box[key]
        neck = lx + lw / 2
        begin = 1.34 + ci * 0.1
        out.append(appear(
            f'<path d="M{cx0:.1f} {bar_y:.1f}'
            f'L{neck - 9:.1f} {neck_y:.1f}H{neck + 9:.1f}'
            f'L{cx0 + cw:.1f} {bar_y:.1f}Z" class="chip" opacity="0.85"/>'
            f'<path d="M{cx0:.1f} {bar_y:.1f}L{neck - 9:.1f} {neck_y:.1f}" '
            f'class="ls" stroke-width="1" fill="none"/>'
            f'<path d="M{cx0 + cw:.1f} {bar_y:.1f}L{neck + 9:.1f} '
            f'{neck_y:.1f}" class="ls" stroke-width="1" fill="none"/>',
            begin, 0.35))
        out.append(link(neck, neck_y, neck, lane_y, begin + 0.2, 0.25))

    # --- the way in: ssh from the workstation, straight into the vm
    out.append(slide_in(
        panel(ws_x, ws_y, ws_w, ws_h, cls="pane", r=7)
        + f'<line x1="{ws_x:.1f}" y1="{ws_y + 16:.1f}" '
          f'x2="{ws_x + ws_w:.1f}" y2="{ws_y + 16:.1f}" class="ls" '
          f'stroke-width="1"/>'
        + "".join(f'<circle cx="{ws_x + 12 + i * 10:.1f}" '
                  f'cy="{ws_y + 8:.1f}" r="2.6" fill="{c}"/>'
                  for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840")))
        + text(ws_x + 14, ws_y + 35, esc(f"{WORKSTATION} · local"), 12, "ink"),
        1.92, dx=0))

    out.append(link(ssh_x, ws_y + ws_h, ssh_x, lane_y, 2.16, 0.4))
    # sits in the corridor below the tool columns, clear of the first chip
    out.append(appear(text(ssh_x + 8, neck_y - 10, "ssh", 9.5, "fnt",
                           spacing="1.2"), 2.5, 0.3))
    ssh_path = f"M{ssh_x:.1f} {ws_y + ws_h:.1f}L{ssh_x:.1f} {lane_y:.1f}"
    out.append(flow(ssh_path, 2.6, 2.4, r=2.4))
    out.append(flow(f"M{ssh_x:.1f} {lane_y:.1f}L{ssh_x:.1f} "
                    f"{ws_y + ws_h:.1f}", 3.8, 2.4, r=2.0))

    out.append("</svg>")
    return "".join(out)


# ------------------------------------------------- switch-*.svg / the tracks

def draw_switch(title, subtitle, accent):
    """One of the two doors into the page.

    A reader here for how I run work and a reader here for what I build want
    different pages, and there is no way to swap content in place — GitHub
    allows no CSS or JS in a README. So the honest version of a "switch" is
    two doors that clearly lead somewhere, which is what this is.
    """
    W, H = 296.0, 92.0
    out = [svg_open(W, H)]
    out.append(f'<rect x="0.75" y="0.75" width="{W - 1.5:.1f}" '
               f'height="{H - 1.5:.1f}" rx="10" class="pane ls" '
               f'stroke-width="1.2"/>')
    # a spine in the track's colour, so the two read as a pair of choices
    out.append(f'<rect x="0.75" y="14" width="3.5" height="{H - 28:.1f}" '
               f'rx="1.75" class="{accent}"/>')
    out.append(text(22, 38, esc(title), 15, "ink", weight="600"))
    out.append(text(22, 58, esc(subtitle), 10.5, "fnt"))

    ax, ay = W - 30, H - 26
    out.append(text(22, ay + 4, "open", 10, accent, weight="600",
                    spacing="0.6"))
    out.append(f'<path d="M{ax - 12:.1f} {ay:.1f}H{ax:.1f}'
               f'M{ax - 4:.1f} {ay - 4:.1f}L{ax:.1f} {ay:.1f}'
               f'L{ax - 4:.1f} {ay + 4:.1f}" class="as" fill="none" '
               f'stroke-width="1.5" stroke-linecap="round" '
               f'stroke-linejoin="round">'
               f'<animateTransform attributeName="transform" '
               f'type="translate" values="0 0;3 0;0 0" keyTimes="0;0.5;1" '
               f'dur="2.6s" begin="0.9s" repeatCount="indefinite"/></path>')
    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------- kanban.svg

def draw_kanban():
    """A board with one card actually crossing it.

    A static board is a picture of a process; a card that moves is the
    process. Only one card travels — four of them would read as noise.
    """
    pad, gap = 8.0, 10.0
    ncol = len(BOARD)
    colw = (WIDTH - pad * 2 - gap * (ncol - 1)) / ncol
    head_y, flight_y, card_h, card_gap = 16.0, 32.0, 32.0, 6.0
    static_y = flight_y + card_h + 14
    depth = max(len(items) for _, items in BOARD)
    height = static_y + depth * (card_h + card_gap) + 6

    xs = [pad + i * (colw + gap) for i in range(ncol)]
    out = [svg_open(WIDTH, height)]

    def card(x, y, w, label, cls="chip", begin=0.0, tone="ink"):
        return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" '
                f'height="{card_h:.1f}" rx="6" class="{cls} ls" '
                f'stroke-width="1"/>'
                + text(x + 11, y + 15, esc(label), 10.5, tone)
                + f'<rect x="{x + 11:.1f}" y="{y + 21:.1f}" '
                  f'width="{min(w * 0.34, 42):.1f}" height="3" rx="1.5" '
                  f'class="fnt" opacity="0.35"/>')

    for i, (name, items) in enumerate(BOARD):
        x = xs[i]
        out.append(appear(
            f'<rect x="{x:.1f}" y="{head_y - 10:.1f}" width="{colw:.1f}" '
            f'height="{height - head_y + 2:.1f}" rx="8" class="pane" '
            f'opacity="0.55"/>'
            + text(x + 11, head_y, name.upper(), 9, "fnt", spacing="1.3")
            + text(x + colw - 11, head_y, str(len(items)), 9, "fnt",
                   anchor="end"),
            0.08 + i * 0.09))
        for j, label in enumerate(items):
            out.append(slide_in(
                card(x + 6, static_y + j * (card_h + card_gap), colw - 12,
                     label),
                0.4 + i * 0.1 + j * 0.08, dx=0, dur=0.3))

    # the card in flight: dwells in each column, then restarts from backlog
    dwell = 1.9
    cycle = dwell * ncol
    stops, keys = [], []
    for i in range(ncol):
        offset = xs[i] - xs[0]
        stops += [f"{offset:.1f} 0", f"{offset:.1f} 0"]
        keys += [f"{i / ncol:.4f}", f"{(i + 0.72) / ncol:.4f}"]
    stops.append("0 0")
    keys.append("1.0000")

    out.append(
        f'<g opacity="0">{fade(1.05, 0.35)}'
        f'<g><animateTransform attributeName="transform" type="translate" '
        f'values="{";".join(stops)}" keyTimes="{";".join(keys)}" '
        f'dur="{cycle:.1f}s" begin="1.4s" repeatCount="indefinite" '
        f'calcMode="spline" '
        f'keySplines="{";".join(["0.4 0 0.2 1"] * (len(stops) - 1))}"/>'
        + card(xs[0] + 6, flight_y, colw - 12, CARD_IN_FLIGHT)
        # sits on the second line, beside the progress bar — level with the
        # title it would otherwise run into
        + f'<circle cx="{xs[0] + colw - 20:.1f}" cy="{flight_y + 22.5:.1f}" '
          f'r="3" class="acc"><animate attributeName="opacity" '
          f'values="1;0.3;1" dur="1.9s" repeatCount="indefinite"/></circle>'
        + "</g></g>")

    out.append("</svg>")
    return "".join(out)


# -------------------------------------------------------------- gitgraph.svg

def draw_gitgraph():
    """main, a branch off it, and the merge back — drawn left to right."""
    H = 108.0
    y_main, y_br = 74.0, 34.0
    x0, x1 = 76.0, WIDTH - 30
    out = [svg_open(WIDTH, H)]

    main_dots = [x0 + i * 84 for i in range(6)]
    fork_x, merge_x = main_dots[1], main_dots[4]
    br_dots = [fork_x + 84, fork_x + 168]

    def draw_path(d, begin, dur, length, cls="ls", width=2.0):
        return (f'<path d="{d}" class="{cls}" fill="none" '
                f'stroke-width="{width}" stroke-linecap="round" '
                f'stroke-dasharray="{length:.0f}" '
                f'stroke-dashoffset="{length:.0f}">'
                f'<animate attributeName="stroke-dashoffset" '
                f'from="{length:.0f}" to="0" begin="{begin:.2f}s" '
                f'dur="{dur:.2f}s" fill="freeze"/></path>')

    out.append(appear(text(30, y_main + 4, GIT_MAIN, 10.5, "mut"), 0.05, 0.3))
    out.append(draw_path(f"M{x0:.0f} {y_main:.0f}H{x1:.0f}", 0.15, 1.5,
                         x1 - x0))
    out.append(appear(text(fork_x, y_br - 16, esc(GIT_BRANCH), 10, "acc"),
                      0.75, 0.3))
    out.append(draw_path(
        f"M{fork_x:.0f} {y_main:.0f}C{fork_x + 26:.0f} {y_main:.0f} "
        f"{fork_x + 14:.0f} {y_br:.0f} {fork_x + 40:.0f} {y_br:.0f}"
        f"H{merge_x - 40:.0f}C{merge_x - 14:.0f} {y_br:.0f} "
        f"{merge_x - 26:.0f} {y_main:.0f} {merge_x:.0f} {y_main:.0f}",
        0.55, 1.3, (merge_x - fork_x) + 90, cls="as"))

    for i, cx in enumerate(main_dots):
        begin = 0.25 + i * 0.26
        out.append(f'<circle cx="{cx:.0f}" cy="{y_main:.0f}" r="0" '
                   f'class="pane ls" stroke-width="2">'
                   f'<animate attributeName="r" from="0" to="5.5" '
                   f'begin="{begin:.2f}s" dur="0.22s" fill="freeze"/>'
                   f"</circle>")
    for i, cx in enumerate(br_dots):
        begin = 0.95 + i * 0.3
        out.append(f'<circle cx="{cx:.0f}" cy="{y_br:.0f}" r="0" '
                   f'class="acc"><animate attributeName="r" from="0" '
                   f'to="5" begin="{begin:.2f}s" dur="0.22s" '
                   f'fill="freeze"/></circle>')

    # the merge commit reads differently from an ordinary one
    out.append(f'<circle cx="{merge_x:.0f}" cy="{y_main:.0f}" r="0" '
               f'class="acc"><animate attributeName="r" from="0" to="5.5" '
               f'begin="1.85s" dur="0.25s" fill="freeze"/></circle>')
    out.append(appear(text(merge_x, y_main + 22, "merge", 9, "fnt",
                           anchor="middle"), 2.05, 0.3))
    out.append(appear(text(x1, y_main - 14, "reviewed, then merged", 9, "fnt",
                           anchor="end"), 2.2, 0.3))
    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------- nav-*.svg

NAV_H, NAV_FS = 34.0, 11.0
NAV_PAD, NAV_ARROW = 15.0, 26.0


def nav_width(label):
    """Sized to its own label, so a longer one never crowds the arrow.

    The README omits width= on these images and lets them render at their
    intrinsic size — that way the two can't drift apart when a label changes.
    """
    return round(NAV_PAD * 2 + len(label) * NAV_FS * CW + NAV_ARROW, 1)


def draw_nav(label):
    """One button. It has to look pressable without a hover state to help.

    Nothing inside an <img> receives pointer events, so :hover and SMIL's
    mouseover both do nothing here. The arrow is doing the whole job of
    saying "this goes somewhere", which is why it is drawn rather than
    implied by colour alone.
    """
    w = nav_width(label)
    out = [svg_open(w, NAV_H)]
    out.append(f'<rect x="0.6" y="0.6" width="{w - 1.2:.1f}" '
               f'height="{NAV_H - 1.2:.1f}" rx="{NAV_H / 2:.1f}" '
               f'class="chip ls" stroke-width="1"/>')
    out.append(text(NAV_PAD, NAV_H / 2 + 4, esc(label), NAV_FS, "ink"))
    ax = w - NAV_PAD - 7
    ay = NAV_H / 2
    out.append(f'<path d="M{ax - 4:.1f} {ay:.1f}H{ax + 4:.1f}'
               f'M{ax + 1:.1f} {ay - 3.4:.1f}L{ax + 4.4:.1f} {ay:.1f}'
               f'L{ax + 1:.1f} {ay + 3.4:.1f}" class="as" fill="none" '
               f'stroke-width="1.4" stroke-linecap="round" '
               f'stroke-linejoin="round">'
               f'<animateTransform attributeName="transform" '
               f'type="translate" values="0 0;2.5 0;0 0" keyTimes="0;0.5;1" '
               f'dur="2.4s" begin="1.2s" repeatCount="indefinite"/></path>')
    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------- main

def write(name, svg):
    path = os.path.join(ROOT, name)
    old = ""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            old = f.read()
    if old == svg:
        return f"{name} unchanged"
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    return f"{name} {len(svg) / 1024:.1f} KB"


def main():
    made = [write("boot.svg", draw_boot()),
            write("whoami.svg", draw_whoami()),
            write("stack.svg", draw_stack()),
            write("infra.svg", draw_infra()),
            write("kanban.svg", draw_kanban()),
            write("gitgraph.svg", draw_gitgraph())]
    made += [write(f"switch-{key}.svg", draw_switch(title, sub, accent))
             for key, title, sub, accent in TRACKS]
    made += [write(f"nav-{key}.svg", draw_nav(label)) for key, label in NAV]
    for line in made:
        print(line)


if __name__ == "__main__":
    main()
