"""
Erebor B+C POC (run inside Blender 3.0 headless).

C: bake a stout dwarf body from the stock mesh by scaling verts + Biped
   edit-bones with the SAME factors, then recenter / feet-to-zero.
   Bone NAMES unchanged -> all stock biped/* variants keep working.
B: procedural dwarf-helm prop (dome + nasal + brow band + cheek flaps)
   standing in for the Sketchfab dwarf_helmet_LP asset, wired via the
   stock `helmet` attachpoint. Same path the real LP helmet takes.

USAGE:
  blender --background --python tools\\art_build\\build_erebor_poc.py

Outputs (under tolkien/):
  art/meshes/skeletal/tolkien/erebor_dwarf_stout.dae
  art/meshes/props/new/erebor_helm.dae
  art/actors/props/units/helmets/erebor_helm.xml
  art/actors/units/erebor/erebor_guard_poc.xml
  art/meshes/skeletal/tolkien/erebor_dwarf_stout_CREDITS.txt
  art/meshes/props/new/erebor_helm_CREDITS.txt
"""
import bpy
import os

MOD = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", "..", "tolkien"))
REF = os.environ.get("ZEROAD_REFERENCE_ART")
if not REF:
    raise RuntimeError("Set ZEROAD_REFERENCE_ART to the extracted 0 A.D. public art directory")

SX, SY, SZ = 1.16, 1.16, 0.82  # stout factors: +16% wide, -18% tall


