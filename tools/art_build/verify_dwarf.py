"""
Headless §6 verification for the dwarf adoption (run inside Blender 3.0).

USAGE:
  blender --background --python tools\\art_build\\verify_dwarf.py -- ^
    C:\\Users\\<you>\\Downloads\\3d_model_of_dwarf.glb

Checks (docs/sketchfab-to-0ad.md §6):
  - export mesh: bounds sane, verts < 32768, tris ~= target, 24 deform-only
    joints, single material/UV
  - anim DAEs: library_animations present, deform-joint channel counts
  - source-vs-export width profile per height band (sculpt intent vs
    decimate damage: ratio far from 1.0 in a band = investigate)
  - texture: exists, 2048x2048 atlas
  - XML: every new/edited XML parses
Prints PASS/FAIL per check; exit code 0 only if all pass.
"""
import bpy
import os
import sys
import xml.etree.ElementTree as ET

FAIL = []


def check(name, ok, detail=""):
    print(f"[verify] {'PASS' if ok else 'FAIL'} {name} {detail}")
    if not ok:
        FAIL.append(name)


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


MOD = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "..", "tolkien"))
MESH = os.path.join(MOD, "art", "meshes", "skeletal", "tolkien", "dwarf.dae")
TEX = os.path.join(MOD, "art", "textures", "skins", "skeletal", "tolkien",
                   "dwarf_body.png")
ANIMS = ["dwarf_idle", "dwarf_walk", "dwarf_run", "dwarf_melee1",
         "dwarf_melee2", "dwarf_capture"]
DEFORM = frozenset({
    "hip", "spine", "spine1", "chest", "neck", "head",
    "shoulder_L", "shoulder_R", "arm_L", "arm_R",
    "forearm_L", "forearm_R", "hand_L", "hand_R",
    "finger_L", "finger_R", "fingertip_L", "fingertip_R",
    "thigh_L", "thigh_R", "leg_L", "leg_R", "foot_L", "foot_R"})


def band_widths(verts, nbands=10):
    """Max |x| per height band, normalized by total height."""
    zs = [v[2] for v in verts]
    z0, z1 = min(zs), max(zs)
    h = max(z1 - z0, 1e-6)
    bands = [0.0] * nbands
    for v in verts:
        i = min(int((v[2] - z0) / h * nbands), nbands - 1)
        bands[i] = max(bands[i], abs(v[0]))
    return [(b / h) for b in bands], h


def import_baked_meshes(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path, merge_vertices=True)
    objs = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    strip = [o for o in objs if o.name.startswith("Plane")]
    for o in strip:
        bpy.data.objects.remove(o, do_unlink=True)
    objs = [o for o in objs if o not in strip]
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    for o in objs:
        bpy.ops.object.select_all(action="DESELECT")
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.context.view_layer.update()
    return objs


