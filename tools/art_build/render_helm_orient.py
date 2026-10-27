"""Orient check: render the LP helmet source from 4 yaw angles in one image."""
import bpy
import math
import os

SRC = os.environ.get("DWARF_HELMET_SOURCE_MODEL")
if not SRC:
    raise RuntimeError("Set DWARF_HELMET_SOURCE_MODEL to the downloaded helmet GLB")
OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "previews", "helm_orient.png")


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=SRC, merge_vertices=True)
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    xs = [v.co.x for o in meshes for v in o.data.vertices]
    ys = [v.co.y for o in meshes for v in o.data.vertices]
    zs = [v.co.z for o in meshes for v in o.data.vertices]
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    cz = (max(zs) + min(zs)) / 2
    r = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    print(f"[orient] src X[{min(xs):.2f},{max(xs):.2f}] "
          f"Y[{min(ys):.2f},{max(ys):.2f}] Z[{min(zs):.2f},{max(zs):.2f}]")
    for o in meshes:
        o.location.x -= cx
        o.location.y -= cy
        o.location.z -= cz
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
    cam_data.lens = 60
    # camera fixed on -Y, rotate the HELMET copies instead: one row, 4 yaw
    # slots at x = -1.5r, -0.5r, +0.5r, +1.5r with yaw 0/90/180/270
    for i, yaw in enumerate((0, 90, 180, 270)):
        bpy.ops.object.select_all(action="DESELECT")
        for o in meshes:
            o.select_set(True)
        bpy.ops.object.duplicate()
        dupes = [o for o in bpy.context.selected_objects]
        for o in dupes:
            o.location.x += -1.5 * r + i * r
            o.rotation_euler[2] += math.radians(yaw)
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:  # hide originals at center
        o.hide_render = True
    cam.location = (0, -10 * r, 0.5 * r)
    from mathutils import Euler
    cam.rotation_euler = Euler((math.radians(87), 0, 0), "XYZ")
    sun_d = bpy.data.lights.new("sun", "SUN")
    sun_d.energy = 3.0
    sun = bpy.data.objects.new("sun", sun_d)
    bpy.context.collection.objects.link(sun)
    sc.render.filepath = OUT
    bpy.ops.render.render(write_still=True)
    print("ORIENT RENDER DONE (slots: yaw 0/90/180/270 left to right)")


if __name__ == "__main__":
    main()
