"""
Rig the Sketchfab Dark Orc Warrior to 0 A.D.'s BIPED skeleton (run inside Blender 3.0).

Cloned from build_troll_rig.py (that file is NOT modified) - pipeline spec:
docs/sketchfab-to-0ad.md.

Why Biped: the orc is humanoid (2 arms / 2 legs / head). Biped
(art/skeletons/biped.xml) already ships idle/walk/run/melee/death in
art/variants/biped/; stock bone names mean stock animations retarget by name.
No new skeleton.xml needed. Mesh .dae carries a Biped armature and the
engine maps it via the stock biped.xml.

Source (NOT bundled - download manually, CC-BY 4.0 by RavenMalmhaus):
  https://sketchfab.com/3d-models/dark-orc-warrior-4b9f2a23153246178a1668d2500ccab2
  (a.k.a. "Viking Orc Warrior"; use the GLB 1k download, ~173.9k tris armoured)

USAGE:
  1. Download model from Sketchfab (GLB 1k) to e.g. C:\\Users\\<you>\\Downloads\\dark_orc_warrior.glb
  2. Reference body must exist:
       %TEMP%\\0ad_ref\\meshes_skeletal_new_m_tunic_short.dae
     (contains the stock Biped armature + m_tunic_short mesh)
  3. "C:\\Program Files\\Blender Foundation\\Blender 3.0\\blender.exe" ^
       --background --python tools\\art_build\\build_darkorc_rig.py -- ^
       C:\\Users\\<you>\\Downloads\\dark_orc_warrior.glb
     Optional: append TARGET_TRIS (default 5500) and DARKORC_SCALE (default 1.15):
       ... -- C:\\Users\\<you>\\Downloads\\dark_orc_warrior.glb 5500 1.15
  4. Output: tolkien\\art\\meshes\\skeletal\\tolkien\\darkorc.dae (RIGGED mesh +
     Biped armature), darkorc_body.png, darkorc_CREDITS.txt,
     tolkien\\art\\animation\\biped\\darkorc_*.dae,
     tolkien\\art\\variants\\biped\\darkorc_relax.xml + darkorc_capture.xml
  5. Actor + template wiring is a manual follow-up (mirror
     tolkien/art/actors/units/mordor/infantry_darkorc.xml).

What the script does:
  - imports reference -> keeps Biped armature, deletes ref mesh
  - imports dark orc -> STRIPS weapon meshes, joins armour+body (armour stays
    merged: one material/UV), cleanup, ITERATIVE decimate ~173.9k -> ~5.5k
    tris (a single 0.05-clamped pass cannot reach it), single mat/UV
  - scales darkorc to ref_height * DARKORC_SCALE (~4.4 game units;
    game units: human body ~= 3.85, see docs/art-unit-template.md section 3)
  - scales armature to match, widens arm/leg bones for orc bulk (edit-mode
    heuristic, tweak WIDEN_* below for your mesh)
  - parents mesh with AUTOMATIC WEIGHTS (heat), exports selected mesh+armature
    as Collada .dae readable by Pyrogenesis/collada2pmd

Manual touch-up (expected for v1 -> v2):
  - open darkorc.dae in Blender, Weight Paint mode, fix armpit/groin bleed
  - if fists clip on walk, widen shoulder_L/R + arm_L/R edit bones further

Credit (REQUIRED by CC-BY): derivative of "Dark Orc Warrior"
(Viking Orc Warrior) by RavenMalmhaus, CC-BY 4.0.
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
DARKORC_SCALE = 1.15  # orc height = human ref height * this (~4.4 game units)
TEXTURE_GAIN = 1.8   # source albedo is near-black in Atlas; linear lift
WIDEN_ARMS = 1.3     # edit-bone X multiplier for shoulder/arm/forearm/hand
WIDEN_LEGS = 1.12    # edit-bone X multiplier for thigh/leg/foot

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
    # NOTE: cape1-3 deliberately excluded - no cape mesh on the darkorc;
    # leaving them deformable steals upper-back verts and creases the torso.
})

ARM_BONES = ("shoulder_L", "shoulder_R", "arm_L", "arm_R",
             "forearm_L", "forearm_R", "hand_L", "hand_R",
             "finger_L", "finger_R", "fingertip_L", "fingertip_R")
LEG_BONES = ("thigh_L", "thigh_R", "leg_L", "leg_R", "foot_L", "foot_R")
# Weapon anchors ride with the fists: widening moves hand_R/L outward but
# stock weapon_R/L/bow markers would stay behind, leaving swords/spears
# hovering ~0.3 units off the palm. Same x1.3 keeps the stock hand offset.
ANCHOR_BONES = ("weapon_R", "weapon_L", "weapon_bow")


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
    print("[darkorc-rig]", *a)


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


WEAPON_RE = None  # compiled lazily inside strip_weapons()


def strip_weapons(objs):
    """Remove carried-weapon meshes (0 A.D. attaches weapons via prop-points;
    a modelled-in sword/axe would double up and eat the tri budget). Armour
    stays: only name-matched weapons are dropped, everything else merges."""
    import re
    global WEAPON_RE
    if WEAPON_RE is None:
        WEAPON_RE = re.compile(
            r"weap|sword|axe|shield|blade|mace|hammer|club|knife|dagger|spear|"
            r"arrow|bow|hacha|espada|arma|katana", re.IGNORECASE)
    kept, dropped = [], []
    for o in objs:
        (dropped if WEAPON_RE.search(o.name or "") else kept).append(o)
    for o in dropped:
        log(f"stripping weapon mesh {o.name!r}")
        bpy.data.objects.remove(o, do_unlink=True)
    log(f"weapon strip: {len(dropped)} removed, {len(kept)} kept "
        f"({sorted(o.name for o in kept)})")
    if not kept:
        raise SystemExit("weapon strip removed everything - check WEAPON_RE")
    return kept


def import_darkorc(path):
    ext = os.path.splitext(path)[1].lower()
    log("importing darkorc", path)
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
        raise SystemExit("no meshes in darkorc download - check the file")
    log("source parts:", sorted(o.name for o in objs))
    objs = strip_weapons(objs)
    # TAG SOURCE PARTS: one 1.0 group per pre-join part (named by parent node:
    # Piezas/FaldaAbajo/FaldaArriba/Cinturon/Orco). join + decimate preserve
    # vertex groups, so the belt/skirt verts stay identifiable to the end -
    # letting the skirt strip below work deterministically instead of by
    # distance heuristics (which keep missing cloth with moderate arm weights
    # that still fly on big swings).
    for o in objs:
        tag = "PART_" + (o.parent.name if o.parent and o.parent.name else o.name)
        g = o.vertex_groups.new(name=tag)
        g.add([v.index for v in o.data.vertices], 1.0, "REPLACE")
    log("part tags:", sorted("PART_" + (o.parent.name if o.parent and o.parent.name else o.name) for o in objs))
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
    darkorc = bpy.context.view_layer.objects.active
    darkorc.name = "darkorc"
    return darkorc


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
        # ITERATIVE decimate: a single COLLAPSE pass with the 0.05 clamp
        # cannot reach 5.5k from ~173.9k (0.05 * 174k ~= 8.7k), and ultra-low
        # single ratios wreck topology. Loop with a gentle per-pass floor
        # (0.30 keeps heat-friendly topology: 174k -> 52k -> 15.6k -> 5.5k).
        for _pass in range(12):
            tris = sum(max(len(p.vertices) - 2, 1) for p in obj.data.polygons)
            if tris <= target_tris:
                break
            ratio = max(target_tris / max(tris, 1), 0.30)
            log(f"decimate pass {_pass + 1}: {tris} tris x{ratio:.3f} "
                f"-> ~{int(tris * ratio)}")
            mod = obj.modifiers.new("Decimate", "DECIMATE")
            mod.decimate_type = "COLLAPSE"
            mod.ratio = ratio
            mod.use_collapse_triangulate = True
            mod.use_symmetry = True
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.modifier_apply(modifier=mod.name)
        else:
            log("WARNING: decimate pass budget exhausted")
        tris = sum(max(len(p.vertices) - 2, 1) for p in obj.data.polygons)
        log(f"post-decimate {tris} tris, {len(obj.data.vertices)} verts")
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
    mat = bpy.data.materials.get("darkorc_body") or bpy.data.materials.new("darkorc_body")
    mat.use_nodes = True
    obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = True
        p.material_index = 0


def place_and_scale(obj, arm, ref_h, scale):
    # normalize darkorc rotation/scale, then size to ref_h * scale
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    h = max(obj.dimensions.z, 0.001)
    f = (ref_h * scale) / h
    log(f"darkorc height {h:.2f} -> x{f:.3f} = {ref_h * scale:.2f} game units")
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
        elif b.name in ANCHOR_BONES:
            b.head.x *= WIDEN_ARMS
            b.tail.x *= WIDEN_ARMS
            n += 1
    bpy.ops.object.mode_set(mode="OBJECT")
    log(f"widened {n} arm/leg bones (arms x{WIDEN_ARMS}, legs x{WIDEN_LEGS}) + weapon anchors")


def _seg_dist(co, h, t):
    seg = t - h
    l2 = seg.length_squared
    f = max(0.0, min(1.0, (co - h).dot(seg) / l2 if l2 > 1e-12 else 0.0))
    return ((h + seg * f) - co).length


MISW_RATIO = 2.5   # dominant bone >2.5x farther than nearest deform = error
MISW_FLOOR = 0.6   # ... and farther than this (game units) - spares soft joints


def fix_misweights(obj, arm):
    """Global mis-weight correction.

    Heat splatters hand/finger weights across the skirt (and arm weights
    across torso armor): perfect at rest, but when the hand flies up in melee
    the skirt teleports with it. Measured on the export: 38-119x edge stretch
    on hip<->fingertip pairs, back-skirt verts displaced 3.8 units with the
    right hand. Rule (deliberately conservative): only the DOMINANT group is
    suspect, and only if its bone lies farther than max(0.6, 2.5x the nearest
    deform bone) - true splatter (culprits measured 1.6-2.0 units out at ~3x).
    A torso vert hanging against the arm keeps its chest weights (dominant
    bone nearby); soft armpit boundaries are untouched. Dropped dominance
    promotes the largest surviving weight (renormalized), else nearest bone
    1.0; repeats while the new dominant still triggers. A light smooth blends
    the edited transitions; residual is measured AFTER it.
    """
    vg = obj.vertex_groups
    segs = {b.name: (arm.matrix_world @ b.head, arm.matrix_world @ b.tail)
            for b in arm.pose.bones if b.name in DEFORM_BONES}
    mesh_world = obj.matrix_world

    def nearest(co):
        return min(((_seg_dist(co, s, t), n) for n, (s, t) in segs.items()),
                   key=lambda t: t[0])

    def dom_entry(v):
        ds = _skin_entries(obj, v)
        e = max(ds, key=lambda g: g.weight)
        return vg[e.group].name, e.weight

    def offender(v):
        if not _skin_entries(obj, v):
            return None
        co = mesh_world @ v.co
        d_near, _n = nearest(co)
        name, _w = dom_entry(v)
        d_dom = _seg_dist(co, *segs[name])
        if d_dom > max(MISW_FLOOR, MISW_RATIO * max(d_near, 1e-9)):
            return name
        return None

    moved = 0
    for v in obj.data.vertices:
        if not _skin_entries(obj, v):
            continue
        orig, _w = dom_entry(v)
        for _ in range(4):
            bad = offender(v)
            if bad is None:
                break
            vg[bad].remove([v.index])
            rest = [(vg[e.group].name, e.weight) for e in _skin_entries(obj, v)]
            if rest:
                tot = sum(w for _, w in rest)
                for n, w in rest:
                    vg[n].add([v.index], w / tot, "REPLACE")
            else:
                _d, n_near = nearest(mesh_world @ v.co)
                vg[n_near].add([v.index], 1.0, "REPLACE")
        if _skin_entries(obj, v) and dom_entry(v)[0] != orig:
            moved += 1
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="WEIGHT_PAINT")
    bpy.ops.object.vertex_group_smooth(group_select_mode="ALL", factor=0.5, repeat=3)
    bpy.ops.object.mode_set(mode="OBJECT")
    residual = sum(1 for v in obj.data.vertices if _skin_entries(obj, v) and offender(v))
    log(f"mis-weight fix: {moved} verts re-parented, "
        f"residual offenders after smooth: {residual}")


HAND_CHAIN = frozenset({"forearm_L", "forearm_R", "hand_L", "hand_R",
                        "finger_L", "finger_R", "fingertip_L", "fingertip_R"})
# True-torso only (deliberately NOT arm/shoulder: forearm<->hand and
# elbow tris live in the same z-band and must never be cut).
CREASE_TORSO = frozenset({"hip", "spine", "spine1", "chest",
                          "thigh_L", "thigh_R", "leg_L", "leg_R"})


def cut_contact_welds(obj):
    """Delete weld triangles where hands touch torso/skirt in bind pose.

    The source models the lowered hands touching the body as one continuous
    shell, so decimate triangulated across the contact: short triangles with
    verts on the hand side AND the torso side. In motion the hand separates
    and those tris stretch into 1-1.7 unit shards (measured). No weight fix
    can save them (endpoints must follow different bones), so cut them: at
    rest the lips coincide (invisible seam); in motion a slit opens exactly
    where anatomy separates anyway. Strictly limited to short mixed tris in
    the hand-contact zone (never the shoulder joint or legit anatomy).
    Aborts if the cut count looks absurd.
    """
    import bmesh
    vg = obj.vertex_groups

    def dom_name(vi):
        v = obj.data.vertices[vi]
        ds = _skin_entries(obj, v)
        return vg[max(ds, key=lambda e: e.weight).group].name if ds else None

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    kill = []
    for f in bm.faces:
        idx = [v.index for v in f.verts]
        doms = {dom_name(i) for i in idx}
        if not (doms & HAND_CHAIN and doms & CREASE_TORSO):
            continue
        cx = sum(obj.data.vertices[i].co.x for i in idx) / len(idx)
        cz = sum(obj.data.vertices[i].co.z for i in idx) / len(idx)
        if not (abs(cx) > 0.35 and 1.7 < cz < 2.4):
            continue
        mx = max((obj.data.vertices[idx[i]].co - obj.data.vertices[idx[j]].co).length
                 for i in range(len(idx)) for j in range(i + 1, len(idx)))
        if mx < 0.25:
            kill.append(f)
    log(f"contact welds: {len(kill)} tris marked (mesh has {len(bm.faces)} faces)")
    if len(kill) > 300:
        log("WARNING: cut count absurd - aborting cut, keeping mesh whole")
    elif kill:
        bmesh.ops.delete(bm, geom=kill, context="FACES")
        bm.to_mesh(obj.data)
        obj.data.update()
        log(f"contact welds cut; mesh now {len(obj.data.polygons)} polys")
    bm.free()


def _skin_entries(obj, v):
    """Group entries carrying real skin weights (excludes PART_ part tags,
    which sit at 1.0 on every vert and would otherwise fake coverage and
    dominate every dominant-group query)."""
    vg = obj.vertex_groups
    return [e for e in v.groups if not vg[e.group].name.startswith("PART_")]


def cut_crease_band(obj):
    """Delete the hand/torso contact-crease band (the two ribbons).

    Where each hanging hand touches the torso the weights form a narrow
    gradient (fingertip 0.47<->0.69 vs spine1 across ~4 rows in 0.2 units).
    On a 3-unit hand swing that band stretches into 0.7-0.9 unit ribbons -
    measured, both hands, symmetric. Smoothing cannot fix it (the band IS
    smooth; it is just narrow) and re-parenting either side only moves the
    tear. So cut tris fully inside the band: at rest the lips coincide
    (hairline seam); in motion a slit opens exactly where the hand leaves
    the torso. Strict definition (mixed hand+torso secondaries AND the hand
    contact zone) keeps wrists/elbows/shoulders safe: those never carry
    >0.15 torso weight (wrist) or live outside the zone (elbow/shoulder).
    """
    import bmesh
    vg = obj.vertex_groups

    def is_crease(vi):
        v = obj.data.vertices[vi]
        w = {}
        for e in v.groups:
            w[vg[e.group].name] = w.get(vg[e.group].name, 0) + e.weight
        hand = sum(w.get(b, 0) for b in HAND_CHAIN)
        torso = sum(w.get(b, 0) for b in CREASE_TORSO)
        c = v.co
        return (0.2 <= hand <= 0.9 and torso > 0.15
                and abs(c.x) > 0.4 and 1.8 < c.z < 2.3)

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    kill = [f for f in bm.faces
            if sum(1 for v in f.verts if is_crease(v.index)) >= 2]
    log(f"crease band: {len(kill)} tris marked (mesh has {len(bm.faces)} faces)")
    if len(kill) > 150:
        log("WARNING: crease cut absurd - aborting, keeping mesh whole")
    elif kill:
        bmesh.ops.delete(bm, geom=kill, context="FACES")
        bm.to_mesh(obj.data)
        obj.data.update()
        log(f"crease band cut; mesh now {len(obj.data.polygons)} polys")
    bm.free()
    # LIP CLEANUP: torso-side verts edging the cut still carry 0.1-0.3
    # fingertip secondaries, stretching 0.5-0.8 on extreme frames. Drop all
    # hand-chain weights there so the lip stays fully with the torso and the
    # slit opens cleanly. No smooth after: the hard edge is the point.
    lips = 0
    for v in obj.data.vertices:
        c = v.co
        if not (abs(c.x) > 0.4 and 1.8 < c.z < 2.3):
            continue
        entries = [(vg[e.group].name, e.weight) for e in v.groups]
        dom = max(entries, key=lambda t: t[1])[0] if entries else None
        if dom not in CREASE_TORSO:
            continue
        if not any(n in HAND_CHAIN for n, _w in entries):
            continue
        keep = [(n, w) for n, w in entries if n not in HAND_CHAIN]
        for n, _w in entries:
            if n in HAND_CHAIN:
                vg[n].remove([v.index])
        tot = sum(w for _, w in keep)
        for n, w in keep:
            vg[n].add([v.index], w / tot, "REPLACE")
        lips += 1
    log(f"crease lips cleaned: {lips} verts pinned to torso")


# Attachpoints the actors need. These live on marker bones (deform disabled
# for skinning); both safeguards below run AFTER all weight ops, so zero
# weights can attach post-hoc - joints merely become present for props.
PROP_BONES = ("weapon_R", "weapon_L", "weapon_bow", "head")


def stock_skin_joints(ref_path):
    """Joint names in the reference mesh's skin (stock capability set)."""
    import xml.etree.ElementTree as ET
    try:
        root = ET.parse(ref_path).getroot()
    except Exception as e:
        log(f"WARNING: cannot parse ref joints ({e})")
        return []
    ns = {"c": "http://www.collada.org/2005/11/COLLADASchema"}
    for na in root.findall(".//c:Name_array", ns):
        if "joints" in (na.get("id") or "") and na.text:
            return na.text.split()
    return []


