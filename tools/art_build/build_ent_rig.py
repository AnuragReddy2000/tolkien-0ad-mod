"""
Rig the Sketchfab Treeman (Ent) to 0 A.D.'s BIPED skeleton (run inside Blender 3.0).

Why Biped and not elephant:
  - Ent is humanoid (2 arms / 2 legs / head). Elephant skeleton is
    quadruped + trunk + 60 bones - wrong hierarchy, all elephant anims fail.
  - Biped (art/skeletons/biped.xml) already ships idle/walk/run/melee/death
    in art/variants/biped/. Same bone names = zero custom anim work:
    base_swordsman_2hand_relax + slaughter + death_infantry just work.
  - No new skeleton.xml needed. Mesh .dae carries a Biped armature and the
    engine maps it via the stock biped.xml.

Source (NOT bundled - download manually, CC-BY 4.0 by DJMaesen (@bumstrum)):
  https://sketchfab.com/3d-models/treeman-e3a094316a8c4820a94d271afffe497c

USAGE:
  1. Download model from Sketchfab (GLB 1k) to e.g. %USERPROFILE%\\Downloads\\treeman.glb
  2. Reference body must exist (already in repo temp):
       %TEMP%\\0ad_ref\\meshes_skeletal_new_m_tunic_short.dae
     (contains the stock Biped armature + m_tunic_short mesh)
  3. "C:\\Program Files\\Blender Foundation\\Blender 3.0\\blender.exe" ^
       --background --python tools\\art_build\\build_ent_rig.py -- ^
       %USERPROFILE%\\Downloads\\treeman.glb
     Optional: append TARGET_TRIS (default 5500) and ENT_SCALE (default 2.0):
       ... -- %USERPROFILE%\\Downloads\\treeman.glb 5500 2.0
  4. Output: tolkien\\art\\meshes\\skeletal\\tolkien\\ent.dae (RIGGED mesh +
     Biped armature), ent_body.png, ent_CREDITS.txt
  5. Actor tolkien/art/actors/units/doriath/ent.xml + template
     tolkien/simulation/templates/units/doriath/siege_ent.xml are wired
     for biped (stone-hurl uses the melee swing v1; dedicated throw later).

What the script does:
  - imports reference -> keeps Biped armature, deletes ref mesh
  - imports ent -> join, cleanup, decimate to ~5500 tris, single mat/UV
  - scales ent to ref_height * ENT_SCALE (~7.7 game units;
    game units: human body ~= 3.85, see docs/art-unit-template.md section 3)
  - scales armature to match, widens arm/leg bones for ent bulk (edit-mode
    heuristic, tweak WIDEN_* below for your mesh)
  - parents mesh with AUTOMATIC WEIGHTS (heat), exports selected mesh+armature
    as Collada .dae readable by Pyrogenesis/collada2pmd

Manual touch-up (expected for v1 -> v2):
  - open ent.dae in Blender, Weight Paint mode, fix armpit/groin bleed
  - if branch-fists clip on walk, widen shoulder_L/R + arm_L/R edit bones further
  - dedicated stone-throw anim (retarget attack_ranged dialogue) for Hurl Stones

Credit (REQUIRED by CC-BY): derivative of "Treeman" by
DJMaesen (@bumstrum), CC-BY 4.0.
"""
import bpy
import os
import sys

MOD = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tolkien"))
REF_DIR = os.environ.get(
    "ZEROAD_REFERENCE_ART",
    os.path.join(os.path.expanduser("~"), "0ad_ref"))
REF_DEFAULT = os.path.join(REF_DIR, "meshes_skeletal_new_m_tunic_short.dae")

DEFAULT_TARGET_TRIS = 5500
ENT_SCALE = 2.0    # ent height = human ref height * this (~7.7 game units)
WIDEN_ARMS = 1.45    # edit-bone X multiplier for shoulder/arm/forearm/hand
WIDEN_LEGS = 1.12    # edit-bone X multiplier for thigh/leg/foot (1.25 pinched the waist)

