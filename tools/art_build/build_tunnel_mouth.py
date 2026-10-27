"""
Moria tunnel mouth from the Sketchfab cave-entrance (Blender 3.0 headless).

Static structure: no rig, no anims. Bake -> cleanup -> light decimate ->
single material/UV (KEEP source UVs: donor rock texture carries the detail)
-> yaw opening to +Y (vert-level, foreach) -> scale to footprint ->
base on Z=0 -> export DAE + actor + portrait icon.

Source (NOT bundled, CC-BY 4.0 by meumh, AI-generated via Meshy):
  https://sketchfab.com/3d-models/cave-entrance-0c1f82288a4046e6919d422c5f16c773
  file: ~/Downloads/cave_entrance.glb (single mesh, 1x1024 texture)

USAGE:
  blender --background --python tools\\art_build\\build_tunnel_mouth.py
Outputs (under tolkien/):
  art/meshes/structural/tolkien/tunnel_mouth.dae
  art/textures/skins/structural/tolkien/tunnel_rock.png
  art/actors/structures/moria/tunnel_entrance.xml (OVERWRITES reskin copy)
  art/textures/ui/session/portraits/structures/moria_tunnel_entrance.png
"""
import bpy
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, "..", "..", "tolkien"))
SRC = os.environ.get("CAVE_ENTRANCE_SOURCE_MODEL")
if not SRC:
    raise RuntimeError("Set CAVE_ENTRANCE_SOURCE_MODEL to the downloaded cave entrance GLB")

TARGET_TRIS = 8000
TARGET_WIDTH = 10.0   # game units; footprint 12x11 leaves a rim
# Source ships the adit in a readable 3/4 orientation (mouth front-left);
# keep as-authored (no yaw): the mound reads from all sides and the icon
# camera below is aimed at the mouth directly.
ROT_Z = 0.0

SOURCE = {
    "author": "meumh",
    "title": "Cave entrance",
    "url": "https://sketchfab.com/3d-models/cave-entrance-0c1f82288a4046e6919d422c5f16c773",
    "license": "CC-BY 4.0",
    "note": "AI-generated via Meshy; generic rock/adit, no film derivation claimed",
}


