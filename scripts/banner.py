"""The banner: an LED board where your avatar (or name) turns into your stack,
next to the real profile.yml that builds this page and a scrolling availability line.

It is black in both themes, like a physical LED sign. Yellow is the only colour:
the frame, the stars in the scrolling line and the cursor.

Two layouts: `desktop` (1200 wide, with the profile.yml panel) and `mobile`
(600 wide, only the board and the scrolling line, so it stays legible on a phone).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import dots
import pixelfont
import typeset as ts
from core import ROOT, n, svg_open, t

COLS, ROWS = 96, 70
TRAVELLERS = 360
HOLD_FIRST, HOLD_WORD, MOVE = 3.2, 2.2, 1.1
LOOPS = 3                      # the board plays three rounds, then rests on the first shape
MARQUEE_HOLD, MARQUEE_SPEED, MARQUEE_LOOPS = 2.5, 70, 2
CURSOR_BLINKS = 12

BOARD = {
    "bg": "#000000", "edge": "#262626", "led_off": "#1C1C1C",
    "text": "#FFFFFF", "muted": "#8C8C8C", "key": "#A3A3A3", "dim": "#7A7A7A",
    "yellow": "#FFD60A",
}

CODE = ts.Style("mono", 15, features=(("calt", False), ("liga", False)))
CODE_NUM = ts.Style("mono", 12)
FILE = ts.Style("sans-medium", 13)

STYLE = (
    "<style>"
    ".still{display:none}"
    "@media (prefers-reduced-motion: reduce){.moving{display:none}.still{display:inline}}"
    "</style>"
)


@dataclass(frozen=True)
class Layout:
    width: float
    height: float
    hud_y: float
    hud_scale: float
    hud_repos: bool                         # room for the third HUD item
    rule_y: float
    panel: tuple[float, float, float, float]  # LED panel x, y, w, h
    pitch: float
    code: tuple[float, float, float, float] | None
    marquee: tuple[float, float, float, float]
    marquee_scale: float


def desktop(hud: bool) -> Layout:
    """1200 wide: LED board on the left, profile.yml and the scrolling line on the right."""
    top = 86 if hud else 24          # the arcade header takes the first 62 px
    return Layout(1200, top + 300 + (34 if hud else 24), 33, 3, True, 72, (40, top, 400, 300), 4,
                  (464, top, 696, 244), (464, top + 256, 696, 44), 3)


def mobile(hud: bool) -> Layout:
    """600 wide for phones: only the LED board and the scrolling line."""
    top = 84 if hud else 24
    return Layout(600, top + 448 + (28 if hud else 24), 30, 3, False, 68, (24, top, 552, 386), 5,
                  None, (24, top + 402, 552, 46), 2.4)


DESKTOP, MOBILE = "desktop", "mobile"


def describe(cfg: dict[str, Any], lang: str) -> str:
    """Alt text: what the banner shows, in plain words."""
    first_word = str(cfg.get("name", cfg["user"])).split()[0].upper()
    avatar = cfg.get("banner", {}).get("avatar")
    has_avatar = bool(avatar) and (ROOT / avatar).exists()
    words = [w.upper() for w in cfg.get("banner", {}).get("words", [])]
    sep = " y " if lang == "es" else " and "
    listed = ", ".join(words[:-1]) + sep + words[-1] if len(words) > 1 else "".join(words)
    line = str(t(cfg["open_to_line"], lang))
    if lang == "es":
        first = "mi avatar" if has_avatar else first_word
        return (f"Banner animado. En un tablero LED los puntos forman {first} y luego {listed}. "
                f"Al lado está el profile.yml que genera esta página. Abajo pasa una línea: {line}")
    first = "my avatar" if has_avatar else first_word
    return (f"Animated banner. On an LED board the dots draw {first} and then {listed}. "
            f"Next to it is the profile.yml that generates this page. Below, a scrolling line: {line}")


def render(cfg: dict[str, Any], gh: dict[str, Any], lang: str, layout: str = DESKTOP) -> str:
    b = BOARD
    hud = bool(cfg.get("banner", {}).get("hud"))
    L = desktop(hud) if layout == DESKTOP else mobile(hud)
    name = cfg.get("name", cfg["user"])
    parts = [
        svg_open(L.width, L.height, f"{name}, {t(cfg['role'], lang)}", describe(cfg, lang)),
        STYLE,
        _defs(L),
        f'<rect x="1" y="1" width="{n(L.width - 2)}" height="{n(L.height - 2)}" rx="18" fill="{b["bg"]}" '
        f'stroke="{b["yellow"]}" stroke-width="2"/>',
    ]
    if hud:
        parts += [
            _hud(cfg, gh, lang, L),
            f'<path d="M{n(L.panel[0] - 6)} {n(L.rule_y)}H{n(L.width - L.panel[0] + 6)}" stroke="{b["edge"]}"/>',
        ]
    parts += [
        _matrix(cfg, L),
        _code(cfg, lang, L) if L.code else "",
        _marquee(cfg, lang, L),
        "</svg>",
    ]
    return "".join(parts)


def _origin(L: Layout) -> tuple[float, float]:
    x, y, w, h = L.panel
    return x + (w - COLS * L.pitch) / 2, y + (h - ROWS * L.pitch) / 2


def _defs(L: Layout) -> str:
    b = BOARD
    mx, my = _origin(L)
    r = L.pitch * 0.19
    c = (L.pitch - 1) / 2
    x, y, w, h = L.marquee
    return (
        "<defs>"
        f'<pattern id="led" x="{n(mx)}" y="{n(my)}" width="{n(L.pitch)}" height="{n(L.pitch)}" '
        f'patternUnits="userSpaceOnUse"><circle cx="{n(c)}" cy="{n(c)}" r="{n(r)}" fill="{b["led_off"]}"/></pattern>'
        f'<clipPath id="marquee"><rect x="{n(x + 8)}" y="{n(y)}" width="{n(w - 16)}" height="{n(h)}" rx="6"/></clipPath>'
        "</defs>"
    )


# --------------------------------------------------------------------------- HUD

def _hud(cfg: dict[str, Any], gh: dict[str, Any], lang: str, L: Layout) -> str:
    b = BOARD
    scale, y = L.hud_scale, L.hud_y
    contributions = gh.get("contributions")
    repos = gh.get("public_repos")
    score = f"{contributions:06d}" if isinstance(contributions, int) else "------"
    repo_txt = f"{repos:02d}" if isinstance(repos, int) else "--"
    player = str(cfg.get("name", cfg["user"])).split()[0].upper()
    labels = {"en": ("1UP", "HI-SCORE", "REPOS"), "es": ("1UP", "RÉCORD", "REPOS")}[lang]
    margin = L.panel[0] + 4

    def pair(label: str, value: str, x: float) -> tuple[str, float]:
        lw = pixelfont.text_width(label, scale)
        d1 = pixelfont.path(label, x, y, scale)
        d2 = pixelfont.path(value, x + lw + 14, y, scale)
        width = lw + 14 + pixelfont.text_width(value, scale)
        return f'<path d="{d1}" fill="{b["muted"]}"/><path d="{d2}" fill="{b["text"]}"/>', width

    left, _ = pair(labels[0], player, margin)
    mid_svg, mid_w = pair(labels[1], score, 0)
    if not L.hud_repos:  # phone: player on the left, score on the right
        return left + f'<g transform="translate({n(L.width - margin - mid_w)} 0)">{mid_svg}</g>'
    right_svg, right_w = pair(labels[2], repo_txt, 0)
    mid = f'<g transform="translate({n((L.width - mid_w) / 2)} 0)">{mid_svg}</g>'
    right = f'<g transform="translate({n(L.width - margin - right_w)} 0)">{right_svg}</g>'
    return left + mid + right


# --------------------------------------------------------------------------- LED matrix

def _shapes(cfg: dict[str, Any]) -> list[set[dots.Cell]]:
    banner = cfg.get("banner", {})
    first = None
    avatar = banner.get("avatar")
    if avatar:
        first = dots.avatar_cells(ROOT / avatar, COLS, ROWS, "dark")
    if not first:
        first = dots.text_cells(str(cfg.get("name", cfg["user"])).split()[0].upper()[:7], COLS, ROWS)
    words = [w.upper()[:6] for w in banner.get("words", [])]
    return [first] + [dots.text_cells(w, COLS, ROWS) for w in words]


def _matrix(cfg: dict[str, Any], L: Layout) -> str:
    b = BOARD
    x, y, w, h = L.panel
    mx, my = _origin(L)
    pitch = L.pitch
    dot = pitch - 1
    shapes = _shapes(cfg)
    k = len(shapes)

    # Timeline: hold the first shape, then for every word move + hold, then move back.
    times = [0.0, HOLD_FIRST]
    for _ in range(1, k):
        times += [times[-1] + MOVE, times[-1] + MOVE + HOLD_WORD]
    times.append(times[-1] + MOVE)
    loop = times[-1]
    key_times = ";".join(f"{v / loop:.4f}".rstrip("0").rstrip(".") or "0" for v in times)
    frame_shape = [0, 0] + [i for i in range(1, k) for _ in (0, 1)] + [0]
    repeat = f'dur="{n(loop)}s" repeatCount="{LOOPS}" fill="freeze"'

    first_rows = dots.dash_rows(shapes[0], mx, my, pitch)
    out = [
        f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="10" fill="{b["bg"]}" stroke="{b["edge"]}"/>',
        f'<rect x="{n(mx)}" y="{n(my)}" width="{n(COLS * pitch)}" height="{n(ROWS * pitch)}" fill="url(#led)"/>',
        # What people who prefer reduced motion see: the first shape, still.
        f'<path class="still" d="{first_rows}" fill="none" stroke="{b["text"]}" '
        f'stroke-width="{n(dot)}" stroke-dasharray="{n(dot)} 1"/>',
        '<g class="moving">',
    ]

    # Dense layers: every dot of a shape, shown only while that shape holds.
    for idx, cells in enumerate(shapes):
        values = ";".join("1" if s == idx else "0" for s in frame_shape)
        base = "1" if idx == 0 else "0"
        out.append(
            f'<path d="{dots.dash_rows(cells, mx, my, pitch)}" fill="none" stroke="{b["text"]}" '
            f'stroke-width="{n(dot)}" stroke-dasharray="{n(dot)} 1" opacity="{base}">'
            f'<animate attributeName="opacity" {repeat} keyTimes="{key_times}" values="{values}"/></path>'
        )

    # Travellers: the same dots in every shape (Hilbert-ordered), gliding between them.
    samples = [dots.ordered_sample(c, TRAVELLERS) for c in shapes]
    for i in range(TRAVELLERS):
        pts = [samples[s][i] for s in frame_shape]
        vals = ";".join(f"{n(mx + c * pitch)} {n(my + r * pitch)}" for c, r in pts)
        c0, r0 = pts[0]
        out.append(
            f'<path d="M0 0h{n(dot)}v{n(dot)}h-{n(dot)}z" fill="{b["text"]}" '
            f'transform="translate({n(mx + c0 * pitch)} {n(my + r0 * pitch)})">'
            f'<animateTransform attributeName="transform" type="translate" {repeat} '
            f'keyTimes="{key_times}" values="{vals}"/></path>'
        )
    out.append("</g>")
    return "".join(out)


# --------------------------------------------------------------------------- profile.yml panel

def _yaml_lines(cfg: dict[str, Any], lang: str) -> list[list[tuple[str, str]]]:
    """The fields of profile.yml shown in the banner, as (token class, text) pairs."""
    names = {s["id"]: s["label"] for s in cfg["stack"]["items"]}
    stack = [names.get(s, s) for s in cfg["stack"]["main"]]
    comment = t(cfg["banner"]["file_comment"], lang)
    location = f"{t(cfg['location'], lang)} ({cfg['timezone']})" if cfg.get("timezone") else t(cfg["location"], lang)

    def item(key: str, value: str | list[str]) -> list[tuple[str, str]]:
        head = [("k", key), ("p", ": ")]
        if isinstance(value, list):
            body: list[tuple[str, str]] = [("p", "[")]
            for i, v in enumerate(value):
                body += [("v", v)] + ([("p", ", ")] if i < len(value) - 1 else [])
            return head + body + [("p", "]")]
        return head + [("v", value)]

    return [
        [("c", comment)],
        item("name", str(cfg["name"])),
        item("role", t(cfg["role"], lang)),
        item("studies", t(cfg["studies"], lang)),
        item("location", location),
        item("stack", stack),
        item("open_to", list(t(cfg["open_to"], lang))),
    ]


def _code(cfg: dict[str, Any], lang: str, L: Layout) -> str:
    b = BOARD
    x, y, w, h = L.code
    color = {"c": b["dim"], "k": b["key"], "v": b["text"], "p": b["dim"]}
    out = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{b["bg"]}" stroke="{b["edge"]}"/>',
        f'<path d="M{x} {y + 34}H{x + w}" stroke="{b["edge"]}"/>',
        ts.text(FILE, "profile.yml", x + 20, y + 22, b["muted"]),
    ]
    lines = _yaml_lines(cfg, lang)
    line_h = 26
    top = y + 66
    end_x = x + 44
    for i, toks in enumerate(lines):
        ly = top + i * line_h
        cursor = x + 44
        paths = []
        for kind, s in toks:
            paths.append(ts.text(CODE, s, cursor, ly, color[kind]))
            cursor += ts.width(CODE, s) + CODE.tracking * CODE.size
        end_x = cursor
        delay = 0.15 + i * 0.18
        out.append(ts.text(CODE_NUM, str(i + 1), x + 28, ly, b["dim"], anchor="end"))
        out.append(
            f'<g opacity="0">{"".join(paths)}'
            f'<set attributeName="opacity" to="1" begin="{n(delay)}s" fill="freeze"/></g>'
        )
    # Cursor after the last line: blinks for a while, then goes away.
    cy = top + (len(lines) - 1) * line_h - 14
    out.append(
        f'<rect class="moving" x="{n(end_x + 6)}" y="{n(cy)}" width="9" height="18" fill="{b["yellow"]}">'
        f'<animate attributeName="opacity" dur="1.1s" repeatCount="{CURSOR_BLINKS}" '
        f'keyTimes="0;.5;.5;1" values="1;1;0;0"/>'
        f'<set attributeName="opacity" to="0" begin="{n(1.1 * CURSOR_BLINKS)}s" fill="freeze"/></rect>'
    )
    return "".join(out)


# --------------------------------------------------------------------------- marquee

def _marquee(cfg: dict[str, Any], lang: str, L: Layout) -> str:
    """The line scrolls twice and comes back to its start. The text starts with a short
    phrase followed by spaces, so the resting position never cuts a word."""
    b = BOARD
    text = str(t(cfg["banner"]["marquee"], lang))
    scale = L.marquee_scale
    mx, my, mw, mh = L.marquee
    width = pixelfont.text_width(text, scale) + 6 * scale
    y = my + (mh - pixelfont.HEIGHT * scale) / 2
    x0 = mx + 16

    def draw(start: float) -> tuple[str, str]:
        """Letters in white, stars in yellow."""
        plain = text.replace("★", " ")
        letters = pixelfont.path(plain, start, y, scale)
        stars = ""
        for i, ch in enumerate(text):
            if ch == "★":
                stars += pixelfont.path("★", start + pixelfont.text_width(text[:i], scale) + scale, y, scale)
        return letters, stars

    l1, s1 = draw(x0)
    l2, s2 = draw(x0 + width)
    moving = (f'<g><path d="{l1}{l2}" fill="{b["text"]}"/><path d="{s1}{s2}" fill="{b["yellow"]}"/>'
              f'<animateTransform attributeName="transform" type="translate" from="0 0" to="{n(-width)} 0" '
              f'begin="{n(MARQUEE_HOLD)}s" dur="{n(width / MARQUEE_SPEED)}s" repeatCount="{MARQUEE_LOOPS}"/></g>')
    still = f'<g class="still"><path d="{l1}" fill="{b["text"]}"/><path d="{s1}" fill="{b["yellow"]}"/></g>'
    return (
        f'<rect x="{n(mx)}" y="{n(my)}" width="{n(mw)}" height="{n(mh)}" rx="8" fill="{b["bg"]}" stroke="{b["edge"]}"/>'
        f'<g clip-path="url(#marquee)"><g class="moving">{moving}</g>{still}</g>'
    )
