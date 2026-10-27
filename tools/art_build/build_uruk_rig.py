"""
Rig the Sketchfab Uruk-Hai to 0 A.D.'s BIPED skeleton (run inside Blender 3.0).

Cloned from tools/art_build/build_troll_rig.py (DO NOT edit the troll script
for uruk work) - same pipeline, uruk parameters. See
docs/sketchfab-to-0ad.md for the full pipeline rationale.

Why Biped: uruk is humanoid (2 arms / 2 legs / head). Biped
(art/skeletons/biped.xml) already ships idle/walk/run/melee/death in
art/variants/biped/. Same bone names = stock animations retarget by name,
no new skeleton.xml needed.

Source (NOT bundled - download manually, CC-BY 4.0 by Ulrik Langvandsbraaten):
  https://sketchfab.com/3d-models/uruk-hai-lotr-c86d316b3f314d11bf3234771b2cc212

USAGE:
  1. Download model from Sketchfab (GLB) to e.g. C:\\Users\\<you>\\Downloads\\uruk_hai_-_lotr.glb
  2. Reference body must exist:
       %TEMP%\\0ad_ref\\meshes_skeletal_new_m_tunic_short.dae
     (contains the stock Biped armature + m_tunic_short mesh)
  3. Stock anims must exist in %TEMP%\\0ad_ref\\stock_anim\\ (walk_relax.dae,
     run_relax_2h.dae, attack_melee_2h_01/02.dae, capturing_a.dae)
  4. "C:\\Program Files\\Blender Foundation\\Blender 3.0\\blender.exe" ^
       --background --python tools\\art_build\\build_uruk_rig.py -- ^
       C:\\Users\\<you>\\Downloads\\uruk_hai_-_lotr.glb
     Optional: append TARGET_TRIS (default 5000) and URUK_SCALE (default 1.15):
       ... -- C:\\Users\\<you>\\Downloads\\uruk_hai_-_lotr.glb 5000 1.15
  5. Output: tolkien\\art\\meshes\\skeletal\\tolkien\\uruk.dae (RIGGED mesh +
     Biped armature), uruk_body.png, uruk_CREDITS.txt,
     tolkien\\art\\animation\\biped\\uruk_*.dae,
     tolkien\\art\\variants\\biped\\uruk_relax.xml + uruk_capture.xml

What the script does:
  - imports reference -> keeps Biped armature, deletes ref mesh
  - imports uruk -> EXCLUDES sword/shield prop mesh(es) + display base,
    joins body, splits the two-figure diorama into loose islands and keeps
    the LEFT (helmeted sword+shield) figure (FIGURE_DEFAULT, CLI-overridable),
    centers/scales FIRST (symmetry decimate needs a centered
    mesh - decimating raw off-center coords kills heat weighting), then
    cleanup + decimate to ~5000 tris, single mat/UV
  - scales uruk to ref_height * URUK_SCALE (~4.4 game units; uruk taller
    than a human but not troll-class)
  - scales armature to match, widens arm/leg bones for uruk bulk (edit-mode
    heuristic, tweak WIDEN_* below for your mesh)
  - restricts to the 24 stock deform bones, parents mesh with AUTOMATIC
    WEIGHTS (heat), smooths deform groups x4, exports selected mesh+armature
    as Collada .dae readable by Pyrogenesis/collada2pmd
  - authors a tall custom idle, retargets 5 stock anims with torso
    dampening, writes relax + capture variants

Prop handling (sword/shield are SEPARATE props later - NOT joined):
  - any mesh whose materials are ALL matched by PROP_MAT_SUBSTR ("weapon")
    is left out of the body join (this download: Object_4 'Weapons',
    ~5.3k verts / ~9.4k polys: sword + shield in hand pose)
  - flat display-base discs (Z-extent < 30% of min XY-extent) are also left
    out (this download: Object_7 'yOLOoRC_*', ~1k verts: ground disc)
  - excluded meshes are logged with vert/poly counts for the props pass

Credit (REQUIRED by CC-BY): derivative of "Uruk Hai - LOTR" by
Ulrik Langvandsbraaten (@best3deu), CC-BY 4.0.
"""
import bpy
import os
import sys

