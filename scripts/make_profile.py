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
    for line in (write("boot.svg", draw_boot()),
                 write("whoami.svg", draw_whoami()),
                 write("infra.svg", draw_infra())):
        print(line)


if __name__ == "__main__":
    main()