def log(*a):
    print("[tunnel-mouth]", *a)


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def main():
    if not os.path.isfile(SRC):
        raise SystemExit(f"input not found: {SRC}")
    clear()
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=SRC, merge_vertices=True)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    if not meshes:
        raise SystemExit("no meshes in source")
    log("imported: " + ", ".join(
        f"{o.name}({len(o.data.vertices)}v)" for o in meshes))

    # texture donor BEFORE joining (largest base-color wins)
    donor, donor_px = None, 0
    for o in meshes:
        if not len(o.data.materials):
            continue
        mat = o.data.materials[0]
        if mat is None or not mat.use_nodes:
            continue
        for link in mat.node_tree.links:
            if (link.to_node.type == "BSDF_PRINCIPLED"
                    and link.to_socket.name == "Base Color"
                    and link.from_node.type == "TEX_IMAGE"
                    and link.from_node.image is not None):
                img = link.from_node.image
                if img.size[0] * img.size[1] > donor_px:
                    donor, donor_px = img, img.size[0] * img.size[1]
    if donor is None:
        raise SystemExit("no base-color texture in source - aborting")
    log(f"donor: {donor.name} {donor.size[0]}x{donor.size[1]}")

    # bake assembly transforms; purge non-meshes only AFTER (orphaning
    # parts discards the assembly - learned on the LP helmet)
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    for o in meshes:
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=True, rotation=True,
                                       scale=True)
    for o in [x for x in new if x.type != "MESH"]:
        bpy.data.objects.remove(o, do_unlink=True)
    meshes = [o for o in bpy.data.objects if o.type == "MESH"
              and o in set(meshes)]

    # join, then orient at vert level (operator yaw proved fragile)
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    rock = bpy.context.view_layer.objects.active
    rock.name = "tunnel_mouth"
    import numpy as _np
    if ROT_Z:
        a = math.radians(ROT_Z)
        ca, sa = math.cos(a), math.sin(a)
        _n = len(rock.data.vertices)
        _arr = _np.empty(_n * 3, dtype=_np.float32)
        rock.data.vertices.foreach_get("co", _arr)
        _arr = _arr.reshape(_n, 3)
        _x = _arr[:, 0].copy()
        _y = _arr[:, 1].copy()
        _arr[:, 0] = _x * ca - _y * sa
        _arr[:, 1] = _x * sa + _y * ca
        rock.data.vertices.foreach_set("co", _arr.ravel())
        rock.data.update()
        log(f"yawed {ROT_Z}deg")

    # cleanup + light decimate (NO symmetry: adit breaks it)
    bpy.ops.object.select_all(action="DESELECT")
    rock.select_set(True)
    bpy.context.view_layer.objects.active = rock
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=0.0001)
    bpy.ops.mesh.delete_loose()
    bpy.ops.object.mode_set(mode="OBJECT")
    me = rock.data
    tris = sum(max(len(p.vertices) - 2, 1) for p in me.polygons)
    log(f"source ~{tris} tris, {len(me.vertices)} verts")
    passes = 0
    while tris > TARGET_TRIS and passes < 6:
        ratio = max(TARGET_TRIS / max(tris, 1), 0.5)
        mod = rock.modifiers.new("Decimate", "DECIMATE")
        mod.decimate_type = "COLLAPSE"
        mod.ratio = ratio
        mod.use_collapse_triangulate = True
        mod.use_symmetry = False
        bpy.ops.object.select_all(action="DESELECT")
        rock.select_set(True)
        bpy.context.view_layer.objects.active = rock
        bpy.ops.object.modifier_apply(modifier=mod.name)
        me = rock.data
        tris = sum(max(len(p.vertices) - 2, 1) for p in me.polygons)
        passes += 1
    log(f"decimated -> ~{tris} tris in {passes} passes")

    # finish: triangulate, normals, KEEP source UVs, single material
    bpy.ops.object.select_all(action="DESELECT")
    rock.select_set(True)
    bpy.context.view_layer.objects.active = rock
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.delete_loose()
    bpy.ops.mesh.quads_convert_to_tris(quad_method="BEAUTY",
                                       ngon_method="BEAUTY")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    while len(rock.data.uv_layers) > 1:
        rock.data.uv_layers.remove(rock.data.uv_layers[1])
    if not rock.data.uv_layers:
        raise SystemExit("source has no UVs - aborting (donor needs them)")
    rock.data.materials.clear()
    mat = bpy.data.materials.get("tunnel_rock") or \
        bpy.data.materials.new("tunnel_rock")
    mat.use_nodes = True
    rock.data.materials.append(mat)
    for p in rock.data.polygons:
        p.material_index = 0

    # scale to footprint, center XY, base on Z=0
    xs = [v.co.x for v in rock.data.vertices]
    ys = [v.co.y for v in rock.data.vertices]
    zs = [v.co.z for v in rock.data.vertices]
    w = max(max(xs) - min(xs), 1e-6)
    f = TARGET_WIDTH / w
    cx, cy, z0 = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, min(zs)
    for v in rock.data.vertices:
        v.co = ((v.co.x - cx) * f, (v.co.y - cy) * f, (v.co.z - z0) * f)
    xs = [v.co.x for v in rock.data.vertices]
    ys = [v.co.y for v in rock.data.vertices]
    zs = [v.co.z for v in rock.data.vertices]
    log(f"frame X[{min(xs):.2f},{max(xs):.2f}] "
        f"Y[{min(ys):.2f},{max(ys):.2f}] Z[{min(zs):.2f},{max(zs):.2f}]")
    if abs(min(zs)) > 0.01 or max(zs) > 12.0:
        raise SystemExit("FRAME VALIDATION FAILED - aborting")

    # texture: donor at full 1024 (a 10m structure earns it)
    texdir = os.path.join(MOD, "art", "textures", "skins", "structural",
                          "tolkien")
    os.makedirs(texdir, exist_ok=True)
    sw, sh = donor.size[0], donor.size[1]
    px = [0.0] * (sw * sh * 4)
    donor.pixels.foreach_get(px)
    out = bpy.data.images.new("tunnel_rock", sw, sh)
    out.pixels.foreach_set(px)
    out.filepath_raw = os.path.join(texdir, "tunnel_rock.png")
    out.file_format = "PNG"
    out.save()
    bpy.data.images.remove(out)
    log(f"texture {sw}x{sh} -> structural/tolkien/tunnel_rock.png")

    # portrait icon: beauty shot of the built rock, 256px, dark bg
    mat2 = bpy.data.materials.new("tunnel_icon_m")
    mat2.use_nodes = True
    nt = mat2.node_tree
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = bpy.data.images.load(os.path.join(texdir, "tunnel_rock.png"))
    nt.links.new(tx.outputs["Color"],
                 nt.nodes.get("Principled BSDF").inputs["Base Color"])
    rock.data.materials.clear()
    rock.data.materials.append(mat2)
    tgt = bpy.data.objects.new("icon_tgt", None)
    bpy.context.collection.objects.link(tgt)
    tgt.location = (-0.5, 0.0, 2.0)
    camd = bpy.data.cameras.new("icon_cam")
    cam = bpy.data.objects.new("icon_cam", camd)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    camd.lens = 50
    cam.location = (-7.0, -10.0, 3.5)
    tt = cam.constraints.new(type="TRACK_TO")
    tt.target = tgt
    tt.track_axis = "TRACK_NEGATIVE_Z"
    tt.up_axis = "UP_Y"
    bpy.context.view_layer.update()
    sun = bpy.data.objects.new("icon_sun",
                               bpy.data.lights.new("icon_sun", "SUN"))
    bpy.context.collection.objects.link(sun)
    sun.data.energy = 3.0
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "FLAT"
    sc.display.shading.color_type = "TEXTURE"
    sc.display.shading.show_cavity = True
    sc.render.resolution_x = 256
    sc.render.resolution_y = 256
    portdir = os.path.join(MOD, "art", "textures", "ui", "session",
                           "portraits", "structures")
    os.makedirs(portdir, exist_ok=True)
    sc.render.filepath = os.path.join(portdir, "moria_tunnel_entrance.png")
    bpy.ops.render.render(write_still=True)
    log("portrait icon rendered")
    bpy.data.objects.remove(tgt, do_unlink=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    bpy.data.objects.remove(sun, do_unlink=True)

    # restore single engine material (icon material was preview-only)
    rock.data.materials.clear()
    rock.data.materials.append(
        bpy.data.materials.get("tunnel_rock")
        or bpy.data.materials.new("tunnel_rock"))
    for p in rock.data.polygons:
        p.material_index = 0

    # export mesh
    meshdir = os.path.join(MOD, "art", "meshes", "structural", "tolkien")
    os.makedirs(meshdir, exist_ok=True)
    out_dae = os.path.join(meshdir, "tunnel_mouth.dae")
    bpy.ops.object.select_all(action="DESELECT")
    rock.select_set(True)
    bpy.context.view_layer.objects.active = rock
    bpy.ops.wm.collada_export(filepath=out_dae, selected=True)
    log("EXPORTED", out_dae)

    # actor (rock: no player tint, default norm, black spec)
    actdir = os.path.join(MOD, "art", "actors", "structures", "moria")
    os.makedirs(actdir, exist_ok=True)
    with open(os.path.join(actdir, "tunnel_entrance.xml"), "w",
              encoding="utf-8") as xf:
        xf.write('<?xml version="1.0" encoding="utf-8"?>\n'
                 '<actor version="1">\n'
                 '  <castshadow/>\n'
                 '  <group>\n'
                 '    <variant frequency="1" name="TunnelMouth">\n'
                 '      <mesh>structural/tolkien/tunnel_mouth.dae</mesh>\n'
                 '      <textures>\n'
                 '        <texture file="structural/tolkien/tunnel_rock.png" name="baseTex"/>\n'
                 '        <texture file="default_norm.png" name="normTex"/>\n'
                 '        <texture file="null_black.dds" name="specTex"/>\n'
                 '      </textures>\n'
                 '    </variant>\n'
                 '  </group>\n'
                 '  <material>objectcolor_norm_spec.xml</material>\n'
                 '</actor>\n')
    log("wrote actor structures/moria/tunnel_entrance.xml")
    meshp = os.path.join(meshdir, "tunnel_mouth_CREDITS.txt")
    with open(meshp, "w", encoding="utf-8") as cf:
        cf.write(f"Derivative of '{SOURCE['title']}' by {SOURCE['author']}, "
                 f"{SOURCE['license']}.\nSource: {SOURCE['url']}\n"
                 f"Note: {SOURCE['note']}.\n"
                 "Changes: baked transforms, cleanup, light decimate, single "
                 "material (source UVs kept), 1024px baseTex, mouth yawed to "
                 "+Y, scaled to ~10m footprint, base on Z=0.\n")
    log("TUNNEL BUILD DONE")


if __name__ == "__main__":
    main()
