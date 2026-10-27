"""
Rig the Sketchfab Sauron to 0 A.D.'s BIPED skeleton (run inside Blender 3.0).

Clone of build_troll_rig.py for an ARMORED HUMANOID hero. Deltas vs troll:
  - part selection: the GLB carries a duplicate body (same bounds, no UVs)
    plus a far-flung stray boot (~200 units out). Keep the UV'd body + mace,
    drop the rest by bounds rules (see import_sauron).
  - NO source textures at all (flat PBR materials only) -> Smart-UV the
    joined mesh and DIFFUSE-bake material colors to a single 512px baseTex.
  - hero scale 1.35x human (~5.2 game units), modest plate widening.
  - mace merged into the mesh (rides the hand via heat weights).

Source (NOT bundled - download manually):
  Sauron by rokaarh, CC BY 4.0
  https://sketchfab.com/3d-models/sauron-5ad2aea041a141d6b3640715a7a54659

USAGE:
  "C:\\Program Files\\Blender Foundation\\Blender 3.0\\blender.exe" ^
    --background --python tools\\art_build\\build_sauron_rig.py -- ^
    C:\\Users\\<you>\\Downloads\\sauron.glb [target_tris] [scale]
Output: tolkien\\art\\meshes\\skeletal\\tolkien\\sauron.dae (rigged),
  sauron_body.png, sauron_CREDITS.txt, biped/sauron_*.dae anims + variants.
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
SAURON_SCALE = 1.35   # Dark Lord presence: ref height * this (~5.2 game units)
WIDEN_ARMS = 1.15     # plate bulk, modest (troll needed 1.45)
WIDEN_LEGS = 1.05

DEFORM_BONES = frozenset({
    "hip", "spine", "spine1", "chest", "neck", "head",
    "shoulder_L", "shoulder_R",
    "arm_L", "arm_R", "forearm_L", "forearm_R",
    "hand_L", "hand_R", "finger_L", "finger_R",
    "fingertip_L", "fingertip_R",
    "thigh_L", "thigh_R", "leg_L", "leg_R", "foot_L", "foot_R",
})

ARM_BONES = ("shoulder_L", "shoulder_R", "arm_L", "arm_R",
             "forearm_L", "forearm_R", "hand_L", "hand_R",
             "finger_L", "finger_R", "fingertip_L", "fingertip_R")
LEG_BONES = ("thigh_L", "thigh_R", "leg_L", "leg_R", "foot_L", "foot_R")


def log(*a):
    print("[sauron-rig]", *a)


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_ref_armature(ref_path):
    if not os.path.isfile(ref_path):
        raise SystemExit("reference body not found: " + ref_path)
    log("importing reference", ref_path)
    before = set(bpy.data.objects)
    bpy.ops.wm.collada_import(filepath=ref_path)
    new_objs = [o for o in bpy.data.objects if o not in before]
    arm = next((o for o in new_objs if o.type == "ARMATURE"), None)
    meshes = [o for o in new_objs if o.type == "MESH"]
    if arm is None:
        raise SystemExit("no armature in reference .dae - wrong file?")
    ref_h = max((m.dimensions.z for m in meshes), default=3.85)
    log("armature:", arm.name, "ref height:", round(ref_h, 2))
    for m in meshes:
        bpy.data.objects.remove(m, do_unlink=True)
    return arm, float(ref_h)


def mesh_bounds(o):
    bpy.context.view_layer.update()
    xs = [v.co.x for v in o.data.vertices]
    ys = [v.co.y for v in o.data.vertices]
    zs = [v.co.z for v in o.data.vertices]
    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


def import_sauron(path):
    log("importing sauron", path)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path, merge_vertices=True)
    objs = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    if not objs:
        raise SystemExit("no meshes in sauron download - check the file")
    # BAKE ASSEMBLY TRANSFORMS FIRST (troll §5 pitfall: join() merges raw
    # local coords and scrambles multi-part scenes otherwise).
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
    # PART SELECTION. Measured layout: main body (~8k verts, has UVs) plus an
    # identical-bounds duplicate WITHOUT UVs, a far-flung stray boot (46 verts,
    # ~200 units out), and the mace overlapping the body region. Rules:
    #   1. main = largest mesh WITH a UV layer;
    #   2. drop parts whose bbox is a near-duplicate of an already-kept part;
    #   3. drop parts not intersecting the main bbox expanded by 25%.
    scored = []
    for o in objs:
        has_uv = len(o.data.uv_layers) > 0
        scored.append((len(o.data.vertices), has_uv, o))
    scored.sort(reverse=True)
    main = next((o for _, uv, o in scored if uv), scored[0][2])
    mb = mesh_bounds(main)
    log("main part:", main.name, "uvs:", len(main.data.uv_layers))
    ex = 0.25
    keep = [main]
    for _, _, o in scored:
        if o is main:
            continue
        b = mesh_bounds(o)
        dup = all(abs(a - c) < 1.0 for a, c in zip(b, mb))
        inside = not (b[1] < mb[0] - ex * (mb[1] - mb[0]) or b[0] > mb[1] + ex * (mb[1] - mb[0])
                      or b[3] < mb[2] - ex * (mb[3] - mb[2]) or b[2] > mb[3] + ex * (mb[3] - mb[2])
                      or b[5] < mb[4] - ex * (mb[5] - mb[4]) or b[4] > mb[5] + ex * (mb[5] - mb[4]))
        if dup:
            log("dropping duplicate-bounds part:", o.name)
            bpy.data.objects.remove(o, do_unlink=True)
        elif not inside:
            log("dropping far stray part:", o.name)
            bpy.data.objects.remove(o, do_unlink=True)
        else:
            log("keeping part:", o.name)
            keep.append(o)
    bpy.ops.object.select_all(action="DESELECT")
    for o in keep:
        o.select_set(True)
    bpy.context.view_layer.objects.active = keep[0]
    bpy.ops.object.join()
    sauron = bpy.context.view_layer.objects.active
    sauron.name = "sauron"
    return sauron


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
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.quads_convert_to_tris(quad_method="BEAUTY", ngon_method="BEAUTY")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    # Fresh Smart-UV layout: parts arrive with unrelated UV spaces (and the
    # flat PBR colors bake per-face next), so overlaps would cross-talk.
    while len(obj.data.uv_layers):
        obj.data.uv_layers.remove(obj.data.uv_layers[0])
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=66, island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")
    log("smart-UV done:", len(obj.data.uv_layers), "layer(s)")


def bake_diffuse(obj):
    """DIFFUSE-color bake of the flat PBR materials into one 512px baseTex."""
    out_png = os.path.join(MOD, "art", "textures", "skins", "skeletal", "tolkien", "sauron_body.png")
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    img = bpy.data.images.new("sauron_bake", 512, 512)
    mat = bpy.data.materials.get("sauron_body") or bpy.data.materials.new("sauron_body")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    texnode = nt.nodes.new("ShaderNodeTexImage")
    texnode.image = img
    nt.nodes.active = texnode
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = True
        p.material_index = 0
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    try:
        sc.cycles.device = "CPU"
    except Exception:
        pass
    sc.cycles.bake_type = "DIFFUSE"
    sc.render.bake.use_pass_direct = False
    sc.render.bake.use_pass_indirect = False
    sc.render.bake.use_pass_color = True
    sc.render.bake.margin = 16
    sc.render.bake.use_clear = True
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.bake()
    img.filepath_raw = out_png
    img.file_format = "PNG"
    img.save()
    log("baked", out_png)
    # Re-link the baked image as the albedo the exporter writes out.
    nt.links.new(texnode.outputs["Color"], bsdf.inputs["Base Color"])


def place_and_scale(obj, arm, ref_h, scale):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    h = max(obj.dimensions.z, 0.001)
    f = (ref_h * scale) / h
    log(f"sauron height {h:.2f} -> x{f:.3f} = {ref_h * scale:.2f} game units")
    obj.scale = (f, f, f)
    bpy.context.view_layer.update()
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
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
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    arm.scale = (scale, scale, scale)
    bpy.context.view_layer.update()
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    log("armature scaled x", scale)


def restrict_deform_bones(arm):
    kept, dropped = 0, 0
    for b in arm.data.bones:
        if b.name in DEFORM_BONES:
            b.use_deform = True
            kept += 1
        else:
            b.use_deform = False
            dropped += 1
    log(f"deform bones: {kept} kept, {dropped} markers disabled")


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


def skin_and_export(sauron, arm, license_note):
    bpy.ops.object.select_all(action="DESELECT")
    sauron.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    log("skinned with automatic weights")
    log("vertex groups:", len(sauron.vertex_groups))
    bad = sorted(g.name for g in sauron.vertex_groups if g.name not in DEFORM_BONES)
    if bad:
        log("WARNING: weights on non-deform bones:", bad)
        for name in bad:
            sauron.vertex_groups.remove(sauron.vertex_groups[name])
        log("removed non-deform groups")
    from collections import Counter
    top = Counter()
    for v in sauron.data.vertices:
        if v.groups:
            g = max(v.groups, key=lambda e: e.weight)
            top[sauron.vertex_groups[g.group].name] += 1
    log("dominant-group histogram:", dict(sorted(top.items())))
    bpy.ops.object.select_all(action="DESELECT")
    sauron.select_set(True)
    bpy.context.view_layer.objects.active = sauron
    bpy.ops.object.mode_set(mode="WEIGHT_PAINT")
    bpy.ops.object.vertex_group_smooth(group_select_mode="ALL", factor=0.5, repeat=4)
    bpy.ops.object.mode_set(mode="OBJECT")
    log("smoothed deform weights")
    out_dae = os.path.join(MOD, "art", "meshes", "skeletal", "tolkien", "sauron.dae")
    os.makedirs(os.path.dirname(out_dae), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    sauron.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.wm.collada_export(filepath=out_dae, selected=True,
                              include_animations=False)
    log("EXPORTED", out_dae)
    with open(os.path.join(os.path.dirname(out_dae), "sauron_CREDITS.txt"), "w", encoding="utf-8") as f:
        f.write("Derivative of 'Sauron' by rokaarh, " + license_note + ".\n"
                "Source: https://sketchfab.com/3d-models/sauron-5ad2aea041a141d6b3640715a7a54659\n"
                "Changes: dropped duplicate body + stray parts, decimated to ~5.5k tris,\n"
                "rigged to stock 0 A.D. Biped (art/skeletons/biped.xml), rescaled ~1.35x human,\n"
                "flat PBR colors baked to a single 512px baseTex, mace merged.\n"
                "Custom idle + walk + run (biped/sauron_*.dae); melee/capture/death stock-based.\n")
    me = sauron.data
    log(f"DONE verts={len(me.vertices)} (limit 32768), bones={len(arm.data.bones)}")
    missing = [b for b in ("hip", "chest", "head", "hand_R", "foot_L") if b not in arm.data.bones]
    if missing:
        log("WARNING missing biped bones:", missing)


IDLE_FRAMES = (1, 16, 32)
DAMP_BASE = {"spine": 0.4, "spine1": 0.4, "chest": 0.45,
             "neck": 0.6, "head": 0.5}
DAMP_MELEE = {**DAMP_BASE,
              "hand_L": 0.45, "hand_R": 0.45,
              "finger_L": 0.0, "finger_R": 0.0,
              "fingertip_L": 0.0, "fingertip_R": 0.0}
LOC_SCALE = 1.35

STOCK_DIR = os.path.join(REF_DIR, "stock_anim")

RETARGET_JOBS = [
    ("walk_relax.dae", "walk", DAMP_BASE),
    ("run_relax_2h.dae", "run", DAMP_BASE),
    ("attack_melee_2h_01.dae", "melee1", DAMP_MELEE),
    ("attack_melee_2h_02.dae", "melee2", DAMP_MELEE),
    ("capturing_a.dae", "capture", DAMP_BASE),
]


def _key_q(pb, axis, angle, frame):
    import math as _m
    pb.rotation_mode = "QUATERNION"
    q = [1.0, 0.0, 0.0, 0.0]
    q[axis + 1] = _m.sin(angle / 2.0)
    q[0] = _m.cos(angle / 2.0)
    pb.rotation_quaternion = q
    pb.keyframe_insert(data_path="rotation_quaternion", frame=frame)


def author_idle(sauron, arm):
    """Heavy menacing idle: tall rest, slow mace-side sway (quats, ~2 deg)."""
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
    act = bpy.data.actions.new("sauron_idle")
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
    log("authored menacing idle (32f loop, quats)")


def export_idle(sauron, arm):
    out_anim = os.path.join(MOD, "art", "animation", "biped", "sauron_idle.dae")
    os.makedirs(os.path.dirname(out_anim), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    sauron.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.wm.collada_export(filepath=out_anim, selected=True,
                              include_animations=True)
    log("EXPORTED idle", out_anim)


def damp_quat(q, k):
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


def retarget_stock(sauron, arm, stock_name, out_name, damp):
    import re
    src = os.path.join(STOCK_DIR, stock_name)
    if not os.path.isfile(src):
        raise SystemExit("stock anim missing: " + src)
    objs_before = set(bpy.data.objects)
    acts_before = set(bpy.data.actions)
    bpy.ops.wm.collada_import(filepath=src)
    new_objs = [o for o in bpy.data.objects if o not in objs_before]
    sarm = next((o for o in new_objs if o.type == "ARMATURE"), None)
    new_acts = [a for a in bpy.data.actions if a not in acts_before]
    if sarm is None or not new_acts:
        raise SystemExit("no armature/action in " + stock_name)
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
    new_act = bpy.data.actions.new("sauron_" + out_name)
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
    out = os.path.join(MOD, "art", "animation", "biped", f"sauron_{out_name}.dae")
    bpy.ops.object.select_all(action="DESELECT")
    sauron.select_set(True)
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


def write_variant():
    # Retargets keep stock key times verbatim (~1.1 s walk/run, 0.83 s melee):
    # hero cadence — walk purposeful, run a dread charge, melee full speed.
    var_dir = os.path.join(MOD, "art", "variants", "biped")
    os.makedirs(var_dir, exist_ok=True)
    with open(os.path.join(var_dir, "sauron_relax.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<variant name="Base" frequency="1">\n'
                '  <animations>\n'
                '    <animation file="biped/sauron_idle.dae" name="idle" id="idle1" speed="35"/>\n'
                '    <animation file="biped/sauron_idle.dae" name="idle" id="idle2" speed="32"/>\n'
                '    <animation file="biped/sauron_walk.dae" name="Walk" id="walk1" speed="90"/>\n'
                '    <animation file="biped/sauron_walk.dae" name="Walk" id="walk2" speed="85"/>\n'
                '    <animation file="biped/sauron_run.dae" name="Run" id="run1" speed="100"/>\n'
                '    <animation file="biped/sauron_run.dae" name="Run" id="run2" speed="105"/>\n'
                '    <animation event="0.5" file="biped/sauron_melee1.dae" name="attack_melee" id="attack1" speed="100"/>\n'
                '    <animation event="0.5" file="biped/sauron_melee2.dae" name="attack_melee" id="attack2" speed="100"/>\n'
                '    <animation event="0.5" file="biped/sauron_melee1.dae" name="attack_melee" id="attack3" speed="100"/>\n'
                '    <animation file="biped/infantry/promotion.dae" name="promotion" speed="80"/>\n'
                '  </animations>\n'
                '</variant>\n')
    log("wrote variant biped/sauron_relax.xml")
    with open(os.path.join(var_dir, "sauron_capture.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<variant name="attack_capture">\n'
                '  <animations>\n'
                '    <animation file="biped/sauron_capture.dae" name="attack_capture" speed="100"/>\n'
                '  </animations>\n'
                '</variant>\n')
    log("wrote variant biped/sauron_capture.xml")


def main():
    argv = sys.argv
    args = argv[argv.index("--") + 1:] if "--" in argv else []
    if not args:
        print("Usage: blender --background --python build_sauron_rig.py -- <sauron.glb> [target_tris] [scale]")
        raise SystemExit(2)
    src = args[0]
    target = int(args[1]) if len(args) > 1 else DEFAULT_TARGET_TRIS
    scale = float(args[2]) if len(args) > 2 else SAURON_SCALE
    if not os.path.isfile(src):
        raise SystemExit("input not found: " + src)
    clear()
    arm, ref_h = import_ref_armature(REF_DEFAULT)
    sauron = import_sauron(src)
    cleanup_decimate(sauron, target)
    bake_diffuse(sauron)
    place_and_scale(sauron, arm, ref_h, scale)
    restrict_deform_bones(arm)
    widen_bones(arm)
    skin_and_export(sauron, arm, "CC BY 4.0")
    author_idle(sauron, arm)
    export_idle(sauron, arm)
    for stock_name, out_name, damp in RETARGET_JOBS:
        retarget_stock(sauron, arm, stock_name, out_name, damp)
    write_variant()
    log("NEXT: actor XML + template wiring + Atlas action tests.")


if __name__ == "__main__":
    main()