MOD = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tolkien"))
REF_DIR = os.environ.get(
    "ZEROAD_REFERENCE_ART",
    os.path.join(os.path.expanduser("~"), "0ad_ref"))
REF_DEFAULT = os.path.join(REF_DIR, "meshes_skeletal_new_m_tunic_short.dae")

DEFAULT_TARGET_TRIS = 5000
URUK_SCALE = 1.15    # uruk height = human ref height * this (~4.4 game units)
WIDEN_ARMS = 1.25    # edit-bone X multiplier for shoulder/arm/forearm/hand
WIDEN_LEGS = 1.10    # edit-bone X multiplier for thigh/leg/foot

# Meshes whose materials ALL match one of these substrings (case-insensitive)
# are weapon props -> excluded from the body join, rigged separately later.
PROP_MAT_SUBSTR = ("weapon",)
# Flat display-base discs (ground plinths the author posed the model on)
# are detected geometrically: Z-extent below this fraction of min(XY-extent).
FLAT_BASE_RATIO = 0.30

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
    # NOTE: cape1-3 deliberately excluded - no cape mesh on the uruk;
    # leaving them deformable steals upper-back verts and creases the torso.
})

ARM_BONES = ("shoulder_L", "shoulder_R", "arm_L", "arm_R",
             "forearm_L", "forearm_R", "hand_L", "hand_R",
             "finger_L", "finger_R", "fingertip_L", "fingertip_R")
LEG_BONES = ("thigh_L", "thigh_R", "leg_L", "leg_R", "foot_L", "foot_R")


# The download is a TWO-FIGURE diorama (plus weapons + display base), not one
# character. We adopt exactly one figure:
#   "left"  = helmeted uruk with sword + shield (DEFAULT - matches the
#             sword/shield prop description; raw X[-1.14,0.26], top Z~1.96)
#   "right" = bald dual-wielding uruk (kept available for a second unit pass;
#             raw X[-0.04,1.62], top Z~1.78)
# Island layout (measured, baked raw coords): left structural islands sit at
# cx -0.96..-0.33 in depth slab Y>0; right ones at cx 0.61..1.36, Y<0.1; two
# reaching arms cross the middle (.023: cx 0.06/cy +0.45 = left's,
# .024: cx 0.21/cy -0.56 = right's). Rule below assigns by (cx, cy).
FIGURE_DEFAULT = "left"


MICRO_ISLAND_MIN_VERTS = 100  # loose islands below this are rivets/studs/deco

# Weld threshold (game units, applied AFTER place_and_scale): the 40 body
# shells interpenetrate (median cross-island nearest distance 0.029) - a
# remove_doubles fuses touching shells so heat + smooth blend ACROSS former
# joint boundaries instead of hinging rigid islands (measured: heat 100%
# after weld; per-loop UVs keep the texture intact).
# Threshold is load-bearing both ways (measured): 0.02 fuses 40 -> 1 but
# ALSO collapses thin armor plates front-to-back (pairs sit <0.02 apart) -
# torn gashes + checkerboard UVs. Boundary-only weld fuses almost nothing
# (169 verts - joint rims don't coincide). 0.01 fuses the core 36 shells
# into one connected mesh (joints bend smoothly) while plate pairs (>0.01
# apart) and 4 small armor tabs survive intact.
WELD_THRESHOLD = 0.01


def _weld_shells(body):
    """Fuse interpenetrating body shells into (near-)one mesh so joints bend
    instead of disassembling. Must run on the SCALED mesh (threshold is in
    game units) and BEFORE decimate."""
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    me = body.data
    pre = len(me.vertices)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=WELD_THRESHOLD)
    bpy.ops.object.mode_set(mode="OBJECT")
    merged = pre - len(me.vertices)
    log(f"weld: merged {merged} verts ({100 * merged / max(pre, 1):.1f}%) "
        f"at threshold {WELD_THRESHOLD}")
    return body


