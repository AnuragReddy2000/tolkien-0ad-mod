"""
Moria dwarf variant pack (Blender 3.0 headless) - LOOK ITERATION, NOT ROSTER.

Builds a set of distinct stout-dwarf looks for review. Nothing existing is
modified; the miners/levies/regulars roster actors are untouched. Once the
looks are approved these actors get wired into templates one by one.

Design rules (user brief):
  - all units short & stout (the 2 baked stout bodies: pants / tunic)
  - regulars: signature dwarven helm (stock LP mesh, silver tex)
  - advanced: dwarven helm in GOLD
  - elite/champion: elaborate helm = gold helm + propped crown / horns / crest
  - try different armour / dress: cloth tints, steel, gilded gold, shields,
    worker tools, beard colours

Outputs (all NEW, never overwriting existing files):
  art/textures/skins/skeletal/tolkien/  moria_cloth_red_01.png, moria_cloth_blue_01.png,
                                        moria_iron_02_steel.png, moria_gold_01.png
  art/textures/skins/props/head/        erebor_face_brown.png, erebor_face_white.png,
                                        erebor_face_ginger.png
  art/textures/skins/props/helmet/      erebor_helm_gold.png, moria_crown.png,
                                        moria_horn.png, moria_crest.png
  art/meshes/props/new/                 moria_crown.dae, moria_horn_l.dae, moria_horn_r.dae,
                                        moria_crest.dae (+ CREDITS sidecars)
  art/actors/props/units/helmets/       moria_helm_gold.xml, moria_crown.xml,
                                        moria_horn_l.xml, moria_horn_r.xml, moria_crest_red.xml
  art/actors/props/units/heads/         moria_beard_brown.xml, moria_beard_white.xml,
                                        moria_beard_ginger.xml
  art/actors/units/moria/variants/      the 10 unit actors (variants/moria_*.xml)

Then render previews:
  blender --background --python tools/art_build/render_moria_variants.py
"""
import bpy
import math
import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, "..", "..", "tolkien"))

SKEL_TEX = os.path.join(MOD, "art", "textures", "skins", "skeletal", "tolkien")
HEAD_TEX = os.path.join(MOD, "art", "textures", "skins", "props", "head")
HELM_TEX = os.path.join(MOD, "art", "textures", "skins", "props", "helmet")
PROP_MESH = os.path.join(MOD, "art", "meshes", "props", "new")


_HERE_LOG = os.path.join(os.environ.get("TEMP", ""), "moria_variants_progress.txt")


def log(*a):
    msg = "[moria-var] " + " ".join(str(x) for x in a)
    with open(_HERE_LOG, "a", encoding="utf-8") as lf:
        lf.write(msg + "\n")
    print(msg)


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


# ---------------------------------------------------------------- textures

