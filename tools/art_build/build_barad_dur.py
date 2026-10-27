"""Barad-dur fusion: ptol lighthouse base (cropped) + Eye of Sauron crown (prop).

Inputs:
  %TEMP%/0ad_ref/ptol_lighthouse.dae   (0 A.D. public art, Wildfire Games, CC BY-SA 3.0)
  ~/Downloads/the_eye_of_sauron_lord_of_the_rings.glb  (Yanez Designs, CC-BY 4.0)
Outputs (mod-side, never touches the 0 A.D. install):
  tolkien/art/meshes/structures/mordor/barad_dur_base.dae
  tolkien/art/meshes/structures/mordor/barad_dur_eye.dae
  tolkien/art/textures/skins/structures/mordor/barad_dur_eye.png
  tolkien/art/meshes/structures/mordor/barad_dur_eye_CREDITS.txt
Run: blender --background --python tools/art_build/build_barad_dur.py
"""
import bpy
import bmesh
import os
import random
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MOD = os.path.join(REPO, "tolkien")
GLB = os.path.join(os.path.expandvars("%USERPROFILE%"), "Downloads",
                   "the_eye_of_sauron_lord_of_the_rings.glb")
LIGHT = os.path.join(os.path.expandvars("%TEMP%"), "0ad_ref", "ptol_lighthouse.dae")

CUT_Z = 26.0        # lighthouse lantern cut (shaft ends, flare begins)
CROWN_MIN_Z = 0.0  # keep tower from here up: full black shaft above the stone base
CROWN_BASE_Z = CUT_Z - 1.5  # sink the crown into the shaft: closes the see-through slit
SCALE = 0.114       # crown 57 wide -> ~6.5 (covers 4.5 platform, matches old flare)

OUT_MESH_DIR = os.path.join(MOD, "art", "meshes", "structures", "mordor")
OUT_TEX_DIR = os.path.join(MOD, "art", "textures", "skins", "structures", "mordor")


def log(*a):
    print("[barad]", *a, flush=True)


def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images,
                 bpy.data.actions, bpy.data.armatures):
        for x in list(coll):
            try:
                coll.remove(x)
            except Exception:
                pass


def tris(me):
    return sum(max(len(p.vertices) - 2, 1) for p in me.polygons)


def bake_gltf_meshes():
    """Unparent (keep transform) + apply, so local coords == assembled world."""
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    if not meshes:
        raise SystemExit("no meshes found after import")
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    for o in meshes:
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.context.view_layer.update()
    return [o for o in bpy.data.objects if o.type == "MESH"]


def remove_loose(obj):
    """Drop wire edges/lone verts (export as <lines> -> engine rejects mesh)."""
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.edges.ensure_lookup_table()
    wire = [e for e in bm.edges if not e.link_faces]
    if wire:
        bmesh.ops.delete(bm, geom=wire, context="EDGES")
    bm.verts.ensure_lookup_table()
    lone = [v for v in bm.verts if not v.link_edges]
    if lone:
        bmesh.ops.delete(bm, geom=lone, context="VERTS")
    bm.faces.ensure_lookup_table()
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(me)
    me.update()
    bm.free()


def delete_verts_where(obj, pred):
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    kill = [v for v in bm.verts if pred(v.co)]
    if kill:
        bmesh.ops.delete(bm, geom=kill, context="VERTS")
    bm.to_mesh(me)
    me.update()
    bm.free()
    remove_loose(obj)


def remap_uv(obj, fn):
    me = obj.data
    if not me.uv_layers:
        raise SystemExit(f"{obj.name} has no UV layer")
    for loop in me.uv_layers[0].data:
        u, v = loop.uv
        loop.uv = fn(u, v)


# ---------------- phase 1: lighthouse base ----------------
for p in (GLB, LIGHT):
    if not os.path.isfile(p):
        raise SystemExit(f"missing input: {p}")
os.makedirs(OUT_MESH_DIR, exist_ok=True)
os.makedirs(OUT_TEX_DIR, exist_ok=True)

clear()
bpy.ops.wm.collada_import(filepath=LIGHT)
base = None
for o in bpy.data.objects:
    if o.type == "MESH":
        base = o
        break
if base is None:
    raise SystemExit("lighthouse DAE imported 0 meshes")
base.scale = (1.0, 1.0, 1.0)  # undo inch->meter import artifact; local == game units
bpy.context.view_layer.update()