def ensure_prop_joints(obj, arm, ref_path):
    """Match the stock skin-joint capability set.

    Blender exports skin joints from deform bones/groups; stock meshes carry
    ~48 joints (deform + attachpoints) while a deform-only export carries 24
    and the engine drops the rest ('Failed to find matching prop point
    weapon_R', weapons vanish). Read the reference DAE's joint list and
    ensure every one exists here: re-enable deform + add (empty) groups AFTER
    all weight ops, so zero weights attach post-hoc - joints merely present.
    Stock attachpoints (back, shield_arm, ...) then resolve exactly as stock.
    """
    vg = obj.vertex_groups
    have = set(g.name for g in vg)
    want = stock_skin_joints(ref_path) or list(PROP_BONES)
    added = 0
    for name in want:
        if name in arm.data.bones:
            arm.data.bones[name].use_deform = True
        if name not in have and name in arm.data.bones:
            vg.new(name=name)
            added += 1
    log(f"prop joints: stock set={len(want)}, empty groups added={added}")


def _clear_skin(obj):
    for m in [m for m in obj.modifiers if m.type == "ARMATURE"]:
        obj.modifiers.remove(m)
    while len(obj.vertex_groups):
        obj.vertex_groups.remove(obj.vertex_groups[0])


APOSE_DEG = 9.0  # arms-out sculpt nudge (bind pose has fists glued to thighs)
LEFT_CHAIN = frozenset({"shoulder_L", "arm_L", "forearm_L", "hand_L",
                        "finger_L", "fingertip_L"})
