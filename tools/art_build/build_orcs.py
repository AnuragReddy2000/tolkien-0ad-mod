import bpy
import numpy as np
import math
import os

REF = os.environ.get("ZEROAD_REFERENCE_ART")
if not REF:
    raise RuntimeError("Set ZEROAD_REFERENCE_ART to the extracted 0 A.D. public art directory")
MOD = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "tolkien"))

def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)

# ---------------------------------------------------------------- head surgery
def build_orc_head():
    clear_scene()
    bpy.ops.wm.collada_import(filepath=os.path.join(REF, "meshes_props_new_dude_head.dae"))
    head = bpy.data.objects["dude_head"]
    # importer applied an inch->meter scale artifact; the game uses raw local coords,
    # so drop the object scale to make local coords == game units (head ~0.6 tall vs body 3.85)
    head.scale = (1.0, 1.0, 1.0)
    bpy.context.view_layer.update()
    me = head.data

    for v in me.vertices:
        x, y, z = v.co
        # 1. flatten + widen skull cap
        if z >= 0.40:
            z = 0.40 + (z - 0.40) * 0.80
            x *= 1.06
        # 2. heavy brow ridge
        elif 0.26 <= z < 0.40 and y > 0.08:
            y += 0.028
        # 3. broad prognathic jaw
        if z < 0.17 and y > 0.0:
            t = min(max((0.17 - z) / 0.28, 0.0), 1.0)
            x *= 1.22
            y += 0.05 * t
        # 4. pointed ears (outermost mid-side verts)
        if abs(x) >= 0.185 and 0.15 < z < 0.32:
            x *= 1.25
            z += 0.06
        v.co = (x, y, z)

    # find an empty UV corner for the tusks
    uv = me.uv_layers.active.data
    corners = {
        "bl": (0.00, 0.00), "br": (0.96, 0.00),
        "tl": (0.00, 0.96), "tr": (0.96, 0.96),
    }
    best, best_n = None, 10**9
    for name, (cu, cv) in corners.items():
        n = sum(1 for d in uv if cu <= d.uv[0] <= cu + 0.04 and cv <= d.uv[1] <= cv + 0.04)
        if n < best_n:
            best, best_n = name, n
    print("TUSK_UV_CORNER", best, "existing loops there:", best_n)
    cu, cv = corners[best]

    # tusks: two lower canines jutting up from mouth corners
    # mouth corners after surgery ~ (+-0.093, 0.156, 0.088)
    tusk_verts = []
    tusk_faces = []
    for sx in (1, -1):
        base = np.array([sx * 0.055, 0.165, 0.050])
        tip = np.array([sx * 0.062, 0.195, 0.128])
        d = tip - base
        d = d / np.linalg.norm(d)
        up = np.array([0.0, 0.0, 1.0])
        side = np.cross(d, up)
        side = side / np.linalg.norm(side)
        fwd = np.cross(side, d)
        fwd = fwd / np.linalg.norm(fwd)
        nseg = 5
        start = len(tusk_verts)
        for i in range(nseg):
            a = 2 * math.pi * i / nseg
            ring = base + (math.cos(a) * 0.014) * side + (math.sin(a) * 0.011) * fwd
            tusk_verts.append(tuple(ring))
        tusk_verts.append(tuple(tip))
        tip_i = len(tusk_verts) - 1
        for i in range(nseg):
            tusk_faces.append((start + i, start + (i + 1) % nseg, tip_i))
        tusk_faces.append(tuple(reversed(range(start, start + nseg))))

    tusk_me = bpy.data.meshes.new("orc_tusks")
    tusk_me.from_pydata(tusk_verts, [], tusk_faces)
    tusk_me.update()
    tusk_obj = bpy.data.objects.new("orc_tusks", tusk_me)
    bpy.context.collection.objects.link(tusk_obj)

    # join tusks into head
    bpy.ops.object.select_all(action="DESELECT")
    tusk_obj.select_set(True)
    head.select_set(True)
    bpy.context.view_layer.objects.active = head
    bpy.ops.object.join()

    # assign tusk UVs to the reserved ivory corner
    uv = head.data.uv_layers.active.data
    n_loops = len(head.data.loops)
    tusk_loops = n_loops - len(tusk_faces) * 3  # joined last
    for i in range(tusk_loops, n_loops):
        fi = (i - tusk_loops) // 3
        li = (i - tusk_loops) % 3
        if fi % 2 == 0:  # side faces -> ivory gradient
            uv[i].uv = (cu + 0.01 + 0.005 * li, cv + 0.02)
        else:            # cap faces -> slightly darker ivory
            uv[i].uv = (cu + 0.03, cv + 0.02)

    # single material
    mat = bpy.data.materials.new("orc_head")
    mat.use_nodes = True
    head.data.materials.clear()
    head.data.materials.append(mat)

    for p in head.data.polygons:
        p.use_smooth = False

    head.name = "orc_head"
    bpy.ops.object.select_all(action="DESELECT")
    head.select_set(True)
    bpy.context.view_layer.objects.active = head
    out = os.path.join(MOD, "art", "meshes", "props", "new", "orc_head.dae")
    bpy.ops.wm.collada_export(filepath=out, selected=True)
    print("EXPORTED", out, "verts:", len(head.data.vertices))