def log(*a):
    print("[erebor-poc]", *a)


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def build_stout_body():
    src = os.path.join(REF, "meshes_skeletal_new_m_armor_tunic_short.dae")
    if not os.path.isfile(src):
        raise SystemExit(f"stock body missing: {src}")
    clear()
    before = set(bpy.data.objects)
    bpy.ops.wm.collada_import(filepath=src)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    arms = [o for o in new if o.type == "ARMATURE"]
    # Collada import brings a junk 8-vert Cube + an empty Biped shell:
    # keep the largest mesh and the armature with the most bones.
    mesh = max(meshes, key=lambda o: len(o.data.vertices)) if meshes else None
    arm = max(arms, key=lambda o: len(o.data.bones)) if arms else None
    for o in list(new):
        if o is not mesh and o is not arm:
            bpy.data.objects.remove(o, do_unlink=True)
    if mesh is None or arm is None:
        raise SystemExit("stock import gave no mesh+armature")
    log(f"stock: verts={len(mesh.data.vertices)} bones={len(arm.data.bones)} "
        f"height={mesh.dimensions.z:.2f}")
    # sanity: the mesh must be bound to THIS armature at the neck -
    # otherwise we would bake garbage (see turno 2026-09-29: connected-bone
    # double-transform pushed head/neck 0.5 low on one attempt).
    hb0 = arm.data.bones.get("head")
    if hb0 is None or abs(hb0.head_local[2] - 3.773) > 0.15:
        raise SystemExit(
            f"stock armature unexpected (head z={hb0.head_local[2] if hb0 else None}, "
            "want ~3.77) - import nondeterminism, aborting loudly")

    # 1. scale mesh verts (each vert independent - no sharing issue)
    for v in mesh.data.vertices:
        x, y, z = v.co
        v.co = (x * SX, y * SY, z * SZ)
    # 2. scale + shift armature edit bones with ONE combined transform.
    # Connected-bone caution: a connected child's head IS its parent's tail
    # (same point). Writing both double-transforms the joint (this pushed
    # head/neck 0.5 low once). So: write every tail, but only heads of
    # UNconnected bones - connected heads follow their parent tail
    # automatically, order-independently (same affine T everywhere).
    # Mesh recenter offset first (mesh already scaled above).
    xs = [v.co.x for v in mesh.data.vertices]
    ys = [v.co.y for v in mesh.data.vertices]
    zs = [v.co.z for v in mesh.data.vertices]
    dx = -((max(xs) + min(xs)) / 2)
    dy = -((max(ys) + min(ys)) / 2)
    dz = -min(zs)
    log(f"shift dx={dx:.3f} dy={dy:.3f} dz={dz:.3f}")

    def T(p):
        return (p[0] * SX + dx, p[1] * SY + dy, p[2] * SZ + dz)

    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    n_conn = 0
    for b in arm.data.edit_bones:
        b.tail = T(b.tail)
        if b.use_connect:
            n_conn += 1
        else:
            b.head = T(b.head)
    bpy.ops.object.mode_set(mode="OBJECT")
    log(f"bone transform done ({n_conn} connected heads followed parents)")

    # 3. same shift for the mesh verts (each vert independent)
    for v in mesh.data.vertices:
        v.co = (v.co[0] + dx, v.co[1] + dy, v.co[2] + dz)

    # 4. validation: head bone must sit at the mesh neck (stock diff 0.078,
    # scaled 0.064) and helmet a touch below head (stock 0.099 -> 0.081).
    # Catches connected-bone double-transforms instead of baking garbage.
    xs = [v.co.x for v in mesh.data.vertices]
    zs = [v.co.z for v in mesh.data.vertices]
    mesh_top = max(zs)
    hb = arm.data.bones.get("head")
    hm = arm.data.bones.get("helmet")
    if hb is None or hm is None:
        raise SystemExit("head/helmet bone missing after transform")
    d_head = mesh_top - hb.head_local[2]
    d_helm = hb.head_local[2] - hm.head_local[2]
    log(f"validate: mesh_top={mesh_top:.3f} head={hb.head_local[2]:.3f} "
        f"helmet={hm.head_local[2]:.3f} (want gaps ~0.064 / ~0.081)")
    if abs(d_head - 0.064) > 0.06 or abs(d_helm - 0.081) > 0.06:
        raise SystemExit(f"VALIDATION FAILED gaps {d_head:.3f}/{d_helm:.3f} - aborting")

    xs = [v.co.x for v in mesh.data.vertices]
    ys = [v.co.y for v in mesh.data.vertices]
    zs = [v.co.z for v in mesh.data.vertices]
    tris = sum(max(len(p.vertices) - 2, 1) for p in mesh.data.polygons)
    log(f"stout: X[{min(xs):.2f},{max(xs):.2f}] Y[{min(ys):.2f},{max(ys):.2f}] "
        f"Z[{min(zs):.2f},{max(zs):.2f}] tris~{tris}")
    for bn in ("foot_L", "hip", "head", "helmet"):
        bb = arm.data.bones.get(bn)
        if bb is not None:
            log(f"bone {bn}: head=({bb.head_local[0]:.2f},"
                f"{bb.head_local[1]:.2f},{bb.head_local[2]:.2f})")

    out = os.path.join(MOD, "art", "meshes", "skeletal", "tolkien",
                       "erebor_dwarf_stout.dae")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.wm.collada_export(filepath=out, selected=True,
                              include_animations=False)
    log("EXPORTED", out)
    with open(os.path.join(os.path.dirname(out),
                           "erebor_dwarf_stout_CREDITS.txt"), "w",
              encoding="utf-8") as f:
        f.write("B+C POC body: derived from 0 A.D. public stock mesh "
                "skeletal/new/m_armor_tunic_short.dae (CC-BY-SA, Wildfire Games).\n"
                f"Changes: baked stout scale X*{SX} Y*{SY} Z*{SZ}, recentered, "
                "feet to Z=0. No new sculpt; bone names unchanged so all stock "
                "biped/* animation variants keep working.\n")
    return out


