"""
Moria deep-shaft mine from the Sketchfab iron-mine (Blender 3.0 headless).

The model's timber hut is deleted and replaced by the vanilla Carthaginian
storehouse (Karth-Hadasht stone store), referenced as an actor PROP so no
vanilla mesh is bundled: the prop resolves from the public mod at runtime.
The store is parked in the old hut yard SOUTH-WEST of the mine mouth, clear
of the track and the emerging wagon (the mouth corridor runs north of the
yard), and its open arcade turned west to face the yard.

Static structure: no rig, no anims. Delete hut -> join mine -> per-face UV
remap onto a tiny palette texture (source has NO uvs/images, only 6 flat
materials) -> ore pile tinted mithril-silver -> translate so the yard spot
sits at the origin -> scale -> base Z=0 -> recentre the WHOLE diorama
(mine + store) on the origin so its footprint stays compact -> export DAE
(with an empty node 'prop-yard' as the store attachpoint) + actor +
portrait/icon + credits.

Source (NOT bundled, CC-BY 4.0 by risKris Design):
  https://sketchfab.com/3d-models/iron-mine-v2-lowpoly-b25c0bf08f05474787c8441675bb58a8
  file: ~/Downloads/iron_mine_v2_lowpoly.glb (25 objects, ~4.9k tris)

USAGE:
  blender --background --python tools\\art_build\\build_deep_shaft.py
Outputs (under tolkien/):
  art/meshes/structural/tolkien/deep_shaft.dae
  art/textures/skins/structural/tolkien/deep_shaft.png (8x8 palette)
  art/actors/structures/moria/mine.xml (main mesh + cart-storehouse prop)
  art/textures/ui/session/portraits/structures/moria_mithril_shaft.png
  art/textures/ui/session/icons/structures/moria_mithril_shaft.png
  art/meshes/structural/tolkien/deep_shaft_CREDITS.txt
"""
import bpy
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, "..", "..", "tolkien"))
SRC = os.environ.get("IRON_MINE_SOURCE_MODEL")
if not SRC:
    raise RuntimeError("Set IRON_MINE_SOURCE_MODEL to the downloaded Iron Mine GLB")

SCALE = 3.5          # model unit -> game unit; mine mouth ~9.5u tall,
                     # looming over the storehouse prop
YARD_X, YARD_Y = -4.39, -1.60   # yard/old-hut footprint center (model units)
# Parked Carthaginian storehouse (vanilla footprint 16x16): ~13.3u wide,
# ~13.5u deep, origin-centered. Park spot in model units, chosen so the
# store clears the track (south edge Y=-0.45*-...) and the mountain's
# south band (west face reaches model X=-2.6 only at Y[-2.01,-1.51];
# the store's NE corner must stay west of it).
STORE_X, STORE_Y = -4.60, -2.75
# engine-size half-extents of the kart storehouse (raw dae * node scale)
STORE_HALF_X = 6.65
STORE_HALF_Y = 6.75
STORE_ROT_Z = 3.141592654  # arcade side faces the yard (west), not the rock
PALETTE = [  # (key, linear RGB) -- sRGB baked at write time
    ("cave", (0.0, 0.0, 0.0)),
    ("rock", (0.070, 0.062, 0.042)),
    ("timber_dark", (0.095, 0.037, 0.011)),
    ("timber", (0.173, 0.089, 0.022)),
    ("iron", (0.031, 0.031, 0.029)),
    ("rail", (0.288, 0.288, 0.288)),
    ("mithril", None),  # computed silver below (sRGB direct)
]
MITHRIL_SRGB = (0.75, 0.80, 0.85)
# source material name -> palette index (by Blender material slot order)
MAT2PAL = {
    "BlackCave": 0, "BrownMountain": 1, "Darkwood": 2,
    "Holz": 3, "Material": 4, "Metall": 5,
}

SOURCE = {
    "author": "risKris Design",
    "title": "Iron Mine v2 (LowPoly)",
    "url": "https://sketchfab.com/3d-models/iron-mine-v2-lowpoly-b25c0bf08f05474787c8441675bb58a8",
    "license": "CC-BY 4.0",
}


def log(*a):
    print("[deep-shaft]", *a)


def lin2srgb(c):
    return max(0.0, min(1.0, c ** (1.0 / 2.2)))


