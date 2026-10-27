import bpy
import numpy as np
import os
import runpy

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tolkien"))


def gen_lindon_face(namespace):
    image = bpy.data.images.load(os.path.join(namespace["REF"], "celt_fem_a.dds"))
    pixels = namespace["img_to_np"](image)[..., :3]
    height, width = pixels.shape[:2]
    sample = pixels[np.ix_(np.arange(128) * height // 128, np.arange(128) * width // 128)]
    h, s, v = namespace["rgb2hsv"](sample)
    hair = 1.0 - namespace["raster_mask"](bpy.data.objects["lindon_head"].data,
                                          set(i for i, p in enumerate(bpy.data.objects["lindon_head"].data.polygons)
                                              if p.center.y < -0.04 or p.center.z >= 0.38), 128)
    for x in range(128):
        hair[:int(24 + 10 * (1.0 - abs(x - 64) / 64.0)), x] = 1.0
    hair[-32:, :] = 1.0
    cream = namespace["hsv2rgb"](np.full_like(h, 0.075), np.clip(s * 0.34, 0.04, 0.20), 0.15 + v * 0.22)
    brown = namespace["hsv2rgb"](np.full_like(h, 0.065), np.full_like(s, 0.48), 0.06 + v * 0.30)
    out = cream * (1.0 - hair[..., None]) + brown * hair[..., None]
    namespace["save_np"](out, os.path.join(MOD, "art", "textures", "skins", "props", "head", "lindon_face_a.png"))


def build_lindon_head(namespace):
    namespace["clear_scene"]()
    bpy.ops.wm.collada_import(filepath=os.path.join(namespace["REF"], "head_longhair.dae"))
    head = bpy.data.objects["head_longhair"]
    head.scale = (1.0, 1.0, 1.0)
    bpy.context.view_layer.update()
    head.name = "lindon_head"
    me = head.data
    for vertex in me.vertices:
        x, y, z = vertex.co
        if abs(x) >= 0.16 and 0.12 < z < 0.30 and -0.05 < y < 0.12:
            x *= 1.08
            z += 0.035
        vertex.co = (x, y, z)
    mat = bpy.data.materials.new("lindon_head")
    mat.use_nodes = True
    me.materials.clear()
    me.materials.append(mat)
    bpy.ops.object.select_all(action="DESELECT")
    head.select_set(True)
    bpy.context.view_layer.objects.active = head
    out = os.path.join(MOD, "art", "meshes", "props", "new", "lindon_head.dae")
    bpy.ops.wm.collada_export(filepath=out, selected=True)


def main():
    # Reuse the verified elf head surgery and texture helpers, then give Lindon
    # its own material palette without duplicating the mesh recipe.
    namespace = runpy.run_path(os.path.join(BASE_DIR, "build_doriath.py"))
    namespace["MOD"] = MOD
    def recolor_lindon_body(src, cloth_h, cloth_smul, cloth_vmul, outp, seed):
        image = bpy.data.images.load(src)
        pixels = namespace["img_to_np"](image)
        h, s, v = namespace["rgb2hsv"](pixels[..., :3])
        skin = (h > 0.02) & (h < 0.13) & (s > 0.18) & (v > 0.25)
        new_h = np.where(skin, 0.075, cloth_h)
        new_s = np.where(skin, np.clip(s * 0.34, 0.04, 0.20), s * cloth_smul)
        new_v = np.where(skin, 0.18 + v * 0.20, v * cloth_vmul + 0.03)
        out = namespace["hsv2rgb"](new_h, new_s, new_v)
        out += (namespace["mottle"](out.shape[:2], seed, 32, 0.04) - 0.02)[..., None]
        namespace["save_np"](out, outp)

    namespace["gen_green"] = lambda: recolor_lindon_body(
        os.path.join(namespace["REF"], "skeletal_pers_padded_01_01.png"),
        0.52, 0.20, 0.48,
        os.path.join(MOD, "art", "textures", "skins", "skeletal", "tolkien", "lindon_sea_green_01.png"), 71)
    namespace["gen_steel"] = lambda: recolor_lindon_body(
        os.path.join(namespace["REF"], "skeletal_pers_linothorax_01_01.png"),
        0.58, 0.13, 0.42,
        os.path.join(MOD, "art", "textures", "skins", "skeletal", "tolkien", "lindon_silver_01.png"), 81)
    build_lindon_head(namespace)
    gen_lindon_face(namespace)
    namespace["gen_green"]()
    namespace["gen_steel"]()
    print("LINDON BUILD DONE")


if __name__ == "__main__":
    main()