# ---------------------------------------------------------------- textures
def img_to_np(img):
    w, h = img.size
    arr = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(arr)
    return arr.reshape(h, w, 4)

def save_np(arr, outp):
    h, w = arr.shape[0], arr.shape[1]
    name = os.path.splitext(os.path.basename(outp))[0]
    img = bpy.data.images.new(name, w, h, alpha=True, float_buffer=False)
    out = np.ones((h, w, 4), dtype=np.float32)
    out[..., :3] = np.clip(arr, 0, 1)
    img.pixels.foreach_set(out.ravel())
    img.filepath_raw = outp
    img.file_format = "PNG"
    img.save()
    print("WROTE", outp, os.path.exists(outp))

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

ORC_SKIN_H = 0.28   # dark grey-green
ORC_SKIN_S = 0.30
ORC_SKIN_V = 0.34

def gen_orc_skin():
    # Repaint the source beard and moustache zones as skin while retaining dark
    # brows and scalp for a harsher, hairless orc face.
    img = bpy.data.images.load(os.path.join(REF, "props_head_pers_face_a.png"))
    px = img_to_np(img)
    h, s, v = rgb2hsv(px[..., :3])
    new_h = np.full_like(h, ORC_SKIN_H)
    new_s = np.clip(s * 0.38 + 0.10, 0.08, 0.34)
    new_v = 0.18 + v * 0.34
    eye = (v > 0.80) & (s < 0.35)
    new_h[eye] = 0.11
    new_s[eye] = 0.55
    new_v[eye] = 0.80
    out = hsv2rgb(new_h, new_s, new_v)
    rough = mottle(out.shape[:2], 7, 16, 0.10)
    out += (rough - 0.05)[..., None]
    outp = os.path.join(MOD, "art", "textures", "skins", "props", "head", "orc_face_a.png")
    save_np(out, outp)

def recolor_body(src, cloth_h, cloth_vmul, outp, seed):
    # warm tan pixels -> orc skin; everything else -> dark clothing
    img = bpy.data.images.load(src)
    px = img_to_np(img)
    h, s, v = rgb2hsv(px[..., :3])
    skin = (h > 0.02) & (h < 0.13) & (s > 0.18) & (v > 0.25)
    new_h = np.where(skin, ORC_SKIN_H, cloth_h)
    new_s = np.where(skin, np.clip(s * 0.5, 0.0, 0.35), s * 0.18)
    new_v = np.where(skin, v * 0.32, v * cloth_vmul + 0.02)
    out = hsv2rgb(new_h, new_s, new_v)
    out += (mottle(out.shape[:2], seed, 32, 0.05) - 0.025)[..., None]
    save_np(out, outp)

def gen_leather():
    src = os.path.join(REF, "skeletal_pers_padded_01_01.png")
    outp = os.path.join(MOD, "art", "textures", "skins", "skeletal", "tolkien", "orc_leather_01.png")
    recolor_body(src, 0.07, 0.30, outp, 11)

def gen_iron():
    src = os.path.join(REF, "skeletal_pers_linothorax_01_01.png")
    outp = os.path.join(MOD, "art", "textures", "skins", "skeletal", "tolkien", "orc_iron_01.png")
    recolor_body(src, 0.60, 0.26, outp, 21)

if __name__ == "__main__":
    build_orc_head()
    gen_orc_skin()
    gen_leather()
    gen_iron()
    print("BUILD DONE")