def _drop_micro_islands(body):
    """Delete loose micro-islands (armor rivets/studs/deco bits).

    They carry roughly half the source verts, vanish at game tri budgets
    anyway (their color detail survives in the 512px texture), and their
    disconnected micro-shells make heat weighting bail on the WHOLE mesh
    (measured single-figure: full soup 0/3120 verts weighted, big-only
    2786/2786)."""
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    had = set(o for o in bpy.data.objects if o.type == "MESH")
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.separate(type="LOOSE")
    bpy.ops.object.mode_set(mode="OBJECT")
    parts = [o for o in bpy.data.objects if o.type == "MESH" and o not in had] + [body]
    big = [o for o in parts if len(o.data.vertices) >= MICRO_ISLAND_MIN_VERTS]
    micro = [o for o in parts if o not in big]
    if not big:
        raise SystemExit("micro-island cleanup kept nothing - threshold insane?")
    mv = sum(len(o.data.vertices) for o in micro)
    bv = sum(len(o.data.vertices) for o in big)
    log(f"micro-islands: dropped {len(micro)} (<{MICRO_ISLAND_MIN_VERTS}v, "
        f"{mv} verts of rivets/studs), kept {len(big)} ({bv} verts)")
    for o in micro:
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in big:
        o.select_set(True)
    bpy.context.view_layer.objects.active = big[0]
    bpy.ops.object.join()
    joined = bpy.context.view_layer.objects.active
    joined.name = "uruk"
    return joined


def _figure_side(obj):
    ws = [obj.matrix_world @ v.co for v in obj.data.vertices]
    xs = [c.x for c in ws]
    ys = [c.y for c in ws]
    cx = (max(xs) + min(xs)) / 2
    cy = (max(ys) + min(ys)) / 2
    if cx <= 0.0 or (cy > 0.1 and cx < 0.3):
        return "left"
    return "right"


def _select_figure(body, which):
    """Split the joined body into loose islands and keep one figure's."""
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    had = set(o for o in bpy.data.objects if o.type == "MESH")
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.separate(type="LOOSE")
    bpy.ops.object.mode_set(mode="OBJECT")
    parts = [o for o in bpy.data.objects if o.type == "MESH" and o not in had]
    parts.append(body)
    kept, dropped = [], []
    for o in parts:
        (kept if _figure_side(o) == which else dropped).append(o)
    if not kept:
        raise SystemExit(f"figure selection {which!r} kept nothing - check island layout")
    kv = sum(len(o.data.vertices) for o in kept)
    dv = sum(len(o.data.vertices) for o in dropped)
    log(f"figure {which!r}: kept {len(kept)} islands ({kv} verts), "
        f"dropped other figure {len(dropped)} islands ({dv} verts, "
        "reusable for a second unit pass)")
    bpy.ops.object.select_all(action="DESELECT")
    for o in kept:
        o.select_set(True)
    bpy.context.view_layer.objects.active = kept[0]
    bpy.ops.object.join()
    uruk = bpy.context.view_layer.objects.active
    uruk.name = "uruk"
    for o in dropped:
        bpy.data.objects.remove(o, do_unlink=True)
    return uruk


def _seg_dist(p, a, b):
    d = b - a
    t = max(0.0, min(1.0, (p - a).dot(d) / max(d.length_squared, 1e-9)))
    return (p - (a + d * t)).length


# Finger/fingertip bones must only own verts near the hands. Heat diffusion
# on this lunged source sprayed fingertip ownership onto torso/skirt armor
# chunks (measured: chest-height + hip-height islands 100% fingertip-owned);
# stock walk/run/melee animate fingers verbatim, so those chunks fly on
# EVERY animation. Drop such far influences and renormalize; verts left
# with nothing fall through to the orphan binder (nearest bone).
PRUNE_BONES = ("finger_L", "finger_R", "fingertip_L", "fingertip_R")
PRUNE_DIST = 0.5  # game units from the bone segment; fist+knuckles are inside


