"""Cave orientation strip v2: 8 yaws, guaranteed framing."""
import bpy
import math
from mathutils import Euler

SRC = os.environ.get("CAVE_ENTRANCE_SOURCE_MODEL")
if not SRC:
    raise RuntimeError("Set CAVE_ENTRANCE_SOURCE_MODEL to the downloaded cave entrance GLB")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "previews", "cave_8view.png")


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=SRC, merge_vertices=True)
    src_meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "FLAT"
    sc.display.shading.color_type = "TEXTURE"
    sc.display.shading.show_cavity = True
    sc.render.resolution_x = 2400
    sc.render.resolution_y = 300
    for i in range(8):
        yaw = i * 45
        bpy.ops.object.select_all(action="DESELECT")
        for o in src_meshes:
            o.select_set(True)
        bpy.context.view_layer.objects.active = src_meshes[0]
        bpy.ops.object.duplicate()
        dupes = list(bpy.context.selected_objects)
        print(f"[strip] slot {i} yaw {yaw}: {len(dupes)} dupes")
        for o in dupes:
            o.location.x = -10.5 + i * 3.0
            o.location.y = 0.0
            o.location.z = 0.0
            o.rotation_mode = "XYZ"
            o.rotation_euler = Euler((0, 0, math.radians(yaw)), "XYZ")
    for o in src_meshes:
        o.hide_render = True
    bpy.context.view_layer.update()
    camd = bpy.data.cameras.new("cam")
    cam = bpy.data.objects.new("cam", camd)
    bpy.context.collection.objects.link(cam)
    sc.camera = cam
    camd.lens = 40
    cam.location = (0, -14, 1.5)
    cam.rotation_euler = Euler((math.radians(84), 0, 0), "XYZ")
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    bpy.context.collection.objects.link(sun)
    sc.render.filepath = OUT
    bpy.ops.render.render(write_still=True)
    print("CAVE8 DONE (slots yaw 0,45,...,315 left to right)")


if __name__ == "__main__":
    main()