RIGHT_CHAIN = frozenset({"shoulder_R", "arm_R", "forearm_R", "hand_R",
                         "finger_R", "fingertip_R"})


def apply_apose(obj, arm):
    """Rotate arm flesh outward about the (widened) shoulder pivots.

    The source bind pose glues the fists to the thighs, so at idle the hands
    vanish against the dark body. A small sculpt-level A-pose opens the
    silhouette (stock units rest arms-out too). Weight-proportional rotation
    keeps armpit blends continuous; weapon anchors rotate rigidly with the
    hand so palm-relative offsets survive. Bones are untouched, so all
    (re)targeted animations keep working: rotation composes about the same
    pivots the bones use.
    """
    import math as _m
    from mathutils import Matrix
    vg = obj.vertex_groups
    me = obj.data
    for side, chain, deg in (
            ("L", LEFT_CHAIN, -APOSE_DEG),
            ("R", RIGHT_CHAIN, APOSE_DEG)):
        pivot = arm.matrix_world @ arm.pose.bones[f"shoulder_{side}"].head.copy()
        moved = dx = 0
        for v in me.vertices:
            f = sum(e.weight for e in v.groups
                    if vg[e.group].name in chain)
            if f <= 0.001:
                continue
            m = Matrix.Rotation(_m.radians(deg) * min(f, 1.0), 4, "Y")
            p = m @ (v.co - pivot) + pivot
            dx += p.x - v.co.x
            v.co = p
            moved += 1
        log(f"apose {side}: {moved} verts, mean dx={dx / max(moved, 1):+.3f} "
            f"(want {'>' if side == 'L' else '<'}0)")
    # anchors rotate rigidly (f=1) with the hand - edit-mode session
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    for side, deg in (("L", -APOSE_DEG), ("R", APOSE_DEG)):
        pivot = arm.matrix_world @ arm.data.edit_bones[f"shoulder_{side}"].head.copy()
        m = Matrix.Rotation(_m.radians(deg), 4, "Y")
        for aname in ([f"weapon_{side}"] + (["weapon_bow"] if side == "L" else [])):
            eb = arm.data.edit_bones.get(aname)
            if eb is None:
                continue
            eb.head = m @ (eb.head - pivot) + pivot
            eb.tail = m @ (eb.tail - pivot) + pivot
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.update_tag()
    log("apose anchors rotated with hands")


