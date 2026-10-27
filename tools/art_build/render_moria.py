"""Moria stout roster preview (Blender 3.0 headless): 6 units, front + 3/4."""
import bpy
import math
import os
import runpy
from mathutils import Euler

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, "..", "..", "tolkien"))
OUT = os.path.normpath(os.path.join(HERE, "..", "..", "previews"))
LEAN = Euler((math.radians(8), 0, 0), "XYZ")


def main():
    base = runpy.run_path(os.path.join(HERE, "render_doriath.py"))
    base["MOD"] = MOD
    base["OUT"] = OUT
    base["clear"]()

    iron = bpy.data.materials.new("moria_iron")
    iron.use_nodes = True
    iron.node_tree.nodes["Principled BSDF"].inputs[
        "Base Color"].default_value = (0.20, 0.16, 0.12, 1)
    wood = bpy.data.materials.new("moria_wood")
    wood.use_nodes = True
    wood.node_tree.nodes["Principled BSDF"].inputs[
        "Base Color"].default_value = (0.18, 0.10, 0.045, 1)

    skel = os.path.join(MOD, "art", "meshes", "skeletal", "tolkien")
    texd = os.path.join(MOD, "art", "textures", "skins", "skeletal", "tolkien")
    head_dae = os.path.join(MOD, "art", "meshes", "props", "new",
                            "erebor_head.dae")
    beard_dae = os.path.join(MOD, "art", "meshes", "props", "new",
                             "erebor_beard.dae")
    helm_dae = os.path.join(MOD, "art", "meshes", "props", "new",
                            "erebor_helm.dae")
    face = os.path.join(MOD, "art", "textures", "skins", "props", "head",
                        "erebor_face_a.png")
    helm_tex = os.path.join(MOD, "art", "textures", "skins", "props",
                            "helmet", "erebor_helm.png")
    BODIES = {
        "armor": os.path.join(skel, "erebor_dwarf_stout.dae"),
        "pants": os.path.join(skel, "moria_dwarf_stout_pants.dae"),
        "tunic": os.path.join(skel, "moria_dwarf_stout_tunic.dae"),
    }
    TEX = {
        "iron": os.path.join(texd, "moria_iron_01.png"),
        "leather": os.path.join(texd, "moria_leather_01.png"),
        "cloth": os.path.join(texd, "moria_cloth_01.png"),
    }

    def place_unit(bodykey, texkey, x, helm, weapon):
        before = set(bpy.data.objects)
        bpy.ops.wm.collada_import(
            filepath=BODIES[bodykey])
        new = [o for o in bpy.data.objects if o not in before]
        mesh = max((o for o in new if o.type == "MESH"),
                   key=lambda o: len(o.data.vertices))
        darms = [o for o in new if o.type == "ARMATURE"]
        arm = max(darms, key=lambda o: len(o.data.bones)) if darms else None
        base["set_tex"](mesh, TEX[texkey])
        if arm:
            arm.location.x = x
            _hb = arm.data.bones.get("head")
            _hm = arm.data.bones.get("helmet")
            hb = _hb.head_local if _hb is not None else None
            hm = _hm.head_local if _hm is not None else None
        else:
            hb = hm = None
        head = base["add_head"](mesh, head_dae, x)
        base["set_tex"](head, face)
        if hb is not None:
            head.location = (arm.location[0] + hb[0],
                             arm.location[1] + hb[1],
                             arm.location[2] + hb[2])
            head.rotation_euler = LEAN
        bb = set(bpy.data.objects)
        bpy.ops.wm.collada_import(filepath=beard_dae)
        beard = next(o for o in bpy.data.objects
                     if o not in bb and o.type == "MESH")
        base["set_tex"](beard, face)
        beard.location = (head.location[0], head.location[1],
                          head.location[2])
        beard.rotation_euler = head.rotation_euler
        if helm and hm is not None:
            hb2 = set(bpy.data.objects)
            bpy.ops.wm.collada_import(filepath=helm_dae)
            hmsh = next(o for o in bpy.data.objects
                        if o not in hb2 and o.type == "MESH")
            base["set_tex"](hmsh, helm_tex)
            hmsh.location = (arm.location[0] + hm[0],
                             arm.location[1] + hm[1],
                             arm.location[2] + hm[2])
            hmsh.rotation_euler = head.rotation_euler
        weapon(x)

    axe = lambda x: base["place"](
        base["make_elfsword"]("moria_axe", iron),
        (x - 0.82, -0.19, 2.08), rot=(0, 20, 0))
    sword = lambda x: base["place"](
        base["make_elfsword"]("moria_sword", iron),
        (x - 0.82, -0.19, 2.08), rot=(0, 20, 0))

    def spear(x):
        pair = base["make_spear"]("moria_spear", wood, iron)
        pair[0].location = (x - 0.8, -0.25, 0.95)
        pair[1].location = (x - 0.8, -0.25, 2.0)

    none = lambda x: None

    # worker, spearman, dwarf(axeman), guardsman, archer, ranger
    # (archer preview carries no stand-in: in-game actor uses the stock bow)
    place_unit("tunic", "cloth", 0, False, none)
    place_unit("pants", "leather", 3.2, True, spear)
    place_unit("armor", "iron", 6.4, True, axe)
    place_unit("armor", "iron", 9.6, True, sword)
    place_unit("armor", "leather", 12.8, False, none)
    place_unit("pants", "leather", 16.0, False, axe)

    cam_data = bpy.data.cameras.new("cam")
    cam = bpy.data.objects.new("cam", cam_data)
    base["link"](cam)
    bpy.context.scene.camera = cam
    base["place"](cam, (8.0, -25, 4.6), rot=(87, 0, 0))
    cam_data.lens = 45
    sun_d = bpy.data.lights.new("sun", "SUN")
    sun_d.energy = 3.0
    sun = bpy.data.objects.new("sun", sun_d)
    base["link"](sun)
    base["place"](sun, (8, 0, 10), rot=(50, 0, 30))
    bpy.ops.mesh.primitive_plane_add(size=80, location=(8.0, 0, 0))
    gnd = bpy.context.active_object
    gm = bpy.data.materials.new("gnd")
    gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs[
        "Base Color"].default_value = (0.05, 0.05, 0.05, 1)
    gnd.data.materials.append(gm)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "FLAT"
    sc.display.shading.color_type = "TEXTURE"
    sc.display.shading.show_cavity = True
    sc.render.resolution_x = 1920
    sc.render.resolution_y = 720
    sc.render.filepath = os.path.join(OUT, "moria_units_front.png")
    bpy.ops.render.render(write_still=True)
    base["place"](cam, (20, -27, 7.5), rot=(83, 0, 40))
    cam_data.lens = 36
    sc.render.filepath = os.path.join(OUT, "moria_units_34.png")
    bpy.ops.render.render(write_still=True)
    print("MORIA RENDERS DONE")


if __name__ == "__main__":
    main()
