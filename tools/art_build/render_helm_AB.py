"""A/B: current helm (left) vs 180-flipped helm (right), front view."""
import bpy
import math
import os
import runpy
from mathutils import Euler

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, "..", "..", "tolkien"))
REF = os.environ.get("ZEROAD_REFERENCE_ART")
if not REF:
    raise RuntimeError("Set ZEROAD_REFERENCE_ART to the extracted 0 A.D. public art directory")
OUT = os.path.normpath(os.path.join(HERE, "..", "..", "previews"))


def dwarf(base, slot_x, helm_dae, helm_tex, iron_tex, head_dae, face,
          beard_dae, stout):
    before = set(bpy.data.objects)
    bpy.ops.wm.collada_import(filepath=stout)
    new = [o for o in bpy.data.objects if o not in before]
    dmesh = max((o for o in new if o.type == "MESH"),
                key=lambda o: len(o.data.vertices))
    darms = [o for o in new if o.type == "ARMATURE"]
    darm = max(darms, key=lambda o: len(o.data.bones)) if darms else None
    base["set_tex"](dmesh, iron_tex)
    if darm:
        darm.location.x = slot_x
    dhead = base["add_head"](dmesh, head_dae, slot_x)
    base["set_tex"](dhead, face)
    if darm is not None and "head" in darm.data.bones:
        hh = darm.data.bones["head"].head_local
        dhead.location = (darm.location[0] + hh[0],
                          darm.location[1] + hh[1],
                          darm.location[2] + hh[2])
    dhead.rotation_euler = Euler((math.radians(8), 0, 0), "XYZ")
    bbefore = set(bpy.data.objects)
    bpy.ops.wm.collada_import(filepath=beard_dae)
    beard = next(o for o in bpy.data.objects
                 if o not in bbefore and o.type == "MESH")
    base["set_tex"](beard, face)
    beard.location = (dhead.location[0], dhead.location[1],
                      dhead.location[2])
    beard.rotation_euler = dhead.rotation_euler
    hbefore = set(bpy.data.objects)
    bpy.ops.wm.collada_import(filepath=helm_dae)
    helm = next(o for o in bpy.data.objects
                if o not in hbefore and o.type == "MESH")
    base["set_tex"](helm, helm_tex)
    if darm is not None and "helmet" in darm.data.bones:
        hb = darm.data.bones["helmet"].head_local
        helm.location = (darm.location[0] + hb[0],
                         darm.location[1] + hb[1],
                         darm.location[2] + hb[2])
    helm.rotation_euler = dhead.rotation_euler


def main():
    base = runpy.run_path(os.path.join(HERE, "render_doriath.py"))
    base["MOD"] = MOD
    base["OUT"] = OUT
    base["clear"]()
    iron = os.path.join(MOD, "art", "textures", "skins", "skeletal",
                        "tolkien", "erebor_iron_01.png")
    head = os.path.join(MOD, "art", "meshes", "props", "new",
                        "erebor_head.dae")
    beard = os.path.join(MOD, "art", "meshes", "props", "new",
                         "erebor_beard.dae")
    face = os.path.join(MOD, "art", "textures", "skins", "props", "head",
                        "erebor_face_a.png")
    stout = os.path.join(MOD, "art", "meshes", "skeletal", "tolkien",
                         "erebor_dwarf_stout.dae")
    ha = os.path.join(MOD, "art", "meshes", "props", "new", "erebor_helm.dae")
    ta = os.path.join(MOD, "art", "textures", "skins", "props", "helmet",
                      "erebor_helm.png")
    hb = os.path.join(MOD, "art", "meshes", "props", "new",
                      "erebor_helm_flip.dae")
    tb = os.path.join(MOD, "art", "textures", "skins", "props", "helmet",
                      "erebor_helm_flip.png")
    dwarf(base, 0, ha, ta, iron, head, face, beard, stout)
    dwarf(base, 3.2, hb, tb, iron, head, face, beard, stout)
    cam_data = bpy.data.cameras.new("cam")
    cam = bpy.data.objects.new("cam", cam_data)
    base["link"](cam)
    bpy.context.scene.camera = cam
    base["place"](cam, (1.6, -14, 3.4), rot=(87, 0, 0))
    cam_data.lens = 50
    sun_d = bpy.data.lights.new("sun", "SUN")
    sun_d.energy = 3.0
    sun = bpy.data.objects.new("sun", sun_d)
    base["link"](sun)
    base["place"](sun, (0, 0, 10), rot=(50, 0, 30))
    bpy.ops.mesh.primitive_plane_add(size=60, location=(1.6, 0, 0))
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
    sc.render.resolution_x = 1280
    sc.render.resolution_y = 720
    sc.render.filepath = os.path.join(OUT, "erebor_helm_AB.png")
    bpy.ops.render.render(write_still=True)
    print("AB DONE (left=current, right=flipped 180)")


if __name__ == "__main__":
    main()
