"""Inspect a Sketchfab GLB for 0 A.D. adoption (headless Blender).

Usage:
  blender --background --python tools/art_build/inspect_glb.py -- <model>.glb
Reports: meshes/tris/verts, materials, embedded images + sizes, armatures +
bone counts/names, object transforms (unbaked node soup is the classic joined
sprawl trap), scene bounds.
"""
import bpy
import sys


def main(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    bpy.context.view_layer.update()

    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    print("MESHES:", len(meshes), "ARMATURES:", len(arms))
    total_tris = 0
    for o in meshes:
        me = o.data
        tris = sum(len(p.vertices) - 2 for p in me.polygons)
        total_tris += tris
        mats = [m.name if m else None for m in me.materials]
        print("  mesh=%r verts=%d tris=%d mats=%s loc=%s rot=%s scale=%s" % (
            o.name, len(me.vertices), tris, mats,
            tuple(round(v, 3) for v in o.location),
            tuple(round(v, 3) for v in o.rotation_euler),
            tuple(round(v, 3) for v in o.scale)))
    print("TOTAL TRIS:", total_tris)
    print("IMAGES:")
    for img in bpy.data.images:
        print("  %r %dx%d" % (img.name, img.size[0], img.size[1]))
    for a in arms:
        bones = a.data.bones
        print("ARMATURE %r bones=%d" % (a.name, len(bones)))
        print("  ", sorted(b.name for b in bones)[:40])
    allx, ally, allz = [], [], []
    for o in meshes:
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            allx.append(w.x)
            ally.append(w.y)
            allz.append(w.z)
    print("WORLD BOUNDS x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]" % (
        min(allx), max(allx), min(ally), max(ally), min(allz), max(allz)))


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1])
