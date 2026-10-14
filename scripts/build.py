#!/usr/bin/env python3
"""Regenerate every profile asset and both READMEs from profile.yml.

    python scripts/build.py              # live numbers from the GitHub API
    python scripts/build.py --offline    # reuse the last numbers in assets/data/github.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import banner  # noqa: E402
import buttons  # noqa: E402
import ghdata  # noqa: E402
import radar  # noqa: E402
import readme  # noqa: E402
import stack  # noqa: E402
import whoami  # noqa: E402
from core import ASSETS, LANGS, ROOT, THEMES, load_config, t, write  # noqa: E402

CACHE = ASSETS / "data" / "github.json"
# Prefixes of files this script owns; old ones it no longer makes are deleted.
GENERATED = ("banner-", "contact-", "stack-", "pixellang-", "whoami-", "radar-")


def load_github(cfg: dict, offline: bool) -> dict:
    user = cfg["user"]
    if not offline:
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        try:
            data = ghdata.fetch(user, token)
            write(CACHE, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
            return data
        except Exception as exc:  # network error, rate limit, API change
            print(f"warning: GitHub API failed ({exc}); using the cached numbers", file=sys.stderr)
    if CACHE.exists():
        return json.loads(CACHE.read_text(encoding="utf-8"))
    return {"user": user}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--offline", action="store_true", help="do not call the GitHub API")
    args = ap.parse_args()

    cfg = load_config()
    gh = load_github(cfg, args.offline)
    written: dict[str, int] = {}

    def emit(name: str, svg: str) -> None:
        written[name] = write(ASSETS / name, svg)

    contacts = readme.contacts(cfg)
    for lang in LANGS:
        # The banner and whoami are black screens in both themes; each has a narrow phone version.
        emit(f"banner-{lang}.svg", banner.render(cfg, gh, lang))
        emit(f"banner-{lang}-mobile.svg", banner.render(cfg, gh, lang, banner.MOBILE))
        emit(f"whoami-{lang}.svg", whoami.render(cfg, gh, lang))
        emit(f"whoami-{lang}-mobile.svg", whoami.render(cfg, gh, lang, mobile=True))
        focus = [(t(a["label"], lang), float(a["value"])) for a in cfg["focus"]["axes"]]
        for theme in THEMES:
            emit(f"radar-focus-{lang}-{theme}.svg", radar.render(t(cfg["focus"]["title"], lang), focus, theme))
            for i, (kind, _) in enumerate(contacts):
                emit(f"contact-{kind}-{lang}-{theme}.svg", buttons.render(kind, theme, lang, primary=i == 0))
    for theme in THEMES:
        emit(f"stack-{theme}.svg", stack.render(cfg, theme))
        emit(f"stack-mobile-{theme}.svg", stack.render(cfg, theme, mobile=True))

    # Drop generated files that this run no longer produces (e.g. a removed contact).
    for old in ASSETS.glob("*.svg"):
        if old.name.startswith(GENERATED) and old.name not in written:
            old.unlink()
            print(f"removed {old.name}")

    for name, content in readme.build(cfg, gh).items():
        write(ROOT / name, content)

    total = sum(written.values())
    print(f"wrote {len(written)} SVGs ({total / 1024:.0f} KiB) + README.md + README.es.md")
    for name, size in sorted(written.items()):
        print(f"  {name:38s} {size / 1024:7.1f} KiB")


if __name__ == "__main__":
    main()
