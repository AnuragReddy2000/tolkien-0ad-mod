"""
Rig the Sketchfab realistic elf warrior to 0 A.D.'s BIPED skeleton (run inside Blender 3.0).

Cloned from tools/art_build/build_troll_rig.py (DO NOT edit the troll script
for elf work) - same pipeline, elf parameters. See
docs/sketchfab-to-0ad.md for the full pipeline rationale.

Why Biped: elf is humanoid (2 arms / 2 legs / head). Biped
(art/skeletons/biped.xml) already ships idle/walk/run/melee/death in
art/variants/biped/. Same bone names = stock animations retarget by name,
no new skeleton.xml needed.

Source (NOT bundled - download manually, CC-BY 4.0 by zaini.AI):
  https://sketchfab.com/3d-models/realistic-3d-fantasy-male-elf-warrior-b40d56a51c574a6e8e09e001d3e7530f

USAGE:
  1. Download model from Sketchfab (GLB) to e.g. C:\\Users\\<you>\\Downloads\\realistic_3d_fantasy_male_elf_warrior.glb
  2. Reference body must exist:
       %TEMP%\\0ad_ref\\meshes_skeletal_new_m_tunic_short.dae
     (contains the stock Biped armature + m_tunic_short mesh)
  3. Stock anims must exist in %TEMP%\\0ad_ref\\stock_anim\\ (walk_relax.dae,
     run_relax_2h.dae, attack_melee_2h_01/02.dae, capturing_a.dae)
  4. "C:\\Program Files\\Blender Foundation\\Blender 3.0\\blender.exe" ^
       --background --python tools\\art_build\\build_elf_rig.py -- ^
       C:\\Users\\<you>\\Downloads\\realistic_3d_fantasy_male_elf_warrior.glb
     Optional: append TARGET_TRIS (default 4500) and ELF_SCALE (default 1.05):
       ... -- C:\\Users\\<you>\\Downloads\\realistic_3d_fantasy_male_elf_warrior.glb 4500 1.05
  5. Output: tolkien\\art\\meshes\\skeletal\\tolkien\\elf.dae (RIGGED mesh +
     Biped armature), elf_body.png, elf_CREDITS.txt,
     tolkien\\art\\animation\\biped\\elf_*.dae,
     tolkien\\art\\variants\\biped\\elf_relax.xml + elf_capture.xml

What the script does:
  - imports reference -> keeps Biped armature, deletes ref mesh
  - imports elf -> EXCLUDES a separate sword prop if present (+ display
    base), joins body (leather armour merged), cleanup, single decimate
    pass to ~4500 tris, single mat/UV
  - scales elf to ref_height * ELF_SCALE (~4.0 game units; tall slim elf)
  - scales armature to match, keeps stock bone widths (WIDEN_* = 1.0, no
    bulk), then drops the arm chains from A-pose to a hanging rest pose -
    this source stands arms-down, so stock spread arms float outside the
    mesh and heat weights collapse (see drop_arm_chains)
  - restricts to the 24 stock deform bones, parents mesh with AUTOMATIC
    WEIGHTS (heat), smooths deform groups x4, exports selected mesh+armature
    as Collada .dae readable by Pyrogenesis/collada2pmd
  - authors a tall custom idle, retargets 5 stock anims with torso
    dampening, writes relax + capture variants

Topology note: AI-generated source, single 5k-vert mesh (~10k tris), 4 UV
layers collapsed to one. Non-manifold seam verts (~3%) are normal open
seams, not broken islands - remove_doubles + delete_loose handle them.

Manual touch-up (expected for v1 -> v2):
  - open elf.dae in Blender, Weight Paint mode, fix armpit/groin bleed
  - for a bow/sword prop, attach to weapon_R like orc_sword

Credit (REQUIRED by CC-BY): derivative of "Realistic 3D fantasy male elf
warrior" by zaini.AI, CC-BY 4.0.
"""
import bpy
import os
import sys

