"""`$ whoami`: what the command would print about me, on a black screen.

Black in both themes, like the banner. Colour only in the prompt (yellow
user name). Two layouts: desktop (960 wide, avatar on the left) and mobile
(480 wide, bigger text, avatar above).
"""

from __future__ import annotations

from typing import Any

import dots
import typeset as ts
from core import ROOT, n, svg_open, t

CODE_FEATURES = (("calt", False), ("liga", False))

SCREEN = {
    "bg": "#000000", "edge": "#262626", "led_off": "#1C1C1C",
    "text": "#FFFFFF", "muted": "#A3A3A3", "dim": "#7A7A7A", "yellow": "#FFD60A",
}

TEXT = {
    "en": {"labels": ["Role", "Studies", "Location", "Stack", "Open to"], "updated": "updated {}", "and": " and "},
    "es": {"labels": ["Rol", "Estudios", "Ubicación", "Stack", "Disponible"], "updated": "actualizado {}", "and": " y "},
}


def _rows(cfg: dict[str, Any], lang: str) -> list[tuple[str, str]]:
    tx = TEXT[lang]
    names = {s["id"]: s["label"] for s in cfg["stack"]["items"]}
    location = f"{t(cfg['location'], lang)} ({cfg['timezone']})" if cfg.get("timezone") else t(cfg["location"], lang)
    # Mid-sentence, only the first item keeps its capital: "Freelance projects, internships and junior roles".
    open_to = [str(x) if i == 0 else str(x)[:1].lower() + str(x)[1:] for i, x in enumerate(t(cfg["open_to"], lang))]
    open_txt = ", ".join(open_to[:-1]) + tx["and"] + open_to[-1] if len(open_to) > 1 else "".join(open_to)
    values = [
        t(cfg["role"], lang),
        t(cfg["studies"], lang),
        location,
        ", ".join(names.get(s, s) for s in cfg["stack"]["main"]),
        open_txt,
    ]
    return [(k, v) for k, v in zip(tx["labels"], values) if v]


def describe(cfg: dict[str, Any], gh: dict[str, Any], lang: str) -> str:
    return "whoami: " + ". ".join(f"{k}: {v}" for k, v in _rows(cfg, lang)) + "."


def _prompt(cfg: dict[str, Any], lang: str, x: float, y: float, style: ts.Style) -> str:
    s = SCREEN
    user = str(cfg.get("name", cfg["user"])).split()[0].lower()
    host = str(t(cfg["location"], lang)).split(",")[0].lower()
    out = []
    for text_, color in ((user, s["yellow"]), ("@", s["muted"]), (host, s["text"]), (":~$ ", s["muted"]),
                         ("whoami", s["text"])):
        out.append(ts.text(style, text_, x, y, color))
        x += ts.width(style, text_)
    return "".join(out)


def render(cfg: dict[str, Any], gh: dict[str, Any], lang: str, mobile: bool = False) -> str:
    return _mobile(cfg, gh, lang) if mobile else _desktop(cfg, gh, lang)


def _desktop(cfg: dict[str, Any], gh: dict[str, Any], lang: str) -> str:
    s = SCREEN
    W, line = 960, 27
    mono = ts.Style("mono", 14.5, features=CODE_FEATURES)
    bold = ts.Style("mono-medium", 14.5, features=CODE_FEATURES)
    small = ts.Style("mono", 11.5)
    name = str(cfg.get("name", cfg["user"]))
    rows = _rows(cfg, lang)

    x_text, top = 296, 70
    last_baseline = top + 2 * line + 10 + (len(rows) - 1) * line
    pad = 40
    H = last_baseline + 52
    avatar = H - 2 * pad                     # the LED square spans the text block
    label_w = max(ts.width(mono, k) for k, _ in rows) + 24

    out = [
        svg_open(W, H, f"{name}: whoami", describe(cfg, gh, lang)),
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="{s["bg"]}" stroke="{s["edge"]}"/>',
        _avatar(cfg, 40, pad, avatar),
        _prompt(cfg, lang, x_text, top, mono),
        ts.text(bold, name, x_text, top + line, s["text"]),
        f'<path d="M{x_text} {top + line + 13}H{n(x_text + ts.width(bold, name))}" stroke="{s["dim"]}" '
        f'stroke-dasharray="5 3"/>',
    ]
    y = top + 2 * line + 10
    for label, value in rows:
        out.append(ts.text(mono, label, x_text, y, s["muted"]))
        out.append(ts.text(mono, value, x_text + label_w, y, s["text"]))
        y += line
    if gh.get("fetched_at"):
        out.append(ts.text(small, TEXT[lang]["updated"].format(gh["fetched_at"][:10]), W - 28, H - 20,
                           s["dim"], anchor="end"))
    out.append("</svg>")
    return "".join(out)


