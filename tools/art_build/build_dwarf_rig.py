"""
Rig the Sketchfab Moria Battle Dwarf to 0 A.D.'s BIPED skeleton (run inside Blender 3.0).

Cloned from build_troll_rig.py (do not edit that file) - same pipeline, dwarf
parameters. See docs/sketchfab-to-0ad.md for the full pipeline.

Why Biped:
  - Dwarf is humanoid (2 arms / 2 legs / head). Biped
    (art/skeletons/biped.xml) already ships walk/run/melee/capture/death in
    art/variants/biped/. Same bone names = stock animations retarget by
    name, no skeleton.xml needed.
  - No new skeleton.xml needed. Mesh .dae carries a Biped armature and the
    engine maps it via the stock biped.xml.

Source (NOT bundled - download manually, CC-BY 4.0 by The Kala Ce (@harishrbat987)):
  https://sketchfab.com/3d-models/3d-model-of-dwarf-6a8f36db7c7a4cecb75c6634052ec598

USAGE:
  1. Download model from Sketchfab (GLB) to e.g. C:\\Users\\<you>\\Downloads\\3d_model_of_dwarf.glb
  2. Reference body must exist (already in repo temp):
       %TEMP%\\0ad_ref\\meshes_skeletal_new_m_tunic_short.dae
     (contains the stock Biped armature + m_tunic_short mesh)
  3. "C:\\Program Files\\Blender Foundation\\Blender 3.0\\blender.exe" ^
       --background --python tools\\art_build\\build_dwarf_rig.py -- ^
       C:\\Users\\<you>\\Downloads\\3d_model_of_dwarf.glb 4500 0.8
  4. Output: tolkien\\art\\meshes\\skeletal\\tolkien\\dwarf.dae (RIGGED mesh +
     Biped armature), dwarf_body.png, dwarf_CREDITS.txt,
     biped/dwarf_*.dae + biped/dwarf_relax.xml + dwarf_capture.xml

What the script does:
  - imports reference -> keeps Biped armature, deletes ref mesh
  - imports dwarf -> strips display-stand disc + held weapons (armour KEPT),
    join, cleanup, ITERATIVE decimate to ~4500 tris (a single COLLAPSE pass
    clamps at ratio 0.05 -> only ~23k from a 473k source), single mat/UV
  - scales dwarf to ref_height * DWARF_SCALE (~3.1 game units; short and wide
    reads dwarvish next to 3.85-unit humans;
    game units: human body ~= 3.85, see docs/art-unit-template.md section 3)
  - scales armature to match, widens arm/leg bones for dwarven bulk
    (arms x1.25, legs x1.20 - edit-mode heuristic, tweak WIDEN_* below)
  - parents mesh with AUTOMATIC WEIGHTS (heat), exports selected mesh+armature
    as Collada .dae readable by Pyrogenesis/collada2pmd
  - authors a sturdy breathing idle, retargets stock walk/run/2x melee/capture
    with torso dampening, writes relax + capture variants

Manual touch-up (expected for v1 -> v2):
  - open dwarf.dae in Blender, Weight Paint mode, fix armpit/groin bleed
  - beard/braid verts may need re-weighting to chest/neck (heat can grab head)
  - if fists clip on walk, widen shoulder_L/R + arm_L/R edit bones further
  - weapons come from 0 A.D. props (attach to weapon_R like orc_sword)

Credit (REQUIRED by CC-BY): derivative of "3D model of dwarf" by The Kala Ce
(@harishrbat987), CC-BY 4.0.
"""
import bpy
import bmesh
import math
import os
import sys

MOD = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tolkien"))
REF_DIR = os.environ.get(
    "ZEROAD_REFERENCE_ART",
    os.path.join(os.path.expanduser("~"), "0ad_ref"))
REF_DEFAULT = os.path.join(REF_DIR, "meshes_skeletal_new_m_tunic_short.dae")

DEFAULT_TARGET_TRIS = 4500
DWARF_SCALE = 0.8    # dwarf height = human ref height * this (~3.1 game units)
WIDEN_ARMS = 1.25    # edit-bone X multiplier for shoulder/arm/forearm/hand
WIDEN_LEGS = 1.2     # edit-bone X multiplier for thigh/leg/foot

# (source tris, final tris) of the last cleanup_decimate - used for credits.
LAST_DECIMATE = (0, 0)

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
    # NOTE: cape1-3 deliberately excluded - no cape mesh on the dwarf;
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
    print("[dwarf-rig]", *a)


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


