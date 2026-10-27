"""Four-view check of the CONVERTED helm: yaw 0/90/180/270 side by side."""
import bpy
import math
import os
from mathutils import Euler

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MOD = os.path.join(ROOT, "tolkien")
DAE = os.path.join(MOD, "art", "meshes", "props", "new", "erebor_helm.dae")
TEX = os.path.join(MOD, "art", "textures", "skins", "props", "helmet",
                   "erebor_helm.png")
OUT = os.path.join(ROOT, "previews", "helm_4view.png")


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.collada_import(filepath=DAE)
    helm = next(o for o in bpy.data.objects if o.type == "MESH")
    mat = bpy.data.materials.new("solo_m")
    mat.use_nodes = True
    nt = mat.node_tree
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(TEX)
    nt.links.new(tex.outputs["Color"],
                 nt.nodes.get("Principled BSDF").inputs["Base Color"])
    helm.data.materials.clear()
    helm.data.materials.append(mat)
    slots = []
    for i, yaw in enumerate((0, 90, 180, 270)):
        bpy.ops.object.select_all(action="DESELECT")
        helm.select_set(True)
        bpy.context.view_layer.objects.active = helm
        bpy.ops.object.duplicate()
        d = bpy.context.selected_objects[0]
        d.location = (-2.4 + i * 1.6, 0, 0)
        d.rotation_euler = Euler((0, 0, math.radians(yaw)), "XYZ")
        slots.append(d)
    helm.hide_render = True
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "FLAT"
    sc.display.shading.color_type = "TEXTURE"
    sc.display.shading.show_cavity = True
    sc.render.resolution_x = 1600
    sc.render.resolution_y = 400
    cam_data = bpy.data.cameras.new("cam")
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.collection.objects.link(cam)
    sc.camera = cam
    cam_data.lens = 50
    cam.location = (0, -8, 0.55)
    cam.rotation_euler = Euler((math.radians(89), 0, 0), "XYZ")
    sun_d = bpy.data.lights.new("sun", "SUN")
    sun_d.energy = 3.0
    sun = bpy.data.objects.new("sun", sun_d)
    bpy.context.collection.objects.link(sun)
    sc.render.filepath = OUT
    bpy.ops.render.render(write_still=True)
    print("4VIEW DONE (slots: base yaw 0/90/180/270 left to right)")


if __name__ == "__main__":
    main()
