"""Dot-matrix shapes: words in the pixel font, an avatar dithered into dots,
and an ordering trick so dots travel smoothly from one shape to the next."""

from __future__ import annotations

from collections import deque
from pathlib import Path

import pixelfont

Cell = tuple[int, int]


def text_cells(text: str, cols: int, rows: int, margin: int = 3, max_block: int = 6) -> set[Cell]:
    """Cells that draw `text` as big LED letters, centred in a cols x rows grid."""
    font_cells, width = pixelfont.layout(text)
    width = max(width, 1)
    k = min((cols - 2 * margin) // width, (rows - 2 * margin) // pixelfont.HEIGHT, max_block)
    k = max(k, 1)
    ox = (cols - width * k) // 2
    oy = (rows - pixelfont.HEIGHT * k) // 2
    out: set[Cell] = set()
    for fx, fy in font_cells:
        if fy < 0:  # accents are skipped in the matrix
            continue
        for dx in range(k):
            for dy in range(k):
                out.add((ox + fx * k + dx, oy + fy * k + dy))
    return out


def avatar_cells(path: Path, cols: int, rows: int, theme: str, margin: int = 2) -> set[Cell] | None:
    """Dither an avatar into lit cells. Returns None if the image or Pillow is missing.

    Dark theme lights the bright parts of the image; light theme inks the dark
    parts. A plain background touching the border is removed first, so it does
    not turn into a solid block of dots.
    """
    if not path.exists():
        return None
    try:
        import numpy as np
        from PIL import Image, ImageEnhance, ImageOps
    except ImportError:
        return None

    img = Image.open(path).convert("RGBA")
    w, h = img.size
    side_px = min(w, h)
    img = img.crop(((w - side_px) // 2, (h - side_px) // 2,
                    (w - side_px) // 2 + side_px, (h - side_px) // 2 + side_px))
    side = min(cols, rows) - 2 * margin
    img = img.resize((side, side), Image.Resampling.LANCZOS)

    rgba = np.asarray(img, dtype=np.float32)
    alpha = rgba[..., 3] / 255.0
    keep = (alpha > 0.1) & ~_border_background(rgba[..., :3], alpha)

    gray = ImageOps.grayscale(Image.fromarray(rgba[..., :3].astype("uint8")))
    gray = ImageOps.autocontrast(gray, cutoff=1)
    gray = ImageEnhance.Contrast(gray).enhance(1.3)
    lum = np.asarray(gray, dtype=np.float32) / 255.0
    # Keep some dots in every part of the subject, so dark hair still reads on
    # the dark theme and a light face still reads on the light theme.
    floor = 0.22
    lum = floor + (1 - floor) * lum if theme == "dark" else (1 - floor) * lum

    bright = _floyd_steinberg(lum)
    lit = (bright if theme == "dark" else ~bright) & keep

    ox, oy = (cols - side) // 2, (rows - side) // 2
    ys, xs = np.nonzero(lit)
    return {(ox + int(x), oy + int(y)) for x, y in zip(xs, ys)}


def _border_background(rgb, alpha, tolerance: float = 38.0):
    """Mask of pixels that look like the background colour and touch the border."""
    import numpy as np

    h, w, _ = rgb.shape
    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    bg = np.median(border, axis=0)
    close = (np.linalg.norm(rgb - bg, axis=2) < tolerance) | (alpha <= 0.1)
    seen = np.zeros((h, w), dtype=bool)
    queue: deque[tuple[int, int]] = deque()
    for x in range(w):
        queue.extend([(0, x), (h - 1, x)])
    for y in range(h):
        queue.extend([(y, 0), (y, w - 1)])
    while queue:
        y, x = queue.popleft()
        if seen[y, x] or not close[y, x]:
            continue
        seen[y, x] = True
        for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= ny < h and 0 <= nx < w and not seen[ny, nx]:
                queue.append((ny, nx))
    return seen


def _floyd_steinberg(lum):
    """Classic error-diffusion dithering; True marks a bright (on) pixel."""
    import numpy as np

    work = lum.copy()
    h, w = work.shape
    out = np.zeros((h, w), dtype=bool)
    for y in range(h):
        for x in range(w):
            old = work[y, x]
            on = old >= 0.5
            out[y, x] = on
            err = old - (1.0 if on else 0.0)
            if x + 1 < w:
                work[y, x + 1] += err * 7 / 16
            if y + 1 < h:
                if x > 0:
                    work[y + 1, x - 1] += err * 3 / 16
                work[y + 1, x] += err * 5 / 16
                if x + 1 < w:
                    work[y + 1, x + 1] += err * 1 / 16
    return out


def _hilbert(order: int, x: int, y: int) -> int:
    """Position of (x, y) along a Hilbert curve covering an order x order grid."""
    d = 0
    s = order // 2
    while s > 0:
        rx = 1 if x & s else 0
        ry = 1 if y & s else 0
        d += s * s * ((3 * rx) ^ ry)
        if ry == 0:
            if rx == 1:
                x, y = order - 1 - x, order - 1 - y
            x, y = y, x
        s //= 2
    return d


def ordered_sample(cells: set[Cell], count: int, order: int = 128) -> list[Cell]:
    """`count` cells picked evenly along a Hilbert curve.

    Sampling every shape this way means the i-th dot of one shape and the i-th
    dot of the next sit in roughly the same region, so dots glide instead of
    criss-crossing the whole matrix.
    """
    seq = sorted(cells, key=lambda c: _hilbert(order, c[0], c[1]))
    if not seq:
        return []
    return [seq[int(i * len(seq) / count)] for i in range(count)]


def dash_rows(cells: set[Cell], x0: float, y0: float, pitch: float) -> str:
    """Path data drawing every lit cell with one dashed stroke per run of cells.

    Stroke the result with width = pitch - 1 and dasharray "pitch-1 1": each
    dash is one dot, so a run of 20 dots costs one short path command.
    """
    rows: dict[int, list[int]] = {}
    for c, r in cells:
        rows.setdefault(r, []).append(c)
    out = []
    half = (pitch - 1) / 2
    for r in sorted(rows):
        cs = sorted(set(rows[r]))
        start = prev = cs[0]
        for c in cs[1:] + [None]:
            if c is not None and c == prev + 1:
                prev = c
                continue
            length = (prev - start + 1) * pitch - 1
            out.append(f"M{_n(x0 + start * pitch)} {_n(y0 + r * pitch + half)}h{_n(length)}")
            if c is not None:
                start = prev = c
    return "".join(out)


def _n(v: float) -> str:
    return f"{v:.2f}".rstrip("0").rstrip(".")