def load_rgba(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    arr = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(arr)
    bpy.data.images.remove(img)
    return arr.reshape(h, w, 4)


def save_rgba(path, arr):
    h, w = arr.shape[:2]
    img = bpy.data.images.new("var_tex", w, h, alpha=True)
    img.pixels.foreach_set(arr.ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def tint(arr, mult, add=0.0, mask_gray=False, label=""):
    """Shift pixels toward a colour recipe.

    mult = (r, g, b) channel multipliers, add = brightness offset.
    mask_gray: only recolour pixels where max-min channel spread is small
    (leaves warm skin/leather/belt pixels alone).
    Returns the changed copy plus diagnostics."""
    rgb = arr[..., :3].copy()
    spread = rgb.max(axis=-1) - rgb.min(axis=-1)
    if mask_gray:
        a = np.clip(1.0 - spread / 0.05, 0.0, 1.0)[..., None]
    else:
        a = np.ones_like(spread)[..., None]
    v = rgb.mean(axis=-1, keepdims=True) + add
    target = v * np.array(mult)
    out = rgb * (1.0 - a) + target * a
    out = np.clip(out, 0.0, 1.0)
    d_gray = np.abs((out[..., :3] - rgb)[spread < 0.02])
    d_warm = np.abs((out[..., :3] - rgb)[spread > 0.06])
    res = arr.copy()
    res[..., :3] = out
    res[..., 3] = 1.0
    log("tint %s: gray_px=%.1f%% dgray=%.3f dwarm=%.3f" % (
        label, 100.0 * (spread < 0.02).mean(),
        d_gray.mean() if d_gray.size else 0.0,
        d_warm.mean() if d_warm.size else 0.0))
    if mask_gray and d_warm.mean() > 0.02:
        raise SystemExit("tint %s bled into warm pixels - aborting" % label)
    if not mask_gray and d_gray.mean() < 0.015:
        raise SystemExit("tint %s changed almost nothing - aborting" % label)
    return res


GOLD = (1.00, 0.74, 0.30)
STEEL = (0.85, 0.92, 1.00)
RED = (1.05, 0.30, 0.26)
BLUE = (0.45, 0.62, 1.05)
BROWN = (0.95, 0.62, 0.42)
WHITE = (1.30, 1.30, 1.28)
GINGER = (1.05, 0.55, 0.38)


def build_textures():
    src_cloth = load_rgba(os.path.join(SKEL_TEX, "moria_cloth_01.png"))
    src_iron = load_rgba(os.path.join(SKEL_TEX, "moria_iron_01.png"))
    src_face = load_rgba(os.path.join(HEAD_TEX, "erebor_face_a.png"))
    src_helm = load_rgba(os.path.join(HELM_TEX, "erebor_helm.png"))

    for name, arr, mult, add, mg in (
            ("moria_cloth_red_01.png", src_cloth, RED, 0.10, True),
            ("moria_cloth_blue_01.png", src_cloth, BLUE, 0.10, True),
            ("moria_iron_02_steel.png", src_iron, STEEL, 0.28, False),
            ("moria_gold_01.png", src_iron, GOLD, 0.30, False)):
        save_rgba(os.path.join(SKEL_TEX, name),
                  tint(arr, mult, add, mg, name))

    for name, mult, add in (
            ("erebor_face_brown.png", BROWN, 0.05),
            ("erebor_face_white.png", WHITE, 0.45),
            ("erebor_face_ginger.png", GINGER, 0.12)):
        save_rgba(os.path.join(HEAD_TEX, name),
                  tint(src_face, mult, add, True, name))

    save_rgba(os.path.join(HELM_TEX, "erebor_helm_gold.png"),
              tint(src_helm, GOLD, 0.35, False, "erebor_helm_gold.png"))


# ---------------------------------------------------------------- textures 2

def bake_flat(path, base, vgrad=0.0, w=256):
    """Simple gradient PNG for the decorative props (own canvases)."""
    rgb = np.array(base, dtype=np.float32)
    arr = np.ones((w, w, 4), dtype=np.float32)
    grad = np.linspace(1.0, 1.0 - vgrad, w)[..., None]
    arr[..., :3] = clip01(rgb[None, None, :] * grad[None, :, None])
    save_rgba(path, arr)
    log("flat tex", os.path.basename(path))


def clip01(x):
    return np.clip(x, 0.0, 1.0)


# ---------------------------------------------------------------- materials


def import_one_mesh(dae):
    before = set(bpy.data.objects)
    bpy.ops.wm.collada_import(filepath=dae)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    meshes = [o for o in bpy.data.objects
              if o not in before and o.type == "MESH"]
    if len(meshes) != 1:
        raise SystemExit("expected 1 mesh in %s got %d" % (dae, len(meshes)))
    return meshes[0]


def bounds_of(obj):
    co = np.empty(len(obj.data.vertices) * 3, dtype=np.float32)
    obj.data.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    x0, y0, z0 = co.min(axis=0)
    x1, y1, z1 = co.max(axis=0)
    return x0, x1, y0, y1, z0, z1


def export_mesh(obj, name, limits, credits):
    """Validate inside the helmet-bone frame, then export + credits."""
    x0, x1, y0, y1, z0, z1 = bounds_of(obj)
    log("bounds %s: X[%.3f,%.3f] Y[%.3f,%.3f] Z[%.3f,%.3f]" %
        (name, x0, x1, y0, y1, z0, z1))
    tol = 1e-3
    if not (limits[0] - tol <= x0 and x1 <= limits[1] + tol
            and limits[2] - tol <= y0 and y1 <= limits[3] + tol
            and limits[4] - tol <= z0 and z1 <= limits[5] + tol):
        raise SystemExit("BOUNDS FAILED for %s: limits X%s Y%s Z%s" %
                         (name, limits[:2], limits[2:4], limits[4:6]))
    out_dae = os.path.join(PROP_MESH, name + ".dae")
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    log("collada out %s" % out_dae)
    bpy.ops.wm.collada_export(filepath=out_dae, selected=True)
    log("EXPORTED", out_dae)
    with open(os.path.join(PROP_MESH, name + "_CREDITS.txt"), "w",
              encoding="utf-8") as cf:
        cf.write(credits)
    return out_dae


CRM_X = (0.30, 0.74, 1.6)      # stats: gold multiple / offsets tested

CREDITS_DECOR = (
    "Procedural Moria helmet decoration (crown band / horns / crest), "
    "authored in the stock helmet-bone frame. Companion prop for the "
    "remodelled 'Dwarf_Helmet_LP' by prorok_009 (CC-BY 4.0); Weta-derived "
    "upstream - same IP review note as erebor_helm.md.\n")


def new_mesh(name, verts, faces, uv_of=None):
    """Static mesh via from_pydata; uv_of(vertex_index) -> (u, v).

    Loops are written in face order (from_pydata preserves it), never via
    me.loops[].vertex_index which is stale on freshly built meshes."""
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    if uv_of is not None:
        ul = me.uv_layers.new(name="UVMap")
        li = 0
        for f in faces:
            for vi in f:
                u, v = uv_of(vi)
                ul.data[li].uv = (u, v)
                li += 1
    me.validate()
    ob = bpy.data.objects.new(name, me)
    me.materials.append(bpy.data.materials.new(name + "_m"))
    bpy.context.collection.objects.link(ob)
    return ob


def build_decor_meshes():
    log("decor: crown begin")
    # ---- crown: closed band hugging the helm dome + 5 spikes
    rx_o, ry_o = 0.315, 0.355
    rx_i, ry_i = 0.275, 0.315
    z0, band = 0.46, 0.075
    n = 48
    verts = []
    faces = []
    def uv_crown(i):
        x, y, z = verts[i]
        ang = math.atan2(y / ry_o, x / rx_o)
        v = (z - 0.46) / 0.185 * 0.94 + 0.03
        return ((ang + math.pi) / (2 * math.pi), max(0.0, min(1.0, v)))
    for k in range(n):
        t = 2 * math.pi * k / n
        co = (math.cos(t), math.sin(t))
        verts.append((rx_o * co[0], ry_o * co[1], z0))            # outer low
        verts.append((rx_o * co[0], ry_o * co[1], z0 + band))     # outer high
        verts.append((rx_i * co[0], ry_i * co[1], z0))            # inner low
        verts.append((rx_i * co[0], ry_i * co[1], z0 + band))     # inner high
    def ring(i):
        a = 4 * i
        b = 4 * ((i + 1) % n)
        return list(range(a, a + 4)), list(range(b, b + 4))
    for i in range(n):
        A, B = ring(i)
        # outer wall, inner wall, top rim, bottom rim
        faces += [
            (A[0], A[1], B[1], B[0]),
            (A[3], A[2], B[2], B[3]),
            (A[1], A[3], B[3], B[1]),
            (A[2], A[0], B[0], B[2]),
        ]
    # 5 spikes on the top rim, front (-Y, angle 270deg) taller
    def add_spike(angle_deg, height):
        a = math.radians(angle_deg)
        px, py = rx_o * math.cos(a), ry_o * math.sin(a)
        rb, rt = 0.018, 0.0
        z1, z2 = z0 + band, z0 + band + height
        ring_ib = len(verts)
        for k in range(6):
            t = 2 * math.pi * k / 6
            verts.append((px + rb * math.cos(t), py + rb * math.sin(t), z1))
        it = len(verts)
        verts.append((px, py, z2))
        for k in range(6):
            a0 = ring_ib + k
            a1 = ring_ib + (k + 1) % 6
            faces.append((a0, a1, it))
        return None
    for ang, h in ((270, 0.11), (225, 0.075), (315, 0.075),
                   (180, 0.075), (0, 0.075)):
        add_spike(ang, h)
    log("decor: crown verts/faces ready")
    crown = new_mesh("moria_crown", verts, faces, uv_of=uv_crown)
    log("decor: crown mesh built")
    export_mesh(crown, "moria_crown",
                (-0.40, 0.40, -0.44, 0.44, 0.40, 0.72), CREDITS_DECOR)
    log("decor: crown exported")

    # ---- horns: swept tapering cones, embedded inside the shell
    def make_horn(sign, tag):
        base = np.array([0.215 * sign, -0.02, 0.46])
        d = np.array([0.90 * sign, -0.18, 0.45])
        d = d / np.linalg.norm(d)
        curva = np.array([0.55 * sign, 0.10, 0.55])
        step = 0.033
        rings = []
        r0 = 0.052
        for i in range(9):
            rings.append((base + d * (i * step), r0 * (1 - i / 9) ** 1.2 + 0.004))
            d = d + curva * step
            d = d / np.linalg.norm(d)
        verts = []
        faces = []
        for i, (c, r) in enumerate(rings):
            for k in range(10):
                t = 2 * math.pi * k / 10
                verts.append((c[0] + r * math.cos(t) * 0.9,
                              c[1] + r * math.sin(t),
                              c[2] + r * 0.35 * math.cos(t)))
        for i in range(8):
            for k in range(10):
                a = i * 10 + k
                b = i * 10 + (k + 1) % 10
                c = (i + 1) * 10 + k
                dd = ((i + 1) * 10 + (k + 1) % 10)
                faces.append((a, dd, c, b))
        # tip cap
        tip = len(verts)
        tl = rings[-1]
        verts.append((tl[0][0] + d[0] * 0.02, tl[0][1] + d[1] * 0.02,
                      tl[0][2] + d[2] * 0.02))
        for k in range(10):
            a = 8 * 10 + k
            b = 8 * 10 + (k + 1) % 10
            faces.append((a, b, tip, tip))
        def uv_horn(i):
            if i >= 90:
                return (0.5, 1.0)
            ring_i, k = divmod(i, 10)
            return (k / 10.0, ring_i / 8.0)
        return new_mesh(tag, verts, faces, uv_of=uv_horn)
    hl = make_horn(1.0, "moria_horn_l")
    hr = make_horn(-1.0, "moria_horn_r")
    export_mesh(hl, "moria_horn_l",
                (-0.02, 0.55, -0.14, 0.16, 0.40, 0.72), CREDITS_DECOR)
    export_mesh(hr, "moria_horn_r",
                (-0.55, 0.02, -0.14, 0.16, 0.40, 0.72), CREDITS_DECOR)

    # ---- crest fin: arc ribbon in the sagittal (YZ) plane, front = -Y
    cy, cz = -0.02, 0.33
    r_out, r_in = 0.37, 0.30
    th = 0.015
    n = 28
    verts = []
    faces = []
    for k in range(n + 1):
        t = math.radians(-60 + 120.0 * k / n)
        yo_o = cy + r_out * math.sin(t)
        z_o = cz + r_out * math.cos(t)
        yo_i = cy + r_in * math.sin(t)
        z_i = cz + r_in * math.cos(t)
        verts += [(-th, yo_o, z_o), (th, yo_o, z_o),
                  (-th, yo_i, z_i), (th, yo_i, z_i)]
    def rowj(k):
        a = 4 * k
        return list(range(a, a + 4)), list(range(a + 4, a + 8))
    for k in range(n):
        A, B = rowj(k)
        faces += [
            (A[0], A[1], B[1], B[0]),        # outer sheet
            (A[3], A[2], B[2], B[3]),        # inner sheet
            (A[1], A[3], B[3], B[1]),        # side X=+th
            (A[2], A[0], B[0], B[2]),        # side X=-th
        ]
    A, _ = rowj(0)
    faces.append((A[0], A[1], A[3], A[2]))
    A, _ = rowj(n)
    faces.append((A[0], A[1], A[3], A[2]))
    def uv_crest(i):
        x, y, z = verts[i]
        v = (z - zmin_crest) / zspan_crest
        return (0.5, max(0.0, min(1.0, v)))
    _zs = [v[2] for v in verts]
    zmin_crest, zmax_crest = min(_zs), max(_zs)
    zspan_crest = max(zmax_crest - zmin_crest, 1e-6)
    mx = max(max(f) for f in faces)
    log("crest chk: verts=%d faces=%d maxidx=%d" %
        (len(verts), len(faces), mx))
    if mx >= len(verts):
        bad = [(fi, f) for fi, f in enumerate(faces) if max(f) >= len(verts)]
        raise SystemExit("crest OOB faces: %s" % bad[:3])
    crest = new_mesh("moria_crest", verts, faces, uv_of=uv_crest)
    export_mesh(crest, "moria_crest",
                (-0.04, 0.04, -0.42, 0.42, 0.48, 0.74), CREDITS_DECOR)


# ---------------------------------------------------------------- actors

def write_actor(path, name, mesh, tex, extra_props=None):
    xml = ['<?xml version="1.0" encoding="utf-8"?>', '<actor version="1">',
           '  <castshadow/>', '  <group>',
           '    <variant frequency="1" name="Base">',
           f'      <mesh>{mesh}</mesh>']
    if extra_props:
        xml.append('      <props>')
        for actor, ap in extra_props:
            xml.append(f'        <prop actor="{actor}" attachpoint="{ap}"/>')
        xml.append('      </props>')
    xml += ['      <textures>',
            f'        <texture file="{tex}" name="baseTex"/>',
            '        <texture file="default_norm.png" name="normTex"/>',
            '        <texture file="null_black.dds" name="specTex"/>',
            '      </textures>', '    </variant>', '  </group>',
            '  <material>objectcolor_norm_spec.xml</material>', '</actor>']
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as xf:
        xf.write("\n".join(xml) + "\n")
    log("wrote", os.path.relpath(path, MOD))


def build_prop_actors():
    hd = os.path.join(MOD, "art", "actors", "props", "units", "helmets")
    head_dir = os.path.join(MOD, "art", "actors", "props", "units", "heads")
    write_actor(os.path.join(hd, "moria_helm_gold.xml"), "moria_helm_gold",
                "props/new/erebor_helm.dae", "props/helmet/erebor_helm_gold.png")
    write_actor(os.path.join(hd, "moria_crown.xml"), "moria_crown",
                "props/new/moria_crown.dae", "props/helmet/moria_crown.png")
    write_actor(os.path.join(hd, "moria_horn_l.xml"), "moria_horn_l",
                "props/new/moria_horn_l.dae", "props/helmet/moria_horn.png")
    write_actor(os.path.join(hd, "moria_horn_r.xml"), "moria_horn_r",
                "props/new/moria_horn_r.dae", "props/helmet/moria_horn.png")
    write_actor(os.path.join(hd, "moria_crest_red.xml"), "moria_crest_red",
                "props/new/moria_crest.dae", "props/helmet/moria_crest.png")
    for tag in ("brown", "white", "ginger"):
        write_actor(os.path.join(head_dir, "moria_beard_%s.xml" % tag),
                    "beard_%s" % tag, "props/new/erebor_beard.dae",
                    "props/head/erebor_face_%s.png" % tag)


W = "props/units/weapons/"
T = "props/units/tools/"
S = "props/units/shields/"

VARIANTS = [
    # fname suffix      body      bodytex                 beard    helm/extras
    ("moria_civil_miner", "moria_dwarf_stout_tunic.dae", "moria_leather_01.png", "", []),
    ("moria_civil_smith", "moria_dwarf_stout_tunic.dae", "moria_cloth_01.png", "white", []),
    ("moria_civil_guest", "moria_dwarf_stout_tunic.dae", "moria_cloth_red_01.png", "ginger", []),
    ("moria_levy_ovalax", "moria_dwarf_stout_pants.dae", "moria_cloth_blue_01.png", "brown", []),
    ("moria_levy_spear", "moria_dwarf_stout_pants.dae", "moria_leather_01.png", "", []),
    ("moria_reg_axe", "moria_dwarf_stout_pants.dae", "moria_iron_01.png", "brown", []),
    ("moria_reg_spearsteel", "moria_dwarf_stout_pants.dae", "moria_iron_02_steel.png", "ginger", []),
    ("moria_adv_shieldgold", "moria_dwarf_stout_pants.dae", "moria_iron_02_steel.png", "ginger",
     [("props/units/helmets/moria_helm_gold.xml", "helmet"),
      ("props/units/helmets/moria_crown.xml", "helmet")]),
    ("moria_adv_gildedaxe", "moria_dwarf_stout_pants.dae", "moria_gold_01.png", "white",
     [("props/units/helmets/moria_helm_gold.xml", "helmet")]),
    ("moria_champ_full", "moria_dwarf_stout_pants.dae", "moria_gold_01.png", "ginger",
     [("props/units/helmets/moria_helm_gold.xml", "helmet"),
      ("props/units/helmets/moria_crown.xml", "helmet"),
      ("props/units/helmets/moria_horn_l.xml", "helmet"),
      ("props/units/helmets/moria_horn_r.xml", "helmet"),
      ("props/units/helmets/moria_crest_red.xml", "helmet")]),
]

GEAR = {
    "moria_civil_miner": (T + "pick.xml", None),
    "moria_civil_smith": (T + "hammer.xml", None),
    "moria_civil_guest": (T + "mallet.xml", None),
    "moria_levy_ovalax": (W + "axe_single.xml", S + "celt_buckler_a.xml"),
    "moria_levy_spear": (W + "spear.xml", S + "celt_buckler_c.xml"),
    "moria_reg_axe": (W + "axe_single.xml", S + "celt_buckler_a.xml"),
    "moria_reg_spearsteel": (W + "spear.xml", None),
    "moria_adv_shieldgold": (W + "xiphos.xml", S + "celt_buckler_a.xml"),
    "moria_adv_gildedaxe": (W + "axe_double.xml", None),
    "moria_champ_full": (W + "axe_double.xml", None),
}


def build_unit_actors():
    outdir = os.path.join(MOD, "art", "actors", "units", "moria", "variants")
    for fname, body, tex, beard, helmprops in VARIANTS:
        props = [("props/units/heads/erebor_head.xml", "head")]
        if beard:
            props.append(("props/units/heads/moria_beard_%s.xml" % beard,
                          "head"))
        else:
            props.append(("props/units/heads/erebor_beard.xml", "head"))
        if not helmprops:
            props.append(("props/units/helmets/erebor_helm.xml", "helmet"))
        props += helmprops
        weapon, shield = GEAR[fname]
        props.append((weapon, "weapon_R"))
        if shield:
            props.append((shield, "shield"))
        base_anim = ("biped/base_spearman_relax.xml"
                     if "spear" in fname else
                     "biped/base_swordsman_2hand_relax.xml")
        if fname.startswith("moria_civil"):
            base_anim = "biped/base_swordsman_2hand_relax.xml"
        xml = ('<?xml version="1.0" encoding="utf-8"?>\n'
               '<actor version="1">\n'
               '  <castshadow/>\n'
               '  <group>\n'
               '    <variant frequency="1" name="Base">\n'
               f'      <mesh>skeletal/tolkien/{body}</mesh>\n'
               '      <props>\n'
               + "".join(f'        <prop actor="{a}" attachpoint="{p}"/>\n'
                         for a, p in props)
               + '      </props>\n'
               '      <textures>\n'
               f'        <texture file="skeletal/tolkien/{tex}" name="baseTex"/>\n'
               '        <texture file="default_norm.png" name="normTex"/>\n'
               '        <texture file="null_black.dds" name="specTex"/>\n'
               '      </textures>\n'
               '    </variant>\n'
               '  </group>\n'
               '  <group>\n'
               f'    <variant file="{base_anim}"/>\n'
               '    <variant file="biped/attack_capture.xml"/>\n'
               '    <variant file="biped/attack_slaughter.xml"/>\n'
               '    <variant file="biped/death_infantry.xml"/>\n'
               '  </group>\n'
               '  <material>player_trans_norm_spec.xml</material>\n'
               '</actor>\n')
        os.makedirs(outdir, exist_ok=True)
        with open(os.path.join(outdir, fname + ".xml"), "w",
                  encoding="utf-8") as xf:
            xf.write(xml)
        log("wrote", os.path.relpath(os.path.join(outdir, fname + ".xml"), MOD))


def validate_gear_paths():
    """Every referenced prop actor must exist in the mod or vanilla."""
    check_all = set()
    for fname, _b, _t, beard, helmprops in VARIANTS:
        check_all.add("props/units/heads/erebor_head.xml")
        if beard:
            check_all.add("props/units/heads/moria_beard_%s.xml" % beard)
        else:
            check_all.add("props/units/heads/erebor_beard.xml")
            check_all.add("props/units/helmets/erebor_helm.xml")
        for a, _ in helmprops:
            check_all.add(a)
        w, s = GEAR[fname]
        if w:
            check_all.add(w)
        if s:
            check_all.add(s)
    source_mod = os.environ.get("ZEROAD_SOURCE_MOD")
    if not source_mod:
        raise RuntimeError("Set ZEROAD_SOURCE_MOD to the installed 0 A.D. public mod directory")
    refroot = os.path.join(source_mod, "art", "actors")
    missing = []
    for rel in sorted(check_all):
        if not (os.path.isfile(os.path.join(MOD, "art", "actors", rel))
                or os.path.isfile(os.path.join(refroot, rel))):
            missing.append(rel)
    if missing:
        raise SystemExit("MISSING PROP ACTORS:\n  " + "\n  ".join(missing))
    log("gear path check OK (%d actor refs)" % len(check_all))


def main():
    # Blender 3.0.1 can segfault when the mesh phase runs in the same
    # context after the numpy-heavy texture phase, so the phases run as
    # separate invocations: ... -- textures | -- models
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not args or args[0] == "textures":
        clear()
        build_textures()
        bake_flat(os.path.join(HELM_TEX, "moria_crown.png"),
                  (0.86, 0.62, 0.20), vgrad=0.28)
        bake_flat(os.path.join(HELM_TEX, "moria_horn.png"),
                  (0.78, 0.74, 0.66), vgrad=0.35)
        bake_flat(os.path.join(HELM_TEX, "moria_crest.png"),
                  (0.45, 0.06, 0.06), vgrad=0.30)
        log("TEXTURE PHASE DONE")
    if not args or args[0] == "models":
        clear()
        build_decor_meshes()
        build_prop_actors()
        build_unit_actors()
        validate_gear_paths()
        log("MESH PHASE DONE")


if __name__ == "__main__":
    main()
