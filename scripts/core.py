"""Shared helpers: config loading, translations, palette and SVG utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
LANGS = ("en", "es")
THEMES = ("dark", "light")


# Black and white, with yellow as the only accent (borders, marks, the radar line).
# True black and white (not tinted greys) so the palette reads as a choice.
PALETTE = {
    "dark": {
        "bg": "#000000", "surface": "#000000", "text": "#FFFFFF", "muted": "#A3A3A3",
        "faint": "#5C5C5C", "line": "#2B2B2B", "edge": "#8F8F8F",
        "yellow": "#FFD60A", "accent": "#FFD60A",
    },
    "light": {
        # Bright yellow almost disappears on white, so thin lines use a deeper yellow.
        "bg": "#FFFFFF", "surface": "#FFFFFF", "text": "#000000", "muted": "#5C5C5C",
        "faint": "#A3A3A3", "line": "#DEDEDE", "edge": "#6B6B6B",
        "yellow": "#E0B000", "accent": "#D19E00",
    },
}


def load_config(path: Path | None = None) -> dict[str, Any]:
    path = path or ROOT / "profile.yml"
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def t(value: Any, lang: str) -> Any:
    """Pick the `lang` entry of an {en, es} pair; return anything else as-is."""
    if isinstance(value, dict) and set(value) & set(LANGS):
        return value.get(lang) or value.get("en")
    return value


def esc(text: Any) -> str:
    s = str(text)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def n(v: float, digits: int = 2) -> str:
    """Compact number formatting for SVG attributes."""
    s = f"{v:.{digits}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def svg_open(width: float, height: float, title: str, desc: str = "") -> str:
    head = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{n(width)}" height="{n(height)}" '
        f'viewBox="0 0 {n(width)} {n(height)}" role="img" aria-labelledby="t d">'
        f'<title id="t">{esc(title)}</title>'
    )
    return head + (f'<desc id="d">{esc(desc)}</desc>' if desc else "")


def write(path: Path, content: str) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return len(content.encode("utf-8"))