def _prune_far_finger_weights(obj, arm):
    from collections import Counter
    segs = {b: (arm.matrix_world @ arm.data.bones[b].head_local,
                arm.matrix_world @ arm.data.bones[b].tail_local)
            for b in PRUNE_BONES if b in arm.data.bones}
    dropped = Counter()
    n_verts = 0
    for v in obj.data.vertices:
        if not v.groups:
            continue
        p = obj.matrix_world @ v.co
        keep = []
        for e in v.groups:
            name = obj.vertex_groups[e.group].name
            if name in segs and _seg_dist(p, *segs[name]) > PRUNE_DIST:
                dropped[name] += 1
            else:
                keep.append((name, e.weight))
        if len(keep) != len(v.groups):
            n_verts += 1
            for g in obj.vertex_groups:
                g.remove([v.index])
            if keep:
                s = sum(w for _n, w in keep)
                for name, w in keep:
                    obj.vertex_groups[name].add([v.index], w / s, "REPLACE")
            # else: fully stripped -> orphan binder assigns nearest bone below
    if n_verts:
        log(f"pruned far finger weights on {n_verts} verts: {dict(sorted(dropped.items()))}")
    return n_verts


# Rigid islands owned 100% by a FAR bone snap to their nearest bone.
# (Measured: a 59-vert head-height plate owned by arm_R at 0.97 distance
# flew with every arm swing; nearest was chest at 0.48.) Generic rule, not
# index hacking: single-bone islands with d_dom > SNAP_FAR and d_near <
# SNAP_NEAR get all verts rebound 1.0 to the nearest bone.
SNAP_FAR = 0.8
SNAP_NEAR = 0.5


def _snap_far_rigid_islands(obj, arm):
    from mathutils import Vector
    segs = {b: (arm.matrix_world @ arm.data.bones[b].head_local,
                arm.matrix_world @ arm.data.bones[b].tail_local)
            for b in DEFORM_BONES if b in arm.data.bones}
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    had = set(o for o in bpy.data.objects if o.type == "MESH")
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.separate(type="LOOSE")
    bpy.ops.object.mode_set(mode="OBJECT")
    parts = [o for o in bpy.data.objects if o.type == "MESH" and o not in had] + [obj]
    n_snapped = 0
    for o in parts:
        ws = [o.matrix_world @ v.co for v in o.data.vertices]
        cx = sum(ws, Vector()) / len(ws)
        votes = {}
        for v in o.data.vertices:
            if v.groups:
                g = max(v.groups, key=lambda e: e.weight)
                name = o.vertex_groups[g.group].name
                votes[name] = votes.get(name, 0) + 1
        if len(votes) != 1:
            continue
        dom = next(iter(votes))
        d_dom = _seg_dist(cx, *segs[dom]) if dom in segs else 999.0
        near, d_near = min(((nb, _seg_dist(cx, *s)) for nb, s in segs.items()),
                           key=lambda t: t[1])
        if d_dom > SNAP_FAR and d_near < SNAP_NEAR and near != dom:
            for v in o.data.vertices:
                for g in o.vertex_groups:
                    g.remove([v.index])
                o.vertex_groups[near].add([v.index], 1.0, "REPLACE")
            n_snapped += 1
            log(f"snapped {len(o.data.vertices)}-vert island {dom} (d={d_dom:.2f}) -> {near} (d={d_near:.2f})")
    bpy.ops.object.select_all(action="DESELECT")
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    joined = bpy.context.view_layer.objects.active
    joined.name = "uruk"
    # join keeps only the active part's modifiers - repair the bind
    if not any(m.type == "ARMATURE" for m in joined.modifiers):
        m = joined.modifiers.new("Armature", "ARMATURE")
        m.object = arm
        log("re-added Armature modifier after island rejoin")
    else:
        for m in joined.modifiers:
            if m.type == "ARMATURE":
                m.object = arm
    if n_snapped:
        log(f"snapped {n_snapped} far-owned rigid islands to nearest bones")
    return joined