def _mobile(cfg: dict[str, Any], gh: dict[str, Any], lang: str) -> str:
    """Narrow card for phones: avatar and prompt on top, then label above value."""
    s = SCREEN
    W, pad = 480, 28
    mono = ts.Style("mono", 17, features=CODE_FEATURES)
    bold = ts.Style("mono-medium", 19, features=CODE_FEATURES)
    label = ts.Style("mono", 15, features=CODE_FEATURES)
    name = str(cfg.get("name", cfg["user"]))
    rows = _rows(cfg, lang)

    avatar = 112
    body: list[str] = []
    x_text = pad + avatar + 22
    body.append(_prompt(cfg, lang, x_text, pad + 34, ts.Style("mono", 15, features=CODE_FEATURES)))
    body.append(ts.text(bold, name, x_text, pad + 70, s["text"]))
    body.append(f'<path d="M{x_text} {pad + 84}H{n(x_text + ts.width(bold, name))}" stroke="{s["dim"]}" '
                f'stroke-dasharray="5 3"/>')
    y = pad + avatar + 44
    for k, v in rows:
        body.append(ts.text(label, k, pad, y, s["muted"]))
        y += 25
        for part in ts.wrap(mono, v, W - 2 * pad):
            body.append(ts.text(mono, part, pad, y, s["text"]))
            y += 24
        y += 14
    H = y + 10
    out = [
        svg_open(W, H, f"{name}: whoami", describe(cfg, gh, lang)),
        f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="{s["bg"]}" stroke="{s["edge"]}"/>',
        _avatar(cfg, pad, pad, avatar, pitch=3),
        *body,
        "</svg>",
    ]
    return "".join(out)


def _avatar(cfg: dict[str, Any], x: float, y: float, size: float, pitch: int = 4) -> str:
    """Avatar (or initials) as lit LEDs, the same board as the banner."""
    s = SCREEN
    grid = int(size // pitch)
    cells = None
    avatar = cfg.get("banner", {}).get("avatar")
    if avatar:
        cells = dots.avatar_cells(ROOT / avatar, grid, grid, "dark", margin=1)
    if not cells:
        name = str(cfg.get("name", cfg["user"]))
        initials = "".join(part[0] for part in name.split()[:2]).upper()
        cells = dots.text_cells(initials, grid, grid, margin=max(3, grid // 10), max_block=4)
    off = grid * pitch
    ox, oy = x + (size - off) / 2, y + (size - off) / 2
    dot = pitch - 1
    return (
        f'<defs><pattern id="whoami-led" x="{n(ox)}" y="{n(oy)}" width="{pitch}" height="{pitch}" '
        f'patternUnits="userSpaceOnUse"><circle cx="{n(dot / 2)}" cy="{n(dot / 2)}" r="{n(pitch * .19)}" '
        f'fill="{s["led_off"]}"/></pattern></defs>'
        f'<rect x="{n(x)}" y="{n(y)}" width="{n(size)}" height="{n(size)}" rx="10" fill="{s["bg"]}" stroke="{s["edge"]}"/>'
        f'<rect x="{n(ox)}" y="{n(oy)}" width="{n(off)}" height="{n(off)}" fill="url(#whoami-led)"/>'
        f'<path d="{dots.dash_rows(cells, ox, oy, pitch)}" fill="none" stroke="{s["text"]}" '
        f'stroke-width="{dot}" stroke-dasharray="{dot} 1"/>'
    )
