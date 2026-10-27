# Art Pipeline — Unit Creation Template (0 A.D. Tolkien Mod)

Purpose: a repeatable procedure for creating mod units (and later buildings) so any
LLM session can produce consistent results without re-deriving the trial-and-error
lessons. Read this fully before creating a new unit.

Existing reference implementation (reuse, don't rewrite from scratch):
- `tools/art_build/build_orcs.py`  — head surgery + procedural textures + .dae export
- `tools/art_build/render_previews.py` — assembles units and renders preview PNGs
- `mod/` — the working mod (orc warrior / spearman / archer)

---

## 0. Prerequisites

- Blender 3.0 headless: `C:\Program Files\Blender Foundation\Blender 3.0\blender.exe`
  Run scripts with: `blender --background --python <script.py>`
  (No standalone Python is installed; use Blender's bundled Python for all `bpy`/numpy work.)
- Base-game art source (GPL, free to use): GitHub mirror `0ad/0ad`, branch `master`
  (tracks trunk, matches 0.28.x art format). Raw files:
  `https://raw.githubusercontent.com/0ad/0ad/master/binaries/data/mods/public/<path>`
  Directory listings: `https://api.github.com/repos/0ad/0ad/contents/<path>?ref=master`
  (The official Gitea is behind an anti-bot challenge — use GitHub.)
- Download base assets to a temp ref folder (e.g. `%TEMP%\0ad_ref`) with flattened
  names (`meshes_props_new_dude_head.dae`, `props_head_pers_face_a.png`, ...).
- NEVER write into the user's 0 A.D. install. All output goes under `mod/` (repo root).

---

## 1. Mod directory layout (mirror the public mod's structure)

```
mod/                                        # repo-root mod folder (junction-linked into the game's mods dir)
  mod.json                                  # depends on mod=public
  art/
    actors/
      units/<faction>/<unit>.xml            # unit actor (binds body+props+anims)
      props/units/heads/<head>.xml          # custom head prop actor
      props/units/weapons/<weapon>.xml     # custom weapon prop actor (if any)
    meshes/
      props/new/<head>.dae                  # custom head mesh
      (bodies/weapons reused from public by path — do NOT copy)
    textures/skins/
      props/head/<face>.png                 # face/skin texture
      skeletal/tolkien/<body>_01.png       # body clothing/skin texture
previews/                                   # render output (not shipped)
tools/art_build/                            # build scripts
```

Key rule: the mod **depends on `public`**, so actor XML can reference any base-game
mesh/animation/material by its normal path. Only author the parts you change
(custom head, custom textures). Do not duplicate base assets.

---

## 2. Mental model of the 0 A.D. art system

A unit is assembled at runtime from:
- **Body mesh**: `art/meshes/skeletal/new/m_<build>.dae` (e.g. `m_armor_tunic_short`,
  `m_armor_pants_tunic_short`, `m_tunic_short`). Has a `Biped` armature with
  attachpoint bones: `head`, `helmet`, `weapon_R`, `weapon_bow`, `shield`, `back`, etc.
- **Prop actors** attached to bones: head, helmet, weapon, shield, quiver.
  Each prop is its own actor XML with its own mesh + textures.
- **Textures** per actor: `baseTex` (color), `normTex` (`default_norm.png`),
  `specTex` (`null_black.dds` / `null_white.dds`).
- **Animation variants**: shared XML in `art/variants/biped/` (NOT `art/animation/`).
  e.g. `biped/base_spearman_relax.xml`, `biped/base_swordsman_2hand_relax.xml`,
  `biped/base_archer_relax.xml`, plus `attack_capture`, `attack_slaughter`,
  `death_infantry`, gather/build/carry variants.
- **Material**: `player_trans_norm_spec.xml` (player-color tinted) or
  `objectcolor_norm_spec.xml` (props) or `no_trans_norm_spec.xml` (weapons).

Actor XML skeleton (see `orc_warrior.xml` for a filled example):
```xml
<actor version="1">
  <castshadow/>
  <group>
    <variant frequency="1" name="Base">
      <mesh>skeletal/new/m_armor_tunic_short.dae</mesh>
      <props>
        <prop actor="props/units/heads/orc_head.xml" attachpoint="head"/>
        <prop actor="props/units/weapons/orc_sword.xml" attachpoint="weapon_R"/>
      </props>
      <textures>
        <texture file="skeletal/tolkien/orc_leather_01.png" name="baseTex"/>
        <texture file="default_norm.png" name="normTex"/>
        <texture file="null_black.dds" name="specTex"/>
      </textures>
    </variant>
  </group>
  <group>
    <variant file="biped/base_swordsman_2hand_relax.xml"/>
    <variant file="biped/attack_capture.xml"/>
    <variant file="biped/attack_slaughter.xml"/>
    <variant file="biped/death_infantry.xml"/>
  </group>
  <group>
    <variant>
      <textures>
        <texture file="default_norm.png" name="normTex"/>
        <texture file="null_black.dds" name="specTex"/>
      </textures>
    </variant>
  </group>
  <material>player_trans_norm_spec.xml</material>
</actor>
```

---

## 3. SCALE CONVENTION (critical — caused the most bugs)

- The **game uses raw local coordinates** (ignores the .dae `<unit meter=...>`).
  In game units: body ≈ **3.85** tall, head ≈ **0.6** tall (correct human ratio).
- Blender's collada **importer applies an inch→meter scale (0.025)** to the head .dae
  as an object-scale artifact. The body imports at scale 1.
- THEREFORE: after importing the head, **set `head.scale = (1,1,1)`** before any
  vertex surgery or joining, so head local coords == game units.
  Verify: head world bounds should be ~z[-0.11, 0.48], y[-0.32, 0.27].
- Do NOT `transform_apply` the 0.025 scale (that bakes the head to 1.5 cm).
  Just zero the object scale; local coords are already the game coords.

---

## 4. Texture generation recipe (procedural, in Blender Python)

Use HSV recoloring with numpy. Core helpers are in `build_orcs.py`
(`rgb2hsv`, `hsv2rgb`, `mottle`, `save_np`).

Orc skin constants (tune per faction):
```
ORC_SKIN_H = 0.28   # grey-green hue
ORC_SKIN_S = 0.30
# value multiplier 0.32 (blacker); raise for lighter skin
```

Face texture (`gen_orc_skin`): recolor ALL pixels toward skin hue, preserve
luminance (so facial features still read), keep eyes yellow:
```
new_h = ORC_SKIN_H
new_s = clip(s*0.5, 0, 0.35)
new_v = v * 0.32
eye = (v>0.80) & (s<0.35)  ->  h=0.11, s=0.55, v=0.80
```
This also removes facial hair (beard becomes same color as skin).

Body texture (`recolor_body`): classify **warm tan pixels as skin** (→ orc green),
everything else as clothing (→ dark leather/iron):
```
skin = (h>0.02) & (h<0.13) & (s>0.18) & (v>0.25)
new_v = where(skin, v*0.32, v*cloth_vmul + 0.02)
```
`cloth_vmul` ~0.30 for leather, ~0.26 for iron. Add `mottle()` noise for grain.

CRITICAL SAVE BUG: do **not** call `img.pack()` — packed images write nothing to
disk on `save()`. Instead create a FRESH image and write pixels:
```
def save_np(arr, outp):
    img = bpy.data.images.new(name, w, h, alpha=True)
    out = ones((h,w,4)); out[...,:3] = clip(arr,0,1)
    img.pixels.foreach_set(out.ravel())
    img.filepath_raw = outp; img.file_format = "PNG"; img.save()
```

---

## 5. Head surgery recipe (vertex regions, head local space)

Face is +Y, up is +Z. Applied to `dude_head` (107 verts) in `build_orc_head()`:
- Skull cap `z>=0.40`: flatten `z = 0.40+(z-0.40)*0.80`, widen `x*=1.06`
- Brow ridge `0.26<=z<0.40 and y>0.08`: `y += 0.028`
- Broad prognathic jaw `z<0.17 and y>0`: `x*=1.22`, `y += 0.05*((0.17-z)/0.28)`
- Pointed ears `|x|>=0.185 and 0.15<z<0.32`: `x*=1.25`, `z += 0.06`
- Tusks: two 5-sided cones at mouth corners (±0.055, 0.165, 0.05)→(±0.062,0.195,0.128),
  joined into the head. Map tusk UVs to an EMPTY UV corner (detect the corner with
  0 existing loops; bottom-left was free) and paint that corner ivory in the texture.
- Single material slot; export with `collada_export(selected=True)`.

---

## 6. Preview render pipeline (`render_previews.py`)

- Engine `BLENDER_WORKBENCH`, `shading.light = "FLAT"`, `color_type = "TEXTURE"`,
  `show_cavity = True` → matte look. (STUDIO light adds a metallic specular that
  is a PREVIEW artifact only — the in-game shader with a black spec map reads matte.)
- Head placement: `align_head_to_body(head, body)` — keep head UPRIGHT with a slight
  forward lean (8° X); match the body's neck-opening center (avg of body verts with
  `z > zmax-0.28`) to the head's neck-base center (avg of head verts `z < -0.05`).
- Weapons: base-game broadsword/spear .dae are REJECTED by Blender's collada importer
  (game engine loads them fine). For previews only, build simple procedural
  scimitar/spear; the actor XML still references the real base-game weapon actors.
  The bow (`bow_greek.dae`) imports fine.

---

## 7. Step-by-step: adding a NEW unit

1. Pick a base body from `skeletal/new/` matching the silhouette you want.
2. Pick the animation variant set from `art/variants/biped/` for the weapon type.
3. Decide custom assets: usually reuse the faction head + textures already built.
   For a new head/weapon, extend `build_orcs.py` with a new builder function.
4. Write the unit actor XML under `art/actors/units/<faction>/<unit>.xml` using
   the skeleton in §2. Reference base bodies/anims by path; custom props by path.
5. If a new custom prop (head/weapon), add its prop actor XML + mesh + textures.
6. Add the unit to `render_previews.py` (clone a unit block) to get a preview.
7. Run build then render:
   `blender --background --python tools/art_build/build_orcs.py`
   `blender --background --python tools/art_build/render_previews.py`
8. Verify previews programmatically (you cannot see images): sample the render for
   the skin hue in each unit's column band to confirm heads are present/aligned.
9. Iterate on the specific knobs (skin value, jaw width, head seat offset) per
   user feedback.

---

## 8. Pitfalls & fixes (learned the hard way)

| Symptom | Cause | Fix |
|---|---|---|
| Head invisible / only tusks show | Head imported at 0.025 scale; tusks joined at world scale → 40× mismatch | Set `head.scale=(1,1,1)` before surgery/join (§3) |
| Head missing on 2nd/3rd unit | Body mesh is parented to armature; setting BOTH `body.location.x` and `arm.location.x` double-offsets the body, leaving head behind | Move ONLY the armature; the mesh follows |
| Head flipped / into body | Used `pose.bone.matrix` for head orientation — Blender bones point along local **Y**, not Z | Don't use bone matrix; keep head upright + manual center-align |
| Texture "SAVED" but no file on disk | `img.pack()` makes image internal; `save()` writes nothing external | Use `save_np()` (fresh image + foreach_set), never pack |
| `inputs["Base Color"] = tuple` TypeError | Assigning to a socket collection item | Use `inputs["Base Color"].default_value = tuple` |
| `shading.matcap` AttributeError (3.0) | matcap path not on scene display | Use `light="FLAT"` for matte instead |
| `use_mesh_modifiers` unrecognized on export | Not a valid kwarg in 3.0 collada_export | Remove it (no modifiers needed) |
| broadsword/spear .dae import 0 objects | Blender collada importer rejects some 0 A.D. prop files | Build procedural stand-ins for preview; actor XML still points at real assets |
| numpy `d.normalize()` error | numpy arrays have no `.normalize()` | `d = d / np.linalg.norm(d)` |
| mottle broadcast shape error | 2D noise added to 3D RGB | add `[..., None]` channel axis |
| Can't see renders | This model has no image input | Verify via pixel sampling (hue in expected columns); user reviews PNGs |

---

## 9. Verification without eyes

After rendering, load the PNG in Blender and sample:
```
green = (g > r*1.08) & (g > b*1.08) & (g > 0.05) & (g < 0.5)
# column buckets should show a green group per unit at its x position
```
A unit's column with ~0 green = head missing/misplaced. This caught the
double-offset and closeup-framing bugs.

---

## 10. Extending to other factions / buildings

- Faction identity = skin constants + clothing `cloth_h/cloth_vmul` + head surgery
  tweaks. Copy the orc recipe, change constants.
- Buildings: same principle — reuse base structural meshes from
  `art/meshes/structural/`, recolor textures procedurally, author actor XML.
  Buildings are single meshes (no biped attachpoints), so simpler: import base
  building .dae, recolor, add silhouette detail (spikes/buttresses) via mesh ops,
  export, write actor XML referencing the building animation/variant.
- Keep every new unit's preview in `previews/` and its build function in
  `tools/art_build/` so the pipeline stays reproducible.