MOD = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tolkien"))
REF_DIR = os.environ.get(
    "ZEROAD_REFERENCE_ART",
    os.path.join(os.path.expanduser("~"), "0ad_ref"))
REF_DEFAULT = os.path.join(REF_DIR, "meshes_skeletal_new_m_tunic_short.dae")

DEFAULT_TARGET_TRIS = 4500
ELF_SCALE = 1.05    # elf height = human ref height * this (~4.0 game units; tall slim elf)
WIDEN_ARMS = 1.0    # no bulk: keep stock Biped arm width (slim elf)
WIDEN_LEGS = 1.0    # no bulk: keep stock Biped leg width (slim elf)

# Meshes whose materials ALL match one of these substrings (case-insensitive)
# are weapon props -> excluded from the body join (sword stays a separate
# prop, rigged later). Leather armour is PART of the body and stays merged.
PROP_MAT_SUBSTR = ("sword", "blade", "weapon", "bow", "arrow", "quiver", "shield")
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
    # NOTE: cape1-3 deliberately excluded - no cape mesh on the elf;
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
    print("[elf-rig]", *a)


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


def import_elf(path):
    ext = os.path.splitext(path)[1].lower()
    log("importing elf", path)
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
        raise SystemExit("no meshes in elf download - check the file")
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
    # PARTITION: a separate sword prop stays OUT of the body join (separate
    # prop mesh later); leather armour is part of the body and stays merged.
    # Display-base discs stay out too.
    body, props = [], []
    for o in objs:
        if _is_weapon_prop(o):
            props.append((o, "weapon prop (separate prop later)"))
        elif _is_flat_base(o):
            props.append((o, "flat display base (not part of unit)"))
        else:
            body.append(o)
    if props:
        for o, why in props:
            log(f"EXCLUDE {o.name} [{_mesh_tris(o)} tris, "
                f"{len(o.data.vertices)} verts] - {why}")
    else:
        log("no separate sword/prop meshes - sword merged or absent, "
            "armour merged (expected for this single-mesh download)")
    if not body:
        raise SystemExit("all meshes excluded as props - nothing left for the body")
    log(f"body parts: {[o.name for o in body]}")
    bpy.ops.object.select_all(action="DESELECT")
    for o in body:
        o.select_set(True)
    bpy.context.view_layer.objects.active = body[0]
    bpy.ops.object.join()
    elf = bpy.context.view_layer.objects.active
    elf.name = "elf"
    # drop excluded prop meshes from the scene (props pass re-imports the GLB)
    for o, _why in props:
        bpy.data.objects.remove(o, do_unlink=True)
    return elf


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
    mat = bpy.data.materials.get("elf_body") or bpy.data.materials.new("elf_body")
    mat.use_nodes = True
    obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = True
        p.material_index = 0


def place_and_scale(obj, arm, ref_h, scale):
    # normalize elf rotation/scale, then size to ref_h * scale
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    h = max(obj.dimensions.z, 0.001)
    f = (ref_h * scale) / h
    log(f"elf height {h:.2f} -> x{f:.3f} = {ref_h * scale:.2f} game units")
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


ARM_CHAIN = ("arm", "forearm", "hand", "finger", "fingertip")

# Bones whose weights must not span onto torso/leg bones (and vice versa):
# the hanging hands rest against the thighs and the arms lie flush on the
# torso, so heat mixes hand<->thigh, finger<->leg, arm<->chest (measured:
# ~250 verts with cross secondaries >0.15, e.g. finger_L/thigh_L,
# chest/arm_L). In animations with big arm swings (capture) those
# torso/leg verts get dragged toward the arm. Snapping them to their top
# bone locks each region to one side. Shoulders/neck/head blends and
# leg-leg / torso-torso blends are legitimate (shoulder caps, inner
# thighs, waist bands) and are deliberately left alone.
DESPAN_BONES = frozenset({
    "arm_L", "arm_R", "forearm_L", "forearm_R",
    "hand_L", "hand_R", "finger_L", "finger_R",
    "fingertip_L", "fingertip_R",
})
DESPAN_SECOND_MIN = 0.01