# Only these bones may deform the mesh (stock Biped deform set).
# Everything else (prop-*/prop_* attachpoints, IK targets, pole targets,
# sheath/quiver/ammo/projectile markers) must NOT get weights: heat diffusion
# across 102 bones assigns verts to far-away marker bones and the idle
# animation then stretches them into spikes.
DEFORM_BONES = frozenset({
    "hip", "spine", "spine1", "chest", "neck", "head",
    "shoulder_L", "shoulder_R",
    "arm_L", "arm_R", "forearm_L", "forearm_R",
    "hand_L", "hand_R", "finger_L", "finger_R",
    "fingertip_L", "fingertip_R",
    "thigh_L", "thigh_R", "leg_L", "leg_R", "foot_L", "foot_R",
    # NOTE: cape1-3 deliberately excluded - no cape mesh on the ENT;
    # leaving them deformable steals upper-back verts and creases the torso.
})

ARM_BONES = ("shoulder_L", "shoulder_R", "arm_L", "arm_R",
             "forearm_L", "forearm_R", "hand_L", "hand_R",
             "finger_L", "finger_R", "fingertip_L", "fingertip_R")
LEG_BONES = ("thigh_L", "thigh_R", "leg_L", "leg_R", "foot_L", "foot_R")


def restrict_deform_bones(arm):
    """Disable deform on marker/attachpoint bones so automatic weights only
    use the stock Biped deform set."""
    kept, dropped = 0, 0
    for b in arm.data.bones:
        if b.name in DEFORM_BONES:
            b.use_deform = True
            kept += 1
        else:
            b.use_deform = False
            dropped += 1
    log(f"deform bones: {kept} kept, {dropped} markers disabled")


def log(*a):
    print("[ENT-rig]", *a)


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_ref_armature(ref_path):
    if not os.path.isfile(ref_path):
        raise SystemExit(f"reference body not found: {ref_path}\n"
                         "See docs/art-unit-template.md section 0 - download base assets to %TEMP%\\0ad_ref")
    log("importing reference", ref_path)
    before = set(bpy.data.objects)
    bpy.ops.wm.collada_import(filepath=ref_path)
    new_objs = [o for o in bpy.data.objects if o not in before]
    arm = next((o for o in new_objs if o.type == "ARMATURE"), None)
    meshes = [o for o in new_objs if o.type == "MESH"]
    if arm is None:
        raise SystemExit("no armature in reference .dae - wrong file?")
    # reference mesh height in GAME UNITS (body ~= 3.85, never meters)
    ref_h = max((m.dimensions.z for m in meshes), default=3.85)
    log("armature:", arm.name, "ref height:", round(ref_h, 2))
    # drop the inch->meter import artifact scale like build_orcs does NOT -
    # for the ARMATURE we want scale 1 (body imports at scale 1 already)
    for m in meshes:
        bpy.data.objects.remove(m, do_unlink=True)
    return arm, float(ref_h)


def import_ENT(path):
    ext = os.path.splitext(path)[1].lower()
    log("importing ENT", path)
    before = set(bpy.data.objects)
    if ext in (".gltf", ".glb"):
        bpy.ops.import_scene.gltf(filepath=path, merge_vertices=True)
    elif ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=path)
    elif ext == ".obj":
        bpy.ops.import_scene.obj(filepath=path)
    elif ext == ".dae":
        bpy.ops.wm.collada_import(filepath=path)
    else:
        raise SystemExit(f"unsupported extension {ext} (use .gltf/.glb/.fbx/.obj/.dae)")
    objs = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    if not objs:
        raise SystemExit("no meshes in ENT download - check the file")
    # BAKE ASSEMBLY TRANSFORMS FIRST: Sketchfab scenes position/rotate parts
    # via object + parent (EMPTY) node transforms. join() ignores those and
    # merges raw local coords -> scrambled sprawl. So: keep-transform unparent,
    # then apply location/rotation/scale into the mesh data, THEN join.
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    for o in objs:
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.context.view_layer.update()
    xs = [v.co.x for o in objs for v in o.data.vertices]
    ys = [v.co.y for o in objs for v in o.data.vertices]
    zs = [v.co.z for o in objs for v in o.data.vertices]
    log(f"assembled bounds X[{min(xs):.2f},{max(xs):.2f}] "
        f"Y[{min(ys):.2f},{max(ys):.2f}] Z[{min(zs):.2f},{max(zs):.2f}]")
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ENT = bpy.context.view_layer.objects.active
    ENT.name = "ENT"
    return ENT


