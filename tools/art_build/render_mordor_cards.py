"""Render Mordor unit cards (256px transparent PNGs) from the 3D models.

Usage (headless, needs this machine's Blender 3.0):
  blender --background --python tools/art_build/render_mordor_cards.py
Output (icons drive the structure-tree cards, portraits the selection panel):
  tolkien/art/textures/ui/session/icons/units/mordor/<name>.png
  tolkien/art/textures/ui/session/portraits/units/mordor/<name>.png
for hero_gothmog, hero_khamul, infantry_troll, and scout_crebain.

Framing is computed from each mesh's bounds (busts for heroes, full body for
beasts). Same lighting/camera rig as render_ent_portrait.py.
"""
import bpy
import os
import math

MOD = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tolkien"))
SRC = os.environ.get("ZEROAD_SOURCE_MOD", "")


def tex_mat(name, texpath):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    texnode = nt.nodes.new("ShaderNodeTexImage")
    texnode.image = bpy.data.images.load(texpath)
    nt.links.new(texnode.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def import_dae(path):
    before = set(bpy.data.objects)
    bpy.ops.wm.collada_import(filepath=path)
    return [o for o in bpy.data.objects if o not in before]


def apply_tex(mesh, texpath, matname):
    mat = tex_mat(matname, texpath)
    mesh.data.materials.clear()
    mesh.data.materials.append(mat)
    for p in mesh.data.polygons:
        p.material_index = 0


def mesh_of(objs):
    ms = [o for o in objs if o.type == "MESH"]
    return max(ms, key=lambda o: len(o.data.vertices))


def armature_of(objs):
    for o in objs:
        if o.type == "ARMATURE":
            return o
    return None


def parent_to_bone(prop_mesh, arm, bone):
    # Collada imports sometimes arrive with a unit-conversion scale (see the
    # inch->meter note in build_orcs.py). Props are game-native meters, so a
    # non-1 import scale would shrink them to specks — normalize it.
    if abs(prop_mesh.scale.x - 1.0) > 1e-6 or abs(prop_mesh.scale.y - 1.0) > 1e-6 \
            or abs(prop_mesh.scale.z - 1.0) > 1e-6:
        print("  normalizing prop import scale:", tuple(round(v, 4) for v in prop_mesh.scale))
        prop_mesh.scale = (1.0, 1.0, 1.0)
    if arm and bone in arm.data.bones:
        prop_mesh.parent = arm
        prop_mesh.parent_type = "BONE"
        prop_mesh.parent_bone = bone
        print("  prop parented to bone:", bone)
    else:
        print("  WARN: bone", bone, "missing — prop left at origin")


def bounds(mesh):
    bpy.context.view_layer.update()
    ws = [mesh.matrix_world @ v.co for v in mesh.data.vertices]
    return ((min(w.x for w in ws), max(w.x for w in ws)),
            (min(w.y for w in ws), max(w.y for w in ws)),
            (min(w.z for w in ws), max(w.z for w in ws)))


def setup_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    cam_d = bpy.data.cameras.new("card_cam")
    cam_d.lens = 50
    cam = bpy.data.objects.new("card_cam", cam_d)
    bpy.context.collection.objects.link(cam)
    sc.camera = cam
    trkc = bpy.data.objects.new("card_target", None)
    bpy.context.collection.objects.link(trkc)
    trk = cam.constraints.new("TRACK_TO")
    trk.target = trkc
    trk.track_axis = "TRACK_NEGATIVE_Z"
    trk.up_axis = "UP_Y"
    sun = bpy.data.lights.new("key", "SUN")
    sun.energy = 5.0
    suno = bpy.data.objects.new("key", sun)
    bpy.context.collection.objects.link(suno)
    suno.rotation_euler = (math.radians(50), 0, math.radians(-35))
    fill = bpy.data.lights.new("fill", "SUN")
    fill.energy = 2.0
    fillo = bpy.data.objects.new("fill", fill)
    bpy.context.collection.objects.link(fillo)
    fillo.rotation_euler = (math.radians(30), 0, math.radians(215))
    world = bpy.data.worlds.new("card_world")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.5
    sc.world = world
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.resolution_x = 256
    sc.render.resolution_y = 256
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.eevee.taa_render_samples = 64
    return sc, cam, trkc


def frame_target(trkc, cam, tx, ty, tz, dist):
    trkc.location = (tx, ty, tz)
    cam.location = (tx + dist * 0.62, ty - dist * 0.72, tz + dist * 0.30)


def render_out(sc, name):
    for sub in ("icons/units/mordor/%s.png" % name,
                "portraits/units/mordor/%s.png" % name):
        out = os.path.join(MOD, "art", "textures", "ui", "session",
                           *sub.split("/"))
        os.makedirs(os.path.dirname(out), exist_ok=True)
        sc.render.filepath = out
        bpy.ops.render.render(write_still=True)
        print("wrote", out, os.path.getsize(out), "bytes")


def M(*parts):
    return os.path.join(MOD, *parts)


def S(*parts):
    if not SRC:
        raise RuntimeError("Set ZEROAD_SOURCE_MOD to the installed 0 A.D. public mod directory")
    return os.path.join(SRC, *parts)


def bounds_union(meshes):
    bpy.context.view_layer.update()
    xs, ys, zs = [], [], []
    for mesh in meshes:
        for v in mesh.data.vertices:
            w = mesh.matrix_world @ v.co
            xs.append(w.x)
            ys.append(w.y)
            zs.append(w.z)
    return ((min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs)))


