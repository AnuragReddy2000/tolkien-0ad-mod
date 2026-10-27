"""Part finder: import LP helm with +90 yaw, color parts distinctly, front view."""
import bpy
import math
import os
from mathutils import Euler

SRC = os.environ.get("DWARF_HELMET_SOURCE_MODEL")
if not SRC:
    raise RuntimeError("Set DWARF_HELMET_SOURCE_MODEL to the downloaded helmet GLB")
OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "previews", "helm_parts_view.png")


def flat(name, rgba):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    tex = m.node_tree.nodes.new("ShaderNodeTexImage")
    img = bpy.data.images.new(name + "_img", 4, 4)
    img.pixels.foreach_set(list(rgba) * 16)
    tex.image = img
    m.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return m


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=SRC, merge_vertices=True)
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
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
        o.rotation_mode = "XYZ"  # glTF may leave QUATERNION: euler writes silently do nothing
        o.rotation_euler[2] += math.radians(90)
    bpy.context.view_layer.update()
    for o in meshes:
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=False, rotation=True,
                                       scale=False)
    colors = {"beard": (0.1, 0.3, 0.9, 1.0), "mask": (0.9, 0.1, 0.1, 1.0)}
    for o in meshes:
        key = "beard" if "beard" in o.name.lower() else (
            "mask" if "mask" in o.name.lower() else None)
        if key:
            o.data.materials.clear()
            o.data.materials.append(flat("p_" + key, colors[key]))
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
    cam_data.lens = 50
    cam.location = (0, -5.5, 0.2)
    cam.rotation_euler = Euler((math.radians(88), 0, 0), "XYZ")
    sun_d = bpy.data.lights.new("sun", "SUN")
    sun_d.energy = 3.0
    sun = bpy.data.objects.new("sun", sun_d)
    bpy.context.collection.objects.link(sun)
    sc.render.filepath = OUT
    bpy.ops.render.render(write_still=True)
    print("PARTS DONE (blue=beard mesh, red=mask mesh, textured=dome)")


if __name__ == "__main__":
    main()