def build_helm():
    # Frame: prop origin = helmet bone. v2 (stock-coolus-sized) got
    # SWALLOWED: the widened erebor skull (X +/-0.22) is nearly as wide as
    # the dome, so dome/band/nasal buried and only knob + flap edges
    # showed. v3 = generous clearance all round (oversized reads fine at
    # game distance; skin-tight clips). Brim at brow ~0.33 (eyes ~0.25).
    clear()
    # dome
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8,
                                        radius=0.30, location=(0, 0.02, 0.42))
    dome = bpy.context.active_object
    dome.name = "helm_dome"
    dome.scale = (1.0, 0.97, 0.95)
    bpy.context.view_layer.update()
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    # brow band (brim clears the eyes, sits at the brow ~0.40)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.295, depth=0.09,
                                       location=(0, 0.02, 0.40), vertices=16)
    band = bpy.context.active_object
    band.name = "helm_band"
    # nasal guard (front = +Y per art-unit-template §5; must stand PROUD
    # of the nose bridge - earlier placements buried it inside the face)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0.17, 0.19))
    nasal = bpy.context.active_object
    nasal.name = "helm_nasal"
    nasal.scale = (0.05, 0.035, 0.28)
    bpy.context.view_layer.update()
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    # cheek flaps L/R (outside the skull, jaw height)
    flaps = []
    for sx in (-1.0, 1.0):
        bpy.ops.mesh.primitive_cube_add(size=1.0,
                                       location=(sx * 0.245, 0.06, 0.16))
        fl = bpy.context.active_object
        fl.name = f"helm_cheek_{'L' if sx < 0 else 'R'}"
        fl.scale = (0.05, 0.17, 0.28)
        bpy.context.view_layer.update()
        bpy.ops.object.transform_apply(location=False, rotation=False,
                                       scale=True)
        flaps.append(fl)
    # top knob
    bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6,
                                        radius=0.05, location=(0, 0.02, 0.72))
    knob = bpy.context.active_object
    knob.name = "helm_knob"

    # join all (bake each part's origin to world origin FIRST: join()
    # rewrites every part into the ACTIVE object's local frame, so a
    # non-zero active origin silently shifts the whole prop - v2 shipped
    # 0.38 low for exactly this reason; and the dome cut below MUST run
    # post-bake, in the helmet frame - pre-bake it cut a part-local sphere
    # and kept only a top sliver, v1..v3's bare skull + floating knob)
    bpy.ops.object.select_all(action="DESELECT")
    for o in (dome, band, nasal, knob, *flaps):
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=True, rotation=False,
                                       scale=False)
    # cut dome open at the brim (helmet frame now == dome local frame)
    me = dome.data
    bpy.ops.object.select_all(action="DESELECT")
    dome.select_set(True)
    bpy.context.view_layer.objects.active = dome
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    for p in me.polygons:
        cz = sum(me.vertices[i].co.z for i in p.vertices) / len(p.vertices)
        if cz < 0.36:
            p.select = True
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.delete(type="FACE")
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    for o in (dome, band, nasal, knob, *flaps):
        o.select_set(True)
    bpy.context.view_layer.objects.active = dome
    bpy.ops.object.join()
    helm = bpy.context.view_layer.objects.active
    helm.name = "erebor_helm"
    # cleanup + UV + single material
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=0.0001)
    bpy.ops.mesh.quads_convert_to_tris(quad_method="BEAUTY",
                                       ngon_method="BEAUTY")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.uv.cube_project(cube_size=1.0)
    bpy.ops.object.mode_set(mode="OBJECT")
    while len(helm.data.uv_layers) > 1:
        helm.data.uv_layers.remove(helm.data.uv_layers[1])
    helm.data.materials.clear()
    mat = bpy.data.materials.get("erebor_helm") or \
        bpy.data.materials.new("erebor_helm")
    mat.use_nodes = True
    helm.data.materials.append(mat)
    for p in helm.data.polygons:
        p.material_index = 0
        p.use_smooth = True
    # frame validation: prop origin = helmet bone, geometry must sit ABOVE
    # it (stock coolus spans +0.30..+0.69). Catches join-origin shifts.
    hxs = [v.co.x for v in helm.data.vertices]
    hzs = [v.co.z for v in helm.data.vertices]
    log(f"helm local X[{min(hxs):.2f},{max(hxs):.2f}] "
        f"Z[{min(hzs):.2f},{max(hzs):.2f}] "
        f"(want X~+/-0.30 Z~0.0..0.77)")
    if min(hzs) < -0.05 or max(hzs) > 0.85:
        raise SystemExit("HELM FRAME VALIDATION FAILED - aborting")
    # dome-presence check: faces with center z in the dome band must be a
    # real shell (v1..v3 cut left only a sliver: verts survived, faces did
    # not - verts-only checks can't catch it)
    n_dome = 0
    for p in helm.data.polygons:
        cz = sum(helm.data.vertices[i].co.z for i in p.vertices)
        cz /= len(p.vertices)
        if 0.45 < cz < 0.70:
            n_dome += 1
    log(f"helm dome-band faces (z 0.45..0.70): {n_dome} (want >= 40)")
    if n_dome < 40:
        raise SystemExit("HELM DOME VALIDATION FAILED - aborting")
    tris = len(helm.data.polygons)
    log(f"helm tris={tris} verts={len(helm.data.vertices)}")
    out = os.path.join(MOD, "art", "meshes", "props", "new", "erebor_helm.dae")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    helm.select_set(True)
    bpy.context.view_layer.objects.active = helm
    bpy.ops.wm.collada_export(filepath=out, selected=True)
    log("EXPORTED", out)
    with open(os.path.join(os.path.dirname(out), "erebor_helm_CREDITS.txt"),
              "w", encoding="utf-8") as f:
        f.write("B+C POC prop: procedural placeholder helmet (dome + nasal + "
                "brow band + cheek flaps), no Sketchfab source bundled.\n"
                "Design evokes 'Dwarf_Helmet_LP' by prorok_009 (CC-BY 4.0, "
                "https://sketchfab.com/3d-models/dwarf-helmet-lp-6196f83b8dc7416583f6197df9f09177). "
                "Swap path: download GLB (login + accept license), decimate to "
                "~1.5k tris, single material/UV, scale to head (~0.6 tall), "
                "feet n/a (prop), export here with the same filename.\n")


