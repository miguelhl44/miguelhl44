<div align="center">

<img src="./portrait.svg" width="420" alt="ASCII portrait"/>

<img src="./whoami.svg" width="620" alt="whoami"/>

<!-- EDIT ME: your real links, or delete the line -->
<!-- [site](https://example.com) &nbsp;·&nbsp; [linkedin](https://www.linkedin.com/in/you/) &nbsp;·&nbsp; [email](mailto:you@example.com) -->

</div>

<img src="./hd-about.svg" width="620" alt="about"/>

### Hey, I'm Mikkel.

Business Economics & IT student in Denmark. Builder, developer and
bootstrapper.

I like building things that solve problems I actually have.

Usually it starts small: something is repetitive, something is difficult to
keep track of, a tool doesn't quite do what I need, or a process could clearly
work better. I'll build something to fix it, use it, find where it falls short,
and keep iterating until it becomes genuinely useful.

That way of working has taken me surprisingly far down the stack.

A small automation can turn into an application. An application needs somewhere
to run. Running it raises questions about infrastructure, networking, storage,
security and monitoring. Eventually you end up learning the layers underneath
the thing you originally wanted to build.

That's probably the common thread through most of what I do:

<samp>find a problem → build a solution → use it → learn from it → iterate → make it valuable</samp>

I'm interested in the whole system rather than a particular layer of it. I
enjoy writing software, working with data, automating processes, designing
infrastructure and figuring out how the pieces fit together.

My Business Economics & IT background adds another perspective: technology is
ultimately there to create value. I care about whether something works, but
also whether it is maintainable, scalable, worth the effort and actually
improves the problem it was built to solve.

I became interested in bootstrapping because this approach naturally lends
itself to it. When you're building things yourself, there is nobody else to
fill the gaps. You learn to move between development, infrastructure, data,
operations and the business problem whenever the project requires it.

I'm still a student, but I don't really think of my projects as exercises.
They're systems I use, problems I'm trying to solve, and experiments that
occasionally turn into something much bigger than I expected.

<img src="./hd-loop.svg" width="620" alt="build it. use it. improve it."/>

<div align="center">

<img src="./loop.svg" width="620" alt="a problem goes in, the middle repeats, something useful comes out"/>

</div>

I learn best when there is a real problem attached to what I'm building.

Rather than starting with a technology and looking for somewhere to use it, I
usually start with a problem. The first version can be simple. What matters is
getting something into use quickly enough that the real problems become
visible.

The first version is rarely the interesting one. The interesting part is what
happens afterwards — discovering that a workflow is slower than expected, that
a dataset needs a different structure, that an interface creates unnecessary
work, or that something which worked for ten records falls apart at ten
thousand.

Those are the moments where a project becomes a learning opportunity.

I tend to keep iterating when there is still a meaningful advantage to gain:
less manual work, better reliability, lower operating cost, better data, a
faster workflow, or simply a system that I understand better than the
alternative.

That is also why many of my projects end up crossing boundaries between
disciplines. A problem that looks like a software problem can turn out to be a
data problem. A data problem can become an infrastructure problem. An
infrastructure problem can be solved with automation.

I enjoy following that chain rather than stopping at the boundary of a job
title.

<img src="./hd-how-i-work.svg" width="620" alt="how i work"/>

**Start with the outcome.** Before building something, I try to define what
"better" actually means. A feature is only useful if it changes the outcome.

**Keep the feedback loop short.** I prefer getting a small version into use and
learning from it over spending too long designing something I haven't tested.

**Make work visible.** Whether it is a project board, a Git branch or a TODO
list, I like being able to see what is happening and what is actually finished.

**Leave things better than I found them.** Good enough for today is sometimes
the right decision. But when I touch something repeatedly, I usually look for
ways to make it simpler, more reliable or easier to reproduce.

**Understand the layers underneath.** I don't need to reinvent everything, but
I like knowing what is happening underneath the abstraction I'm relying on.
That curiosity is what took me from writing applications into infrastructure,
systems and automation.

<div align="center">

<img src="./kanban.svg" width="620" alt="a board with one card crossing it"/>

<img src="./gitgraph.svg" width="620" alt="branch, review, merge"/>

</div>

<!-- EDIT ME: the board is illustrative — the BOARD list in
     scripts/make_profile.py holds the card names. -->

<img src="./hd-homelab.svg" width="620" alt="the homelab"/>

### The homelab is where software stops being just code.

<div align="center">

<a href="#guests"><img src="./infra.svg" width="620" alt="homelab topology"/></a>

<a href="#guests"><img src="./nav-guests.svg" alt="vm / ct split"/></a>
<a href="#storage"><img src="./nav-storage.svg" alt="storage and backups"/></a>
<a href="#access"><img src="./nav-access.svg" alt="network and access"/></a>
<a href="#why"><img src="./nav-why.svg" alt="why self-host"/></a>

</div>

I run my own infrastructure with **Proxmox VE**, using virtual machines and LXC
containers for development, services and experiments. It gives me a place to
build, deploy, break, restore and operate systems rather than only developing
them locally.

The useful part isn't the hardware. It's having to deal with the consequences
of decisions.

A service that crashes at 2 AM is different from one that merely failed a local
test. A full disk becomes a capacity problem. A broken configuration becomes a
recovery problem. A network change becomes an availability problem. Those
experiences have made infrastructure much easier to understand, because there
is always a real system behind the concept.

I use **ZFS** for storage, snapshots for cheap rollbacks and backups for actual
recovery. Development work is isolated in VMs where I can experiment freely,
while persistent services live in lightweight containers.

The general principle is simple: make systems reproducible, isolate failures,
automate what is repetitive, and make mistakes cheap to recover from.

<!-- EDIT ME: the tiles in infra.svg are the SERVICES list in
     scripts/make_profile.py. Swap them for what you really run. -->

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

Partly cost. A subscription that charges per seat or per run gets more expensive
exactly when something starts working, which is the worst possible time to be
punished for it. Hardware I already own costs the same whether an automation
runs ten times a month or ten thousand.

Mostly, though, operating something teaches what reading about it does not.
Restoring a backup, chasing why a container will not start, watching a disk
fill — those are the moments where you find out which parts you actually
understood.

The trade is real: I am also the person who gets paged. Self-hosting is worth it
for the things I want to understand and the things that would otherwise meter
me. Not for everything.

</details>

<div align="center">

<a href="#guests"><img src="./stack.svg" width="620" alt="the stack, funnelling onto one machine"/></a>

</div>

One machine underneath all of it. Dev work sits in a VM I can break; the
services run as containers that need to stay up. I reach both from VS Code over
SSH, which makes the laptop mostly a keyboard — nothing important lives locally,
so a reinstall costs an afternoon rather than a weekend.

<!-- EDIT ME: the tools and which lane each runs in are the TOOLS list in
     scripts/make_profile.py — tag a tool "vm" or "ct" and the funnel follows. -->

<details>
<summary><b>&nbsp;Go, Terraform and MCP — the parts I write myself</b></summary>

<br>

**Go, for the things that have to just run.** A single static binary with no
runtime to install is the right shape for a box I want to stay boring: drop it
in a container, point systemd at it, and it does not break because something
upgraded a dependency underneath it.

**Terraform, so the lab is describable.** The point is not that clicking through
the Proxmox UI is slow — it is that clicking leaves no record. A guest defined
in code can be read, diffed and recreated; a guest defined by remembering what I
clicked eight months ago cannot. Same instinct as the snapshots: make being
wrong cheap to undo.

**MCP servers, to give a model real access instead of a description.** Writing
my own means deciding exactly what it can see and do, which puts the whole
security question in one place rather than scattering it. A narrow tool that
returns real data beats a broad one that guesses.

The thread through all three: I would rather write a small thing I fully
understand than adopt a large thing I do not. Not because it is always the right
trade — it is not, and I have spent time finding that out — but because
understanding the layer under you is most of what this is for.

<!-- EDIT ME: name the actual Go tools and MCP servers you have built, and what
     your Terraform manages. Specifics beat principles here. -->

</details>

<img src="./hd-repos.svg" width="620" alt="repos"/>

<!-- EDIT ME: one block per project, a line or two on the problem it solved -->
**[mathias-n8n](https://github.com/miguelhl44/mathias-n8n)** &nbsp;·&nbsp; <samp>n8n</samp><br>
Automation workflows — the glue that removes the manual step between two tools.

**[miguelhl44](https://github.com/miguelhl44/miguelhl44)** &nbsp;·&nbsp; <samp>python, svg</samp><br>
This page. Every graphic on it is drawn by a script in this repo.

<img src="./hd-interests.svg" width="620" alt="what i'm interested in"/>

I'm currently most interested in the space where software, data and
infrastructure meet.

<div align="center">

<img src="./loading.svg" width="620" alt="Currently loading: building reliable software and internal tools; data pipelines, processing and automation; Linux, virtualization and infrastructure; cloud and self-hosted systems; APIs and system integrations; AI tooling, agents and MCP; developer tooling and reproducible environments; turning manual workflows into systems."/>

</div>

I'm less interested in collecting technologies than in understanding how they
combine to solve a real problem. If a project teaches me something useful and
ends up making something faster, simpler, cheaper or more reliable, it was
probably worth building.
