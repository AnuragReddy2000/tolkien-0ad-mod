# Sketchfab → 0 A.D. Unit Adoption Guide

Repeatable pipeline for turning a Sketchfab character model into a fully
animated 0 A.D. unit. Written from the cave-troll adoption
(`tools/art_build/build_troll_rig.py`) — every pitfall below actually bit us.

## 0. Case-study numbers (troll)

| Item | Value |
|---|---|
| Source | LOTR Cave Troll by Ole Gunnar Isager, CC-BY 4.0, A-pose, no rig/anims |
| Download | GLB 1k (6.6 MB), 3 meshes, ~17.9k tris / 9.5k verts, 2 materials |
| Export | 2842 verts, ~5.5k tris, 1 material, 512px PNG, 102-bone Biped rig |
| Anims | custom tall idle + 5 retargeted stock anims (walk/run/2×melee/capture) |
| Template | `template_unit_infantry_melee` parent, 2.5×2.5 footprint |

## 1. License first (before any download)

* Acceptable: **CC-BY**, CC0, CC-BY-SA (0 A.D. art is CC-BY-SA; GPL code + CC art coexist in mods).
* Avoid: NC (non-commercial), ND (no-derivatives — decimation/rigging violates it), "Editorial", or murky "fan-art of film IP" uploads with no license stated.
* Sketchfab requires login + license accept to download. The repo must **never**
  bundle the download — only your derived files.
* Ship a `troll_CREDITS.txt`-style sidecar next to every derived mesh:
  author, source URL, license, what you changed.

## 2. Which download format

* **GLB (single file) — preferred.** Blender 3.0's glTF importer preserves UVs
  and PBR linkage; one file can't lose sidecars.
* Texture size: **1k is enough** — 0 A.D. units target 512px, so 4k only costs
  RAM/time. (Troll: 6.6 MB 1k vs 44 MB 4k, identical in-game result.)
