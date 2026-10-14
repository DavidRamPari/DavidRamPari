"""Set text as SVG outlines with the fonts bundled in assets/fonts.

GitHub serves README images through a proxy that blocks web fonts, so text drawn
with <text> falls back to whatever the visitor's system has. Converting each glyph
to a path keeps the typography identical on every device. HarfBuzz does the
shaping (kerning, ligatures, accents) and fontTools reads the outlines.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

from core import ROOT, n

FONT_DIR = ROOT / "assets" / "fonts"

# Roles used by the drawing scripts, mapped to the files in assets/fonts.
# profile.yml can override them under `fonts:`.
ROLES = {
    "sans": "IBMPlexSans-Regular.otf",
    "sans-medium": "IBMPlexSans-Medium.otf",
    "sans-semibold": "IBMPlexSans-SemiBold.otf",
    "mono": "IBMPlexMono-Regular.otf",
    "mono-medium": "IBMPlexMono-Medium.otf",
}


def _num(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


@dataclass(frozen=True)
class Style:
    """A font file at a size, with optional tracking (in em) and OpenType features."""
    font: str
    size: float
    tracking: float = 0.0
    features: tuple[tuple[str, bool], ...] = ()

    def with_size(self, size: float) -> "Style":
        return Style(self.font, size, self.tracking, self.features)


class Face:
    def __init__(self, path: Path):
        self.path = path
        self.hb_face = hb.Face(hb.Blob.from_file_path(str(path)))
        self.hb_font = hb.Font(self.hb_face)
        self.upem = self.hb_face.upem
        self.tt = TTFont(str(path))
        self.glyphs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()
        os2 = self.tt["OS/2"]
        self.cap_height = getattr(os2, "sCapHeight", 0) or int(self.upem * 0.7)
        self.x_height = getattr(os2, "sxHeight", 0) or int(self.upem * 0.5)
        self.ascender = os2.sTypoAscender
        self.descender = os2.sTypoDescender


def face(font: str) -> Face:
    """A font by role ("mono") or by file name ("IBMPlexSans-Regular.otf")."""
    return _face(ROLES.get(font, font))


@lru_cache(maxsize=None)
def _face(file_name: str) -> Face:
    return Face(FONT_DIR / file_name)


def _shape(style: Style, text: str) -> list[tuple[int, float, float, float]]:
    f = face(style.font)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    features = {"kern": True, "liga": True}
    features.update(dict(style.features))
    hb.shape(f.hb_font, buf, features)
    scale = style.size / f.upem
    track = style.tracking * style.size
    out = []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        out.append((info.codepoint, pos.x_advance * scale + track, pos.x_offset * scale, pos.y_offset * scale))
    return out


def width(style: Style, text: str) -> float:
    """Advance width of `text`, without the tracking after the last glyph."""
    glyphs = _shape(style, text)
    if not glyphs:
        return 0.0
    return sum(g[1] for g in glyphs) - style.tracking * style.size


def cap_height(style: Style) -> float:
    f = face(style.font)
    return f.cap_height * style.size / f.upem


def x_height(style: Style) -> float:
    f = face(style.font)
    return f.x_height * style.size / f.upem


def path(style: Style, text: str, x: float, y: float, anchor: str = "start") -> str:
    """SVG path data for `text` with its baseline at (x, y)."""
    if anchor != "start":
        w = width(style, text)
        x -= w if anchor == "end" else w / 2
    f = face(style.font)
    scale = style.size / f.upem
    pen = SVGPathPen(f.glyphs, ntos=_num)
    cursor = x
    for gid, advance, dx, dy in _shape(style, text):
        name = f.order[gid]
        glyph = f.glyphs[name]
        glyph.draw(TransformPen(pen, (scale, 0, 0, -scale, cursor + dx, y - dy)))
        cursor += advance
    return pen.getCommands()


def wrap(style: Style, text: str, max_width: float) -> list[str]:
    """Greedy line breaking on spaces."""
    lines: list[str] = []
    current = ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if current and width(style, trial) > max_width:
            lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    return lines


def text(style: Style, content: str, x: float, y: float, fill: str, anchor: str = "start",
         extra: str = "") -> str:
    """A <path> element drawing `content`; `extra` adds attributes such as class or opacity."""
    d = path(style, content, x, y, anchor)
    if not d:
        return ""
    attrs = f' {extra}' if extra else ""
    return f'<path d="{d}" fill="{fill}"{attrs}/>'


__all__ = ["Style", "face", "width", "cap_height", "x_height", "path", "wrap", "text", "n"]
