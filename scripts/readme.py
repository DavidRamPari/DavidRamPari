"""Fill templates/README.<lang>.md with blocks built from profile.yml."""

from __future__ import annotations

import re
from typing import Any

import banner
import buttons
import stack
import whoami
from core import ROOT, t

OUTPUT = {"en": "README.md", "es": "README.es.md"}
GAME_NAMES = {"pacman": "Pac-Man", "bomberman": "Bomberman", "galaga": "Galaga", "breakout": "Breakout",
              "puzzle-bobble": "Puzzle Bobble", "minesweeper": "Minesweeper"}


PHONE = "(max-width: 600px)"


def picture(stem: str, alt: str, width: int | None = None, mobile: str | None = None) -> str:
    """<picture> that swaps between the -dark and -light version of an asset.
    With `mobile`, phones get `{mobile}-dark/-light.svg` instead (a narrower layout)."""
    w = f' width="{width}"' if width else ""
    phone = ""
    if mobile:
        phone = (f'<source media="{PHONE} and (prefers-color-scheme: dark)" srcset="{mobile}-dark.svg">'
                 f'<source media="{PHONE} and (prefers-color-scheme: light)" srcset="{mobile}-light.svg">')
    return (f'<picture>{phone}<source media="(prefers-color-scheme: dark)" srcset="{stem}-dark.svg">'
            f'<source media="(prefers-color-scheme: light)" srcset="{stem}-light.svg">'
            f'<img src="{stem}-light.svg" alt="{alt}"{w}></picture>')


def screen(stem: str, alt: str, width: int) -> str:
    """A black screen (same in both themes) with a narrower file for phones."""
    return (f'<picture><source media="{PHONE}" srcset="{stem}-mobile.svg">'
            f'<img src="{stem}.svg" alt="{alt}" width="{width}"></picture>')


def _remote_picture(base: str, alt: str) -> str:
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="{base}-dark.svg">'
            f'<source media="(prefers-color-scheme: light)" srcset="{base}.svg">'
            f'<img src="{base}.svg" alt="{alt}" width="100%"></picture>')


def _join(items: list[str], lang: str) -> str:
    """'a, b and c' / 'a, b y c'."""
    items = [str(i) for i in items]
    if len(items) < 2:
        return "".join(items)
    return ", ".join(items[:-1]) + (" y " if lang == "es" else " and ") + items[-1]


def contacts(cfg: dict[str, Any]) -> list[tuple[str, str]]:
    """Non-empty contacts in the order of profile.yml. The first one is the main one."""
    return [(k, v) for k, v in (cfg.get("contacts") or {}).items() if v and k in buttons.LABELS]


def blocks(cfg: dict[str, Any], gh: dict[str, Any], lang: str) -> dict[str, str]:
    user = cfg["user"]
    es = lang == "es"
    out: dict[str, str] = {}

    out["lang_switch"] = "[English](README.md) / **Español**" if es else "**English** / [Español](README.es.md)"
    # Banner and whoami are black screens in both themes: one file per language.
    out["banner"] = screen(f"assets/banner-{lang}", banner.describe(cfg, lang), 960)
    out["headline"] = t(cfg["headline"], lang)
    out["pitch"] = " ".join(str(t(cfg["pitch"], lang)).split())
    out["open_to"] = str(t(cfg["open_to_line"], lang))

    links = []
    for kind, value in contacts(cfg):
        links.append(f'<a href="{buttons.link(kind, value)}">'
                     f'{picture(f"assets/contact-{kind}-{lang}", buttons.LABELS[kind][lang])}</a>')
    out["contacts"] = "\n".join(links)

    head = "| Área | Qué hago |" if es else "| Area | What I do |"
    rows = [head, "| --- | --- |"]
    for item in cfg.get("offer", []):
        rows.append(f"| {t(item['title'], lang)} | {t(item['body'], lang)} |")
    out["offer"] = "\n".join(rows)

    out["whoami"] = screen(f"assets/whoami-{lang}", whoami.describe(cfg, gh, lang), 960)

    head = "| Proyecto | Qué hace | Stack |" if es else "| Project | What it does | Stack |"
    rows = [head, "| --- | --- | --- |"]
    for pr in cfg.get("projects", []):
        if pr.get("show") is False:
            continue
        label = t(pr["name"], lang)
        title = f"[{label}]({pr['url']})" if pr.get("url") else label
        rows.append(f"| {title} | {t(pr['desc'], lang)} | {', '.join(pr.get('stack') or [])} |")
    out["projects"] = "\n".join(rows)

    out["stack"] = picture("assets/stack", stack.describe(cfg, lang), mobile="assets/stack-mobile")
    out["radars"] = picture(f"assets/radar-focus-{lang}", t(cfg["focus"]["title"], lang), 420)
    out["radar_note"] = t(cfg["focus"]["note"], lang)

    games = cfg.get("arcade", {}).get("games", [])
    raw = f"https://raw.githubusercontent.com/{user}/{user}/output"
    suffix = " jugando mi gráfico de contribuciones" if es else " playing my contribution graph"
    out["arcade"] = "\n\n".join(
        _remote_picture(f"{raw}/{g}-contribution-graph", GAME_NAMES.get(g, g) + suffix) for g in games)
    out["updated"] = (gh.get("fetched_at") or "")[:10]
    return out


def render(template: str, values: dict[str, str]) -> str:
    def sub(m: re.Match) -> str:
        key = m.group(1)
        if key not in values:
            raise KeyError(f"unknown template field: {key}")
        return values[key]
    text = re.sub(r"\{\{\s*(\w+)\s*\}\}", sub, template)
    # Blocks that came out empty leave blank lines behind; keep at most one.
    return re.sub(r"\n{3,}", "\n\n", text)


def build(cfg: dict[str, Any], gh: dict[str, Any]) -> dict[str, str]:
    files = {}
    for lang, out_name in OUTPUT.items():
        template = (ROOT / "templates" / f"README.{lang}.md").read_text(encoding="utf-8")
        files[out_name] = render(template, blocks(cfg, gh, lang))
    return files
