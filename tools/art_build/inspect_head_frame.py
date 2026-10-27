"""Measure head/beard/helm frames: which way does a dwarf face?

Beard hangs forward past the face plane -> its Y-extremes vs the head mesh
give the front-direction sign. Helmet should share that frame.
  blender --background --python tools/art_build/inspect_head_frame.py
"""
import bpy
import os
import numpy as np

MOD = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "tolkien"))
DAES = [
    ("art/meshes/props/new/erebor_head.dae", "head"),
    ("art/meshes/props/new/erebor_beard.dae", "beard"),
    ("art/meshes/props/new/erebor_helm.dae", "helm"),
]


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for rel, tag in DAES:
        before = set(bpy.data.objects)
        bpy.ops.wm.collada_import(filepath=os.path.join(MOD, rel))
        new = [o for o in bpy.data.objects if o not in before]
        meshes = [o for o in new if o.type == "MESH"]
        for m in meshes:
            co = np.empty(len(m.data.vertices) * 3, dtype=np.float32)
            m.data.vertices.foreach_get("co", co)
            co = co.reshape(-1, 3)
            x0, y0, z0 = co.min(axis=0)
            x1, y1, z1 = co.max(axis=0)
            cz = co.mean(axis=0)
            ys = co[:, 1]
            print(f"[{tag}] mesh={m.name} verts={len(co)}")
            print(f"   X[{x0:.3f},{x1:.3f}] Y[{y0:.3f},{y1:.3f}] "
                  f"Z[{z0:.3f},{z1:.3f}] csv cx={cz[0]:.3f} "
                  f"cy={cz[1]:.3f} breadthY={y1-y0:.3f}")
            # y histogram in 8 bands to see mass split front/back
            hist, _ = np.histogram(ys, bins=8)
            print("   y-band hist:", " ".join(f"{v:4d}" for v in hist))
        for o in new:
            bpy.data.objects.remove(o, do_unlink=True)
    print("HEAD FRAME DONE")


if __name__ == "__main__":
    main()