# Texture-atlas globals, filled by pack_atlas_uvs() during import.
ATLAS_SIZE = 2048   # single texture for the merged mesh (<=2048 per §4)
ATLAS_GRID = 0      # grid is ATLAS_GRID x ATLAS_GRID cells
ATLAS_CELLS = {}    # base-color image name -> cell index
ATLAS_GRAY = 0      # cell index of the flat-gray fallback (imageless parts)
ATLAS_SKIN = 0      # cell index of flat skin tone (bare hands, see below)
ATLAS_SKIN_IMG = None   # face albedo (material Glava_LP): skin-tone donor
ATLAS_GLOVE_IMG = None  # glove albedo (material Gloves): sleeves keep it


def part_base_image(obj):
    """Base-Color-linked image of an object's first material (or None)."""
    if not len(obj.data.materials):
        return None
    mat = obj.data.materials[0]
    if mat is None or not mat.use_nodes:
        return None
    for link in mat.node_tree.links:
        if (link.to_node.type == "BSDF_PRINCIPLED"
                and link.to_socket.name == "Base Color"
                and link.from_node.type == "TEX_IMAGE"
                and link.from_node.image is not None):
            return link.from_node.image.name
    return None


def pack_atlas_uvs(objs):
    """Remap each part's UVs into its own atlas cell (called post-bake).

    Merging 21 parts into one material means one texture: baking the
    largest single map (as v1 did) paints the whole dwarf with one part's
    colors (v1 shipped the helmet's gray steel everywhere). Instead, tile
    every part's base-color map into a 2048px atlas and shrink/shift UVs
    into the matching cell. Parts with no base-color map share one
    flat-gray cell. join() + decimate both preserve per-loop UVs.

    Runs AFTER assembly transforms are baked so the glove split below
    can use final world coords. The glove mesh spans full forearm
    sleeves AND hands: sleeve faces keep the leather cell, hand faces
    (|x| beyond HAND_X) go to a flat skin-tone cell (requester asked
    for bare hands; sleeves stay source-authentic leather).
    """
    global ATLAS_GRID, ATLAS_CELLS, ATLAS_GRAY, ATLAS_SKIN
    global ATLAS_SKIN_IMG, ATLAS_GLOVE_IMG
    HAND_X = 0.7
    by_part = {o.name: part_base_image(o) for o in objs}
    for o in objs:
        if not len(o.data.materials):
            continue
        mname = o.data.materials[0].name if o.data.materials[0] else ""
        if mname == "Glava_LP":
            ATLAS_SKIN_IMG = by_part[o.name]
        elif mname == "Gloves":
            ATLAS_GLOVE_IMG = by_part[o.name]
    unique = sorted(set(v for v in by_part.values() if v is not None))
    ATLAS_CELLS = {img: i for i, img in enumerate(unique)}
    ATLAS_GRAY = len(unique)
    ATLAS_SKIN = len(unique) + 1
    ATLAS_GRID = int(math.ceil(math.sqrt(len(unique) + 2)))
    log(f"atlas: {len(objs)} parts, {len(unique)} base-color maps, "
        f"{ATLAS_GRID}x{ATLAS_GRID} grid (gray {ATLAS_GRAY}, skin {ATLAS_SKIN})")
    gray_parts = sorted(n for n, v in by_part.items() if v is None)
    if gray_parts:
        log(f"atlas: imageless parts -> gray cell: {gray_parts}")
    g = ATLAS_GRID
    for o in objs:
        img = by_part[o.name]
        if not o.data.uv_layers:
            bpy.ops.object.select_all(action="DESELECT")
            o.select_set(True)
            bpy.context.view_layer.objects.active = o
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.uv.cube_project(cube_size=1.0)
            bpy.ops.object.mode_set(mode="OBJECT")
        uvl = o.data.uv_layers[0]
        split = (img == ATLAS_GLOVE_IMG and ATLAS_GLOVE_IMG is not None)
        hand_faces = 0
        if not split:
            idx = ATLAS_CELLS[img] if img is not None else ATLAS_GRAY
            ox, oy = (idx % g) / g, (idx // g) / g
            for loop in uvl.data:
                u, v = loop.uv
                loop.uv = (u / g + ox, v / g + oy)
        else:
            # per-face: hands -> flat skin cell, sleeves -> leather cell
            me = o.data
            for poly in me.polygons:
                cx = sum(me.vertices[i].co.x for i in poly.vertices)
                cx /= len(poly.vertices)
                idx = (ATLAS_SKIN if abs(cx) > HAND_X
                       else ATLAS_CELLS[img])
                if idx == ATLAS_SKIN:
                    hand_faces += 1
                ox, oy = (idx % g) / g, (idx // g) / g
                for li in poly.loop_indices:
                    u, v = uvl.data[li].uv
                    uvl.data[li].uv = (u / g + ox, v / g + oy)
            log(f"atlas: glove split: {hand_faces}/{len(me.polygons)} faces -> skin")


def import_dwarf(path):
    ext = os.path.splitext(path)[1].lower()
    log("importing dwarf", path)
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
        raise SystemExit("no meshes in dwarf download - check the file")
    # STRIP NON-DWARF PARTS: display-stand discs (Plane*) and any held
    # weapons by name keyword. Armour is KEPT - it sells dwarvish at game distance.
    # (This source: 22 meshes all map to body/armour/beard/braid/belt/boots/
    # gloves/helmet materials, so only the Chainmail-textured Plane stand
    # goes; the keyword guard stays for re-runs on other downloads.)
    WEAPON_KEYS = ("sword", "axe", "blade", "dagger", "hammer", "mace",
                   "spear", "bow", "arrow", "knife", "club", "staff",
                   "weapon")
    strip = [o for o in objs
             if o.name.startswith("Plane")
             or any(k in o.name.lower() for k in WEAPON_KEYS)]
    for o in strip:
        log("stripping non-dwarf part:", o.name)
        bpy.data.objects.remove(o, do_unlink=True)
    objs = [o for o in objs if o not in strip]
    if not objs:
        raise SystemExit("all meshes stripped - check the weapon filter")
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
    # UV atlas AFTER baking: the glove hand/sleeve split needs final coords
    pack_atlas_uvs(objs)
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
    dwarf = bpy.context.view_layer.objects.active
    dwarf.name = "dwarf"
    return dwarf


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
    src_tris = tris
    # ITERATIVE decimate: a single COLLAPSE pass clamps at ratio 0.05, which
    # only reaches ~23k tris from a 473k-tri source. Loop gentle halves
    # while dense (deep jumps shred thin shells like pauldrons/vambraces
    # into spikes), then 0.25 to punch through the late-pass convergence
    # stall (a pure 0.5 floor stalls ~2x over target and the futile extra
    # passes shred the mesh). Cap passes so a stall can never compound.
    passes = 0
    prev = tris + 1
    stalled = False
    while tris > target_tris and passes < 12:
        floor = 0.25 if (tris <= target_tris * 4 or stalled) else 0.5
        ratio = max(target_tris / max(tris, 1), floor)
        log(f"decimate pass {passes + 1}: {tris} tris x{ratio:.3f} -> ~{int(tris * ratio)}")
        mod = obj.modifiers.new("Decimate", "DECIMATE")
        mod.decimate_type = "COLLAPSE"
        mod.ratio = ratio
        mod.use_collapse_triangulate = True
        mod.use_symmetry = True
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        me = obj.data
        tris = sum(max(len(p.vertices) - 2, 1) for p in me.polygons)
        stalled = (prev - tris) < prev * 0.01
        prev = tris
        passes += 1
    log(f"decimated {src_tris} -> {tris} tris in {passes} passes (target {target_tris})")
    global LAST_DECIMATE
    LAST_DECIMATE = (src_tris, tris)


def finish_mesh(obj):
    # Surface finishing AFTER place_and_scale, in FINAL game units (the
    # plug/seat boxes below are tuned in those units - running them on the
    # unscaled import silently matches nothing). Triangulate, hole plug +
    # armpit seat, normals, single UV/material. Must run before skinning.
    # triangulate + normals + single UV + single material
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    # decimate COLLAPSE leaves loose verts/edges that the exporter writes
    # as <lines> - the engine asserts "mesh is made of triangles" and
    # refuses the whole file. Clean again AFTER the loop, not just before.
    bpy.ops.mesh.delete_loose()
    # plug open shells: decimate shreds the arm<->torso intersection into
    # boundary loops (see-through armpit gaps + backface holes in Atlas).
    # mesh.fill caps each boundary loop with a triangle fan (NOT
    # edge_face_add, which grid-fills ACROSS the model). Scoped to the
    # armpit boxes: plate rims elsewhere stay open (their edges are
    # sub-pixel). Caps get gray-cell UVs (below) so they hide in shadow
    # instead of smearing atlas texels.
    bm = bmesh.from_edit_mesh(obj.data)
    for v in bm.verts:
        v.select = False
    for e in bm.edges:
        e.select = False
    for e in bm.edges:
        if e.is_boundary:
            mx = (e.verts[0].co.x + e.verts[1].co.x) / 2.0
            mz = (e.verts[0].co.z + e.verts[1].co.z) / 2.0
            if 0.2 <= abs(mx) <= 0.95 and 1.85 <= mz <= 2.65:
                e.select = True
    bmesh.update_edit_mesh(obj.data)
    n_sel = sum(1 for e in bm.edges if e.select)
    if n_sel:
        for f in bm.faces:
            f.tag = True
        bpy.ops.mesh.fill()
        bmesh.update_edit_mesh(obj.data)
        bm = bmesh.from_edit_mesh(obj.data)
        uv_lay = bm.loops.layers.uv.get(obj.data.uv_layers[0].name)
        g = ATLAS_GRID if ATLAS_GRID else 5
        gray = ATLAS_GRAY
        gu, gv = ((gray % g) + 0.5) / g, ((gray // g) + 0.5) / g
        n_new = 0
        for f in bm.faces:
            if not f.tag:
                n_new += 1
                if uv_lay is not None:
                    for loop in f.loops:
                        loop[uv_lay].uv = (gu, gv)
        log(f"hole plug: {n_sel} armpit boundary edges -> {n_new} gray cap faces")
    else:
        log("hole plug: no armpit boundary edges, junction closed")
    # seat the arms: decimate collapse shrinks the arm/torso overlap into a
    # slit gap (closed shells both sides - nothing to fill). Shift arm-side
    # junction verts inward so the arm sinks back into the torso, restoring
    # the hidden-seam overlap. Box avoids the torso wall (which must stay)
    # and the vambrace (already clean). 0.05 vanishes in armpit shadow.
    bm = bmesh.from_edit_mesh(obj.data)
    n_seat = 0
    for v in bm.verts:
        if 0.45 <= abs(v.co.x) <= 0.95 and 1.85 <= v.co.z <= 2.65:
            v.co.x -= math.copysign(0.05, v.co.x)
            n_seat += 1
    bmesh.update_edit_mesh(obj.data)
    log(f"armpit seat: {n_seat} junction verts shifted inward 0.05")
    # normal repair: decimate folds whole patches inside-out (37% of the
    # under-pauldron faces pointed strongly inward in the probe). Atlas
    # culls backfaces, so those render as holes. Flip faces whose normal
    # opposes the body-radial direction; the recalc below harmonizes.
    # Scoped to the shoulder boxes: a mesh-wide radial test misfires in
    # true concavities (groin, beard underside).
    bm = bmesh.from_edit_mesh(obj.data)
    bm.normal_update()
    n_flip = 0
    for f in bm.faces:
        c = f.calc_center_median()
        if 0.3 <= abs(c.x) <= 1.0 and 1.85 <= c.z <= 2.7:
            rl = math.hypot(c.x, c.y)
            if rl > 1e-6:
                fn = f.normal
                if (fn.x * c.x + fn.y * c.y) / rl < -0.3:
                    f.normal_flip()
                    n_flip += 1
    bmesh.update_edit_mesh(obj.data)
    log(f"normal repair: flipped {n_flip} inward faces in shoulder boxes")
    bpy.ops.mesh.quads_convert_to_tris(quad_method="BEAUTY", ngon_method="BEAUTY")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    if not obj.data.uv_layers:
        bpy.ops.uv.cube_project(cube_size=1.0)
    bpy.ops.object.mode_set(mode="OBJECT")
    while len(obj.data.uv_layers) > 1:
        obj.data.uv_layers.remove(obj.data.uv_layers[1])
    obj.data.materials.clear()
    mat = bpy.data.materials.get("dwarf_body") or bpy.data.materials.new("dwarf_body")
    mat.use_nodes = True
    obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = True
        p.material_index = 0


def place_and_scale(obj, arm, ref_h, scale):
    # normalize dwarf rotation/scale, then size to ref_h * scale
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    h = max(obj.dimensions.z, 0.001)
    f = (ref_h * scale) / h
    log(f"dwarf height {h:.2f} -> x{f:.3f} = {ref_h * scale:.2f} game units")
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


ENVELOPE_FATTEN = 6.0  # envelope head/tail radius multiplier (floor 0.35)


def fatten_envelopes(arm):
    """Fatten deform-bone envelopes (UNUSED since the rigid-bind fallback
    replaced envelopes - kept for the experiment record).

    The stock Biped envelopes are sized for a slim human; the dwarf torso /
    beard / pauldrons stick out far beyond them, so ENVELOPE parenting
    leaves half the mesh unbound. Heat ignores envelopes, so this is free
    when heat succeeds.
    """
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    n = 0
    for b in arm.data.edit_bones:
        if b.name in DEFORM_BONES:
            b.head_radius = max(b.head_radius * ENVELOPE_FATTEN, 0.35)
            b.tail_radius = max(b.tail_radius * ENVELOPE_FATTEN, 0.35)
            n += 1
    bpy.ops.object.mode_set(mode="OBJECT")
    log(f"fattened {n} deform-bone envelopes (x{ENVELOPE_FATTEN}, floor 0.35)")


def build_atlas_png(out_png):
    """Composite every part's base-color map into one atlas PNG.

    Blender pixel buffers run bottom-row-first, same convention as UV
    space, so cell (col, row-from-bottom) blits straight in and the
    pack_atlas_uvs() remap just works. Nearest-neighbor downsample is
    fine at these cell sizes. Imageless parts share the flat-gray cell.
    """
    size, g = ATLAS_SIZE, ATLAS_GRID
    cell = size // g
    total = size * size * 4
    # whole-buffer gray first: imageless parts share the gray cell, and any
    # unsampled spare cell degrades to gray instead of rainbow garbage
    buf = [0.5, 0.5, 0.5, 1.0] * (size * size)
    n = 0
    for imgname, idx in sorted(ATLAS_CELLS.items(), key=lambda kv: kv[1]):
        src = bpy.data.images.get(imgname)
        if src is None:
            log(f"WARNING: atlas source gone: {imgname}")
            continue
        w, h = src.size[0], src.size[1]
        if w < 8 or h < 8:
            continue
        px = [0.0] * (w * h * 4)
        src.pixels.foreach_get(px)
        cx, cy = (idx % g) * cell, (idx // g) * cell
        # nearest-neighbor w x h -> cell x cell
        for yy in range(cell):
            sy = min(int(yy * h / cell), h - 1) * w * 4
            do = ((cy + yy) * size + cx) * 4
            for xx in range(cell):
                so = sy + min(int(xx * w / cell), w - 1) * 4
                buf[do] = px[so]
                buf[do + 1] = px[so + 1]
                buf[do + 2] = px[so + 2]
                buf[do + 3] = px[so + 3]
                do += 4
        n += 1
    # Requester-approved deviation (Atlas v1): bare skin hands read better
    # at game size. The glove mesh spans leather forearm sleeves AND hands,
    # so only hand faces (|x| split in pack_atlas_uvs) land in the flat
    # skin cell; sleeves keep the source leather. Skin tone = face-cell
    # average (geometry untouched).
    if ATLAS_SKIN_IMG in ATLAS_CELLS:
        sidx = ATLAS_CELLS[ATLAS_SKIN_IMG]
        sx, sy = (sidx % g) * cell, (sidx // g) * cell
        r = gcol = b = cnt = 0.0
        for yy in range(cell):
            o = ((sy + yy) * size + sx) * 4
            for xx in range(cell):
                r += buf[o]
                gcol += buf[o + 1]
                b += buf[o + 2]
                cnt += 1.0
                o += 4
        r, gcol, b = r / cnt, gcol / cnt, b / cnt
        gx2, gy2 = (ATLAS_SKIN % g) * cell, (ATLAS_SKIN // g) * cell
        for yy in range(cell):
            o = ((gy2 + yy) * size + gx2) * 4
            for xx in range(cell):
                buf[o] = r
                buf[o + 1] = gcol
                buf[o + 2] = b
                buf[o + 3] = 1.0
                o += 4
        log(f"atlas: skin cell <- face average ({r:.2f},{gcol:.2f},{b:.2f})")
    out = bpy.data.images.new("dwarf_atlas", size, size)
    out.pixels.foreach_set(buf)
    out.filepath_raw = out_png
    out.file_format = "PNG"
    out.save()
    # free the composite (keep sources; Blender unloads on quit anyway)
    bpy.data.images.remove(out)
    log(f"atlas: {n} maps + gray {ATLAS_GRAY} + skin {ATLAS_SKIN} -> {size}px {out_png}")


def rigid_bind(dwarf, arm):
    """Bind every vert to exactly ONE nearest deform-bone segment.

    Replaces the envelope fallback: fattened torso capsules claimed
    mid-arm verts, and under 90-degree melee swings the arm bones left
    them behind - clean gaps opened at shoulder/armpit plus stretch
    spikes, while the head-cap/chest boundary sheared into neck slits
    (all invisible at rest, all obvious posed). Single-bone assignment
    cannot tear by construction: boundaries fall in natural creases
    (armpit, wrist, neck, groin, waist). A light smooth afterwards keeps
    rigid steps from looking hinged; normalize keeps sums at 1.
    Bone head/tail are in armature space == mesh space here (both
    transforms applied, both objects at origin).
    """
    for g in list(dwarf.vertex_groups):
        dwarf.vertex_groups.remove(g)
    for m in list(dwarf.modifiers):
        if m.type == "ARMATURE":
            dwarf.modifiers.remove(m)
    vgs = {name: dwarf.vertex_groups.new(name=name) for name in DEFORM_BONES}
    mod = dwarf.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    dwarf.parent = arm
    dwarf.matrix_parent_inverse.identity()
    segs = [(n, arm.data.bones[n].head_local, arm.data.bones[n].tail_local)
            for n in DEFORM_BONES if n in arm.data.bones]
    counts = {n: 0 for n, _h, _t in segs}
    for v in dwarf.data.vertices:
        px, py, pz = v.co
        best, best_d = None, 1e18
        for n, h, t in segs:
            ax, ay, az = h[0], h[1], h[2]
            abx, aby, abz = t[0] - ax, t[1] - ay, t[2] - az
            denom = abx * abx + aby * aby + abz * abz
            s = ((px - ax) * abx + (py - ay) * aby + (pz - az) * abz) / denom \
                if denom > 1e-12 else 0.0
            s = 0.0 if s < 0.0 else (1.0 if s > 1.0 else s)
            dx, dy, dz = px - (ax + abx * s), py - (ay + aby * s), pz - (az + abz * s)
            d = dx * dx + dy * dy + dz * dz
            if d < best_d:
                best, best_d = n, d
        vgs[best].add([v.index], 1.0, "REPLACE")
        counts[best] += 1
    log(f"rigid bind: {sum(1 for c in counts.values() if c)}/24 bones own verts")
    empties = sorted(n for n, c in counts.items() if not c)
    if empties:
        log(f"rigid bind: empty bones (no nearest verts): {empties}")


def skin_and_export(dwarf, arm):
    # parent mesh -> armature, heat first, envelope fallback (see below)
    bpy.ops.object.select_all(action="DESELECT")
    dwarf.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    assigned = sum(1 for v in dwarf.data.vertices if v.groups)
    log(f"heat weights: {assigned}/{len(dwarf.data.vertices)} verts assigned")
    heat_ok = assigned >= len(dwarf.data.vertices) // 2
    if not heat_ok:
        # Heat diffusion fails totally on some dense multi-shell Sketchfab
        # soup (this source: 461k tris with layered belt/braid shells even
        # after remove-doubles). Empty groups export as zero influences and
        # the unit can't animate, so bind rigidly to the nearest deform
        # segment instead (see rigid_bind: tear-proof by construction).
        log("WARNING: heat failed - falling back to rigid nearest-segment bind")
        rigid_bind(dwarf, arm)
        assigned = sum(1 for v in dwarf.data.vertices if v.groups)
        log(f"rigid weights: {assigned}/{len(dwarf.data.vertices)} verts assigned")
    else:
        log("skinned with automatic weights")
    log("vertex groups:", len(dwarf.vertex_groups))
    bad = sorted(g.name for g in dwarf.vertex_groups if g.name not in DEFORM_BONES)
    if bad:
        log("WARNING: weights on non-deform bones:", bad)
        for name in bad:
            dwarf.vertex_groups.remove(dwarf.vertex_groups[name])
        log("removed non-deform groups")
    # Head-cap (non-heat path only - heat already blends the skull well):
    # rigid nearest-segment leaves skull/face/helmet split between the
    # small head bone and the big neck/chest capsules, so the face would
    # ride the torso while the idle keys nod the head bone. Rebind the head
    # pauldrons and outstretched arms can't leak in) to the head bone.
    # Runs BEFORE smooth/normalize so the neck/beard seam stays soft.
    if not heat_ok and "head" in dwarf.vertex_groups:
        head_b = arm.data.bones.get("head")
        thr = head_b.head_local[2] - 0.5 if head_b is not None else 2.5
        head_vg = dwarf.vertex_groups["head"]
        capped = 0
        for v in dwarf.data.vertices:
            if v.co.z > thr and abs(v.co.x) < 0.4 and abs(v.co.y) < 0.5:
                for g in list(v.groups):
                    dwarf.vertex_groups[g.group].remove([v.index])
                head_vg.add([v.index], 1.0, "REPLACE")
                capped += 1
        log(f"head-cap: {capped} verts in head column (z>{thr:.2f}) assigned to head")
    # per-vertex sanity: strongest group must be a nearby deform bone;
    # report the distribution so spikes get caught here, not in Atlas
    from collections import Counter
    top = Counter()
    for v in dwarf.data.vertices:
        if v.groups:
            g = max(v.groups, key=lambda e: e.weight)
            top[dwarf.vertex_groups[g.group].name] += 1
    log("dominant-group histogram:", dict(sorted(top.items())))
    # soften weight boundaries. Heat blends get the full treatment;
    # rigid single-bone assignment gets ONE light pass: anything more
    # re-blurs the tear-proof boundaries back into shear zones.
    smooth_factor, smooth_repeat = (0.5, 4) if heat_ok else (0.25, 1)
    bpy.ops.object.select_all(action="DESELECT")
    dwarf.select_set(True)
    bpy.context.view_layer.objects.active = dwarf
    bpy.ops.object.mode_set(mode="WEIGHT_PAINT")
    bpy.ops.object.vertex_group_smooth(group_select_mode="ALL",
                                       factor=smooth_factor,
                                       repeat=smooth_repeat)
    if hasattr(bpy.ops.object, "vertex_group_normalize_all"):
        bpy.ops.object.vertex_group_normalize_all(
            group_select_mode="ALL", lock_active=False)
        log("normalized deform weights")
    bpy.ops.object.mode_set(mode="OBJECT")
    log("smoothed deform weights")
    # gate: the exporter writes zero-influence verts as rigid bind-pose -
    # catch an unskinned mesh here, not in Atlas
    assigned = sum(1 for v in dwarf.data.vertices if v.groups)
    log(f"weight gate: {assigned}/{len(dwarf.data.vertices)} verts bound")
    if assigned < len(dwarf.data.vertices) // 2:
        log("WARNING: mesh mostly unweighted - animations will look rigid")
    else:
        # height bands of unbound verts: tells Atlas what will stay rigid
        # (helmet? beard tip? skirt hem?) without opening Blender
        bands = {}
        for v in dwarf.data.vertices:
            if not v.groups:
                key = f"{v.co.z:.1f}"
                bands[key] = bands.get(key, 0) + 1
        if bands:
            log("unbound height bands (z: count):",
                dict(sorted(bands.items())))

    # §6 bone-head check: feet ~0.2, hip ~55% height, head ~98%
    for bn in ("foot_L", "hip", "chest", "head"):
        bb = arm.data.bones.get(bn)
        if bb is not None:
            log(f"bone {bn}: head=({bb.head_local[0]:.2f},{bb.head_local[1]:.2f},{bb.head_local[2]:.2f})")
    xs = [v.co.x for v in dwarf.data.vertices]
    ys = [v.co.y for v in dwarf.data.vertices]
    zs = [v.co.z for v in dwarf.data.vertices]
    log(f"final bounds X[{min(xs):.2f},{max(xs):.2f}] "
        f"Y[{min(ys):.2f},{max(ys):.2f}] Z[{min(zs):.2f},{max(zs):.2f}]")
    # texture atlas: one base-color map per part -> single 2048px baseTex
    out_png = os.path.join(MOD, "art", "textures", "skins", "skeletal", "tolkien", "dwarf_body.png")
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    build_atlas_png(out_png)
    # export mesh + armature (same call pattern as build_orcs.py - known good on 3.0)
    out_dae = os.path.join(MOD, "art", "meshes", "skeletal", "tolkien", "dwarf.dae")
    os.makedirs(os.path.dirname(out_dae), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    dwarf.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.wm.collada_export(filepath=out_dae, selected=True,
                               include_animations=False)
    log("EXPORTED", out_dae)
    with open(os.path.join(os.path.dirname(out_dae), "dwarf_CREDITS.txt"), "w", encoding="utf-8") as f:
        f.write("Derivative of '3D model of dwarf' by "
                "The Kala Ce (@harishrbat987), CC-BY 4.0.\n"
                "Source: https://sketchfab.com/3d-models/3d-model-of-dwarf-6a8f36db7c7a4cecb75c6634052ec598\n"
                f"Changes: decimated ~{LAST_DECIMATE[0] // 1000}k -> ~{LAST_DECIMATE[1]} tris "
                "(iterative collapse), display-stand disc stripped, armour KEPT, "
                "rigged to stock 0 A.D. Biped (art/skeletons/biped.xml), rescaled "
                "0.8x human (~3.1 game units), single material, 2048px atlas "
                "baseTex (one cell per part albedo).\n"
                "Deviation: hand faces repainted to face skin tone (forearm "
                "sleeves keep source leather; throat skin left authentic).\n"
                "Custom sturdy idle + retargeted walk/run (biped/dwarf_*.dae); "
                "melee/capture retargeted, death/promotion stock.\n")
    # sanity: verts under engine hard limit, armature present
    me = dwarf.data
    log(f"DONE verts={len(me.vertices)} (limit 32768), bones={len(arm.data.bones)}")
    missing = [b for b in ("hip", "chest", "head", "hand_R", "foot_L") if b not in arm.data.bones]
    if missing:
        log("WARNING missing biped bones:", missing)


IDLE_FRAMES = (1, 16, 32)

# Torso dampening for retargets: quaternion angle scale per bone. Limbs copy
# verbatim (1.0); spine/chest/head shrink toward rest so the human hunch
# doesn't crumple the stocky dwarf. Hip location deltas scale to dwarf size
# (x0.8) below.
DAMP_BASE = {"spine": 0.4, "spine1": 0.4, "chest": 0.45,
             "neck": 0.6, "head": 0.5}
# Melee adds: fists locked to the natural rest curl (the stock grip-release
# splays giant dwarf fingers into a wave), wrists calmed (stock sword-roll
# corkscrews the long forearms). Arms keep full swing.
DAMP_MELEE = {**DAMP_BASE,
              "hand_L": 0.45, "hand_R": 0.45,
              "finger_L": 0.0, "finger_R": 0.0,
              "fingertip_L": 0.0, "fingertip_R": 0.0}
LOC_SCALE = 0.8

STOCK_DIR = os.path.join(REF_DIR, "stock_anim")

# (stock file, dwarf anim name, damp profile). Times copy verbatim -> stock
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


def author_idle(dwarf, arm):
    """Sturdy breathing idle in the source pose (NOT the stock human crouch).

    Quaternion keys (shared mode with retargets). Amplitudes tiny (~2 deg);
    the win is the BASE pose itself - stocky rest instead of relax-crouch.
    Hip bob scaled to dwarf size (0.04 vs dwarf 0.05).
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
    act = bpy.data.actions.new("dwarf_idle")
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
        for f, v in zip(IDLE_FRAMES, [hip_base_z, hip_base_z + 0.04, hip_base_z]):
            pose.bones["hip"].location[2] = v
            pose.bones["hip"].keyframe_insert(data_path="location", index=2, frame=f)
    bpy.ops.object.mode_set(mode="OBJECT")
    sc.frame_set(1)
    log("authored sturdy idle (32f loop, quats)")


def export_idle(dwarf, arm):
    out_anim = os.path.join(MOD, "art", "animation", "biped", "dwarf_idle.dae")
    os.makedirs(os.path.dirname(out_anim), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    dwarf.select_set(True)
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


def retarget_stock(dwarf, arm, stock_name, out_name, damp):
    """Copy a stock Biped animation onto the dwarf with torso dampening.

    Same bone names + same hierarchy, so rotation curves transfer 1:1 on
    limbs; spine/chest/head angles shrink (DAMP_TORSO) so the human hunch
    doesn't crumple the stocky dwarf; hip location deltas scale by LOC_SCALE.
    Key TIMES copy verbatim -> stock variant speeds stay valid.
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
    new_act = bpy.data.actions.new("dwarf_" + out_name)
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
    out = os.path.join(MOD, "art", "animation", "biped", f"dwarf_{out_name}.dae")
    bpy.ops.object.select_all(action="DESELECT")
    dwarf.select_set(True)
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
    with open(os.path.join(var_dir, "dwarf_relax.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<variant name="Base" frequency="1">\n'
                '  <animations>\n'
                '    <animation file="biped/dwarf_idle.dae" name="idle" id="idle1" speed="35"/>\n'
                '    <animation file="biped/dwarf_idle.dae" name="idle" id="idle2" speed="32"/>\n'
                f'    <animation file="{walk_file}" name="Walk" id="walk1" speed="30"/>\n'
                f'    <animation file="{walk_file}" name="Walk" id="walk2" speed="29"/>\n'
                f'    <animation file="{walk_file}" name="Walk" id="walk3" speed="28"/>\n'
                f'    <animation file="{run_file}" name="Run" id="run1" speed="8"/>\n'
                f'    <animation file="{run_file}" name="Run" id="run2" speed="9"/>\n'
                f'    <animation file="{run_file}" name="Run" id="run3" speed="10"/>\n'
                '    <animation event="0.5" file="biped/dwarf_melee1.dae" name="attack_melee" id="attack1" speed="100"/>\n'
                '    <animation event="0.5" file="biped/dwarf_melee2.dae" name="attack_melee" id="attack2" speed="100"/>\n'
                '    <animation event="0.5" file="biped/dwarf_melee1.dae" name="attack_melee" id="attack3" speed="100"/>\n'
                '    <animation file="biped/infantry/promotion.dae" name="promotion" speed="80"/>\n'
                '  </animations>\n'
                '</variant>\n')
    log(f"wrote variant biped/dwarf_relax.xml (walk={walk_file} run={run_file})")
    with open(os.path.join(var_dir, "dwarf_capture.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<variant name="attack_capture">\n'
                '  <animations>\n'
                '    <animation file="biped/dwarf_capture.dae" name="attack_capture" speed="100"/>\n'
                '  </animations>\n'
                '</variant>\n')
    log("wrote variant biped/dwarf_capture.xml")


def main():
    argv = sys.argv
    args = argv[argv.index("--") + 1:] if "--" in argv else []
    if not args:
        print("Usage: blender --background --python build_dwarf_rig.py -- <dwarf.gltf|glb|fbx|obj> [target_tris] [scale] [ref_dae]")
        raise SystemExit(2)
    src = args[0]
    target = int(args[1]) if len(args) > 1 else DEFAULT_TARGET_TRIS
    scale = float(args[2]) if len(args) > 2 else DWARF_SCALE
    ref = args[3] if len(args) > 3 else REF_DEFAULT
    if not os.path.isfile(src):
        raise SystemExit(f"input not found: {src}")
    clear()
    arm, ref_h = import_ref_armature(ref)
    dwarf = import_dwarf(src)
    cleanup_decimate(dwarf, target)
    place_and_scale(dwarf, arm, ref_h, scale)
    finish_mesh(dwarf)
    restrict_deform_bones(arm)
    widen_bones(arm)
    skin_and_export(dwarf, arm)
    author_idle(dwarf, arm)
    export_idle(dwarf, arm)
    for stock_name, out_name, damp in RETARGET_JOBS:
        retarget_stock(dwarf, arm, stock_name, out_name, damp)
    write_variant("biped/dwarf_walk.dae", "biped/dwarf_run.dae")
    log("NEXT: test in 0 A.D. (mod selection -> Tolkien), check interestinglog.html for errors.")


if __name__ == "__main__":
    main()