def card_gothmog(sc, cam, trkc):
    setup_body = import_dae(M("art", "meshes", "skeletal", "tolkien", "darkorc.dae"))
    mesh = mesh_of(setup_body)
    apply_tex(mesh, M("art", "textures", "skins", "skeletal", "tolkien", "urukhai_body.png"),
              "gothmog_m")
    helm = mesh_of(import_dae(S("art", "meshes", "props", "helmet", "gladiator_c.dae")))
    apply_tex(helm, S("art", "textures", "skins", "props", "helmet", "gladiator_03_iron.png"),
              "gothmog_helm_m")
    parent_to_bone(helm, armature_of(setup_body), "helmet")
    (x0, x1), (y0, y1), (z0, z1) = bounds_union([mesh, helm])
    tz = z1 - 0.30 * (z1 - z0)  # helm + face + pauldrons
    frame_target(trkc, cam, (x0 + x1) / 2, (y0 + y1) / 2, tz, 2.4)
    render_out(sc, "hero_gothmog")


def card_khamul(sc, cam, trkc):
    setup_body = import_dae(S("art", "meshes", "skeletal", "new", "m_pants.dae"))
    body_arm = armature_of(setup_body)
    mesh = mesh_of(setup_body)
    apply_tex(mesh, S("art", "textures", "skins", "skeletal", "celt", "tunic_02_01.png"),
              "khamul_m")
    # Shadow face: plain dude head in a dark-ish persian face. The lime head
    # mesh is spiked and its texture is DDS-only; a smooth dark head reads
    # as the Black Rider's shadowed visage at card scale.
    # NOTE: parent to the BODY armature — prop files carry their own.
    head = mesh_of(import_dae(S("art", "meshes", "props", "new", "dude_head.dae")))
    apply_tex(head, S("art", "textures", "skins", "props", "head", "pers_face_a.png"),
              "khamul_head_m")
    parent_to_bone(head, body_arm, "head")
    head.location.z -= 0.12  # seat the chin into the neck
    (x0, x1), (y0, y1), (z0, z1) = bounds_union([mesh, head])
    # Rider meshes run large (~3.8 tall); anchor the bust on the head.
    frame_target(trkc, cam, (x0 + x1) / 2, (y0 + y1) / 2, z1 - 0.55, 2.6)
    render_out(sc, "hero_khamul")


def card_troll(sc, cam, trkc):
    setup_body = import_dae(M("art", "meshes", "skeletal", "tolkien", "troll.dae"))
    mesh = mesh_of(setup_body)
    apply_tex(mesh, M("art", "textures", "skins", "skeletal", "tolkien", "troll_body.png"),
              "troll_m")
    (x0, x1), (y0, y1), (z0, z1) = bounds(mesh)
    print("troll bounds z: %.2f .. %.2f" % (z0, z1))
    tz = z0 + 0.68 * (z1 - z0)  # head + crushing torso
    frame_target(trkc, cam, (x0 + x1) / 2, (y0 + y1) / 2, tz, (z1 - z0) * 1.5)
    render_out(sc, "infantry_troll")


def card_crebain(sc, cam, trkc):
    src = S("art", "meshes", "skeletal", "crow.dae")
    tex = S("art", "textures", "skins", "skeletal", "animal_crow.png")
    spots = [(0.0, 0.0, 0.0, 0.0), (-1.5, 0.6, 0.5, 0.5), (1.5, 0.65, 0.25, -0.4)]
    allx, ally, allz = [], [], []
    for i, (lx, ly, lz, rz) in enumerate(spots):
        objs = import_dae(src)
        mesh = mesh_of(objs)
        mesh.location = (lx, ly, lz)
        mesh.rotation_euler = (0.0, 0.0, rz)
        apply_tex(mesh, tex, "crow_m_%d" % i)
        bpy.context.view_layer.update()
        for v in mesh.data.vertices:
            w = mesh.matrix_world @ v.co
            allx.append(w.x)
            ally.append(w.y)
            allz.append(w.z)
    frame_target(trkc, cam, sum(allx) / len(allx), sum(ally) / len(ally),
                 sum(allz) / len(allz), 4.4)
    render_out(sc, "scout_crebain")


def card_sauron(sc, cam, trkc):
    setup_body = import_dae(M("art", "meshes", "skeletal", "tolkien", "sauron.dae"))
    mesh = mesh_of(setup_body)
    apply_tex(mesh, M("art", "textures", "skins", "skeletal", "tolkien", "sauron_body.png"),
              "sauron_m")
    (x0, x1), (y0, y1), (z0, z1) = bounds(mesh)
    print("sauron bounds z: %.2f .. %.2f" % (z0, z1))
    tz = z1 - 0.30 * (z1 - z0)  # crowned helm + pauldrons + mace shoulder
    frame_target(trkc, cam, (x0 + x1) / 2, (y0 + y1) / 2, tz, 2.6)
    render_out(sc, "hero_sauron")


CARDS = {
    "hero_sauron": card_sauron,
    "hero_gothmog": card_gothmog,
    "hero_khamul": card_khamul,
    "infantry_troll": card_troll,
    "scout_crebain": card_crebain,
}


if __name__ == "__main__":
    import sys
    which = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    for name in which or CARDS:
        print("=== card:", name, "===")
        sc, cam, trkc = setup_scene()  # fresh scene per card, no cleanup needed
        CARDS[name](sc, cam, trkc)
    print("CARDS DONE")
