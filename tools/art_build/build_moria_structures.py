"""
Moria structure reskins (Blender 3.0 headless): darken stock building
textures to deep-hall basalt. Meshes/UVs/AO untouched - same layout,
Moria read. Sources in %TEMP%\\moriatex (re-fetched upstream; %TEMP%\\0ad_ref
gets pruned by temp cleaners).

USAGE:
  blender --background --python tools\\art_build\\build_moria_structures.py
"""
import bpy
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, "..", "..", "tolkien"))
SRC = os.environ.get("MORIA_TEXTURE_SOURCE_DIR")
if not SRC:
    raise RuntimeError("Set MORIA_TEXTURE_SOURCE_DIR to the directory containing source textures")

# (source file, mod output name, mode) - gate mode bronzes warm trim
JOBS = [
    ("structural_hele_struct_b.png", "moria_struct_b.png", "hall"),
    ("structural_hele_struct_b.png", "moria_struct_b_gate.png", "gate"),
    ("structural_hele_struct.dds", "moria_struct_plain.png", "hall"),
    ("structural_celt_struct_1.dds", "moria_celt_struct.png", "hall"),
    ("props_hele_gate.png", "moria_gate.png", "gate"),
    ("props_palisade_main.png", "moria_palisade.png", "hall"),
    ("structural_sparta_struct.png", "moria_sparta_struct.png", "hall"),
]


def log(*a):
    print("[moria-struct]", *a)


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def rgb2hsv(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    maxc = np.max(rgb, axis=-1)
    minc = np.min(rgb, axis=-1)
    diff = maxc - minc
    v = maxc
    s = np.where(maxc > 1e-6, diff / np.maximum(maxc, 1e-6), 0.0)
    h = np.zeros_like(v)
    d = np.maximum(diff, 1e-6)
    m_r = (maxc == r) & (diff > 1e-6)
    m_g = (maxc == g) & (diff > 1e-6) & ~m_r
    m_b = (diff > 1e-6) & ~m_r & ~m_g
    h[m_r] = (((g[m_r] - b[m_r]) / d[m_r]) % 6.0) / 6.0
    h[m_g] = (((b[m_g] - r[m_g]) / d[m_g]) + 2.0) / 6.0
    h[m_b] = (((r[m_b] - g[m_b]) / d[m_b]) + 4.0) / 6.0
    return h, s, v


def hsv2rgb(h, s, v):
    i = np.floor(h * 6.0)
    f = h * 6.0 - i
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    i = (i % 6).astype(int)
    r = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5],
                  [v, q, p, p, t, v])
    g = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5],
                  [t, v, v, q, p, p])
    b = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5],
                  [p, p, t, v, v, q])
    return np.stack([r, g, b], axis=-1)


def img_to_np(img):
    w, h = img.size
    arr = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(arr)
    return arr.reshape(h, w, 4)


def save_np(arr, outp):
    h, w = arr.shape[0], arr.shape[1]
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    img = bpy.data.images.new(os.path.basename(outp), w, h,
                              alpha=True, float_buffer=False)
    out = np.ones((h, w, 4), dtype=np.float32)
    out[..., :3] = np.clip(arr, 0, 1)
    img.pixels.foreach_set(out.ravel())
    img.filepath_raw = outp
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def main():
    clear()
    outdir = os.path.join(MOD, "art", "textures", "skins", "structural",
                          "tolkien")
    rng = np.random.default_rng(7)
    for src_name, out_name, mode in JOBS:
        src = os.path.join(SRC, src_name)
        if not os.path.isfile(src):
            raise SystemExit(f"source missing: {src}")
        try:
            img = bpy.data.images.load(src)
        except RuntimeError:
            raise SystemExit(f"Blender cannot read {src} (DDS?) - aborting")
        px = img_to_np(img)[..., :3]
        h, s, v = rgb2hsv(px)
        warm = (h > 0.02) & (h < 0.14) & (s > 0.18)
        if mode == "gate":
            nh = np.where(warm, 0.08, h + (0.58 - h) * 0.35)
            ns = np.where(warm, np.maximum(s, 0.35), s * 0.9)
            nv = np.where(warm, v * 0.65 + 0.02, v * 0.55 + 0.02)
        else:
            nh = np.where(warm, h, h + (0.58 - h) * 0.35)
            ns = np.where(warm, s * 0.95, s * 0.9)
            nv = v * 0.55 + 0.02
        out = hsv2rgb(nh, np.clip(ns, 0, 1), np.clip(nv, 0, 1))
        mottle = (rng.random((32, 32)) - 0.5) * 0.05
        big = np.kron(mottle, np.ones((out.shape[0] // 32,
                                      out.shape[1] // 32)))
        out += big[:out.shape[0], :out.shape[1]][..., None]
        save_np(out, os.path.join(outdir, out_name))
        log(f"{src_name} -> {out_name} ({mode}, meanV {v.mean():.2f}"
            f"->{np.clip(nv,0,1).mean():.2f})")
        bpy.data.images.remove(img)
    with open(os.path.join(outdir, "moria_structures_CREDITS.txt"), "w",
              encoding="utf-8") as f:
        f.write("Moria structure reskins: recolored derivatives of 0 A.D. "
                "public building textures (CC-BY-SA, Wildfire Games) - "
                "darkened to deep-hall basalt; meshes, UVs, AO untouched.\n"
                "Sources: hele_struct_b.png, hele_struct.dds, "
                "celt_struct_1.dds, hele_gate.png, palisade_main.png, "
                "sparta_struct.png.\n")
    log("STRUCTURE TEXTURES DONE")


if __name__ == "__main__":
    main()
