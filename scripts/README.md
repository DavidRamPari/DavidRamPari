# How this profile works

Everything on the profile is generated from [`profile.yml`](../profile.yml) by plain Python. No image comes from a third-party service: the scripts draw every SVG and commit it to this repo.

| File | What it does |
| --- | --- |
| `build.py` | Entry point. Reads `profile.yml`, fetches two live numbers from GitHub, writes every SVG and both READMEs |
| `banner.py` | The LED banner: name (or avatar) turning into the stack, the `profile.yml` panel and the scrolling line |
| `whoami.py` | The `$ whoami` card |
| `radar.py` | The focus-areas radar |
| `stack.py` | The tech stack strip |
| `buttons.py` | The contact buttons |
| `icons.py` | Single-colour logos from `assets/icons` |
| `typeset.py` | Turns text into outlines with the fonts in `assets/fonts`, so it looks the same on every device |
| `dots.py`, `pixelfont.py` | LED letters, avatar dithering and the dot paths that move between shapes |
| `ghdata.py` | Reads public repos and contributions from the GitHub API |

Two workflows run every day:

- `.github/workflows/profile.yml` runs `build.py` and commits the result.
- `.github/workflows/arcade.yml` plays the contribution graph as the games listed in `profile.yml` (via `abozanona/pacman-contribution-graph`, pinned to a release) and publishes them to the `output` branch.

Run it on your machine:

```bash
pip install -r requirements.txt
python scripts/build.py --offline          # reuses assets/data/github.json
GITHUB_TOKEN=... python scripts/build.py   # live numbers
```

Credits: the fonts are IBM Plex Sans and IBM Plex Mono (SIL Open Font License, `assets/fonts`); `typeset.ROLES` says which file each role uses. Logos come from Simple Icons (CC0) and skill-icons (MIT), see `assets/icons/README.md`. The idea of a profile drawn by its own scripts comes from [@macu-dev](https://github.com/macu-dev); the code here is written from scratch.

---

## Cómo funciona (español)

Todo sale de [`profile.yml`](../profile.yml). Edítalo y haz push: la Action "Build profile" vuelve a dibujar las imágenes y los dos README.

- **Tu avatar en el banner:** guarda la imagen como `assets/source/avatar.png` (cuadrada y con fondo liso). Los puntos LED la dibujan en lugar de tu nombre.
- **Contactos:** llena `contacts`. El primero que tenga valor lleva el borde amarillo.
- **Juegos arcade:** se eligen en `arcade.games`.
