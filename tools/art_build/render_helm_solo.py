"""Solo check: converted helm from front (+Y) and side (+X), with axes marker."""
import bpy
import math
import os
from mathutils import Euler

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MOD = os.path.join(ROOT, "tolkien")
DAE = os.path.join(MOD, "art", "meshes", "props", "new", "erebor_helm.dae")
TEX = os.path.join(MOD, "art", "textures", "skins", "props", "helmet",
                   "erebor_helm.png")
OUT = os.path.join(ROOT, "previews", "helm_solo.png")


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.collada_import(filepath=DAE)
    helm = next(o for o in bpy.data.objects if o.type == "MESH")
    xs = [v.co.x for v in helm.data.vertices]
    ys = [v.co.y for v in helm.data.vertices]
    zs = [v.co.z for v in helm.data.vertices]
    print(f"[solo] local X[{min(xs):.2f},{max(xs):.2f}] "
          f"Y[{min(ys):.2f},{max(ys):.2f}] Z[{min(zs):.2f},{max(zs):.2f}]")
    mat = bpy.data.materials.new("solo_m")
    mat.use_nodes = True
    nt = mat.node_tree
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(TEX)
    nt.links.new(tex.outputs["Color"],
                 nt.nodes.get("Principled BSDF").inputs["Base Color"])
    helm.data.materials.clear()
    helm.data.materials.append(mat)
    # duplicate for side slot
    bpy.ops.object.select_all(action="DESELECT")
    helm.select_set(True)
    bpy.context.view_layer.objects.active = helm
    bpy.ops.object.duplicate()
    side = bpy.context.selected_objects[0]
    side.location.x += 1.6
    side.rotation_euler = Euler((0, 0, math.radians(-90)), "XYZ")  # +X flank to camera
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "FLAT"
    sc.display.shading.color_type = "TEXTURE"
    sc.display.shading.show_cavity = True
    sc.render.resolution_x = 800
    sc.render.resolution_y = 400
    cam_data = bpy.data.cameras.new("cam")
    cam = bpy.data.objects.new("cam", cam_data)
    bpy.context.collection.objects.link(cam)
    sc.camera = cam
    cam_data.lens = 60
    cam.location = (0.8, -3.2, 0.45)
    cam.rotation_euler = Euler((math.radians(82), 0, 0), "XYZ")
    sun_d = bpy.data.lights.new("sun", "SUN")
    sun_d.energy = 3.0
    sun = bpy.data.objects.new("sun", sun_d)
    bpy.context.collection.objects.link(sun)
    sc.render.filepath = OUT
    bpy.ops.render.render(write_still=True)
    print("SOLO DONE (left=front +Y view, right=side +X view)")


if __name__ == "__main__":
    main()
