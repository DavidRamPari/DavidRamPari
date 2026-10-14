"""Radar (spider) chart drawn from plain numbers: grey grid, a yellow outline, no fill."""

from __future__ import annotations

import math

import typeset as ts
from core import PALETTE, n, svg_open

R = 140          # outer ring radius
GAP = 16         # distance between the outer ring and the labels
RINGS = 3
LABEL = ts.Style("sans-medium", 14)
VALUE = ts.Style("sans", 12)
TITLE = ts.Style("sans-semibold", 16)


def render(title: str, axes: list[tuple[str, float]], theme: str,
           notes: list[str] | None = None, show_title: bool = False) -> str:
    """`axes` are (label, value 0-100). `notes` adds a small line under each label.
    The title goes into the SVG's accessible name; it is drawn only with `show_title`
    (the README heading above the chart already names it)."""
    p = PALETTE[theme]
    color = p["accent"]
    k = len(axes)
    angles = [-math.pi / 2 + i * 2 * math.pi / k for i in range(k)]

    labels = []
    for i, (label, _) in enumerate(axes):
        ca, sa = math.cos(angles[i]), math.sin(angles[i])
        lx, ly = (R + GAP) * ca, (R + GAP) * sa
        anchor = "middle" if abs(ca) < 0.3 else ("start" if ca > 0 else "end")
        ly += 5 if abs(sa) < 0.3 else (LABEL.size if sa > 0 else -4 - (VALUE.size + 3 if notes else 0))
        labels.append((lx, ly, anchor, label, notes[i] if notes else ""))

    # Fit the canvas around whatever the labels occupy.
    minx, maxx, miny, maxy = -R, R, -R, R
    for lx, ly, anchor, label, note in labels:
        w = max(ts.width(LABEL, label), ts.width(VALUE, note) if note else 0)
        x0 = lx if anchor == "start" else lx - w if anchor == "end" else lx - w / 2
        minx, maxx = min(minx, x0), max(maxx, x0 + w)
        miny = min(miny, ly - LABEL.size)
        maxy = max(maxy, ly + (VALUE.size + 6 if note else 4))
    pad = 14
    head = TITLE.size + 24 if show_title else 0
    width = max(maxx - minx + 2 * pad, ts.width(TITLE, title) + 2 * pad if show_title else 0)
    height = maxy - miny + 2 * pad + head
    cx = (width - (maxx - minx)) / 2 - minx
    cy = pad + head - miny

    out = [svg_open(width, height, title, ", ".join(f"{l} {v:g}/100" for l, v in axes)),
           ts.text(TITLE, title, width / 2, pad + TITLE.size, p["text"], anchor="middle") if show_title else "",
           f'<g transform="translate({n(cx)} {n(cy)})">']

    for ring in range(RINGS, 0, -1):
        r = R * ring / RINGS
        pts = " ".join(f"{n(r * math.cos(a))},{n(r * math.sin(a))}" for a in angles)
        out.append(f'<polygon points="{pts}" fill="none" stroke="{p["line"]}" stroke-width="1"/>')
    for a in angles:
        out.append(f'<line x1="0" y1="0" x2="{n(R * math.cos(a))}" y2="{n(R * math.sin(a))}" '
                   f'stroke="{p["line"]}" stroke-width="1"/>')

    shape = [(R * max(0, min(v, 100)) / 100 * math.cos(a), R * max(0, min(v, 100)) / 100 * math.sin(a))
             for (_, v), a in zip(axes, angles)]
    pts = " ".join(f"{n(x)},{n(y)}" for x, y in shape)
    out.append('<g><animateTransform attributeName="transform" type="scale" values="0.05;1" '
               'dur="1s" calcMode="spline" keyTimes="0;1" keySplines=".2 .8 .3 1" fill="freeze"/>')
    out.append(f'<polygon points="{pts}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round"/>')
    out.append("</g>")

    for lx, ly, anchor, label, note in labels:
        out.append(ts.text(LABEL, label, lx, ly, p["text"], anchor=anchor))
        if note:
            out.append(ts.text(VALUE, note, lx, ly + VALUE.size + 4, p["muted"], anchor=anchor))
    out.append("</g></svg>")
    return "".join(out)