def cleanup_decimate(obj, target_tris):
    me = obj.data
    tris = sum(max(len(p.vertices) - 2, 1) for p in me.polygons)
    log(f"source ~{tris} tris, {len(me.vertices)} verts")
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=0.0001)
    bpy.ops.mesh.delete_loose()
    bpy.ops.object.mode_set(mode="OBJECT")
    me = obj.data
    tris = sum(max(len(p.vertices) - 2, 1) for p in me.polygons)
    if tris > target_tris:
        ratio = max(target_tris / max(tris, 1), 0.05)
        log(f"decimate {ratio:.3f} -> {target_tris}")
        mod = obj.modifiers.new("Decimate", "DECIMATE")
        mod.decimate_type = "COLLAPSE"
        mod.ratio = ratio
        mod.use_collapse_triangulate = True
        mod.use_symmetry = True
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    # triangulate + normals + single UV + single material
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.quads_convert_to_tris(quad_method="BEAUTY", ngon_method="BEAUTY")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    if not obj.data.uv_layers:
        bpy.ops.uv.cube_project(cube_size=1.0)
    bpy.ops.object.mode_set(mode="OBJECT")
    while len(obj.data.uv_layers) > 1:
        obj.data.uv_layers.remove(obj.data.uv_layers[1])
    obj.data.materials.clear()
    mat = bpy.data.materials.get("ent_body") or bpy.data.materials.new("ent_body")
    mat.use_nodes = True
    obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = True
        p.material_index = 0


def place_and_scale(obj, arm, ref_h, scale):
    # normalize ENT rotation/scale, then size to ref_h * scale
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    h = max(obj.dimensions.z, 0.001)
    f = (ref_h * scale) / h
    log(f"ENT height {h:.2f} -> x{f:.3f} = {ref_h * scale:.2f} game units")
    obj.scale = (f, f, f)
    bpy.context.view_layer.update()
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    # center XY, feet on Z=0
    bpy.context.view_layer.update()
    xs = [v.co.x for v in obj.data.vertices]
    ys = [v.co.y for v in obj.data.vertices]
    obj.location.x -= (max(xs) + min(xs)) / 2
    obj.location.y -= (max(ys) + min(ys)) / 2
    bpy.context.view_layer.update()
    min_z = min(v.co.z for v in obj.data.vertices)
    obj.location.z -= min_z
    bpy.context.view_layer.update()
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    # scale armature to match (armature was built for ref_h)
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    arm.scale = (scale, scale, scale)
    bpy.context.view_layer.update()
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    log("armature scaled x", scale)


def widen_bones(arm):
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    n = 0
    for b in arm.data.edit_bones:
        if b.name in ARM_BONES:
            b.head.x *= WIDEN_ARMS
            b.tail.x *= WIDEN_ARMS
            n += 1
        elif b.name in LEG_BONES:
            b.head.x *= WIDEN_LEGS
            b.tail.x *= WIDEN_LEGS
            n += 1
    bpy.ops.object.mode_set(mode="OBJECT")
    log(f"widened {n} arm/leg bones (arms x{WIDEN_ARMS}, legs x{WIDEN_LEGS})")