xs = [v.co.x for v in base.data.vertices]
ys = [v.co.y for v in base.data.vertices]
zs = [v.co.z for v in base.data.vertices]
log(f"lighthouse local X[{min(xs):.2f},{max(xs):.2f}] "
    f"Y[{min(ys):.2f},{max(ys):.2f}] Z[{min(zs):.2f},{max(zs):.2f}] "
    f"verts={len(base.data.vertices)} tris~{tris(base.data)}")

ring = [(v.co.x, v.co.y) for v in base.data.vertices if CUT_Z - 6.0 <= v.co.z <= CUT_Z]
shaft_x = sum(p[0] for p in ring) / len(ring)
shaft_y = sum(p[1] for p in ring) / len(ring)
log(f"shaft center at cut: ({shaft_x:.2f}, {shaft_y:.2f}), ring verts={len(ring)}")

delete_verts_where(base, lambda co: co.z > CUT_Z)
log(f"base after cut: verts={len(base.data.vertices)} tris~{tris(base.data)} "
    f"zmax={max(v.co.z for v in base.data.vertices):.2f}")
base.name = "BaradDurBase"

# ---------------- phase 2: eye crown ----------------
# (parse GLB in a second scene state, then re-import base? simpler: stash base coords)
# Save base mesh to a temp DAE and re-import later would lose empties; instead do crown
# work first in variables, then rebuild. Order: finish crown now, base export after.
clear()
bpy.ops.import_scene.gltf(filepath=GLB)
meshes = bake_gltf_meshes()
for o in meshes:
    me = o.data
    pts = [v.co for v in me.vertices]
    log(f"raw {o.name}: verts={len(me.vertices)} "
        f"X[{min(c.x for c in pts):.1f},{max(c.x for c in pts):.1f}] "
        f"Y[{min(c.y for c in pts):.1f},{max(c.y for c in pts):.1f}] "
        f"Z[{min(c.z for c in pts):.1f},{max(c.z for c in pts):.1f}]")

tower = next(o for o in meshes if "Tower" in o.name)
eye_red = next(o for o in meshes if "Eye_03" in o.name)
pupil = next(o for o in meshes if "Eye_07" in o.name)

delete_verts_where(tower, lambda co: co.z < CROWN_MIN_Z)
log(f"tower crown kept: verts={len(tower.data.vertices)} tris~{tris(tower.data)}")

# UV park: left half = basalt, top-right = glowing red, bottom-right = pupil black
remap_uv(tower, lambda u, v: (u * 0.48, v))
remap_uv(eye_red, lambda u, v: (u * 0.46 + 0.52, v * 0.46 + 0.52))
remap_uv(pupil, lambda u, v: (u * 0.46 + 0.52, v * 0.46 + 0.02))

bpy.ops.object.select_all(action="DESELECT")
for o in (tower, eye_red, pupil):
    o.select_set(True)
bpy.context.view_layer.objects.active = tower
# eye-ball center in baked source coords (used for the fire/attach point later)
erc = [v.co for v in eye_red.data.vertices]
eye_src = (sum(c.x for c in erc) / len(erc),
           sum(c.y for c in erc) / len(erc),
           sum(c.z for c in erc) / len(erc))
bpy.ops.object.join()
crown = bpy.context.view_layer.objects.active
crown.name = "BaradDurEye"

allc = [v.co for v in crown.data.vertices]
cx = (min(c.x for c in allc) + max(c.x for c in allc)) / 2
cy = (min(c.y for c in allc) + max(c.y for c in allc)) / 2
minz = min(c.z for c in allc)
log(f"crown pre-fit center=({cx:.1f},{cy:.1f}) minZ={minz:.1f}")
for v in crown.data.vertices:
    v.co.x = (v.co.x - cx) * SCALE + shaft_x
    v.co.y = (v.co.y - cy) * SCALE + shaft_y
    v.co.z = (v.co.z - minz) * SCALE + CROWN_BASE_Z
# eye-center (fire point) = transformed eye-ball center
fire = ((eye_src[0] - cx) * SCALE + shaft_x,
        (eye_src[1] - cy) * SCALE + shaft_y,
        (eye_src[2] - minz) * SCALE + CROWN_BASE_Z)
log(f"eye center (fire point): ({fire[0]:.2f}, {fire[1]:.2f}, {fire[2]:.2f})")
# make crown coords relative to the fire point: prop attaches AT fire
for v in crown.data.vertices:
    v.co.x -= fire[0]
    v.co.y -= fire[1]
    v.co.z -= fire[2]
remove_loose(crown)
cc = [v.co for v in crown.data.vertices]
log(f"crown local X[{min(c.x for c in cc):.2f},{max(c.x for c in cc):.2f}] "
    f"Y[{min(c.y for c in cc):.2f},{max(c.y for c in cc):.2f}] "
    f"Z[{min(c.z for c in cc):.2f},{max(c.z for c in cc):.2f}] "
    f"verts={len(cc)} tris~{tris(crown.data)}")