def _assign_orphan_weights(obj):
    """Bind weightless verts to nearest weighted neighbour's dominant bone.

    Returns the orphan count (0 = heat covered everything)."""
    from mathutils.kdtree import KDTree
    verts = obj.data.vertices
    weighted = [v for v in verts if len(v.groups) > 0]
    orphans = [v for v in verts if len(v.groups) == 0]
    if not orphans:
        return 0
    if not weighted:
        return 0  # caller fail-fasts on total heat failure
    kd = KDTree(len(weighted))
    for i, v in enumerate(weighted):
        kd.insert(v.co, i)
    kd.balance()
    for v in orphans:
        _co, idx, _dist = kd.find(v.co)
        donor = weighted[idx]
        g = max(donor.groups, key=lambda e: e.weight)
        name = obj.vertex_groups[g.group].name
        obj.vertex_groups[name].add([v.index], 1.0, "REPLACE")
    return len(orphans)


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
    print("[uruk-rig]", *a)


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


def _mesh_tris(obj):
    return sum(max(len(p.vertices) - 2, 1) for p in obj.data.polygons)


def _is_weapon_prop(obj):
    mats = [m.name.lower() for m in obj.data.materials if m]
    return bool(mats) and all(
        any(s in name for s in PROP_MAT_SUBSTR) for name in mats)


def _is_flat_base(obj):
    ws = [obj.matrix_world @ v.co for v in obj.data.vertices]
    ex = max(c.x for c in ws) - min(c.x for c in ws)
    ey = max(c.y for c in ws) - min(c.y for c in ws)
    ez = max(c.z for c in ws) - min(c.z for c in ws)
    return ez < FLAT_BASE_RATIO * min(ex, ey)


def import_uruk(path, which=FIGURE_DEFAULT):
    ext = os.path.splitext(path)[1].lower()
    log("importing uruk", path)
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
        raise SystemExit("no meshes in uruk download - check the file")
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
    # PARTITION: sword/shield (+ display base) stay OUT of the body join -
    # they become separate prop meshes later. Everything else joins.
    body, props = [], []
    for o in objs:
        if _is_weapon_prop(o):
            props.append((o, "weapon prop (separate props later)"))
        elif _is_flat_base(o):
            props.append((o, "flat display base (not part of unit)"))
        else:
            body.append(o)
    if props:
        for o, why in props:
            log(f"EXCLUDE {o.name} [{_mesh_tris(o)} tris, "
                f"{len(o.data.vertices)} verts] - {why}")
    else:
        log("WARNING: no prop meshes excluded - expected a Weapons mesh; "
            "check material names if sword/shield got merged into the body")
    if not body:
        raise SystemExit("all meshes excluded as props - nothing left for the body")
    log(f"body parts: {[o.name for o in body]}")
    bpy.ops.object.select_all(action="DESELECT")
    for o in body:
        o.select_set(True)
    bpy.context.view_layer.objects.active = body[0]
    bpy.ops.object.join()
    uruk = bpy.context.view_layer.objects.active
    uruk.name = "uruk_tmp"
    # drop excluded prop meshes from the scene (props pass re-imports the GLB;
    # NOTE: the Weapons mesh spans BOTH figures - the props pass must split it
    # the same way _select_figure splits the body)
    for o, _why in props:
        bpy.data.objects.remove(o, do_unlink=True)
    return _drop_micro_islands(_select_figure(uruk, which))


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
    mat = bpy.data.materials.get("uruk_body") or bpy.data.materials.new("uruk_body")
    mat.use_nodes = True
    obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = True
        p.material_index = 0


def place_and_scale(obj, arm, ref_h, scale):
    # normalize uruk rotation/scale, then size to ref_h * scale
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    h = max(obj.dimensions.z, 0.001)
    f = (ref_h * scale) / h
    log(f"uruk height {h:.2f} -> x{f:.3f} = {ref_h * scale:.2f} game units")
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


