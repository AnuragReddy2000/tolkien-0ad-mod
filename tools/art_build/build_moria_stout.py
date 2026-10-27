"""
Moria stout roster (Blender 3.0 headless) - the B+C pivot applied to a faction.

Bakes stout bodies from stock meshes with the SAME connected-safe transform
proven by build_erebor_poc (single affine T, tails + unconnected heads only;
head/helmet gap validation), recolors Moria-dark textures, writes unit actors.

USAGE:
  blender --background --python tools\\art_build\\build_moria_stout.py

Bodies (stock -> mod stout; armored short shares the Erebor bake):
  m_armor_pants_tunic_short -> moria_dwarf_stout_pants.dae (spearman, ranger)
  m_tunic_short             -> moria_dwarf_stout_tunic.dae (miner/worker)
Textures (Moria palette: dark bronze + charcoal):
  moria_iron_01, moria_leather_01, moria_cloth_01
Actors (art/actors/units/moria/):
  infantry_dwarf (axeman, LP helm), infantry_guardsman (sword, LP helm),
  infantry_spearman (spear, LP helm), infantry_archer (bow, no helm),
  infantry_ranger (throwing axe, no helm), support_worker (miner, no helm)
Helm rule: melee line wears the LP war-helm; scouts/archers/workers don't.
"""
import bpy
import os
import runpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.normpath(os.path.join(HERE, "..", "..", "tolkien"))
REF = os.environ.get("ZEROAD_REFERENCE_ART")
if not REF:
    raise RuntimeError("Set ZEROAD_REFERENCE_ART to the extracted 0 A.D. public art directory")

SX, SY, SZ = 1.16, 1.16, 0.82  # same stout factors as the Erebor POC

BODIES = [
    # (stock ref file, mod output mesh name)
    ("meshes_skeletal_new_m_armor_pants_tunic_short.dae",
     "moria_dwarf_stout_pants.dae"),
    ("meshes_skeletal_new_m_tunic_short.dae",
     "moria_dwarf_stout_tunic.dae"),
]


def log(*a):
    print("[moria-stout]", *a)


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def bake_body(ref_file, out_name):
    src = os.path.join(REF, ref_file)
    if not os.path.isfile(src):
        raise SystemExit(f"stock body missing: {src}")
    clear()
    before = set(bpy.data.objects)
    bpy.ops.wm.collada_import(filepath=src)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    arms = [o for o in new if o.type == "ARMATURE"]
    mesh = max(meshes, key=lambda o: len(o.data.vertices)) if meshes else None
    arm = max(arms, key=lambda o: len(o.data.bones)) if arms else None
    for o in list(new):
        if o is not mesh and o is not arm:
            bpy.data.objects.remove(o, do_unlink=True)
    if mesh is None or arm is None or not len(arm.data.bones):
        raise SystemExit(f"bad import for {ref_file}")
    log(f"stock {ref_file}: verts={len(mesh.data.vertices)} "
        f"bones={len(arm.data.bones)} height={mesh.dimensions.z:.2f}")
    hb0 = arm.data.bones.get("head")
    if hb0 is None or abs(hb0.head_local[2] - 3.773) > 0.15:
        raise SystemExit("stock armature unexpected - aborting loudly")

    for v in mesh.data.vertices:
        x, y, z = v.co
        v.co = (x * SX, y * SY, z * SZ)
    xs = [v.co.x for v in mesh.data.vertices]
    ys = [v.co.y for v in mesh.data.vertices]
    zs = [v.co.z for v in mesh.data.vertices]
    dx = -((max(xs) + min(xs)) / 2)
    dy = -((max(ys) + min(ys)) / 2)
    dz = -min(zs)

    def T(p):
        return (p[0] * SX + dx, p[1] * SY + dy, p[2] * SZ + dz)

    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    for b in arm.data.edit_bones:
        b.tail = T(b.tail)
        if not b.use_connect:
            b.head = T(b.head)
    bpy.ops.object.mode_set(mode="OBJECT")
    for v in mesh.data.vertices:
        v.co = (v.co[0] + dx, v.co[1] + dy, v.co[2] + dz)

    xs = [v.co.x for v in mesh.data.vertices]
    zs = [v.co.z for v in mesh.data.vertices]
    mesh_top = max(zs)
    hb = arm.data.bones.get("head")
    hm = arm.data.bones.get("helmet")
    d_head = mesh_top - hb.head_local[2]
    d_helm = hb.head_local[2] - hm.head_local[2]
    log(f"validate {out_name}: mesh_top={mesh_top:.3f} "
        f"gaps {d_head:.3f}/{d_helm:.3f} (want ~0.064/~0.081)")
    if abs(d_head - 0.064) > 0.06 or abs(d_helm - 0.081) > 0.06:
        raise SystemExit(f"VALIDATION FAILED for {out_name} - aborting")

    out = os.path.join(MOD, "art", "meshes", "skeletal", "tolkien", out_name)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.wm.collada_export(filepath=out, selected=True,
                              include_animations=False)
    log("EXPORTED", out)
    with open(os.path.join(os.path.dirname(out),
                           out_name.replace(".dae", "_CREDITS.txt")),
              "w", encoding="utf-8") as f:
        f.write("B+C body: derived from 0 A.D. public stock mesh "
                f"{ref_file} (CC-BY-SA, Wildfire Games).\n"
                f"Baked stout scale X*{SX} Y*{SY} Z*{SZ}; bone names "
                "unchanged so all stock biped/* variants keep working.\n")


