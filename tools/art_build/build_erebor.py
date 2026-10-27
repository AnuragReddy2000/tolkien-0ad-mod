import bpy
import math
import os
import runpy
import numpy as np

MOD = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tolkien"))
REF = os.environ.get("ZEROAD_REFERENCE_ART")
if not REF:
    raise RuntimeError("Set ZEROAD_REFERENCE_ART to the extracted 0 A.D. public art directory")


def export_selected(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = bpy.context.scene.objects[-1]
    bpy.context.scene.objects[-1].select_set(True)
    bpy.ops.wm.collada_export(filepath=path, selected=True)


def main():
    base = runpy.run_path(os.path.join(os.path.dirname(__file__), "build_doriath.py"))
    base["MOD"] = MOD
    base["REF"] = REF
    base["clear_scene"]()
    bpy.ops.wm.collada_import(filepath=os.path.join(REF, "meshes_props_new_dude_head.dae"))
    head = bpy.data.objects["dude_head"]
    head.scale = (1.0, 1.0, 1.0)
    for vertex in head.data.vertices:
        x, y, z = vertex.co
        x *= 1.16
        z = 0.10 + (z - 0.10) * 0.92
        vertex.co = (x, y, z)
    head.name = "erebor_head"
    export_selected(os.path.join(MOD, "art", "meshes", "props", "new", "erebor_head.dae"))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.collada_import(filepath=os.path.join(REF, "meshes_props_new_head_beard_small.dae"))
    beard = bpy.data.objects["head_beard_small"]
    beard.scale = (1.0, 1.0, 1.0)
    beard.name = "erebor_beard"
    export_selected(os.path.join(MOD, "art", "meshes", "props", "new", "erebor_beard.dae"))

    face = bpy.data.images.load(os.path.join(REF, "props_head_pers_face_a.png"))
    pixels = base["img_to_np"](face)[..., :3]
    h, s, v = base["rgb2hsv"](pixels)
    out = base["hsv2rgb"](np.full_like(h, 0.075), np.clip(s * 0.42, 0.04, 0.22), 0.24 + v * 0.27)
    base["save_np"](out, os.path.join(MOD, "art", "textures", "skins", "props", "head", "erebor_face_a.png"))

    def recolor(src, hue, value, output, seed):
        image = bpy.data.images.load(src)
        source = base["img_to_np"](image)
        sh, ss, sv = base["rgb2hsv"](source[..., :3])
        skin = (sh > 0.02) & (sh < 0.13) & (ss > 0.18) & (sv > 0.25)
        nh = np.where(skin, 0.075, hue)
        ns = np.where(skin, np.clip(ss * 0.42, 0.04, 0.22), ss * 0.18)
        nv = np.where(skin, 0.24 + sv * 0.27, sv * value + 0.02)
        result = base["hsv2rgb"](nh, ns, nv)
        result += (base["mottle"](result.shape[:2], seed, 32, 0.04) - 0.02)[..., None]
        base["save_np"](result, output)

    recolor(os.path.join(REF, "skeletal_pers_linothorax_01_01.png"), 0.58, 0.34,
            os.path.join(MOD, "art", "textures", "skins", "skeletal", "tolkien", "erebor_iron_01.png"), 91)
    recolor(os.path.join(REF, "skeletal_pers_padded_01_01.png"), 0.06, 0.26,
            os.path.join(MOD, "art", "textures", "skins", "skeletal", "tolkien", "erebor_leather_01.png"), 101)
    print("EREBOR BUILD DONE")


if __name__ == "__main__":
    main()