* Avoid `.obj` (loses material/texture links, splits parts) and `.usdz`
  (Blender 3.0's USD support is weak).

## 3. Prerequisites

* Blender 3.0 headless: `C:\Program Files\Blender Foundation\Blender 3.0\blender.exe`
  (`blender --background --python <script> -- <args>`). No standalone Python needed.
* 0 A.D. install: `%LOCALAPPDATA%\0 A.D. Empires Ascendant\binaries\system\`
  (`pyrogenesis.exe`), logs at `%LOCALAPPDATA%\0ad\logs\interestinglog.html`
  (warnings+errors only — your first stop for every failure).
* Stock art sources:
  * Set `ZEROAD_REFERENCE_ART` to the extracted reference-art directory,
    containing `meshes_skeletal_new_m_tunic_short.dae` (the stock Biped
    armature) and, for rig-retarget scripts, a `stock_anim/` subdirectory.
  * Set `ZEROAD_SOURCE_MOD` to the installed 0 A.D. `public` mod directory
    when a build or preview script reads base-game actors, meshes, or textures.
  * `.../binaries/data/mods/public/public.zip` — readable `art/skeletons/*.xml`,
    `art/variants/biped/*.xml`. Animations exist there **only** as
    `.cached.psa` binaries (durations unreadable) — get source `.dae` anims from
    GitHub: `https://raw.githubusercontent.com/0ad/0ad/master/binaries/data/mods/public/art/animation/biped/...`
    (same for reference meshes per `docs/art-unit-template.md` §0).
* External model inputs are not bundled. Scripts that need a downloaded model
  read its path from the environment variable named in that script and stop
  with an error when it is missing; for example, `CAVE_ENTRANCE_SOURCE_MODEL`
  and `DWARF_HELMET_SOURCE_MODEL`.

## 4. Hard engine constraints (do not negotiate with these)

* **32768 verts/mesh max.** Budget ~2–5k tris for troops, ~5–6k for
  elephant-class. Decimate with UV preservation + symmetry.
* **One material per mesh**, one UV layer. Multi-material sources must merge
  (accept that two textures become one — see §7).
* Textures power-of-two, ≤2048 (512px PNG is the unit sweet spot).
* Mesh must be **triangulated**, normals outward, feet on Z=0, centered on XY.
* Skeletal units must reuse **stock bone names** (`art/skeletons/biped.xml`) —
  then all stock animations retarget by name automatically, no `skeleton.xml`.
* **Animation `speed` = playback factor `value/100`** (engine:
  `ObjectBase.cpp` — `speed/100.f`). Blender exports key times in **seconds**
  (@scene fps), so a 33-frame file ≈ 1.1 s intrinsic. Consequence: copying stock
  *values* only works on stock-*duration* files. Custom files need speed math:
  `speed = 100 × intrinsic_seconds / desired_cadence` (e.g. run 1.1 s → 0.65 s
  cycle needs ~170, not the stock 8 — stock 8 on your file = 13 s statue).
* Templates: humanoids parent to `template_unit_infantry_melee` (NOT elephant —
  quadruped skeleton/sounds), keep `<Promotion disable=""/>`, and any
  `<Footprint>` override **must** carry `replace=""` or RelaxNG validation fails
  (`Extra element Square in interleave`) and the whole entity silently vanishes.

## 5. Pipeline (mirror `build_troll_rig.py`)

1. **Import reference body** → keep the `Biped` armature, delete its mesh.
   Record its height (≈3.85 game units for a human).
2. **Import source** (glTF/FBX/OBJ). Multi-part scenes position parts via
   object + parent-EMPTY node transforms — **bake them before joining**
   (`parent_clear(CLEAR_KEEP_TRANSFORM)` per object, then `transform_apply`
   location+rotation+scale), else `join()` merges raw local coords into a
   scrambled sprawl. Log assembled bounds as a sanity check.
3. **Cleanup + decimate** to target tris (remove doubles/loose, collapse with
   triangulate + symmetry, explicit triangulate, recalc normals).
4. **Single UV/material.** If no UVs, cube-project (and plan a manual unwrap).
   If merging materials, expect cross-part color bleeding (see §7).
5. **Scale** to `ref_height × creature_factor` (troll 1.8× ≈ 6.93 units),
   center XY, feet to Z=0. Game uses raw local coords — meters are irrelevant.
6. **Fit armature**: scale uniformly to match, widen arm/leg bone chains for
   bulk (troll: arms ×1.45, legs ×1.12 — wider drags the waist, see §7).
7. **Restrict to the 24 deform bones** (`hip/spine/spine1/chest/neck/head`,
   shoulders/arms/forearms/hands/fingers/fingertips ×L/R, thighs/legs/feet ×L/R)
   — `use_deform=False` on everything else (all `prop-*`, IK targets, sheaths…).
   Skipping this lets heat weights grab marker bones and the idle animation
   stretches verts into spikes. Also exclude `cape1-3` unless there's a cape.
8. **Parent with automatic weights**, then smooth deform groups
   (`vertex_group_smooth ALL ×4`) to soften chest↔hip↔thigh bands.
9. **Pick largest source image → 512px baseTex.** Log which one.
10. **Export mesh DAE** (`selected=True, include_animations=False`) + credits.
11. **Custom idle** (optional but recommended for non-humans): author tiny
    quaternion keys in rest pose (shared QUATERNION mode with retargets below).
12. **Retarget stock anims**: import each stock `.dae`, copy its action's
    fcurves onto your armature — limbs verbatim, **torso dampened**
    (spine 0.4, chest 0.45, neck 0.6, head 0.5 via quaternion-angle scaling),
    hip-location deltas × creature scale, key **times verbatim** (keeps stock
    speeds valid), deform bones only. Export one anim DAE each
    (`include_animations=True, include_all_actions=False`).
    For melee, additionally lock `finger*` to rest (damp 0) and calm `hand*`
    (~0.45) — human grip-release splays giant fingers; wrists corkscrew.
13. **Variants**: mod-side `art/variants/biped/<unit>_relax.xml` (custom
    idle/walk/run + stock or retargeted melee), `<unit>_capture.xml` if needed.
14. **Actor** `art/actors/units/<civ>/<unit>.xml`: mesh + textures + variant
    files + `player_trans_norm_spec` material. **Template** `VisualActor` →
    your actor.
15. **Verify** (§6), test in Atlas action by action.

## 6. Verification checklist

* Blender numeric checks (all scriptable headless): assembled bounds sane;
  source-vs-export width profile ≈1.00 per height band (catches decimate damage
  vs sculpt intent); final bounds (X width, Y depth, Z 0→height); bone heads
  (feet ~0.2, hip ~55% height, head ~98%); vertex-group histogram ⊆ deform set
  with no marker groups; anim DAEs contain `library_animations` with expected
  joint counts.
* `xmllint`-equivalent: parse every new/edited XML with Python before launching.
* Headless engine run (60 s autostart) → `interestinglog.html` must be 0 bytes.
* Atlas: place the unit, play idle/walk/run/attack/capture/death one at a time,
  screenshot each. Blind-authored values always need one visual pass.

## 7. Bug gallery (symptom → cause → fix)

| Symptom | Cause | Fix |
|---|---|---|
| Sprawled parts soup, 27 units wide | Joined multi-part scene without baking node transforms | `parent_clear` + `transform_apply` before `join` |
| Spikes through torso on idle | Weights on ~75 `prop-*`/IK marker bones | `use_deform=False` except the 24-bone set |
| Upper-back crease | Back verts grabbed `cape1-3` | Exclude capes without a cape mesh |
| Entity missing, `Extra element Square in interleave` | `<Footprint>` without `replace=""` vs parent `<Circle>` | Add `replace=""` |
| Run frozen mid-pose, walk OK | Copied stock speeds (run 8) onto 1.1 s file → 13 s cycle | Speed math per §4 (run→~170) or retarget (inherits stock timing) |
| Human sprint-crouch on monster | Stock relax/run lean on non-human mass | Custom tall idle; retarget with torso dampening |
| Splayed waving fingers, twisted wrists in melee | Human grip/sword-roll on giant hands | Lock `finger*` to rest, `hand*` ×0.45 in melee |
| Pale flashes on palms/inner arms | Merged materials share one texture; islands land anywhere | Accept, or split textures (atlas rework) |
| Symmetric waist dent, weights innocent | Mirror decimate **or the source sculpt itself** — measure! | Source-vs-export band profile decides: sculpt intent (leave or sculpt-edit) vs decimate damage (raise tri target) |
| Legs hidden by loincloth | Source anatomy + idle crouch | Don't reshape silently — confirm sculpt-edit with requester |

## 8. Runbook (adapt paths/names per unit)

```bat
:: 0. manual: download GLB (1k) from Sketchfab to Downloads, accept license
:: 1. manual: fetch stock anims you plan to retarget into %TEMP%\0ad_ref\stock_anim\
:: 2. rig + mesh + idle + retargets + variants (clone build_troll_rig.py first:
::    TARGET_TRIS, creature scale, WIDEN_*, DAMP_*, RETARGET_JOBS, variant speeds)
"C:\Program Files\Blender Foundation\Blender 3.0\blender.exe" --background ^
  --python tools\art_build\build_troll_rig.py -- C:\Users\<you>\Downloads\<model>.glb
:: 3. actor XML + template VisualActor wiring (hand-edit, then XML-parse check)
:: 4. headless check: 60 s autostart, interestinglog.html must be empty
:: 5. Atlas per-action screenshots; tune amps/speeds/damps; re-run from step 2
```

One rule above all: **measure before morphing**. Every "looks off" so far was
either a pipeline bug (fix the script), a speed mismatch (do the math), or the
author's sculpt (confirm before deviating). The numeric checks in §6 tell you
which within minutes.