def gen_textures():
    base = runpy.run_path(os.path.join(HERE, "build_doriath.py"))

    def recolor(src, hue, value, output, seed):
        image = bpy.data.images.load(src)
        source = base["img_to_np"](image)
        sh, ss, sv = base["rgb2hsv"](source[..., :3])
        skin = (sh > 0.02) & (sh < 0.13) & (ss > 0.18) & (sv > 0.25)
        nh = np.where(skin, 0.075, hue)
        ns = np.where(skin, np.clip(ss * 0.42, 0.04, 0.22), ss * 0.18)
        nv = np.where(skin, 0.24 + sv * 0.27, sv * value + 0.02)
        result = base["hsv2rgb"](nh, ns, nv)
        result += (base["mottle"](result.shape[:2], seed, 32, 0.04)
                   - 0.02)[..., None]
        base["save_np"](result, output)

    tex = os.path.join(MOD, "art", "textures", "skins", "skeletal", "tolkien")
    recolor(os.path.join(REF, "skeletal_pers_linothorax_01_01.png"),
            0.07, 0.30, os.path.join(tex, "moria_iron_01.png"), 71)
    recolor(os.path.join(REF, "skeletal_pers_padded_01_01.png"),
            0.05, 0.22, os.path.join(tex, "moria_leather_01.png"), 72)
    recolor(os.path.join(REF, "skeletal_pers_padded_01_01.png"),
            0.00, 0.35, os.path.join(tex, "moria_cloth_01.png"), 73)
    log("textures done")


MELEE_ANIMS = """    <variant file="biped/base_swordsman_2hand_relax.xml"/>
    <variant file="biped/attack_capture.xml"/>
    <variant file="biped/attack_slaughter.xml"/>
    <variant file="biped/death_infantry.xml"/>"""
SPEAR_ANIMS = """    <variant file="biped/base_spearman_relax.xml"/>
    <variant file="biped/attack_capture.xml"/>
    <variant file="biped/attack_slaughter.xml"/>
    <variant file="biped/death_infantry.xml"/>"""
ARCHER_ANIMS = """    <variant file="biped/base_archer_relax.xml"/>
    <variant file="biped/attack_ranged_archer.xml"/>
    <variant file="biped/death_infantry.xml"/>"""
RANGER_ANIMS = """    <variant file="biped/base_skirmisher.xml"/>
    <variant file="biped/attack_ranged_javelinist.xml"/>
    <variant file="biped/death_infantry.xml"/>"""
