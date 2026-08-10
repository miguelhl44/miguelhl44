#!/usr/bin/env python3
"""Draw the animated SVG graphics for the profile README.

Everything is generated locally from the GitHub GraphQL API — no third-party
image services, so nothing can rate-limit, watermark, or go offline. Motion
is SMIL (<animate>/<set>) because GitHub strips <script> from READMEs but
leaves SVG documents loaded through <img> intact.

Outputs (620px wide, transparent background, light/dark aware):
  banner.svg   terminal-style intro that types itself out
  stats.svg    contribution total + weekly bar sparkline
  streak.svg   current and longest daily streak
  langs.svg    top languages across public repos
  year.svg     the full year heatmap, with a left-to-right sweep
  hd-*.svg     section headings (markdown can't carry custom styling)

Env:
  GITHUB_TOKEN  required — any token that can read public profile data
  GH_LOGIN      login to draw (default: miguelhl44)
  OUT_DIR       output directory (default: the repo root, one level up)

Standard library only. Run: python3 scripts/generate_stats.py
"""
import json
import os
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone

API = "https://api.github.com/graphql"
WIDTH = 620
CW = 0.6  # monospace advance width in em; the common ratio

# The contribution window is pinned to whole UTC days so the same day always
# produces byte-identical SVGs — otherwise every nightly run would commit a
# sparkline shifted by a fraction of a pixel. Language totals are restricted
# to PUBLIC repos so a personal token and the workflow token agree.
QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount date weekday } }
      }
    }
    repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC) {
      nodes {
        isFork
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
  }
}
"""

LIGHT = dict(ink="#1f2328", mut="#59636e", fnt="#818b98", lin="#d1d9e0",
             acc="#1a7f37",
             g=["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"])
DARK = dict(ink="#f0f6fc", mut="#9198a1", fnt="#6e7681", lin="#3d444d",
            acc="#3fb950",
            g=["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"])
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

# GitHub's linguist colors for the languages likely to show up here.
LANG_COLORS = {
    "Python": "#3572A5", "TypeScript": "#3178c6", "JavaScript": "#f1e05a",
    "Svelte": "#ff3e00", "CSS": "#663399", "HTML": "#e34c26",
    "Shell": "#89e051", "Go": "#00ADD8", "Rust": "#dea584",
    "Java": "#b07219", "C": "#555555", "C++": "#f34b7d", "C#": "#178600",
    "Ruby": "#701516", "PHP": "#4F5D95", "Kotlin": "#A97BFF",
    "Swift": "#F05138", "Vue": "#41b883", "Dockerfile": "#384d54",
    "Jupyter Notebook": "#DA5B0B", "Lua": "#000080", "PowerShell": "#012456",
}
LANG_FALLBACK = "#8b949e"

MONTHS = "jan feb mar apr may jun jul aug sep oct nov dec".split()


# ---------------------------------------------------------------- data

def fetch(login, token):
    today = datetime.now(timezone.utc).date()
    frm = f"{(today - timedelta(days=364)).isoformat()}T00:00:00Z"
    to = f"{today.isoformat()}T23:59:59Z"
    body = json.dumps({"query": QUERY,
                       "variables": {"login": login, "from": frm,
                                     "to": to}}).encode()
    req = urllib.request.Request(
        API, data=body,
        headers={"Authorization": f"bearer {token}",
                 "Content-Type": "application/json",
                 "User-Agent": f"{login}-profile-graphics"})
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if payload.get("errors"):
        sys.exit(f"GraphQL errors: {payload['errors']}")
    user = (payload.get("data") or {}).get("user")
    if not user:
        sys.exit(f"no such user: {login}")
    return user


def streaks(days):
    """Current and longest runs of consecutive days with contributions.

    Today counting zero doesn't end the current streak — the day isn't over.
    """
    best = (0, None, None)
    length, start = 0, None
    for d in days:
        if d["contributionCount"] > 0:
            if length == 0:
                start = d["date"]
            length += 1
            if length > best[0]:
                best = (length, start, d["date"])
        else:
            length = 0

    trail = days[:-1] if days and days[-1]["contributionCount"] == 0 else days
    cur_len, cur_start, cur_end = 0, None, None
    for d in reversed(trail):
        if d["contributionCount"] == 0:
            break
        cur_len += 1
        cur_start = d["date"]
        cur_end = cur_end or d["date"]
    return (cur_len, cur_start, cur_end), best


def top_languages(nodes):
    """Bytes per language. Own repos first; if that's empty (all code lives
    in forks), fall back to every public repo and say so in the label."""
    def tally(include_forks):
        acc = {}
        for repo in nodes:
            if repo.get("isFork") and not include_forks:
                continue
            for e in (repo.get("languages") or {}).get("edges") or []:
                name = e["node"]["name"]
                acc[name] = acc.get(name, 0) + e["size"]
        return acc

    acc, note = tally(False), "by bytes &#183; own public repos"
    if not acc:
        acc, note = tally(True), "by bytes &#183; public repos incl. forks"
    ranked = sorted(acc.items(), key=lambda kv: (-kv[1], kv[0]))[:6]
    return ranked, note


def crunch(user):
    cal = user["contributionsCollection"]["contributionCalendar"]
    weeks = [w["contributionDays"] for w in cal["weeks"]]
    days = [d for w in weeks for d in w]
    weekly = [sum(x["contributionCount"] for x in w) for w in weeks]
    cur, best = streaks(days)
    langs, note = top_languages(user["repositories"]["nodes"])
    return dict(total=cal["totalContributions"],
                active=sum(1 for d in days if d["contributionCount"] > 0),
                ndays=len(days),
                weekly=weekly, weeks=weeks,
                best_week=max(weekly, default=0),
                current=cur, longest=best,
                langs=langs, langs_note=note)


def nice(iso):
    d = date.fromisoformat(iso)
    return f"{MONTHS[d.month - 1]} {d.day}"


# ---------------------------------------------------------------- svg bits

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def theme_css(t):
    levels = "".join(f".g{i}{{fill:{c}}}" for i, c in enumerate(t["g"]))
    return (f".ink{{fill:{t['ink']}}}.mut{{fill:{t['mut']}}}"
            f".fnt{{fill:{t['fnt']}}}.lin{{stroke:{t['lin']}}}"
            f".acc{{fill:{t['acc']}}}{levels}")


def svg_open(w, h):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" font-family="{MONO}">'
            f"<style>{theme_css(LIGHT)}"
            f"@media(prefers-color-scheme:dark){{{theme_css(DARK)}}}</style>")


def txt(x, y, s, size=12, cls="mut", anchor=None, weight=None, spacing=None):
    a = ""
    if anchor:
        a += f' text-anchor="{anchor}"'
    if weight:
        a += f' font-weight="{weight}"'
    if spacing:
        a += f' letter-spacing="{spacing}"'
    return (f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" '
            f'font-size="{size}"{a}>{s}</text>')


def appear(begin, dur=0.4):
    return (f'<animate attributeName="opacity" from="0" to="1" '
            f'begin="{begin:.2f}s" dur="{dur:.2f}s" fill="freeze"/>')


# ---------------------------------------------------------------- graphics

def draw_stats(d):
    H = 150
    p = [svg_open(WIDTH, H)]
    p.append(f'<g opacity="0">{appear(0.05)}'
             + txt(0, 48, f"{d['total']:,}", 46, "ink", weight="600")
             + txt(0, 70, "contributions in the last year", 12) + "</g>")
    for i, (val, lab) in enumerate([(d["active"], "active days"),
                                    (d["best_week"], "best week")]):
        p.append(f'<g opacity="0">{appear(0.25 + i * 0.12)}'
                 + txt(WIDTH, 30 + i * 40, f"{val}", 18, "ink", "end", "600")
                 + txt(WIDTH, 46 + i * 40, lab, 10, "fnt", "end") + "</g>")

    weekly = d["weekly"] or [0]
    peak = max(weekly) or 1
    n = len(weekly)
    pitch = WIDTH / n
    bw = min(pitch * 0.72, 9.0)
    base, maxh = H - 4, 44.0
    for i, v in enumerate(weekly):
        if v == 0:
            h, cls = 1.5, "g0"
        else:
            h = max((v / peak) * maxh, 2.5)
            cls = f"g{1 + min(3, int(v / peak * 4))}"
        x = i * pitch
        b = 0.35 + i * 0.014
        p.append(f'<rect x="{x:.1f}" y="{base}" width="{bw:.1f}" height="0" '
                 f'rx="1.5" class="{cls}">'
                 f'<animate attributeName="height" from="0" to="{h:.1f}" '
                 f'begin="{b:.2f}s" dur="0.4s" fill="freeze"/>'
                 f'<animate attributeName="y" from="{base}" '
                 f'to="{base - h:.1f}" begin="{b:.2f}s" dur="0.4s" '
                 f'fill="freeze"/></rect>')
    p.append("</svg>")
    return "".join(p)


def draw_streak(d):
    H, mid = 106, WIDTH / 2
    p = [svg_open(WIDTH, H)]
    p.append(f'<line x1="{mid:.0f}" y1="16" x2="{mid:.0f}" y2="90" '
             f'class="lin" stroke-width="1" opacity="0">{appear(0.15)}</line>')
    panels = [(d["current"], "current streak", 30),
              (d["longest"], "longest streak", mid + 30)]
    for i, ((length, start, end), lab, x) in enumerate(panels):
        span = f"{nice(start)} &#8211; {nice(end)}" if length else "&#8212;"
        p.append(f'<g opacity="0">{appear(0.10 + i * 0.15)}'
                 + txt(x, 48, f"{length}", 36, "ink", weight="600")
                 + txt(x, 80, lab, 11, "mut")
                 + txt(x, 96, span, 10, "fnt") + "</g>")
        p.append(f'<rect x="{x:.1f}" y="56" width="0" height="3" rx="1.5" '
                 f'class="acc"><animate attributeName="width" from="0" '
                 f'to="44" begin="{0.35 + i * 0.15:.2f}s" dur="0.4s" '
                 f'fill="freeze"/></rect>')
    p.append("</svg>")
    return "".join(p)


def draw_langs(d):
    data = d["langs"]
    rows = max(len(data), 1)
    H = 26 + rows * 24 + 6
    p = [svg_open(WIDTH, H)]
    p.append(f'<g opacity="0">{appear(0.05)}'
             + txt(0, 12, "TOP LANGUAGES", 9, "fnt", spacing="1.5")
             + txt(WIDTH, 12, d["langs_note"], 9, "fnt", "end") + "</g>")
    if not data:
        p.append(f'<g opacity="0">{appear(0.25)}'
                 + txt(0, 46, "no public code to count yet", 12) + "</g>")
        p.append("</svg>")
        return "".join(p)

    top = max(v for _, v in data)
    total = sum(v for _, v in data)
    bar_x, bar_max = 170, WIDTH - 170 - 52
    for i, (name, val) in enumerate(data):
        by = 36 + i * 24
        color = LANG_COLORS.get(name, LANG_FALLBACK)
        b = 0.20 + i * 0.10
        p.append(f'<g opacity="0">{appear(b)}'
                 + f'<circle cx="5" cy="{by - 4:.1f}" r="4.5" fill="{color}"/>'
                 + txt(16, by, esc(name.lower()), 12, "ink")
                 + txt(WIDTH, by, f"{val / total * 100:.0f}%", 11, "mut",
                       "end") + "</g>")
        p.append(f'<rect x="{bar_x}" y="{by - 8.5:.1f}" width="{bar_max}" '
                 f'height="9" rx="4.5" class="g0"/>')
        p.append(f'<rect x="{bar_x}" y="{by - 8.5:.1f}" width="0" height="9" '
                 f'rx="4.5" fill="{color}"><animate attributeName="width" '
                 f'from="0" to="{bar_max * val / top:.1f}" '
                 f'begin="{b + 0.10:.2f}s" dur="0.5s" fill="freeze"/></rect>')
    p.append("</svg>")
    return "".join(p)


def draw_year(d):
    CELL, PITCH, GUT, TOP = 8.6, 11.0, 30, 44
    weeks = d["weeks"]
    H = int(TOP + 7 * PITCH + 26)

    def level(v):
        if v == 0:
            return 0
        for cut, lvl in ((2, 1), (5, 2), (9, 3)):
            if v <= cut:
                return lvl
        return 4

    p = [svg_open(WIDTH, H)]
    p.append(f'<g opacity="0">{appear(0.05)}'
             + txt(GUT, 14, "THE LAST YEAR", 9, "fnt", spacing="1.5")
             + txt(GUT, 31, f"{d['active']} of {d['ndays']} days had a "
                            f"contribution", 11) + "</g>")

    lx = WIDTH - 100
    legend = [txt(lx - 6, 14, "less", 9, "fnt", "end")]
    for j in range(5):
        legend.append(f'<rect x="{lx + j * 11:.1f}" y="6" width="{CELL}" '
                      f'height="{CELL}" rx="2" class="g{j}"/>')
    legend.append(txt(lx + 4 * 11 + CELL + 6, 14, "more", 9, "fnt"))
    p.append(f'<g opacity="0">{appear(1.10)}' + "".join(legend) + "</g>")

    for c, week in enumerate(weeks):
        x = GUT + c * PITCH
        cells = "".join(
            f'<rect x="{x:.1f}" y="{TOP + day["weekday"] * PITCH:.1f}" '
            f'width="{CELL}" height="{CELL}" rx="2" '
            f'class="g{level(day["contributionCount"])}"/>'
            for day in week)
        p.append(f'<g opacity="0">{appear(0.15 + c * 0.016, 0.35)}'
                 f'{cells}</g>')

    for r, lab in ((1, "mon"), (3, "wed"), (5, "fri")):
        p.append(f'<g opacity="0">{appear(0.10)}'
                 + txt(GUT - 8, TOP + r * PITCH + 7, lab, 9, "fnt", "end")
                 + "</g>")

    base_y = TOP + 7 * PITCH + 16
    last_m, last_x = None, -999.0
    for i, week in enumerate(weeks):
        m = int(week[0]["date"][5:7])
        x = GUT + i * PITCH
        if m != last_m and i < len(weeks) - 2 and x - last_x >= 34:
            p.append(f'<g opacity="0">{appear(0.9)}'
                     + txt(x, base_y, MONTHS[m - 1], 9, "fnt") + "</g>")
            last_x = x
        last_m = m
    p.append("</svg>")
    return "".join(p)


def draw_header(word):
    fs, H = 15, 26
    tw = (len(word) + 3) * fs * CW + 12
    p = [svg_open(WIDTH, H)]
    p.append(f'<g opacity="0">{appear(0.05, 0.3)}'
             f'<text x="0" y="18" font-size="{fs}" font-weight="600" '
             f'xml:space="preserve"><tspan class="acc">// </tspan>'
             f'<tspan class="ink">{esc(word)}</tspan></text></g>')
    p.append(f'<line x1="{tw:.0f}" y1="13" x2="{tw:.0f}" y2="13" class="lin" '
             f'stroke-width="1"><animate attributeName="x2" from="{tw:.0f}" '
             f'to="{WIDTH}" begin="0.15s" dur="0.55s" fill="freeze"/></line>')
    p.append("</svg>")
    return "".join(p)


# ---------------------------------------------------------------- main

def write_if_changed(path, svg):
    old = ""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            old = f.read()
    if old == svg:
        return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    return True


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN is not set")
    login = os.environ.get("GH_LOGIN", "miguelhl44")
    default_out = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = os.environ.get("OUT_DIR", default_out)

    d = crunch(fetch(login, token))
    files = {
        "stats.svg": draw_stats(d),
        "streak.svg": draw_streak(d),
        "langs.svg": draw_langs(d),
        "year.svg": draw_year(d),
    }
    for word in ("about", "homelab", "stack", "projects", "stats",
                 "how this works"):
        files[f"hd-{word.replace(' ', '-')}.svg"] = draw_header(word)

    changed = sorted(n for n, svg in files.items()
                     if write_if_changed(os.path.join(out_dir, n), svg))
    print(f"{d['total']} contributions, {d['active']} active days, "
          f"best week {d['best_week']}, streak {d['current'][0]} now / "
          f"{d['longest'][0]} best")
    print("languages: " + (", ".join(f"{n} {v}" for n, v in d["langs"])
                           or "none"))
    print("updated: " + (", ".join(changed) if changed else "nothing"))


if __name__ == "__main__":
    main()