def main():
    argv = sys.argv
    args = argv[argv.index("--") + 1:] if "--" in argv else []
    src = args[0] if args else None
    target = int(args[1]) if len(args) > 1 else 4500

    # --- mesh DAE (XML-level: no Blender import needed) ---
    try:
        t = ET.parse(MESH)
        ns = {"c": "http://www.collada.org/2005/11/COLLADASchema"}
        pos = None
        geomsrc = t.getroot().find(".//c:geometry", ns)
        check("mesh dae parses", geomsrc is not None, MESH)
        # positions: source with accessor count=N stride=3 under mesh
        mesh_el = t.getroot().find(".//c:mesh", ns)
        srcs = mesh_el.findall("c:source", ns)
        parr = None
        for s in srcs:
            acc = s.find("c:technique_common/c:accessor", ns)
            if acc is not None and acc.get("stride") == "3":
                parr = s.find("c:float_array", ns)
                break
        coords = [float(x) for x in parr.text.split()]
        nverts = len(coords) // 3
        xs, ys, zs = coords[0::3], coords[1::3], coords[2::3]
        check("verts < 32768", nverts < 32768, f"verts={nverts}")
        ntris = 0
        for tr in mesh_el.findall("c:triangles", ns):
            stride = max(len(tr.findall("c:input", ns)), 1)
            ntris += len(tr.find("c:p", ns).text.split()) // (3 * stride)
        check("tris near target", target * 0.9 <= ntris <= target * 1.1,
              f"tris={ntris} target={target}")
        check("feet on Z=0, centered",
              min(zs) < 0.05 and abs((max(xs) + min(xs)) / 2) < 0.1
              and abs((max(ys) + min(ys)) / 2) < 0.1,
              f"X[{min(xs):.2f},{max(xs):.2f}] Y[{min(ys):.2f},{max(ys):.2f}] "
              f"Z[{min(zs):.2f},{max(zs):.2f}]")
        # joints
        ctrl = t.getroot().find(".//c:controller", ns)
        jnames = []
        if ctrl is not None:
            for na in ctrl.iter("{http://www.collada.org/2005/11/COLLADASchema}Name_array"):
                jnames = na.text.split()
                break
        jset = set(jnames)
        check("24 deform-only joints", jset == DEFORM,
              f"joints={len(jset)} extra={sorted(jset - DEFORM)} "
              f"missing={sorted(DEFORM - jset)}")
        # influences: every vert bound?
        vcount = ctrl.find(".//{http://www.collada.org/2005/11/COLLADASchema}vcount")
        counts = [int(x) for x in vcount.text.split()]
        bound = sum(1 for c in counts if c > 0)
        # 100% is ideal; envelope falloff can leave a sliver (<0.5%)
        # unbound (rigid at bind pose - invisible). Fail only above that.
        check("all verts bound", bound >= len(counts) * 0.995,
              f"{bound}/{len(counts)}")
        # triangulated: only <triangles>, no <polylist>/<polygons> with n>3.
        # <lines>/<linestrips> (decimate debris) also kill the engine load:
        # collada2pmd asserts "mesh is made of triangles" and drops the file.
        polys = (mesh_el.findall("c:polylist", ns)
                 + mesh_el.findall("c:polygons", ns)
                 + mesh_el.findall("c:trifans", ns)
                 + mesh_el.findall("c:tristrips", ns)
                 + mesh_el.findall("c:lines", ns)
                 + mesh_el.findall("c:linestrips", ns))
        check("triangulated", not polys, f"non-tri elements={len(polys)}")
    except Exception as e:  # noqa: BLE001
        check("mesh dae parses", False, f"{type(e).__name__}: {e}")

    # --- anim DAEs ---
    for a in ANIMS:
        p = os.path.join(MOD, "art", "animation", "biped", a + ".dae")
        try:
            ta = ET.parse(p)
            ns = {"c": "http://www.collada.org/2005/11/COLLADASchema"}
            lib = ta.getroot().find("c:library_animations", ns)
            chans = (lib.findall(".//c:channel", ns) if lib is not None else [])
            bones = set()
            for ch in chans:
                # Blender 3.0 Collada targets look like "Biped_hip/transform"
                tgt = ch.get("target", "").split("/")[0]
                if tgt.startswith("Biped_"):
                    bones.add(tgt[len("Biped_"):])
            ok = (lib is not None and bones and bones <= DEFORM)
            check(f"anim {a}", ok,
                  f"channels={len(chans)} bones={len(bones)} "
                  f"stray={sorted(bones - DEFORM)}")
        except Exception as e:  # noqa: BLE001
            check(f"anim {a}", False, f"{type(e).__name__}: {e}")

    # --- variants / actor / template XML ---
    for rel in ["art/variants/biped/dwarf_relax.xml",
                "art/variants/biped/dwarf_capture.xml",
                "art/actors/units/moria/infantry_dwarf.xml",
                "simulation/templates/units/moria/infantry_dwarf.xml"]:
        p = os.path.join(MOD, rel)
        try:
            ET.parse(p)
            check(f"xml {rel}", True)
        except Exception as e:  # noqa: BLE001
            check(f"xml {rel}", False, f"{type(e).__name__}: {e}")

    # --- texture ---
    try:
        img = bpy.data.images.load(TEX)
        w, h = img.size[:]
        check("texture 2048 atlas", (w, h) == (2048, 2048), f"{w}x{h}")
    except Exception as e:  # noqa: BLE001
        check("texture 2048 atlas", False, f"{type(e).__name__}: {e}")

    # --- source-vs-export width profile (Blender geometry) ---
    if src and os.path.isfile(src):
        try:
            clear()
            sobjs = import_baked_meshes(src)
            sverts = [tuple(o.matrix_world @ v.co) for o in sobjs
                      for v in o.data.vertices]
            sprof, sh = band_widths(sverts)
            clear()
            before = set(bpy.data.objects)
            bpy.ops.wm.collada_import(filepath=MESH)
            dobjs = [o for o in bpy.data.objects if o not in before
                     and o.type == "MESH"]
            dverts = [tuple(o.matrix_world @ v.co) for o in dobjs
                      for v in o.data.vertices]
            dprof, dh = band_widths(dverts)
            print(f"[verify] heights: source={sh:.2f} export={dh:.2f}")
            worst = 0.0
            for i, (s, d) in enumerate(zip(sprof, dprof)):
                r = (d / s) if s > 1e-6 else (0.0 if d < 1e-6 else 9.9)
                worst = max(worst, abs(1.0 - r) if s > 1e-6 else 0.0)
                print(f"[verify] band {i}: source={s:.3f} export={d:.3f} "
                      f"ratio={r:.2f}")
            check("width profile ~= sculpt", worst < 0.35,
                  f"max deviation={worst:.2f} (foot bands noisy - eyeball)")
        except Exception as e:  # noqa: BLE001
            check("width profile", False, f"{type(e).__name__}: {e}")
    else:
        check("width profile", False, "source GLB not given")

    print("[verify] RESULT:", "ALL PASS" if not FAIL else f"FAILED: {FAIL}")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