def skin_and_export(uruk, arm):
    # parent mesh -> armature with automatic weights (heat)
    bpy.ops.object.select_all(action="DESELECT")
    uruk.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    log("skinned with automatic weights")
    log("vertex groups:", len(uruk.vertex_groups))
    bad = sorted(g.name for g in uruk.vertex_groups if g.name not in DEFORM_BONES)
    if bad:
        log("WARNING: weights on non-deform bones:", bad)
        for name in bad:
            uruk.vertex_groups.remove(uruk.vertex_groups[name])
        log("removed non-deform groups")
    # heat leaves isolated verts (inner shells, dense open seams) with NO
    # weights - they would export jointless and freeze at bind pose while the
    # body moves. Bind each orphan to its nearest weighted neighbour's
    # dominant bone (weight 1.0); the x4 smooth below blends the seams.
    # (Runs after finger pruning so fully-stripped strays land here too.)
    _prune_far_finger_weights(uruk, arm)
    uruk = _snap_far_rigid_islands(uruk, arm)
    n_orphan = _assign_orphan_weights(uruk)
    if n_orphan:
        log(f"bound {n_orphan} weightless orphans to nearest weighted neighbour")
    n_weighted = sum(1 for v in uruk.data.vertices if len(v.groups) > 0)
    if n_weighted == 0:
        raise SystemExit("heat weighting failed on ALL verts - mesh unsuitable "
                         "(check non-manifold soup / decimate damage), refusing "
                         "to export an unskinned statue")
    # per-vertex sanity: strongest group must be a nearby deform bone;
    # report the distribution so spikes get caught here, not in Atlas
    from collections import Counter
    top = Counter()
    for v in uruk.data.vertices:
        if v.groups:
            g = max(v.groups, key=lambda e: e.weight)
            top[uruk.vertex_groups[g.group].name] += 1
    log("dominant-group histogram:", dict(sorted(top.items())))
    # soften weight boundaries (waist/hip pinch from heat + mirror decimate):
    # smooth all deform groups so chest<->hip<->thigh transitions are gradual
    bpy.ops.object.select_all(action="DESELECT")
    uruk.select_set(True)
    bpy.context.view_layer.objects.active = uruk
    bpy.ops.object.mode_set(mode="WEIGHT_PAINT")
    bpy.ops.object.vertex_group_smooth(group_select_mode="ALL", factor=0.5, repeat=4)
    bpy.ops.object.mode_set(mode="OBJECT")
    log("smoothed deform weights")
    # texture: LARGEST source image -> 512px baseTex (body albedo)
    out_png = os.path.join(MOD, "art", "textures", "skins", "skeletal", "tolkien", "uruk_body.png")
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
    out_dae = os.path.join(MOD, "art", "meshes", "skeletal", "tolkien", "uruk.dae")
    os.makedirs(os.path.dirname(out_dae), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    uruk.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.wm.collada_export(filepath=out_dae, selected=True,
                               include_animations=False)
    log("EXPORTED", out_dae)
    with open(os.path.join(os.path.dirname(out_dae), "uruk_CREDITS.txt"), "w", encoding="utf-8") as f:
        f.write("Derivative of 'Uruk Hai - LOTR' by "
                "Ulrik Langvandsbraaten (@best3deu), CC-BY 4.0.\n"
                "Source: https://sketchfab.com/3d-models/uruk-hai-lotr-c86d316b3f314d11bf3234771b2cc212\n"
                "Changes: kept the LEFT (helmeted sword+shield) figure of the "
                "two-figure diorama - second (bald dual-wielder) figure, "
                "sword/shield prop mesh (Object_4, 9447 tris) + display base "
                "excluded (separate props / second unit pass later). Body "
                "19913 verts/37520 tris -> micro-island (rivet) cleanup -> "
                "decimated ~29.4k -> ~5k tris, rigged to stock 0 A.D. "
                "Biped (art/skeletons/biped.xml), rescaled ~1.15x "
                "human, 512px baseTex.\n"
                "Custom tall idle + walk + run (biped/uruk_*.dae); melee/capture retargeted stock.\n")
    # sanity: verts under engine hard limit, armature present
    me = uruk.data
    log(f"DONE verts={len(me.vertices)} (limit 32768), bones={len(arm.data.bones)}")
    missing = [b for b in ("hip", "chest", "head", "hand_R", "foot_L") if b not in arm.data.bones]
    if missing:
        log("WARNING missing biped bones:", missing)
    # NOTE: the island snap above rejoins into a NEW object - callers must use
    # the returned reference (the old one points at a removed object).
    return uruk


IDLE_FRAMES = (1, 16, 32)

# Torso dampening for retargets: quaternion angle scale per bone. Limbs copy
# verbatim (1.0); spine/chest/head shrink toward rest so the human hunch
# doesn't crumple the bulky uruk. Hip location deltas scale up x1.15 below.
# Arm chains swing at 0.55: our rest pose already holds the sword-arm raised,
# so verbatim stock swings hyper-extend past vertical and the separate armor
# shells disassemble (measured melee peak-frame breakup); dampening keeps
# swings in shell-tolerant range while stock key TIMES (hence speeds) stay.
DAMP_BASE = {"spine": 0.4, "spine1": 0.4, "chest": 0.45,
             "neck": 0.6, "head": 0.5,
             "shoulder_L": 0.55, "shoulder_R": 0.55,
             "arm_L": 0.55, "arm_R": 0.55,
             "forearm_L": 0.55, "forearm_R": 0.55,
             "hand_L": 0.55, "hand_R": 0.55}
# Melee adds: arm chains swing at 0.45 (peak-frame renders show pauldron
# plates peeling off the torso past ~0.55 arm swing on overhead slams -
# 0.45 keeps the chop readable while plates stay seated), fists locked to
# the natural rest curl (the stock grip-release splays giant uruk fingers
# into a wave), wrists calmed (stock sword-roll corkscrews the long
# forearms). Torso keeps base dampening so the twist still sells the hit.
DAMP_MELEE = {**DAMP_BASE,
              "shoulder_L": 0.45, "shoulder_R": 0.45,
              "arm_L": 0.45, "arm_R": 0.45,
              "forearm_L": 0.45, "forearm_R": 0.45,
              "hand_L": 0.45, "hand_R": 0.45,
              "finger_L": 0.0, "finger_R": 0.0,
              "fingertip_L": 0.0, "fingertip_R": 0.0}
LOC_SCALE = 1.15

STOCK_DIR = os.path.join(REF_DIR, "stock_anim")

# (stock file, uruk anim name, damp profile). Times copy verbatim -> stock
# variant speeds stay valid (verified: engine speed factor = value/100).
RETARGET_JOBS = [
    ("walk_relax.dae", "walk", DAMP_BASE),
    ("run_relax_2h.dae", "run", DAMP_BASE),
    ("attack_melee_2h_01.dae", "melee1", DAMP_MELEE),
    ("attack_melee_2h_02.dae", "melee2", DAMP_MELEE),
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


def author_idle(uruk, arm):
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
    act = bpy.data.actions.new("uruk_idle")
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


def export_idle(uruk, arm):
    out_anim = os.path.join(MOD, "art", "animation", "biped", "uruk_idle.dae")
    os.makedirs(os.path.dirname(out_anim), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    uruk.select_set(True)
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


def retarget_stock(uruk, arm, stock_name, out_name, damp):
    """Copy a stock Biped animation onto the uruk with torso dampening.

    Same bone names + same hierarchy, so rotation curves transfer 1:1 on
    limbs; spine/chest/head angles shrink (DAMP_TORSO) so the human hunch
    doesn't crumple the bulky uruk; hip location deltas scale up (LOC_SCALE)
    to uruk size. Key TIMES copy verbatim -> stock variant speeds stay valid.
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
    new_act = bpy.data.actions.new("uruk_" + out_name)
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
    out = os.path.join(MOD, "art", "animation", "biped", f"uruk_{out_name}.dae")
    bpy.ops.object.select_all(action="DESELECT")
    uruk.select_set(True)
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
    with open(os.path.join(var_dir, "uruk_relax.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<variant name="Base" frequency="1">\n'
                '  <animations>\n'
                '    <animation file="biped/uruk_idle.dae" name="idle" id="idle1" speed="35"/>\n'
                '    <animation file="biped/uruk_idle.dae" name="idle" id="idle2" speed="32"/>\n'
                f'    <animation file="{walk_file}" name="Walk" id="walk1" speed="30"/>\n'
                f'    <animation file="{walk_file}" name="Walk" id="walk2" speed="29"/>\n'
                f'    <animation file="{walk_file}" name="Walk" id="walk3" speed="28"/>\n'
                f'    <animation file="{run_file}" name="Run" id="run1" speed="8"/>\n'
                f'    <animation file="{run_file}" name="Run" id="run2" speed="9"/>\n'
                f'    <animation file="{run_file}" name="Run" id="run3" speed="10"/>\n'
                '    <animation event="0.5" file="biped/uruk_melee1.dae" name="attack_melee" id="attack1" speed="100"/>\n'
                '    <animation event="0.5" file="biped/uruk_melee2.dae" name="attack_melee" id="attack2" speed="100"/>\n'
                '    <animation event="0.5" file="biped/uruk_melee1.dae" name="attack_melee" id="attack3" speed="100"/>\n'
                '    <animation file="biped/infantry/promotion.dae" name="promotion" speed="80"/>\n'
                '  </animations>\n'
                '</variant>\n')
    log(f"wrote variant biped/uruk_relax.xml (walk={walk_file} run={run_file})")
    with open(os.path.join(var_dir, "uruk_capture.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<variant name="attack_capture">\n'
                '  <animations>\n'
                '    <animation file="biped/uruk_capture.dae" name="attack_capture" speed="100"/>\n'
                '  </animations>\n'
                '</variant>\n')
    log("wrote variant biped/uruk_capture.xml")


def main():
    argv = sys.argv
    args = argv[argv.index("--") + 1:] if "--" in argv else []
    if not args:
        print("Usage: blender --background --python build_uruk_rig.py -- <uruk.gltf|glb|fbx|obj> [target_tris] [scale] [ref_dae] [figure:left|right]")
        raise SystemExit(2)
    src = args[0]
    target = int(args[1]) if len(args) > 1 else DEFAULT_TARGET_TRIS
    scale = float(args[2]) if len(args) > 2 else URUK_SCALE
    ref = args[3] if len(args) > 3 else REF_DEFAULT
    which = args[4] if len(args) > 4 else FIGURE_DEFAULT
    if not os.path.isfile(src):
        raise SystemExit(f"input not found: {src}")
    clear()
    arm, ref_h = import_ref_armature(ref)
    uruk = import_uruk(src, which)
    # Center+scale BEFORE decimate (unlike the troll order): this source is
    # off-center in raw coords and use_symmetry decimates about the object
    # origin - decimating off-center shreds topology and heat then fails on
    # ALL verts. Scaling first also makes remove_doubles absolute thresholds
    # behave the same as the in-game proportions.
    place_and_scale(uruk, arm, ref_h, scale)
    _weld_shells(uruk)
    cleanup_decimate(uruk, target)
    restrict_deform_bones(arm)
    widen_bones(arm)
    uruk = skin_and_export(uruk, arm)
    author_idle(uruk, arm)
    export_idle(uruk, arm)
    for stock_name, out_name, damp in RETARGET_JOBS:
        retarget_stock(uruk, arm, stock_name, out_name, damp)
    write_variant("biped/uruk_walk.dae", "biped/uruk_run.dae")
    log("NEXT: test in 0 A.D. (mod selection -> Tolkien), check interestinglog.html for errors.")


if __name__ == "__main__":
    main()
