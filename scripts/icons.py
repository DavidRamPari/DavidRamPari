"""Single-colour logos from assets/icons, drawn at any size and colour.

Most come from Simple Icons (CC0); linkedin is a single-colour version of the
skill-icons one (MIT). See assets/icons/README.md. `cloud`, `envelope` and `globe`
are drawn here, since they are generic symbols rather than logos.
"""

from __future__ import annotations

import re
from functools import lru_cache

from core import ROOT, n

ICON_DIR = ROOT / "assets" / "icons"

FILLED = {
    # 24 x 24 filled symbols for tools without a single-colour logo
    "cloud": "M6.6 19.5a4.6 4.6 0 0 1-1.1-9.07A6.5 6.5 0 0 1 17.8 8.7a5.4 5.4 0 0 1 .4 10.8z",
}

GENERIC = {
    # 24 x 24 outline symbols, drawn with a stroke instead of a fill
    "envelope": "M3 5.5h18v13H3z M3.5 6l8.5 7 8.5-7",
    "globe": "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18z M3 12h18 M12 3c2.6 2.7 3.9 5.7 3.9 9s-1.3 6.3-3.9 9 "
             "M12 3c-2.6 2.7-3.9 5.7-3.9 9s1.3 6.3 3.9 9",
}


@lru_cache(maxsize=None)
def _load(slug: str) -> tuple[tuple[float, float, float, float], str, str] | None:
    f = ICON_DIR / f"{slug}.svg"
    if not f.exists():
        return None
    src = f.read_text(encoding="utf-8")
    vb = tuple(float(v) for v in re.search(r'viewBox="([^"]+)"', src).group(1).split())
    d = re.search(r' d="([^"]+)"', src).group(1)
    rule = re.search(r'fill-rule="([^"]+)"', src)
    return vb, d, rule.group(1) if rule else "nonzero"


def exists(slug: str) -> bool:
    return slug in GENERIC or slug in FILLED or _load(slug) is not None


def draw(slug: str, x: float, y: float, size: float, color: str) -> str:
    """The logo fitted in a size x size box with its top-left corner at (x, y)."""
    if slug in FILLED:
        k = size / 24
        return f'<path transform="translate({n(x)} {n(y)}) scale({n(k, 4)})" d="{FILLED[slug]}" fill="{color}"/>'
    if slug in GENERIC:
        k = size / 24
        return (f'<path transform="translate({n(x)} {n(y)}) scale({n(k, 4)})" d="{GENERIC[slug]}" fill="none" '
                f'stroke="{color}" stroke-width="{n(1.8)}" stroke-linejoin="round" stroke-linecap="round"/>')
    icon = _load(slug)
    if icon is None:
        return ""
    (vx, vy, vw, vh), d, rule = icon
    k = size / max(vw, vh)
    ox = x + (size - vw * k) / 2 - vx * k
    oy = y + (size - vh * k) / 2 - vy * k
    rule_attr = f' fill-rule="{rule}"' if rule != "nonzero" else ""
    return f'<path transform="translate({n(ox)} {n(oy)}) scale({n(k, 5)})" d="{d}" fill="{color}"{rule_attr}/>'
