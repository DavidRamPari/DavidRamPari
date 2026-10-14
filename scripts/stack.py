"""Tech stack strip: the tools I use most on the first row, the rest below.

Single-colour logos (assets/icons), black on white or white on black. The first
row carries a short yellow mark under each name.
"""

from __future__ import annotations

from typing import Any

import icons
import typeset as ts
from core import PALETTE, n, svg_open, t

CELL, SIZE, PAD = 96, 40, 16
ROW_H = SIZE + 50
LABEL = ts.Style("sans-medium", 13.5)


def describe(cfg: dict[str, Any], lang: str) -> str:
    names = {s["id"]: s["label"] for s in cfg["stack"]["items"]}
    main = ", ".join(names[i] for i in cfg["stack"]["main"])
    also = ", ".join(names[i] for i in cfg["stack"].get("also", []))
    if lang == "es":
        return f"Stack principal: {main}. También: {also}." if also else f"Stack principal: {main}."
    return f"Main stack: {main}. Also: {also}." if also else f"Main stack: {main}."


def _chunks(items: list[str], most: int) -> list[list[str]]:
    """Split a row into even rows of at most `most` items (8 -> 4 + 4, not 5 + 3)."""
    if len(items) <= most:
        return [items]
    count = -(-len(items) // most)
    size = -(-len(items) // count)
    return [items[i:i + size] for i in range(0, len(items), size)]


def render(cfg: dict[str, Any], theme: str, mobile: bool = False) -> str:
    """Desktop: main stack on one row, the rest on another. Mobile: rows of up to five."""
    p = PALETTE[theme]
    names = {s["id"]: s for s in cfg["stack"]["items"]}
    main, also = cfg["stack"]["main"], cfg["stack"].get("also", [])
    if mobile:
        rows = _chunks(main, 5) + _chunks(also, 5)
        first_rows = len(_chunks(main, 5))
    else:
        rows = [r for r in (main, also) if r]
        first_rows = 1
    width = max(len(r) for r in rows) * CELL + 2 * PAD
    height = len(rows) * ROW_H + 2 * PAD - 10
    out = [svg_open(width, height, str(t(cfg["stack"]["title"], "en")), describe(cfg, "en"))]
    for ri, row in enumerate(rows):
        x0 = (width - len(row) * CELL) / 2
        y = PAD + ri * ROW_H
        for ci, item_id in enumerate(row):
            item = names[item_id]
            cx = x0 + ci * CELL + CELL / 2
            out.append(icons.draw(item.get("icon", item_id), cx - SIZE / 2, y, SIZE, p["text"]))
            out.append(ts.text(LABEL, item["label"], cx, y + SIZE + 22, p["text"], anchor="middle"))
            if ri < first_rows:
                out.append(f'<rect x="{n(cx - 11)}" y="{n(y + SIZE + 31)}" width="22" height="2.5" '
                           f'fill="{p["accent"]}"/>')
    out.append("</svg>")
    return "".join(out)