WORKER_ANIMS = """    <variant file="biped/base_swordsman_2hand_relax.xml"/>
    <variant file="biped/carry_food.xml"/>
    <variant file="biped/carry_meat.xml"/>
    <variant file="biped/carry_wood.xml"/>
    <variant file="biped/carry_stone.xml"/>
    <variant file="biped/carry_metal.xml"/>
    <variant file="biped/approach_tree.xml"/>
    <variant file="biped/approach_grain.xml"/>
    <variant file="biped/approach_fruit.xml"/>
    <variant file="biped/approach_meat.xml"/>
    <variant file="biped/approach_rock.xml"/>
    <variant file="biped/approach_ore.xml"/>
    <variant file="biped/approach_ruins.xml"/>
    <variant file="biped/approach_praise.xml"/>
    <variant file="biped/attack_capture.xml"/>
    <variant file="biped/attack_slaughter.xml"/>
    <variant file="biped/gather_tree.xml"/>
    <variant file="biped/gather_grain.xml"/>
    <variant file="biped/gather_fruit.xml"/>
    <variant file="biped/gather_meat.xml"/>
    <variant file="biped/gather_rock.xml"/>
    <variant file="biped/gather_ore.xml"/>
    <variant file="biped/gather_ruins.xml"/>
    <variant file="biped/gather_praise.xml"/>
    <variant file="biped/build.xml"/>
    <variant file="biped/build_farm.xml"/>
    <variant file="biped/death_infantry.xml"/>"""

HELM = '        <prop actor="props/units/helmets/erebor_helm.xml" attachpoint="helmet"/>\n'
HEAD = ('        <prop actor="props/units/heads/erebor_head.xml" attachpoint="head"/>\n'
        '        <prop actor="props/units/heads/erebor_beard.xml" attachpoint="head"/>\n')

# (actor file, mesh, texture, extra props, anims) - HEAD always included
UNITS = [
    ("infantry_dwarf.xml", "skeletal/tolkien/erebor_dwarf_stout.dae",
     "skeletal/tolkien/moria_iron_01.png",
     '        <prop actor="props/units/weapons/axe_double.xml" attachpoint="weapon_R"/>\n',
     MELEE_ANIMS, True),
    ("infantry_guardsman.xml", "skeletal/tolkien/erebor_dwarf_stout.dae",
     "skeletal/tolkien/moria_iron_01.png",
     '        <prop actor="props/units/weapons/elf_sword.xml" attachpoint="weapon_R"/>\n',
     MELEE_ANIMS, True),
    ("infantry_spearman.xml", "skeletal/tolkien/moria_dwarf_stout_pants.dae",
     "skeletal/tolkien/moria_leather_01.png",
     '        <prop actor="props/units/weapons/spear.xml" attachpoint="weapon_R"/>\n',
     SPEAR_ANIMS, True),
    ("infantry_archer.xml", "skeletal/tolkien/erebor_dwarf_stout.dae",
     "skeletal/tolkien/moria_leather_01.png",
     '        <prop actor="props/units/weapons/elf_bow.xml" attachpoint="weapon_bow"/>\n',
     ARCHER_ANIMS, False),
    ("infantry_ranger.xml", "skeletal/tolkien/moria_dwarf_stout_pants.dae",
     "skeletal/tolkien/moria_leather_01.png",
     '        <prop actor="props/units/weapons/axe_single.xml" attachpoint="weapon_R"/>\n',
     RANGER_ANIMS, False),
    ("support_worker.xml", "skeletal/tolkien/moria_dwarf_stout_tunic.dae",
     "skeletal/tolkien/moria_cloth_01.png",
     "", WORKER_ANIMS, False),
]


def write_actor(fname, mesh, tex, weapon_prop, anims, helm):
    props = HEAD + (HELM if helm else "") + weapon_prop
    body = ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<actor version="1">\n'
            '  <castshadow/>\n'
            '  <group>\n'
            '    <variant frequency="1" name="Base">\n'
            f'      <mesh>{mesh}</mesh>\n'
            '      <props>\n'
            f'{props}'
            '      </props>\n'
            '      <textures>\n'
            f'        <texture file="{tex}" name="baseTex"/>\n'
            '        <texture file="default_norm.png" name="normTex"/>\n'
            '        <texture file="null_black.dds" name="specTex"/>\n'
            '      </textures>\n'
            '    </variant>\n'
            '  </group>\n'
            '  <group>\n'
            f'{anims}\n'
            '  </group>\n'
            '  <material>player_trans_norm_spec.xml</material>\n'
            '</actor>\n')
    out = os.path.join(MOD, "art", "actors", "units", "moria", fname)
    with open(out, "w", encoding="utf-8") as f:
        f.write(body)
    log("wrote actor units/moria/" + fname)


def main():
    for ref, out in BODIES:
        bake_body(ref, out)
    gen_textures()
    for fname, mesh, tex, weapon, anims, helm in UNITS:
        write_actor(fname, mesh, tex, weapon, anims, helm)
    log("MORIA BUILD DONE")


if __name__ == "__main__":
    main()
