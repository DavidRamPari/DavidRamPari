"""Contact buttons as small SVGs: a single-colour logo or symbol and a label.

The first contact listed in profile.yml gets the yellow border; the others a grey one.
"""

from __future__ import annotations

import icons
import typeset as ts
from core import PALETTE, n, svg_open

LABELS = {
    "email": {"en": "Email", "es": "Correo"},
    "linkedin": {"en": "LinkedIn", "es": "LinkedIn"},
    "github": {"en": "GitHub", "es": "GitHub"},
    "codeforces": {"en": "Codeforces", "es": "Codeforces"},
    "website": {"en": "Portfolio", "es": "Portafolio"},
}
GLYPH = {"email": "envelope", "linkedin": "linkedin", "github": "github", "codeforces": "codeforces",
         "website": "globe"}
TEXT = ts.Style("sans-semibold", 14.5)
H, PAD, ICON, GAP, MARGIN = 42, 16, 18, 9, 4


def link(kind: str, value: str) -> str:
    return {
        "github": f"https://github.com/{value}",
        "linkedin": value,
        "email": f"mailto:{value}",
        "codeforces": f"https://codeforces.com/profile/{value}",
        "website": value,
    }[kind]


def render(kind: str, theme: str, lang: str, primary: bool) -> str:
    p = PALETTE[theme]
    label = LABELS[kind][lang]
    w = PAD + ICON + GAP + ts.width(TEXT, label) + PAD
    border = p["yellow"] if primary else p["faint"]
    x0, y0 = MARGIN, MARGIN
    out = [
        svg_open(w + 2 * MARGIN, H + 2 * MARGIN, label),
        f'<rect x="{n(x0 + 1)}" y="{n(y0 + 1)}" width="{n(w - 2)}" height="{H - 2}" rx="8" '
        f'fill="none" stroke="{border}" stroke-width="{2 if primary else 1.25}"/>',
        icons.draw(GLYPH[kind], x0 + PAD, y0 + (H - ICON) / 2, ICON, p["text"]),
        ts.text(TEXT, label, x0 + PAD + ICON + GAP, y0 + H / 2 + 5.2, p["text"]),
        "</svg>",
    ]
    return "".join(out)
