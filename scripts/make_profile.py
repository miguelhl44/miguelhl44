#!/usr/bin/env python3
"""Draw every figure in the README.

    python3 scripts/make_portrait.py   # only when the photo changes
    python3 scripts/make_profile.py    # everything else

Needs fontTools (the figures embed a subset of JetBrains Mono, because an
SVG loaded through <img> fetches nothing). Everything else is the standard
library.

Each figure is written twice, assets/<name>-dark.svg and -light.svg, and the
README picks one with <picture> and prefers-color-scheme, which GitHub
resolves against the reader's GitHub theme rather than their OS.

The figures are isometric line art (see iso.py): one bright silhouette and
one dim crease per solid, one highlight at a time, no words inside the
drawing. GitHub strips <script>, so every figure plays a loop in CSS
keyframes, and its read-out (bottom right) narrates the loop in a few
characters.

One rule from the old page stays: nothing here is a fake measurement. Every
number below is a fact about the setup as it stands, and the figures draw
what the setup actually does, nothing aspirational. When the setup changes,
change CONFIG and run this again.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import figures  # noqa: E402

# ==================================================================
# CONFIG: this is the part to edit. Everything else just draws it.
# ==================================================================

NAME = "Mikkel"
TAGLINE = "growth engineer · bootstrapper"

# The spec card under the name. Keys are padded to the longest one.
FACTS = [
    ("studio", "holmgaard co. · copenhagen"),
    ("study", "business economics & it"),
    ("builds", "go infra · python tests · next.js"),
    ("lab", "3 proxmox nodes · talos k8s"),
    ("ships", "own ventures first, then partners"),
    ("repos", "85 · mostly private"),
]

# The Proxmox cluster, one row per node: name, ram, threads, what it is for,
# (half width, half depth, height) of the box drawn for it, (guest kind,
# count), and the read-out while it is in focus. Guest kinds: "lxc" draws a
# tray of containers, "vm" stacked slabs, "talos" slabs with a dot code.
HOSTS = [
    ("pve", "32 GB", "12", "lxc services", (24, 24, 22), ("lxc", 5), "gitea · gotify · ci runner"),
    ("dell", "64 GB", "12", "project vms", (31, 31, 30), ("vm", 3), "vm1–3 · hermes agent"),
    ("m920q", "32 GB", "6", "kubernetes", (18, 18, 11), ("talos", 4), "devops vm + 3 talos vms"),
]
LAB_TOTAL = ("128 GB", "30")

# The stack: a table of jobs, and a tray of tools that stand up one at a
# time in this order, each lighting the job it does. (simple-icons slug,
# read-out, row in JOBS). Twelve fill a 4 x 3 tray. The marks are vendored
# in logos.json (Simple Icons, CC0).
JOBS = [
    ("infra & services", "go"),
    ("tests & prototypes", "python"),
    ("web apps", "next.js"),
    ("client sites", "wordpress, if needed"),
    ("platform", "talos · k8s · argo cd"),
    ("metal & iac", "proxmox · opentofu"),
    ("network", "tailscale"),
    ("agents", "claude"),
]
STACK = [
    ("go", "infra · backend · micro-services", 0),
    ("python", "tests · prototypes", 1),
    ("nextdotjs", "web apps", 2),
    ("kubernetes", "orchestration", 4),
    ("proxmox", "hypervisor", 5),
    ("talos", "node os", 4),
    ("argo", "gitops", 4),
    ("opentofu", "infra as code", 5),
    ("tailscale", "network", 6),
    ("helm", "charts", 4),
    ("claude", "agents", 7),
    ("wordpress", "if a client needs it", 3),
]

# The method, as a line every idea rides down: the studio's research, build,
# test, scale. Four rows for the table, four read-outs that follow the bright
# crate, one closing line.
METHOD = [
    ["01", "research", "signal → hypothesis"],
    ["02", "build", "first working version"],
    ["03", "test", "in our own ventures"],
    ["04", "scale", "into partner workflows"],
]
METHOD_READOUTS = ["research · signal in", "build · smallest version", "test · own ventures first",
                   "scale · plugged into partners"]
METHOD_FOOT = "proven on our own first"

# ==================================================================


def write(name, svg_for_theme):
    for theme in ("dark", "light"):
        path = os.path.join(ROOT, "assets", f"{name}-{theme}.svg")
        with open(path, "w") as fh:
            fh.write(svg_for_theme(theme))
        print(f"  {os.path.relpath(path, ROOT):34s} {os.path.getsize(path) / 1024:6.1f} KB")


def main():
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    portrait = open(os.path.join(ROOT, "assets", "portrait.svg")).read()
    write("operator", lambda th: figures.portrait_card(th, portrait))
    write("spec", lambda th: figures.id_card(th, NAME, TAGLINE, FACTS))
    write("homelab", lambda th: figures.homelab(th, "Fig 1.1", hosts=HOSTS, total=LAB_TOTAL))
    write("cluster", lambda th: figures.cluster(th, "Fig 1.2"))
    write("previews", lambda th: figures.previews(th, "Fig 1.3"))
    write("agents", lambda th: figures.agents(th, "Fig 1.4"))
    write("services", lambda th: figures.services(th, "Fig 1.5"))
    write("stack", lambda th: figures.stack(th, STACK, JOBS, fig_no="Fig 1.6"))
    write("method", lambda th: figures.pipeline(th, METHOD, METHOD_READOUTS, METHOD_FOOT))


if __name__ == "__main__":
    main()