def _weight_coverage(obj):
    """Fraction of verts carrying at least one vertex-group weight."""
    n = len(obj.data.vertices)
    if not n:
        return 1.0
    return sum(1 for v in obj.data.vertices if _skin_entries(obj, v)) / n


# Belt + skirt parts: cloth must NEVER follow arms, whatever heat says.
SKIRT_PARTS = frozenset({"PART_Cinturon_low", "PART_FaldaArriba_low",
                         "PART_FaldaAbajo_low"})
# Lower-body + torso bones allowed to drive cloth.
CLOTH_BONES = frozenset({"hip", "spine", "spine1", "chest", "neck", "head",
                         "thigh_L", "thigh_R", "leg_L", "leg_R",
                         "foot_L", "foot_R"})


def strip_skirt_arm_weights(obj, arm):
    """Remove every arm-chain weight from belt/skirt verts (part-tagged).

    Cloth physics by rigging convention: skirt/belt follow hips/thighs only.
    Heat + smoothing smear arm weights across the hanging cloth (worst on the
    rear panel, which has no arm contact at all in bind pose yet flew with
    the raised arm in Atlas). Deterministic: any vert whose strongest part
    tag is belt/skirt loses all ARM_BONES groups; keepers renormalize, else
    the nearest cloth bone takes 1.0. Runs AFTER the last smooth (smoothing
    would re-bleed arm weights back in) and deletes the PART_ tags so they
    never export as bogus skin joints.
    """
    vg = obj.vertex_groups
    segs = {b.name: (arm.matrix_world @ b.head, arm.matrix_world @ b.tail)
            for b in arm.pose.bones if b.name in CLOTH_BONES}
    mesh_world = obj.matrix_world

    def part_of(v):
        best, bw = None, 0.5
        for e in v.groups:
            n = vg[e.group].name
            if n in SKIRT_PARTS and e.weight > bw:
                best, bw = n, e.weight
        return best

    moved = 0
    for v in obj.data.vertices:
        if part_of(v) is None:
            continue
        entries = [(vg[e.group].name, e.weight) for e in v.groups
                   if not vg[e.group].name.startswith("PART_")]
        if not any(n in ARM_BONES for n, _w in entries):
            continue
        keep = [(n, w) for n, w in entries if n not in ARM_BONES]
        for n, _w in entries:
            if n in ARM_BONES:
                vg[n].remove([v.index])
        if keep:
            tot = sum(w for _, w in keep)
            for n, w in keep:
                vg[n].add([v.index], w / tot, "REPLACE")
        else:
            co = mesh_world @ v.co
            nb = min(segs, key=lambda b: _seg_dist(co, *segs[b]))
            vg[nb].add([v.index], 1.0, "REPLACE")
        moved += 1
    for g in [g for g in vg if g.name.startswith("PART_")]:
        vg.remove(g)
    log(f"skirt strip: {moved} cloth verts cleaned of arm weights, PART tags removed")
    return moved