def skin_and_export(ENT, arm):
    # parent mesh -> armature with automatic weights (heat)
    bpy.ops.object.select_all(action="DESELECT")
    ENT.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    log("skinned with automatic weights")
    log("vertex groups:", len(ENT.vertex_groups))
    bad = sorted(g.name for g in ENT.vertex_groups if g.name not in DEFORM_BONES)
    if bad:
        log("WARNING: weights on non-deform bones:", bad)
        for name in bad:
            ENT.vertex_groups.remove(ENT.vertex_groups[name])
        log("removed non-deform groups")
    # per-vertex sanity: strongest group must be a nearby deform bone;
    # report the distribution so spikes get caught here, not in Atlas
    from collections import Counter
    top = Counter()
    for v in ENT.data.vertices:
        if v.groups:
            g = max(v.groups, key=lambda e: e.weight)
            top[ENT.vertex_groups[g.group].name] += 1
    log("dominant-group histogram:", dict(sorted(top.items())))
    # soften weight boundaries (waist/hip pinch from heat + mirror decimate):
    # smooth all deform groups so chest<->hip<->thigh transitions are gradual
    bpy.ops.object.select_all(action="DESELECT")
    ENT.select_set(True)
    bpy.context.view_layer.objects.active = ENT
    bpy.ops.object.mode_set(mode="WEIGHT_PAINT")
    bpy.ops.object.vertex_group_smooth(group_select_mode="ALL", factor=0.5, repeat=4)
    bpy.ops.object.mode_set(mode="OBJECT")
    log("smoothed deform weights")
    # texture: LARGEST source image -> 512px baseTex (body albedo, not pants)
    out_png = os.path.join(MOD, "art", "textures", "skins", "skeletal", "tolkien", "ent_body.png")
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    cands = [img for img in bpy.data.images
             if img.type == "IMAGE" and min(img.size[:]) >= 8
             and "Render Result" not in img.name and "Viewer Node" not in img.name]
    if cands:
        img = max(cands, key=lambda i: i.size[0] * i.size[1])
        log("texture source:", img.name, list(img.size[:]))
        img.scale(512, 512)
        img.filepath_raw = out_png
        img.file_format = "PNG"
        img.save()
        log("wrote", out_png)
    else:
        log("WARNING: no source texture found")
    # export mesh + armature (same call pattern as build_orcs.py - known good on 3.0)
    out_dae = os.path.join(MOD, "art", "meshes", "skeletal", "tolkien", "ent.dae")
    os.makedirs(os.path.dirname(out_dae), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    ENT.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.wm.collada_export(filepath=out_dae, selected=True,
                               include_animations=False)
    log("EXPORTED", out_dae)
    with open(os.path.join(os.path.dirname(out_dae), "ent_CREDITS.txt"), "w", encoding="utf-8") as f:
        f.write("Derivative of 'Treeman' by "
                "DJMaesen (@bumstrum), CC-BY 4.0.\n"
                "Source: https://sketchfab.com/3d-models/treeman-e3a094316a8c4820a94d271afffe497c\n"
                "Changes: decimated ~8.6k -> ~5.5k tris, rigged to stock 0 A.D. "
                "Biped (art/skeletons/biped.xml), rescaled ~2.0x human, 512px baseTex.\n"
                "Custom tall idle + walk + run (biped/ent_*.dae); melee/death/promotion stock.\n")
    # sanity: verts under engine hard limit, armature present
    me = ENT.data
    log(f"DONE verts={len(me.vertices)} (limit 32768), bones={len(arm.data.bones)}")
    missing = [b for b in ("hip", "chest", "head", "hand_R", "foot_L") if b not in arm.data.bones]
    if missing:
        log("WARNING missing biped bones:", missing)


IDLE_FRAMES = (1, 16, 32)

# Torso dampening for retargets: quaternion angle scale per bone. Limbs copy
# verbatim (1.0); spine/chest/head shrink toward rest so the human hunch
# doesn't crumple the bulky ent. Hip location deltas scale up x2.0 below.
DAMP_BASE = {"spine": 0.4, "spine1": 0.4, "chest": 0.45,
             "neck": 0.6, "head": 0.5}
# Melee adds: fists locked to the natural rest curl (the stock grip-release
# splays giant ENT fingers into a wave), wrists calmed (stock sword-roll
# corkscrews the long forearms). Arms keep full swing.
DAMP_MELEE = {**DAMP_BASE,
              "hand_L": 0.45, "hand_R": 0.45,
              "finger_L": 0.0, "finger_R": 0.0,
              "fingertip_L": 0.0, "fingertip_R": 0.0}
LOC_SCALE = 2.0

STOCK_DIR = os.path.join(REF_DIR, "stock_anim")

# (stock file, ENT anim name, damp profile). Times copy verbatim -> stock
# variant speeds stay valid (verified: engine speed factor = value/100).
RETARGET_JOBS = [
    ("walk_relax.dae", "walk", DAMP_BASE),
    ("run_relax_2h.dae", "run", DAMP_BASE),
    ("attack_melee_2h_01.dae", "melee1", DAMP_MELEE),
    ("attack_melee_2h_02.dae", "melee2", DAMP_MELEE),
    ("attack_ranged_javelin.dae", "throw", DAMP_MELEE),
    ("capturing_a.dae", "capture", DAMP_BASE),
]


def _key_q(pb, axis, angle, frame):
    """Key a small rest-relative rotation as quaternion (exact for any angle;
    bone local axes vary, but amplitudes here are ~2 deg)."""
    import math as _m
    pb.rotation_mode = "QUATERNION"
    q = [1.0, 0.0, 0.0, 0.0]
    q[axis + 1] = _m.sin(angle / 2.0)
    q[0] = _m.cos(angle / 2.0)
    pb.rotation_quaternion = q
    pb.keyframe_insert(data_path="rotation_quaternion", frame=frame)


def author_idle(ENT, arm):
    """Tall breathing idle in the source A-pose (NOT the stock human crouch).

    Quaternion keys (shared mode with retargets). Amplitudes tiny (~2 deg);
    the win is the BASE pose itself - tall rest instead of relax-crouch.
    """
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, 32
    if hasattr(sc.render, "fps"):
        sc.render.fps = 30
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="POSE")
    pose = arm.pose
    for b in pose.bones:
        if b.name in DEFORM_BONES:
            b.rotation_mode = "QUATERNION"
    if arm.animation_data is None:
        arm.animation_data_create()
    act = bpy.data.actions.new("ent_idle")
    arm.animation_data.action = act
    hip_base_z = pose.bones["hip"].location[2] if "hip" in pose.bones else 0.0
    if "chest" in pose.bones:
        for f, v in zip(IDLE_FRAMES, [0.0, 0.035, 0.0]):
            _key_q(pose.bones["chest"], 0, v, f)
    if "shoulder_L" in pose.bones:
        for f, v in zip(IDLE_FRAMES, [0.0, 0.05, 0.0]):
            _key_q(pose.bones["shoulder_L"], 1, v, f)
    if "shoulder_R" in pose.bones:
        for f, v in zip(IDLE_FRAMES, [0.0, -0.05, 0.0]):
            _key_q(pose.bones["shoulder_R"], 1, v, f)
    if "head" in pose.bones:
        for f, v in zip(IDLE_FRAMES, [0.0, -0.025, 0.0]):
            _key_q(pose.bones["head"], 0, v, f)
    if "hip" in pose.bones:
        for f, v in zip(IDLE_FRAMES, [hip_base_z, hip_base_z + 0.05, hip_base_z]):
            pose.bones["hip"].location[2] = v
            pose.bones["hip"].keyframe_insert(data_path="location", index=2, frame=f)
    bpy.ops.object.mode_set(mode="OBJECT")
    sc.frame_set(1)
    log("authored tall idle (32f loop, quats)")