# Rigid weapon/torso regions (sculpt-specific, measured from Atlas feedback):
# the merged back-sword is dominated by left fingers/forearm and the held
# blades spread across forearm/fingers, so arm swings bend them like rubber
# and drag the torso with them. Each region below locks to ONE bone. No
# finger articulation is lost: no elf anim keys fingers (walk/run lack
# them, melee locks them to rest, capture has none).
RIGID_TORSO_BONES = ("chest", "spine1", "spine", "hip")
RIGID_LEG_BONES = ("thigh_L", "thigh_R", "leg_L", "leg_R")


def _nearest_bone(arm, vert_co, names):
    best, bd = names[0], 1e9
    for n in names:
        b = arm.data.bones.get(n)
        if b is None:
            continue
        d = ((arm.matrix_world @ b.head_local) - vert_co).length
        if d < bd:
            best, bd = n, d
    return best


def rigid_regions(mesh, arm):
    """Lock merged-weapon + stolen-torso verts to single bones (see above)."""
    hl = arm.matrix_world @ arm.data.bones["hand_L"].head_local
    hr = arm.matrix_world @ arm.data.bones["hand_R"].head_local
    n = 0
    for v in mesh.data.vertices:
        gs = sorted(((mesh.vertex_groups[e.group].name, e.group, e.weight)
                     for e in v.groups), key=lambda t: -t[2])
        topn = gs[0][0]
        p = mesh.matrix_world @ v.co
        # back-sword blade box: everything here belongs on the chest,
        # including the tip riding the neck (it stretches the blade when
        # the neck flexes) and mid-blade stragglers on arm bones
        in_blade = (p[1] < -0.20 and p[2] > 2.8)
        if topn not in DESPAN_BONES and topn not in ("shoulder_L", "shoulder_R") \
                and not (in_blade and topn in ("neck", "head")):
            continue
        dl = (p - hl).length
        dr = (p - hr).length
        if in_blade:
            dest = "chest"
        elif min(dl, dr) < 0.30:
            # tight fist+grip radius: a wider one grabs the waist belt ring
            # (3 scabbard verts flew to z=5.1 in capture) and stiffens the
            # elbow with forearm tissue
            dest = "hand_L" if dl < dr else "hand_R"
        elif p[2] < 2.08 and p[1] > -0.15 and 0.0 < p[0] < 0.45:
            # held blades angling down-forward from the left fist
            dest = "hand_L"
        elif p[2] < 2.20 and p[1] < -0.15 and abs(p[0]) < 0.5:
            # waist belt / scabbard-mouth ring: hips, not hands (fingers are
            # all inside the 0.30 fist radius, so this box is belt-only)
            dest = "hip"
        elif p[1] < -0.30:
            dest = "chest"
        elif p[2] > 3.60:
            # back-sword tip pokes above the shoulder on a shoulder bone and
            # would swing with the arm verbatim (shoulders undampened) -
            # pin the behind-shoulder part to the chest, keep the front
            # shoulder cap articulated
            if topn in ("shoulder_L", "shoulder_R") and p[1] < -0.05:
                dest = "chest"
            else:
                continue
        elif abs(p[0]) < 0.35 and 2.0 < p[2] < 3.6:
            dest = _nearest_bone(arm, p, RIGID_TORSO_BONES)
        elif p[2] < 2.0:
            dest = _nearest_bone(arm, p, RIGID_LEG_BONES)
        else:
            continue  # limbs: genuine arm verts, leave alone
        if dest not in mesh.vertex_groups:
            continue
        for _name, gi, _w in gs:
            mesh.vertex_groups[gi].remove([v.index])
        mesh.vertex_groups[dest].add([v.index], 1.0, "REPLACE")
        n += 1
    log(f"rigid-locked {n} weapon/stolen-torso verts to single bones")


