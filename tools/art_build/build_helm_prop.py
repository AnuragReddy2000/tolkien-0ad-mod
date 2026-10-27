"""
Convert a Sketchfab helmet (static prop) to a 0 A.D. helmet prop.

NO rigging, NO animation - static props skip 90% of the character pipeline:
bake transforms -> cleanup -> decimate -> single material/UV -> scale into
the helmet-bone frame -> export DAE + prop actor XML + CREDITS.

Frame (prop origin = helmet bone, cf. celt_coolus_01 reference):
  geometry must span roughly Z 0.0..0.77, X +/-0.30 (see build_erebor_poc).

USAGE (Blender 3.0 headless):
  blender --background --python tools\\art_build\\build_helm_prop.py -- ^
    <helmet.glb|dae|fbx|obj> [prop_name] [target_height] [target_tris] [rot_z_deg]

  prop_name default: erebor_helm  (writes art/meshes/props/new/<name>.dae,
    art/actors/props/units/helmets/<name>.xml, *_CREDITS.txt)
  target_height default 0.75 (helmet-bone frame top incl. crest/knob)
  target_tris default 1500
  rot_z_deg default 0 (Sketchfab forwards vary; check the preview, adjust)

Example (surrogate test, no login needed):
  blender --background --python tools\\art_build\\build_helm_prop.py -- ^
    %TEMP%\\0ad_ref\\ref_helm\\celt_coolus_01.dae test_coolus

Real asset (user downloads first - Sketchfab needs login + license click):
  https://sketchfab.com/3d-models/dwarf-helmet-lp-6196f83b8dc7416583f6197df9f09177
  by prorok_009, CC-BY 4.0. Prefer GLB, 1k textures (512px is our target).
  Drop it anywhere and pass the path as arg 1.
"""
import bpy
import math
import os
import sys

MOD = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "tolkien"))

SOURCE = {
    "author": "prorok_009",
    "title": "Dwarf_Helmet_LP",
    "url": "https://sketchfab.com/3d-models/dwarf-helmet-lp-6196f83b8dc7416583f6197df9f09177",
    "license": "CC-BY 4.0",
}


def log(*a):
    print("[helm-prop]", *a)


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_any(path):
    ext = os.path.splitext(path)[1].lower()
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
        raise SystemExit(f"unsupported extension {ext}")
    return [o for o in bpy.data.objects if o not in before]


def base_image_of(obj):
    if obj.type != "MESH" or not len(obj.data.materials):
        return None
    mat = obj.data.materials[0]
    if mat is None or not mat.use_nodes:
        return None
    for link in mat.node_tree.links:
        if (link.to_node.type == "BSDF_PRINCIPLED"
                and link.to_socket.name == "Base Color"
                and link.from_node.type == "TEX_IMAGE"
                and link.from_node.image is not None):
            return link.from_node.image
    return None


def save_image_512(src_img, out_png):
    """Downsample any source image to a 512px PNG (nearest neighbour)."""
    w, h = src_img.size[0], src_img.size[1]
    px = [0.0] * (w * h * 4)
    src_img.pixels.foreach_get(px)
    S = 512
    buf = [0.0] * (S * S * 4)
    for yy in range(S):
        sy = min(int(yy * h / S), h - 1) * w * 4
        do = yy * S * 4
        for xx in range(S):
            so = sy + min(int(xx * w / S), w - 1) * 4
            buf[do] = px[so]
            buf[do + 1] = px[so + 1]
            buf[do + 2] = px[so + 2]
            buf[do + 3] = 1.0
            do += 4
    out = bpy.data.images.new("helm_tex", S, S)
    out.pixels.foreach_set(buf)
    out.filepath_raw = out_png
    out.file_format = "PNG"
    out.save()
    bpy.data.images.remove(out)
    log(f"texture {w}x{h} -> 512px {out_png}")


