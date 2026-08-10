<div align="center">

<img src="./banner.svg" width="620" alt="miguelhl44"/>

<img src="./stats.svg" width="620" alt="Contributions in the last year"/>

<!-- EDIT ME: put your real links here, or delete this line -->
<!-- [yoursite.com](https://yoursite.com) &nbsp;·&nbsp; [linkedin](https://www.linkedin.com/in/you/) &nbsp;·&nbsp; [email](mailto:you@example.com) -->

</div>

<img src="./hd-about.svg" width="620" alt="about"/>

<!-- EDIT ME: two or three lines about who you are and what you're building -->
> Just yet another nerd :)

Tinkering with automation, MCP servers, and whatever else looks interesting<br>
this week.

<img src="./hd-stack.svg" width="620" alt="stack"/>

<!-- EDIT ME: your actual tools -->
<samp>python &nbsp; typescript &nbsp; n8n &nbsp; docker &nbsp; linux</samp>

<img src="./hd-projects.svg" width="620" alt="projects"/>

<!-- EDIT ME: one block per project you want to show off, a line or two each -->
**[mathias-n8n](https://github.com/miguelhl44/mathias-n8n)** &nbsp;·&nbsp; <samp>n8n</samp><br>
Automation workflows built with n8n.

<img src="./hd-stats.svg" width="620" alt="stats"/>

<div align="center">

<img src="./streak.svg" width="620" alt="Current and longest contribution streak"/>

<img src="./langs.svg" width="620" alt="Top languages across public repositories"/>

<img src="./year.svg" width="620" alt="Contribution heatmap for the last year"/>

</div>

<img src="./hd-how-this-works.svg" width="620" alt="how this works"/>

Every graphic on this page is generated, not embedded from someone else's
server. A [scheduled GitHub Action](.github/workflows/stats.yml) runs
[`scripts/generate_stats.py`](scripts/generate_stats.py) once a day: it reads
the GitHub GraphQL API, draws these SVGs, and commits only the files that
changed.

They animate with SMIL — declarative `<animate>` tags inside the SVG itself —
because GitHub strips `<script>` and `<style>` from READMEs but leaves SVG
documents loaded through `<img>` alone. Since nothing is fetched from a third
party, nothing here can rate-limit, watermark, or go dark. Colors follow your
GitHub theme via a `prefers-color-scheme` media query inside each SVG.