# palette texture 128px
random.seed(7)
W = H = 128
pix = [0.0] * (W * H * 4)
for y in range(H):
    for x in range(W):
        i = (y * W + x) * 4
        if x < 64:
            n = random.uniform(-0.018, 0.018)
            course = 0.012 if (y % 16 == 0) else 0.0  # faint ashlar courses
            v = 0.085 + n - course
            pix[i:i + 3] = (v, v, v + 0.006)
        elif y >= 64:
            dx, dy = (x - 96) / 30.0, (y - 96) / 30.0
            d = min((dx * dx + dy * dy) ** 0.5, 1.0)
            r = 1.0 - d * 0.55
            pix[i:i + 3] = (r, 0.10 * (1 - d) + 0.02, 0.015)
        else:
            v = 0.02 + random.uniform(0, 0.012)
            pix[i:i + 3] = (v, v, v)
        pix[i + 3] = 1.0
img = bpy.data.images.new("barad_dur_eye", W, H, alpha=False)
img.pixels.foreach_set(pix)
out_png = os.path.join(OUT_TEX_DIR, "barad_dur_eye.png")
img.filepath_raw = out_png
img.file_format = "PNG"
img.save()
log("wrote", out_png)

mat = bpy.data.materials.new("BaradDurEye")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
tex.image = img
mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
crown.data.materials.clear()
crown.data.materials.append(mat)

out_eye = os.path.join(OUT_MESH_DIR, "barad_dur_eye.dae")
bpy.ops.object.select_all(action="DESELECT")
crown.select_set(True)
bpy.context.view_layer.objects.active = crown
bpy.ops.wm.collada_export(filepath=out_eye, selected=True, include_animations=False)
log("EXPORTED", out_eye, f"{os.path.getsize(out_eye)} bytes")
crown_nverts = len(crown.data.vertices)
crown_ntris = tris(crown.data)

with open(os.path.join(OUT_MESH_DIR, "barad_dur_eye_CREDITS.txt"), "w", encoding="utf-8") as f:
    f.write("Derivative of 'The Eye Of Sauron (Lord of the Rings)' by Yanez Designs, CC-BY 4.0.\n"
            "Source: https://sketchfab.com/3d-models/the-eye-of-sauron-lord-of-the-rings-fadecd2a323b47dab09f7e27402e521d\n"
            "Changes: baked node transforms, kept crown (tower Z>140) + eye, scaled 0.114x and seated\n"
            "for the Barad-dur lighthouse fusion; single material with new 128px palette texture\n"
            "(basalt / glowing red / pupil black). Base shaft: 0 A.D. public ptol_lighthouse mesh "
            "(Wildfire Games, CC BY-SA 3.0).\n")

# ---------------- phase 3: base export (needs fire point) ----------------
clear()
bpy.ops.wm.collada_import(filepath=LIGHT)
# drop the source's prop empties (they sit at the origin); we author our own below
for o in [o for o in bpy.data.objects if o.type == "EMPTY"]:
    bpy.data.objects.remove(o, do_unlink=True)
base = next(o for o in bpy.data.objects if o.type == "MESH")
base.scale = (1.0, 1.0, 1.0)
bpy.context.view_layer.update()
delete_verts_where(base, lambda co: co.z > CUT_Z)
base.name = "BaradDurBase"
if base.data.materials:
    base.data.materials.clear()


def mk_empty(name, loc):
    bpy.ops.object.empty_add(location=loc)
    e = bpy.context.view_layer.objects.active
    e.name = name
    e.parent = base
    return e


mk_empty("prop-fire", fire)
mk_empty("prop-projectile", (shaft_x, shaft_y, CUT_Z + 2.0))
mk_empty("prop-garrisoned", (0.0, 0.0, 0.0))
out_base = os.path.join(OUT_MESH_DIR, "barad_dur_base.dae")
bpy.ops.object.select_all(action="DESELECT")
base.select_set(True)
for o in bpy.data.objects:
    if o.type == "EMPTY":
        o.select_set(True)
bpy.context.view_layer.objects.active = base
bpy.ops.wm.collada_export(filepath=out_base, selected=True, include_animations=False)
log("EXPORTED", out_base, f"{os.path.getsize(out_base)} bytes")
log(f"DONE base_verts={len(base.data.vertices)} base_tris~{tris(base.data)} "
    f"crown_verts={crown_nverts} crown_tris~{crown_ntris} (limit 32768/mesh)")