def main():
    if not os.path.isfile(SRC):
        raise SystemExit("input not found: %s" % SRC)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=SRC, merge_vertices=True)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    log("imported %d meshes" % len(meshes))

    # bake transforms first (node soup has identity transforms, but be safe)
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

    # drop the timber hut (replaced by the Carthaginian storehouse prop)
    hut = [o for o in meshes if o.name.startswith("Housing")]
    log("removing hut: %s" % [o.name for o in hut])
    for o in hut:
        bpy.data.objects.remove(o, do_unlink=True)
        meshes.remove(o)

    # per-object: record palette index (ore pile -> mithril silver)
    obj_pal = {}
    for o in meshes:
        if o.name.startswith("Ironore"):
            obj_pal[o.name] = 6
            continue
        mats = [m.name if m else "" for m in o.data.materials]
        pal = 1
        for m in mats:
            if m in MAT2PAL:
                pal = MAT2PAL[m]
                break
        obj_pal[o.name] = pal
    log("kept: %s" % [(o.name, obj_pal[o.name]) for o in meshes])

    # palette UVs per object BEFORE join (join merges same-named layers).
    # Each face maps to its palette texel; ore pile -> mithril silver.
    for o in meshes:
        me2 = o.data
        while len(me2.uv_layers):
            me2.uv_layers.remove(me2.uv_layers[0])
        uv2 = me2.uv_layers.new(name="PaletteUV")
        u = (obj_pal[o.name] + 0.5) / 8.0
        for p in me2.polygons:
            for li in p.loop_indices:
                uv2.data[li].uv = (u, 0.5)

    # join
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    mine = bpy.context.view_layer.objects.active
    mine.name = "deep_shaft"

    # cleanup
    bpy.ops.object.select_all(action="DESELECT")
    mine.select_set(True)
    bpy.context.view_layer.objects.active = mine
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=0.0001)
    bpy.ops.mesh.delete_loose()
    bpy.ops.mesh.quads_convert_to_tris(quad_method="BEAUTY",
                                       ngon_method="BEAUTY")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    me = mine.data
    # single palette layer survives the join; drop any extras
    while len(me.uv_layers) > 1:
        me.uv_layers.remove(me.uv_layers[1])
    if not len(me.uv_layers) or me.uv_layers[0].name != "PaletteUV":
        raise SystemExit("palette UV layer lost in join - aborting")

    # translate (yard spot to origin) + scale + base Z=0, then recentre the
    # WHOLE diorama (mine + parked store) on the origin so footprint and
    # obstruction stay compact and cover it
    tx, ty = -YARD_X, -YARD_Y
    for v in me.vertices:
        v.co = ((v.co.x + tx) * SCALE, (v.co.y + ty) * SCALE,
                max(v.co.z, 0.0) * SCALE)
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    log("mine only X[%.2f,%.2f] Y[%.2f,%.2f] Z[%.2f,%.2f]" % (
        min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
    prop_x = (STORE_X + tx) * SCALE
    prop_y = (STORE_Y + ty) * SCALE
    cx0 = min(min(xs), prop_x - STORE_HALF_X)
    cx1 = max(max(xs), prop_x + STORE_HALF_X)
    cy0 = min(min(ys), prop_y - STORE_HALF_Y)
    cy1 = max(max(ys), prop_y + STORE_HALF_Y)
    dx, dy = -(cx0 + cx1) / 2, -(cy0 + cy1) / 2
    for v in me.vertices:
        v.co.x += dx
        v.co.y += dy
    prop_x += dx
    prop_y += dy
    foot_w = math.ceil((cx1 - cx0) / 2.0) * 2
    foot_d = math.ceil((cy1 - cy0) / 2.0) * 2
    log("store park node (%.2f, %.2f); diorama +shift (%.2f, %.2f)" % (
        prop_x, prop_y, dx, dy))
    log("suggest footprint Square width=%.0f depth=%.0f" % (foot_w, foot_d))
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    log("mine final X[%.2f,%.2f] Y[%.2f,%.2f] Z[%.2f,%.2f]" % (
        min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))

    tris = sum(max(len(p.vertices) - 2, 1) for p in me.polygons)
    log("~%d tris, %d verts" % (tris, len(me.vertices)))

    # single engine material
    me.materials.clear()
    mat = bpy.data.materials.get("deep_shaft") or \
        bpy.data.materials.new("deep_shaft")
    mat.use_nodes = True
    me.materials.append(mat)
    for p in me.polygons:
        p.material_index = 0

    # palette texture 8x8 (POT-safe); each column = one palette entry
    texdir = os.path.join(MOD, "art", "textures", "skins", "structural",
                          "tolkien")
    os.makedirs(texdir, exist_ok=True)
    S = 8
    px = [0.0] * (S * S * 4)
    for i, (key, lin) in enumerate(PALETTE):
        if lin is None:
            r, g, b = MITHRIL_SRGB
        else:
            r, g, b = (lin2srgb(c) for c in lin)
        for y in range(S):
            o = (y * S + i) * 4
            px[o:o + 4] = [r, g, b, 1.0]
    # write palette image (columns = palette entries used by the UVs)
    img = bpy.data.images.new("deep_shaft_pal", S, S)
    img.pixels.foreach_set(px)
    img.filepath_raw = os.path.join(texdir, "deep_shaft.png")
    img.file_format = "PNG"
    img.save()
    log("palette -> structural/tolkien/deep_shaft.png")

    # export mesh + 'prop-yard' attachpoint. The prop node MUST be a CHILD
    # of the mesh node (like vanilla athen_barracks_struct.dae): the
    # converter's static prop-point walk starts at the exported mesh node,
    # so a root-level sibling empty is never harvested.
    meshdir = os.path.join(MOD, "art", "meshes", "structural", "tolkien")
    os.makedirs(meshdir, exist_ok=True)
    out_dae = os.path.join(meshdir, "deep_shaft.dae")
    yard = bpy.data.objects.new("prop-yard", None)
    bpy.context.collection.objects.link(yard)
    yard.parent = mine
    yard.location = (prop_x, prop_y, 0.0)
    yard.rotation_euler = (0.0, 0.0, STORE_ROT_Z)
    bpy.ops.object.select_all(action="DESELECT")
    mine.select_set(True)
    yard.select_set(True)
    bpy.context.view_layer.objects.active = mine
    bpy.ops.wm.collada_export(filepath=out_dae, selected=True)
    log("EXPORTED", out_dae)

    # actor: mine mesh + vanilla Carthaginian storehouse prop on the yard
    actdir = os.path.join(MOD, "art", "actors", "structures", "moria")
    os.makedirs(actdir, exist_ok=True)
    with open(os.path.join(actdir, "mine.xml"), "w",
              encoding="utf-8") as xf:
        xf.write('<?xml version="1.0" encoding="utf-8"?>\n'
                 '<actor version="1">\n'
                 '  <castshadow/>\n'
                 '  <group>\n'
                 '    <variant frequency="1" name="DeepShaftMine">\n'
                 '      <mesh>structural/tolkien/deep_shaft.dae</mesh>\n'
                 '      <props>\n'
                 '        <prop actor="structures/carthaginians/storehouse.xml" attachpoint="yard"/>\n'
                 '      </props>\n'
                 '      <textures>\n'
                 '        <texture file="structural/tolkien/deep_shaft.png" name="baseTex"/>\n'
                 '        <texture file="default_norm.png" name="normTex"/>\n'
                 '        <texture file="null_black.dds" name="specTex"/>\n'
                 '      </textures>\n'
                 '    </variant>\n'
                 '  </group>\n'
                 '  <material>objectcolor_norm_spec.xml</material>\n'
                 '</actor>\n')
    log("wrote actor structures/moria/mine.xml")

    # preview portrait (WORKBENCH flat) for both trees
    mat2 = bpy.data.materials.new("shaft_icon_m")
    mat2.use_nodes = True
    nt = mat2.node_tree
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = bpy.data.images.load(os.path.join(texdir, "deep_shaft.png"))
    nt.links.new(tx.outputs["Color"],
                 nt.nodes.get("Principled BSDF").inputs["Base Color"])
    me.materials.clear()
    me.materials.append(mat2)
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    mix = (min(xs) + max(xs)) / 2
    miy = (min(ys) + max(ys)) / 2
    miz = 2.5
    tgt = bpy.data.objects.new("icon_tgt", None)
    bpy.context.collection.objects.link(tgt)
    tgt.location = (mix, miy, miz)
    camd = bpy.data.cameras.new("icon_cam")
    cam = bpy.data.objects.new("icon_cam", camd)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    camd.lens = 50
    cam.location = (mix - 13.0, miy - 17.0, miz + 5.5)
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
    sc.render.resolution_x = 256
    sc.render.resolution_y = 256
    for sub, name in (("portraits", "moria_mithril_shaft.png"),
                      ("icons", "moria_mithril_shaft.png")):
        d = os.path.join(MOD, "art", "textures", "ui", "session", sub,
                         "structures")
        os.makedirs(d, exist_ok=True)
        sc.render.filepath = os.path.join(d, name)
        bpy.ops.render.render(write_still=True)
    log("portrait+icon rendered")

    meshp = os.path.join(meshdir, "deep_shaft_CREDITS.txt")
    with open(meshp, "w", encoding="utf-8") as cf:
        cf.write("Derivative of '%s' by %s, %s.\nSource: %s\n"
                 "Changes: timber hut objects removed (replaced in-actor by "
                 "vanilla Carthaginian storehouse prop "
                 "structures/carthaginians/storehouse.xml on a 'prop-yard' "
                 "point parked south-west of the mouth, clear of the track "
                 "and wagon); remaining meshes joined; flat materials baked "
                 "to 8x8 palette texture (ore pile tinted mithril-silver); "
                 "translated so the yard spot sits at origin, then the "
                 "whole diorama (mine + store) recentred on its footprint; "
                 "scaled x%.1f; based on Z=0.\n" % (
                     SOURCE["title"], SOURCE["author"], SOURCE["license"],
                     SOURCE["url"], SCALE))
    log("DEEP SHAFT BUILD DONE")


if __name__ == "__main__":
    main()
