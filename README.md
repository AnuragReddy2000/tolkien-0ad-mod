# Tolkien 0 A.D. Mod

An unofficial, fan-made total conversion for [0 A.D.](https://play0ad.com/),
targeting **0 A.D. Release 28 (0.28.0)**.

## Learn about the project

The [project site](https://anuragreddy2000.github.io/tolkien-0ad-mod/) introduces
the design and explains the setting, identity, and gameplay rationale behind
each civilization, including concepts that are not yet playable. See also the
project's [design documents](docs/).
To enable deployment, set the repository's **Settings → Pages → Build and
deployment → Source** to **GitHub Actions**.

Five Tolkien civilizations currently have playable mod data: **Doriath,
Lindon, Mordor, Moria, and Númenor**. Their faction descriptions, heroes,
technologies, distinctive structures, and effects are documented in the
civilization data and the site's [civilization guide](docs/civilizations.md).
The `tolkien_test` civ is retained for development and hidden from normal game
setup.

## Download and install

Versioned releases are published on the repository's
[Releases page](https://github.com/AnuragReddy2000/tolkien-0ad-mod/releases).
Each release archive contains a top-level `tolkien/` folder and a SHA-256
checksum. The mod depends on 0 A.D. 0.28.0; players in a multiplayer match
must use compatible game and mod versions.

On Windows:

1. Download the ZIP from a release and extract it.
2. Copy the contained `tolkien` folder to
   `%USERPROFILE%\Documents\My Games\0ad\mods\`.
3. Confirm the final path is
   `%USERPROFILE%\Documents\My Games\0ad\mods\tolkien\mod.json`.
4. Enable **Tolkien: Total Conversion** in 0 A.D.'s Mod Selection screen and
   restart the game.

Push builds are available as GitHub Actions artifacts. They are useful for
testing but are not published releases; use a tagged release for a stable,
version-matched download.

## Repository layout

```text
tolkien-0ad-mod/
├── tolkien/              # installable 0 A.D. mod
│   ├── mod.json
│   ├── simulation/       # civs, technologies, templates, scripts
│   └── art/              # actors, meshes, animations, textures
├── docs/                 # GitHub Pages site and design documentation
├── tools/                # validation, packaging, and art-pipeline scripts
└── .github/workflows/    # CI packaging and Pages deployment
```

The game loads the `tolkien/` folder directly. `docs/` and `tools/` are
repository-only and are not part of the mod archive.

## Development

Run the same data and faction-catalog checks used by CI, then build a local
archive:

```powershell
python tools\validate_mod.py
python tools\package_mod.py --output-dir dist
```

The validator checks JSON/XML syntax and verifies that faction technology
catalogs match their technology files and that every listed technology is
reachable from a building's `Researcher` list. The packager produces a ZIP
with the mod version, includes the software license and asset credits, and
writes a SHA-256 checksum. Release tags must match the mod version in
`tolkien/mod.json` (for example, `v0.0.1`).

For iterative development on Windows, a junction can point the game's user
mods folder to this checkout. From the repository root, run:

```bat
mklink /J "%USERPROFILE%\Documents\My Games\0ad\mods\tolkien" "%CD%\tolkien"
```

For a headless engine smoke test, run the game's `pyrogenesis.exe` with:

```powershell
& "$env:LOCALAPPDATA\0 A.D. Empires Ascendant\binaries\system\pyrogenesis.exe" `
  --mod=mod --mod=public --mod=tolkien `
  --autostart=random/alpine_lakes --autostart-players=2 `
  --autostart-civ=1:doriath --autostart-civ=2:athen `
  --autostart-seed=42 --autostart-nonvisual --autostart-disable-replay
```

The engine log is under `%LOCALAPPDATA%\0ad\logs\`. Pass repeated `--mod`
options rather than a comma-separated list. Keep the following implementation
conventions for new content:

- Reuse vanilla classes and component layouts so Petra AI can play the civs.
- Keep faction-specific values in faction child templates.
- Use the engine's seeded RNG in simulation scripts, never `Math.random()`.
- Preserve the `<Promotion disable=""/>` override on custom infantry templates
  that inherit a promotion component without an entity definition.

## Credits and licensing

See [`tolkien/ASSET-CREDITS.md`](tolkien/ASSET-CREDITS.md) for asset-level
attributions and license notes. The root [`LICENSE`](LICENSE) covers original
software only; it does not replace the licenses of third-party or 0 A.D.
assets. This Tolkien fan project is not affiliated with or endorsed by the
Tolkien Estate, Middle-earth Enterprises, or Wildfire Games.
