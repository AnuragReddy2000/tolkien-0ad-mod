import bpy
import math
import os
import runpy
from mathutils import Euler

MOD = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tolkien"))
REF = os.environ.get("ZEROAD_REFERENCE_ART")
if not REF:
    raise RuntimeError("Set ZEROAD_REFERENCE_ART to the extracted 0 A.D. public art directory")
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "previews"))


def main():
    base = runpy.run_path(os.path.join(os.path.dirname(__file__), "render_doriath.py"))
    base["MOD"] = MOD
    base["OUT"] = OUT
    base["clear"]()
    iron = bpy.data.materials.new("erebor_iron")
    iron.use_nodes = True
    iron.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.16, 0.18, 0.19, 1)
    wood = bpy.data.materials.new("erebor_wood")
    wood.use_nodes = True
    wood.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.18, 0.10, 0.045, 1)
    head_dae = os.path.join(MOD, "art", "meshes", "props", "new", "erebor_head.dae")
    beard_dae = os.path.join(MOD, "art", "meshes", "props", "new", "erebor_beard.dae")
    face = os.path.join(MOD, "art", "textures", "skins", "props", "head", "erebor_face_a.png")
    iron_tex = os.path.join(MOD, "art", "textures", "skins", "skeletal", "tolkien", "erebor_iron_01.png")
    leather_tex = os.path.join(MOD, "art", "textures", "skins", "skeletal", "tolkien", "erebor_leather_01.png")

    def dwarf(body_file, texture, x, weapon):
        body, arm, _ = base["import_body"](body_file)
        base["set_tex"](body, texture)
        if arm:
            arm.scale = (1.08, 1.08, 0.86)
            arm.location.x = x
        head = base["add_head"](body, head_dae, x)
        base["set_tex"](head, face)
        beard_before = set(bpy.data.objects)
        bpy.ops.wm.collada_import(filepath=beard_dae)
        beard = next(o for o in bpy.data.objects if o not in beard_before and o.type == "MESH")
        base["set_tex"](beard, os.path.join(MOD, "art", "textures", "skins", "props", "head", "erebor_face_a.png"))
        base["place"](head, (x, -0.06, 3.14), rot=(8, 0, 0))
        base["place"](beard, (x, -0.04, 3.12), rot=(8, 0, 0))
        weapon(x)

    dwarf("meshes_skeletal_new_m_armor_tunic_short.dae", iron_tex, 0,
          lambda x: base["place"](base["make_elfsword"]("erebor_guard_axe", iron), (x - 0.82, -0.19, 2.08), rot=(0, 20, 0)))
    spear = lambda x: (lambda pair: (setattr(pair[0], "location", (x - 0.8, -0.25, 0.95)), setattr(pair[1], "location", (x - 0.8, -0.25, 2.0))))(base["make_spear"]("erebor_spear", wood, iron))
    dwarf("meshes_skeletal_new_m_armor_pants_tunic_short.dae", leather_tex, 3, spear)
    dwarf("meshes_skeletal_new_m_armor_tunic_short.dae", leather_tex, 6,
          lambda x: base["place"](base["make_elfsword"]("erebor_crossbow", iron), (x - 0.82, -0.19, 2.08), rot=(0, 20, 0)))
    dwarf("meshes_skeletal_new_m_armor_pants_tunic_short.dae", iron_tex, 9,
          lambda x: base["place"](base["make_elfsword"]("erebor_champion_axe", iron), (x - 0.82, -0.19, 2.08), rot=(0, 20, 0)))

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
    ground_mat = bpy.data.materials.new("erebor_ground")
    ground_mat.use_nodes = True
    ground_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.055, 0.045, 0.035, 1)
    ground.data.materials.append(ground_mat)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "FLAT"
    scene.display.shading.color_type = "TEXTURE"
    scene.display.shading.show_cavity = True
    scene.render.resolution_x = 1440
    scene.render.resolution_y = 720
    scene.render.filepath = os.path.join(OUT, "erebor_units_front.png")
    bpy.ops.render.render(write_still=True)
    base["place"](cam, (13, -14, 5.8), rot=(83, 0, 40))
    scene.render.filepath = os.path.join(OUT, "erebor_units_34.png")
    bpy.ops.render.render(write_still=True)
    base["place"](cam, (3, -3.6, 3.35), rot=(90, 0, 0))
    cam_data.lens = 85
    scene.render.filepath = os.path.join(OUT, "erebor_heads_closeup.png")
    bpy.ops.render.render(write_still=True)
    print("EREBOR RENDERS DONE")


if __name__ == "__main__":
    main()