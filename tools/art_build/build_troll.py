"""
Cave Troll -> 0 A.D. converter (run inside Blender).

Source model (NOT bundled - download manually):
  LOTR Cave Troll - (for animating/rigging) by Ole Gunnar Isager
  https://sketchfab.com/3d-models/lotr-cave-troll-for-animatingrigging-20a50af723314c1dac04aad8c929aa1e
  Triangles: ~17.9k, Vertices: ~9.1k, License: CC-BY 4.0
  A-pose, NO rig, NO animations, 4K PBR textures.

What this script does (0 A.D. requirements):
  - hard engine limit is 32768 verts/mesh, but RTS budget for an
    elephant-class unit is ~5-6k tris -> default TARGET_TRIS = 5500
  - joins all meshes, single material, single UV layer (0 A.D. = 1 mat/mesh)
  - planar-degenerate cleanup, decimate (collapse, preserve UVs/symmetry),
    triangulate, recalc normals
  - scales to ~3.6m tall (troll vs ~1.8m human), applies transforms,
    Z-up / Y-forward (Blender default = 0 A.D. convention)
  - exports Collada 1.4 (.dae) readable by collada2pmd / Pyrogenesis
  - downscales source textures to 512px PNG for
    tolkien/art/textures/skins/skeletal/tolkien/

USAGE (Blender 3.6 LTS recommended, glTF importer built-in):
  1. Log into Sketchfab, download the model (glTF/FBX/OBJ) + accept CC-BY.
     Unzip to e.g. C:\\Temp\\troll\\scene.gltf (or .glb / .fbx / .obj)
  2. blender --background --python tools\\art_build\\build_troll.py -- ^
       C:\\Temp\\troll\\scene.gltf 5500
  3. Output: tolkien\\art\\meshes\\skeletal\\tolkien\\troll.dae
             tolkien\\art\\textures\\skins\\skeletal\\tolkien\\troll_body.png
  4. Wire up tolkien\\art\\actors\\units\\mordor\\infantry_troll.xml (created
     separately as a STATIC placeholder). Full walk/attack/death needs a
     rig + skeleton.xml + per-action .dae anims - this script does NOT rig.

Credit (REQUIRED by CC-BY if you ship the derivative):
  Derivative of "LOTR Cave Troll - (for animating/rigging)" by
  Ole Gunnar Isager (@FrenchBaguette), CC-BY 4.0. Keep this notice in
  tolkien/art/meshes/skeletal/tolkien/troll_CREDITS.txt
"""
import bpy
import os
import sys
import math

MOD = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tolkien"))
# fallback if repo moved: resolve relative to this script
try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
    _REPO_MOD = os.path.normpath(os.path.join(_HERE, "..", "..", "tolkien"))
    if os.path.isdir(_REPO_MOD):
        MOD = _REPO_MOD
except Exception:
    pass

TARGET_HEIGHT = 3.6   # meters, troll standing height
DEFAULT_TARGET_TRIS = 5500


def log(*a):
    print("[troll]", *a)


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_source(path):
    ext = os.path.splitext(path)[1].lower()
    log("importing", path)
    if ext in (".gltf", ".glb"):
        bpy.ops.import_scene.gltf(filepath=path, merge_vertices=True)
    elif ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=path)
    elif ext in (".obj",):
        bpy.ops.import_scene.obj(filepath=path)
    elif ext == ".dae":
        bpy.ops.wm.collada_import(filepath=path)
    else:
        raise SystemExit(f"unsupported input extension: {ext} (use .gltf/.glb/.fbx/.obj/.dae)")
    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not objs:
        raise SystemExit("no meshes found after import - check the download")
    return objs


def join_meshes(objs):
    # bake object + parent node transforms first (see build_troll_rig.py):
    # join() merges raw local coords and would scramble multi-part scenes.
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
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    troll = bpy.context.view_layer.objects.active
    troll.name = "troll"
    return troll


def count_tris(obj):
    me = obj.data
    # polygons may be n-gons pre-triangulation; estimate tris via loop fan count
    n = sum(max(len(p.vertices) - 2, 1) for p in me.polygons)
    return n, len(me.vertices)


def decimate_to_target(obj, target_tris):
    tris, verts = count_tris(obj)
    log(f"source: ~{tris} tris, {verts} verts (Sketchfab lists ~17900/9100)")
    if tris <= target_tris:
        log("already under target, skipping decimate")
        return
    ratio = max(target_tris / max(tris, 1), 0.05)
    log(f"decimate ratio {ratio:.3f} -> target {target_tris}")
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=0.0001)
    bpy.ops.mesh.delete_loose()
    bpy.ops.object.mode_set(mode="OBJECT")
    mod = obj.modifiers.new("Decimate", "DECIMATE")
    mod.decimate_type = "COLLAPSE"
    mod.ratio = ratio
    mod.use_collapse_triangulate = True
    mod.use_symmetry = True
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    # triangulate explicitly - 0 A.D. importer expects triangles
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.quads_convert_to_tris(quad_method="BEAUTY", ngon_method="BEAUTY")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    tris2, verts2 = count_tris(obj)
    log(f"after: ~{tris2} tris, {verts2} verts")
    if verts2 > 32768:
        log("WARNING: still over 0 A.D. hard limit 32768 verts - lower TARGET_TRIS")