def despan_bleed(mesh):
    """Snap arm-vs-torso/leg weight spans to the top bone (see DESPAN_BONES).

    Heat's top choice is the anatomically nearer bone, so dropping the
    cross secondary removes the drag without moving the region.
    """
    snapped = 0
    for v in mesh.data.vertices:
        if len(v.groups) < 2:
            continue
        gs = sorted(((mesh.vertex_groups[e.group].name, e.group, e.weight)
                     for e in v.groups), key=lambda t: -t[2])
        (top_name, top_i, _top_w), (sec_name, _sec_i, sec_w) = gs[0], gs[1]
        if sec_w <= DESPAN_SECOND_MIN:
            continue
        if (top_name in DESPAN_BONES) == (sec_name in DESPAN_BONES):
            continue
        for _name, gi, _w in gs[1:]:
            mesh.vertex_groups[gi].remove([v.index])
        mesh.vertex_groups[top_i].add([v.index], 1.0, "REPLACE")
        snapped += 1
    log(f"despanned {snapped} arm/torso bleed verts to single bone")


def drop_arm_chains(arm):
    """Rotate arm chains from A-pose to hang inside the mesh arms.

    This source stands with arms hanging at its sides, not spread: stock
    A-pose arm bones float 0.3-0.7 outside the mesh, heat weights collapse
    onto chest/thigh (max arm weight 0.13, hands ~0), and the arms can't
    bend. Rigid-rotating each chain about its arm-bone head keeps relative
    joint poses - only the rest pose changes to arms-down. Retargeted stock
    anims are rest-relative, so walk/run/melee still play correctly from
    the hanging base (verified: bone-to-mesh distance post-fit).
    Shoulder bones stay untouched (tails already sit ~0.1 from the mesh).
    """
    from mathutils import Vector
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    for side, s in (("L", 1.0), ("R", -1.0)):
        pivot_b = arm.data.edit_bones.get(f"arm_{side}")
        if pivot_b is None:
            continue
        cur = (pivot_b.tail - pivot_b.head)
        if cur.length < 1e-6:
            continue
        tgt = Vector((0.10 * s, 0.02, -1.0))
        rot = cur.normalized().rotation_difference(tgt.normalized()).to_matrix()
        pivot = pivot_b.head.copy()
        for name in ARM_CHAIN:
            b = arm.data.edit_bones.get(f"{name}_{side}")
            if b is None:
                continue
            b.head = pivot + rot @ (b.head - pivot)
            b.tail = pivot + rot @ (b.tail - pivot)
    bpy.ops.object.mode_set(mode="OBJECT")
    log("dropped arm chains to hanging rest pose")