def _fill_bare_verts(obj, arm):
    """Assign weightless verts to the nearest deform bone (weight 1.0).

    Heat leaves extremities (fingertips, armour tips, skirt hem) bare and the
    engine pins bare verts to bind pose (rigid statue bits), so full coverage
    matters more than perfect falloff there; the smooth pass below blends the
    1.0 assignments at region boundaries."""
    from collections import Counter
    deform = [b for b in arm.pose.bones if b.name in DEFORM_BONES]
    segs = [(b.name, arm.matrix_world @ b.head, arm.matrix_world @ b.tail)
            for b in deform]
    mesh_world = obj.matrix_world
    filled = Counter()
    for v in obj.data.vertices:
        if _skin_entries(obj, v):
            continue
        co = mesh_world @ v.co
        best, best_d = None, None
        for name, h, t in segs:
            seg = t - h
            l2 = seg.length_squared
            f = max(0.0, min(1.0, (co - h).dot(seg) / l2 if l2 > 1e-12 else 0.0))
            d = ((h + seg * f) - co).length
            if best_d is None or d < best_d:
                best, best_d = name, d
        g = obj.vertex_groups.get(best)
        if g is None:
            g = obj.vertex_groups.new(name=best)
        g.add([v.index], 1.0, "REPLACE")
        filled[best] += 1
    log(f"nearest-bone fill: {sum(filled.values())} verts -> "
        f"{dict(sorted(filled.items()))}")


