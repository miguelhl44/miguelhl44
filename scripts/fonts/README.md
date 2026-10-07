# Fonts

`JetBrainsMono-Regular.ttf` is [JetBrains Mono](https://github.com/JetBrains/JetBrainsMono)
v2.304, redistributed unmodified under the SIL Open Font License 1.1
(`OFL.txt`).

It is not loaded by the README. `scripts/make_portrait.py` uses it twice at
build time: once to measure the ink coverage of each candidate glyph, so the
character ramp is ordered by real coverage rather than a guess, and once to cut
a subset containing only the ramp's glyphs. That subset, about 2 KB, is what
gets inlined into `portrait.svg` as base64.

Inlining is required rather than preferred: the SVG is loaded through an
`<img>` tag, and browsers do not fetch subresources for an image document, so a
linked font would never arrive. It also pins the advance width to 0.6 em, which
the character grid assumes; a viewer whose default monospace is narrower would
otherwise see the portrait squeezed horizontally.