def skin_and_export(elf, arm):
    # parent mesh -> armature with automatic weights (heat)
    bpy.ops.object.select_all(action="DESELECT")
    elf.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    log("skinned with automatic weights")
    log("vertex groups:", len(elf.vertex_groups))
    bad = sorted(g.name for g in elf.vertex_groups if g.name not in DEFORM_BONES)
    if bad:
        log("WARNING: weights on non-deform bones:", bad)
        for name in bad:
            elf.vertex_groups.remove(elf.vertex_groups[name])
        log("removed non-deform groups")
    # per-vertex sanity: strongest group must be a nearby deform bone;
    # report the distribution so spikes get caught here, not in Atlas
    from collections import Counter
    top = Counter()
    for v in elf.data.vertices:
        if v.groups:
            g = max(v.groups, key=lambda e: e.weight)
            top[elf.vertex_groups[g.group].name] += 1
    log("dominant-group histogram:", dict(sorted(top.items())))
    # soften weight boundaries (waist/hip pinch from heat + mirror decimate):
    # smooth all deform groups so chest<->hip<->thigh transitions are gradual
    bpy.ops.object.select_all(action="DESELECT")
    elf.select_set(True)
    bpy.context.view_layer.objects.active = elf
    bpy.ops.object.mode_set(mode="WEIGHT_PAINT")
    bpy.ops.object.vertex_group_smooth(group_select_mode="ALL", factor=0.5, repeat=4)
    bpy.ops.object.mode_set(mode="OBJECT")
    log("smoothed deform weights")
    despan_bleed(elf)
    rigid_regions(elf, arm)
    # texture: LARGEST source image -> 512px baseTex (body albedo, not pants)
    out_png = os.path.join(MOD, "art", "textures", "skins", "skeletal", "tolkien", "elf_body.png")
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
    out_dae = os.path.join(MOD, "art", "meshes", "skeletal", "tolkien", "elf.dae")
    os.makedirs(os.path.dirname(out_dae), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    elf.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.wm.collada_export(filepath=out_dae, selected=True,
                               include_animations=False)
    log("EXPORTED", out_dae)
    with open(os.path.join(os.path.dirname(out_dae), "elf_CREDITS.txt"), "w", encoding="utf-8") as f:
        f.write("Derivative of 'Realistic 3D fantasy male elf warrior' by "
                "zaini.AI, CC-BY 4.0.\n"
                "Source: https://sketchfab.com/3d-models/realistic-3d-fantasy-male-elf-warrior-b40d56a51c574a6e8e09e001d3e7530f\n"
                "Changes: single-mesh source decimated ~10k -> ~4.5k tris "
                "(separate sword prop excluded if present, leather armour kept "
                "merged), rigged to stock 0 A.D. Biped "
                "(art/skeletons/biped.xml), rescaled ~1.05x human "
                "(tall slim elf), 512px baseTex.\n"
                "Custom tall idle + walk + run (biped/elf_*.dae); melee/capture retargeted stock.\n")
    # sanity: verts under engine hard limit, armature present
    me = elf.data
    log(f"DONE verts={len(me.vertices)} (limit 32768), bones={len(arm.data.bones)}")
    missing = [b for b in ("hip", "chest", "head", "hand_R", "foot_L") if b not in arm.data.bones]
    if missing:
        log("WARNING missing biped bones:", missing)


IDLE_FRAMES = (1, 16, 32)

# Torso dampening for retargets: quaternion angle scale per bone. Limbs copy
# verbatim (1.0); spine/chest/head shrink toward rest so the human hunch
# doesn't crumple the slim elf torso. Hip location deltas scale up x1.05 below.
DAMP_BASE = {"spine": 0.4, "spine1": 0.4, "chest": 0.45,
             "neck": 0.6, "head": 0.5}
# Melee adds: fists locked to the natural rest curl (the stock grip-release
# splays slender elf fingers into a wave), wrists calmed (stock sword-roll
# corkscrews the slim forearms). Arms keep full swing.
DAMP_MELEE = {**DAMP_BASE,
              "hand_L": 0.45, "hand_R": 0.45,
              "finger_L": 0.0, "finger_R": 0.0,
              "fingertip_L": 0.0, "fingertip_R": 0.0}
LOC_SCALE = 1.05

STOCK_DIR = os.path.join(REF_DIR, "stock_anim")

# (stock file, elf anim name, damp profile). Times copy verbatim -> stock
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


def author_idle(elf, arm):
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
    act = bpy.data.actions.new("elf_idle")
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


def export_idle(elf, arm):
    out_anim = os.path.join(MOD, "art", "animation", "biped", "elf_idle.dae")
    os.makedirs(os.path.dirname(out_anim), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    elf.select_set(True)
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


def retarget_stock(elf, arm, stock_name, out_name, damp):
    """Copy a stock Biped animation onto the elf with torso dampening.

    Same bone names + same hierarchy, so rotation curves transfer 1:1 on
    limbs; spine/chest/head angles shrink (DAMP_TORSO) so the human hunch
    doesn't crumple the slim elf; hip location deltas scale up (LOC_SCALE)
    to elf size. Key TIMES copy verbatim -> stock variant speeds stay valid.
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
    new_act = bpy.data.actions.new("elf_" + out_name)
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
    out = os.path.join(MOD, "art", "animation", "biped", f"elf_{out_name}.dae")
    bpy.ops.object.select_all(action="DESELECT")
    elf.select_set(True)
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
    # idle ~3s loop, walk ~1.2s stride, run ~0.65s stride.
    var_dir = os.path.join(MOD, "art", "variants", "biped")
    os.makedirs(var_dir, exist_ok=True)
    with open(os.path.join(var_dir, "elf_relax.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<variant name="Base" frequency="1">\n'
                '  <animations>\n'
                '    <animation file="biped/elf_idle.dae" name="idle" id="idle1" speed="35"/>\n'
                '    <animation file="biped/elf_idle.dae" name="idle" id="idle2" speed="32"/>\n'
                f'    <animation file="{walk_file}" name="Walk" id="walk1" speed="30"/>\n'
                f'    <animation file="{walk_file}" name="Walk" id="walk2" speed="29"/>\n'
                f'    <animation file="{walk_file}" name="Walk" id="walk3" speed="28"/>\n'
                f'    <animation file="{run_file}" name="Run" id="run1" speed="8"/>\n'
                f'    <animation file="{run_file}" name="Run" id="run2" speed="9"/>\n'
                f'    <animation file="{run_file}" name="Run" id="run3" speed="10"/>\n'
                '    <animation event="0.5" file="biped/elf_melee1.dae" name="attack_melee" id="attack1" speed="100"/>\n'
                '    <animation event="0.5" file="biped/elf_melee2.dae" name="attack_melee" id="attack2" speed="100"/>\n'
                '    <animation event="0.5" file="biped/elf_melee1.dae" name="attack_melee" id="attack3" speed="100"/>\n'
                '    <animation file="biped/infantry/promotion.dae" name="promotion" speed="80"/>\n'
                '  </animations>\n'
                '</variant>\n')
    log(f"wrote variant biped/elf_relax.xml (walk={walk_file} run={run_file})")
    with open(os.path.join(var_dir, "elf_capture.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<variant name="attack_capture">\n'
                '  <animations>\n'
                '    <animation file="biped/elf_capture.dae" name="attack_capture" speed="100"/>\n'
                '  </animations>\n'
                '</variant>\n')
    log("wrote variant biped/elf_capture.xml")


def main():
    argv = sys.argv
    args = argv[argv.index("--") + 1:] if "--" in argv else []
    if not args:
        print("Usage: blender --background --python build_elf_rig.py -- <elf.gltf|glb|fbx|obj> [target_tris] [scale] [ref_dae]")
        raise SystemExit(2)
    src = args[0]
    target = int(args[1]) if len(args) > 1 else DEFAULT_TARGET_TRIS
    scale = float(args[2]) if len(args) > 2 else ELF_SCALE
    ref = args[3] if len(args) > 3 else REF_DEFAULT
    if not os.path.isfile(src):
        raise SystemExit(f"input not found: {src}")
    clear()
    arm, ref_h = import_ref_armature(ref)
    elf = import_elf(src)
    cleanup_decimate(elf, target)
    place_and_scale(elf, arm, ref_h, scale)
    restrict_deform_bones(arm)
    widen_bones(arm)
    drop_arm_chains(arm)
    skin_and_export(elf, arm)
    author_idle(elf, arm)
    export_idle(elf, arm)
    for stock_name, out_name, damp in RETARGET_JOBS:
        retarget_stock(elf, arm, stock_name, out_name, damp)
    write_variant("biped/elf_walk.dae", "biped/elf_run.dae")
    log("NEXT: test in 0 A.D. (mod selection -> Tolkien), check interestinglog.html for errors.")


if __name__ == "__main__":
    main()