def _parent(obj, arm, mode, label):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type=mode)
    log(f"skinned with {label}: coverage={_weight_coverage(obj):.3f}")


def skin_and_export(darkorc, arm, ref_path):
    # parent mesh -> armature. Heat first (best quality); harsh iterative
    # decimate can leave heat-hostile topology (Bone Heat finds no solution
    # for extremities), so nearest-bone-fill the bare verts: the engine pins
    # weightless verts to bind pose (rigid statue bits). Envelope weights
    # were tried and rejected (79% coverage, arms/hands missed entirely).
    # (The troll never hit this: 17.9k needed one gentle pass; the dark orc
    # needs 174k -> 5.5k.)
    _parent(darkorc, arm, "ARMATURE_AUTO", "provisional weights (apose ref)")
    apply_apose(darkorc, arm)
    _clear_skin(darkorc)
    _parent(darkorc, arm, "ARMATURE_AUTO", "automatic weights (heat)")
    if _weight_coverage(darkorc) < 0.999:
        _fill_bare_verts(darkorc, arm)
        log(f"post-fill coverage={_weight_coverage(darkorc):.3f}")
    log("vertex groups:", len(darkorc.vertex_groups))
    bad = sorted(g.name for g in darkorc.vertex_groups
                 if g.name not in DEFORM_BONES and not g.name.startswith("PART_"))
    if bad:
        log("WARNING: weights on non-deform bones:", bad)
        for name in bad:
            darkorc.vertex_groups.remove(darkorc.vertex_groups[name])
        log("removed non-deform groups")
    # per-vertex sanity: strongest group must be a nearby deform bone;
    # report the distribution so spikes get caught here, not in Atlas
    from collections import Counter
    top = Counter()
    for v in darkorc.data.vertices:
        ds = [e for e in v.groups
              if not darkorc.vertex_groups[e.group].name.startswith("PART_")]
        if ds:
            g = max(ds, key=lambda e: e.weight)
            top[darkorc.vertex_groups[g.group].name] += 1
    log("dominant-group histogram:", dict(sorted(top.items())))
    bare = sum(1 for v in darkorc.data.vertices if not _skin_entries(darkorc, v))
    log(f"unweighted verts: {bare}/{len(darkorc.data.vertices)}")
    if bare:
        log("WARNING: unweighted verts present - engine pins them to bind pose")
    # soften weight boundaries (waist/hip pinch from heat + mirror decimate):
    # smooth all deform groups so chest<->hip<->thigh transitions are gradual
    bpy.ops.object.select_all(action="DESELECT")
    darkorc.select_set(True)
    bpy.context.view_layer.objects.active = darkorc
    bpy.ops.object.mode_set(mode="WEIGHT_PAINT")
    bpy.ops.object.vertex_group_smooth(group_select_mode="ALL", factor=0.5, repeat=4)
    bpy.ops.object.mode_set(mode="OBJECT")
    log("smoothed deform weights")
    fix_misweights(darkorc, arm)
    cut_contact_welds(darkorc)
    strip_skirt_arm_weights(darkorc, arm)
    cut_crease_band(darkorc)
    ensure_prop_joints(darkorc, arm, ref_path)
    bare = sum(1 for v in darkorc.data.vertices if not _skin_entries(darkorc, v))
    log(f"post-fix coverage={(len(darkorc.data.vertices) - bare) / len(darkorc.data.vertices):.3f}")
    # texture: Principled 'Base Color' image -> 512px baseTex. The source
    # packs 3x 1k maps (albedo JPG + data PNG + normal-map PNG) on different
    # sockets of ONE shared material; blind largest-image fallback could grab
    # the NORMAL map and bake a pale-blue orc (§7 pale-flash class of bug),
    # so follow the socket and only fall back to largest on failure.
    out_png = os.path.join(MOD, "art", "textures", "skins", "skeletal", "tolkien", "darkorc_body.png")
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    base_img = None
    # NOTE: the mesh slots were already cleared to one fresh material, so
    # search ALL materials for the imported source (TT_checker_* holds the
    # Principled Base Color link we need).
    for m in list(bpy.data.materials):
        if m and m.use_nodes and m.node_tree:
            for n in m.node_tree.nodes:
                if n.type == "BSDF_PRINCIPLED":
                    inp = n.inputs.get("Base Color")
                    if inp and inp.links and inp.links[0].from_node.type == "TEX_IMAGE":
                        base_img = inp.links[0].from_node.image
                        log("texture socket: Base Color ->", base_img.name if base_img else None)
                        break
        if base_img is not None:
            break
    if base_img is None:
        cands = [img for img in bpy.data.images
                 if img.type == "IMAGE" and min(img.size[:]) >= 8
                 and "Render Result" not in img.name and "Viewer Node" not in img.name]
        if cands:
            base_img = max(cands, key=lambda i: i.size[0] * i.size[1])
            log("texture fallback (largest):", base_img.name, list(base_img.size[:]))
    if base_img is not None:
        img = base_img
        log("texture source:", img.name, list(img.size[:]))
        img.scale(512, 512)
        if TEXTURE_GAIN != 1.0:
            # Source albedo renders near-black in Atlas (mean rgb ~0.06);
            # linear gain keeps detail, alpha untouched.
            import time as _t
            _t0 = _t.time()
            px = list(img.pixels)
            g = TEXTURE_GAIN
            for i in range(0, len(px), 4):
                px[i] = 1.0 if px[i] * g >= 1.0 else px[i] * g
                px[i + 1] = 1.0 if px[i + 1] * g >= 1.0 else px[i + 1] * g
                px[i + 2] = 1.0 if px[i + 2] * g >= 1.0 else px[i + 2] * g
            img.pixels.foreach_set(px)
            img.update()
            log(f"texture gain x{g} applied in {(_t.time() - _t0):.0f}s")
        img.filepath_raw = out_png
        img.file_format = "PNG"
        img.save()
        log("wrote", out_png)
    else:
        log("WARNING: no source texture found")
    # export mesh + armature (same call pattern as build_orcs.py - known good on 3.0)
    out_dae = os.path.join(MOD, "art", "meshes", "skeletal", "tolkien", "darkorc.dae")
    os.makedirs(os.path.dirname(out_dae), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    darkorc.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.wm.collada_export(filepath=out_dae, selected=True,
                               include_animations=False)
    log("EXPORTED", out_dae)
    with open(os.path.join(os.path.dirname(out_dae), "darkorc_CREDITS.txt"), "w", encoding="utf-8") as f:
        f.write("Derivative of 'Dark Orc Warrior' (Viking Orc Warrior) by "
                "RavenMalmhaus, CC-BY 4.0.\n"
                "Source: https://sketchfab.com/3d-models/dark-orc-warrior-4b9f2a23153246178a1668d2500ccab2\n"
                "Changes: stripped carried weapons (none as separate meshes - no-op logged), "
                "armour kept merged (one material/UV), iteratively decimated "
                "~173.9k -> ~5.5k tris, rigged to stock 0 A.D. "
                "Biped (art/skeletons/biped.xml), rescaled ~1.15x human, 512px baseTex "
                "(Principled Base Color map; packed data/normal maps dropped), "
                "global mis-weight correction (hand weights had splattered the skirt).\n"
                "Custom tall idle + walk + run (biped/darkorc_*.dae); melee/death/promotion stock.\n")
    # sanity: verts under engine hard limit, armature present
    me = darkorc.data
    log(f"DONE verts={len(me.vertices)} (limit 32768), bones={len(arm.data.bones)}")
    missing = [b for b in ("hip", "chest", "head", "hand_R", "foot_L") if b not in arm.data.bones]
    if missing:
        log("WARNING missing biped bones:", missing)


IDLE_FRAMES = (1, 16, 32)

# Torso dampening for retargets: quaternion angle scale per bone. Limbs copy
# verbatim (1.0); spine/chest/head shrink toward rest so the human hunch
# doesn't crumple the bulky darkorc. Hip location deltas scale up x1.15 below.
DAMP_BASE = {"spine": 0.4, "spine1": 0.4, "chest": 0.45,
             "neck": 0.6, "head": 0.5}
# Melee adds: fists locked to the natural rest curl (the stock grip-release
# splays giant darkorc fingers into a wave), wrists calmed (stock sword-roll
# corkscrews the long forearms). Arms keep full swing.
DAMP_MELEE = {**DAMP_BASE,
              "shoulder_L": 0.6, "shoulder_R": 0.6,
              "arm_L": 0.7, "arm_R": 0.7,
              "forearm_L": 0.7, "forearm_R": 0.7,
              "hand_L": 0.45, "hand_R": 0.45,
              "finger_L": 0.0, "finger_R": 0.0,
              "fingertip_L": 0.0, "fingertip_R": 0.0}
LOC_SCALE = 1.15

STOCK_DIR = os.path.join(REF_DIR, "stock_anim")

# (stock file, darkorc anim name, damp profile). Times copy verbatim -> stock
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


def author_idle(darkorc, arm):
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
    act = bpy.data.actions.new("darkorc_idle")
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


def export_idle(darkorc, arm):
    out_anim = os.path.join(MOD, "art", "animation", "biped", "darkorc_idle.dae")
    os.makedirs(os.path.dirname(out_anim), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    darkorc.select_set(True)
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


def retarget_stock(darkorc, arm, stock_name, out_name, damp):
    """Copy a stock Biped animation onto the darkorc with torso dampening.

    Same bone names + same hierarchy, so rotation curves transfer 1:1 on
    limbs; spine/chest/head angles shrink (DAMP_TORSO) so the human hunch
    doesn't crumple the bulky darkorc; hip location deltas scale up (LOC_SCALE)
    to darkorc size. Key TIMES copy verbatim -> stock variant speeds stay valid.
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
    new_act = bpy.data.actions.new("darkorc_" + out_name)
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
    out = os.path.join(MOD, "art", "animation", "biped", f"darkorc_{out_name}.dae")
    bpy.ops.object.select_all(action="DESELECT")
    darkorc.select_set(True)
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
    # walk/run 1.10s, attack/capture 0.83s. Retargets copy key times verbatim
    # so stock-timed speeds stay valid; idle/walk/run values mirrored from the
    # validated troll build (custom 32f idle wants ~3s loop -> speed ~35).
    var_dir = os.path.join(MOD, "art", "variants", "biped")
    os.makedirs(var_dir, exist_ok=True)
    with open(os.path.join(var_dir, "darkorc_relax.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<variant name="Base" frequency="1">\n'
                '  <animations>\n'
                '    <animation file="biped/darkorc_idle.dae" name="idle" id="idle1" speed="35"/>\n'
                '    <animation file="biped/darkorc_idle.dae" name="idle" id="idle2" speed="32"/>\n'
                f'    <animation file="{walk_file}" name="Walk" id="walk1" speed="30"/>\n'
                f'    <animation file="{walk_file}" name="Walk" id="walk2" speed="29"/>\n'
                f'    <animation file="{walk_file}" name="Walk" id="walk3" speed="28"/>\n'
                f'    <animation file="{run_file}" name="Run" id="run1" speed="8"/>\n'
                f'    <animation file="{run_file}" name="Run" id="run2" speed="9"/>\n'
                f'    <animation file="{run_file}" name="Run" id="run3" speed="10"/>\n'
                '    <animation event="0.5" file="biped/darkorc_melee1.dae" name="attack_melee" id="attack1" speed="100"/>\n'
                '    <animation event="0.5" file="biped/darkorc_melee2.dae" name="attack_melee" id="attack2" speed="100"/>\n'
                '    <animation event="0.5" file="biped/darkorc_melee1.dae" name="attack_melee" id="attack3" speed="100"/>\n'
                '    <animation file="biped/infantry/promotion.dae" name="promotion" speed="80"/>\n'
                '  </animations>\n'
                '</variant>\n')
    log(f"wrote variant biped/darkorc_relax.xml (walk={walk_file} run={run_file})")
    with open(os.path.join(var_dir, "darkorc_capture.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<variant name="attack_capture">\n'
                '  <animations>\n'
                '    <animation file="biped/darkorc_capture.dae" name="attack_capture" speed="100"/>\n'
                '  </animations>\n'
                '</variant>\n')
    log("wrote variant biped/darkorc_capture.xml")


def main():
    argv = sys.argv
    args = argv[argv.index("--") + 1:] if "--" in argv else []
    if not args:
        print("Usage: blender --background --python build_darkorc_rig.py -- <darkorc.gltf|glb|fbx|obj> [target_tris] [scale] [ref_dae]")
        raise SystemExit(2)
    src = args[0]
    target = int(args[1]) if len(args) > 1 else DEFAULT_TARGET_TRIS
    scale = float(args[2]) if len(args) > 2 else DARKORC_SCALE
    ref = args[3] if len(args) > 3 else REF_DEFAULT
    if not os.path.isfile(src):
        raise SystemExit(f"input not found: {src}")
    clear()
    arm, ref_h = import_ref_armature(ref)
    darkorc = import_darkorc(src)
    cleanup_decimate(darkorc, target)
    place_and_scale(darkorc, arm, ref_h, scale)
    restrict_deform_bones(arm)
    widen_bones(arm)
    skin_and_export(darkorc, arm, ref)
    author_idle(darkorc, arm)
    export_idle(darkorc, arm)
    for stock_name, out_name, damp in RETARGET_JOBS:
        retarget_stock(darkorc, arm, stock_name, out_name, damp)
    write_variant("biped/darkorc_walk.dae", "biped/darkorc_run.dae")
    log("NEXT: test in 0 A.D. (mod selection -> Tolkien), check interestinglog.html for errors.")


if __name__ == "__main__":
    main()