def export_idle(ENT, arm):
    out_anim = os.path.join(MOD, "art", "animation", "biped", "ent_idle.dae")
    os.makedirs(os.path.dirname(out_anim), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    ENT.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.wm.collada_export(filepath=out_anim, selected=True,
                               include_animations=True)
    log("EXPORTED idle", out_anim)


def damp_quat(q, k):
    """Scale a quaternion's rotation angle by k (exact slerp toward rest).
    k=1 copies verbatim (zero float drift)."""
    import math as _m
    w, x, y, z = q
    w = max(-1.0, min(1.0, w))
    if k >= 0.999:
        return (w, x, y, z)
    if k <= 0.0:
        return (1.0, 0.0, 0.0, 0.0)
    ang = 2.0 * _m.acos(w)
    if ang < 1e-6:
        return (1.0, 0.0, 0.0, 0.0)
    na = ang * k
    s = _m.sin(na / 2.0) / _m.sin(ang / 2.0)
    return (_m.cos(na / 2.0), x * s, y * s, z * s)


def retarget_stock(ENT, arm, stock_name, out_name, damp):
    """Copy a stock Biped animation onto the ENT with torso dampening.

    Same bone names + same hierarchy, so rotation curves transfer 1:1 on
    limbs; spine/chest/head angles shrink (DAMP_TORSO) so the human hunch
    doesn't crumple the bulky ENT; hip location deltas scale up (LOC_SCALE)
    to ENT size. Key TIMES copy verbatim -> stock variant speeds stay valid.
    Only deform bones transfer (markers/props stay bound to rest).
    """
    import re
    src = os.path.join(STOCK_DIR, stock_name)
    if not os.path.isfile(src):
        raise SystemExit(f"stock anim missing: {src}\n"
                         "Download from https://github.com/0ad/0ad "
                         "binaries/data/mods/public/art/animation/biped/...")
    objs_before = set(bpy.data.objects)
    acts_before = set(bpy.data.actions)
    bpy.ops.wm.collada_import(filepath=src)
    new_objs = [o for o in bpy.data.objects if o not in objs_before]
    sarm = next((o for o in new_objs if o.type == "ARMATURE"), None)
    new_acts = [a for a in bpy.data.actions if a not in acts_before]
    if sarm is None or not new_acts:
        raise SystemExit(f"no armature/action in {stock_name}")
    sact = new_acts[0]
    log(f"retarget {stock_name}: {len(sact.fcurves)} curves, "
        f"frames {sact.frame_range[0]:.0f}..{sact.frame_range[1]:.0f}")
    for b in arm.pose.bones:
        if b.name in DEFORM_BONES:
            b.rotation_mode = "QUATERNION"
    rot, loc = {}, {}
    for fc in sact.fcurves:
        m = re.match(r'pose\.bones\["([^"]+)"\]\.(rotation_quaternion|location)$',
                     fc.data_path)
        if not m:
            continue
        bone, prop = m.group(1), m.group(2)
        if bone not in DEFORM_BONES or bone not in arm.pose.bones:
            continue
        keys = [(kp.co[0], kp.co[1]) for kp in fc.keyframe_points]
        (rot if prop == "rotation_quaternion" else loc)[(bone, fc.array_index)] = keys
    new_act = bpy.data.actions.new("ent_" + out_name)
    bones = sorted(set(b for (b, _c) in list(rot.keys()) + list(loc.keys())))
    for bone in bones:
        k = damp.get(bone, 1.0)
        if all((bone, c) in rot for c in range(4)):
            ts = [t for t, _v in rot[(bone, 0)]]
            for i, t in enumerate(ts):
                q = tuple(rot[(bone, c)][i][1] for c in range(4))
                for c, v in enumerate(damp_quat(q, k)):
                    fc = new_act.fcurves.find(
                        f'pose.bones["{bone}"].rotation_quaternion', index=c)
                    if fc is None:
                        fc = new_act.fcurves.new(
                            f'pose.bones["{bone}"].rotation_quaternion', index=c)
                    fc.keyframe_points.insert(t, v, options={"FAST"})
        for c in range(3):
            if (bone, c) in loc:
                fc = new_act.fcurves.new(
                    f'pose.bones["{bone}"].location', index=c)
                for t, v in loc[(bone, c)]:
                    fc.keyframe_points.insert(t, v * LOC_SCALE, options={"FAST"})
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = new_act
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = int(sact.frame_range[0]), int(sact.frame_range[1])
    out = os.path.join(MOD, "art", "animation", "biped", f"ent_{out_name}.dae")
    bpy.ops.object.select_all(action="DESELECT")
    ENT.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.wm.collada_export(filepath=out, selected=True,
                               include_animations=True,
                               include_all_actions=False)
    log(f"EXPORTED retarget {out_name} ({len(new_act.fcurves)} curves)")
    for o in new_objs:
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.actions.remove(sact)
    sc.frame_set(sc.frame_start)


def write_variant(walk_file, run_file):
    # Speed semantics (engine: factor = speed/100; cadence = intrinsic/speed):
    # Blender exports seconds @30fps, so intrinsic durs are idle 1.07s,
    # walk/run 1.10s, attack/capture 0.83s. Stock speed values assumed ~1s
    # stock files and would freeze ours (run @8 = 13.7s/cycle!). Retuned:
    # idle ~3s loop, walk ~1.2s shamble, run ~0.65s charge.
    var_dir = os.path.join(MOD, "art", "variants", "biped")
    os.makedirs(var_dir, exist_ok=True)
    with open(os.path.join(var_dir, "ent_relax.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<variant name="Base" frequency="1">\n'
                '  <animations>\n'
                '    <animation file="biped/ent_idle.dae" name="idle" id="idle1" speed="35"/>\n'
                '    <animation file="biped/ent_idle.dae" name="idle" id="idle2" speed="32"/>\n'
                f'    <animation file="{walk_file}" name="Walk" id="walk1" speed="30"/>\n'
                f'    <animation file="{walk_file}" name="Walk" id="walk2" speed="29"/>\n'
                f'    <animation file="{walk_file}" name="Walk" id="walk3" speed="28"/>\n'
                f'    <animation file="{run_file}" name="Run" id="run1" speed="8"/>\n'
                f'    <animation file="{run_file}" name="Run" id="run2" speed="9"/>\n'
                f'    <animation file="{run_file}" name="Run" id="run3" speed="10"/>\n'
                '    <animation event="0.5" file="biped/ent_melee1.dae" name="attack_melee" id="attack1" speed="100"/>\n'
                '    <animation event="0.5" file="biped/ent_melee2.dae" name="attack_melee" id="attack2" speed="100"/>\n'
                '    <animation event="0.5" file="biped/ent_melee1.dae" name="attack_melee" id="attack3" speed="100"/>\n'
                '    <animation event="0.6" file="biped/ent_throw.dae" name="attack_ranged" id="attackr1" speed="100"/>\n'
                '    <animation event="0.6" file="biped/ent_throw.dae" name="attack_ranged" id="attackr2" speed="100"/>\n'
                '    <animation file="biped/infantry/promotion.dae" name="promotion" speed="80"/>\n'
                '  </animations>\n'
                '</variant>\n')
    log(f"wrote variant biped/ent_relax.xml (walk={walk_file} run={run_file})")
    with open(os.path.join(var_dir, "ent_capture.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<variant name="attack_capture">\n'
                '  <animations>\n'
                '    <animation file="biped/ent_capture.dae" name="attack_capture" speed="100"/>\n'
                '  </animations>\n'
                '</variant>\n')
    log("wrote variant biped/ent_capture.xml")


def main():
    argv = sys.argv
    args = argv[argv.index("--") + 1:] if "--" in argv else []
    if not args:
        print("Usage: blender --background --python build_ENT_rig.py -- <ENT.gltf|glb|fbx|obj> [target_tris] [scale] [ref_dae]")
        raise SystemExit(2)
    src = args[0]
    target = int(args[1]) if len(args) > 1 else DEFAULT_TARGET_TRIS
    scale = float(args[2]) if len(args) > 2 else ENT_SCALE
    ref = args[3] if len(args) > 3 else REF_DEFAULT
    if not os.path.isfile(src):
        raise SystemExit(f"input not found: {src}")
    clear()
    arm, ref_h = import_ref_armature(ref)
    ENT = import_ENT(src)
    cleanup_decimate(ENT, target)
    place_and_scale(ENT, arm, ref_h, scale)
    restrict_deform_bones(arm)
    widen_bones(arm)
    skin_and_export(ENT, arm)
    author_idle(ENT, arm)
    export_idle(ENT, arm)
    for stock_name, out_name, damp in RETARGET_JOBS:
        retarget_stock(ENT, arm, stock_name, out_name, damp)
    write_variant("biped/ent_walk.dae", "biped/ent_run.dae")
    log("NEXT: test in 0 A.D. (mod selection -> Tolkien), check interestinglog.html for errors.")


if __name__ == "__main__":
    main()