def write_xml():
    prop_dir = os.path.join(MOD, "art", "actors", "props", "units", "helmets")
    os.makedirs(prop_dir, exist_ok=True)
    with open(os.path.join(prop_dir, "erebor_helm.xml"), "w",
              encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n'
                '<actor version="1">\n'
                '  <castshadow/>\n'
                '  <group>\n'
                '    <variant frequency="1" name="erebor-helm">\n'
                '      <mesh>props/new/erebor_helm.dae</mesh>\n'
                '      <textures>\n'
                '        <texture file="skeletal/tolkien/erebor_iron_01.png" name="baseTex"/>\n'
                '        <texture file="default_norm.png" name="normTex"/>\n'
                '        <texture file="null_black.dds" name="specTex"/>\n'
                '      </textures>\n'
                '    </variant>\n'
                '  </group>\n'
                '  <material>objectcolor_norm_spec.xml</material>\n'
                '</actor>\n')
    log("wrote prop actor helmets/erebor_helm.xml")
    with open(os.path.join(MOD, "art", "actors", "units", "erebor",
                           "erebor_guard_poc.xml"), "w",
              encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n'
                '<actor version="1">\n'
                '  <castshadow/>\n'
                '  <group>\n'
                '    <variant frequency="1" name="Base">\n'
                '      <mesh>skeletal/tolkien/erebor_dwarf_stout.dae</mesh>\n'
                '      <props>\n'
                '        <prop actor="props/units/heads/erebor_head.xml" attachpoint="head"/>\n'
                '        <prop actor="props/units/heads/erebor_beard.xml" attachpoint="head"/>\n'
                '        <prop actor="props/units/helmets/erebor_helm.xml" attachpoint="helmet"/>\n'
                '        <prop actor="props/units/weapons/elf_sword.xml" attachpoint="weapon_R"/>\n'
                '      </props>\n'
                '      <textures>\n'
                '        <texture file="skeletal/tolkien/erebor_iron_01.png" name="baseTex"/>\n'
                '        <texture file="default_norm.png" name="normTex"/>\n'
                '        <texture file="null_black.dds" name="specTex"/>\n'
                '      </textures>\n'
                '    </variant>\n'
                '  </group>\n'
                '  <group>\n'
                '    <variant file="biped/base_swordsman_2hand_relax.xml"/>\n'
                '    <variant file="biped/attack_capture.xml"/>\n'
                '    <variant file="biped/attack_slaughter.xml"/>\n'
                '    <variant file="biped/death_infantry.xml"/>\n'
                '  </group>\n'
                '  <material>player_trans_norm_spec.xml</material>\n'
                '</actor>\n')
    log("wrote unit actor erebor/erebor_guard_poc.xml")


def main():
    build_stout_body()
    build_helm()
    write_xml()
    log("POC BUILD DONE")


if __name__ == "__main__":
    main()
