import bpy
import bmesh
import math
import os
import numpy as np
from mathutils import Vector

REF = os.environ.get("ZEROAD_REFERENCE_ART")
if not REF:
    raise RuntimeError("Set ZEROAD_REFERENCE_ART to the extracted 0 A.D. public art directory")
MOD = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tolkien"))

def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)

# ---------------------------------------------------------------- color helpers
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
    r = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [v, q, p, p, t, v])
    g = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [t, v, v, q, p, p])
    b = np.select([i == 0, i == 1, i == 2, i == 3, i == 4, i == 5], [p, p, t, v, v, q])
    return np.stack([r, g, b], axis=-1)

def mottle(shape, seed, base=32, amp=0.06):
    rng = np.random.default_rng(seed)
    small = rng.random((base, base))
    big = np.kron(small, np.ones((shape[0] // base, shape[1] // base)))
    return big[: shape[0], : shape[1]] * amp

def save_np(arr, outp):
    h, w = arr.shape[0], arr.shape[1]
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    name = os.path.splitext(os.path.basename(outp))[0]
    img = bpy.data.images.new(name, w, h, alpha=True, float_buffer=False)
    out = np.ones((h, w, 4), dtype=np.float32)
    out[..., :3] = np.clip(arr, 0, 1)
    img.pixels.foreach_set(out.ravel())
    img.filepath_raw = outp
    img.file_format = "PNG"
    img.save()
    print("WROTE", outp, os.path.exists(outp))

def img_to_np(img):
    w, h = img.size
    arr = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(arr)
    return arr.reshape(h, w, 4)

# ---------------------------------------------------------------- head + hair
def raster_mask(me, face_idx, RES):
    """Rasterize the given faces' UV triangles into a RES x RES mask (1 = inside)."""
    mask = np.zeros((RES, RES), dtype=np.float32)
    uvl = me.uv_layers.active.data
    for i, poly in enumerate(me.polygons):
        if i not in face_idx:
            continue
        loops = list(poly.loop_indices)
        for k in range(1, len(loops) - 1):
            u0, v0 = uvl[loops[0]].uv
            u1, v1 = uvl[loops[k]].uv
            u2, v2 = uvl[loops[k + 1]].uv
            xs = (u0 * RES, u1 * RES, u2 * RES)
            ys = (v0 * RES, v1 * RES, v2 * RES)
            xmin = max(int(min(xs)) - 1, 0); xmax = min(int(max(xs)) + 2, RES)
            ymin = max(int(min(ys)) - 1, 0); ymax = min(int(max(ys)) + 2, RES)
            def sign(ax, ay, bx, by, cx, cy):
                return (cx - ax) * (by - ay) - (cy - ay) * (bx - ax)
            area = sign(xs[0], ys[0], xs[1], ys[1], xs[2], ys[2])
            if abs(area) < 1e-9:
                continue
            for py in range(ymin, ymax):
                cy = py + 0.5
                for px in range(xmin, xmax):
                    cx = px + 0.5
                    w0 = sign(xs[1], ys[1], xs[2], ys[2], cx, cy)
                    w1 = sign(xs[2], ys[2], xs[0], ys[0], cx, cy)
                    w2 = sign(xs[0], ys[0], xs[1], ys[1], cx, cy)
                    inside = (w0 >= 0 and w1 >= 0 and w2 >= 0) if area > 0 \
                        else (w0 <= 0 and w1 <= 0 and w2 <= 0)
                    if inside:
                        mask[py, px] = 1.0
    return mask

def build_elf_head():
    clear_scene()
    bpy.ops.wm.collada_import(filepath=os.path.join(REF, "dudette_head_a.dae"))
    head = bpy.data.objects["dudette_head_a"]
    head.scale = (1.0, 1.0, 1.0)   # game uses raw local coords (template §3)
    bpy.context.view_layer.update()
    me = head.data

    # --- mesh tweaks
    for v in me.vertices:
        x, y, z = v.co
        # pointed ears (subtle, so side hair isn't distorted)
        if abs(x) >= 0.15 and 0.12 < z < 0.30 and -0.06 < y < 0.12:
            x *= 1.12
            z += 0.07
        # slightly widen the MOUTH band only (skip the chin) -> horizontal widen
        if y > 0.08 and 0.07 <= z <= 0.12:
            x *= 1.05
        # flowing untied hair: pull the hanging back curtain further down + out
        if y < 0.0 and z < 0.12:
            t = min(max((0.12 - z) / 0.22, 0.0), 1.0)
            z -= 0.28 * t
            y -= 0.04 * t
            x *= (1.0 + 0.08 * t)
        v.co = (x, y, z)

    # --- hair region by 3D position: back of head or top/scalp (NOT the face)
    hair_idx = set(i for i, p in enumerate(me.polygons)
                  if p.center.y < 0.02 or p.center.z >= 0.30)

    # --- recolor: hair -> brown (preserve strand luminance); face -> original
    RES = 128
    mask = raster_mask(me, hair_idx, RES)
    img = bpy.data.images.load(os.path.join(REF, "celt_fem_a.dds"))
    orig = img_to_np(img)[..., :3]
    oy, ox = orig.shape[0], orig.shape[1]
    yy = (np.arange(RES) * oy // RES)
    xx = (np.arange(RES) * ox // RES)
    orig_r = orig[np.ix_(yy, xx)]
    h, s, v = rgb2hsv(orig_r)
    brown = hsv2rgb(np.full_like(h, 0.075), np.full_like(s, 0.45), 0.10 + v * 0.34)
    # face -> pale fair elf skin (desaturate + lighten, preserve luminance so the
    # painted eyes/mouth keep their contrast)
    pale = hsv2rgb(np.full_like(h, 0.08), np.clip(s * 0.35, 0.0, 0.20), 0.62 + v * 0.38)
    m = mask[..., None]
    out = pale * (1.0 - m) + brown * m
    out += (mottle((RES, RES), 9, 64, 0.04) - 0.02)[..., None]
    outp = os.path.join(MOD, "art", "textures", "skins", "props", "head", "elf_face_a.png")
    save_np(out, outp)

    # --- material + export
    mat = bpy.data.materials.new("elf_head")
    mat.use_nodes = True
    me.materials.clear()
    me.materials.append(mat)
    head.name = "elf_head"
    bpy.ops.object.select_all(action="DESELECT")
    head.select_set(True)
    bpy.context.view_layer.objects.active = head
    outp2 = os.path.join(MOD, "art", "meshes", "props", "new", "elf_head.dae")
    os.makedirs(os.path.dirname(outp2), exist_ok=True)
    bpy.ops.wm.collada_export(filepath=outp2, selected=True)
    print("EXPORTED", outp2, "verts:", len(me.vertices), "hair_faces:", len(hair_idx))

# ---------------------------------------------------------------- body textures
ELF_SKIN_H = 0.08
ELF_SKIN_S = 0.22

def recolor_body(src, cloth_h, cloth_smul, cloth_vmul, outp, seed):
    # warm tan pixels -> pale elf skin; everything else -> faction clothing
    img = bpy.data.images.load(src)
    px = img_to_np(img)
    h, s, v = rgb2hsv(px[..., :3])
    skin = (h > 0.02) & (h < 0.13) & (s > 0.18) & (v > 0.25)
    new_h = np.where(skin, ELF_SKIN_H, cloth_h)
    new_s = np.where(skin, np.clip(s * 0.30, 0.0, ELF_SKIN_S), s * cloth_smul)
    new_v = np.where(skin, 0.55 + v * 0.45, v * cloth_vmul + 0.03)
    out = hsv2rgb(new_h, new_s, new_v)
    out += (mottle(out.shape[:2], seed, 32, 0.05) - 0.025)[..., None]
    save_np(out, outp)

def gen_green():
    src = os.path.join(REF, "skeletal_pers_padded_01_01.png")
    outp = os.path.join(MOD, "art", "textures", "skins", "skeletal", "tolkien", "elf_green_01.png")
    recolor_body(src, 0.30, 0.22, 0.55, outp, 41)

def gen_steel():
    src = os.path.join(REF, "skeletal_pers_linothorax_01_01.png")
    outp = os.path.join(MOD, "art", "textures", "skins", "skeletal", "tolkien", "elf_steel_01.png")
    recolor_body(src, 0.33, 0.15, 0.45, outp, 51)

if __name__ == "__main__":
    build_elf_head()
    gen_green()
    gen_steel()
    print("BUILD DONE")
