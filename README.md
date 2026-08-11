<div align="center">

<img src="./portrait.svg" width="420" alt="ASCII portrait"/>

<img src="./boot.svg" width="620" alt="boot sequence"/>

<img src="./whoami.svg" width="620" alt="whoami"/>

<!-- EDIT ME: your real links, or delete the line -->
<!-- [site](https://example.com) &nbsp;·&nbsp; [linkedin](https://www.linkedin.com/in/you/) &nbsp;·&nbsp; [email](mailto:you@example.com) -->

</div>

<img src="./hd-about.svg" width="620" alt="about"/>

> Business Economics & IT student in Denmark. Bootstrapper — marketing and IT.

Bootstrapping means no budget to hide behind, so I learn the whole stack
rather than the part that fits a job title: the campaign and the funnel it
runs on, the automation and the hypervisor it runs on. The economics half of
the degree is why I care what a thing costs to keep running, not just whether
it works on the day it ships.

Mostly that looks like small automations that remove a manual step, sites that
load fast, and a homelab I run properly instead of leaving it to rot.

<img src="./hd-homelab.svg" width="620" alt="homelab"/>

<div align="center">

<a href="#guests"><img src="./infra.svg" width="620" alt="homelab topology"/></a>

<a href="#guests"><img src="./nav-guests.svg" width="148" alt="vm / ct split"/></a>
<a href="#storage"><img src="./nav-storage.svg" width="148" alt="storage and backups"/></a>
<a href="#access"><img src="./nav-access.svg" width="148" alt="network and access"/></a>
<a href="#why"><img src="./nav-why.svg" width="148" alt="why self-host"/></a>

</div>

Everything self-hosted runs on **Proxmox VE** — one hypervisor, guests split by
job rather than piled into one box, so a broken container is a broken container
and not a broken evening. Storage is **ZFS**, which is the actual reason the
setup is worth running: snapshots make a bad change cheap to undo, and
scrubbing means bit rot gets caught rather than quietly restored from a backup
that already has it.

The rule I hold it to is that a rebuild has to be boring. Configuration lives
in files, backups run without being asked, and nothing important exists in only
one place. Running it is how I learn infrastructure — you find out what you
actually understand the first time you have to restore something.

<!-- EDIT ME: the tiles in infra.svg are set in scripts/make_profile.py
     (the SERVICES list). Swap them for what you really run, then re-run
     `python3 scripts/make_profile.py`. -->

<a id="guests"></a>

<details>
<summary><b>&nbsp;The guest split — a VM to break, containers to keep up</b></summary>

<br>

The split is not about tidiness, it is about what a mistake costs.

**Dev lives in a VM.** It has its own kernel, so I can install anything, load
modules, and change things that a container is not allowed to touch. It is the
box I am allowed to break, and a snapshot before an experiment means breaking
it costs a rollback instead of an evening.

**Services live in LXC containers.** They share the host kernel, so they boot in
about a second and cost roughly what the process itself costs — no second kernel
sitting in RAM doing nothing. Running eight of them is realistic on one machine
in a way that eight VMs would not be.

The rule I use when adding something new: if it needs its own kernel, or I do
not trust it, it gets a VM. If it is a service I trust to sit still and do one
job, it gets a container.

</details>

<a id="storage"></a>

<details>
<summary><b>&nbsp;Storage and backups — why ZFS is the point</b></summary>

<br>

**Snapshots make changes reversible.** Taking one before an upgrade turns "I
hope this works" into "I can undo this", which is the difference between
tinkering carefully and tinkering freely. They are cheap because they only
store what changed.

**Scrubbing catches bit rot.** ZFS checksums every block and verifies them on a
schedule, so silent corruption is found and repaired rather than sitting in a
file until the day I open it. Without that, a backup can faithfully preserve
data that is already broken.

**A snapshot is not a backup.** It lives on the same pool, so it does not
survive the pool dying. Anything I would be upset to lose exists somewhere the
server cannot reach on its own.

The honest test is restoring, not backing up. A backup nobody has restored is a
belief, not a backup.

<!-- EDIT ME: add your real snapshot/scrub/backup schedule here. -->

</details>

<a id="access"></a>

<details>
<summary><b>&nbsp;Network and access — how I actually reach it</b></summary>

<br>

I work on the server from **VS Code over SSH**, so the editor runs on my laptop
while everything it touches — the files, the language server, the terminal —
runs on the guest. The laptop stops being a machine I have to keep configured
and becomes a keyboard and a screen.

Keys, not passwords. The management interface is not something I expose to the
internet; reaching it from outside goes through a VPN rather than a port
forward. Anything that genuinely needs to be public sits behind a reverse proxy
that terminates TLS in one place, so certificates are one job instead of one job
per service.

<!-- EDIT ME: swap in your real firewall, VPN and reverse proxy choices. -->

</details>

<a id="why"></a>

<details>
<summary><b>&nbsp;Why self-host any of this</b></summary>

<br>

Bootstrapping is the short answer. A subscription that charges per seat or per
run gets more expensive exactly when something starts working, which is the
worst possible time to be punished for it. Hardware I already own costs the same
whether an automation runs ten times a month or ten thousand.

The longer answer is that operating something teaches what reading about it
does not. Restoring a backup, chasing why a container will not start, watching a
disk fill — those are the moments where you find out which parts you actually
understood. That is difficult to get from a tutorial and it is most of why the
lab exists.

The trade is real, though: I am also the person who gets paged. Self-hosting is
worth it for the things I want to understand and the things that would otherwise
meter me. Not for everything.

</details>

<img src="./hd-stack.svg" width="620" alt="stack"/>

<div align="center">

<a href="#guests"><img src="./stack.svg" width="620" alt="the stack, funnelling onto one machine"/></a>

</div>

One machine underneath all of it. Dev work sits in a **VM** — its own kernel, so
I can break it without taking anything else down — and the services run as **LXC
containers**, which share the host kernel and cost almost nothing to leave
running. Splitting them that way is the whole point: the thing I experiment on
and the things that need to stay up are not the same thing.

I work on it from **VS Code over SSH**, which makes the laptop mostly a keyboard.
Nothing important lives locally, so a reinstall costs an afternoon rather than a
weekend.

<!-- EDIT ME: the tools and which lane each runs in are the TOOLS list in
     scripts/make_profile.py — tag a tool "vm" or "ct" and the funnel follows. -->

<samp>proxmox &nbsp; zfs &nbsp; lxc &nbsp; docker &nbsp; linux &nbsp; n8n &nbsp; python &nbsp; typescript &nbsp; postgres &nbsp; nginx &nbsp; git</samp>

<img src="./hd-projects.svg" width="620" alt="projects"/>

<!-- EDIT ME: one block per project, a line or two each -->
**[mathias-n8n](https://github.com/miguelhl44/mathias-n8n)** &nbsp;·&nbsp; <samp>n8n</samp><br>
Automation workflows — the glue that removes the manual step between two tools.

**[miguelhl44](https://github.com/miguelhl44/miguelhl44)** &nbsp;·&nbsp; <samp>python, svg</samp><br>
This page. Every graphic on it is drawn by a script in this repo.

<img src="./hd-stats.svg" width="620" alt="stats"/>

<div align="center">

<img src="./stats.svg" width="620" alt="Contributions in the last year"/>

<img src="./streak.svg" width="620" alt="Current and longest contribution streak"/>

<img src="./langs.svg" width="620" alt="Top languages across public repositories"/>

<img src="./year.svg" width="620" alt="Contribution heatmap for the last year"/>

</div>

<img src="./hd-how-this-works.svg" width="620" alt="how this works"/>

Every graphic here is generated, not embedded from someone else's server.
Nothing is fetched from a third party, so nothing on this page can rate-limit,
watermark, or go dark.

They animate with SMIL — declarative `<animate>` tags inside the SVG itself —
because GitHub strips `<script>` and `<style>` from READMEs but leaves SVG
documents loaded through `<img>` alone. That is also why the section headings
are images: an SVG is the only way to put this page's own typeface on them.
Colours come from a `prefers-color-scheme` query inside each file.

Three scripts, split by what feeds them:

- [`generate_stats.py`](scripts/generate_stats.py) is the only one on a
  schedule. A [daily action](.github/workflows/stats.yml) runs it against the
  GitHub GraphQL API and commits just the files whose contents changed.
- [`make_profile.py`](scripts/make_profile.py) draws the boot console, the
  terminal card, the stack funnel and the topology from a config block at the
  top of the file — edit what it says about me, re-run it. Tagging a tool `vm`
  or `ct` is enough to move it to the other lane; the funnel is computed from
  that, not drawn by hand.
- [`make_portrait.py`](scripts/make_portrait.py) pushes a photo through a
  character ramp it picks by rendering each candidate glyph and measuring the
  ink it actually lays down. Its typeface is [JetBrains Mono](scripts/fonts),
  subset to the eleven glyphs the ramp uses and inlined as base64 — an SVG in
  an `<img>` cannot fetch a linked font, and the grid assumes an advance width
  of exactly 0.6 em.

No number on this page is decorative. The contribution figures come from the
API, the guest count under the node is derived from the tiles drawn beside it,
and there are no invented load averages — a reading that looks live and isn't
is worse than no reading at all.