def single_material_uv(obj):
    me = obj.data
    if not me.uv_layers:
        log("WARNING: no UVs found - adding cube project (re-unwrap manually for quality)")
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.cube_project(cube_size=1.0)
        bpy.ops.object.mode_set(mode="OBJECT")
    # keep only the active UV layer (0 A.D. = one UV set for baseTex)
    while len(me.uv_layers) > 1:
        me.uv_layers.remove(me.uv_layers[1])
    me.materials.clear()
    mat = bpy.data.materials.get("troll_body") or bpy.data.materials.new("troll_body")
    mat.use_nodes = True
    obj.data.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
        p.material_index = 0


def normalize_scale(obj, target_height=TARGET_HEIGHT):
    # apply scale first, then measure
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    dims = obj.dimensions
    h = max(dims.z, 0.001)
    f = target_height / h
    log(f"height {h:.2f}m -> scale x{f:.3f} -> {target_height:.1f}m")
    obj.scale = (f, f, f)
    bpy.context.view_layer.update()
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    # sit feet on ground plane
    bpy.context.view_layer.update()
    min_z = min(v.co.z for v in obj.data.vertices)
    obj.location.z -= min_z
    bpy.context.view_layer.update()
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    log("dimensions:", tuple(round(d, 2) for d in obj.dimensions))


def downscale_textures(out_png, size=512):
    saved = False
    for img in bpy.data.images:
        if img.type not in ("IMAGE",):
            continue
        if img.size[0] < 8 or img.size[1] < 8:
            continue
        # skip tiny icons / render results
        if "Render Result" in img.name or "Viewer Node" in img.name:
            continue
        # take the largest image as albedo
        img.scale(size, size)
        img.filepath_raw = out_png
        img.file_format = "PNG"
        img.save()
        log("wrote texture", out_png, img.size[:])
        saved = True
        break  # one material -> one baseTex for 0 A.D.
    if not saved:
        log("WARNING: no source texture found - create troll_body.png manually (512px, power of two)")


def export_dae(obj, out_dae):
    os.makedirs(os.path.dirname(out_dae), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.wm.collada_export(
        filepath=out_dae,
        selected=True,
        include_uv_textures=True,
        include_material_textures=True,
        triangulate=True,
        apply_modifiers=True,
    )
    log("EXPORTED", out_dae)
    # CC-BY credit sidecar (required)
    credit = os.path.join(os.path.dirname(out_dae), "troll_CREDITS.txt")
    with open(credit, "w", encoding="utf-8") as f:
        f.write(
            "Derivative of 'LOTR Cave Troll - (for animating/rigging)' by "
            "Ole Gunnar Isager (@FrenchBaguette), CC-BY 4.0.\n"
            "Source: https://sketchfab.com/3d-models/lotr-cave-troll-for-animatingrigging-20a50af723314c1dac04aad8c929aa1e\n"
            "Changes: decimated ~17.9k -> ~5.5k tris, single material/UV, "
            "rescaled to ~3.6m, 512px baseTex for 0 A.D.\n"
        )
    log("wrote", credit)


def main():
    argv = sys.argv
    args = argv[argv.index("--") + 1:] if "--" in argv else []
    if not args:
        print("Usage: blender --background --python build_troll.py -- <input.gltf|glb|fbx|obj> [target_tris]")
        raise SystemExit(2)
    src = args[0]
    target = int(args[1]) if len(args) > 1 else DEFAULT_TARGET_TRIS
    if not os.path.isfile(src):
        raise SystemExit(f"input not found: {src}\nDownload it manually from Sketchfab (login + accept CC-BY).")

    clear_scene()
    objs = import_source(src)
    troll = join_meshes(objs)
    decimate_to_target(troll, target)
    single_material_uv(troll)
    normalize_scale(troll)

    out_dae = os.path.join(MOD, "art", "meshes", "skeletal", "tolkien", "troll.dae")
    out_png = os.path.join(MOD, "art", "textures", "skins", "skeletal", "tolkien", "troll_body.png")
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    downscale_textures(out_png)
    export_dae(troll, out_dae)
    tris, verts = count_tris(troll)
    log(f"DONE tris~{tris} verts={verts}")
    log("NEXT: rig with a biped/elephant skeleton + export idle/walk/attack/death .dae anims,")
    log("then point tolkien/art/actors/units/mordor/infantry_troll.xml at skeletal/tolkien/troll.dae")


if __name__ == "__main__":
    main()
