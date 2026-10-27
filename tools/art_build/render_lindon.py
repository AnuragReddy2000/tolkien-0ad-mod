import bpy
import math
import os
import numpy as np
from mathutils import Euler

MOD = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tolkien"))
REF = os.environ.get("ZEROAD_REFERENCE_ART")
if not REF:
    raise RuntimeError("Set ZEROAD_REFERENCE_ART to the extracted 0 A.D. public art directory")
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "previews"))


def load_base():
    return __import__("runpy").run_path(os.path.join(os.path.dirname(__file__), "render_doriath.py"))


def main():
    base = load_base()
    base["MOD"] = MOD
    base["OUT"] = OUT
    base["clear"]()
    steel = bpy.data.materials.new("lindon_silver")
    steel.use_nodes = True
    steel.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.38, 0.44, 0.46, 1)
    wood = bpy.data.materials.new("lindon_ash")
    wood.use_nodes = True
    wood.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.18, 0.24, 0.20, 1)
    head_dae = os.path.join(MOD, "art", "meshes", "props", "new", "lindon_head.dae")
    face = os.path.join(MOD, "art", "textures", "skins", "props", "head", "lindon_face_a.png")
    sea_green = os.path.join(MOD, "art", "textures", "skins", "skeletal", "tolkien", "lindon_sea_green_01.png")
    silver = os.path.join(MOD, "art", "textures", "skins", "skeletal", "tolkien", "lindon_silver_01.png")

    body, arm, _ = base["import_body"]("m_armor_tunic_long_sleeves.dae")
    base["set_tex"](body, silver)
    head = base["add_head"](body, head_dae, 0)
    base["set_tex"](head, face)
    sword = base["make_elfsword"]("lindon_sword", steel)
    base["place"](sword, (-0.84, -0.19, 2.16), rot=(0, 20, 0))

    body2, arm2, _ = base["import_body"]("meshes_skeletal_new_m_armor_pants_tunic_short.dae")
    base["set_tex"](body2, sea_green)
    if arm2:
        arm2.location.x = 3
    head2 = base["add_head"](body2, head_dae, 3)
    base["set_tex"](head2, face)
    shaft, blade = base["make_spear"]("lindon_spear", wood, steel)
    shaft.location = (2.2, -0.25, 0.95)
    blade.location = (2.2, -0.25, 2.0)

    body3, arm3, _ = base["import_body"]("m_robe.dae")
    base["set_tex"](body3, sea_green)
    if arm3:
        arm3.location.x = 6
    head3 = base["add_head"](body3, head_dae, 6)
    base["set_tex"](head3, face)
    before = set(bpy.data.objects)
    bpy.ops.wm.collada_import(filepath=os.path.join(REF, "meshes_props_weapons_bow_greek.dae"))
    bow = next(o for o in bpy.data.objects if o not in before and o.type == "MESH")
    base["set_tex"](bow, silver)
    base["place"](bow, (5.3, -0.1, 2.2), rot=(90, 0, 0))

    body4, arm4, _ = base["import_body"]("m_armor_hero_pants_tunic.dae")
    base["set_tex"](body4, silver)
    if arm4:
        arm4.location.x = 9
    head4 = base["add_head"](body4, head_dae, 9)
    base["set_tex"](head4, face)
    guard = base["make_elfsword"]("lindon_guard_blade", steel)
    base["place"](guard, (8.16, -0.19, 2.16), rot=(0, 20, 0))

    cam_data = bpy.data.cameras.new("cam")
    cam = bpy.data.objects.new("cam", cam_data)
    base["link"](cam)
    bpy.context.scene.camera = cam
    base["place"](cam, (4.5, -17, 4.7), rot=(87, 0, 0))
    cam_data.lens = 52
    sun_d = bpy.data.lights.new("sun", "SUN")
    sun_d.energy = 3.0
    sun = bpy.data.objects.new("sun", sun_d)
    base["link"](sun)
    base["place"](sun, (0, 0, 10), rot=(50, 0, 30))
    fill_d = bpy.data.lights.new("fill", "AREA")
    fill_d.energy = 500
    fill = bpy.data.objects.new("fill", fill_d)
    base["link"](fill)
    base["place"](fill, (4, -8, 6), rot=(75, 0, 0))
    bpy.ops.mesh.primitive_plane_add(size=60, location=(4.5, 0, 0))
    ground = bpy.context.active_object
    ground_mat = bpy.data.materials.new("lindon_ground")
    ground_mat.use_nodes = True
    ground_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.035, 0.06, 0.065, 1)
    ground.data.materials.append(ground_mat)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "FLAT"
    scene.display.shading.color_type = "TEXTURE"
    scene.display.shading.show_cavity = True
    scene.render.resolution_x = 1440
    scene.render.resolution_y = 720
    scene.render.filepath = os.path.join(OUT, "lindon_units_front.png")
    bpy.ops.render.render(write_still=True)
    base["place"](cam, (13, -14, 5.8), rot=(83, 0, 40))
    scene.render.filepath = os.path.join(OUT, "lindon_units_34.png")
    bpy.ops.render.render(write_still=True)
    base["place"](cam, (3, -3.6, 4.0), rot=(90, 0, 0))
    cam_data.lens = 85
    scene.render.filepath = os.path.join(OUT, "lindon_heads_closeup.png")
    bpy.ops.render.render(write_still=True)
    verify()


def verify():
    for name in ("lindon_units_front.png", "lindon_units_34.png"):
        path = os.path.join(OUT, name)
        image = bpy.data.images.load(path)
        width, height = image.size
        pixels = np.empty(width * height * 4, dtype=np.float32)
        image.pixels.foreach_get(pixels)
        pixels = pixels.reshape(height, width, 4)
        skin = (pixels[..., 0] > pixels[..., 1] * 1.08) & (pixels[..., 1] > pixels[..., 2] * 1.02)
        print("VERIFY", name, "size", width, height, "skin_pixels", int(skin.sum()))


if __name__ == "__main__":
    main()