def main():
    argv = sys.argv
    args = argv[argv.index("--") + 1:] if "--" in argv else []
    if not args:
        print("Usage: blender --background --python build_helm_prop.py -- "
              "<helmet.glb|dae|fbx|obj> [prop_name] [target_h] [target_tris] [rot_z]")
        raise SystemExit(2)
    src = args[0]
    name = args[1] if len(args) > 1 else "erebor_helm"
    target_h = float(args[2]) if len(args) > 2 else 0.75
    target_tris = int(args[3]) if len(args) > 3 else 1500
    rot_z = float(args[4]) if len(args) > 4 else 0.0
    # vertical ride height: LP-style deep skirts bury the eyes unless the
    # whole shell rides up (erebor_helm: eyes sit ~0.12 below the mask
    # holes at lift 0). Prop origin stays on the helmet bone - only the
    # geometry inside the frame moves.
    lift = float(args[5]) if len(args) > 5 else 0.0
    if not os.path.isfile(src):
        raise SystemExit(f"input not found: {src}")

    clear()
    imported = import_any(src)
    meshes = [o for o in imported if o.type == "MESH"]
    if not meshes:
        raise SystemExit("no meshes in source file")
    log(f"imported {len(meshes)} mesh(es): "
        + ", ".join(f"{o.name}({len(o.data.vertices)}v)" for o in meshes))

    # drop armatures/cameras/lights EMPTY props can't use; strip vertex
    # groups (static prop, no skinning)
    # drop non-mesh imports only AFTER their transforms are baked into the
    # meshes (parent_clear below) - deleting parent EMPTYs first orphans
    # the parts and silently discards the assembly (this shipped a
    # scrambled, effectively unyawed helm: face sideways, knot-cross out).
    for o in meshes:
        for m in list(o.modifiers):
            if m.type == "ARMATURE":
                o.modifiers.remove(m)
    # NOTE: do NOT assign o.parent = None here - that silently DISCARDS the
    # parent EMPTY-node assembly transforms (mask/beard offsets live there).
    # parent_clear(KEEP_TRANSFORM) in the bake step below preserves them.

    # pick texture BEFORE joining: largest base-color image wins
    donor = None
    donor_px = 0
    for o in meshes:
        img = base_image_of(o)
        if img is not None:
            px = img.size[0] * img.size[1]
            if px > donor_px:
                donor, donor_px = img, px
    if donor is not None:
        log(f"texture donor: {donor.name} {donor.size[0]}x{donor.size[1]}")

    # bake assembly transforms (multi-part sources position parts via
    # object/node transforms - join() would scramble them otherwise)
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    if meshes:
        bpy.context.view_layer.objects.active = meshes[0]
        bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    for o in meshes:
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=True, rotation=True,
                                       scale=True)
    # assembly baked into verts: NOW safe to purge non-mesh imports
    # (empties/cameras/lights) so join/export see only the prop
    for o in imported:
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    if rot_z:
        log(f"rot_z={rot_z}deg will yaw verts pre-scale (see orient step)")

    # join multi-part sources (origins already baked -> no frame shift)
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    helm = bpy.context.view_layer.objects.active
    helm.name = name

    # orient at vert level right after join (BEFORE decimate: collapse
    # symmetry assumes X-symmetry, which only holds post-yaw).
    # Object-level rotate+apply proved fragile (glTF QUATERNION mode and
    # parent-EMPTY assembly each caused a silent no-op); vert math cannot
    # be ignored.
    if rot_z:
        import numpy as _np
        a = math.radians(rot_z)
        ca, sa = math.cos(a), math.sin(a)
        _n = len(helm.data.vertices)
        _arr = _np.empty(_n * 3, dtype=_np.float32)
        helm.data.vertices.foreach_get("co", _arr)
        _arr = _arr.reshape(_n, 3)
        _x = _arr[:, 0].copy()
        _y = _arr[:, 1].copy()
        _arr[:, 0] = _x * ca - _y * sa
        _arr[:, 1] = _x * sa + _y * ca
        helm.data.vertices.foreach_set("co", _arr.ravel())
        helm.data.update()
        log(f"yawed verts by {rot_z}deg")

    # cleanup + decimate to budget
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=0.0001)
    bpy.ops.mesh.delete_loose()
    bpy.ops.object.mode_set(mode="OBJECT")
    me = helm.data
    tris = sum(max(len(p.vertices) - 2, 1) for p in me.polygons)
    log(f"source ~{tris} tris, {len(me.vertices)} verts")
    passes = 0
    while tris > target_tris and passes < 8:
        ratio = max(target_tris / max(tris, 1), 0.25)
        mod = helm.modifiers.new("Decimate", "DECIMATE")
        mod.decimate_type = "COLLAPSE"
        mod.ratio = ratio
        mod.use_collapse_triangulate = True
        mod.use_symmetry = True
        bpy.ops.object.select_all(action="DESELECT")
        helm.select_set(True)
        bpy.context.view_layer.objects.active = helm
        bpy.ops.object.modifier_apply(modifier=mod.name)
        me = helm.data
        tris = sum(max(len(p.vertices) - 2, 1) for p in me.polygons)
        passes += 1
    log(f"decimated -> ~{tris} tris in {passes} passes (target {target_tris})")

    # finish: triangulate, normals, single UV + single material
    bpy.ops.object.select_all(action="DESELECT")
    helm.select_set(True)
    bpy.context.view_layer.objects.active = helm
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.delete_loose()
    bpy.ops.mesh.quads_convert_to_tris(quad_method="BEAUTY",
                                       ngon_method="BEAUTY")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    if not helm.data.uv_layers:
        bpy.ops.uv.cube_project(cube_size=1.0)
    bpy.ops.object.mode_set(mode="OBJECT")
    while len(helm.data.uv_layers) > 1:
        helm.data.uv_layers.remove(helm.data.uv_layers[1])
    helm.data.materials.clear()
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    helm.data.materials.append(mat)
    for p in helm.data.polygons:
        p.material_index = 0
        p.use_smooth = True

    # scale into the helmet-bone frame: uniform scale by height, center
    # XY on origin, base slightly above 0 (sits on the skull, not in it).
    # (Yaw already applied at vert level right after join.)
    xs = [v.co.x for v in helm.data.vertices]
    ys = [v.co.y for v in helm.data.vertices]
    zs = [v.co.z for v in helm.data.vertices]
    h = max(max(zs) - min(zs), 1e-6)
    f = target_h / h
    cx, cy, z0 = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, min(zs)
    for v in helm.data.vertices:
        v.co = ((v.co.x - cx) * f, (v.co.y - cy) * f,
                (v.co.z - z0) * f + 0.02 + lift)
    xs = [v.co.x for v in helm.data.vertices]
    ys = [v.co.y for v in helm.data.vertices]
    zs = [v.co.z for v in helm.data.vertices]
    log(f"helm frame X[{min(xs):.2f},{max(xs):.2f}] "
        f"Y[{min(ys):.2f},{max(ys):.2f}] Z[{min(zs):.2f},{max(zs):.2f}] "
        f"(want X~+/-0.30 Z~0.0..0.77)")
    if min(zs) < -0.05 or max(zs) > 0.90 or max(abs(min(xs)), abs(max(xs))) > 0.45:
        raise SystemExit("HELM FRAME VALIDATION FAILED - aborting")

    # texture: donor -> 512px prop texture, else flat iron fallback
    tex_dir = os.path.join(MOD, "art", "textures", "skins", "props", "helmet")
    os.makedirs(tex_dir, exist_ok=True)
    tex_file = f"props/helmet/{name}.png"
    if donor is not None:
        save_image_512(donor, os.path.join(MOD, "art", "textures", "skins",
                                           "props", "helmet", f"{name}.png"))
    else:
        import numpy as _np  # Blender-bundled numpy
        arr = _np.full((512, 512, 3), (0.23, 0.25, 0.27), dtype=_np.float32)
        img = bpy.data.images.new(f"{name}_flat", 512, 512)
        out = _np.ones((512, 512, 4), dtype=_np.float32)
        out[..., :3] = arr
        img.pixels.foreach_set(out.ravel())
        img.filepath_raw = os.path.join(tex_dir, f"{name}.png")
        img.file_format = "PNG"
        img.save()
        bpy.data.images.remove(img)
        log(f"no donor texture - flat iron fallback -> {tex_file}")

    # export mesh
    out_dae = os.path.join(MOD, "art", "meshes", "props", "new", f"{name}.dae")
    os.makedirs(os.path.dirname(out_dae), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    helm.select_set(True)
    bpy.context.view_layer.objects.active = helm
    bpy.ops.wm.collada_export(filepath=out_dae, selected=True)
    log("EXPORTED", out_dae)

    # prop actor XML
    prop_dir = os.path.join(MOD, "art", "actors", "props", "units", "helmets")
    os.makedirs(prop_dir, exist_ok=True)
    with open(os.path.join(prop_dir, f"{name}.xml"), "w",
              encoding="utf-8") as xf:
        xf.write('<?xml version="1.0" encoding="utf-8"?>\n'
                 '<actor version="1">\n'
                 '  <castshadow/>\n'
                 '  <group>\n'
                 f'    <variant frequency="1" name="{name}">\n'
                 f'      <mesh>props/new/{name}.dae</mesh>\n'
                 '      <textures>\n'
                 f'        <texture file="{tex_file}" name="baseTex"/>\n'
                 '        <texture file="default_norm.png" name="normTex"/>\n'
                 '        <texture file="null_black.dds" name="specTex"/>\n'
                 '      </textures>\n'
                 '    </variant>\n'
                 '  </group>\n'
                 '  <material>objectcolor_norm_spec.xml</material>\n'
                 '</actor>\n')
    log(f"wrote prop actor helmets/{name}.xml")

    # credits sidecar (REQUIRED - repo never bundles the download)
    is_real = (name == "erebor_helm")
    with open(os.path.join(os.path.dirname(out_dae), f"{name}_CREDITS.txt"),
              "w", encoding="utf-8") as cf:
        if is_real:
            cf.write(f"Derivative of '{SOURCE['title']}' by {SOURCE['author']}, "
                     f"{SOURCE['license']}.\nSource: {SOURCE['url']}\n"
                     "Changes: baked part transforms, cleanup, decimated to "
                     "troop budget, single material/UV, 512px baseTex, scaled "
                     "into the stock helmet-bone frame (origin = helmet bone).\n"
                     "NOTE: upstream design derives from Weta Workshop film "
                     "concepts (author credits them) - review IP comfort "
                     "before release; swap path documented in actor XML.\n")
        else:
            cf.write(f"POC/surrogate prop '{name}' converted from {src} for "
                     "pipeline testing only.\n")
    log("POC HELM BUILD DONE")


if __name__ == "__main__":
    main()
