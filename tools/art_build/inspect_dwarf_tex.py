"""Analyze the Moria/Erebor unit textures + prop UV layouts to plan recolors.

GPU-free headless inspection:
  blender --background --python tools/art_build/inspect_dwarf_tex.py
"""
import bpy
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, "..", "..", "tolkien"))

PNGS = [
    ("skeletal/tolkien/moria_cloth_01.png", "cloth"),
    ("skeletal/tolkien/moria_iron_01.png", "iron"),
    ("skeletal/tolkien/moria_leather_01.png", "leather"),
    ("skeletal/tolkien/erebor_iron_01.png", "erebor_iron"),
    ("props/helmet/erebor_helm.png", "helm"),
    ("props/head/erebor_face_a.png", "face"),
]

DAES = [
    ("art/meshes/props/new/erebor_helm.dae", "helm"),
    ("art/meshes/props/new/erebor_beard.dae", "beard"),
    ("art/meshes/props/new/erebor_head.dae", "head"),
]


def load_rgba(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    arr = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(arr)
    bpy.data.images.remove(img)
    return arr.reshape(h, w, 4), w, h


def srgb2lin(c):
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def quant_stats(arr, tag, w):
    """quantized rgb histogram in srgb, top 16 bins."""
    rgb = arr[..., :3] / max(arr.max() if arr.max() > 1e-6 else 1, 1)
    rgb = rgb * (arr.max() if arr.max() > 1e-6 else 1)
    rgb = arr[..., :3].copy()
    q = (rgb * 40).astype(int)
    key = q[..., 0] * 41 * 41 + q[..., 1] * 41 + q[..., 2]
    ids, cnts = np.unique(key, return_counts=True)
    order = np.argsort(cnts)[::-1][:16]
    print(f"[{tag}] {w}x{arr.shape[1]} px={arr.shape[0]*arr.shape[1]} "
          f"buckets={len(ids)}")
    for o in order:
        k = ids[o]
        r, gg, b = k // (41 * 41), (k // 41) % 41, k % 41
        print(f"   ({r/40:5.2f},{gg/40:5.2f},{b/40:5.2f}) "
              f"-> {cnts[o]/arr.shape[0]/arr.shape[1]*100:5.1f}%")
    # sRGB luminance extremes summary
    lum = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    print(f"   lum range {lum.min():.3f}..{lum.max():.3f} mean {lum.mean():.3f}")


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    texd = os.path.join(MOD, "art", "textures", "skins")
    for rel, tag in PNGS:
        p = os.path.join(texd, rel)
        if not os.path.isfile(p):
            print(f"[{tag}] MISSING {p}")
            continue
        a, w, h = load_rgba(p)
        quant_stats(a, tag, w)

    # prop UV coverage: does the beard share texel space with face skin?
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for rel, tag in DAES:
        p = os.path.join(MOD, rel)
        if not os.path.isfile(p):
            print(f"[{tag}] MISSING {p}")
            continue
        before = set(bpy.data.objects)
        bpy.ops.wm.collada_import(filepath=p)
        new = [o for o in bpy.data.objects if o not in before]
        meshes = [o for o in new if o.type == "MESH"]
        for m in meshes:
            me = m.data
            uvl = me.uv_layers[0] if me.uv_layers else None
            if uvl:
                uv = np.array([tuple(uvl.data[li].uv)
                               for poly in me.polygons
                               for li in poly.loop_indices])
                u0, v0 = uv.min(axis=0)
                u1, v1 = uv.max(axis=0)
                print(f"[{tag}-uv] mesh={m.name} "
                      f"U[{u0:.3f},{u1:.3f}] V[{v0:.3f},{v1:.3f}] "
                      f"verts={len(me.vertices)} tris={len(me.polygons)}")
            else:
                print(f"[{tag}-uv] mesh={m.name} NO U Vs")
        for o in new:
            bpy.data.objects.remove(o, do_unlink=True)

    print("TEX INSPECT DONE")


if __name__ == "__main__":
    main()
